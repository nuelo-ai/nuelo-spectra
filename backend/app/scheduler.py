"""APScheduler setup for periodic credit reset processing.

Runs a job every 15 minutes to check all users with recurring reset policies
(weekly/monthly) and reset their credits when their rolling cycle is due.

Only runs when ENABLE_SCHEDULER=true environment variable is set.
This prevents multiple instances from running the same job.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import func, select

from app.database import async_session_maker
from app.models.collection import Collection
from app.models.pulse_run import PulseRun
from app.models.signal import Signal
from app.models.user import User
from app.models.user_credit import UserCredit
from app.services.credit import CreditService
from app.services.user_class import get_user_classes

logger = logging.getLogger("spectra.scheduler")

scheduler = AsyncIOScheduler()


def is_scheduler_enabled() -> bool:
    """Check if scheduler should run on this instance."""
    return os.environ.get("ENABLE_SCHEDULER", "").lower() in ("true", "1", "yes")


async def process_credit_resets():
    """Periodic job: check all active users and reset credits where due.

    For each user with a recurring reset policy (weekly/monthly):
    1. Check if their rolling cycle has elapsed (anchored to signup or last reset)
    2. If due, lock their credit row and reset balance to tier allocation
    3. Record an auto_reset transaction
    4. Update last_reset_at to prevent double-reset (idempotent)

    Uses its own database session (not request-scoped) since this runs
    outside of any HTTP request context.
    """
    logger.info("Starting credit reset check")
    reset_count = 0

    async with async_session_maker() as db:
        try:
            # Query all active users with their credit rows
            result = await db.execute(
                select(UserCredit, User.user_class, User.created_at)
                .join(User, UserCredit.user_id == User.id)
                .where(User.is_active == True)
            )

            user_classes = get_user_classes()
            rows = result.all()

            for credit, user_class_name, signup_date in rows:
                class_config = user_classes.get(user_class_name, {})
                reset_policy = class_config.get("reset_policy", "none")
                allocation = class_config.get("credits", 0)

                if CreditService.is_reset_due(
                    signup_date, credit.last_reset_at, reset_policy
                ):
                    # Lock the row to prevent concurrent reset
                    locked_result = await db.execute(
                        select(UserCredit)
                        .where(UserCredit.id == credit.id)
                        .with_for_update()
                    )
                    locked_credit = locked_result.scalar_one()

                    # Double-check after locking (another instance may have reset)
                    if CreditService.is_reset_due(
                        signup_date, locked_credit.last_reset_at, reset_policy
                    ):
                        await CreditService.execute_reset(
                            db, locked_credit, allocation, "auto_reset"
                        )
                        reset_count += 1

            await db.commit()
            logger.info(f"Credit reset check complete. Reset {reset_count} user(s).")

        except Exception:
            logger.exception("Error during credit reset processing")
            await db.rollback()


async def process_orphan_refunds():
    """Periodic job: find stuck PulseRuns and refund credits.

    A PulseRun is "orphaned" when:
    - status is still in ('pending', 'profiling', 'analyzing')
    - created_at is older than PULSE_ORPHAN_TIMEOUT_MINUTES
    - completed_at is NULL
    - no Signal rows exist for this run

    For each orphaned run: refund credits to the collection owner, set
    status='failed', set error_message to a timeout message.

    Uses WITH FOR UPDATE SKIP LOCKED to prevent double-refund if two
    scheduler instances fire concurrently (or if _run_pipeline exception
    handler also attempts refund simultaneously).
    """
    from app.config import get_settings
    settings = get_settings()
    timeout_minutes = settings.pulse_orphan_timeout_minutes
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

    logger.info("Starting orphan refund check (cutoff: %s min)", timeout_minutes)
    refund_count = 0

    async with async_session_maker() as db:
        try:
            # Join Collection to get user_id without N+1
            result = await db.execute(
                select(PulseRun, Collection.user_id)
                .join(Collection, PulseRun.collection_id == Collection.id)
                .where(
                    PulseRun.status.in_(["pending", "profiling", "analyzing"]),
                    PulseRun.created_at < cutoff,
                    PulseRun.completed_at.is_(None),
                )
                .with_for_update(skip_locked=True)
            )
            rows = result.all()

            for pulse_run, user_id in rows:
                # Verify no signals exist (avoid refunding partially-completed runs)
                signal_count_result = await db.execute(
                    select(func.count(Signal.id)).where(
                        Signal.pulse_run_id == pulse_run.id
                    )
                )
                signal_count = signal_count_result.scalar_one()

                if signal_count == 0:
                    await CreditService.refund(
                        db,
                        user_id,
                        pulse_run.credit_cost,
                        reason="Pulse orphan timeout: no signals produced within timeout window",
                    )
                    refund_count += 1

                pulse_run.status = "failed"
                pulse_run.error_message = (
                    f"Detection timed out after {timeout_minutes} minutes with no results"
                )

            await db.commit()
            logger.info("Orphan refund check complete. Refunded %d run(s).", refund_count)

        except Exception:
            logger.exception("Error during orphan refund processing")
            await db.rollback()


def setup_scheduler():
    """Configure and return the scheduler. Call start() separately in lifespan."""
    scheduler.add_job(
        process_credit_resets,
        IntervalTrigger(minutes=15),
        id="credit_reset_job",
        replace_existing=True,
        next_run_time=None,  # Don't run immediately on startup; wait for first interval
    )
    scheduler.add_job(
        process_orphan_refunds,
        IntervalTrigger(minutes=5),
        id="pulse_orphan_refund_job",
        replace_existing=True,
        next_run_time=None,
    )
    return scheduler
