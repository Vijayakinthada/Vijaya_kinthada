import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class GentleSessionType(str, PyEnum):
    WALKING = "walking"
    LIGHT_STRETCHING = "light_stretching"
    GENTLE_MOBILITY = "gentle_mobility"
    BREATHING_WALK = "breathing_walk"


class PointReason(str, PyEnum):
    STEPS_MILESTONE = "steps_milestone"
    SESSION_COMPLETED = "session_completed"
    ACTIVE_MINUTES = "active_minutes"
    GOAL_MET = "goal_met"


class ScopeMixin:
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profiles: Mapped[list["Profile"]] = relationship(back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship_label: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="profiles")


class DailySteps(Base, ScopeMixin):
    __tablename__ = "daily_steps"
    __table_args__ = (
        UniqueConstraint("profile_id", "date", name="uq_daily_steps_profile_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    step_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_credited_hundreds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )


class Goal(Base, ScopeMixin):
    __tablename__ = "goals"
    __table_args__ = (
        UniqueConstraint("profile_id", name="uq_goals_profile"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    daily_step_target: Mapped[int] = mapped_column(Integer, nullable=False, default=5000)
    daily_active_minutes_target: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )


class GentleSession(Base, ScopeMixin):
    __tablename__ = "gentle_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_type: Mapped[GentleSessionType] = mapped_column(
        Enum(GentleSessionType, name="gentle_session_type", native_enum=False),
        nullable=False,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Vitals(Base, ScopeMixin):
    __tablename__ = "vitals"
    __table_args__ = (
        UniqueConstraint("profile_id", "date", name="uq_vitals_profile_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    bp_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pulse: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReminderSettings(Base, ScopeMixin):
    __tablename__ = "reminder_settings"
    __table_args__ = (
        UniqueConstraint("profile_id", name="uq_reminder_settings_profile"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    walk_reminder_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    vitals_reminder_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PointLedger(Base, ScopeMixin):
    __tablename__ = "point_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    delta_points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[PointReason] = mapped_column(
        Enum(PointReason, name="point_reason", native_enum=False), nullable=False
    )
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
