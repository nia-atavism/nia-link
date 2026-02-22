"""
Nia-Link Rate Limiter
In-memory token bucket rate limiter per API key
"""

import time
from collections import defaultdict
from fastapi import HTTPException, status, Depends

from .config import get_settings
from .auth import verify_api_key


class RateLimiter:
    """Token bucket rate limiter (per API key, in-memory)"""
    
    def __init__(self):
        self._buckets: dict[str, dict] = defaultdict(lambda: {"tokens": 0, "last_refill": 0.0})
    
    def check(self, api_key: str) -> bool:
        """Check and consume a token. Returns True if allowed, False if rate limited."""
        settings = get_settings()
        rpm = settings.rate_limit_rpm
        
        if rpm <= 0:
            return True  # Unlimited
        
        now = time.time()
        bucket = self._buckets[api_key]
        
        # Initialize on first use
        if bucket["last_refill"] == 0.0:
            bucket["tokens"] = rpm
            bucket["last_refill"] = now
        
        # Refill tokens based on elapsed time
        elapsed = now - bucket["last_refill"]
        refill = elapsed * (rpm / 60.0)  # tokens per second
        bucket["tokens"] = min(rpm, bucket["tokens"] + refill)
        bucket["last_refill"] = now
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False
    
    def get_retry_after(self, api_key: str) -> int:
        """Get seconds until next token is available"""
        settings = get_settings()
        rpm = settings.rate_limit_rpm
        if rpm <= 0:
            return 0
        return max(1, int(60 / rpm))


# Singleton
_limiter = RateLimiter()


async def check_rate_limit(api_key: str = Depends(verify_api_key)) -> str:
    """FastAPI dependency that enforces rate limiting per API key"""
    if not _limiter.check(api_key):
        retry_after = _limiter.get_retry_after(api_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "status": "error",
                "code": "RATE_LIMITED",
                "message": f"Rate limit exceeded. Try again in {retry_after}s.",
                "retry_after": retry_after
            }
        )
    return api_key
