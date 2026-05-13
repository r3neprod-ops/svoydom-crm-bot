from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead
from app.schemas import LeadFilters


async def build_leads_export(session: AsyncSession, filters: LeadFilters) -> BytesIO:
    stmt = select(Lead).order_by(Lead.created_at.desc())
    if filters.status:
        stmt = stmt.where(Lead.status == filters.status)
    if filters.outcome:
        stmt = stmt.where(Lead.outcome == filters.outcome)
    if filters.manager_id:
        stmt = stmt.where(Lead.assigned_manager_id == filters.manager_id)
    if filters.created_from:
        stmt = stmt.where(Lead.created_at >= filters.created_from)
    if filters.created_to:
        stmt = stmt.where(Lead.created_at <= filters.created_to)

    leads = list((await session.scalars(stmt)).all())

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Leads"
    sheet.append([
        "ID",
        "Created At",
        "Source",
        "Name",
        "Phone",
        "Status",
        "Outcome",
        "Manager ID",
        "Message",
        "Quiz Answers",
    ])
    for lead in leads:
        sheet.append([
            lead.id,
            lead.created_at.isoformat() if lead.created_at else None,
            lead.source,
            lead.customer_name,
            lead.phone,
            lead.status.value,
            lead.outcome.value if lead.outcome else None,
            lead.assigned_manager_id,
            lead.message,
            str(lead.quiz_answers),
        ])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output
