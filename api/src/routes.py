from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.models import (
    DailySteps,
    GentleSession,
    GentleSessionType,
    Goal,
    PointLedger,
    ReminderSettings,
    Vitals,
)
from src.schemas import (
    GentleSessionCreate,
    GentleSessionResponse,
    GoalResponse,
    GoalUpsert,
    HistoryEntry,
    LedgerEntry,
    MeResponse,
    PointBalanceResponse,
    PointReason,
    RegisterRequest,
    RegisterResponse,
    ReminderResponse,
    ReminderUpsert,
    ScopeHeaders,
    StepsResponse,
    StepsUpsert,
    VitalsResponse,
    VitalsUpsert,
    WELLNESS_DISCLAIMER,
)
from src.services import (
    credit_active_minutes,
    credit_points,
    credit_step_milestones,
    evaluate_vitals_needs_review,
    filter_by_scope,
    get_balance,
    get_profile_or_404,
    maybe_credit_goal_met,
    register_user,
    today_active_minutes,
    vitals_review_message,
)

router = APIRouter(prefix=settings.api_prefix)


def get_scope(request: Request) -> ScopeHeaders:
    scope = getattr(request.state, "scope", None)
    if not scope:
        raise HTTPException(status_code=401, detail="Request not scoped")
    return scope


DbSession = Annotated[Session, Depends(get_db)]
Scope = Annotated[ScopeHeaders, Depends(get_scope)]


@router.post("/register", response_model=RegisterResponse)
def post_register(body: RegisterRequest, db: DbSession):
    user, profile = register_user(
        db,
        display_name=body.display_name,
        email=body.email,
        relationship_label=body.relationship_label,
        tenant_id=body.tenant_id,
    )
    return RegisterResponse(
        user_id=user.id,
        profile_id=profile.id,
        tenant_id=user.tenant_id,
        display_name=profile.display_name,
    )


@router.get("/me", response_model=MeResponse)
def get_me(db: DbSession, scope: Scope):
    profile = get_profile_or_404(db, scope)
    today = date.today()
    steps_row = filter_by_scope(
        db.query(DailySteps).filter(DailySteps.date == today),
        DailySteps,
        scope,
    ).first()
    goal_row = filter_by_scope(db.query(Goal), Goal, scope).first()
    return MeResponse(
        user_id=scope.user_id,
        profile_id=scope.profile_id,
        tenant_id=scope.tenant_id,
        display_name=profile.display_name,
        balance=get_balance(db, scope),
        today_steps=steps_row.step_count if steps_row else 0,
        today_active_minutes=today_active_minutes(db, scope, today),
        goal=GoalResponse.model_validate(goal_row) if goal_row else None,
    )


@router.post("/sessions", response_model=GentleSessionResponse)
def create_session(body: GentleSessionCreate, db: DbSession, scope: Scope):
    get_profile_or_404(db, scope)
    try:
        session_type = GentleSessionType(body.session_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Session type not allowed. Wellness-only types: walking, light_stretching, gentle_mobility, breathing_walk",
        ) from exc

    session = GentleSession(
        tenant_id=scope.tenant_id,
        user_id=scope.user_id,
        profile_id=scope.profile_id,
        session_type=session_type,
        duration_minutes=body.duration_minutes,
        started_at=body.started_at,
        notes=body.notes,
    )
    db.add(session)
    db.flush()

    awarded = [
        credit_points(
            db,
            scope,
            settings.points_per_session,
            PointReason.SESSION_COMPLETED,
            reference_id=str(session.id),
            description=f"Gentle {session_type.value} session completed",
        )
    ]

    target_date = body.started_at.date()
    total_minutes = today_active_minutes(db, scope, target_date) + body.duration_minutes
    awarded.extend(credit_active_minutes(db, scope, target_date, total_minutes))

    goal = filter_by_scope(db.query(Goal), Goal, scope).first()
    steps_row = filter_by_scope(
        db.query(DailySteps).filter(DailySteps.date == target_date),
        DailySteps,
        scope,
    ).first()
    awarded.extend(
        maybe_credit_goal_met(
            db,
            scope,
            target_date,
            steps_row.step_count if steps_row else 0,
            total_minutes,
            goal,
        )
    )

    db.commit()
    db.refresh(session)
    return GentleSessionResponse.model_validate(session).model_copy(
        update={"points_awarded": awarded}
    )


@router.get("/sessions", response_model=list[GentleSessionResponse])
def list_sessions(
    db: DbSession,
    scope: Scope,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
):
    q = filter_by_scope(db.query(GentleSession), GentleSession, scope)
    if from_date:
        q = q.filter(GentleSession.started_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        q = q.filter(GentleSession.started_at <= datetime.combine(to_date, datetime.max.time()))
    return [GentleSessionResponse.model_validate(s) for s in q.order_by(GentleSession.started_at.desc()).all()]


@router.put("/steps/{target_date}", response_model=StepsResponse)
def upsert_steps(target_date: date, body: StepsUpsert, db: DbSession, scope: Scope):
    get_profile_or_404(db, scope)
    row = filter_by_scope(
        db.query(DailySteps).filter(DailySteps.date == target_date),
        DailySteps,
        scope,
    ).first()
    if not row:
        row = DailySteps(
            tenant_id=scope.tenant_id,
            user_id=scope.user_id,
            profile_id=scope.profile_id,
            date=target_date,
            step_count=body.step_count,
        )
        db.add(row)
    else:
        row.step_count = body.step_count

    db.flush()
    awarded = credit_step_milestones(db, scope, row)

    goal = filter_by_scope(db.query(Goal), Goal, scope).first()
    awarded.extend(
        maybe_credit_goal_met(
            db,
            scope,
            target_date,
            row.step_count,
            today_active_minutes(db, scope, target_date),
            goal,
        )
    )

    db.commit()
    db.refresh(row)
    return StepsResponse.model_validate(row).model_copy(update={"points_awarded": awarded})


@router.get("/steps", response_model=list[StepsResponse])
def list_steps(
    db: DbSession,
    scope: Scope,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
):
    rows = (
        filter_by_scope(
            db.query(DailySteps).filter(
                DailySteps.date >= from_date,
                DailySteps.date <= to_date,
            ),
            DailySteps,
            scope,
        )
        .order_by(DailySteps.date.desc())
        .all()
    )
    return [StepsResponse.model_validate(r) for r in rows]


@router.put("/goals", response_model=GoalResponse)
def upsert_goals(body: GoalUpsert, db: DbSession, scope: Scope):
    get_profile_or_404(db, scope)
    row = filter_by_scope(db.query(Goal), Goal, scope).first()
    if not row:
        row = Goal(
            tenant_id=scope.tenant_id,
            user_id=scope.user_id,
            profile_id=scope.profile_id,
            daily_step_target=body.daily_step_target,
            daily_active_minutes_target=body.daily_active_minutes_target,
        )
        db.add(row)
    else:
        row.daily_step_target = body.daily_step_target
        row.daily_active_minutes_target = body.daily_active_minutes_target
    db.commit()
    db.refresh(row)
    return GoalResponse.model_validate(row)


@router.get("/goals", response_model=GoalResponse)
def get_goals(db: DbSession, scope: Scope):
    row = filter_by_scope(db.query(Goal), Goal, scope).first()
    if not row:
        raise HTTPException(status_code=404, detail="Goals not configured")
    return GoalResponse.model_validate(row)


@router.get("/reminders", response_model=ReminderResponse)
def get_reminders(db: DbSession, scope: Scope):
    row = filter_by_scope(db.query(ReminderSettings), ReminderSettings, scope).first()
    if not row:
        return ReminderResponse(
            enabled=False,
            walk_reminder_time=None,
            vitals_reminder_time=None,
            message=WELLNESS_DISCLAIMER,
        )
    return ReminderResponse.model_validate(row)


@router.put("/reminders", response_model=ReminderResponse)
def upsert_reminders(body: ReminderUpsert, db: DbSession, scope: Scope):
    row = filter_by_scope(db.query(ReminderSettings), ReminderSettings, scope).first()
    if not row:
        row = ReminderSettings(
            tenant_id=scope.tenant_id,
            user_id=scope.user_id,
            profile_id=scope.profile_id,
        )
        db.add(row)
    row.enabled = body.enabled
    row.walk_reminder_time = body.walk_reminder_time
    row.vitals_reminder_time = body.vitals_reminder_time
    row.message = body.message or WELLNESS_DISCLAIMER
    db.commit()
    db.refresh(row)
    return ReminderResponse.model_validate(row)


@router.put("/vitals/{target_date}", response_model=VitalsResponse)
def upsert_vitals(target_date: date, body: VitalsUpsert, db: DbSession, scope: Scope):
    get_profile_or_404(db, scope)
    needs_review = evaluate_vitals_needs_review(
        body.pulse, body.bp_systolic, body.bp_diastolic
    )
    row = filter_by_scope(
        db.query(Vitals).filter(Vitals.date == target_date),
        Vitals,
        scope,
    ).first()
    if not row:
        row = Vitals(
            tenant_id=scope.tenant_id,
            user_id=scope.user_id,
            profile_id=scope.profile_id,
            date=target_date,
        )
        db.add(row)
    row.bp_systolic = body.bp_systolic
    row.bp_diastolic = body.bp_diastolic
    row.pulse = body.pulse
    row.mood = body.mood
    row.sleep_hours = body.sleep_hours
    row.notes = body.notes
    row.needs_review = needs_review
    db.commit()
    db.refresh(row)
    return VitalsResponse.model_validate(row).model_copy(
        update={"review_message": vitals_review_message(needs_review)}
    )


@router.get("/vitals/{target_date}", response_model=VitalsResponse)
def get_vitals(target_date: date, db: DbSession, scope: Scope):
    row = filter_by_scope(
        db.query(Vitals).filter(Vitals.date == target_date),
        Vitals,
        scope,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="No vitals for date")
    return VitalsResponse.model_validate(row).model_copy(
        update={"review_message": vitals_review_message(row.needs_review)}
    )


@router.get("/points/balance", response_model=PointBalanceResponse)
def points_balance(db: DbSession, scope: Scope):
    return PointBalanceResponse(balance=get_balance(db, scope))


@router.get("/points/ledger", response_model=list[LedgerEntry])
def points_ledger(db: DbSession, scope: Scope, limit: int = Query(default=50, le=200)):
    rows = (
        filter_by_scope(db.query(PointLedger), PointLedger, scope)
        .order_by(PointLedger.created_at.desc())
        .limit(limit)
        .all()
    )
    return [LedgerEntry.model_validate(r) for r in rows]


@router.get("/history", response_model=list[HistoryEntry])
def unified_history(db: DbSession, scope: Scope, days: int = Query(default=14, le=90)):
    since = date.today() - timedelta(days=days)
    entries: list[HistoryEntry] = []

    for s in filter_by_scope(
        db.query(GentleSession).filter(GentleSession.started_at >= since),
        GentleSession,
        scope,
    ).all():
        entries.append(
            HistoryEntry(
                kind="session",
                timestamp=s.started_at,
                title=f"Gentle {s.session_type.value.replace('_', ' ')}",
                detail=f"{s.duration_minutes} min",
            )
        )

    for st in filter_by_scope(
        db.query(DailySteps).filter(DailySteps.date >= since),
        DailySteps,
        scope,
    ).all():
        entries.append(
            HistoryEntry(
                kind="steps",
                timestamp=datetime.combine(st.date, datetime.min.time()),
                title="Daily steps",
                detail=f"{st.step_count} steps",
            )
        )

    for v in filter_by_scope(
        db.query(Vitals).filter(Vitals.date >= since),
        Vitals,
        scope,
    ).all():
        detail = []
        if v.pulse:
            detail.append(f"Pulse {v.pulse}")
        if v.bp_systolic:
            detail.append(f"BP {v.bp_systolic}/{v.bp_diastolic}")
        entries.append(
            HistoryEntry(
                kind="vitals",
                timestamp=datetime.combine(v.date, datetime.min.time()),
                title="Wellness vitals",
                detail=", ".join(detail) or "Logged",
            )
        )

    for p in filter_by_scope(
        db.query(PointLedger).filter(PointLedger.created_at >= since),
        PointLedger,
        scope,
    ).all():
        entries.append(
            HistoryEntry(
                kind="ledger",
                timestamp=p.created_at,
                title=p.reason.value.replace("_", " ").title(),
                detail=p.description or "",
                points_delta=p.delta_points,
            )
        )

    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries
