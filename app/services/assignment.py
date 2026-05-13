from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead, LeadStatus, User, UserRole

ACTIVE_LEAD_STATUSES = (LeadStatus.assigned, LeadStatus.accepted)


async def pick_manager_with_lowest_load(session: AsyncSession) -> User | None:
    active_counts = (
        select(Lead.assigned_manager_id, func.count(Lead.id).label("active_count"))
        .where(Lead.status.in_(ACTIVE_LEAD_STATUSES))
        .group_by(Lead.assigned_manager_id)
        .subquery()
    )

    stmt: Select[tuple[User]] = (
        select(User)
        .outerjoin(active_counts, User.id == active_counts.c.assigned_manager_id)
        .where(
            User.role == UserRole.manager,
            User.is_active.is_(True),
            User.can_receive_leads.is_(True),
        )
        .order_by(func.coalesce(active_counts.c.active_count, 0), User.id)
        .limit(1)
    )
    return await session.scalar(stmt)
