"""API v1 envelope schemas and error code catalog.

Standard response wrappers for all API v1 endpoints. Every response
uses either ApiResponse (success) or ApiErrorResponse (error).
"""

from typing import Any, Literal

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Standard success envelope for API v1 responses."""

    success: bool = True
    credits_used: float | None = None
    data: Any = None


class ApiErrorDetail(BaseModel):
    """Machine-readable error code with human-readable message."""

    code: str
    message: str


class ApiErrorResponse(BaseModel):
    """Standard error envelope for API v1 responses."""

    success: Literal[False] = False
    error: ApiErrorDetail


# Comprehensive error code catalog — machine-readable codes with default messages.
ERROR_CODES: dict[str, str] = {
    "INSUFFICIENT_CREDITS": "Not enough credits. Top up your balance or contact your admin.",
    "FILE_NOT_FOUND": "File not found. Verify the file_id exists and belongs to your account.",
    "INVALID_FILE_TYPE": "Unsupported file type. Allowed: .csv, .xlsx, .xls",
    "FILE_TOO_LARGE": "File exceeds maximum upload size.",
    "FILE_VALIDATION_FAILED": "File could not be parsed. Ensure it is a valid CSV or Excel file.",
    "ONBOARDING_FAILED": "Data analysis failed during file processing. Please try uploading again.",
    "ANALYSIS_FAILED": "Analysis query failed. Credit has been refunded.",
    "ANALYSIS_TIMEOUT": "Analysis exceeded the maximum execution time. Credit has been refunded.",
    "FILE_NOT_ONBOARDED": "File has not been analyzed yet. Wait for processing to complete or re-upload.",
    "TOO_MANY_FILES": "Too many files in request.",
    "INVALID_REQUEST": "Request body is invalid.",
    "UNAUTHORIZED": "Invalid or missing API key.",
    "FORBIDDEN": "Access denied.",
}


def api_error(status_code: int, code: str, message: str | None = None) -> JSONResponse:
    """Build a JSONResponse with ApiErrorResponse body.

    Args:
        status_code: HTTP status code (e.g. 400, 401, 404).
        code: Machine-readable error code from ERROR_CODES.
        message: Human-readable message. Falls back to ERROR_CODES default if None.

    Returns:
        JSONResponse with ApiErrorResponse-shaped body.
    """
    if message is None:
        message = ERROR_CODES.get(code, code)

    body = ApiErrorResponse(
        error=ApiErrorDetail(code=code, message=message),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())
