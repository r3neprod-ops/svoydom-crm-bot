from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models import User, UserRole


async def require_site_webhook_secret(
    x_webhook_secret: str = Header(default=""), settings: Settings = Depends(get_settings)
) -> None:
    if x_webhook_secret != settings.site_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


async def get_current_user(
    telegram_id: int = Header(alias="X-Telegram-Id"),
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id, User.is_active.is_(True)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
