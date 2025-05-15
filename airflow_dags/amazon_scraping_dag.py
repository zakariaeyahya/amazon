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

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import our custom modules
from scrapers.scraping import run_full_scrape
from scrapers.categories import scrape_categories
from scrapers.amazon_details_scraper import scrape_product_details
from scrapers.commentaire import scrape_reviews
from utils.file_utils import merge_csv_files, clean_data, export_to_json
from utils.scraping_logger import get_logger, scraper_logger
from utils.scraping_metrics import metrics, time_operation

# Configure logger
logger = get_logger('airflow_dag')

# Default arguments for all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
    'start_date': datetime(2023, 1, 1),
    'pool': 'scraper_pool',  # Use a dedicated Airflow pool for scraping tasks
    'priority_weight': 10
}

# Create DAG
dag = DAG(
    'optimized_amazon_scraping',
    default_args=default_args,
    description='Optimized Amazon product scraping pipeline',
    schedule_interval=timedelta(days=1),  # Run daily
    catchup=False,
    max_active_runs=1,  # Only one run at a time
    concurrency=8,      # Maximum concurrent tasks
    tags=['scraping', 'amazon', 'optimized'],
)

# Get configuration from Airflow Variables or use defaults
try:
    config = Variable.get("amazon_scraper_config", deserialize_json=True)
except:
    # Default configuration
    config = {
        'categories': ['electronics', 'computers', 'smart-home'],
        'max_products_per_category': 100,
        'max_pages_per_category': 5,
        'scrape_reviews': True,
        'max_reviews_per_product': 50,
        'user_agent_rotation': True,
        'proxy_rotation': True,
        'request_delay': 1.5,  # seconds
        'max_retries': 5,
        'timeout': 30,  # seconds
        'output_directory': 'data',
        'export_formats': ['csv', 'json']
    }

# Task function definitions
@logger.airflow_task_logger('check_environment')
def check_environment(**kwargs):
    """Check if the environment is properly set up for scraping."""
    try:
        # Check if required directories exist
        required_dirs = ['data', 'logs', 'scrapers', 'utils']
        for directory in required_dirs:
            if not os.path.isdir(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")

        # Check if we have the necessary modules
        import requests
        import bs4
        import pandas
        
        logger.info("Environment check passed")
        return True
    except Exception as e:
        logger.error(f"Environment check failed: {str(e)}")
        raise

@logger.airflow_task_logger('prepare_scraping')
def prepare_scraping(**kwargs):
    """Prepare for scraping by setting up necessary files and configurations."""
    try:
        ti = kwargs['ti']
        execution_date = kwargs['execution_date']
        
        # Create a unique run ID based on the execution date
        run_id = execution_date.strftime('%Y%m%d_%H%M%S')
        
        # Determine which categories to scrape
        categories = config['categories']
        
        # Create a configuration for this run
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
            }
        }
        
        # Push the configuration to XCom for downstream tasks
        ti.xcom_push(key='run_config', value=run_config)
        
        # Log the configuration
        logger.info(f"Prepared scraping run: {run_id}")
        logger.debug(f"Run configuration: {json.dumps(run_config)}")
        
        # Create empty output files to ensure they exist
        for output_file in run_config['output_files'].values():
            with open(output_file, 'w') as f:
                if output_file.endswith('.json'):
                    f.write('{}')
                elif output_file.endswith('.csv'):
                    f.write('')
        
        return run_config
    except Exception as e:
        logger.error(f"Prepare scraping failed: {str(e)}")
        raise

@logger.airflow_task_logger('scrape_category')
@time_operation('category_scrape')
def scrape_category(category, **kwargs):
    """Scrape a single category."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        logger.info(f"Starting scrape for category: {category}")
        
        # Set context for logging
        logger.set_context(category=category, custom_data={'run_id': run_config['run_id']})
        
        # Start metrics for this category
        metrics.increment(f'category.{category}.started')
        metrics.start_timer(f'category_{category}')
        
        # Run the scraper for this category
        result = scrape_categories(
            category=category,
            max_pages=run_config['max_pages_per_category'],
            max_products=run_config['max_products_per_category'],
            output_file=run_config['output_files']['categories']
        )
        
        # Record time and success
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
    """Process product details for products found in categories."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        # Load the category results
        with open(run_config['output_files']['categories'], 'r') as f:
            category_data = json.load(f)
        
        # Get product URLs from the category data
        product_urls = []
        for category, data in category_data.items():
            if 'product_urls' in data:
                product_urls.extend(data['product_urls'])
        
        logger.info(f"Found {len(product_urls)} products to scrape")
        
        # Set up progress tracking
        metrics.set_gauge('total_products', len(product_urls))
        products_scraped = 0
        
        # Process each product
        product_results = []
        for url in product_urls:
            try:
                metrics.start_timer(f'product_{url}')
                
                # Scrape the product details
                product_data = scrape_product_details(url)
                
                if product_data:
                    product_results.append(product_data)
                    products_scraped += 1
                    metrics.increment('products_scraped')
                
                # Record time
                elapsed = metrics.stop_timer(f'product_{url}', 'product_details')
                logger.debug(f"Scraped product {url} in {elapsed:.2f}s")
                
            except Exception as e:
                metrics.record_error('product_details')
                logger.error(f"Error scraping product {url}: {str(e)}")
                # Continue with the next product
        
        # Save the results
        output_file = run_config['output_files']['products']
        if product_results:
            import pandas as pd
            df = pd.DataFrame(product_results)
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(product_results)} products to {output_file}")
        
        # Update metrics
        metrics.set_gauge('products_scraped', products_scraped)
        
        return products_scraped
    except Exception as e:
        metrics.record_error('process_product_details')
        logger.error(f"Error processing product details: {str(e)}")
        raise

@logger.airflow_task_logger('scrape_reviews')
@time_operation('reviews_scrape')
def process_reviews(**kwargs):
    """Scrape reviews for products if enabled."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        if not run_config['scrape_reviews']:
            logger.info("Review scraping disabled, skipping")
            return 0
        
        # Load the product data
        import pandas as pd
        try:
            products_df = pd.read_csv(run_config['output_files']['products'])
        except:
            logger.warning("No product data found, skipping review scraping")
            return 0
        
        if products_df.empty:
            logger.warning("No products to scrape reviews for")
            return 0
        
        # Get product URLs - assuming the URL column is named 'url'
        if 'url' not in products_df.columns:
            logger.error("Product data doesn't contain URL column")
            return 0
        
        product_urls = products_df['url'].tolist()
        logger.info(f"Found {len(product_urls)} products to scrape reviews for")
        
        # Set up progress tracking
        metrics.set_gauge('total_products_for_reviews', len(product_urls))
        reviews_scraped = 0
        
        # Process reviews for each product
        all_reviews = []
        for url in product_urls:
            try:
                metrics.start_timer(f'reviews_{url}')
                
                # Scrape reviews
                product_reviews = scrape_reviews(
                    url, 
                    max_reviews=config['max_reviews_per_product']
                )
                
                if product_reviews:
                    all_reviews.extend(product_reviews)
                    reviews_scraped += len(product_reviews)
                    metrics.increment('reviews_scraped', len(product_reviews))
                
                # Record time
                elapsed = metrics.stop_timer(f'reviews_{url}', 'reviews_scrape')
                logger.debug(f"Scraped {len(product_reviews) if product_reviews else 0} reviews for {url} in {elapsed:.2f}s")
                
            except Exception as e:
                metrics.record_error('reviews_scrape')
                logger.error(f"Error scraping reviews for {url}: {str(e)}")
                # Continue with the next product
        
        # Save the reviews
        with open(run_config['output_files']['reviews'], 'w') as f:
            json.dump(all_reviews, f, indent=2)
        
        logger.info(f"Saved {reviews_scraped} reviews to {run_config['output_files']['reviews']}")
        
        # Update metrics
        metrics.set_gauge('reviews_scraped', reviews_scraped)
        
        return reviews_scraped
    except Exception as e:
        metrics.record_error('process_reviews')
        logger.error(f"Error processing reviews: {str(e)}")
        raise

@logger.airflow_task_logger('post_process_data')
def post_process_data(**kwargs):
    """Post-process the scraped data."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        logger.info("Starting post-processing of scraped data")
        
        # Clean product data
        products_file = run_config['output_files']['products']
        if os.path.exists(products_file) and os.path.getsize(products_file) > 0:
            # Clean and transform the product data
            clean_data(products_file, products_file)
            logger.info(f"Cleaned product data in {products_file}")
            
            # Export to other formats if configured
            if 'json' in config['export_formats']:
                json_file = products_file.replace('.csv', '.json')
                export_to_json(products_file, json_file)
                logger.info(f"Exported product data to JSON: {json_file}")
        
        # Calculate statistics
        try:
            import pandas as pd
            stats = {}
            
            # Product stats
            try:
                df = pd.read_csv(products_file)
                stats['product_count'] = len(df)
                
                # More product statistics can be added here
                if 'price' in df.columns:
                    stats['avg_price'] = df['price'].mean()
                    stats['min_price'] = df['price'].min()
                    stats['max_price'] = df['price'].max()
            except:
                logger.warning("Could not calculate product statistics")
            
            # Review stats
            try:
                with open(run_config['output_files']['reviews'], 'r') as f:
                    reviews = json.load(f)
                stats['review_count'] = len(reviews)
                
                # More review statistics can be added here
            except:
                logger.warning("Could not calculate review statistics")
            
            # Save statistics
            stats_file = f"data/{run_config['run_id']}_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
            logger.info(f"Generated statistics: {json.dumps(stats)}")
            
            # Push stats to XCom
            ti.xcom_push(key='scraping_stats', value=stats)
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error in post-processing: {str(e)}")
        raise

@logger.airflow_task_logger('generate_report')
def generate_report(**kwargs):
    """Generate a summary report of the scraping run."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        stats = ti.xcom_pull(task_ids='post_process_data', key='scraping_stats')
        
        if not stats:
            logger.warning("No statistics available for report")
            stats = {}
        
        # Get metrics summary
        from utils.scraping_metrics import get_current_metrics
        metrics_data = get_current_metrics()
        
        # Create the report
        report = {
            'run_id': run_config['run_id'],
            'timestamp': datetime.now().isoformat(),
            'execution_date': kwargs['execution_date'].isoformat(),
            'categories': run_config['categories'],
            'statistics': stats,
            'performance': {
                'products_scraped': metrics_data['counters'].get('products_scraped', 0),
                'reviews_scraped': metrics_data['counters'].get('reviews_scraped', 0),
                'errors': metrics_data['counters'].get('total_errors', 0),
                'avg_request_time': metrics_data['request_stats'].get('avg_request_time', 0),
                'total_runtime': metrics_data['uptime_seconds']
            },
            'output_files': run_config['output_files']
        }
        
        # Save the report
        report_file = f"data/{run_config['run_id']}_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated report: {report_file}")
        
        # Also create a simple text version
        text_report = f"""
Amazon Scraping Report
=====================
Run ID: {run_config['run_id']}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary
-------
Categories scraped: {', '.join(run_config['categories'])}
Products scraped: {stats.get('product_count', 0)}
Reviews scraped: {stats.get('review_count', 0)}

Performance
-----------
Average request time: {metrics_data['request_stats'].get('avg_request_time', 0):.2f} seconds
Total runtime: {metrics_data['uptime_seconds'] / 60:.2f} minutes
Error count: {metrics_data['counters'].get('total_errors', 0)}

Output Files
-----------
Products: {run_config['output_files']['products']}
Reviews: {run_config['output_files']['reviews']}
Categories: {run_config['output_files']['categories']}
        """
        
        text_report_file = f"data/{run_config['run_id']}_report.txt"
        with open(text_report_file, 'w') as f:
            f.write(text_report)
        
        logger.info(f"Generated text report: {text_report_file}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise

@logger.airflow_task_logger('run_full_scraping')
@time_operation('full_scrape')
def execute_full_scrape(**kwargs):
    """Execute the full scraping process using run_full_scrape."""
    try:
        ti = kwargs['ti']
        run_config = ti.xcom_pull(task_ids='prepare_scraping', key='run_config')
        
        logger.info("Starting full scraping process")
        
        # Start metrics
        metrics.start_timer('full_scrape')
        
        # Run the full scraping process
        success = run_full_scrape(max_pages=run_config['max_pages_per_category'])
        
        # Record time and success
        elapsed = metrics.stop_timer('full_scrape', 'full_scrape')
        if success:
            metrics.increment('full_scrape.completed')
            logger.info(f"Full scraping completed successfully in {elapsed:.2f}s")
        else:
            metrics.record_error('full_scrape')
            logger.error("Full scraping failed")
        
        return success
    except Exception as e:
        metrics.record_error('full_scrape')
        logger.error(f"Error in full scraping: {str(e)}")
        raise

# Define the tasks
check_env = PythonOperator(
    task_id='check_environment',
    python_callable=check_environment,
    dag=dag,
)

prepare = PythonOperator(
    task_id='prepare_scraping',
    python_callable=prepare_scraping,
    dag=dag,
)

# Add the full scraping task
full_scrape = PythonOperator(
    task_id='run_full_scraping',
    python_callable=execute_full_scrape,
    dag=dag,
)

# Create a task group for category scraping
with TaskGroup(group_id='scrape_categories', dag=dag) as category_group:
    category_tasks = []
    for category in config['categories']:
        task = PythonOperator(
            task_id=f'scrape_category_{category}',
            python_callable=scrape_category,
            op_kwargs={'category': category},
            dag=dag,
        )
        category_tasks.append(task)

product_details = PythonOperator(
    task_id='scrape_product_details',
    python_callable=process_product_details,
    dag=dag,
)

reviews = PythonOperator(
    task_id='scrape_reviews',
    python_callable=process_reviews,
    dag=dag,
)

post_process = PythonOperator(
    task_id='post_process_data',
    python_callable=post_process_data,
    dag=dag,
)

report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_report,
    dag=dag,
)

# Define task dependencies
check_env >> prepare >> [full_scrape, category_group] >> product_details >> reviews >> post_process >> report

# Add this at the end to ensure metrics are saved when the DAG completes
completion = DummyOperator(
    task_id='completion',
    dag=dag,
    trigger_rule=TriggerRule.ALL_DONE,  # Run even if upstream tasks fail
)

report >> completion