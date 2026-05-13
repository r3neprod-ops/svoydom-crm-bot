from app.bot.notifications import notify_admins, notify_manager_about_lead
from app.models import ActionType, LeadStatus
from app.services.assignment import pick_manager_with_lowest_load
from app.services.leads import assign_lead, find_overdue_for_reassign, find_overdue_for_reminder, log_action


async def send_due_reminders(session, bot) -> None:
    for lead in await find_overdue_for_reminder(session):
        if lead.assigned_manager:
            await notify_manager_about_lead(bot, lead.assigned_manager, lead)
        lead.last_reminded_at = lead.assigned_at
        await log_action(session, lead.id, None, ActionType.reminder_sent, {})
    await session.commit()


async def reassign_overdue_leads(session, bot) -> None:
    for lead in await find_overdue_for_reassign(session):
        previous_manager_id = lead.assigned_manager_id
        lead.status = LeadStatus.refused
        lead.assigned_manager_id = None
        manager = await pick_manager_with_lowest_load(session)
        if manager:
            await assign_lead(session, lead, manager.id, None, ActionType.lead_reassigned)
            await notify_manager_about_lead(bot, manager, lead)
        await notify_admins(bot, f"Заявка #{lead.id} передана другому менеджеру после 1 часа")
        await log_action(
            session,
            lead.id,
            None,
            ActionType.lead_reassigned,
            {"previous_manager_id": previous_manager_id, "reason": "timeout"},
        )
    await session.commit()
