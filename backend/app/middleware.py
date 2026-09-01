"""Middleware for request correlation and logging."""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import get_logger, set_request_id

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        request_id = set_request_id(request_id)

        # Track request timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request
        logger.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )

        return response
