# docker/selenium/Dockerfile

# Use official Selenium base image with Node.js
FROM selenium/standalone-chrome:4.14.0-20231004

# Switch to root for installations
USER root

# Install Firefox and geckodriver
RUN apt-get update -qqy \
    && apt-get install -y --no-install-recommends \
       firefox-esr \
       libavcodec-extra \
       libgtk-3-0 \
    && FIREFOX_VERSION=$(firefox --version | awk '{print $3}') \
    && GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4) \
    && curl -sSL https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz | tar -xz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver

# Configure headless operation
ENV SE_OPTS="--log-level WARNING"
ENV SCREEN_WIDTH=1920
ENV SCREEN_HEIGHT=1080
ENV SCREEN_DEPTH=24
ENV START_XVFB=false
ENV CHROMEDRIVER_ARGS="--log-level=3 --disable-dev-shm-usage"
ENV FIREFOX_ARGS="-headless"

# Network configurations
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV NO_PROXY="localhost,127.0.0.1"
ENV DISABLE_CACHE=false

# Install scraping tools
RUN apt-get install -y \
    xvfb \
    tcpdump \
    net-tools \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Create custom user for security
RUN groupadd -g 1200 selenium \
    && useradd -u 1200 -g selenium -d /home/selenium -m selenium \
    && chown -R selenium:selenium /opt

# Configure browser environments
COPY browser-profiles/ /home/selenium/browser-profiles/
RUN mkdir -p /home/selenium/downloads \
    && chown -R selenium:selenium /home/selenium

# Switch to non-root user
USER selenium

# Expose Selenium ports
EXPOSE 4444
EXPOSE 7900

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sS http://localhost:4444/status | grep '"ready": true' || exit 1

# Entrypoint configuration
COPY entrypoint.sh /home/selenium/
ENTRYPOINT ["/home/selenium/entrypoint.sh"]