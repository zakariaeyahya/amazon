# Start from official Airflow image
FROM apache/airflow:2.7.2-python3.10

# Switch to root for system package installation
USER root

# Install system dependencies, curl and ca-certificates for SSL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    g++ \
    libcurl4-openssl-dev \
    libssl-dev \
    wget \
    curl \
    gnupg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome for Selenium (with updated keyring and repository addition)
RUN mkdir -p /etc/apt/keyrings && \
    echo "Fetching Google signing key..." && \
    Invoke-WebRequest -Uri "https://dl.google.com/linux/linux_signing_key.pub" -OutFile "linux_signing_key.pub"| tee /etc/apt/keyrings/google-linux-signing-key.gpg || { echo "Failed to fetch Google signing key"; exit 1; } && \
    echo "Adding Chrome repository to sources list..." && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    echo "Updating apt repositories..." && \
    apt-get update -o Acquire::ForceIPv4=true || { echo "Failed to update apt repositories"; exit 1; } && \
    echo "Installing Google Chrome..." && \
    apt-get install -y --no-install-recommends google-chrome-stable || { echo "Failed to install Google Chrome"; exit 1; } && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


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
