import uuid
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from src.config import settings
from src.models import (
    DailySteps,
    GentleSession,
    Goal,
    PointLedger,
    PointReason,
    Profile,
    User,
    Vitals,
)
from src.schemas import PointsAwarded, ScopeHeaders, VITALS_REVIEW_MESSAGE


def filter_by_scope(query: Query, model, scope: ScopeHeaders) -> Query:
    """Every read/write query scoped by user_id + profile_id; tenant when header set."""
    query = query.filter(
        model.user_id == scope.user_id,
        model.profile_id == scope.profile_id,
    )
    if scope.tenant_id is not None:
        query = query.filter(model.tenant_id == scope.tenant_id)
    return query


def evaluate_vitals_needs_review(
    pulse: int | None,
    bp_systolic: int | None,
    bp_diastolic: int | None,
) -> bool:
    if pulse is not None and (
        pulse < settings.vitals_pulse_min or pulse > settings.vitals_pulse_max
    ):
        return True
    if bp_systolic is not None and bp_systolic > settings.vitals_bp_systolic_max:
        return True
    if bp_diastolic is not None and bp_diastolic > settings.vitals_bp_diastolic_max:
        return True
    return False


def get_balance(db: Session, scope: ScopeHeaders) -> int:
    q = filter_by_scope(db.query(func.coalesce(func.sum(PointLedger.delta_points), 0)), PointLedger, scope)
    return int(q.scalar() or 0)


def credit_points(
    db: Session,
    scope: ScopeHeaders,
    delta: int,
    reason: PointReason,
    reference_id: str | None = None,
    description: str | None = None,
) -> PointsAwarded:
    entry = PointLedger(
        tenant_id=scope.tenant_id,
        user_id=scope.user_id,
        profile_id=scope.profile_id,
        delta_points=delta,
        reason=reason,
        reference_id=reference_id,
        description=description,
    )
    db.add(entry)
    return PointsAwarded(delta_points=delta, reason=reason, description=description)


def credit_step_milestones(
    db: Session,
    scope: ScopeHeaders,
    row: DailySteps,
) -> list[PointsAwarded]:
    awarded: list[PointsAwarded] = []
    current_hundreds = row.step_count // 100
    while row.last_credited_hundreds < current_hundreds:
        row.last_credited_hundreds += 1
        awarded.append(
            credit_points(
                db,
                scope,
                settings.points_per_100_steps,
                PointReason.STEPS_MILESTONE,
                reference_id=f"{row.date.isoformat()}:{row.last_credited_hundreds}",
                description=f"+{settings.points_per_100_steps} for 100 steps",
            )
        )
    return awarded


def credit_active_minutes(
    db: Session,
    scope: ScopeHeaders,
    target_date: date,
    total_minutes: int,
) -> list[PointsAwarded]:
    awarded: list[PointsAwarded] = []
    bucket = settings.active_minutes_bucket_size
    buckets = total_minutes // bucket
    for i in range(1, buckets + 1):
        ref = f"{target_date.isoformat()}:active:{i}"
        exists = (
            filter_by_scope(
                db.query(PointLedger).filter(
                    PointLedger.reason == PointReason.ACTIVE_MINUTES,
                    PointLedger.reference_id == ref,
                ),
                PointLedger,
                scope,
            )
            .first()
        )
        if not exists:
            awarded.append(
                credit_points(
                    db,
                    scope,
                    settings.points_per_active_minutes_bucket,
                    PointReason.ACTIVE_MINUTES,
                    reference_id=ref,
                    description=f"+{settings.points_per_active_minutes_bucket} for {bucket} active minutes",
                )
            )
    return awarded


def maybe_credit_goal_met(
    db: Session,
    scope: ScopeHeaders,
    target_date: date,
    steps: int,
    active_minutes: int,
    goal: Goal | None,
) -> list[PointsAwarded]:
    if not goal:
        return []
    steps_met = steps >= goal.daily_step_target
    minutes_met = active_minutes >= goal.daily_active_minutes_target
    if not (steps_met or minutes_met):
        return []

    ref = f"{target_date.isoformat()}:goal_met"
    exists = (
        filter_by_scope(
            db.query(PointLedger).filter(
                PointLedger.reason == PointReason.GOAL_MET,
                PointLedger.reference_id == ref,
            ),
            PointLedger,
            scope,
        )
        .first()
    )
    if exists:
        return []

    return [
        credit_points(
            db,
            scope,
            settings.points_goal_met,
            PointReason.GOAL_MET,
            reference_id=ref,
            description="Daily wellness goal met",
        )
    ]


def today_active_minutes(db: Session, scope: ScopeHeaders, target_date: date) -> int:
    q = filter_by_scope(
        db.query(func.coalesce(func.sum(GentleSession.duration_minutes), 0)).filter(
            func.date(GentleSession.started_at) == target_date,
        ),
        GentleSession,
        scope,
    )
    return int(q.scalar() or 0)


def get_profile_or_404(db: Session, scope: ScopeHeaders) -> Profile:
    profile = (
        db.query(Profile)
        .filter(
            Profile.id == scope.profile_id,
            Profile.user_id == scope.user_id,
        )
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for scope")
    return profile


def register_user(
    db: Session,
    display_name: str,
    email: str | None,
    relationship_label: str | None,
    tenant_id: uuid.UUID | None,
) -> tuple[User, Profile]:
    user = User(tenant_id=tenant_id, email=email)
    db.add(user)
    db.flush()
    profile = Profile(
        user_id=user.id,
        tenant_id=tenant_id,
        display_name=display_name,
        relationship_label=relationship_label,
    )
    db.add(profile)
    db.flush()
    goal = Goal(
        tenant_id=tenant_id,
        user_id=user.id,
        profile_id=profile.id,
    )
    db.add(goal)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return user, profile


def vitals_review_message(needs_review: bool) -> str | None:
    return VITALS_REVIEW_MESSAGE if needs_review else None
