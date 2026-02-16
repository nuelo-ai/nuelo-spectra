"""Admin token reissue middleware for sliding window session management.

On every successful admin API response (except login), reissues a fresh JWT
with updated iat/exp claims and returns it in the X-Admin-Token response header.
The admin frontend reads this header and updates its stored token.
"""

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings


class AdminTokenReissueMiddleware(BaseHTTPMiddleware):
    """Reissue admin JWT on every successful admin API response (sliding window)."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Only reissue for admin routes with successful responses
        if not request.url.path.startswith("/api/admin"):
            return response
        if response.status_code >= 400:
            return response

        # Skip login endpoint (it issues its own token)
        if request.url.path.endswith("/auth/login"):
            return response

        # Extract and decode current token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return response

        token = auth_header[7:]
        settings = get_settings()

        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            if not payload.get("is_admin"):
                return response

            # Reissue with fresh iat and exp
            from app.utils.security import create_admin_tokens

            new_tokens = create_admin_tokens(payload["sub"], settings)
            response.headers["X-Admin-Token"] = new_tokens["access_token"]
        except jwt.InvalidTokenError:
            pass  # Don't break the response if token decode fails

        return response
