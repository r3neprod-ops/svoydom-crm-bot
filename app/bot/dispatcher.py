from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import get_settings


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def create_bot() -> Bot:
    settings = get_settings()
    return Bot(token=settings.bot_token)
