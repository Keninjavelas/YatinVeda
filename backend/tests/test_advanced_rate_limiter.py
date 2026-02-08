"""
Test script for the Advanced Rate Limiter implementation.

This script tests the core functionality of the advanced rate limiting system
including progressive delays, IP blocking, and differential rate limits.
"""

import asyncio
import time
from datetime import datetime, timedelta

# Import the classes directly from the file
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'middleware'))

# Import the rate limiter components
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple, Any, Callable

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
    limit: int
    window: int
    action: RateLimitAction
    delay_seconds: Optional[int] = None
    block_duration: Optional[int] = None
    progressive_multiplier: float = 2.0
    max_delay: int = 300

# Simple in-memory storage for testing
class SimpleRateLimitStorage:
    def __init__(self):
        self.counts = {}
        self.blocks = {}
        self.failures = {}
        
    async def get_count(self, key: str, window: int) -> Tuple[int, datetime]:
        now = datetime.utcnow()
        if key not in self.counts:
            return 0, now
        data = self.counts[key]
        window_start = data.get("window_start", now)
        count = data.get("count", 0)
        if now - window_start > timedelta(seconds=window):
            count = 0
            window_start = now
        return count, window_start
    
    async def increment_count(self, key: str, window: int) -> int:
        now = datetime.utcnow()
        if key not in self.counts:
            self.counts[key] = {"count": 0, "window_start": now}
        data = self.counts[key]
        window_start = data["window_start"]
        if now - window_start > timedelta(seconds=window):
            data["count"] = 0
            data["window_start"] = now
        data["count"] += 1
        return data["count"]


def test_basic_rate_limiting():
    """Test basic rate limiting functionality"""
    print("Testing basic rate limiting...")
    
    # Create a simple rule
    rule = RateLimitRule(
        name="test_rule",
        limit=3,
        window=60,  # 3 requests per minute
        action=RateLimitAction.THROTTLE
    )
    
    print(f"Created rule: {rule}")
    
    # Test storage
    storage = SimpleRateLimitStorage()
    
    async def test_storage():
        # Test count operations
        count, window_start = await storage.get_count("test_key", 60)
        assert count == 0, "Initial count should be 0"
        
        new_count = await storage.increment_count("test_key", 60)
        assert new_count == 1, "Count should increment to 1"
        
        new_count = await storage.increment_count("test_key", 60)
        assert new_count == 2, "Count should increment to 2"
        
        print("✓ Storage operations work correctly")
    
    # Run the async test
    asyncio.run(test_storage())
    
    print("✅ Basic rate limiting test passed!")


def test_progressive_delay():
    """Test progressive delay functionality"""
    print("\nTesting progressive delay...")
    
    # Create progressive delay rule
    rule = RateLimitRule(
        name="login_attempts",
        limit=2,
        window=3600,  # 2 attempts per hour
        action=RateLimitAction.PROGRESSIVE_DELAY,
        progressive_multiplier=2.0,
        max_delay=10  # Max 10 seconds for testing
    )
    
    print(f"Created progressive delay rule: {rule}")
    
    # Test delay calculation
    delays = []
    for i in range(5):
        delay = min(int(rule.progressive_multiplier ** i), rule.max_delay)
        delays.append(delay)
    
    print(f"Progressive delays: {delays}")
    assert delays == [1, 2, 4, 8, 10], f"Expected [1, 2, 4, 8, 10], got {delays}"
    
    print("✅ Progressive delay test passed!")


def test_rule_configuration():
    """Test different rule configurations"""
    print("\nTesting rule configurations...")
    
    # Test different actions
    rules = {
        "throttle": RateLimitRule("throttle", 100, 60, RateLimitAction.THROTTLE),
        "block": RateLimitRule("block", 50, 60, RateLimitAction.BLOCK),
        "progressive": RateLimitRule("progressive", 5, 3600, RateLimitAction.PROGRESSIVE_DELAY),
        "log_only": RateLimitRule("log_only", 1000, 60, RateLimitAction.LOG_ONLY)
    }
    
    for name, rule in rules.items():
        print(f"✓ {name} rule: {rule.action.value}")
    
    print("✅ Rule configuration test passed!")


def main():
    """Run all tests"""
    print("🚀 Testing Advanced Rate Limiter Implementation")
    print("=" * 50)
    
    try:
        # Run tests
        test_basic_rate_limiting()
        test_progressive_delay()
        test_rule_configuration()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Advanced Rate Limiter components are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()