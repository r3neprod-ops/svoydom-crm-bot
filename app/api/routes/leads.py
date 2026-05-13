from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin, require_site_webhook_secret
from app.core.database import get_session
from app.models import Lead, LeadStatus, User, UserRole
from app.schemas import LeadAssign, LeadClose, LeadCreate, LeadFilters, LeadRead
from app.services.export import build_leads_export
from app.services.leads import assign_lead, close_lead, create_lead

router = APIRouter()


@router.post("/site/leads", response_model=LeadRead, dependencies=[Depends(require_site_webhook_secret)])
async def receive_site_lead(payload: LeadCreate, session: AsyncSession = Depends(get_session)) -> Lead:
    return await create_lead(session, payload)


@router.get("/leads", response_model=list[LeadRead])
async def list_leads(
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[Lead]:
    stmt = select(Lead).order_by(Lead.created_at.desc())
    if current_user.role != UserRole.admin:
        stmt = stmt.where(Lead.assigned_manager_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Lead.status == status_filter)
    return list((await session.scalars(stmt)).all())


@router.post("/leads/{lead_id}/assign", response_model=LeadRead)
async def manually_assign_lead(
    lead_id: int,
    payload: LeadAssign,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
) -> Lead:
    lead = await session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    await assign_lead(session, lead, payload.manager_id, admin.id)
    await session.commit()
    await session.refresh(lead)
    return lead


@router.post("/leads/{lead_id}/close", response_model=LeadRead)
async def close_lead_endpoint(
    lead_id: int,
    payload: LeadClose,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Lead:
    lead = await session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    try:
        return await close_lead(session, lead, current_user, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/leads/export.xlsx")
async def export_leads(
    filters: LeadFilters = Depends(),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
) -> Response:
    output = await build_leads_export(session, filters)
    return Response(
        output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"},
    )
