"""initial CRM schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_role = sa.Enum("admin", "manager", name="userrole")
    lead_status = sa.Enum("new", "assigned", "accepted", "refused", "closed", name="leadstatus")
    lead_outcome = sa.Enum("success", "no_answer", "declined", "thinking", "duplicate", name="leadoutcome")
    action_type = sa.Enum(
        "lead_created",
        "lead_assigned",
        "lead_accepted",
        "lead_refused",
        "lead_reassigned",
        "reminder_sent",
        "lead_closed",
        "manager_availability_changed",
        name="actiontype",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("can_receive_leads", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"])
    op.create_index(op.f("ix_users_role"), "users", ["role"])
    op.create_index(op.f("ix_users_can_receive_leads"), "users", ["can_receive_leads"])

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("quiz_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", lead_status, nullable=False),
        sa.Column("outcome", lead_outcome, nullable=True),
        sa.Column("assigned_manager_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reminded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index(op.f("ix_leads_source"), "leads", ["source"])
    op.create_index(op.f("ix_leads_phone"), "leads", ["phone"])
    op.create_index(op.f("ix_leads_status"), "leads", ["status"])
    op.create_index(op.f("ix_leads_outcome"), "leads", ["outcome"])
    op.create_index(op.f("ix_leads_assigned_manager_id"), "leads", ["assigned_manager_id"])
    op.create_index(op.f("ix_leads_created_at"), "leads", ["created_at"])
    op.create_index("ix_leads_active_manager", "leads", ["assigned_manager_id", "status"])

    op.create_table(
        "action_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", action_type, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_action_logs_lead_id"), "action_logs", ["lead_id"])
    op.create_index(op.f("ix_action_logs_actor_user_id"), "action_logs", ["actor_user_id"])
    op.create_index(op.f("ix_action_logs_action"), "action_logs", ["action"])
    op.create_index("ix_logs_lead_created", "action_logs", ["lead_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_logs_lead_created", table_name="action_logs")
    op.drop_table("action_logs")
    op.drop_index("ix_leads_active_manager", table_name="leads")
    op.drop_table("leads")
    op.drop_table("users")
    op.execute("DROP TYPE actiontype")
    op.execute("DROP TYPE leadoutcome")
    op.execute("DROP TYPE leadstatus")
    op.execute("DROP TYPE userrole")
