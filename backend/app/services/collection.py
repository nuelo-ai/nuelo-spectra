"""CollectionService for workspace CRUD operations."""

from uuid import UUID

from sqlalchemy import select, func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collection import Collection, CollectionFile
from app.models.report import Report
from app.models.signal import Signal


class CollectionService:
    """Static-method service for Collection CRUD, file management, and reports."""

    # --- Collection CRUD ---

    @staticmethod
    async def create_collection(
        db: AsyncSession,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Collection:
        """Create a new collection for the user."""
        collection = Collection(
            user_id=user_id,
            name=name,
            description=description,
        )
        db.add(collection)
        await db.flush()
        await db.refresh(collection)
        return collection

    @staticmethod
    async def list_user_collections(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[dict]:
        """List user's collections with file_count and signal_count.

        Returns list of dicts with keys: collection, file_count, signal_count.
        Ordered by created_at DESC.
        """
        file_count_sq = (
            select(func.count(CollectionFile.id))
            .where(CollectionFile.collection_id == Collection.id)
            .correlate(Collection)
            .scalar_subquery()
            .label("file_count")
        )
        signal_count_sq = (
            select(func.count(Signal.id))
            .where(Signal.collection_id == Collection.id)
            .correlate(Collection)
            .scalar_subquery()
            .label("signal_count")
        )

        stmt = (
            select(Collection, file_count_sq, signal_count_sq)
            .where(Collection.user_id == user_id)
            .order_by(Collection.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            {
                "collection": row[0],
                "file_count": row[1],
                "signal_count": row[2],
            }
            for row in rows
        ]

    @staticmethod
    async def get_user_collection(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
    ) -> Collection | None:
        """Get a single collection filtered by user_id."""
        stmt = select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_collection_detail(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
    ) -> dict | None:
        """Get collection with file_count, signal_count, report_count.

        Returns dict with keys: collection, file_count, signal_count, report_count.
        Returns None if collection not found or not owned by user.
        """
        file_count_sq = (
            select(func.count(CollectionFile.id))
            .where(CollectionFile.collection_id == Collection.id)
            .correlate(Collection)
            .scalar_subquery()
            .label("file_count")
        )
        signal_count_sq = (
            select(func.count(Signal.id))
            .where(Signal.collection_id == Collection.id)
            .correlate(Collection)
            .scalar_subquery()
            .label("signal_count")
        )
        report_count_sq = (
            select(func.count(Report.id))
            .where(Report.collection_id == Collection.id)
            .correlate(Collection)
            .scalar_subquery()
            .label("report_count")
        )

        stmt = (
            select(Collection, file_count_sq, signal_count_sq, report_count_sq)
            .where(
                Collection.id == collection_id,
                Collection.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        return {
            "collection": row[0],
            "file_count": row[1],
            "signal_count": row[2],
            "report_count": row[3],
        }

    @staticmethod
    async def update_collection(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Collection | None:
        """Partial update of a collection. Returns updated collection or None."""
        stmt = select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        result = await db.execute(stmt)
        collection = result.scalar_one_or_none()

        if collection is None:
            return None

        if name is not None:
            collection.name = name
        if description is not None:
            collection.description = description

        await db.flush()
        await db.refresh(collection)
        return collection

    @staticmethod
    async def count_user_collections(
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Count user's collections for limit checking."""
        stmt = select(func.count(Collection.id)).where(
            Collection.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    # --- Collection Files ---

    @staticmethod
    async def add_file_to_collection(
        db: AsyncSession,
        collection_id: UUID,
        file_id: UUID,
    ) -> CollectionFile:
        """Create a junction row linking a file to a collection."""
        collection_file = CollectionFile(
            collection_id=collection_id,
            file_id=file_id,
        )
        db.add(collection_file)
        await db.flush()
        await db.refresh(collection_file)
        return collection_file

    @staticmethod
    async def get_collection_file(
        db: AsyncSession,
        collection_id: UUID,
        file_id: UUID,
    ) -> CollectionFile | None:
        """Check if a file is already linked to a collection."""
        stmt = select(CollectionFile).where(
            CollectionFile.collection_id == collection_id,
            CollectionFile.file_id == file_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_collection_files(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
    ) -> list[CollectionFile]:
        """List files in a collection with eagerly loaded File relationship.

        Verifies collection ownership via user_id filter on the parent collection.
        """
        # Verify ownership first
        ownership_stmt = select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        ownership_result = await db.execute(ownership_stmt)
        if ownership_result.scalar_one_or_none() is None:
            return []

        stmt = (
            select(CollectionFile)
            .where(CollectionFile.collection_id == collection_id)
            .options(selectinload(CollectionFile.file))
            .order_by(CollectionFile.added_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def remove_file_from_collection(
        db: AsyncSession,
        collection_id: UUID,
        file_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Remove a file link from a collection (NOT the File itself).

        Verifies collection ownership. Returns True if deleted, False if not found.
        """
        # Verify ownership
        ownership_stmt = select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        ownership_result = await db.execute(ownership_stmt)
        if ownership_result.scalar_one_or_none() is None:
            return False

        stmt = select(CollectionFile).where(
            CollectionFile.collection_id == collection_id,
            CollectionFile.file_id == file_id,
        )
        result = await db.execute(stmt)
        collection_file = result.scalar_one_or_none()

        if collection_file is None:
            return False

        await db.delete(collection_file)
        await db.flush()
        return True

    @staticmethod
    async def delete_collection(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a collection owned by user_id. Returns True if deleted, False if not found or not owned.

        DB cascade removes child rows (signals, collection_files, pulse_runs, reports).
        """
        stmt = select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        result = await db.execute(stmt)
        collection = result.scalar_one_or_none()

        if collection is None:
            return False

        await db.delete(collection)
        await db.flush()
        return True

    # --- Signals ---

    @staticmethod
    async def list_collection_signals(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
    ) -> list[Signal]:
        """List all signals for a collection, verifying ownership.

        Ordered by created_at DESC.
        """
        # Verify ownership
        ownership_stmt = select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        ownership_result = await db.execute(ownership_stmt)
        if ownership_result.scalar_one_or_none() is None:
            return []

        stmt = (
            select(Signal)
            .where(Signal.collection_id == collection_id)
            .order_by(Signal.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # --- Reports ---

    @staticmethod
    async def list_collection_reports(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
    ) -> list[Report]:
        """List reports for a collection, verifying ownership.

        Ordered by created_at DESC.
        """
        # Verify ownership
        ownership_stmt = select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        ownership_result = await db.execute(ownership_stmt)
        if ownership_result.scalar_one_or_none() is None:
            return []

        stmt = (
            select(Report)
            .where(Report.collection_id == collection_id)
            .order_by(Report.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_report(
        db: AsyncSession,
        report_id: UUID,
        collection_id: UUID,
        user_id: UUID,
    ) -> dict | None:
        """Get report detail with signal_count.

        signal_count = COUNT of signals where pulse_run_id matches report's pulse_run_id.
        Handles None pulse_run_id gracefully (returns 0).

        Returns dict with keys: report, signal_count. Or None if not found.
        """
        # Verify ownership
        ownership_stmt = select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        ownership_result = await db.execute(ownership_stmt)
        if ownership_result.scalar_one_or_none() is None:
            return None

        # Get the report
        report_stmt = select(Report).where(
            Report.id == report_id,
            Report.collection_id == collection_id,
        )
        report_result = await db.execute(report_stmt)
        report = report_result.scalar_one_or_none()

        if report is None:
            return None

        # Count signals for this report's pulse_run_id
        if report.pulse_run_id is not None:
            count_stmt = select(func.count(Signal.id)).where(
                Signal.pulse_run_id == report.pulse_run_id
            )
            count_result = await db.execute(count_stmt)
            signal_count = count_result.scalar_one()
        else:
            signal_count = 0

        return {
            "report": report,
            "signal_count": signal_count,
        }

    @staticmethod
    async def get_report_for_download(
        db: AsyncSession,
        report_id: UUID,
        collection_id: UUID,
        user_id: UUID,
    ) -> Report | None:
        """Get report row for content download, verifying ownership."""
        # Verify ownership
        ownership_stmt = select(Collection.id).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
        ownership_result = await db.execute(ownership_stmt)
        if ownership_result.scalar_one_or_none() is None:
            return None

        stmt = select(Report).where(
            Report.id == report_id,
            Report.collection_id == collection_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
