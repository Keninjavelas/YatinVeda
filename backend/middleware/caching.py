"""Caching utilities for YatinVeda backend.

Provides in-memory caching for expensive operations like guru lists,
popular posts, and chart calculations. Uses simple TTL-based caching
with automatic expiration.
"""

import time
from typing import Any, Optional, Callable, Dict
from functools import wraps
import hashlib
import json
from datetime import datetime, timedelta


class SimpleCache:
    """Simple in-memory cache with TTL support.
    
    For production, consider using Redis or Memcached.
    This implementation is suitable for single-server deployments.
    """
    
    def __init__(self):
        """Initialize cache storage."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._stats["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry["expires_at"] < time.time():
            del self._cache[key]
            self._stats["misses"] += 1
            return None
        
        self._stats["hits"] += 1
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set cache value with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }
        self._stats["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """Delete cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            self._stats["deletes"] += 1
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry["expires_at"] < now
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with hit/miss rates and entry count
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )
        
        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.2f}%",
            "entries": len(self._cache),
        }


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance."""
    return _cache


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of serialized arguments
    """
    # Create deterministic string from args
    key_parts = []
    
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(json.dumps(arg, sort_keys=True, default=str))
    
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={json.dumps(v, sort_keys=True, default=str)}")
    
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache key
        
    Usage:
        @cached(ttl=600, key_prefix="guru_list")
        def get_active_gurus():
            # Expensive database query
            return gurus
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            arg_key = generate_cache_key(*args, **kwargs)
            cache_key = f"{key_prefix}:{func.__name__}:{arg_key}" if key_prefix else f"{func.__name__}:{arg_key}"
            
            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Add cache control methods to wrapper
        wrapper.cache_clear = lambda: _cache.delete(f"{key_prefix}:{func.__name__}")
        wrapper.cache_info = lambda: _cache.get_stats()
        
        return wrapper
    
    return decorator


# Predefined TTL values for different data types
class CacheTTL:
    """Standard TTL values for different cache categories."""
    
    # Short-lived (frequently changing data)
    SHORT = 60  # 1 minute
    
    # Medium-lived (semi-static data)
    MEDIUM = 300  # 5 minutes
    
    # Long-lived (rarely changing data)
    LONG = 900  # 15 minutes
    
    # Extra long (static configuration)
    EXTRA_LONG = 3600  # 1 hour
    
    # Specific use cases
    GURU_LIST = 600  # 10 minutes
    POPULAR_POSTS = 180  # 3 minutes
    USER_PROFILE = 300  # 5 minutes
    CHART_CALCULATION = 1800  # 30 minutes
    COMMUNITY_STATS = 300  # 5 minutes
    EVENT_LIST = 600  # 10 minutes


def invalidate_cache(pattern: str = None) -> int:
    """Invalidate cache entries matching pattern.
    
    Args:
        pattern: Optional pattern to match (simple substring match)
        
    Returns:
        Number of entries invalidated
    """
    cache = get_cache()
    
    if pattern is None:
        cache.clear()
        return -1  # All entries cleared
    
    # Find matching keys
    matching_keys = [
        key for key in cache._cache.keys()
        if pattern in key
    ]
    
    # Delete matching entries
    for key in matching_keys:
        cache.delete(key)
    
    return len(matching_keys)


def cache_guru_list(func: Callable) -> Callable:
    """Specialized decorator for caching guru lists."""
    return cached(ttl=CacheTTL.GURU_LIST, key_prefix="guru_list")(func)


def cache_popular_posts(func: Callable) -> Callable:
    """Specialized decorator for caching popular posts."""
    return cached(ttl=CacheTTL.POPULAR_POSTS, key_prefix="popular_posts")(func)


def cache_user_profile(func: Callable) -> Callable:
    """Specialized decorator for caching user profiles."""
    return cached(ttl=CacheTTL.USER_PROFILE, key_prefix="user_profile")(func)


def cache_chart_calculation(func: Callable) -> Callable:
    """Specialized decorator for caching chart calculations."""
    return cached(ttl=CacheTTL.CHART_CALCULATION, key_prefix="chart_calc")(func)


# Background cleanup task
def cleanup_expired_cache():
    """Clean up expired cache entries.
    
    Call this periodically (e.g., every 5 minutes) from a background task.
    """
    cache = get_cache()
    removed = cache.cleanup_expired()
    return removed


__all__ = [
    "SimpleCache",
    "get_cache",
    "cached",
    "CacheTTL",
    "invalidate_cache",
    "cache_guru_list",
    "cache_popular_posts",
    "cache_user_profile",
    "cache_chart_calculation",
    "cleanup_expired_cache",
]
