# docker/airflow/Dockerfile

# Start from official Airflow image
FROM apache/airflow:2.7.2-python3.10-slim

# Switch to root for system package installation
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    g++ \
    libcurl4-openssl-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Switch back to airflow user
USER airflow

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__FERNET_KEY=k6CpuyNfmTVlx6NSfe0Ly34M8P9s-q1exdjyXaJ4Cgc=
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV PYTHONPATH=${PYTHONPATH}:/opt/airflow/scrapers:/opt/airflow/utils

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt \
    && pip install --user webdriver-manager

# Create directory for logs
RUN mkdir -p /opt/airflow/logs/scraping_logs