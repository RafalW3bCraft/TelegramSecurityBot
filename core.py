import os
import time
import json
import logging
from datetime import datetime, timezone
from collections import defaultdict
from threading import Lock
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def check_rate_limit(self, key, limit, window):
        """
        Check if request is within rate limit
        
        Args:
            key: Unique identifier for rate limiting (usually IP or user ID)
            limit: Maximum number of requests allowed
            window: Time window in seconds
        
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        try:
            with self.lock:
                now = time.time()
                
                # Clean old requests outside the window
                self.requests[key] = [
                    timestamp for timestamp in self.requests[key]
                    if now - timestamp < window
                ]
                
                # Check if limit exceeded
                if len(self.requests[key]) >= limit:
                    return False
                
                # Add current request
                self.requests[key].append(now)
                return True
                
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # On error, allow the request
            return True
    
    def clear_expired(self):
        """Clear expired rate limit entries"""
        try:
            with self.lock:
                now = time.time()
                keys_to_remove = []
                
                for key, timestamps in self.requests.items():
                    # Remove timestamps older than 1 hour
                    valid_timestamps = [
                        timestamp for timestamp in timestamps
                        if now - timestamp < 3600
                    ]
                    
                    if valid_timestamps:
                        self.requests[key] = valid_timestamps
                    else:
                        keys_to_remove.append(key)
                
                # Remove empty entries
                for key in keys_to_remove:
                    del self.requests[key]
                    
        except Exception as e:
            logger.error(f"Error clearing expired rate limits: {e}")

class CacheManager:
    """Simple in-memory cache for threat intelligence results"""
    
    def __init__(self, default_ttl=3600):  # 1 hour default TTL
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def get(self, key):
        """Get cached value if not expired"""
        try:
            with self.lock:
                if key not in self.cache:
                    return None
                
                # Check if expired
                if time.time() - self.timestamps[key] > self.default_ttl:
                    del self.cache[key]
                    del self.timestamps[key]
                    return None
                
                return self.cache[key]
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL"""
        try:
            with self.lock:
                self.cache[key] = value
                self.timestamps[key] = time.time()
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, key):
        """Delete cached value"""
        try:
            with self.lock:
                if key in self.cache:
                    del self.cache[key]
                    del self.timestamps[key]
                    
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        try:
            with self.lock:
                now = time.time()
                expired_keys = [
                    key for key, timestamp in self.timestamps.items()
                    if now - timestamp > self.default_ttl
                ]
                
                for key in expired_keys:
                    if key in self.cache:
                        del self.cache[key]
                    if key in self.timestamps:
                        del self.timestamps[key]
                        
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
    
    def stats(self):
        """Get cache statistics"""
        with self.lock:
            return {
                'total_entries': len(self.cache),
                'oldest_entry': min(self.timestamps.values()) if self.timestamps else None,
                'newest_entry': max(self.timestamps.values()) if self.timestamps else None
            }

class ConfigManager:
    """Configuration management with environment variable fallbacks"""
    
    def __init__(self):
        self.config = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration values"""
        load_dotenv()  # Ensure .env is loaded
        
        self.config = {
            # API Keys
            'virustotal_api_key': os.environ.get('VIRUSTOTAL_API_KEY', ''),
            'urlhaus_api_key': os.environ.get('URLHAUS_API_KEY', ''),
            'telegram_bot_token': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
            
            # Payment Configuration
            'btc_address': os.environ.get('BTC_WALLET_ADDRESS', ''),
            'trx_address': os.environ.get('TRX_WALLET_ADDRESS', ''), 
            'usdt_trc20_address': os.environ.get('USDT_TRC20_WALLET_ADDRESS', ''),
            
            # Pricing
            'individual_scan_price': float(os.environ.get('INDIVIDUAL_SCAN_PRICE', '0.70')),
            'group_scan_price': float(os.environ.get('GROUP_SCAN_PRICE', '1.73')),
            'individual_scan_quantity': int(os.environ.get('INDIVIDUAL_SCAN_QUANTITY', '3')),
            'group_scan_quantity': int(os.environ.get('GROUP_SCAN_QUANTITY', '5')),
            
            # Rate Limiting
            'api_rate_limit': int(os.environ.get('API_RATE_LIMIT', '60')),
            'api_rate_window': int(os.environ.get('API_RATE_WINDOW', '60')),
            
            # Cache Settings
            'cache_ttl': int(os.environ.get('CACHE_TTL', '3600')),
            'threat_intel_cache_ttl': int(os.environ.get('THREAT_INTEL_CACHE_TTL', '1800')),
            
            # Security Settings
            'admin_api_key': os.environ.get('ADMIN_API_KEY', ''),
            'readonly_api_key': os.environ.get('READONLY_API_KEY', ''),
        }
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, config_dict):
        """Update multiple configuration values"""
        self.config.update(config_dict)

# Global instances
rate_limiter = RateLimiter()
cache_manager = CacheManager()
config_manager = ConfigManager()

# Utility functions
def get_config(key, default=None):
    """Get configuration value"""
    return config_manager.get(key, default)

def set_config(key, value):
    """Set configuration value"""
    return config_manager.set(key, value)

def cache_get(key):
    """Get cached value"""
    return cache_manager.get(key)

def cache_set(key, value, ttl=None):
    """Set cached value"""
    return cache_manager.set(key, value, ttl)

def check_rate_limit(key, limit=60, window=60):
    """Check rate limit"""
    return rate_limiter.check_rate_limit(key, limit, window)

logger.info("Core services initialized successfully")
