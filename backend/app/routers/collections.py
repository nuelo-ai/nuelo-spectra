"""Collections API endpoints for workspace CRUD, file management, and reports."""

import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, UploadFile, status

from app.config import get_settings
from app.database import async_session_maker
from app.dependencies import DbSession, WorkspaceUser
from app.schemas.collection import (
    CollectionCreate,
    CollectionDetailResponse,
    CollectionFileResponse,
    CollectionListItem,
    CollectionUpdate,
    FileLinkRequest,
    ReportDetailResponse,
    ReportListItem,
)
from app.schemas.pulse import PulseRunCreate, PulseRunDetailResponse, PulseRunTriggerResponse, SignalDetailResponse
from app.services import agent_service
from app.services.collection import CollectionService
from app.services.file import FileService
from app.services.pulse import PulseService
from app.services.user_class import get_class_config

router = APIRouter(prefix="/collections", tags=["Collections"])

# Allowed file extensions (same as files router)
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


# --- Collection CRUD ---


@router.post("", response_model=CollectionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionDetailResponse:
    """Create a new collection.

    Checks max_active_collections limit for the user's tier.
    Returns 403 if user is at the limit.
    """
    # Check collection limit
    config = get_class_config(current_user.user_class)
    if config:
        max_collections = config.get("max_active_collections", -1)
        if max_collections != -1:
            current_count = await CollectionService.count_user_collections(db, current_user.id)
            if current_count >= max_collections:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Collection limit reached ({max_collections} active collections)",
                )

    collection = await CollectionService.create_collection(
        db, current_user.id, body.name, body.description
    )
    return CollectionDetailResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        file_count=0,
        signal_count=0,
        report_count=0,
    )


@router.get("", response_model=list[CollectionListItem])
async def list_collections(
    current_user: WorkspaceUser,
    db: DbSession,
) -> list[CollectionListItem]:
    """List all collections for the authenticated user."""
    rows = await CollectionService.list_user_collections(db, current_user.id)
    return [
        CollectionListItem(
            id=row["collection"].id,
            name=row["collection"].name,
            description=row["collection"].description,
            created_at=row["collection"].created_at,
            updated_at=row["collection"].updated_at,
            file_count=row["file_count"],
            signal_count=row["signal_count"],
        )
        for row in rows
    ]


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(
    collection_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionDetailResponse:
    """Get collection detail with file, signal, and report counts."""
    detail = await CollectionService.get_collection_detail(db, collection_id, current_user.id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    c = detail["collection"]
    return CollectionDetailResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        created_at=c.created_at,
        updated_at=c.updated_at,
        file_count=detail["file_count"],
        signal_count=detail["signal_count"],
        report_count=detail["report_count"],
    )


@router.patch("/{collection_id}", response_model=CollectionDetailResponse)
async def update_collection(
    collection_id: UUID,
    body: CollectionUpdate,
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionDetailResponse:
    """Update collection name and/or description."""
    updated = await CollectionService.update_collection(
        db, collection_id, current_user.id, body.name, body.description
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    # Re-fetch detail for counts
    detail = await CollectionService.get_collection_detail(db, collection_id, current_user.id)
    c = detail["collection"]
    return CollectionDetailResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        created_at=c.created_at,
        updated_at=c.updated_at,
        file_count=detail["file_count"],
        signal_count=detail["signal_count"],
        report_count=detail["report_count"],
    )


# --- File endpoints ---


@router.post(
    "/{collection_id}/files",
    response_model=CollectionFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file_to_collection(
    collection_id: UUID,
    file: UploadFile,
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionFileResponse:
    """Upload a file to a collection.

    Creates the File record, links it to the collection, and triggers
    background onboarding.
    """
    # Verify collection ownership
    collection = await CollectionService.get_user_collection(db, collection_id, current_user.id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Upload file
    try:
        file_record = await FileService.upload_file(
            db, current_user.id, file, file_extension
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Link file to collection
    collection_file = await CollectionService.add_file_to_collection(
        db, collection_id, file_record.id
    )

    # Trigger background onboarding
    async def _run_onboarding_background(file_id: UUID, user_id: UUID):
        async with async_session_maker() as background_db:
            try:
                await agent_service.run_onboarding(background_db, file_id, user_id, "")
            except Exception as e:
                print(f"Background onboarding failed for file {file_id}: {e}")

    asyncio.create_task(_run_onboarding_background(file_record.id, current_user.id))

    return CollectionFileResponse(
        id=collection_file.id,
        file_id=file_record.id,
        added_at=collection_file.added_at,
        filename=file_record.original_filename,
        file_size=file_record.file_size,
        data_summary=file_record.data_summary,
    )


@router.post(
    "/{collection_id}/files/link",
    response_model=CollectionFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def link_file_to_collection(
    collection_id: UUID,
    body: FileLinkRequest,
    current_user: WorkspaceUser,
    db: DbSession,
) -> CollectionFileResponse:
    """Link an existing file to a collection."""
    # Verify collection ownership
    collection = await CollectionService.get_user_collection(db, collection_id, current_user.id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Verify file ownership
    file_record = await FileService.get_user_file(db, body.file_id, current_user.id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Check for duplicate
    existing = await CollectionService.get_collection_file(db, collection_id, body.file_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File already linked to this collection",
        )

    # Create link
    collection_file = await CollectionService.add_file_to_collection(
        db, collection_id, body.file_id
    )

    return CollectionFileResponse(
        id=collection_file.id,
        file_id=file_record.id,
        added_at=collection_file.added_at,
        filename=file_record.original_filename,
        file_size=file_record.file_size,
        data_summary=file_record.data_summary,
    )


@router.get("/{collection_id}/files", response_model=list[CollectionFileResponse])
async def list_collection_files(
    collection_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> list[CollectionFileResponse]:
    """List files in a collection with file metadata."""
    collection_files = await CollectionService.list_collection_files(
        db, collection_id, current_user.id
    )
    return [
        CollectionFileResponse(
            id=cf.id,
            file_id=cf.file_id,
            added_at=cf.added_at,
            filename=cf.file.original_filename,
            file_size=cf.file.file_size,
            data_summary=cf.file.data_summary,
        )
        for cf in collection_files
    ]


@router.delete("/{collection_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_file_from_collection(
    collection_id: UUID,
    file_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> None:
    """Remove a file link from a collection (does NOT delete the File)."""
    removed = await CollectionService.remove_file_from_collection(
        db, collection_id, file_id, current_user.id
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in collection",
        )


# --- Signal endpoints ---


@router.get("/{collection_id}/signals", response_model=list[SignalDetailResponse])
async def list_collection_signals(
    collection_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> list[SignalDetailResponse]:
    """List all signals for a collection."""
    signals = await CollectionService.list_collection_signals(
        db, collection_id, current_user.id
    )
    return [SignalDetailResponse.model_validate(s) for s in signals]


# --- Report endpoints ---


@router.get("/{collection_id}/reports", response_model=list[ReportListItem])
async def list_collection_reports(
    collection_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> list[ReportListItem]:
    """List reports for a collection (metadata only, no content)."""
    reports = await CollectionService.list_collection_reports(
        db, collection_id, current_user.id
    )
    return [
        ReportListItem(
            id=r.id,
            title=r.title,
            report_type=r.report_type,
            created_at=r.created_at,
            pulse_run_id=r.pulse_run_id,
        )
        for r in reports
    ]


@router.get(
    "/{collection_id}/reports/{report_id}",
    response_model=ReportDetailResponse,
)
async def get_report_detail(
    collection_id: UUID,
    report_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> ReportDetailResponse:
    """Get report detail with content and signal count."""
    result = await CollectionService.get_report(db, report_id, collection_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    report = result["report"]
    return ReportDetailResponse(
        id=report.id,
        title=report.title,
        report_type=report.report_type,
        content=report.content,
        created_at=report.created_at,
        pulse_run_id=report.pulse_run_id,
        signal_count=result["signal_count"],
    )


@router.get("/{collection_id}/reports/{report_id}/download")
async def download_report(
    collection_id: UUID,
    report_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> Response:
    """Download report as markdown file."""
    report = await CollectionService.get_report_for_download(
        db, report_id, collection_id, current_user.id
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    filename = f"{report.title.replace(' ', '_')}.md"
    return Response(
        content=report.content or "",
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Pulse endpoints ---


@router.post(
    "/{collection_id}/pulse",
    response_model=PulseRunTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_pulse(
    collection_id: UUID,
    body: PulseRunCreate,
    current_user: WorkspaceUser,
    db: DbSession,
) -> PulseRunTriggerResponse:
    """Trigger Pulse detection on selected files in a collection.

    Returns 202 Accepted immediately; frontend polls GET pulse-runs/{run_id} for status.
    Returns 402 if insufficient credits (with required/available balance).
    Returns 409 if a detection run is already active (with active_run_id for resumption).
    """
    # Ownership verification
    collection = await CollectionService.get_user_collection(db, collection_id, current_user.id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    # Delegate to PulseService (handles 402/409 raises, credit deduction, background task)
    pulse_run = await PulseService.run_detection(
        db,
        collection_id=collection_id,
        user_id=current_user.id,
        file_ids=body.file_ids,
        user_context=body.user_context,
    )

    return PulseRunTriggerResponse(
        pulse_run_id=pulse_run.id,
        status=pulse_run.status,
        credit_cost=pulse_run.credit_cost,
    )


@router.get(
    "/{collection_id}/pulse-runs/{run_id}",
    response_model=PulseRunDetailResponse,
)
async def get_pulse_run(
    collection_id: UUID,
    run_id: UUID,
    current_user: WorkspaceUser,
    db: DbSession,
) -> PulseRunDetailResponse:
    """Poll a Pulse detection run for status and results.

    Returns full Signal objects in the signals list when status='completed'.
    Returns error_message when status='failed'.
    Verifies collection ownership to prevent cross-user PulseRun access.
    """
    # Ownership verification on the collection
    collection = await CollectionService.get_user_collection(db, collection_id, current_user.id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    pulse_run = await PulseService.get_pulse_run(db, run_id)
    if pulse_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pulse run not found")

    # Cross-check: ensure run belongs to this collection (prevents ownership bypass)
    if pulse_run.collection_id != collection_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pulse run not found")

    data = {
        **pulse_run.__dict__,
        "signal_count": len(pulse_run.signals),
        "signals": pulse_run.signals,
    }
    return PulseRunDetailResponse.model_validate(data)
