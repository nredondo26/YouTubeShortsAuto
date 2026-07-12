"""Rate limiting module to prevent API abuse and bans."""

import os
import sys
import time
import json
import threading
from typing import Dict, Optional, Callable
from functools import wraps
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

RATE_LIMITS_FILE = os.path.join(ROOT_DIR, "rate_limits.json")


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, max_requests: int, time_window: int, name: str = "default"):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
            name: Name for this rate limiter
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.name = name
        self.requests = []
        self.lock = threading.Lock()
    
    def _cleanup(self):
        """Remove old requests outside the time window."""
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.time_window]
    
    def acquire(self) -> bool:
        """Try to acquire a request slot.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        with self.lock:
            self._cleanup()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(time.time())
                return True
            
            return False
    
    def wait(self, timeout: float = 60.0) -> bool:
        """Wait until a request slot is available.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if slot acquired, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.acquire():
                return True
            time.sleep(0.1)
        
        return False
    
    def get_wait_time(self) -> float:
        """Get time until next request slot is available."""
        with self.lock:
            self._cleanup()
            
            if len(self.requests) < self.max_requests:
                return 0.0
            
            oldest = self.requests[0]
            return max(0, self.time_window - (time.time() - oldest))
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        with self.lock:
            self._cleanup()
            return {
                "name": self.name,
                "requests_made": len(self.requests),
                "max_requests": self.max_requests,
                "time_window": self.time_window,
                "wait_time": self.get_wait_time(),
            }


class APIRateLimits:
    """Manage rate limits for different APIs."""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.config = self._load_config()
        self._setup_default_limiters()
    
    def _load_config(self) -> Dict:
        """Load rate limit configuration."""
        if os.path.exists(RATE_LIMITS_FILE):
            with open(RATE_LIMITS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Default configuration
        return {
            "ollama": {"max_requests": 10, "time_window": 60},
            "gemini": {"max_requests": 15, "time_window": 60},
            "assemblyai": {"max_requests": 20, "time_window": 60},
            "youtube_upload": {"max_requests": 5, "time_window": 300},
            "youtube_api": {"max_requests": 100, "time_window": 86400},
            "pollinations": {"max_requests": 30, "time_window": 60},
            "edge_tts": {"max_requests": 20, "time_window": 60},
        }
    
    def _save_config(self):
        """Save rate limit configuration."""
        with open(RATE_LIMITS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _setup_default_limiters(self):
        """Setup default rate limiters from config."""
        for api_name, limits in self.config.items():
            self.limiters[api_name] = RateLimiter(
                max_requests=limits["max_requests"],
                time_window=limits["time_window"],
                name=api_name
            )
    
    def get_limiter(self, api_name: str) -> RateLimiter:
        """Get or create a rate limiter for an API."""
        if api_name not in self.limiters:
            # Create with default limits
            self.limiters[api_name] = RateLimiter(
                max_requests=10,
                time_window=60,
                name=api_name
            )
        return self.limiters[api_name]
    
    def check_rate_limit(self, api_name: str) -> bool:
        """Check if request is allowed for an API."""
        limiter = self.get_limiter(api_name)
        return limiter.acquire()
    
    def wait_for_slot(self, api_name: str, timeout: float = 60.0) -> bool:
        """Wait for a request slot for an API."""
        limiter = self.get_limiter(api_name)
        return limiter.wait(timeout)
    
    def update_limits(self, api_name: str, max_requests: int, time_window: int):
        """Update rate limits for an API."""
        self.config[api_name] = {
            "max_requests": max_requests,
            "time_window": time_window
        }
        self.limiters[api_name] = RateLimiter(
            max_requests=max_requests,
            time_window=time_window,
            name=api_name
        )
        self._save_config()
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all rate limiters."""
        return {name: limiter.get_stats() for name, limiter in self.limiters.items()}
    
    def reset(self, api_name: str = None):
        """Reset rate limiter for an API or all APIs."""
        if api_name:
            if api_name in self.limiters:
                self.limiters[api_name].requests = []
        else:
            for limiter in self.limiters.values():
                limiter.requests = []


def rate_limit(api_name: str, wait: bool = True, timeout: float = 60.0):
    """Decorator for rate limiting function calls.
    
    Args:
        api_name: Name of the API to rate limit
        wait: If True, wait for slot; if False, raise error
        timeout: Maximum time to wait for slot
    
    Usage:
        @rate_limit("ollama")
        def call_ollama():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = _global_limits.get_limiter(api_name)
            
            if wait:
                if not limiter.wait(timeout):
                    raise RateLimitError(f"Rate limit timeout for {api_name}")
            else:
                if not limiter.acquire():
                    wait_time = limiter.get_wait_time()
                    raise RateLimitError(
                        f"Rate limit exceeded for {api_name}. "
                        f"Wait {wait_time:.1f}s or use wait=True"
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


# Global rate limits instance
_global_limits = APIRateLimits()


def get_rate_limits() -> APIRateLimits:
    """Get global rate limits instance."""
    return _global_limits


if __name__ == "__main__":
    print("Rate Limits Status:")
    stats = _global_limits.get_all_stats()
    for api, stat in stats.items():
        print(f"  {api}: {stat['requests_made']}/{stat['max_requests']} "
              f"(wait: {stat['wait_time']:.1f}s)")
