"""
Alpha AI Autotrader - Monitoring Middleware
Automatically tracks HTTP requests, response times, and errors
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import time
from loguru import logger

from ..core.metrics import get_metrics_collector


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect metrics for all HTTP requests

    Tracks:
    - Request count per endpoint
    - Response times
    - Status codes
    - Errors
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = get_metrics_collector()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        start_time = time.time()
        error_message = None

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Record metrics
            self.metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                error=None if response.status_code < 400 else f"HTTP {response.status_code}"
            )

            # Log slow requests (> 2 seconds)
            if response_time_ms > 2000:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {response_time_ms:.2f}ms"
                )

            return response

        except Exception as e:
            # Record error
            response_time_ms = (time.time() - start_time) * 1000
            error_message = type(e).__name__

            self.metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=500,
                response_time_ms=response_time_ms,
                error=error_message
            )

            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {response_time_ms:.2f}ms - {error_message}"
            )

            # Re-raise to let FastAPI handle it
            raise
