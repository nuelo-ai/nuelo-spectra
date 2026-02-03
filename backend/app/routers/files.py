"""File management API endpoints."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.file import FileDetailResponse, FileListItem, FileUploadResponse
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["Files"])

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession
) -> FileUploadResponse:
    """Upload a CSV or Excel file.

    Args:
        file: Uploaded file (CSV, XLSX, or XLS)
        current_user: Authenticated user
        db: Database session

    Returns:
        File upload response with metadata

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
