"""API v1 file management endpoints (upload, list, delete, download)."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from app.config import get_settings
from app.dependencies import ApiAuthUser, DbSession
from app.routers.api_v1.schemas import ApiResponse, api_error
from app.services import agent_service
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["API v1 - Files"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    user: ApiAuthUser,
    db: DbSession,
):
    """Upload a CSV/Excel file and run synchronous onboarding.

    Returns file metadata with data_brief and query_suggestions once
    onboarding completes. The file is saved even if onboarding fails.
    """
    # Validate filename present
    if not file.filename:
        return api_error(400, "INVALID_REQUEST", "Filename is required")

    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return api_error(400, "INVALID_FILE_TYPE")

    # Validate file size (UploadFile.size may be None for chunked uploads)
    settings = get_settings()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if file.size is not None and file.size > max_bytes:
        return api_error(400, "FILE_TOO_LARGE", f"File exceeds maximum size of {settings.max_file_size_mb}MB.")

    # Upload file via FileService (reuses existing logic: chunk write, pandas validation)
    try:
        file_record = await FileService.upload_file(db, user.id, file, ext)
    except ValueError as e:
        return api_error(400, "FILE_VALIDATION_FAILED", str(e))

    # Synchronous onboarding — blocks until complete (per user decision)
    try:
        await agent_service.run_onboarding(db, file_record.id, user.id, "")
        await db.refresh(file_record)
    except Exception:
        # File saved successfully but onboarding failed — caller gets file_id to retry later
        return api_error(
            500,
            "ONBOARDING_FAILED",
            f"Data analysis failed during file processing. File was saved with id {file_record.id}. Please try again later.",
        )

    return ApiResponse(
        data={
            "id": str(file_record.id),
            "filename": file_record.original_filename,
            "data_brief": file_record.data_summary,
            "query_suggestions": file_record.query_suggestions,
            "created_at": file_record.created_at.isoformat(),
        }
    )


@router.get("")
async def list_files(
    user: ApiAuthUser,
    db: DbSession,
):
    """List all files for the authenticated user."""
    files = await FileService.list_user_files(db, user.id)
    return ApiResponse(
        data=[
            {
                "id": str(f.id),
                "filename": f.original_filename,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in files
        ]
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    user: ApiAuthUser,
    db: DbSession,
):
    """Delete a file by ID with ownership check."""
    file_record = await FileService.get_user_file(db, file_id, user.id)
    if file_record is None:
        return api_error(404, "FILE_NOT_FOUND")

    await FileService.delete_file(db, file_id, user.id)
    return ApiResponse(data={"deleted": True})


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    user: ApiAuthUser,
    db: DbSession,
):
    """Download a file as a binary stream. Returns FileResponse, not JSON envelope."""
    file_record = await FileService.get_user_file(db, file_id, user.id)
    if file_record is None:
        return api_error(404, "FILE_NOT_FOUND")

    file_path = Path(file_record.file_path)
    if not file_path.exists():
        return api_error(404, "FILE_NOT_FOUND", "File not found on disk.")

    return FileResponse(
        path=str(file_path),
        filename=file_record.original_filename,
        media_type="application/octet-stream",
    )
