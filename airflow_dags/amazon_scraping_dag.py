"""
Optimized Amazon Scraping DAG with advanced error handling, monitoring, and efficient processing.
"""

from datetime import datetime, timedelta
import os
import json
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowSkipException
from airflow.utils.session import create_session
from airflow.models.taskinstance import TaskInstance

import sys
import os
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import our custom modules
from scrapers.scraping import run_full_scrape
from scrapers.categories import scrape_amazon_filters
from scrapers.amazon_details_scraper import scrape_product_details
from scrapers.commentaire import scrape_reviews
from utils.file_utils import merge_csv_files, clean_data, export_to_json
from utils.scraping_logger import get_logger, scraper_logger
from utils.scraping_metrics import metrics, time_operation

# Configure logger
logger = get_logger('airflow_dag')

# Enhanced default arguments for all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 5,  # Increased retries
    'retry_delay': timedelta(minutes=2),  # Shorter retry delay
    'retry_exponential_backoff': True,  # Enable exponential backoff
    'max_retry_delay': timedelta(minutes=30),  # Maximum retry delay
    'execution_timeout': timedelta(hours=2),
    'start_date': datetime(2023, 1, 1),
    'pool': 'scraper_pool',
    'priority_weight': 10,
    'wait_for_downstream': True,  # Wait for downstream tasks to complete
    'trigger_rule': TriggerRule.ALL_SUCCESS
}

# Create DAG with enhanced configuration
dag = DAG(
    'optimized_amazon_scraping',
    default_args=default_args,
    description='Optimized Amazon product scraping pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False,
    max_active_runs=1,
    concurrency=12,  # Increased concurrency
    tags=['scraping', 'amazon', 'optimized'],
)

# Enhanced configuration with retry and rate limiting settings
try:
    config = Variable.get("amazon_scraper_config", deserialize_json=True)
except:
    config = {
        'categories': ['electronics', 'computers', 'smart-home'],
        'max_products_per_category': 100,
        'max_pages_per_category': 5,
        'scrape_reviews': True,
        'max_reviews_per_product': 50,
        'user_agent_rotation': True,
        'proxy_rotation': True,
        'request_delay': 2.0,  # Increased delay
        'max_retries': 5,
        'timeout': 30,
        'output_directory': 'data',
        'export_formats': ['csv', 'json'],
        'batch_size': 10,  # Process products in batches
        'max_workers': 4,  # Number of parallel workers
        'rate_limit': {
            'requests_per_second': 2,
            'burst_size': 5
        },
        'retry_config': {
            'max_retries': 5,
            'base_delay': 2,
            'max_delay': 30,
            'exponential_base': 2
        }
    }

# Rate limiting decorator
def rate_limit(requests_per_second: float, burst_size: int):
    """Rate limiting decorator for API calls."""
    min_interval = 1.0 / requests_per_second
    last_call_time = 0
    tokens = burst_size

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call_time, tokens
            current_time = time.time()
            
            # Add tokens based on time passed
            time_passed = current_time - last_call_time
            tokens = min(burst_size, tokens + time_passed * requests_per_second)
            
            if tokens < 1:
                sleep_time = (1 - tokens) / requests_per_second
                time.sleep(sleep_time)
                tokens = 1
            
            tokens -= 1
            last_call_time = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Enhanced retry decorator
def retry_with_exponential_backoff(max_retries: int, base_delay: int, max_delay: int):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    
                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    logger.warning(f"Retry {retries}/{max_retries} after {delay}s due to: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# Enhanced task function definitions
@logger.airflow_task_logger('check_environment')
def check_environment(**kwargs):
    """Enhanced environment check with detailed validation."""
    try:
        # Check required directories
        required_dirs = ['data', 'logs', 'scrapers', 'utils']
        for directory in required_dirs:
            if not os.path.isdir(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")

        # Check required modules
        required_modules = ['requests', 'bs4', 'pandas', 'selenium']
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            raise ImportError(f"Missing required modules: {', '.join(missing_modules)}")

        # Check file permissions
        for directory in required_dirs:
            if not os.access(directory, os.W_OK):
                raise PermissionError(f"No write permission for directory: {directory}")

        logger.info("Environment check passed")
        return True
    except Exception as e:
        logger.error(f"Environment check failed: {str(e)}")
        raise

@logger.airflow_task_logger('prepare_scraping')
def prepare_scraping(**kwargs):
    """Enhanced preparation with better error handling and validation."""
    try:
        ti = kwargs['ti']
        execution_date = kwargs['execution_date']
        
        # Create unique run ID
        run_id = execution_date.strftime('%Y%m%d_%H%M%S')
        
        # Validate categories
        categories = config['categories']
        if not categories:
            raise ValueError("No categories specified in configuration")
        
        # Enhanced run configuration
        run_config = {
            'run_id': run_id,
            'categories': categories,
            'max_products_per_category': config['max_products_per_category'],
            'max_pages_per_category': config['max_pages_per_category'],
            'scrape_reviews': config['scrape_reviews'],
            'timestamp': execution_date.isoformat(),
            'output_files': {
                'products': f"data/{run_id}_products.csv",
                'reviews': f"data/{run_id}_reviews.json",
                'categories': f"data/{run_id}_categories.json"
            },
            'batch_size': config['batch_size'],
            'max_workers': config['max_workers'],
            'rate_limit': config['rate_limit']
        }
        
        # Validate and create output files
        for output_file in run_config['output_files'].values():
            directory = os.path.dirname(output_file)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(output_file, 'w') as f:
                if output_file.endswith('.json'):
                    f.write('{}')
                elif output_file.endswith('.csv'):
                    f.write('')
        
        # Push configuration to XCom
        ti.xcom_push(key='run_config', value=run_config)
        logger.info(f"Prepared scraping run: {run_id}")
        
        return run_config
    except Exception as e:
        logger.error(f"Prepare scraping failed: {str(e)}")
        raise

@logger.airflow_task_logger('scrape_category')
@time_operation('category_scrape')
@rate_limit(requests_per_second=2, burst_size=5)
@retry_with_exponential_backoff(max_retries=5, base_delay=2, max_delay=30)
def scrape_category(category, **kwargs):
    """Enhanced category scraping with rate limiting and retries."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        logger.info(f"Starting scrape for category: {category}")
        logger.set_context(category=category, custom_data={'run_id': run_config['run_id']})
        
        metrics.increment(f'category.{category}.started')
        metrics.start_timer(f'category_{category}')
        
        result = scrape_amazon_filters(
            category=category,
            max_pages=run_config['max_pages_per_category'],
            max_products=run_config['max_products_per_category'],
            output_file=run_config['output_files']['categories']
        )
        
        elapsed = metrics.stop_timer(f'category_{category}', 'category_scrape')
        metrics.increment(f'category.{category}.completed')
        
        logger.info(f"Completed scrape for category {category} in {elapsed:.2f}s")
        return result
    except Exception as e:
        metrics.record_error(f"category_scrape_{category}")
        logger.error(f"Error scraping category {category}: {str(e)}")
        raise

@logger.airflow_task_logger('scrape_product_details')
@time_operation('product_details')
def process_product_details(**kwargs):
    """Enhanced product details processing with parallel execution."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        # Load category results
        with open(run_config['output_files']['categories'], 'r') as f:
            category_data = json.load(f)
        
        # Collect product URLs
        product_urls = []
        for category, data in category_data.items():
            if 'product_urls' in data:
                product_urls.extend(data['product_urls'])
        
        logger.info(f"Found {len(product_urls)} products to scrape")
        metrics.set_gauge('total_products', len(product_urls))
        
        # Process products in parallel
        product_results = []
        with ThreadPoolExecutor(max_workers=run_config['max_workers']) as executor:
            future_to_url = {
                executor.submit(
                    retry_with_exponential_backoff(
                        max_retries=config['retry_config']['max_retries'],
                        base_delay=config['retry_config']['base_delay'],
                        max_delay=config['retry_config']['max_delay']
                    )(scrape_product_details),
                    url
                ): url for url in product_urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    product_data = future.result()
                    if product_data:
                        product_results.append(product_data)
                        metrics.increment('products_scraped')
                except Exception as e:
                    metrics.record_error('product_details')
                    logger.error(f"Error scraping product {url}: {str(e)}")
        
        # Save results
        if product_results:
            import pandas as pd
            df = pd.DataFrame(product_results)
            df.to_csv(run_config['output_files']['products'], index=False)
            logger.info(f"Saved {len(product_results)} products to {run_config['output_files']['products']}")
        
        metrics.set_gauge('products_scraped', len(product_results))
        return len(product_results)
    except Exception as e:
        metrics.record_error('process_product_details')
        logger.error(f"Error processing product details: {str(e)}")
        raise

@logger.airflow_task_logger('scrape_reviews')
@time_operation('reviews_scrape')
@rate_limit(requests_per_second=2, burst_size=5)
def process_reviews(**kwargs):
    """Enhanced review processing with rate limiting and parallel execution."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        # Load product data
        try:
            import pandas as pd
            products_df = pd.read_csv(run_config['output_files']['products'])
            product_urls = products_df['url'].tolist()
        except Exception as e:
            logger.warning(f"No product data found, skipping review scraping: {str(e)}")
            return 0
        
        logger.info(f"Found {len(product_urls)} products for review scraping")
        metrics.set_gauge('total_products_for_reviews', len(product_urls))
        
        # Process reviews in parallel
        all_reviews = []
        with ThreadPoolExecutor(max_workers=run_config['max_workers']) as executor:
            future_to_url = {
                executor.submit(
                    retry_with_exponential_backoff(
                        max_retries=config['retry_config']['max_retries'],
                        base_delay=config['retry_config']['base_delay'],
                        max_delay=config['retry_config']['max_delay']
                    )(scrape_reviews),
                    url,
                    config['max_reviews_per_product']
                ): url for url in product_urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    reviews = future.result()
                    if reviews:
                        all_reviews.extend(reviews)
                        metrics.increment('reviews_scraped', len(reviews))
                except Exception as e:
                    metrics.record_error('review_scrape')
                    logger.error(f"Error scraping reviews for {url}: {str(e)}")
        
        # Save reviews
        if all_reviews:
            with open(run_config['output_files']['reviews'], 'w') as f:
                json.dump(all_reviews, f, indent=2)
            logger.info(f"Saved {len(all_reviews)} reviews to {run_config['output_files']['reviews']}")
        
        metrics.set_gauge('total_reviews', len(all_reviews))
        return len(all_reviews)
    except Exception as e:
        metrics.record_error('process_reviews')
        logger.error(f"Error processing reviews: {str(e)}")
        raise

@logger.airflow_task_logger('post_process_data')
def post_process_data(**kwargs):
    """Enhanced post-processing with better data validation and error handling."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        logger.info("Starting post-processing of scraped data")
        
        # Load and validate data
        try:
            import pandas as pd
            products_df = pd.read_csv(run_config['output_files']['products'])
            
            # Calculate product statistics
            product_stats = {
                'total_products': len(products_df),
                'categories': products_df['category'].value_counts().to_dict(),
                'price_stats': {
                    'min': products_df['price'].min(),
                    'max': products_df['price'].max(),
                    'mean': products_df['price'].mean(),
                    'median': products_df['price'].median()
                }
            }
        except Exception as e:
            logger.warning(f"Could not calculate product statistics: {str(e)}")
            product_stats = {}
        
        # Load and process reviews
        try:
            with open(run_config['output_files']['reviews'], 'r') as f:
                reviews = json.load(f)
            
            review_stats = {
                'total_reviews': len(reviews),
                'average_rating': sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0,
                'rating_distribution': pd.Series([r['rating'] for r in reviews]).value_counts().to_dict()
            }
        except Exception as e:
            logger.warning(f"Could not calculate review statistics: {str(e)}")
            review_stats = {'review_count': 0}
        
        # Combine statistics
        statistics = {
            'products': product_stats,
            'reviews': review_stats,
            'timestamp': run_config['timestamp'],
            'run_id': run_config['run_id']
        }
        
        # Save statistics
        stats_file = f"data/{run_config['run_id']}_statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(statistics, f, indent=2)
        
        logger.info(f"Generated statistics: {json.dumps(review_stats)}")
        return True
    except Exception as e:
        metrics.record_error('post_process_data')
        logger.error(f"Error in post-processing: {str(e)}")
        raise

@logger.airflow_task_logger('generate_report')
def generate_report(**kwargs):
    """Enhanced report generation with better formatting and error handling."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        # Load statistics
        stats_file = f"data/{run_config['run_id']}_statistics.json"
        with open(stats_file, 'r') as f:
            statistics = json.load(f)
        
        # Generate JSON report
        report = {
            'run_id': run_config['run_id'],
            'timestamp': run_config['timestamp'],
            'statistics': statistics,
            'categories_scraped': run_config['categories'],
            'output_files': run_config['output_files']
        }
        
        # Save JSON report
        json_report_file = f"data/{run_config['run_id']}_report.json"
        with open(json_report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Generated report: {json_report_file}")
        
        # Generate text report
        text_report = f"""Amazon Scraping Report
====================
Run ID: {run_config['run_id']}
Timestamp: {run_config['timestamp']}

Categories Scraped:
{chr(10).join(f'- {cat}' for cat in run_config['categories'])}

Product Statistics:
-----------------
Total Products: {statistics['products'].get('total_products', 0)}
Categories: {chr(10).join(f'  - {cat}: {count}' for cat, count in statistics['products'].get('categories', {}).items())}

Price Statistics:
---------------
Min Price: {statistics['products'].get('price_stats', {}).get('min', 'N/A')}
Max Price: {statistics['products'].get('price_stats', {}).get('max', 'N/A')}
Average Price: {statistics['products'].get('price_stats', {}).get('mean', 'N/A')}
Median Price: {statistics['products'].get('price_stats', {}).get('median', 'N/A')}

Review Statistics:
----------------
Total Reviews: {statistics['reviews'].get('total_reviews', 0)}
Average Rating: {statistics['reviews'].get('average_rating', 'N/A')}

Output Files:
------------
{chr(10).join(f'- {file}' for file in run_config['output_files'].values())}
"""
        
        # Save text report
        text_report_file = f"data/{run_config['run_id']}_report.txt"
        with open(text_report_file, 'w') as f:
            f.write(text_report)
        logger.info(f"Generated text report: {text_report_file}")
        
        return True
    except Exception as e:
        metrics.record_error('generate_report')
        logger.error(f"Error generating report: {str(e)}")
        raise

@logger.airflow_task_logger('run_full_scraping')
@time_operation('full_scrape')
def execute_full_scrape(**kwargs):
    """Enhanced full scraping execution with better error handling and monitoring."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        logger.info("Starting full scraping process")
        metrics.start_timer('full_scrape')
        
        # Execute the full scrape
        result = run_full_scrape(
            categories=run_config['categories'],
            max_products=run_config['max_products_per_category'],
            max_pages=run_config['max_pages_per_category'],
            output_file=run_config['output_files']['products']
        )
        
        # Record completion
        elapsed = metrics.stop_timer('full_scrape', 'full_scrape')
        logger.info(f"Full scraping completed successfully in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        metrics.record_error('full_scrape')
        logger.error(f"Error in full scraping: {str(e)}")
        raise

# Task definitions
with dag:
    # Initial tasks
    check_env = PythonOperator(
        task_id='check_environment',
        python_callable=check_environment,
        provide_context=True
    )
    
    prepare = PythonOperator(
        task_id='prepare_scraping',
        python_callable=prepare_scraping,
        provide_context=True
    )
    
    # Category scraping tasks
    with TaskGroup(group_id='scrape_categories') as category_group:
        category_tasks = {}
        for category in config['categories']:
            category_tasks[category] = PythonOperator(
                task_id=f'scrape_category_{category}',
                python_callable=scrape_category,
                op_kwargs={'category': category},
                provide_context=True
            )
    
    # Product details task
    product_details = PythonOperator(
        task_id='scrape_product_details',
        python_callable=process_product_details,
        provide_context=True
    )
    
    # Reviews task
    reviews = PythonOperator(
        task_id='scrape_reviews',
        python_callable=process_reviews,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_SUCCESS
    )
    
    # Post-processing task
    post_process = PythonOperator(
        task_id='post_process_data',
        python_callable=post_process_data,
        provide_context=True
    )
    
    # Report generation task
    generate = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
        provide_context=True
    )
    
    # Completion task
    completion = DummyOperator(
        task_id='completion',
        trigger_rule=TriggerRule.ALL_SUCCESS
    )
    
    # Set task dependencies
    check_env >> prepare >> category_group >> product_details >> reviews >> post_process >> generate >> completion