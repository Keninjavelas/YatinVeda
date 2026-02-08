"""Test rate limiter step by step"""

print("Step 1: Testing basic imports...")
try:
    from enum import Enum
    from dataclasses import dataclass
    from typing import Optional, Dict, List
    from datetime import datetime, timedelta
    print("✓ Basic imports successful")
except Exception as e:
    print(f"✗ Basic imports failed: {e}")
    exit(1)

print("\nStep 2: Testing enum definition...")
try:
    class RateLimitAction(Enum):
        THROTTLE = "throttle"
        BLOCK = "block"
        PROGRESSIVE_DELAY = "progressive_delay"
        LOG_ONLY = "log_only"
    print("✓ Enum definition successful")
except Exception as e:
    print(f"✗ Enum definition failed: {e}")
    exit(1)

print("\nStep 3: Testing dataclass definition...")
try:
    @dataclass
    class RateLimitRule:
        name: str
        limit: int
        window: int
        action: RateLimitAction
        delay_seconds: Optional[int] = None
    print("✓ Dataclass definition successful")
except Exception as e:
    print(f"✗ Dataclass definition failed: {e}")
    exit(1)

print("\nStep 4: Testing class instantiation...")
try:
    rule = RateLimitRule(
        name="test",
        limit=10,
        window=60,
        action=RateLimitAction.THROTTLE
    )
    print(f"✓ Class instantiation successful: {rule}")
except Exception as e:
    print(f"✗ Class instantiation failed: {e}")
    exit(1)

print("\nStep 5: Testing FastAPI imports...")
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response, JSONResponse
    from starlette.types import ASGIApp
    print("✓ FastAPI imports successful")
except Exception as e:
    print(f"✗ FastAPI imports failed: {e}")
    exit(1)

print("\nAll steps completed successfully!")