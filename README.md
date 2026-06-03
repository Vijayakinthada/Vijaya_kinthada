# Gentle Activity & Wellness Module

Standalone Phase 1 deliverable: a **wellness-only** activity API (FastAPI + PostgreSQL) and a **Flutter demo app**. Integration into a host product happens in a later phase by the product owner's team.

## What this system is

| Component | Role |
|-----------|------|
| **Activity API** (`api/`) | REST + Postgres backend any health app can call in Phase 2 |
| **Demo Flutter app** (`flutter_app/`) | Standalone proof: walks, goals, reminders, vitals, points, mobile pedometer |

No Firebase, NextStage, or medical-report dependencies. Patterns from [Flutter-Steps-Tracker](https://github.com/TarekAlabd/Flutter-Steps-Tracker) with REST replacing Firestore.

## Why FastAPI (not Node)

- Strong typing with Pydantic matches our scoped request/response contracts (`user_id`, `profile_id`, optional `tenant_id`).
- OpenAPI is generated automatically and stays aligned with `docs/API.md`.
- Async I/O fits periodic step sync from mobile clients without blocking.
- Python ecosystem (SQLAlchemy, Alembic, pytest) keeps migrations and integration tests in one stack.

## Product rules (summary)

| Rule | Detail |
|------|--------|
| Wellness only | Session types: `walking`, `light_stretching`, `gentle_mobility`, `breathing_walk` |
| No medical advice | Vitals out-of-range → `needs_review: true` only |
| Scoped data | Every row and request uses `user_id` + `profile_id`; optional `tenant_id` |
| Points | Balance + ledger only — **no redemption** |
| Mobile | Foreground pedometer on Android/iOS; web/desktop manual session entry only |

Full rules: [docs/PRODUCT_RULES.md](docs/PRODUCT_RULES.md). Handoff: [DEVELOPER_BRIEF.md](DEVELOPER_BRIEF.md).

## Prerequisites

- Docker Desktop (PostgreSQL via Compose)
- Python 3.12+
- Flutter 3.x (for the demo app)

## Quick start

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### Windows one-liner (API)

```powershell
.\scripts\start-api.ps1
```

### 2. Run the API (manual)

```bash
cd api
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 3. Run the Flutter demo

```bash
cd flutter_app
flutter create . --project-name gentle_activity_demo   # first time only
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### 4. Run tests

```bash
cd api
pytest tests/ -v
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg2://gentle:gentle@localhost:5432/gentle_activity` | Postgres connection |
| `VITALS_PULSE_MIN` | `50` | Below → `needs_review` |
| `VITALS_PULSE_MAX` | `120` | Above → `needs_review` |
| `VITALS_BP_SYSTOLIC_MAX` | `140` | Above → `needs_review` |
| `VITALS_BP_DIASTOLIC_MAX` | `90` | Above → `needs_review` |
| `POINTS_PER_100_STEPS` | `5` | Reference rule (Flutter-Steps-Tracker) |
| `POINTS_PER_SESSION` | `10` | Gentle session completed |
| `POINTS_PER_ACTIVE_MINUTES_BUCKET` | `5` | Per 15 active minutes |
| `POINTS_GOAL_MET` | `25` | Once per day when goal achieved |

## Phase 1 checklist

Without any parent codebase, the demo can:

1. Register a test user + profile
2. Log a gentle walk session
3. Set daily step / active-minute goals
4. Save reminder settings
5. Log BP + pulse (with `needs_review` when out of band)
6. View points balance + ledger
7. On phone: count foreground steps and sync to API

## Repository layout (Phase 1 deliverable)

```
gentle-activity-module/
  README.md                 # setup, env vars, how to run API + Flutter
  LICENSE                   # MIT + Apache-2.0 notice for Steps-Tracker adaptations
  api/                      # Backend — Python FastAPI (see "Why FastAPI" above)
    migrations/             # SQL / Alembic table creation
    src/                    # routes, services, models, middleware
    tests/
    openapi.yaml            # OpenAPI 3 spec
    requirements.txt
  flutter_app/              # Standalone Flutter demo (not embedded in another app)
    lib/
    pubspec.yaml            # includes pedometer on mobile
  docs/
    API.md                  # Human-readable endpoint doc
    INTEGRATION_CONTRACT.md # Phase 2 host app obligations
```

Also included: `docker-compose.yml`, `DEVELOPER_BRIEF.md`, `docs/REFERENCE.md`, `docs/PHASE1.md`, `docs/PRODUCT_RULES.md`.

Full Phase 1 checklist: [docs/PHASE1.md](docs/PHASE1.md).

## Phase 2 integration

See [docs/INTEGRATION_CONTRACT.md](docs/INTEGRATION_CONTRACT.md).

## Reference

Patterns adapted from [Flutter-Steps-Tracker](https://github.com/TarekAlabd/Flutter-Steps-Tracker) (Apache-2.0). See [docs/REFERENCE.md](docs/REFERENCE.md).
