# Amazon Product Scraping Project

A robust and scalable Amazon product scraping solution built with Python and Apache Airflow. This project efficiently scrapes product details, categories, and reviews from Amazon while implementing best practices for rate limiting, error handling, and data processing.

## Features

- **Multi-category Scraping**: Scrape products from multiple Amazon categories simultaneously
- **Comprehensive Data Collection**:
  - Product details (title, price, description, etc.)
  - Category information and filters
  - Customer reviews and ratings
- **Robust Error Handling**: Implements retry mechanisms with exponential backoff
- **Rate Limiting**: Prevents IP blocking with configurable request rates
- **Parallel Processing**: Utilizes ThreadPoolExecutor for efficient scraping
- **Data Export**: Supports multiple export formats (CSV, JSON)
- **Detailed Reporting**: Generates comprehensive scraping reports
- **Monitoring & Metrics**: Built-in logging and metrics collection

## Prerequisites

- Python 3.8+
- Apache Airflow 2.5.0+
- PostgreSQL 13+ (recommended for Airflow backend)
- Required Python packages (see `requirements.txt`)

## Dependencies

### Core Dependencies
```
apache-airflow>=2.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
selenium>=4.7.0
webdriver-manager>=3.8.0
python-dotenv>=0.21.0
```

### Optional Dependencies
```
aiohttp>=3.8.0  # For async scraping
fake-useragent>=1.1.0  # For user agent rotation
python-json-logger>=2.0.0  # For structured logging
prometheus-client>=0.16.0  # For metrics collection
```

## Detailed Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd amazon-scraping
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
# Install core dependencies
pip install -r requirements.txt

# Install optional dependencies
pip install -r requirements-optional.txt
```

4. Configure Airflow:
```bash
# Set Airflow home directory
export AIRFLOW_HOME=/path/to/airflow

# Initialize the database
airflow db init

# Create an admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password your_password

# Create necessary directories
mkdir -p $AIRFLOW_HOME/dags
mkdir -p $AIRFLOW_HOME/logs
mkdir -p $AIRFLOW_HOME/plugins
```

5. Configure the project:
```bash
# Copy the example configuration
cp config.example.yaml config.yaml

# Edit the configuration file
nano config.yaml
```

## Advanced Configuration

### Airflow Configuration
```yaml
# airflow.cfg
[core]
dags_folder = /path/to/your/dags
load_examples = False
executor = LocalExecutor
sql_alchemy_conn = postgresql+psycopg2://user:password@localhost/airflow

[scheduler]
min_file_process_interval = 30
dag_file_processor_timeout = 600
```

### Scraper Configuration Examples

1. Basic Configuration:
```json
{
    "categories": ["electronics", "computers"],
    "max_products_per_category": 100,
    "max_pages_per_category": 5
}
```

2. Advanced Configuration with Rate Limiting:
```json
{
    "categories": ["electronics", "computers", "smart-home"],
    "max_products_per_category": 100,
    "max_pages_per_category": 5,
    "rate_limit": {
        "requests_per_second": 2,
        "burst_size": 5,
        "retry_after": 300
    },
    "proxy_config": {
        "use_proxies": true,
        "proxy_list": [
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080"
        ],
        "rotation_interval": 100
    }
}
```

3. Custom User Agent Configuration:
```json
{
    "user_agents": {
        "enabled": true,
        "rotation_interval": 50,
        "custom_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
    }
}
```

## Troubleshooting

### Common Issues and Solutions

1. **Airflow DAG Not Showing Up**
   - Check if the DAG file is in the correct directory
   - Verify file permissions
   - Check Airflow logs for syntax errors
   ```bash
   airflow dags list
   airflow dags show optimized_amazon_scraping
   ```

2. **Scraping Rate Limited**
   - Increase delay between requests
   - Rotate IP addresses more frequently
   - Use more user agents
   ```python
   # Example fix in config
   "request_delay": 5.0,  # Increase from 2.0
   "user_agent_rotation": true,
   "proxy_rotation": true
   ```

3. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string
   - Ensure database user has proper permissions
   ```bash
   # Test database connection
   airflow db check
   ```

4. **Memory Issues**
   - Reduce batch size
   - Decrease number of parallel workers
   - Monitor system resources
   ```python
   # Example fix in config
   "batch_size": 5,  # Reduce from 10
   "max_workers": 2  # Reduce from 4
   ```

### Logging and Debugging

1. Enable debug logging:
```bash
export AIRFLOW_LOGGING_LEVEL=DEBUG
```

2. Check specific task logs:
```bash
airflow tasks test optimized_amazon_scraping task_name execution_date
```

3. Monitor system resources:
```bash
# Check Airflow processes
ps aux | grep airflow

# Monitor memory usage
top -p $(pgrep -f airflow)
```

## Project Structure

```
amazon-scraping/
├── airflow_dags/
│   └── amazon_scraping_dag.py
├── scrapers/
│   ├── categories.py
│   ├── amazon_details_scraper.py
│   ├── commentaire.py
│   └── scraping.py
├── utils/
│   ├── file_utils.py
│   ├── scraping_logger.py
│   └── scraping_metrics.py
├── data/
├── logs/
├── config/
│   ├── config.example.yaml
│   └── config.yaml
├── tests/
├── requirements.txt
├── requirements-optional.txt
└── README.md
```

## Usage

1. Start the Airflow webserver:
```bash
airflow webserver -p 8080
```

2. Start the Airflow scheduler:
```bash
airflow scheduler
```

3. Access the Airflow UI at `http://localhost:8080`

4. Enable the `optimized_amazon_scraping` DAG

## DAG Structure

The scraping process follows these steps:
1. Environment check
2. Preparation
3. Category scraping
4. Product details scraping
5. Review scraping
6. Post-processing
7. Report generation

## Output

The project generates several output files:
- Product data in CSV format
- Review data in JSON format
- Category information in JSON format
- Detailed scraping reports in both JSON and text formats

## Error Handling

The project implements several error handling mechanisms:
- Exponential backoff for retries
- Rate limiting to prevent IP blocking
- Comprehensive logging
- Error metrics collection

## Monitoring

Monitor the scraping process through:
- Airflow UI
- Generated logs in the `logs` directory
- Metrics collection
- Generated reports

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is for educational purposes only. Please ensure you comply with Amazon's terms of service and robots.txt when using this scraper. The developers are not responsible for any misuse or violation of Amazon's terms of service.

