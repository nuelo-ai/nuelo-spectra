"""File management API endpoints."""

import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import get_settings
from app.database import async_session_maker
from app.dependencies import CurrentUser, DbSession
from app.schemas.file import FileDetailResponse, FileListItem, FileUploadResponse
from app.services import agent_service
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["Files"])

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession,
    user_context: str = Form(default="")
) -> FileUploadResponse:
    """Upload a CSV or Excel file and trigger Onboarding Agent.

    Args:
        file: Uploaded file (CSV, XLSX, or XLS)
        current_user: Authenticated user
        db: Database session
        user_context: Optional user-provided context about the data

    Returns:
        File upload response with metadata (data_summary will be None initially,
        populated by background onboarding task)

    Raises:
        HTTPException: 400 if file type is unsupported or file is invalid
        HTTPException: 413 if file exceeds size limit
    """
    # Extract file extension from original filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_extension = Path(file.filename).suffix.lower()

    # Validate file extension
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Upload and validate file
    try:
        file_record = await FileService.upload_file(
            db,
            current_user.id,
            file,
            file_extension
        )
    except ValueError as e:
        # Pandas validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Trigger onboarding in background task
    async def _run_onboarding_background(file_id: UUID, user_id: UUID, context: str):
        """Background task to run onboarding agent."""
        async with async_session_maker() as background_db:
            try:
                await agent_service.run_onboarding(background_db, file_id, user_id, context)
            except Exception as e:
                # Log error but don't fail upload - user can retry onboarding
                print(f"Background onboarding failed for file {file_id}: {e}")

    asyncio.create_task(_run_onboarding_background(file_record.id, current_user.id, user_context))

    return FileUploadResponse.model_validate(file_record)


@router.get("/", response_model=list[FileListItem])
async def list_files(
    current_user: CurrentUser,
    db: DbSession
) -> list[FileListItem]:
    """List all files for the authenticated user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of user's files with metadata
    """
    files = await FileService.list_user_files(db, current_user.id)
    return [FileListItem.model_validate(f) for f in files]


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file(
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> FileDetailResponse:
    """Get details for a specific file.

    Args:
        file_id: File UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        File details

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
    """
    file = await FileService.get_user_file(db, file_id, current_user.id)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileDetailResponse.model_validate(file)


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> FileResponse:
    """Download a file by returning it as a FileResponse.

    Sets Content-Disposition header with original filename.

    Args:
        file_id: File UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        FileResponse with file content

    Raises:
        HTTPException: 404 if file not found or doesn't exist on disk
    """
    file = await FileService.get_user_file(db, file_id, current_user.id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = Path(file.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    return FileResponse(
        path=str(file_path),
        filename=file.original_filename,
        media_type="application/octet-stream",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> None:
    """Delete a file and its associated data.

    Args:
        file_id: File UUID
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
    """
    success = await FileService.delete_file(db, file_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )


class FileContextUpdate(BaseModel):
    """Request schema for updating file context."""
    context: str


class FileSummaryResponse(BaseModel):
    """Response schema for file summary."""
    data_summary: str | None
    query_suggestions: dict | None = None
    suggestion_auto_send: bool = True
    user_context: str | None


@router.post("/{file_id}/context", response_model=FileDetailResponse)
async def update_file_context(
    file_id: UUID,
    body: FileContextUpdate,
    current_user: CurrentUser,
    db: DbSession
) -> FileDetailResponse:
    """Update user context for a file.

    This endpoint allows users to refine the AI's understanding of their data
    by providing additional context after initial upload.

    Args:
        file_id: File UUID
        body: Context update with additional context string
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated file details with new user_context

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
    """
    # Update context via agent service
    await agent_service.update_user_context(
        db, file_id, current_user.id, body.context
    )

    # Fetch updated file record
    file = await FileService.get_user_file(db, file_id, current_user.id)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileDetailResponse.model_validate(file)


@router.get("/{file_id}/summary", response_model=FileSummaryResponse)
async def get_file_summary(
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> FileSummaryResponse:
    """Get data summary and user context for a file.

    This endpoint is used by the frontend to check if onboarding has completed
    and to retrieve the AI-generated data summary.

    Args:
        file_id: File UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        File summary with data_summary and user_context

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
    """
    file = await FileService.get_user_file(db, file_id, current_user.id)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileSummaryResponse(
        data_summary=file.data_summary,
        query_suggestions=file.query_suggestions,
        suggestion_auto_send=get_settings().suggestion_auto_send,
        user_context=file.user_context,
    )
