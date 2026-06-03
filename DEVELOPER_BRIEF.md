# Developer handoff — Gentle Activity Module

**For product owners:** Give your developer **only the section below** — copy from **`COPY FROM HERE`** through **`END COPY`** into Cursor, Copilot, or similar.

**For developers:** Create or work in a **new repository** named `gentle-activity-module` (or similar). **Do not modify an unknown parent/host app.** Phase 2 integration is handled by the product owner's team later.

---

## COPY FROM HERE

You are building the **standalone Gentle Activity & Wellness system** (Phase 1).

### Non-negotiable rules

| Rule | Detail |
|------|--------|
| **New repo only** | Create/use repo `gentle-activity-module`. Never modify a parent product, monorepo host, NextStage, or unknown app. |
| **Wellness only** | Allowed session types: `walking`, `light_stretching`, `gentle_mobility`, `breathing_walk`. **Reject** HIIT, weight programs, clinician-prescribed training (API enum + 422). |
| **No medical advice** | All UI/API copy: *“general wellness”*, *“not a substitute for professional care”*. Vitals out-of-range → `needs_review: true` only — **no diagnosis**, no treatment text. |
| **User-scoped data** | Every DB row and every API call scoped by **`user_id`** + **`profile_id`** (family-ready: one user, multiple profiles). |
| **Tenant-ready** | Optional **`tenant_id`** on **all business tables** (nullable UUID) + optional header **`X-Tenant-Id`** — no schema migration when a multi-tenant host plugs in. |
| **Points** | Award for **steps**, **sessions**, **active minutes**, **goals met**. Expose **`balance` + `ledger` only**. **Redemption** (partners, IAP, QR) is **out of scope**. |
| **Platform** | **Android/iOS:** `pedometer` while app is in **foreground**. **Web/desktop:** **manual session entry only** (no pedometer). |

### Explicit exclusions

- NextStage, Firebase, medical-report code, unknown parent apps
- HIIT / weights / clinical training types
- Points redemption, partners, IAP, QR rewards, leaderboard
- Embedding inside another app (demo is standalone)

---

### Mandatory open-source reference study

**Before feature work**, study: https://github.com/TarekAlabd/Flutter-Steps-Tracker (Apache-2.0)

Document parity in `docs/REFERENCE.md`. Include Apache-2.0 attribution in `LICENSE`.

| Flutter-Steps-Tracker | Gentle Activity module |
|----------------------|------------------------|
| Firestore | **Postgres + REST** |
| Anonymous Firebase user | `POST /api/v1/register` → `user_id` + `profile_id` |
| Foreground `Pedometer.stepCountStream` | Same on mobile → sync `PUT /api/v1/steps/{date}` |
| 5 health points per 100 steps | Server ledger `steps_milestone` (+5, idempotent) |
| Snackbar on milestone | Flutter `SnackBar` on +N points |
| Exchanges history UI | `GET /api/v1/history` + Flutter list |
| Clean Architecture (data/domain/presentation) | `flutter_app/lib/features/*/domain`, `data`, presentation screens |
| Customized goals (reference: future) | Implement in Phase 1 (`PUT /goals`) |
| Rewards / redeem / leaderboard | **Removed** — balance + ledger only |

---

### What you are building

Two parts, one repo:

1. **Activity API** — FastAPI + PostgreSQL + Docker Compose. REST `/api/v1/*` with OpenAPI.
2. **Demo Flutter app** — Standalone (not embedded). Proves register, walk log, goals, reminders, vitals, points, foreground pedometer on phone.

**Stack:** Python 3.12 + FastAPI, PostgreSQL 16, Alembic, pytest, Flutter 3.x, `dio`, `pedometer` (mobile). Justify FastAPI vs Node in `README.md`.

---

### Repository layout (exact)

```
gentle-activity-module/
  README.md                 # setup, env vars, run API + Flutter
  LICENSE                   # project license + Apache-2.0 notice (Steps-Tracker)
  DEVELOPER_BRIEF.md        # this file
  docker-compose.yml
  api/
    migrations/             # Alembic / SQL revisions
    src/                    # routes, services, models, middleware
    tests/
    openapi.yaml            # OpenAPI 3 — must match live routes
    requirements.txt
  flutter_app/
    lib/
      core/                 # ApiClient, scope headers, disclaimers, step_milestone
      features/             # auth, home, pedometer, sessions, goals, reminders, vitals, points, history, steps/
    pubspec.yaml            # include pedometer for mobile
    README.md               # flutter create . + permissions
  docs/
    REFERENCE.md            # mandatory Steps-Tracker study + parity table
    API.md                  # human-readable endpoints
    INTEGRATION_CONTRACT.md # Phase 2 host obligations
    REQUIREMENTS_CROSSCHECK.md
```

---

### Request scoping (every API call)

**Required headers** (middleware enforces; exempt: `/health`, `/docs`, `/api/v1/register`):

| Header | Purpose |
|--------|---------|
| `X-User-Id` | Account owner (UUID) |
| `X-Profile-Id` | Family member profile under that user |
| `X-Tenant-Id` | Optional multi-tenant scope |

Registration returns `user_id`, `profile_id`, optional `tenant_id` for the client to attach on all subsequent requests.

---

### Data model (business tables)

Base columns on every business table: `tenant_id` (nullable), `user_id`, `profile_id`, `created_at`, `updated_at`.

| Table | Purpose |
|-------|---------|
| `users` | Account |
| `profiles` | `display_name`, optional `relationship_label` |
| `daily_steps` | `date`, `step_count`, `last_credited_hundreds` |
| `goals` | `daily_step_target`, `daily_active_minutes_target` |
| `gentle_sessions` | wellness enum, `duration_minutes`, `started_at`, `notes` |
| `vitals` | BP, pulse, mood, sleep; **`needs_review`** computed server-side |
| `reminder_settings` | walk/vitals reminder times |
| `point_ledger` | immutable: `delta_points`, `reason` enum |

**Points engine:**

| Trigger | Default credit |
|---------|----------------|
| Steps | +5 per **new** 100 steps (idempotent) |
| Session completed | +10 |
| Active minutes | +5 per 15-minute bucket |
| Goal met | +25 once per day |

---

### REST surface (`/api/v1`)

| Method | Path |
|--------|------|
| POST | `/register` |
| GET | `/me` |
| POST | `/sessions` |
| GET | `/sessions` |
| PUT | `/steps/{date}` |
| GET | `/steps` |
| PUT | `/goals` |
| GET | `/goals` |
| GET/PUT | `/reminders` |
| PUT/GET | `/vitals/{date}` |
| GET | `/points/balance` |
| GET | `/points/ledger` |
| GET | `/history` |
| GET | `/health` |

No redemption endpoints. Keep `openapi.yaml` and `docs/API.md` in sync.

---

### Flutter demo (standalone)

```
flutter_app/lib/
├── core/              # dio + header injection + wellness disclaimers
├── features/
│   ├── auth/          # register → store scope IDs
│   ├── pedometer/     # mobile only, foreground lifecycle
│   ├── steps/         # domain + data repository (Clean Architecture)
│   ├── sessions/      # manual gentle walk (all platforms)
│   ├── goals/
│   ├── reminders/
│   ├── vitals/        # BP + pulse (+ mood/sleep optional)
│   ├── points/
│   └── history/       # exchanges-style ledger list
```

- Static disclaimer on home + vitals screens.
- Mobile: subscribe to pedometer in foreground; sync steps to API; Snackbar on +5 per 100 steps.
- Web/desktop: hide pedometer; show manual “Log gentle walk” only.
- First-time setup: `flutter create . --project-name gentle_activity_demo` + ACTIVITY_RECOGNITION (Android) / NSMotionUsageDescription (iOS).

---

### Phase 1 is complete when

**Without any external parent codebase**, the demo can:

1. **Register** a test user + profile
2. **Log a gentle walk** (wellness session type)
3. **Set a daily goal** (steps / active minutes)
4. **Save reminder** config
5. **Log BP + pulse**; API returns `needs_review` when out of band — not a diagnosis
6. **See points** (balance + ledger from steps/sessions/minutes/goal)
7. **On a phone:** count steps in **foreground** via pedometer and sync to API

Plus: `docker compose up`, `pytest tests/ -v` pass, `openapi.yaml` aligned with routes.

---

### Verify commands

```bash
# Database
docker compose up -d

# API
cd api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload --port 8000
pytest tests/ -v

# Flutter demo
cd ../flutter_app
flutter create . --project-name gentle_activity_demo
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

---

### Phase 2 (out of scope for you)

Host app integration is **not** your task. Document obligations in `docs/INTEGRATION_CONTRACT.md`: pass scope headers, replace demo registration with real auth, no redemption expectations.

### END COPY

---

## For product owners (do not give developers this section)

| Artifact | Purpose |
|----------|---------|
| [docs/INTEGRATION_CONTRACT.md](docs/INTEGRATION_CONTRACT.md) | Phase 2 host team obligations |
| [docs/API.md](docs/API.md) | Endpoint reference |
| [docs/REFERENCE.md](docs/REFERENCE.md) | Steps-Tracker study notes |
| [docs/REQUIREMENTS_CROSSCHECK.md](docs/REQUIREMENTS_CROSSCHECK.md) | Requirement traceability matrix |

**Do not** hand developers the parent `DEMO PROJECT` folder or any unknown monorepo — only this brief (COPY block) and/or a fresh `gentle-activity-module` repo.
