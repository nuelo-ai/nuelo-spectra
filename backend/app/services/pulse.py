"""PulseService: lifecycle orchestration for Pulse detection runs.

Handles credit pre-check, atomic deduction, PulseRun creation, background
pipeline execution, signal persistence, report generation, and refund on failure.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.pulse import build_pulse_graph
from app.database import async_session_maker
from app.models import File, PulseRun, Report, Signal
from app.models.user_credit import UserCredit
from app.services import platform_settings
from app.services.credit import CreditService

logger = logging.getLogger(__name__)


class PulseService:
    """Service for Pulse detection lifecycle management.

    Static methods following the CollectionService pattern.
    """

    @staticmethod
    async def run_detection(
        db: AsyncSession,
        collection_id: UUID,
        user_id: UUID,
        file_ids: list[UUID],
        user_context: str | None = None,
    ) -> PulseRun:
        """Start a new Pulse detection run.

        1. Read cost from platform settings
        2. Atomically deduct credits (402 on insufficient)
        3. Check for active runs (409 on conflict, refund credits)
        4. Create PulseRun with status='pending'
        5. Launch background pipeline task
        6. Return PulseRun

        Args:
            db: Database session.
            collection_id: Target collection UUID.
            user_id: User requesting detection.
            file_ids: List of file UUIDs to analyze.
            user_context: Optional user guidance text.

        Returns:
            PulseRun: Created pulse run record.

        Raises:
            HTTPException: 402 (insufficient credits) or 409 (active run conflict).
        """
        # 1. Read cost
        cost = Decimal(
            str(await platform_settings.get(db, "workspace_credit_cost_pulse"))
        )

        # 2. Pre-fetch balance for 402 body, then attempt deduction
        credit_record = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = credit_record.scalars().first()
        available_balance = float(user_credit.balance) if user_credit else 0.0

        result = await CreditService.deduct_credit(db, user_id, cost)
        if not result.success:
            raise HTTPException(
                status_code=402,
                detail={
                    "detail": "Insufficient credits",
                    "required": float(cost),
                    "available": available_balance,
                },
            )

        # 3. Check for active run on this collection
        active_check = await db.execute(
            select(PulseRun).where(
                PulseRun.collection_id == collection_id,
                PulseRun.status.in_(["pending", "profiling", "analyzing"]),
            )
        )
        existing_run = active_check.scalars().first()
        if existing_run is not None:
            # Refund the just-deducted credits
            await CreditService.refund(
                db,
                user_id,
                cost,
                reason="Pulse detection conflict: active run already exists",
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "detail": "A detection run is already in progress for this collection",
                    "active_run_id": str(existing_run.id),
                },
            )

        # 4. Create PulseRun
        pulse_run = PulseRun(
            collection_id=collection_id,
            status="pending",
            credit_cost=float(cost),
            user_context=user_context,
        )
        db.add(pulse_run)

        # Associate files
        file_result = await db.execute(
            select(File).where(File.id.in_(file_ids))
        )
        files = file_result.scalars().all()
        pulse_run.files = list(files)

        await db.commit()

        # 5. Launch background pipeline
        asyncio.create_task(
            PulseService._run_pipeline(
                pulse_run.id,
                collection_id,
                user_id,
                cost,
                file_ids,
                user_context,
            )
        )

        return pulse_run

    @staticmethod
    async def _run_pipeline(
        pulse_run_id: UUID,
        collection_id: UUID,
        user_id: UUID,
        cost: Decimal,
        file_ids: list[UUID],
        user_context: str | None,
    ) -> None:
        """Execute the Pulse Agent pipeline in background.

        Creates a fresh DB session. Updates PulseRun status through transitions.
        Persists signals and report on success. Refunds credits on failure.

        Args:
            pulse_run_id: PulseRun UUID.
            collection_id: Collection UUID.
            user_id: User UUID for refund.
            cost: Credit cost to refund on failure.
            file_ids: File UUIDs to analyze.
            user_context: Optional user guidance.
        """
        async with async_session_maker() as db:
            try:
                # Load PulseRun
                pr_result = await db.execute(
                    select(PulseRun).where(PulseRun.id == pulse_run_id)
                )
                pulse_run = pr_result.scalars().first()
                if pulse_run is None:
                    logger.error("PulseRun %s not found", pulse_run_id)
                    return

                # Update status: profiling
                pulse_run.status = "profiling"
                pulse_run.started_at = datetime.now(timezone.utc)
                await db.commit()

                # Load files
                file_result = await db.execute(
                    select(File).where(File.id.in_(file_ids))
                )
                files = file_result.scalars().all()

                # Prepare file_data dicts
                file_data = []
                for f in files:
                    try:
                        with open(f.file_path, "rb") as fh:
                            file_bytes = fh.read()
                    except Exception as e:
                        logger.warning("Failed to read file %s: %s", f.id, str(e))
                        file_bytes = b""

                    file_data.append({
                        "file_id": str(f.id),
                        "filename": f.original_filename,
                        "file_bytes": file_bytes,
                        "file_type": f.file_type,
                        "data_summary": f.data_summary or "",
                        "deep_profile": f.deep_profile,
                    })

                # Build and invoke pipeline
                graph = build_pulse_graph()
                initial_state = {
                    "collection_id": str(collection_id),
                    "user_id": str(user_id),
                    "pulse_run_id": str(pulse_run_id),
                    "user_context": user_context or "",
                    "file_data": file_data,
                    "file_profiles": [],
                    "signal_candidates": [],
                    "validated_signals": [],
                    "signals_output": [],
                    "report_content": "",
                    "error": "",
                }

                result = await graph.ainvoke(initial_state)

                # Check for pipeline error
                if result.get("error"):
                    raise RuntimeError(result["error"])

                # Update status: analyzing
                pulse_run.status = "analyzing"
                await db.commit()

                # Persist signals
                for signal_data in result.get("signals_output", []):
                    evidence = signal_data.get("statistical_evidence", {})
                    signal = Signal(
                        collection_id=collection_id,
                        pulse_run_id=pulse_run_id,
                        title=signal_data.get("title", ""),
                        severity=signal_data.get("severity", "info"),
                        category=signal_data.get("category", "general"),
                        analysis=signal_data.get("analysis_text", ""),
                        evidence=evidence if isinstance(evidence, dict) else None,
                        chart_data=signal_data.get("chart_data"),
                        chart_type=signal_data.get("chartType", "bar"),
                    )
                    db.add(signal)

                # Persist deep profiles for uncached files
                file_profiles = result.get("file_profiles", [])
                for i, f in enumerate(files):
                    if f.deep_profile is None and i < len(file_profiles):
                        profile = file_profiles[i]
                        if isinstance(profile, dict) and "error" not in profile:
                            f.deep_profile = profile

                # Generate report
                collection_name = "Collection"
                if hasattr(pulse_run, "collection") and pulse_run.collection:
                    collection_name = pulse_run.collection.name or "Collection"

                report = Report(
                    collection_id=collection_id,
                    pulse_run_id=pulse_run_id,
                    report_type="pulse_detection",
                    title=f"Detection Report - {collection_name}",
                    content=result.get("report_content", ""),
                )
                db.add(report)

                # Update status: completed
                pulse_run.status = "completed"
                pulse_run.completed_at = datetime.now(timezone.utc)
                await db.commit()

                logger.info(
                    "Pulse pipeline completed for run %s: %d signals",
                    pulse_run_id,
                    len(result.get("signals_output", [])),
                )

            except Exception as e:
                logger.error(
                    "Pulse pipeline failed for run %s: %s", pulse_run_id, str(e)
                )
                try:
                    # Refund credits
                    await CreditService.refund(
                        db,
                        user_id,
                        cost,
                        reason=f"Pulse detection failed: {str(e)[:200]}",
                    )

                    # Update PulseRun status to failed
                    pulse_run.status = "failed"
                    pulse_run.error_message = str(e)[:1000]
                    await db.commit()
                except Exception as refund_err:
                    logger.error(
                        "Failed to refund credits for run %s: %s",
                        pulse_run_id,
                        str(refund_err),
                    )

    @staticmethod
    async def get_pulse_run(
        db: AsyncSession, pulse_run_id: UUID
    ) -> PulseRun | None:
        """Get a PulseRun by ID with eager-loaded signals.

        Args:
            db: Database session.
            pulse_run_id: PulseRun UUID.

        Returns:
            PulseRun or None if not found.
        """
        result = await db.execute(
            select(PulseRun)
            .where(PulseRun.id == pulse_run_id)
            .options(selectinload(PulseRun.signals))
        )
        return result.scalars().first()
