from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.models import ActionType, User
from app.schemas import ManagerCreate, ManagerRead, ManagerUpdate
from app.services.leads import log_action

router = APIRouter()


@router.get("/managers", response_model=list[ManagerRead])
async def list_managers(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
) -> list[User]:
    return list((await session.scalars(select(User).order_by(User.id))).all())


@router.post("/managers", response_model=ManagerRead, status_code=status.HTTP_201_CREATED)
async def create_manager(
    payload: ManagerCreate,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
) -> User:
    manager = User(**payload.model_dump())
    session.add(manager)
    await session.flush()
    await log_action(
        session,
        lead_id=None,
        actor_user_id=admin.id,
        action=ActionType.manager_availability_changed,
        payload={"manager_id": manager.id, "created": True},
    )
    await session.commit()
    await session.refresh(manager)
    return manager


@router.patch("/managers/{manager_id}", response_model=ManagerRead)
async def update_manager(
    manager_id: int,
    payload: ManagerUpdate,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
) -> User:
    manager = await session.get(User, manager_id)
    if not manager:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(manager, field, value)
    await log_action(
        session,
        lead_id=None,
        actor_user_id=admin.id,
        action=ActionType.manager_availability_changed,
        payload={"manager_id": manager.id, "changes": changes},
    )
    await session.commit()
    await session.refresh(manager)
    return manager
