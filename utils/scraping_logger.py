"""
Comprehensive logging utility for Amazon scraping operations.
Provides structured logging with different log levels, rotation policies,
and integration with Airflow's logging system.
"""

import os
import json
import time
import logging
import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import threading
from functools import wraps
import socket
import traceback

# Constants
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
JSON_FORMAT = '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "file": "%(filename)s", "line": %(lineno)d, "message": "%(message)s"}'

# Thread-local storage for request context tracking
_thread_local = threading.local()

class ScrapingLogger:
    """
    Advanced logger for scraping operations with multiple output formats,
    rotation policies, and context tracking.
    """
    
    def __init__(self, logger_name='scraping', 
                 log_level='INFO',
                 log_to_console=True, 
                 log_to_file=True,
                 log_directory='logs',
                 log_format='standard',  # 'standard' or 'json'
                 rotation_policy='size',  # 'size' or 'time'
                 max_bytes=10 * 1024 * 1024,  # 10 MB
                 backup_count=5,
                 rotation_interval='midnight'):
        """
        Initialize the scraping logger with customizable settings.
        
        Args:
            logger_name: Name of the logger instance
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_console: Whether to output logs to console
            log_to_file: Whether to output logs to file
            log_directory: Directory to store log files
            log_format: Format of log messages ('standard' or 'json')
            rotation_policy: Log rotation policy ('size' or 'time')
            max_bytes: Maximum log file size before rotation (for 'size' policy)
            backup_count: Number of backup files to keep
            rotation_interval: When to rotate logs (for 'time' policy)
        """
        self.logger_name = logger_name
        self.log_level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
        self.log_directory = log_directory
        self.log_format = DEFAULT_FORMAT if log_format == 'standard' else JSON_FORMAT
        
        # Create logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(self.log_format)
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_to_file:
            # Create log directory if it doesn't exist
            os.makedirs(log_directory, exist_ok=True)
            
            log_file = os.path.join(log_directory, f"{logger_name}.log")
            
            if rotation_policy == 'size':
                file_handler = RotatingFileHandler(
                    log_file, 
                    maxBytes=max_bytes,
                    backupCount=backup_count
                )
            else:  # time-based rotation
                file_handler = TimedRotatingFileHandler(
                    log_file,
                    when=rotation_interval,
                    backupCount=backup_count
                )
            
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Initialize context for the current thread
        self.reset_context()
        
        self.hostname = socket.gethostname()
        
    def reset_context(self):
        """Reset the thread-local context data."""
        _thread_local.context = {
            'session_id': None,
            'request_id': None,
            'url': None,
            'product_id': None,
            'category': None,
            'start_time': None,
            'custom_data': {}
        }
    
    def set_context(self, **kwargs):
        """Set context values for the current thread."""
        for key, value in kwargs.items():
            if key in _thread_local.context or key == 'custom_data':
                if key == 'custom_data' and isinstance(value, dict):
                    _thread_local.context['custom_data'].update(value)
                else:
                    _thread_local.context[key] = value
    
    def get_context(self):
        """Get the current context dictionary."""
        return _thread_local.context.copy()
    
    def _format_with_context(self, message):
        """Format message with current context."""
        context = self.get_context()
        # Only include non-None context values
        context_str = {k: v for k, v in context.items() if v is not None and k != 'custom_data'}
        
        # Add custom data if any
        if context['custom_data']:
            context_str.update(context['custom_data'])
        
        # If context is empty, just return the original message
        if not context_str:
            return message
            
        # Convert context to string representation
        try:
            ctx_msg = f"{message} | Context: {json.dumps(context_str)}"
        except TypeError:
            # If JSON serialization fails, fall back to string representation
            ctx_msg = f"{message} | Context: {str(context_str)}"
            
        return ctx_msg
    
    def debug(self, message, *args, **kwargs):
        """Log a debug message with context."""
        self.logger.debug(self._format_with_context(message), *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """Log an info message with context."""
        self.logger.info(self._format_with_context(message), *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Log a warning message with context."""
        self.logger.warning(self._format_with_context(message), *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """Log an error message with context."""
        self.logger.error(self._format_with_context(message), *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """Log a critical message with context."""
        self.logger.critical(self._format_with_context(message), *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        """Log an exception message with context and stack trace."""
        self.logger.exception(self._format_with_context(message), *args, **kwargs)
    
    def timing(self, operation=None):
        """
        Decorator to log the execution time of functions.
        
        Usage:
            @logger.timing('scrape_product')
            def scrape_product(url):
                # function body
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation or func.__name__
                start_time = time.time()
                self.set_context(start_time=start_time)
                
                try:
                    # Log start of operation
                    self.debug(f"Starting {op_name}")
                    result = func(*args, **kwargs)
                    # Log successful completion
                    elapsed = time.time() - start_time
                    self.info(f"Completed {op_name} in {elapsed:.2f} seconds")
                    return result
                except Exception as e:
                    # Log exception details
                    elapsed = time.time() - start_time
                    self.error(f"Failed {op_name} after {elapsed:.2f} seconds: {str(e)}")
                    self.debug(f"Exception traceback: {traceback.format_exc()}")
                    raise
                finally:
                    # Clean up context
                    self.set_context(start_time=None)
            
            return wrapper
        return decorator
    
    def log_request(self, url=None, session_id=None, request_id=None):
        """
        Decorator to log HTTP request details.
        
        Usage:
            @logger.log_request()
            def fetch_page(url):
                # function body
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract URL from args or kwargs if not provided directly
                _url = url
                if _url is None:
                    if args and isinstance(args[0], str) and (args[0].startswith('http://') or args[0].startswith('https://')):
                        _url = args[0]
                    elif 'url' in kwargs:
                        _url = kwargs['url']
                
                # Generate IDs if not provided
                _session_id = session_id or f"session_{int(time.time())}"
                _request_id = request_id or f"req_{int(time.time()*1000)}"
                
                # Set context
                self.set_context(
                    url=_url,
                    session_id=_session_id,
                    request_id=_request_id
                )
                
                start_time = time.time()
                
                try:
                    # Log request start
                    self.debug(f"Sending request to {_url}")
                    result = func(*args, **kwargs)
                    # Log request success
                    elapsed = time.time() - start_time
                    self.info(f"Request successful in {elapsed:.2f} seconds")
                    return result
                except Exception as e:
                    # Log request failure
                    elapsed = time.time() - start_time
                    self.error(f"Request failed after {elapsed:.2f} seconds: {str(e)}")
                    raise
                finally:
                    # Clean up URL from context
                    self.set_context(url=None)
            
            return wrapper
        return decorator
    
    def log_product_scrape(self, product_id=None, category=None):
        """
        Decorator to log product scraping activity.
        
        Usage:
            @logger.log_product_scrape(category='electronics')
            def scrape_product_details(product_id):
                # function body
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract product ID from args or kwargs if not provided directly
                _product_id = product_id
                if _product_id is None:
                    if args and isinstance(args[0], str):
                        _product_id = args[0]
                    elif 'product_id' in kwargs:
                        _product_id = kwargs['product_id']
                
                # Extract category from kwargs if not provided directly
                _category = category
                if _category is None and 'category' in kwargs:
                    _category = kwargs['category']
                
                # Set context
                self.set_context(
                    product_id=_product_id,
                    category=_category
                )
                
                try:
                    # Log start of product scraping
                    self.info(f"Scraping product {_product_id}")
                    result = func(*args, **kwargs)
                    # Log successful product scraping
                    self.info(f"Successfully scraped product {_product_id}")
                    return result
                except Exception as e:
                    # Log product scraping failure
                    self.error(f"Failed to scrape product {_product_id}: {str(e)}")
                    raise
                finally:
                    # Clean up product context
                    self.set_context(product_id=None, category=None)
            
            return wrapper
        return decorator

    def log_performance_stats(self, stats):
        """
        Log performance statistics in a structured way.
        
        Args:
            stats (dict): Dictionary containing performance statistics
        """
        stats_str = json.dumps(stats)
        self.info(f"Performance stats: {stats_str}")
    
    def airflow_task_logger(self, task_id):
        """
        Create a specialized logger for Airflow tasks.
        
        Args:
            task_id (str): The Airflow task ID
            
        Returns:
            A decorator that logs Airflow task execution
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.set_context(
                    custom_data={
                        'airflow_task_id': task_id,
                        'execution_date': datetime.datetime.now().isoformat()
                    }
                )
                
                self.info(f"Starting Airflow task: {task_id}")
                
                try:
                    result = func(*args, **kwargs)
                    self.info(f"Successfully completed Airflow task: {task_id}")
                    return result
                except Exception as e:
                    self.error(f"Airflow task failed: {task_id} - {str(e)}")
                    self.exception("Task exception details")
                    raise
                finally:
                    # Clean up airflow context
                    self.set_context(custom_data={})
            
            return wrapper
        return decorator

# Create a default instance of the logger
scraper_logger = ScrapingLogger(
    logger_name='amazon_scraper',
    log_level='INFO',
    log_format='json',  # Use JSON format for better parsing
    rotation_policy='time'  # Rotate logs daily
)

# Function to get a logger instance with custom settings
def get_logger(name=None, **kwargs):
    """
    Get a logger instance with custom settings.
    
    Args:
        name (str, optional): Logger name suffix
        **kwargs: Additional settings to override defaults
        
    Returns:
        ScrapingLogger: Configured logger instance
    """
    logger_name = f"amazon_scraper.{name}" if name else "amazon_scraper"
    return ScrapingLogger(logger_name=logger_name, **kwargs)