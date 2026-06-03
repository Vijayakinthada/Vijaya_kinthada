# Phase 1 deliverable checklist

Standalone build — **no parent/host app required**.

## Required repository layout

```
gentle-activity-module/
  README.md                 ✅ setup, env vars, run API + Flutter; FastAPI justified
  LICENSE                   ✅ MIT + Apache-2.0 notice (Steps-Tracker)
  api/
    migrations/             ✅ Alembic — 001_initial_schema.py
    src/                    ✅ routes, services, models, middleware
    tests/                  ✅ pytest (SQLite in-memory default)
    openapi.yaml            ✅ OpenAPI 3.1 — all /api/v1 routes
  flutter_app/
    lib/                    ✅ standalone demo (not embedded)
    pubspec.yaml            ✅ includes pedometer
  docs/
    API.md                  ✅ human-readable endpoints
    INTEGRATION_CONTRACT.md ✅ Phase 2 host obligations
```

## Additional files (supporting Phase 1)

| File | Purpose |
|------|---------|
| `docker-compose.yml` | PostgreSQL 16 for local API |
| `DEVELOPER_BRIEF.md` | Single-file developer handoff |
| `docs/REFERENCE.md` | Flutter-Steps-Tracker mandatory study |
| `docs/PRODUCT_RULES.md` | Non-negotiable rules → code mapping |
| `docs/REQUIREMENTS_CROSSCHECK.md` | Full traceability matrix |
| `api/requirements.txt` | Python dependencies |
| `scripts/start-api.ps1` | Windows API startup helper |

## Phase 1 complete when

Without any external parent codebase:

| # | Flow | API | Flutter |
|---|------|-----|---------|
| 1 | Register user + profile | `POST /api/v1/register` | ✅ |
| 2 | Log gentle walk | `POST /api/v1/sessions` | ✅ |
| 3 | Set daily goals | `PUT /api/v1/goals` | ✅ |
| 4 | Save reminders | `PUT /api/v1/reminders` | ✅ |
| 5 | Log BP + pulse | `PUT /api/v1/vitals/{date}` | ✅ |
| 6 | View points | `GET /points/balance`, `/points/ledger` | ✅ |
| 7 | Foreground pedometer → API | `PUT /api/v1/steps/{date}` | ✅ mobile |

## Verify

```bash
docker compose up -d
cd api && pip install -r requirements.txt && alembic upgrade head
pytest tests/ -v
uvicorn src.main:app --reload --port 8000

cd ../flutter_app
flutter create . --project-name gentle_activity_demo
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Phase 2

Host integration: [INTEGRATION_CONTRACT.md](INTEGRATION_CONTRACT.md) — not part of this deliverable.
