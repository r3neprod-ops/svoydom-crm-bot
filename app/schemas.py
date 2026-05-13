from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import LeadOutcome, LeadStatus, UserRole


class LeadCreate(BaseModel):
    source: str = "svoydom-lugansk.ru"
    external_id: str | None = None
    customer_name: str | None = None
    phone: str
    message: str | None = None
    quiz_answers: dict[str, Any] = Field(default_factory=dict)


class LeadRead(BaseModel):
    id: int
    source: str
    external_id: str | None
    customer_name: str | None
    phone: str
    message: str | None
    quiz_answers: dict[str, Any]
    status: LeadStatus
    outcome: LeadOutcome | None
    assigned_manager_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadClose(BaseModel):
    outcome: LeadOutcome
    comment: str | None = None


class LeadAssign(BaseModel):
    manager_id: int


class LeadFilters(BaseModel):
    status: LeadStatus | None = None
    outcome: LeadOutcome | None = None
    manager_id: int | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


class ManagerCreate(BaseModel):
    telegram_id: int
    full_name: str
    role: UserRole = UserRole.manager
    can_receive_leads: bool = True


class ManagerRead(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    role: UserRole
    is_active: bool
    can_receive_leads: bool

    model_config = ConfigDict(from_attributes=True)


class ManagerUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    can_receive_leads: bool | None = None
