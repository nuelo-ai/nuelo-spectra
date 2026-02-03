"""File service layer for upload, validation, and management."""

import asyncio
from pathlib import Path
from uuid import UUID, uuid4

import aiofiles
import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.file import File

# 1MB chunk size for streaming uploads
CHUNK_SIZE = 1024 * 1024


def _validate_file(file_path: str, file_type: str) -> None:
    """Validate CSV or Excel file using pandas.

    Args:
        file_path: Path to the file to validate
        file_type: File type (csv, xlsx, or xls)

    Raises:
        ValueError: If file cannot be read or parsed
    """
    try:
        if file_type == "csv":
            # Try to read first 5 rows as validation
            pd.read_csv(file_path, nrows=5)
        elif file_type in ("xlsx", "xls"):
            # Try to read first 5 rows as validation
            pd.read_excel(file_path, nrows=5)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        raise ValueError(f"Invalid {file_type.upper()} file: {str(e)}")


class FileService:
    """Service for file upload, validation, and management operations."""

    @staticmethod
    async def upload_file(
        db: AsyncSession,
        user_id: UUID,
        upload_file: UploadFile,
        file_extension: str
    ) -> File:
        """Upload and validate a user file.

        Args:
            db: Database session
            user_id: User UUID
            upload_file: FastAPI UploadFile instance
            file_extension: File extension (e.g., '.csv', '.xlsx')

        Returns:
            Created File record

        Raises:
            HTTPException: If file size exceeds limit or validation fails
        """
        settings = get_settings()

        # Create user-specific upload directory
        upload_dir = Path(settings.upload_dir) / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique stored filename
        stored_filename = f"{uuid4()}{file_extension}"
        file_path = upload_dir / stored_filename

        # Get file type from extension
        file_type = file_extension.lstrip(".")

        # Save file to disk with chunked writes and size tracking
        total_size = 0
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024

        try:
            # Write file in chunks to avoid loading entire file into memory
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await upload_file.read(CHUNK_SIZE):
                    total_size += len(chunk)

                    # Check size limit during upload
                    if total_size > max_size_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
                        )

                    await f.write(chunk)

            # Validate file using pandas (in thread to avoid blocking)
            await asyncio.to_thread(_validate_file, str(file_path), file_type)

            # Create database record
            file_record = File(
                user_id=user_id,
                original_filename=upload_file.filename or "unknown",
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_size=total_size,
                file_type=file_type
            )

            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)

            return file_record

        except Exception:
            # Clean up file if any error occurs
            if file_path.exists():
                file_path.unlink()
            raise

    @staticmethod
    async def list_user_files(db: AsyncSession, user_id: UUID) -> list[File]:
        """List all files for a user.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            List of File records ordered by created_at descending
        """
        result = await db.execute(
            select(File)
            .where(File.user_id == user_id)
            .order_by(File.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_file(
        db: AsyncSession,
        file_id: UUID,
        user_id: UUID
    ) -> File | None:
        """Get a specific file for a user.

        Args:
            db: Database session
            file_id: File UUID
            user_id: User UUID (for isolation check)

        Returns:
            File record if found and belongs to user, None otherwise
        """
        result = await db.execute(
            select(File).where(
                File.id == file_id,
                File.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_file(
        db: AsyncSession,
        file_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a file record and its physical file.

        Args:
            db: Database session
            file_id: File UUID
            user_id: User UUID (for isolation check)

        Returns:
            True if file was deleted, False if not found

        Note:
            Uses SQL delete statement for reliable cascade in async context.
            Database-level ON DELETE CASCADE handles related chat_messages.
        """
        # First get the file to retrieve the file_path
        file_record = await FileService.get_user_file(db, file_id, user_id)

        if not file_record:
            return False

        # Store file path before deleting record
        file_path = Path(file_record.file_path)

        # Delete from database (cascade deletes related chat_messages)
        await db.execute(
            delete(File).where(
                File.id == file_id,
                File.user_id == user_id
            )
        )
        await db.commit()

        # Delete physical file
        file_path.unlink(missing_ok=True)

        return True
