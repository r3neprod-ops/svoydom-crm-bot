import enum
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"


class LeadStatus(str, enum.Enum):
    new = "new"
    assigned = "assigned"
    accepted = "accepted"
    refused = "refused"
    closed = "closed"


class LeadOutcome(str, enum.Enum):
    success = "success"
    no_answer = "no_answer"
    declined = "declined"
    thinking = "thinking"
    duplicate = "duplicate"


class ActionType(str, enum.Enum):
    lead_created = "lead_created"
    lead_assigned = "lead_assigned"
    lead_accepted = "lead_accepted"
    lead_refused = "lead_refused"
    lead_reassigned = "lead_reassigned"
    reminder_sent = "reminder_sent"
    lead_closed = "lead_closed"
    manager_availability_changed = "manager_availability_changed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.manager, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    can_receive_leads: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assigned_leads: Mapped[list["Lead"]] = relationship(back_populates="assigned_manager")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100), default="svoydom-lugansk.ru", index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    quiz_answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.new, index=True)
    outcome: Mapped[LeadOutcome | None] = mapped_column(Enum(LeadOutcome), index=True)
    assigned_manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    assigned_manager: Mapped[User | None] = relationship(back_populates="assigned_leads")
    action_logs: Mapped[list["ActionLog"]] = relationship(back_populates="lead")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[ActionType] = mapped_column(Enum(ActionType), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped[Lead | None] = relationship(back_populates="action_logs")
    actor: Mapped[User | None] = relationship()


Index("ix_leads_active_manager", Lead.assigned_manager_id, Lead.status)
Index("ix_logs_lead_created", ActionLog.lead_id, ActionLog.created_at)
