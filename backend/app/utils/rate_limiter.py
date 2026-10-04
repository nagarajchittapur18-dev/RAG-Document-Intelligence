import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter per IP/client identifier.
    Thread-safe for standard ASGI async processing.
    """

    def __init__(self, requests_per_minute: int = 120):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._history: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request, custom_limit: int = None) -> None:
        """
        Enforces rate limiting. Raises HTTP 429 if the request limit is exceeded.
        """
        limit = custom_limit or self.requests_per_minute
        now = time.time()
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Prune old timestamps
        cutoff = now - self.window_seconds
        timestamps = [t for t in self._history[client_ip] if t > cutoff]
        self._history[client_ip] = timestamps

        if len(timestamps) >= limit:
            retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({limit} req/min). Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        self._history[client_ip].append(now)

    def reset(self):
        """Clears rate limit history (useful for testing)."""
        self._history.clear()


# Default application-wide rate limiter
rate_limiter = InMemoryRateLimiter(requests_per_minute=120)
