"""Admin dashboard metrics aggregation endpoint."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, case, cast, Date, select

from app.database import get_db
from app.dependencies import CurrentAdmin, DbSession
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.credit_transaction import CreditTransaction
from app.models.file import File
from app.models.user import User
from app.models.user_credit import UserCredit
from app.schemas.admin_dashboard import (
    CreditDistributionEntry,
    CreditSummary,
    DashboardMetricsResponse,
    LowCreditUser,
    TrendPoint,
)

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])


@router.get("", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    admin: CurrentAdmin,
    db: DbSession,
    days: int = Query(default=30, ge=7, le=90),
) -> DashboardMetricsResponse:
    """Return aggregated platform metrics for the admin dashboard.

    Covers DASH-01 through DASH-07 requirements in a single response.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())  # Monday
    month_start = today_start.replace(day=1)
    trend_start = today_start - timedelta(days=days)

    # DASH-01: User counts
    user_counts_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(User.is_active.is_(True)).label("active"),
            func.count().filter(User.is_active.is_(False)).label("inactive"),
            func.count()
            .filter(User.last_login_at >= today_start)
            .label("active_today"),
        ).select_from(User)
    )
    user_counts = user_counts_result.one()

    # DASH-02: Signup counts
    signup_counts_result = await db.execute(
        select(
            func.count()
            .filter(User.created_at >= today_start)
            .label("today"),
            func.count()
            .filter(User.created_at >= week_start)
            .label("this_week"),
            func.count()
            .filter(User.created_at >= month_start)
            .label("this_month"),
        ).select_from(User)
    )
    signup_counts = signup_counts_result.one()

    # DASH-03: Total sessions
    sessions_result = await db.execute(
        select(func.count()).select_from(ChatSession)
    )
    total_sessions = sessions_result.scalar_one()

    # DASH-04: Total files
    files_result = await db.execute(select(func.count()).select_from(File))
    total_files = files_result.scalar_one()

    # DASH-05: Total messages
    messages_result = await db.execute(
        select(func.count()).select_from(ChatMessage)
    )
    total_messages = messages_result.scalar_one()

    # DASH-06: Credit summary
    total_used_result = await db.execute(
        select(func.coalesce(func.sum(CreditTransaction.amount), 0)).where(
            CreditTransaction.transaction_type == "usage"
        )
    )
    # Deductions are stored as negative amounts, so negate the sum
    raw_used = float(total_used_result.scalar_one())
    total_used = abs(raw_used)

    total_remaining_result = await db.execute(
        select(func.coalesce(func.sum(UserCredit.balance), 0))
    )
    total_remaining = float(total_remaining_result.scalar_one())

    # DASH-07: Signup trend (time-series)
    signup_trend_result = await db.execute(
        select(
            cast(User.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(User.created_at >= trend_start)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
    )
    signup_trend = [
        TrendPoint(date=str(row.date), count=row.count)
        for row in signup_trend_result.all()
    ]

    # DASH-07: Message trend (time-series)
    message_trend_result = await db.execute(
        select(
            cast(ChatMessage.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(ChatMessage.created_at >= trend_start)
        .group_by(cast(ChatMessage.created_at, Date))
        .order_by(cast(ChatMessage.created_at, Date))
    )
    message_trend = [
        TrendPoint(date=str(row.date), count=row.count)
        for row in message_trend_result.all()
    ]

    # Credit distribution by user tier
    credit_dist_result = await db.execute(
        select(
            User.user_class.label("tier"),
            func.count().label("user_count"),
            func.coalesce(func.sum(UserCredit.balance), 0).label("total_credits"),
        )
        .join(UserCredit, UserCredit.user_id == User.id, isouter=True)
        .group_by(User.user_class)
        .order_by(User.user_class)
    )
    credit_distribution = [
        CreditDistributionEntry(
            tier=row.tier,
            user_count=row.user_count,
            total_credits=float(row.total_credits),
        )
        for row in credit_dist_result.all()
    ]

    # Low credit users (balance < 10, ordered by balance ASC, limit 20)
    low_credit_result = await db.execute(
        select(
            User.id.label("user_id"),
            User.email,
            func.coalesce(User.first_name, "").label("first_name"),
            func.coalesce(User.last_name, "").label("last_name"),
            UserCredit.balance,
            User.user_class.label("tier"),
        )
        .join(UserCredit, UserCredit.user_id == User.id)
        .where(UserCredit.balance < 10)
        .where(User.is_active.is_(True))
        .order_by(UserCredit.balance.asc())
        .limit(20)
    )
    low_credit_users = [
        LowCreditUser(
            user_id=str(row.user_id),
            email=row.email,
            name=f"{row.first_name} {row.last_name}".strip(),
            balance=float(row.balance),
            tier=row.tier,
        )
        for row in low_credit_result.all()
    ]

    return DashboardMetricsResponse(
        total_users=user_counts.total,
        active_users=user_counts.active,
        inactive_users=user_counts.inactive,
        active_today=user_counts.active_today,
        signups_today=signup_counts.today,
        signups_this_week=signup_counts.this_week,
        signups_this_month=signup_counts.this_month,
        total_sessions=total_sessions,
        total_files=total_files,
        total_messages=total_messages,
        credit_summary=CreditSummary(
            total_used=total_used,
            total_remaining=total_remaining,
        ),
        signup_trend=signup_trend,
        message_trend=message_trend,
        credit_distribution=credit_distribution,
        low_credit_users=low_credit_users,
    )
