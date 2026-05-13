from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import ActionLog, ActionType, Lead, LeadStatus, User, UserRole
from app.schemas import LeadClose, LeadCreate
from app.services.assignment import pick_manager_with_lowest_load


def _now() -> datetime:
    return datetime.now(UTC)


async def create_lead(session: AsyncSession, payload: LeadCreate) -> Lead:
    lead = Lead(**payload.model_dump())
    session.add(lead)
    await session.flush()
    await log_action(session, lead.id, None, ActionType.lead_created, payload.model_dump())

    manager = await pick_manager_with_lowest_load(session)
    if manager:
        await assign_lead(session, lead, manager.id, actor_user_id=None, action=ActionType.lead_assigned)

    await session.commit()
    await session.refresh(lead)
    return lead


async def assign_lead(
    session: AsyncSession,
    lead: Lead,
    manager_id: int,
    actor_user_id: int | None,
    action: ActionType = ActionType.lead_assigned,
) -> Lead:
    lead.assigned_manager_id = manager_id
    lead.assigned_at = _now()
    lead.status = LeadStatus.assigned
    lead.last_reminded_at = None
    await log_action(session, lead.id, actor_user_id, action, {"manager_id": manager_id})
    return lead


async def accept_lead(session: AsyncSession, lead: Lead, manager: User) -> Lead:
    if lead.assigned_manager_id != manager.id:
        raise PermissionError("Lead is assigned to another manager")
    lead.status = LeadStatus.accepted
    lead.accepted_at = _now()
    await log_action(session, lead.id, manager.id, ActionType.lead_accepted, {})
    await session.commit()
    await session.refresh(lead)
    return lead


async def refuse_lead(session: AsyncSession, lead: Lead, manager: User, reason: str | None = None) -> Lead:
    if lead.assigned_manager_id != manager.id:
        raise PermissionError("Lead is assigned to another manager")
    previous_manager_id = lead.assigned_manager_id
    lead.status = LeadStatus.refused
    lead.assigned_manager_id = None
    await log_action(
        session,
        lead.id,
        manager.id,
        ActionType.lead_refused,
        {"reason": reason, "previous_manager_id": previous_manager_id},
    )

    next_manager = await pick_manager_with_lowest_load(session)
    if next_manager:
        await assign_lead(session, lead, next_manager.id, manager.id, ActionType.lead_reassigned)

    await session.commit()
    await session.refresh(lead)
    return lead


async def close_lead(session: AsyncSession, lead: Lead, actor: User, payload: LeadClose) -> Lead:
    if actor.role != UserRole.admin and lead.assigned_manager_id != actor.id:
        raise PermissionError("Only admins or assigned managers can close this lead")
    lead.status = LeadStatus.closed
    lead.outcome = payload.outcome
    lead.closed_at = _now()
    await log_action(
        session,
        lead.id,
        actor.id,
        ActionType.lead_closed,
        {"outcome": payload.outcome.value, "comment": payload.comment},
    )
    await session.commit()
    await session.refresh(lead)
    return lead


async def find_overdue_for_reminder(session: AsyncSession) -> list[Lead]:
    settings = get_settings()
    cutoff = _now() - timedelta(minutes=settings.lead_reminder_minutes)
    stmt = select(Lead).where(
        Lead.status == LeadStatus.assigned,
        Lead.assigned_at <= cutoff,
        Lead.last_reminded_at.is_(None),
    )
    return list((await session.scalars(stmt)).all())


async def find_overdue_for_reassign(session: AsyncSession) -> list[Lead]:
    settings = get_settings()
    cutoff = _now() - timedelta(minutes=settings.lead_reassign_minutes)
    stmt = select(Lead).where(Lead.status == LeadStatus.assigned, Lead.assigned_at <= cutoff)
    return list((await session.scalars(stmt)).all())


async def log_action(
    session: AsyncSession,
    lead_id: int | None,
    actor_user_id: int | None,
    action: ActionType,
    payload: dict,
) -> None:
    session.add(
        ActionLog(
            lead_id=lead_id,
            actor_user_id=actor_user_id,
            action=action,
            payload=payload,
        )
    )
