from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.config import get_settings
from app.models import Lead, User


def lead_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Принять", callback_data=f"lead:accept:{lead_id}"),
                InlineKeyboardButton(text="Отказаться", callback_data=f"lead:refuse:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text="Успешно", callback_data=f"lead:close:{lead_id}:success"),
                InlineKeyboardButton(text="Не дозвонился", callback_data=f"lead:close:{lead_id}:no_answer"),
            ],
            [
                InlineKeyboardButton(text="Отказ", callback_data=f"lead:close:{lead_id}:declined"),
                InlineKeyboardButton(text="Думает", callback_data=f"lead:close:{lead_id}:thinking"),
                InlineKeyboardButton(text="Дубль", callback_data=f"lead:close:{lead_id}:duplicate"),
            ],
        ]
    )


async def notify_manager_about_lead(bot: Bot, manager: User, lead: Lead) -> None:
    text = f"Новая заявка #{lead.id}\nТелефон: {lead.phone}\nИмя: {lead.customer_name or '-'}"
    await bot.send_message(manager.telegram_id, text, reply_markup=lead_keyboard(lead.id))


async def notify_admins(bot: Bot, text: str) -> None:
    for telegram_id in get_settings().admin_telegram_ids:
        await bot.send_message(telegram_id, text)
