"""API v1 query endpoint for synchronous analysis execution with credit handling."""

import time
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

from app.dependencies import ApiAuthUser, DbSession
from app.routers.api_v1.schemas import ApiResponse, api_error
from app.services.agent_service import run_api_query
from app.services.credit import CreditService
from app.services.file import FileService
from app.services.api_usage import ApiUsageService
from app.services import platform_settings

router = APIRouter(tags=["API v1 - Query"])


class ApiQueryRequest(BaseModel):
    """Request body for POST /chat/query."""

    query: str
    file_ids: list[UUID]
    web_search_enabled: bool = False

    @field_validator("file_ids")
    @classmethod
    def at_least_one_file(cls, v: list[UUID]) -> list[UUID]:
        if not v:
            raise ValueError("At least one file_id is required")
        return v


@router.post("/chat/query")
async def api_query(
    body: ApiQueryRequest,
    user: ApiAuthUser,
    db: DbSession,
    request: Request,
):
    """Run a synchronous analysis query against one or more files.

    Deducts credits before execution and refunds on failure.
    Returns the full analysis result in the standard API envelope.
    """
    start_time = time.monotonic()

    # Validate file_ids count against platform limit
    max_files = await platform_settings.get(db, "max_files_per_session")
    if max_files is None:
        max_files = 5  # fallback default
    if len(body.file_ids) > int(max_files):
        return api_error(400, "TOO_MANY_FILES", f"Maximum {int(max_files)} files allowed per query.")

    # Validate file ownership for ALL files before proceeding
    for file_id in body.file_ids:
        file_record = await FileService.get_user_file(db, file_id, user.id)
        if file_record is None:
            return api_error(
                404, "FILE_NOT_FOUND",
                f"File {file_id} not found or does not belong to your account.",
            )
        if file_record.data_summary is None:
            return api_error(
                400, "FILE_NOT_ONBOARDED",
                f"File {file_id} has not been analyzed yet. Wait for processing to complete.",
            )

    # Deduct credit before analysis
    cost_value = await platform_settings.get(db, "default_credit_cost")
    cost = Decimal(str(cost_value))
    api_key_id = getattr(request.state, "api_key_id", None)
    deduction = await CreditService.deduct_credit(db, user.id, cost, api_key_id=api_key_id)
    if not deduction.success:
        return api_error(402, "INSUFFICIENT_CREDITS")
    # Commit credit deduction independently before agent execution
    await db.commit()

    # Run analysis (refund on failure)
    try:
        result = await run_api_query(
            db,
            body.file_ids,
            user.id,
            body.query,
            body.web_search_enabled,
            api_key_id=api_key_id,
            credit_cost=cost,
        )
    except Exception as e:
        # Refund on failure
        await CreditService.refund(db, user.id, cost)
        await db.commit()
        return api_error(
            500, "ANALYSIS_FAILED",
            f"Analysis failed: {str(e)}. Credit has been refunded.",
        )

    # DB usage log for credit tracking
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    try:
        await ApiUsageService.log_request(
            db=db,
            user_id=user.id,
            api_key_id=api_key_id,
            endpoint="/v1/chat/query",
            method="POST",
            status_code=200,
            credits_used=float(cost),
            response_time_ms=elapsed_ms,
        )
        await db.commit()
    except Exception:
        pass  # Don't fail the response if logging fails

    return ApiResponse(success=True, credits_used=float(cost), data=result)
