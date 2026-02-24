"""API usage logging middleware for all /v1/ requests.

Logs every API v1 request with timing, endpoint, method, and status code
using structured Python logging. DB-level usage logging with credits and
api_key_id is handled explicitly in credit-consuming endpoints (e.g., query.py).

This satisfies APIINFRA-04 (structured request/error logs) while keeping
the middleware lightweight and avoiding DB session lifecycle complications.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("spectra.api.v1")


class ApiUsageMiddleware(BaseHTTPMiddleware):
    """Log all /v1/ API requests with timing and status via structured logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only log API v1 requests
        if not request.url.path.startswith("/v1/") and not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        # Skip health endpoint (noisy)
        if request.url.path.endswith("/health"):
            return await call_next(request)

        start_time = time.monotonic()
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # Structured log for every API v1 request
        logger.info(
            "API request: %s %s -> %d (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            extra={
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
            },
        )

        return response
