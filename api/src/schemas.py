import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.models import GentleSessionType, PointReason

WELLNESS_DISCLAIMER = (
    "For general wellness only — not a substitute for professional medical care."
)
VITALS_REVIEW_MESSAGE = (
    "Flagged for review — not medical advice. "
    "Consult a qualified professional if concerned."
)

GentleSessionTypeLiteral = Literal[
    "walking", "light_stretching", "gentle_mobility", "breathing_walk"
]


class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    email: str | None = None
    relationship_label: str | None = None
    tenant_id: uuid.UUID | None = None


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    profile_id: uuid.UUID
    tenant_id: uuid.UUID | None
    display_name: str
    disclaimer: str = WELLNESS_DISCLAIMER


class ScopeHeaders(BaseModel):
    user_id: uuid.UUID
    profile_id: uuid.UUID
    tenant_id: uuid.UUID | None = None


class PointsAwarded(BaseModel):
    delta_points: int
    reason: PointReason
    description: str | None = None


class GentleSessionCreate(BaseModel):
    session_type: GentleSessionTypeLiteral
    duration_minutes: int = Field(ge=1, le=480)
    started_at: datetime
    notes: str | None = None


class GentleSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_type: GentleSessionType
    duration_minutes: int
    started_at: datetime
    notes: str | None
    points_awarded: list[PointsAwarded] = []


class StepsUpsert(BaseModel):
    step_count: int = Field(ge=0)


class StepsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    step_count: int
    last_credited_hundreds: int
    points_awarded: list[PointsAwarded] = []


class GoalUpsert(BaseModel):
    daily_step_target: int = Field(ge=500, le=100000)
    daily_active_minutes_target: int = Field(ge=5, le=600)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_step_target: int
    daily_active_minutes_target: int
    disclaimer: str = WELLNESS_DISCLAIMER


class ReminderUpsert(BaseModel):
    enabled: bool = True
    walk_reminder_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    vitals_reminder_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    message: str | None = None


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    walk_reminder_time: str | None
    vitals_reminder_time: str | None
    message: str | None
    disclaimer: str = WELLNESS_DISCLAIMER


class VitalsUpsert(BaseModel):
    bp_systolic: int | None = Field(default=None, ge=60, le=250)
    bp_diastolic: int | None = Field(default=None, ge=40, le=150)
    pulse: int | None = Field(default=None, ge=30, le=220)
    mood: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    notes: str | None = None


class VitalsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    bp_systolic: int | None
    bp_diastolic: int | None
    pulse: int | None
    mood: int | None
    sleep_hours: float | None
    needs_review: bool
    review_message: str | None = None
    disclaimer: str = WELLNESS_DISCLAIMER
    notes: str | None


class PointBalanceResponse(BaseModel):
    balance: int
    disclaimer: str = WELLNESS_DISCLAIMER


class LedgerEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delta_points: int
    reason: PointReason
    description: str | None
    created_at: datetime


class HistoryEntry(BaseModel):
    kind: Literal["session", "steps", "vitals", "ledger"]
    timestamp: datetime
    title: str
    detail: str
    points_delta: int | None = None


class MeResponse(BaseModel):
    user_id: uuid.UUID
    profile_id: uuid.UUID
    tenant_id: uuid.UUID | None
    display_name: str
    balance: int
    today_steps: int
    today_active_minutes: int
    goal: GoalResponse | None
    disclaimer: str = WELLNESS_DISCLAIMER
