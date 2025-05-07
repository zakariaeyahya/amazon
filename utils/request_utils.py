"""
Request utility functions for managing web requests with advanced features:
- User-agent rotation
- Proxy management
- Request throttling
- Exponential backoff for retries
- IP ban detection and handling
"""

import random
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging
from airflow.models import Variable
from functools import wraps
from typing import Dict, List, Optional, Union, Callable

# Setup logging
logger = logging.getLogger(__name__)

# Common user agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.76',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile/15E148 Safari/604.1'
]

# Rate limiting decorator
def rate_limit(min_interval: float = 1.0):
    """Decorator to enforce minimum interval between function calls"""
    last_call_time = 0
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call_time
            current_time = time.time()
            time_since_last_call = current_time - last_call_time
            
            if time_since_last_call < min_interval:
                sleep_time = min_interval - time_since_last_call
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            last_call_time = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_random_user_agent() -> str:
    """Return a random user agent from the list"""
    return random.choice(USER_AGENTS)

def create_session(
    retries: int = 3, 
    backoff_factor: float = 0.3, 
    status_forcelist: List[int] = [429, 500, 502, 503, 504],
    use_proxy: bool = False
) -> requests.Session:
    """
    Creates a requests session with retry capabilities and optional proxy
    
    Args:
        retries: Maximum number of retries
        backoff_factor: Backoff factor for retry timing
        status_forcelist: HTTP status codes to retry on
        use_proxy: Whether to use a proxy for this session
    
    Returns:
        A configured requests Session object
    """
    session = requests.Session()
    
    # Setup retry strategy with exponential backoff
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "HEAD"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set default headers
    session.headers.update({
        'User-Agent': get_random_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.amazon.com/',
        'Accept-Encoding': 'gzip, deflate, br'
    })
    
    # Add proxy if enabled
    if use_proxy:
        proxy = get_proxy()
        if proxy:
            session.proxies.update(proxy)
    
    return session

def setup_proxy_rotation():
    """
    Set up proxy rotation from Airflow variables
    This loads proxy configuration from Airflow variables if available
    """
    try:
        # Try to get proxies from Airflow variables
        proxies_str = Variable.get("scraping_proxies", default="[]")
        import json
        proxies = json.loads(proxies_str)
        
        if proxies:
            global PROXY_LIST
            PROXY_LIST = proxies
            logger.info(f"Loaded {len(PROXY_LIST)} proxies for rotation")
        else:
            logger.warning("No proxies configured in Airflow variables")
    except Exception as e:
        logger.error(f"Failed to load proxy configuration: {e}")

# Global proxy list - will be populated from Airflow variables
PROXY_LIST = []
CURRENT_PROXY_INDEX = 0

def get_proxy() -> Dict[str, str]:
    """
    Get the next proxy from the rotation
    Returns an empty dict if no proxies are configured
    """
    global CURRENT_PROXY_INDEX, PROXY_LIST
    
    if not PROXY_LIST:
        return {}
    
    proxy = PROXY_LIST[CURRENT_PROXY_INDEX]
    CURRENT_PROXY_INDEX = (CURRENT_PROXY_INDEX + 1) % len(PROXY_LIST)
    
    return proxy

def is_blocked_response(response: requests.Response) -> bool:
    """
    Check if a response indicates we've been blocked or rate-limited
    
    Args:
        response: The HTTP response to check
    
    Returns:
        True if the response indicates blocking, False otherwise
    """
    # Check for CAPTCHA pages
    if response.status_code == 200 and 'captcha' in response.text.lower():
        return True
    
    # Check for robot check pages
    if 'robot check' in response.text.lower():
        return True
    
    # Check for specific Amazon block messages
    if 'To discuss automated access to Amazon data please contact' in response.text:
        return True
    
    # Check for unusual redirects
    if response.history and len(response.history) > 2:
        return True
    
    return False

@rate_limit(min_interval=2.0)  # Enforce minimum 2 seconds between requests
def make_request(url: str, method: str = 'GET', params: Dict = None, 
                 data: Dict = None, headers: Dict = None, 
                 use_proxy: bool = True, max_retries: int = 3) -> Optional[requests.Response]:
    """
    Make a web request with advanced error handling and proxy rotation
    
    Args:
        url: URL to request
        method: HTTP method (GET, POST, etc.)
        params: URL parameters
        data: POST data
        headers: Additional headers to send
        use_proxy: Whether to use a proxy
        max_retries: Maximum number of retries before giving up
    
    Returns:
        Response object if successful, None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            # Create a new session for each attempt
            session = create_session(use_proxy=use_proxy)
            
            # Update headers if provided
            if headers:
                session.headers.update(headers)
            else:
                # Rotate user agent for each attempt
                session.headers.update({'User-Agent': get_random_user_agent()})
            
            # Make the request
            if method.upper() == 'GET':
                response = session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = session.post(url, params=params, data=data, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check if we've been blocked
            if is_blocked_response(response):
                logger.warning(f"Detected blocking at URL {url}. Rotating proxy and retrying.")
                # Force proxy rotation for next attempt
                global CURRENT_PROXY_INDEX
                if PROXY_LIST:
                    CURRENT_PROXY_INDEX = (CURRENT_PROXY_INDEX + 1) % len(PROXY_LIST)
                time.sleep(5 + attempt * 5)  # Progressive backoff
                continue
            
            # Check if the response is valid
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"Request failed with status {response.status_code}: {url}")
                # Add exponential backoff
                time.sleep(2 ** attempt)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error on attempt {attempt+1}/{max_retries}: {e}")
            # Switch proxy for next attempt
            if use_proxy and PROXY_LIST:
                global CURRENT_PROXY_INDEX
                CURRENT_PROXY_INDEX = (CURRENT_PROXY_INDEX + 1) % len(PROXY_LIST)
            time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"All {max_retries} attempts failed for URL: {url}")
    return None

def get_amazon_url(path: str, params: Dict = None) -> str:
    """
    Construct a proper Amazon URL with locale and tracking parameters stripped
    
    Args:
        path: Path component of the URL
        params: Query parameters to include
    
    Returns:
        Properly formatted Amazon URL
    """
    # Get base domain from Airflow variables or use default
    try:
        base_domain = Variable.get("amazon_domain", default="amazon.com")
    except:
        base_domain = "amazon.com"
    
    # Ensure path starts with a slash
    if not path.startswith('/'):
        path = '/' + path
    
    url = f"https://www.{base_domain}{path}"
    
    # Add query parameters if provided
    if params:
        from urllib.parse import urlencode
        query_string = urlencode(params)
        url = f"{url}?{query_string}"
    
    return url

def extract_amazon_id(url: str) -> Optional[str]:
    """
    Extract Amazon product ID (ASIN) from a URL
    
    Args:
        url: Amazon product URL
    
    Returns:
        ASIN string if found, None otherwise
    """
    import re
    
    # Try multiple patterns
    patterns = [
        r'/dp/([A-Z0-9]{10})/?',
        r'/gp/product/([A-Z0-9]{10})/?',
        r'/ASIN/([A-Z0-9]{10})/?',
        r'(?:product|dp|gp/product)/([A-Z0-9]{10})/?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None