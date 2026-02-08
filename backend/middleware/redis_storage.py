"""
Redis storage implementation for advanced rate limiting.
"""

import logging
from typing import Tuple, Optional
from datetime import datetime, timedelta
from .rate_limit_storage import RateLimitStorage

# Redis imports (optional dependency)
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RedisRateLimitStorage(RateLimitStorage):
    """Redis-backed storage for rate limiting"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is required for RedisRateLimitStorage. Install with: pip install redis")
        
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.key_prefix = "ratelimit:"
        
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client, creating if necessary"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client
    
    async def get_count(self, key: str, window: int) -> Tuple[int, datetime]:
        """Get current count and window start for a key"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}count:{key}"
            
            # Get current count and timestamp
            pipe = client.pipeline()
            pipe.hget(redis_key, "count")
            pipe.hget(redis_key, "window_start")
            results = await pipe.execute()
            
            count = int(results[0]) if results[0] else 0
            window_start_str = results[1]
            
            if window_start_str:
                window_start = datetime.fromisoformat(window_start_str)
                # Check if window has expired
                if datetime.utcnow() - window_start > timedelta(seconds=window):
                    count = 0
                    window_start = datetime.utcnow()
            else:
                window_start = datetime.utcnow()
            
            return count, window_start
            
        except Exception as e:
            logger.error(f"Redis error getting count for {key}: {str(e)}")
            return 0, datetime.utcnow()
    
    async def increment_count(self, key: str, window: int) -> int:
        """Increment count for a key and return new count"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}count:{key}"
            
            now = datetime.utcnow()
            
            # Use Lua script for atomic increment with window management
            lua_script = """
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local now = ARGV[2]
            
            local current = redis.call('HMGET', key, 'count', 'window_start')
            local count = tonumber(current[1]) or 0
            local window_start = current[2]
            
            -- Check if window has expired
            if window_start then
                local window_start_time = redis.call('TIME')[1] - window
                if tonumber(window_start) < window_start_time then
                    count = 0
                    window_start = now
                end
            else
                window_start = now
            end
            
            count = count + 1
            
            redis.call('HMSET', key, 'count', count, 'window_start', window_start)
            redis.call('EXPIRE', key, window * 2)  -- Set expiration to 2x window
            
            return count
            """
            
            count = await client.eval(lua_script, 1, redis_key, window, now.isoformat())
            return int(count)
            
        except Exception as e:
            logger.error(f"Redis error incrementing count for {key}: {str(e)}")
            return 1
    
    async def set_block(self, key: str, duration: int) -> None:
        """Block a key for specified duration"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}block:{key}"
            
            expires_at = datetime.utcnow() + timedelta(seconds=duration)
            await client.setex(redis_key, duration, expires_at.isoformat())
            
        except Exception as e:
            logger.error(f"Redis error setting block for {key}: {str(e)}")
    
    async def is_blocked(self, key: str) -> Tuple[bool, Optional[datetime]]:
        """Check if key is blocked and when block expires"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}block:{key}"
            
            expires_str = await client.get(redis_key)
            if expires_str:
                expires_at = datetime.fromisoformat(expires_str)
                if datetime.utcnow() < expires_at:
                    return True, expires_at
                else:
                    # Block has expired, clean up
                    await client.delete(redis_key)
            
            return False, None
            
        except Exception as e:
            logger.error(f"Redis error checking block for {key}: {str(e)}")
            return False, None
    
    async def get_failure_count(self, key: str) -> int:
        """Get progressive failure count for a key"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}failures:{key}"
            
            count = await client.get(redis_key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Redis error getting failure count for {key}: {str(e)}")
            return 0
    
    async def increment_failure_count(self, key: str) -> int:
        """Increment failure count and return new count"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}failures:{key}"
            
            # Increment with expiration (failures reset after 1 hour)
            count = await client.incr(redis_key)
            await client.expire(redis_key, 3600)  # 1 hour
            
            return count
            
        except Exception as e:
            logger.error(f"Redis error incrementing failure count for {key}: {str(e)}")
            return 1
    
    async def reset_failure_count(self, key: str) -> None:
        """Reset failure count for a key"""
        try:
            client = await self._get_redis()
            redis_key = f"{self.key_prefix}failures:{key}"
            await client.delete(redis_key)
            
        except Exception as e:
            logger.error(f"Redis error resetting failure count for {key}: {str(e)}")