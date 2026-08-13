from datetime import datetime, timedelta

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """In-memory rate limiter. Used in tests and as fallback when Redis is unavailable."""

    def __init__(self, app, max_requests: int = 60):
        super().__init__(app, dispatch=self.dispatch)
        self.max_requests = max_requests
        self._store: dict = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"
        now = datetime.utcnow()
        window = self._store.get(key, {"count": 0, "start": now})
        if now - window["start"] > timedelta(minutes=1):
            window = {"count": 0, "start": now}
        window["count"] += 1
        self._store[key] = window
        if window["count"] > self.max_requests:
            logger.warning("rate_limit_exceeded", ip=client_ip, count=window["count"])
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"},
            )
        return await call_next(request)


class RedisRateLimiter(BaseHTTPMiddleware):
    """Redis-backed rate limiter for production. Falls back to in-memory on Redis errors."""

    def __init__(self, app, redis_url: str, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app, dispatch=self.dispatch)
        self.redis_url = redis_url
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis = None
        self._fallback = InMemoryRateLimiter(app, max_requests=max_requests)

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        try:
            redis_client = await self._get_redis()
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, self.window_seconds)
            if count > self.max_requests:
                logger.warning("rate_limit_exceeded", ip=client_ip, count=count, backend="redis")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests"},
                )
        except Exception as exc:
            logger.warning("rate_limit_redis_fallback", error=str(exc))
            return await self._fallback.dispatch(request, call_next)

        return await call_next(request)
