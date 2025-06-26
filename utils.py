import re
import json
import logging
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse
from functools import wraps

logger = logging.getLogger(__name__)

def sanitize_url(url):
    """Sanitize and validate URL"""
    try:
        # Remove whitespace and normalize
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse and validate
        parsed = urlparse(url)
        
        if not parsed.netloc:
            raise ValueError("Invalid URL: missing domain")
        
        # Reconstruct clean URL
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        if parsed.fragment:
            clean_url += f"#{parsed.fragment}"
        
        return clean_url
        
    except Exception as e:
        logger.error(f"Error sanitizing URL {url}: {e}")
        raise ValueError(f"Invalid URL: {url}")

def extract_urls_from_text(text):
    """Extract all URLs from text"""
    try:
        # URL pattern
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        urls = url_pattern.findall(text)
        
        # Clean and validate URLs
        clean_urls = []
        for url in urls:
            try:
                clean_url = sanitize_url(url)
                clean_urls.append(clean_url)
            except ValueError:
                continue
        
        return clean_urls
        
    except Exception as e:
        logger.error(f"Error extracting URLs from text: {e}")
        return []

def generate_payment_id():
    """Generate unique payment ID"""
    try:
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        random_part = hashlib.md5(f"{timestamp}{id(object())}".encode()).hexdigest()[:8]
        return f"PAY_{timestamp}_{random_part}".upper()
    except Exception as e:
        logger.error(f"Error generating payment ID: {e}")
        return f"PAY_{int(datetime.now(timezone.utc).timestamp())}"

def format_currency(amount, currency='USD'):
    """Format currency amount"""
    try:
        if currency == 'USD':
            return f"${amount:.2f}"
        elif currency == 'BTC':
            return f"₿{amount:.8f}"
        elif currency == 'TRX':
            return f"TRX {amount:.6f}"
        elif currency == 'USDT':
            return f"USDT {amount:.6f}"
        else:
            return f"{amount:.6f} {currency}"
    except Exception:
        return str(amount)

def validate_telegram_data(data):
    """Validate Telegram webhook data"""
    try:
        required_fields = ['update_id']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating Telegram data: {e}")
        return False

def safe_json_loads(json_str, default=None):
    """Safely parse JSON string"""
    try:
        if not json_str:
            return default
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON: {json_str}")
        return default

def safe_json_dumps(obj, default=None):
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return json.dumps(default) if default is not None else "{}"

def log_api_call(func):
    """Decorator to log API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now(timezone.utc)
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"API call {func.__name__} completed in {duration:.3f}s")
            return result
            
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"API call {func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper

def rate_limit_key(user_id, endpoint):
    """Generate rate limit key"""
    return f"rate_limit:{user_id}:{endpoint}"

def hash_string(text, algorithm='md5'):
    """Hash string using specified algorithm"""
    try:
        if algorithm == 'md5':
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(text.encode()).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(text.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    except Exception as e:
        logger.error(f"Error hashing string: {e}")
        return None

def truncate_string(text, max_length=100, suffix='...'):
    """Truncate string to maximum length"""
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except Exception:
        return str(text)

def is_valid_email(email):
    """Validate email address"""
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    except Exception:
        return False

def is_valid_telegram_id(telegram_id):
    """Validate Telegram user ID"""
    try:
        return isinstance(telegram_id, int) and telegram_id > 0
    except Exception:
        return False

def format_datetime(dt, format_str=None):
    """Format datetime with fallback"""
    try:
        if not dt:
            return 'N/A'
        
        if format_str:
            return dt.strftime(format_str)
        
        # Default format
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return 'Invalid Date'

def calculate_confidence_score(positives, total, base_score=0.5):
    """Calculate confidence score from scan results"""
    try:
        if total == 0:
            return base_score
        
        ratio = positives / total
        
        # Logarithmic scaling for confidence
        if ratio == 0:
            return max(0.1, base_score - 0.2)
        elif ratio < 0.1:
            return base_score
        elif ratio < 0.3:
            return 0.7
        elif ratio < 0.5:
            return 0.85
        else:
            return 0.95
            
    except Exception as e:
        logger.error(f"Error calculating confidence score: {e}")
        return base_score

def get_threat_level_color(classification):
    """Get color code for threat level"""
    colors = {
        'clean': '#28a745',      # Green
        'suspicious': '#ffc107', # Yellow
        'malicious': '#dc3545',  # Red
        'unknown': '#6c757d',    # Gray
        'error': '#fd7e14'       # Orange
    }
    return colors.get(classification, '#6c757d')

def get_threat_level_emoji(classification):
    """Get emoji for threat level"""
    emojis = {
        'clean': '✅',
        'suspicious': '⚠️',
        'malicious': '🚨',
        'unknown': '❓',
        'error': '❌'
    }
    return emojis.get(classification, '❓')

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def with_timeout(timeout_seconds):
    """Decorator to add timeout to function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
            
            # Set timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Reset alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

logger.info("Utility functions loaded successfully")
