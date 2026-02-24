"""ApiUsageService for logging per-request API v1 usage."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_usage_log import ApiUsageLog


class ApiUsageService:
    """Service for recording API v1 request usage."""

    @staticmethod
    async def log_request(
        db: AsyncSession,
        user_id: UUID,
        api_key_id: UUID | None,
        endpoint: str,
        method: str,
        status_code: int,
        credits_used: float,
        response_time_ms: int,
        error_code: str | None = None,
    ) -> ApiUsageLog:
        """Log an API v1 request.

        Creates an ApiUsageLog record. Uses db.flush() (not commit) so the
        caller controls the transaction boundary per project convention.
        """
        log = ApiUsageLog(
            user_id=user_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            credits_used=credits_used,
            response_time_ms=response_time_ms,
            error_code=error_code,
        )
        db.add(log)
        await db.flush()
        return log
