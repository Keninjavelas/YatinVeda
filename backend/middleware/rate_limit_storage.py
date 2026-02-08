"""
Storage interfaces for rate limiting.
"""

from typing import Tuple, Optional
from datetime import datetime


class RateLimitStorage:
    """Abstract storage interface for rate limiting data"""
    
    async def get_count(self, key: str, window: int) -> Tuple[int, datetime]:
        """Get current count and window start for a key"""
        raise NotImplementedError
    
    async def increment_count(self, key: str, window: int) -> int:
        """Increment count for a key and return new count"""
        raise NotImplementedError
    
    async def set_block(self, key: str, duration: int) -> None:
        """Block a key for specified duration"""
        raise NotImplementedError
    
    async def is_blocked(self, key: str) -> Tuple[bool, Optional[datetime]]:
        """Check if key is blocked and when block expires"""
        raise NotImplementedError
    
    async def get_failure_count(self, key: str) -> int:
        """Get progressive failure count for a key"""
        raise NotImplementedError
    
    async def increment_failure_count(self, key: str) -> int:
        """Increment failure count and return new count"""
        raise NotImplementedError
    
    async def reset_failure_count(self, key: str) -> None:
        """Reset failure count for a key"""
        raise NotImplementedError