"""API v1 file context endpoints (get detail, update, suggestions)."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import ApiAuthUser, DbSession
from app.routers.api_v1.schemas import ApiResponse, api_error
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["API v1 - File Context"])


class UpdateContextRequest(BaseModel):
    """Request body for updating file context."""

    user_context: str | None = None


@router.get("/{file_id}/context")
async def get_file_context(
    file_id: UUID,
    user: ApiAuthUser,
    db: DbSession,
):
    """Get full file context: data brief, summary, user context, and suggestions."""
    f = await FileService.get_user_file(db, file_id, user.id)
    if f is None:
        return api_error(404, "FILE_NOT_FOUND")

    return ApiResponse(
        data={
            "id": str(f.id),
            "filename": f.original_filename,
            "data_brief": f.data_summary,
            "data_summary": f.data_summary,
            "user_context": f.user_context,
            "query_suggestions": f.query_suggestions,
            "created_at": f.created_at.isoformat(),
        }
    )


@router.put("/{file_id}/context")
async def update_file_context(
    file_id: UUID,
    body: UpdateContextRequest,
    user: ApiAuthUser,
    db: DbSession,
):
    """Update user context for a file. Only provided fields are updated."""
    f = await FileService.get_user_file(db, file_id, user.id)
    if f is None:
        return api_error(404, "FILE_NOT_FOUND")

    # Update only the fields that are provided (not None)
    if body.user_context is not None:
        f.user_context = body.user_context

    await db.commit()

    return ApiResponse(
        data={
            "id": str(f.id),
            "user_context": f.user_context,
        }
    )


@router.get("/{file_id}/suggestions")
async def get_file_suggestions(
    file_id: UUID,
    user: ApiAuthUser,
    db: DbSession,
):
    """Get query suggestions for a file."""
    f = await FileService.get_user_file(db, file_id, user.id)
    if f is None:
        return api_error(404, "FILE_NOT_FOUND")

    return ApiResponse(
        data={
            "id": str(f.id),
            "query_suggestions": f.query_suggestions or [],
        }
    )
