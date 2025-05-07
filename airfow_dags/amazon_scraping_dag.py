"""
Optimized Amazon Scraping DAG
This DAG coordinates the complete scraping process for Amazon products with:
- Parallelization for better performance
- Robust error handling and retries
- Incremental scraping to avoid redundant work
- Resource management to prevent IP blocking
- Comprehensive logging and monitoring
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from airflow.hooks.filesystem import FSHook

# Import your scraper modules
import sys
sys.path.append('/path/to/your/project')  # Replace with your actual project path
from scrapers.scraping import (
    get_category_filters, 
    get_products_from_category,
    get_product_details,
    get_product_reviews
)
from utils.file_utils import load_json, save_json, save_csv, load_csv
from utils.request_utils import get_random_user_agent, setup_proxy_rotation

# Default arguments for tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
    'start_date': datetime(2025, 5, 1),
    # Add connection timeout
    'pool': 'amazon_scraper_pool',  # Create this pool in Airflow UI with limited slots
}

# Create the DAG
dag = DAG(
    'amazon_product_scraper',
    default_args=default_args,
    description='Scrape Amazon products data incrementally with robust error handling',
    schedule_interval='0 0 * * *',  # Daily at midnight, adjust as needed
    catchup=False,
    max_active_runs=1,
    concurrency=16,  # Adjust based on your resources
    tags=['scraping', 'amazon'],
)

# Function to handle scraping categories
def scrape_categories(**kwargs):
    """Scrape category filters and store them"""
    categories = Variable.get("amazon_categories", deserialize_json=True, default=["electronics", "books"])
    results = {}
    
    for category in categories:
        category_filters = get_category_filters(category)
        results[category] = category_filters
    
    # Save results to a timestamped file
    timestamp = datetime.now().strftime("%Y%m%d")
    file_path = f"{kwargs['data_dir']}/amazon_filters_{timestamp}.json"
    save_json(results, file_path)
    
    # Also save to the main file for reference by other tasks
    save_json(results, f"{kwargs['data_dir']}/amazon_filters.json")
    
    return file_path

# Function to get product listings from categories (paginated)
def scrape_product_listings(**kwargs):
    """Scrape product listings from each category"""
    category = kwargs['category']
    ti = kwargs['ti']
    data_dir = kwargs['data_dir']
    
    # Load existing products to implement incremental scraping
    existing_products = {}
    try:
        existing_products_path = f"{data_dir}/amazon_products_all.csv"
        if os.path.exists(existing_products_path):
            existing_df = load_csv(existing_products_path)
            existing_products = {row['product_id']: row for _, row in existing_df.iterrows()}
    except Exception as e:
        print(f"Warning: Could not load existing products: {e}")
    
    # Get filters
    filters = load_json(f"{data_dir}/amazon_filters.json")
    category_filters = filters.get(category, {})
    
    # Configure pagination
    max_pages = int(Variable.get("max_pages_per_category", default=5))
    
    # Get product listings
    new_products = get_products_from_category(
        category, 
        max_pages=max_pages, 
        filters=category_filters,
        existing_products=existing_products  # Pass existing products to avoid duplicates
    )
    
    # Save category-specific results
    timestamp = datetime.now().strftime("%Y%m%d")
    file_path = f"{data_dir}/amazon_products_{category}_{timestamp}.csv"
    save_csv(new_products, file_path)
    
    # Return the list of new product IDs for detailed scraping
    return [p['product_id'] for p in new_products]

# Function to scrape details for a batch of products
def scrape_product_details(**kwargs):
    """Scrape detailed information for a batch of products"""
    ti = kwargs['ti']
    data_dir = kwargs['data_dir']
    batch_index = kwargs['batch_index']
    
    # Get all product IDs from upstream tasks
    all_product_ids = []
    categories = Variable.get("amazon_categories", deserialize_json=True, default=["electronics", "books"])
    for category in categories:
        task_id = f"get_product_listings.get_listings_{category}"
        category_product_ids = ti.xcom_pull(task_ids=task_id) or []
        all_product_ids.extend(category_product_ids)
    
    # Load existing product details to implement incremental scraping
    existing_details = {}
    try:
        existing_details_path = f"{data_dir}/product_information.csv"
        if os.path.exists(existing_details_path):
            existing_df = load_csv(existing_details_path)
            existing_details = {row['product_id']: row for _, row in existing_df.iterrows()}
    except Exception as e:
        print(f"Warning: Could not load existing product details: {e}")
    
    # Split products into batches for parallel processing
    batch_size = int(Variable.get("product_batch_size", default=20))
    total_batches = (len(all_product_ids) + batch_size - 1) // batch_size
    
    if batch_index >= total_batches:
        print(f"Batch index {batch_index} exceeds total batches {total_batches}. Skipping.")
        return []
    
    start_idx = batch_index * batch_size
    end_idx = min((batch_index + 1) * batch_size, len(all_product_ids))
    batch_product_ids = all_product_ids[start_idx:end_idx]
    
    # Filter out products we already have detailed information for
    new_product_ids = [pid for pid in batch_product_ids if pid not in existing_details]
    
    if not new_product_ids:
        print(f"No new products to process in batch {batch_index}. Skipping.")
        return []
    
    # Setup proxy rotation and random user agents
    setup_proxy_rotation()
    
    # Get product details with rate limiting and retries
    product_details = []
    for product_id in new_product_ids:
        try:
            details = get_product_details(product_id)
            if details:
                product_details.append(details)
                # Add a small delay between requests to avoid rate limiting
                time.sleep(float(Variable.get("request_delay_seconds", default=1.5)))
        except Exception as e:
            print(f"Error scraping product {product_id}: {e}")
    
    # Save this batch's results
    if product_details:
        timestamp = datetime.now().strftime("%Y%m%d")
        file_path = f"{data_dir}/product_details_batch_{batch_index}_{timestamp}.csv"
        save_csv(product_details, file_path)
    
    # Return the product IDs that were successfully processed
    return [p['product_id'] for p in product_details]

# Function to scrape reviews for products
def scrape_product_reviews(**kwargs):
    """Scrape reviews for products"""
    ti = kwargs['ti']
    data_dir = kwargs['data_dir']
    batch_index = kwargs['batch_index']
    
    # Get successfully processed product IDs from the details task
    task_id = f"get_product_details.get_details_batch_{batch_index}"
    product_ids = ti.xcom_pull(task_ids=task_id) or []
    
    if not product_ids:
        print(f"No products to get reviews for in batch {batch_index}. Skipping.")
        return
    
    # Load existing reviews to implement incremental scraping
    existing_reviews = {}
    try:
        existing_reviews_path = f"{data_dir}/amazon_reviews.json"
        if os.path.exists(existing_reviews_path):
            existing_reviews = load_json(existing_reviews_path)
    except Exception as e:
        print(f"Warning: Could not load existing reviews: {e}")
    
    # Setup proxy rotation and random user agents
    setup_proxy_rotation()
    
    # Get reviews with rate limiting
    all_reviews = {}
    for product_id in product_ids:
        # Skip if we already have recent reviews for this product
        if product_id in existing_reviews:
            last_scraped = existing_reviews[product_id].get('last_scraped')
            if last_scraped:
                last_scraped_date = datetime.strptime(last_scraped, "%Y-%m-%d")
                days_since_scrape = (datetime.now() - last_scraped_date).days
                # Only re-scrape reviews if it's been more than a week
                if days_since_scrape < 7:
                    print(f"Skipping reviews for {product_id}, scraped {days_since_scrape} days ago")
                    all_reviews[product_id] = existing_reviews[product_id]
                    continue
        
        try:
            reviews = get_product_reviews(product_id)
            if reviews:
                all_reviews[product_id] = {
                    'reviews': reviews,
                    'last_scraped': datetime.now().strftime("%Y-%m-%d")
                }
                # Add a small delay between requests
                time.sleep(float(Variable.get("request_delay_seconds", default=1.5)))
        except Exception as e:
            print(f"Error scraping reviews for product {product_id}: {e}")
    
    # Save this batch's results
    if all_reviews:
        timestamp = datetime.now().strftime("%Y%m%d")
        file_path = f"{data_dir}/reviews_batch_{batch_index}_{timestamp}.json"
        save_json(all_reviews, file_path)
    
    return

# Function to merge all batched files into the main datasets
def merge_results(**kwargs):
    """Merge all batch results into main datasets"""
    data_dir = kwargs['data_dir']
    ti = kwargs['ti']
    
    # Merge product details
    import pandas as pd
    import glob
    
    # Find all batch files
    detail_batch_files = glob.glob(f"{data_dir}/product_details_batch_*_*.csv")
    review_batch_files = glob.glob(f"{data_dir}/reviews_batch_*_*.json")
    
    # Merge product details
    all_details = []
    for file in detail_batch_files:
        try:
            details = load_csv(file)
            all_details.extend(details)
        except Exception as e:
            print(f"Error loading detail file {file}: {e}")
    
    # Load existing details and merge
    try:
        existing_details_path = f"{data_dir}/product_information.csv"
        if os.path.exists(existing_details_path):
            existing_details = load_csv(existing_details_path)
            
            # Create dict of product_id -> row for efficient lookup
            existing_dict = {row['product_id']: row for _, row in pd.DataFrame(existing_details).iterrows()}
            new_dict = {row['product_id']: row for row in all_details}
            
            # Merge existing with new, preferring new data
            merged_dict = {**existing_dict, **new_dict}
            all_details = list(merged_dict.values())
    except Exception as e:
        print(f"Warning: Could not merge with existing details: {e}")
    
    # Save merged details
    if all_details:
        save_csv(all_details, f"{data_dir}/product_information.csv")
    
    # Merge reviews
    all_reviews = {}
    for file in review_batch_files:
        try:
            reviews = load_json(file)
            all_reviews.update(reviews)
        except Exception as e:
            print(f"Error loading review file {file}: {e}")
    
    # Load existing reviews and merge
    try:
        existing_reviews_path = f"{data_dir}/amazon_reviews.json"
        if os.path.exists(existing_reviews_path):
            existing_reviews = load_json(existing_reviews_path)
            # Merge existing with new, preferring new data
            merged_reviews = {**existing_reviews, **all_reviews}
            all_reviews = merged_reviews
    except Exception as e:
        print(f"Warning: Could not merge with existing reviews: {e}")
    
    # Save merged reviews
    if all_reviews:
        save_json(all_reviews, f"{data_dir}/amazon_reviews.json")
    
    # Clean up batch files if needed
    if Variable.get("cleanup_batch_files", default="False") == "True":
        for file in detail_batch_files + review_batch_files:
            try:
                os.remove(file)
            except Exception as e:
                print(f"Error removing batch file {file}: {e}")
    
    return

# Function to check data freshness and trigger scraping
def check_data_freshness(**kwargs):
    """Determine if a full scrape is needed or just an incremental update"""
    data_dir = kwargs['data_dir']
    
    # Check when the last full scrape was performed
    last_scrape_marker = f"{data_dir}/last_full_scrape.txt"
    perform_full_scrape = True
    
    if os.path.exists(last_scrape_marker):
        with open(last_scrape_marker, 'r') as f:
            last_scrape_date = datetime.strptime(f.read().strip(), "%Y-%m-%d")
            days_since_scrape = (datetime.now() - last_scrape_date).days
            
            # If it's been less than the threshold, do an incremental scrape
            if days_since_scrape < int(Variable.get("full_scrape_interval_days", default=7)):
                perform_full_scrape = False
    
    # Update the marker file
    with open(last_scrape_marker, 'w') as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))
    
    return "full_scrape" if perform_full_scrape else "incremental_scrape"

# Define data directory
data_dir = "{{ dag_run.conf['data_dir'] if dag_run.conf and 'data_dir' in dag_run.conf else '/path/to/your/project/data' }}"

# Start of the pipeline
start = DummyOperator(
    task_id='start',
    dag=dag,
)

# Check if we need full or incremental scrape
check_freshness = PythonOperator(
    task_id='check_data_freshness',
    python_callable=check_data_freshness,
    op_kwargs={'data_dir': data_dir},
    dag=dag,
)

# Branch task to decide between full and incremental scrape
from airflow.operators.python import BranchPythonOperator

def decide_scrape_path(**kwargs):
    ti = kwargs['ti']
    scrape_type = ti.xcom_pull(task_ids='check_data_freshness')
    if scrape_type == "full_scrape":
        return "scrape_categories"
    else:
        return "skip_categories_scrape"

branch_op = BranchPythonOperator(
    task_id='decide_scrape_path',
    python_callable=decide_scrape_path,
    dag=dag,
)

skip_categories = DummyOperator(
    task_id='skip_categories_scrape',
    dag=dag,
)

# Task to scrape categories
scrape_categories_task = PythonOperator(
    task_id='scrape_categories',
    python_callable=scrape_categories,
    op_kwargs={'data_dir': data_dir},
    dag=dag,
)

# Join paths
join_paths = DummyOperator(
    task_id='join_paths',
    trigger_rule='one_success',
    dag=dag,
)

# Task group for product listings
with TaskGroup(group_id="get_product_listings", dag=dag) as get_product_listings:
    categories = Variable.get("amazon_categories", deserialize_json=True, default=["electronics", "books"])
    
    listing_tasks = []
    for category in categories:
        get_listings = PythonOperator(
            task_id=f"get_listings_{category}",
            python_callable=scrape_product_listings,
            op_kwargs={
                'category': category,
                'data_dir': data_dir
            },
            dag=dag,
        )
        listing_tasks.append(get_listings)

# Calculate number of batches dynamically
def calculate_batches(**kwargs):
    ti = kwargs['ti']
    
    # Count total products from all categories
    total_products = 0
    categories = Variable.get("amazon_categories", deserialize_json=True, default=["electronics", "books"])
    for category in categories:
        task_id = f"get_product_listings.get_listings_{category}"
        category_product_ids = ti.xcom_pull(task_ids=task_id) or []
        total_products += len(category_product_ids)
    
    batch_size = int(Variable.get("product_batch_size", default=20))
    total_batches = (total_products + batch_size - 1) // batch_size
    
    return {"total_batches": max(1, total_batches)}  # At least 1 batch

calculate_batches_task = PythonOperator(
    task_id='calculate_batches',
    python_callable=calculate_batches,
    dag=dag,
)

# Task group for product details
with TaskGroup(group_id="get_product_details", dag=dag) as get_product_details:
    def create_dynamic_tasks(**kwargs):
        ti = kwargs['ti']
        batch_info = ti.xcom_pull(task_ids='calculate_batches')
        total_batches = batch_info['total_batches']
        
        detail_tasks = []
        for batch_index in range(total_batches):
            detail_task = PythonOperator(
                task_id=f"get_details_batch_{batch_index}",
                python_callable=scrape_product_details,
                op_kwargs={
                    'batch_index': batch_index,
                    'data_dir': data_dir
                },
                dag=dag,
            )
            detail_tasks.append(detail_task)
        
        return detail_tasks
    
    # This is a placeholder - in a production environment,
    # you would likely use a dynamic task mapping feature
    # For this example, we'll create a fixed number of batch tasks
    max_batches = int(Variable.get("max_detail_batches", default=10))
    detail_tasks = []
    
    for batch_index in range(max_batches):
        detail_task = PythonOperator(
            task_id=f"get_details_batch_{batch_index}",
            python_callable=scrape_product_details,
            op_kwargs={
                'batch_index': batch_index,
                'data_dir': data_dir
            },
            dag=dag,
        )
        detail_tasks.append(detail_task)

# Task group for product reviews
with TaskGroup(group_id="get_product_reviews", dag=dag) as get_product_reviews:
    max_batches = int(Variable.get("max_detail_batches", default=10))
    review_tasks = []
    
    for batch_index in range(max_batches):
        review_task = PythonOperator(
            task_id=f"get_reviews_batch_{batch_index}",
            python_callable=scrape_product_reviews,
            op_kwargs={
                'batch_index': batch_index,
                'data_dir': data_dir
            },
            dag=dag,
        )
        review_tasks.append(review_task)

# Merge results task
merge_task = PythonOperator(
    task_id='merge_results',
    python_callable=merge_results,
    op_kwargs={'data_dir': data_dir},
    dag=dag,
)

# End task
end = DummyOperator(
    task_id='end',
    dag=dag,
)

# Define task dependencies
start >> check_freshness >> branch_op
branch_op >> scrape_categories_task >> join_paths
branch_op >> skip_categories >> join_paths
join_paths >> get_product_listings >> calculate_batches_task >> get_product_details >> get_product_reviews >> merge_task >> end