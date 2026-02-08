"""
Simple test of rate limiter classes
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime, timedelta

class RateLimitAction(Enum):
    """Actions to take when rate limit is exceeded"""
    THROTTLE = "throttle"
    BLOCK = "block"
    PROGRESSIVE_DELAY = "progressive_delay"
    LOG_ONLY = "log_only"

@dataclass
class RateLimitRule:
    """Configuration for a rate limiting rule"""
    name: str
    limit: int  # Number of requests
    window: int  # Time window in seconds
    action: RateLimitAction
    delay_seconds: Optional[int] = None
    block_duration: Optional[int] = None
    progressive_multiplier: float = 2.0
    max_delay: int = 300  # Maximum delay in seconds

class SimpleRateLimiter:
    """Simple rate limiter for testing"""
    
    def __init__(self):
        self.rules = {}
        print("SimpleRateLimiter created")

if __name__ == "__main__":
    print("Testing simple rate limiter...")
    limiter = SimpleRateLimiter()
    rule = RateLimitRule(
        name="test",
        limit=10,
        window=60,
        action=RateLimitAction.THROTTLE
    )
    print(f"Rule created: {rule}")
    print("Test successful!")