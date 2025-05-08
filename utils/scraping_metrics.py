"""
Metrics collection utility for Amazon scraping operations.
Collects and reports metrics about scraping performance, success rates, and resource usage.
Can integrate with Airflow's metrics system or standalone monitoring.
"""

import time
import threading
import json
import os
import psutil
import datetime
from collections import defaultdict, deque
import atexit
from utils.scraping_logger import get_logger

# Configure logger
logger = get_logger('metrics')

class ScrapingMetrics:
    """
    Collects, aggregates, and reports metrics about scraping operations.
    Thread-safe for concurrent scraping tasks.
    """
    
    def __init__(self, metrics_file='logs/scraping_metrics.json', 
                 report_interval=300,  # 5 minutes
                 history_size=100):
        """
        Initialize the metrics collector.
        
        Args:
            metrics_file: File to save metrics to
            report_interval: How often to save metrics to file (seconds)
            history_size: How many recent request times to keep for statistics
        """
        self.metrics_file = metrics_file
        self.report_interval = report_interval
        self.history_size = history_size
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Metrics storage
        self._counters = defaultdict(int)
        self._gauges = {}
        self._request_times = deque(maxlen=history_size)
        self._category_times = defaultdict(lambda: deque(maxlen=history_size))
        self._errors = defaultdict(int)
        self._start_time = time.time()
        
        # Custom timers
        self._timers = {}
        
        # Resource metrics
        self._process = psutil.Process(os.getpid())
        
        # Start background reporting thread
        if report_interval > 0:
            self._reporting_thread = threading.Thread(
                target=self._background_reporting,
                daemon=True
            )
            self._reporting_thread.start()
            
            # Register cleanup on exit
            atexit.register(self.save_metrics)
    
    def _background_reporting(self):
        """Background thread that periodically saves metrics to disk."""
        while True:
            time.sleep(self.report_interval)
            try:
                self.save_metrics()
                self.log_summary()
            except Exception as e:
                logger.error(f"Error in metrics reporting: {str(e)}")
    
    def increment(self, metric, value=1):
        """
        Increment a counter metric.
        
        Args:
            metric: Name of the metric
            value: Value to increment by (default: 1)
        """
        with self._lock:
            self._counters[metric] += value
    
    def set_gauge(self, metric, value):
        """
        Set a gauge metric to a specific value.
        
        Args:
            metric: Name of the metric
            value: Value to set
        """
        with self._lock:
            self._gauges[metric] = value
    
    def record_time(self, category, duration):
        """
        Record the time taken for an operation.
        
        Args:
            category: Category of the operation
            duration: Time taken in seconds
        """
        with self._lock:
            self._request_times.append(duration)
            self._category_times[category].append(duration)
    
    def record_error(self, error_type):
        """
        Record an error occurrence.
        
        Args:
            error_type: Type of error that occurred
        """
        with self._lock:
            self._errors[error_type] += 1
            self._counters['total_errors'] += 1
    
    def start_timer(self, name):
        """
        Start a named timer.
        
        Args:
            name: Name of the timer
        """
        with self._lock:
            self._timers[name] = time.time()
    
    def stop_timer(self, name, record_category=None):
        """
        Stop a named timer and get the elapsed time.
        
        Args:
            name: Name of the timer
            record_category: If provided, record this time in the category's history
            
        Returns:
            float: Elapsed time in seconds, or None if timer not found
        """
        with self._lock:
            if name in self._timers:
                elapsed = time.time() - self._timers[name]
                del self._timers[name]
                
                if record_category:
                    self.record_time(record_category, elapsed)
                
                return elapsed
            return None
    
    def _collect_resource_metrics(self):
        """Collect system resource metrics."""
        try:
            # CPU and memory usage
            cpu_percent = self._process.cpu_percent()
            memory_info = self._process.memory_info()
            
            resources = {
                'cpu_percent': cpu_percent,
                'memory_rss_mb': memory_info.rss / (1024 * 1024),
                'memory_vms_mb': memory_info.vms / (1024 * 1024),
                'threads': len(self._process.threads()),
                'open_files': len(self._process.open_files())
            }
            
            # Add to gauges
            for key, value in resources.items():
                self.set_gauge(f'resource.{key}', value)
                
            return resources
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {str(e)}")
            return {}
    
    def get_metrics(self):
        """
        Get the current metrics.
        
        Returns:
            dict: Current metrics values
        """
        with self._lock:
            # Calculate statistics for request times
            request_stats = {}
            if self._request_times:
                times = list(self._request_times)
                request_stats = {
                    'avg_request_time': sum(times) / len(times),
                    'min_request_time': min(times),
                    'max_request_time': max(times),
                    'request_count': len(times)
                }
            
            # Calculate per-category statistics
            category_stats = {}
            for category, times in self._category_times.items():
                if times:
                    category_stats[category] = {
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times),
                        'count': len(times)
                    }
            
            # Get resource metrics
            resources = self._collect_resource_metrics()
            
            # Calculate uptime
            uptime = time.time() - self._start_time
            
            # Combine all metrics
            metrics = {
                'timestamp': datetime.datetime.now().isoformat(),
                'uptime_seconds': uptime,
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'request_stats': request_stats,
                'category_stats': category_stats,
                'errors': dict(self._errors),
                'resources': resources
            }
            
            return metrics
    
    def save_metrics(self):
        """Save current metrics to file."""
        metrics = self.get_metrics()
        
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.debug(f"Metrics saved to {self.metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {str(e)}")
    
    def log_summary(self):
        """Log a summary of current metrics."""
        metrics = self.get_metrics()
        
        # Create a simplified summary
        summary = {
            'uptime_hours': round(metrics['uptime_seconds'] / 3600, 2),
            'total_requests': metrics['counters'].get('total_requests', 0),
            'success_rate': 0,
            'avg_request_time': metrics['request_stats'].get('avg_request_time', 0),
            'total_products': metrics['counters'].get('products_scraped', 0),
            'total_errors': metrics['counters'].get('total_errors', 0),
            'memory_usage_mb': metrics['resources'].get('memory_rss_mb', 0)
        }
        
        # Calculate success rate if we have both metrics
        if 'total_requests' in metrics['counters'] and metrics['counters']['total_requests'] > 0:
            success_rate = 1 - (metrics['counters'].get('total_errors', 0) / metrics['counters']['total_requests'])
            summary['success_rate'] = round(success_rate * 100, 2)
        
        logger.info(f"Metrics summary: {json.dumps(summary)}")

    def timing_decorator(self, category):
        """
        Decorator to time function execution and record metrics.
        
        Args:
            category: Category to record the timing under
            
        Returns:
            decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                timer_name = f"{func.__name__}_{id(func)}"
                self.start_timer(timer_name)
                self.increment('total_requests')
                
                try:
                    result = func(*args, **kwargs)
                    self.increment(f'success.{category}')
                    return result
                except Exception as e:
                    self.record_error(e.__class__.__name__)
                    self.increment(f'error.{category}')
                    raise
                finally:
                    elapsed = self.stop_timer(timer_name, category)
                    if elapsed is not None:
                        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
            
            return wrapper
        return decorator

# Create a singleton instance
metrics = ScrapingMetrics()

# Helper functions
def time_operation(category):
    """
    Decorator for timing operations and adding to metrics.
    
    Usage:
        @time_operation('product_scrape')
        def scrape_product(url):
            # function body
    """
    return metrics.timing_decorator(category)

def record_success(category='general'):
    """Record a successful operation."""
    metrics.increment(f'success.{category}')
    metrics.increment('total_successes')

def record_error(error_type, category='general'):
    """Record an error."""
    metrics.record_error(error_type)
    metrics.increment(f'error.{category}')

def set_gauge(name, value):
    """Set a gauge value."""
    metrics.set_gauge(name, value)

def get_current_metrics():
    """Get current metrics summary."""
    return metrics.get_metrics()