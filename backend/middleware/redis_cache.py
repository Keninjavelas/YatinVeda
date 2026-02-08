"""Redis-based caching for production deployments.

Provides distributed caching with Redis for scalability across multiple instances.
Falls back to in-memory cache if Redis is unavailable.
"""

import redis
import json
import hashlib
from typing import Any, Optional, Callable, Dict
from functools import wraps
from datetime import timedelta
import logging
import os

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based cache with automatic fallback to in-memory cache.
    
    For production deployments with multiple instances.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        max_connections: int = 50,
    ):
        """Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            decode_responses: Decode responses to strings
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
            max_connections: Maximum connection pool size
        """
        self._redis_available = False
        self._fallback_cache: Dict[str, Any] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }
        
        try:
            # Create connection pool
            self._pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                max_connections=max_connections,
            )
            
            # Create Redis client
            self._redis = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            self._redis.ping()
            self._redis_available = True
            logger.info(f"Redis cache initialized: {host}:{port}/{db}")
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
            self._redis_available = False
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}", exc_info=True)
            self._redis_available = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self._redis_available:
                value = self._redis.get(key)
                if value is not None:
                    self._stats["hits"] += 1
                    # Deserialize JSON
                    return json.loads(value) if value else None
                else:
                    self._stats["misses"] += 1
                    return None
            else:
                # Use fallback cache
                if key in self._fallback_cache:
                    self._stats["hits"] += 1
                    return self._fallback_cache[key]
                else:
                    self._stats["misses"] += 1
                    return None
                    
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._stats["errors"] += 1
            self._stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cache value with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self._redis_available:
                # Serialize to JSON
                serialized = json.dumps(value, default=str)
                self._redis.setex(key, ttl, serialized)
                self._stats["sets"] += 1
                return True
            else:
                # Use fallback cache (no TTL in fallback)
                self._fallback_cache[key] = value
                self._stats["sets"] += 1
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            if self._redis_available:
                result = self._redis.delete(key)
                self._stats["deletes"] += 1
                return result > 0
            else:
                if key in self._fallback_cache:
                    del self._fallback_cache[key]
                    self._stats["deletes"] += 1
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful
        """
        try:
            if self._redis_available:
                self._redis.flushdb()
                return True
            else:
                self._fallback_cache.clear()
                return True
                
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self._stats["errors"] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            if self._redis_available:
                return bool(self._redis.exists(key))
            else:
                return key in self._fallback_cache
                
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None on error
        """
        try:
            if self._redis_available:
                return self._redis.incr(key, amount)
            else:
                current = self._fallback_cache.get(key, 0)
                new_value = current + amount
                self._fallback_cache[key] = new_value
                return new_value
                
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict mapping keys to values (missing keys omitted)
        """
        result = {}
        
        try:
            if self._redis_available:
                values = self._redis.mget(keys)
                for key, value in zip(keys, values):
                    if value is not None:
                        result[key] = json.loads(value)
                        self._stats["hits"] += 1
                    else:
                        self._stats["misses"] += 1
            else:
                for key in keys:
                    if key in self._fallback_cache:
                        result[key] = self._fallback_cache[key]
                        self._stats["hits"] += 1
                    else:
                        self._stats["misses"] += 1
                        
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            self._stats["errors"] += 1
        
        return result
    
    def set_many(self, mapping: Dict[str, Any], ttl: int = 300) -> bool:
        """Set multiple values in cache.
        
        Args:
            mapping: Dict mapping keys to values
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            if self._redis_available:
                pipe = self._redis.pipeline()
                for key, value in mapping.items():
                    serialized = json.dumps(value, default=str)
                    pipe.setex(key, ttl, serialized)
                pipe.execute()
                self._stats["sets"] += len(mapping)
                return True
            else:
                self._fallback_cache.update(mapping)
                self._stats["sets"] += len(mapping)
                return True
                
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            self._stats["errors"] += 1
            return False
    
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
        
        stats = {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.2f}%",
            "redis_available": self._redis_available,
            "backend": "redis" if self._redis_available else "in-memory",
        }
        
        # Add Redis-specific stats
        if self._redis_available:
            try:
                info = self._redis.info("stats")
                stats["redis_keyspace_hits"] = info.get("keyspace_hits", 0)
                stats["redis_keyspace_misses"] = info.get("keyspace_misses", 0)
                stats["redis_connected_clients"] = info.get("connected_clients", 0)
                
                # Get memory info
                memory_info = self._redis.info("memory")
                stats["redis_used_memory_human"] = memory_info.get("used_memory_human", "unknown")
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        else:
            stats["entries"] = len(self._fallback_cache)
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health.
        
        Returns:
            Dict with health status
        """
        health = {
            "healthy": False,
            "backend": "redis" if self._redis_available else "in-memory",
            "redis_available": self._redis_available,
        }
        
        try:
            if self._redis_available:
                # Test Redis connection
                self._redis.ping()
                health["healthy"] = True
                health["latency_ms"] = 0  # Could measure actual latency
            else:
                # In-memory cache is always healthy
                health["healthy"] = True
                
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health["error"] = str(e)
            
            # Try to reconnect
            try:
                self._redis = redis.Redis(connection_pool=self._pool)
                self._redis.ping()
                self._redis_available = True
                health["healthy"] = True
                health["reconnected"] = True
                logger.info("Reconnected to Redis")
            except:
                self._redis_available = False
        
        return health


# Global Redis cache instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get or create global Redis cache instance.
    
    Returns:
        RedisCache instance
    """
    global _redis_cache
    
    if _redis_cache is None:
        # Get Redis configuration from environment
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        _redis_cache = RedisCache(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
        )
    
    return _redis_cache


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of serialized arguments
    """
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


def redis_cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results in Redis.
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache key
        
    Usage:
        @redis_cached(ttl=600, key_prefix="guru_list")
        def get_active_gurus():
            # Expensive database query
            return gurus
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_redis_cache()
            
            # Generate cache key
            arg_key = generate_cache_key(*args, **kwargs)
            cache_key = f"{key_prefix}:{func.__name__}:{arg_key}" if key_prefix else f"{func.__name__}:{arg_key}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Add cache control methods to wrapper
        wrapper.cache_clear = lambda: get_redis_cache().clear()
        wrapper.cache_info = lambda: get_redis_cache().get_stats()
        
        return wrapper
    
    return decorator


__all__ = [
    "RedisCache",
    "get_redis_cache",
    "redis_cached",
    "generate_cache_key",
]
