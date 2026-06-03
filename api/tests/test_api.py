import os
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://gentle:gentle@localhost:5432/gentle_activity_test",
)


@pytest.fixture(scope="session")
def use_sqlite():
    return os.getenv("USE_SQLITE_TESTS", "1") == "1"


@pytest.fixture()
def db_engine(use_sqlite):
    if use_sqlite:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered(client):
    resp = client.post(
        "/api/v1/register",
        json={"display_name": "Test User", "email": "test@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    headers = {
        "X-User-Id": data["user_id"],
        "X-Profile-Id": data["profile_id"],
    }
    return data, headers


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_register_and_me(client, registered):
    data, headers = registered
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["display_name"] == "Test User"
    assert "disclaimer" in me.json()


def test_missing_scope_headers(client):
    resp = client.get("/api/v1/me")
    assert resp.status_code == 401


def test_gentle_session_and_points(client, registered):
    _, headers = registered
    resp = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={
            "session_type": "walking",
            "duration_minutes": 20,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_type"] == "walking"
    assert len(body["points_awarded"]) >= 1

    balance = client.get("/api/v1/points/balance", headers=headers)
    assert balance.json()["balance"] >= 10


def test_reject_invalid_session_type(client, registered):
    _, headers = registered
    resp = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={
            "session_type": "hiit",
            "duration_minutes": 20,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 422


def test_steps_milestone_points(client, registered):
    _, headers = registered
    today = date.today().isoformat()
    resp = client.put(
        f"/api/v1/steps/{today}",
        headers=headers,
        json={"step_count": 250},
    )
    assert resp.status_code == 200
    awarded = resp.json()["points_awarded"]
    assert len(awarded) == 2
    assert sum(a["delta_points"] for a in awarded) == 10


def test_vitals_needs_review(client, registered):
    _, headers = registered
    today = date.today().isoformat()
    resp = client.put(
        f"/api/v1/vitals/{today}",
        headers=headers,
        json={"pulse": 130, "bp_systolic": 120, "bp_diastolic": 80},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["needs_review"] is True
    assert body["review_message"] is not None


def test_goals_and_reminders(client, registered):
    _, headers = registered
    goals = client.put(
        "/api/v1/goals",
        headers=headers,
        json={"daily_step_target": 6000, "daily_active_minutes_target": 45},
    )
    assert goals.status_code == 200

    reminders = client.put(
        "/api/v1/reminders",
        headers=headers,
        json={"enabled": True, "walk_reminder_time": "09:00"},
    )
    assert reminders.status_code == 200
    assert reminders.json()["walk_reminder_time"] == "09:00"


def test_history(client, registered):
    _, headers = registered
    resp = client.get("/api/v1/history", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_goal_met_points(client, registered):
    _, headers = registered
    today = date.today().isoformat()
    client.put(
        "/api/v1/goals",
        headers=headers,
        json={"daily_step_target": 100, "daily_active_minutes_target": 5},
    )
    resp = client.put(
        f"/api/v1/steps/{today}",
        headers=headers,
        json={"step_count": 150},
    )
    awarded = resp.json()["points_awarded"]
    reasons = [a["reason"] for a in awarded]
    assert "goal_met" in reasons


def test_no_redemption_endpoints(client, registered):
    _, headers = registered
    for path in ["/api/v1/points/redeem", "/api/v1/rewards", "/api/v1/redeem"]:
        resp = client.post(path, headers=headers, json={})
        assert resp.status_code == 404


def test_reject_weight_program_session(client, registered):
    _, headers = registered
    resp = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={
            "session_type": "weight_program",
            "duration_minutes": 30,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 422


def test_wrong_user_scope_rejected(client, registered):
    data, headers = registered
    other_user = client.post(
        "/api/v1/register",
        json={"display_name": "Other User"},
    ).json()
    bad_headers = {
        "X-User-Id": other_user["user_id"],
        "X-Profile-Id": data["profile_id"],
    }
    resp = client.get("/api/v1/me", headers=bad_headers)
    assert resp.status_code == 404


def test_register_with_tenant_id(client):
    import uuid

    tenant = str(uuid.uuid4())
    resp = client.post(
        "/api/v1/register",
        json={"display_name": "Tenant User", "tenant_id": tenant},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == tenant
    headers = {
        "X-User-Id": body["user_id"],
        "X-Profile-Id": body["profile_id"],
        "X-Tenant-Id": tenant,
    }
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
