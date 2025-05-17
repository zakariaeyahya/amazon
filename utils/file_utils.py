"""
File utility functions for handling data storage and retrieval with:
- CSV reading/writing with proper encoding
- JSON handling
- Data deduplication
- Incremental data updates
- File locking for concurrent access
"""

import os
import json
import csv
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Union
import fcntl
import time
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger(__name__)

@contextmanager
def file_lock(file_path: str):
    """
    Context manager for file locking to prevent concurrent access issues
    
    Args:
        file_path: Path to the file to lock
    """
    lock_path = f"{file_path}.lock"
    with open(lock_path, 'w') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            try:
                os.remove(lock_path)
            except OSError:
                pass

def ensure_dir(file_path: str) -> None:
    """
    Ensure the directory exists for a given file path
    
    Args:
        file_path: Path to a file
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def load_json(file_path: str, default: Any = None) -> Any:
    """
    Load JSON data from a file with error handling
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
    
    Returns:
        Parsed JSON data or default value
    """
    try:
        if not os.path.exists(file_path):
            return default if default is not None else {}
        
        with file_lock(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default if default is not None else {}

def save_json(data: Any, file_path: str, pretty: bool = True) -> bool:
    """
    Save data to a JSON file with error handling
    
    Args:
        data: Data to save
        file_path: Target file path
        pretty: Whether to format the JSON with indentation
    
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_dir(file_path)
        
        with file_lock(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def load_csv(file_path: str, default: Any = None) -> List[Dict]:
    """
    Load CSV data from a file with error handling
    
    Args:
        file_path: Path to the CSV file
        default: Default value to return if file doesn't exist or is invalid
    
    Returns:
        List of dictionaries representing CSV rows
    """
    try:
        if not os.path.exists(file_path):
            return default if default is not None else []
        
        with file_lock(file_path):
            df = pd.read_csv(file_path, encoding='utf-8')
            return df.to_dict('records')
    except pd.errors.EmptyDataError:
        logger.warning(f"Empty CSV file: {file_path}")
        return default if default is not None else []
    except Exception as e:
        logger.error(f"Error loading CSV from {file_path}: {e}")
        return default if default is not None else []

def save_csv(data: List[Dict], file_path: str, mode: str = 'w') -> bool:
    """
    Save data to a CSV file with error handling
    
    Args:
        data: List of dictionaries to save
        file_path: Target file path
        mode: File open mode ('w' for write, 'a' for append)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not data:
            logger.warning(f"No data to save to {file_path}")
            return False
        
        ensure_dir(file_path)
        
        df = pd.DataFrame(data)
        
        with file_lock(file_path):
            if mode == 'a' and os.path.exists(file_path):
                # For append mode, read existing data to avoid duplicates
                existing_df = pd.read_csv(file_path, encoding='utf-8')
                
                # Identify a unique key for deduplication
                # Use 'product_id' or 'id' if available
                key_columns = [col for col in ['product_id', 'id'] if col in df.columns and col in existing_df.columns]
                
                if key_columns:
                    # Use the first key column found for deduplication
                    key_col = key_columns[0]
                    # Replace existing entries with new ones and add truly new entries
                    combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=[key_col], keep='last')
                    combined_df.to_csv(file_path, index=False, encoding='utf-8')
                else:
                    # If no key column, just append all rows
                    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False, encoding='utf-8')
            else:
                # For write mode, simply write the data
                df.to_csv(file_path, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        logger.error(f"Error saving CSV to {file_path}: {e}")
        return False

def append_to_file(line: str, file_path: str) -> bool:
    """
    Append a line to a text file with error handling
    
    Args:
        line: Line to append
        file_path: Target file path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_dir(file_path)
        
        with file_lock(file_path):
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        return True
    except Exception as e:
        logger.error(f"Error appending to {file_path}: {e}")
        return False

def deduplicate_csv(file_path: str, key_column: str) -> bool:
    """
    Deduplicate a CSV file based on a key column
    
    Args:
        file_path: Path to the CSV file
        key_column: Column to use for deduplication
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return False
        
        with file_lock(file_path):
            df = pd.read_csv(file_path, encoding='utf-8')
            original_count = len(df)
            
            if key_column not in df.columns:
                logger.error(f"Key column '{key_column}' not found in {file_path}")
                return False
            
            df = df.drop_duplicates(subset=[key_column], keep='last')
            new_count = len(df)
            
            if original_count > new_count:
                logger.info(f"Removed {original_count - new_count} duplicates from {file_path}")
                df.to_csv(file_path, index=False, encoding='utf-8')
            
            return True
    except Exception as e:
        logger.error(f"Error deduplicating CSV {file_path}: {e}")
        return False

def merge_csv_files(input_files: List[str], output_file: str, key_column: Optional[str] = None) -> bool:
    """
    Merge multiple CSV files into one with optional deduplication
    
    Args:
        input_files: List of input CSV file paths
        output_file: Path to the output merged file
        key_column: Column to use for deduplication (optional)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        dfs = []
        
        for file_path in input_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                    dfs.append(df)
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
        
        if not dfs:
            logger.warning("No valid input files to merge")
            return False
        
        # Combine all dataframes
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Deduplicate if key column is provided
        if key_column and key_column in merged_df.columns:
            original_count = len(merged_df)
            merged_df = merged_df.drop_duplicates(subset=[key_column], keep='last')
            new_count = len(merged_df)
            
            if original_count > new_count:
                logger.info(f"Removed {original_count - new_count} duplicates from merged file")
        
        # Save the merged file
        ensure_dir(output_file)
        merged_df.to_csv(output_file, index=False, encoding='utf-8')
        
        return True
    except Exception as e:
        logger.error(f"Error merging CSV files: {e}")
        return False

def incremental_update(
    source_data: List[Dict],
    target_file: str, 
    key_column: str = 'product_id',
    timestamp_column: Optional[str] = 'last_updated'
) -> bool:
    """
    Update a target file with new/updated records from source data
    
    Args:
        source_data: New data to merge
        target_file: Path to the target file to update
        key_column: Column to use as unique identifier
        timestamp_column: Column to use for determining newer records
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not source_data:
            logger.warning("No source data provided for incremental update")
            return False
        
        # Create pandas DataFrame from source data
        source_df = pd.DataFrame(source_data)
        
        # Ensure key column exists
        if key_column not in source_df.columns:
            logger.error(f"Key column '{key_column}' not found in source data")
            return False
        
        # If target file doesn't exist, just write the source data
        if not os.path.exists(target_file):
            return save_csv(source_data, target_file)
        
        # Read target file
        with file_lock(target_file):
            target_df = pd.read_csv(target_file, encoding='utf-8')
            
            # Ensure key column exists in target
            if key_column not in target_df.columns:
                logger.error(f"Key column '{key_column}' not found in target file")
                return False
            
            # If timestamp column is provided, use it for determining newer records
            if timestamp_column and timestamp_column in source_df.columns and timestamp_column in target_df.columns:
                # Convert both to datetime if not already
                for df in [source_df, target_df]:
                    if not pd.api.types.is_datetime64_dtype(df[timestamp_column]):
                        df[timestamp_column] = pd.to_datetime(df[timestamp_column], errors='coerce')
                
                # Update strategy: keep newest by timestamp
                combined = pd.concat([target_df, source_df])
                combined = combined.sort_values(timestamp_column, ascending=False)
                result_df = combined.drop_duplicates(subset=[key_column], keep='first')
                
            else:
                # Simple update strategy: prefer source data
                result_df = pd.concat([target_df, source_df]).drop_duplicates(subset=[key_column], keep='last')
            
            # Save the updated file
            result_df.to_csv(target_file, index=False, encoding='utf-8')
            
            logger.info(f"Incremental update successful: {target_file}")
            return True
            
    except Exception as e:
        logger.error(f"Error performing incremental update: {e}")
        return False

def clean_data(input_file: str, output_file: Optional[str] = None) -> bool:
    """
    Clean and standardize data in a CSV file.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file (if None, overwrites input file)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return False
            
        with file_lock(input_file):
            # Read the CSV file
            df = pd.read_csv(input_file, encoding='utf-8')
            
            # Clean column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Remove duplicate rows
            df = df.drop_duplicates()
            
            # Clean string columns
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace empty strings with NaN
                df[col] = df[col].replace('', pd.NA)
            
            # Clean numeric columns
            for col in df.select_dtypes(include=['float64', 'int64']).columns:
                # Replace negative values with NaN
                df.loc[df[col] < 0, col] = pd.NA
            
            # Remove rows where all values are NaN
            df = df.dropna(how='all')
            
            # Save the cleaned data
            output_path = output_file if output_file else input_file
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Data cleaned and saved to {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error cleaning data in {input_file}: {e}")
        return False

def export_to_json(input_file: str, output_file: str) -> bool:
    """
    Export CSV data to JSON format.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output JSON file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return False
            
        with file_lock(input_file):
            # Read the CSV file
            df = pd.read_csv(input_file, encoding='utf-8')
            
            # Convert to JSON
            data = df.to_dict('records')
            
            # Save as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data exported to JSON: {output_file}")
            return True
            
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return False