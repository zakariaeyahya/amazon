# 🚀 Amazon Product Extraction and Analysis Platform
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Airflow](https://img.shields.io/badge/Airflow-2.5.0%2B-red)
![Snowflake](https://img.shields.io/badge/Snowflake-Ready-9cf)
![License](https://img.shields.io/badge/License-MIT-green)
> A distributed e-commerce data extraction and analysis architecture optimized for Amazon, built on Python and Apache Airflow with Snowflake integration.

![image](https://github.com/user-attachments/assets/07cdaade-045a-42b3-b941-ee4dc6c1fc45)

## 🔍 Overview
This platform enables the extraction and analysis of product data from Amazon, offering a comprehensive and high-performance solution through a distributed and scalable architecture.

**Key Capabilities:**
- Multi-category collection with parallel processing
- Comprehensive extraction of product metadata, taxonomy, and user reviews
- Advanced anti-blocking systems
- Complete analysis pipeline via Snowflake

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Execution Pipeline](#-execution-pipeline)
- [Data Model](#-data-model)
- [Usage Examples](#-usage-examples)
- [Troubleshooting](#-troubleshooting)
- [Security and Compliance](#-security-and-compliance)
- [Performance](#-performance-and-optimization)
- [Future Developments](#-future-developments)
- [License](#-license)

## ✨ Features

### 🔍 Data Extraction
- **Multi-category Collection:** Optimized system to extract data from multiple Amazon categories simultaneously
- **Comprehensive Extraction:**
  - Product metadata (IDs, prices, specifications)
  - Category taxonomy and filtering systems
  - User data (reviews, ratings)
- **Advanced Anti-blocking:**
  - Intelligent throttling management with exponential backoff
  - User agent and proxy rotation
  - Dynamic request rate modulation

### ⚙️ Processing and Pipeline
- **Orchestration via Apache Airflow:** Complete workflow management with configurable DAGs
- **Optimized Parallelization:** Use of ThreadPoolExecutor to maximize efficiency
- **Multi-format Export:** Support for CSV and JSON formats with structural validation
- **Built-in Observability:** Comprehensive metrics, structured logs, and execution reports

### 📊 Data Analysis via Snowflake
- **ETL Pipeline:** Automated ingestion and transformation system
- **Analytical Modeling:** Normalized and denormalized tables for various use cases
- **Analytical Capabilities:** Product segmentation, sentiment analysis, and other features

## 📋 Prerequisites
- Python 3.8+
- Apache Airflow 2.5.0+
- PostgreSQL 13+ (recommended for Airflow)
- Snowflake account with adequate permissions
- *(Optional)* AWS S3 for intermediate storage of extracted data

### Python Dependencies
```bash
apache-airflow>=2.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
selenium>=4.7.0
webdriver-manager>=3.8.0
python-dotenv>=0.21.0
snowflake-connector-python>=2.7.0
```

## 🔧 Installation
```bash
# Clone the repository
git clone https://github.com/zakariaeyahya/amazon.git
cd amazon-scraping

# Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

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

# Set up necessary directories
mkdir -p $AIRFLOW_HOME/{dags,logs,plugins}
```

## 🏗️ Architecture
```
amazon-analytics/
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
├── snowflake/
│   ├── SQLrequet.sql
│   └── snowflakeconnection.py
├── data/
├── logs/
├── config/
├── tests/
└── requirements.txt
```

## ⚙️ Configuration

### Scraper Configuration
```json
{
  "extraction": {
    "categories": ["electronics", "computers", "smart-home"],
    "limits": {
      "products_per_category": 100,
      "pages_per_category": 5
    },
    "rate_control": {
      "requests_per_second": 2,
      "burst_size": 5,
      "delay_after_failure": 300
    },
    "proxies": {
      "active": true,
      "list": [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080"
      ],
      "rotation_interval": 100
    },
    "user_agents": {
      "active": true,
      "rotation_interval": 50
    }
  },
  "processing": {
    "batch_size": 5,
    "max_workers": 2
  }
}
```

### Snowflake Configuration
```python
# snowflakeconnection.py
conn_config = {
    'user': 'SNOWFLAKE_USER',
    'password': 'SNOWFLAKE_PASSWORD',
    'account': 'SNOWFLAKE_ACCOUNT',
    'warehouse': 'COMPUTE_WH',
    'database': 'AMAZON_ANALYTICS',
    'schema': 'PUBLIC'
}
```

## 🔄 Execution Pipeline

### Extraction Phase
1. Preliminary Check – Environment and dependency validation
2. Category Extraction – Product taxonomy mapping
3. Product Details Extraction – Collection of main metadata
4. Review Extraction – Collection of user data
5. Post-processing – Cleaning and normalization
6. Report Generation – Execution metrics and validations

### Snowflake Analysis Phase
1. Data Loading – Ingestion into Snowflake tables
2. Transformation – Normalization and enrichment
3. Modeling – Creation of analytical views
4. Segmentation – Classification by price and other dimensions
5. Advanced Analysis – Analytical queries and reports

## 💾 Data Model

### Main Tables


| Table | Description |
|-------|-------------|
| `product_info1` | Core product data |
| `product_info2` | Technical product specifications |
| `review` | User reviews and ratings |
| `full_product_info` | Integrated denormalized view |
| `classe_prix` | Price range segmentation |

> **Note:** The schema is designed to optimize both analytical queries and OLTP operations.

## 💡 Usage Examples

### Product Classification and Sentiment Analysis
```sql
SELECT
    p.asin,
    p.titre,
    p.prix,
    c.classe AS price_range,
    r.sentiment,
    COUNT(r.review_id) AS review_count
FROM
    full_product_info p
JOIN
    classe_prix c ON p.asin = c.asin
LEFT JOIN
    review r ON p.asin = r.asin
GROUP BY
    1, 2, 3, 4, 5
ORDER BY
    review_count DESC;
```

### Transformation of Technical Specifications
```sql
-- Normalize hard drive sizes to GB
UPDATE product_info2
SET disque_dur =
    CASE
        WHEN disque_dur LIKE '%TB%' THEN TO_NUMBER(REGEXP_SUBSTR(disque_dur, '[0-9]+')) * 1024
        WHEN disque_dur LIKE '%GB%' THEN TO_NUMBER(REGEXP_SUBSTR(disque_dur, '[0-9]+'))
        ELSE NULL
    END;
```

## 🔧 Troubleshooting

### Airflow DAGs
- Check DAG file permissions
- Validate Python syntax with `airflow dags list` and `airflow dags show`
- Review logs for syntax or import errors

### Rate Limiting
- Implement progressive backoff strategy
- Increase interval between requests
- Diversify proxies and user agents

### Snowflake Connection
- Verify credentials and permissions
- Ensure IP address is allowed
- Test connection with a simple query

## 📜 License
This project is distributed under the [MIT License](LICENSE).

---
© 2025 - Amazon Product Extraction and Analysis Platform - All rights reserved
