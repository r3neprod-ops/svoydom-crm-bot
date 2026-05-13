from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import Lead, LeadOutcome, User
from app.schemas import LeadClose
from app.services.leads import accept_lead, close_lead, refuse_lead

router = Router()


@router.callback_query(F.data.startswith("lead:accept:"))
async def accept_callback(callback: CallbackQuery) -> None:
    lead_id = int(callback.data.split(":")[-1])
    async with AsyncSessionLocal() as session:
        manager = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        lead = await session.get(Lead, lead_id)
        if not manager or not lead:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        try:
            await accept_lead(session, lead, manager)
            await callback.answer("Заявка принята")
        except PermissionError as exc:
            await callback.answer(str(exc), show_alert=True)


@router.callback_query(F.data.startswith("lead:refuse:"))
async def refuse_callback(callback: CallbackQuery) -> None:
    lead_id = int(callback.data.split(":")[-1])
    async with AsyncSessionLocal() as session:
        manager = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        lead = await session.get(Lead, lead_id)
        if not manager or not lead:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        try:
            await refuse_lead(session, lead, manager)
            await callback.answer("Отказ сохранен, заявка передана дальше")
        except PermissionError as exc:
            await callback.answer(str(exc), show_alert=True)


@router.callback_query(F.data.startswith("lead:close:"))
async def close_callback(callback: CallbackQuery) -> None:
    _, _, lead_id, outcome = callback.data.split(":")
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        lead = await session.get(Lead, int(lead_id))
        if not user or not lead:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        try:
            await close_lead(session, lead, user, LeadClose(outcome=LeadOutcome(outcome)))
            await callback.answer("Заявка закрыта")
        except PermissionError as exc:
            await callback.answer(str(exc), show_alert=True)
