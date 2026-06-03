"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("relationship_label", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])
    op.create_index("ix_profiles_tenant_id", "profiles", ["tenant_id"])

    gentle_session_type = postgresql.ENUM(
        "walking", "light_stretching", "gentle_mobility", "breathing_walk",
        name="gentle_session_type",
        create_type=True,
    )
    point_reason = postgresql.ENUM(
        "steps_milestone", "session_completed", "active_minutes", "goal_met",
        name="point_reason",
        create_type=True,
    )

    scope_cols = [
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]

    op.create_table(
        "daily_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_credited_hundreds", sa.Integer(), nullable=False, server_default="0"),
        *scope_cols,
        sa.UniqueConstraint("profile_id", "date", name="uq_daily_steps_profile_date"),
    )
    op.create_index("ix_daily_steps_date", "daily_steps", ["date"])
    op.create_index("ix_daily_steps_profile_id", "daily_steps", ["profile_id"])

    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("daily_step_target", sa.Integer(), nullable=False, server_default="5000"),
        sa.Column("daily_active_minutes_target", sa.Integer(), nullable=False, server_default="30"),
        *scope_cols,
        sa.UniqueConstraint("profile_id", name="uq_goals_profile"),
    )

    op.create_table(
        "gentle_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_type", gentle_session_type, nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *scope_cols,
    )

    op.create_table(
        "vitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("bp_systolic", sa.Integer(), nullable=True),
        sa.Column("bp_diastolic", sa.Integer(), nullable=True),
        sa.Column("pulse", sa.Integer(), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=True),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        *scope_cols,
        sa.UniqueConstraint("profile_id", "date", name="uq_vitals_profile_date"),
    )

    op.create_table(
        "reminder_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("walk_reminder_time", sa.String(5), nullable=True),
        sa.Column("vitals_reminder_time", sa.String(5), nullable=True),
        sa.Column("message", sa.String(255), nullable=True),
        *scope_cols,
        sa.UniqueConstraint("profile_id", name="uq_reminder_settings_profile"),
    )

    op.create_table(
        "point_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("delta_points", sa.Integer(), nullable=False),
        sa.Column("reason", point_reason, nullable=False),
        sa.Column("reference_id", sa.String(64), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        *scope_cols,
    )


def downgrade() -> None:
    op.drop_table("point_ledger")
    op.drop_table("reminder_settings")
    op.drop_table("vitals")
    op.drop_table("gentle_sessions")
    op.drop_table("goals")
    op.drop_table("daily_steps")
    op.drop_table("profiles")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS point_reason")
    op.execute("DROP TYPE IF EXISTS gentle_session_type")
