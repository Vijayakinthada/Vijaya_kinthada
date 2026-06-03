# Requirements cross-check (Phase 1)

Baseline sources: product rules from planning, `DEVELOPER_BRIEF.md`, and Phase 1 completion criteria.

**Legend:** ✅ Met · ⚠️ Partial · ❌ Missing · ⏳ Not verified locally

## Open-source reference (mandatory study)

[Flutter-Steps-Tracker](https://github.com/TarekAlabd/Flutter-Steps-Tracker) (Apache-2.0) — full notes in [REFERENCE.md](REFERENCE.md).

| Reference pattern | Gentle Activity | Status |
|-------------------|-----------------|--------|
| Foreground pedometer | `pedometer_service.dart` | ✅ |
| 5 pts / 100 steps | API + `core/steps/step_milestone.dart` | ✅ |
| Snackbar on milestone | `home_screen.dart` | ✅ |
| Exchange history UI | `history_screen.dart` | ✅ |
| Clean Architecture | `features/steps/domain` + `data` | ✅ |
| Custom goals (ref: future) | goals + home progress gauge | ✅ |
| Rewards / leaderboard | — | ❌ Excluded by product rules |
| Firebase | Postgres + REST | ➡️ Replaced |

---

## Product rules (non-negotiable)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | **Wellness only** — walking, light stretching, gentle mobility, breathing walk; reject HIIT/weights/clinical | ✅ | `GentleSessionType` enum in `api/src/models.py`; Pydantic literal in `schemas.py`; test rejects `hiit` → 422 |
| 2 | **No medical advice** — “general wellness”, “not a substitute for professional care”; vitals → `needs_review` only | ✅ | `WELLNESS_DISCLAIMER` in API + Flutter `constants.dart`; vitals service + Flutter banner |
| 3 | **User-scoped data** — `user_id` + `profile_id` on every record and API call | ✅ | `ScopeMixin` on business tables; scoping middleware; Flutter `ScopeStorage` + Dio interceptors |
| 4 | **Tenant-ready** — optional `tenant_id` on rows and `X-Tenant-Id` header | ✅ | Columns + header; `filter_by_scope` on all API reads when tenant header set |
| 5 | **Points** — steps, sessions, active minutes, goals; balance + ledger only; no redemption | ✅ | `services.py` points engine; `/points/balance`, `/points/ledger`; no redeem routes |
| 6 | **Platform** — mobile foreground pedometer; web/desktop manual sessions only | ✅ | `pedometer_service.dart` gated by platform; manual log on all platforms |

---

## Repository layout

| Path | Required | Status |
|------|----------|--------|
| `README.md` | Yes | ✅ |
| `LICENSE` (+ Apache notice) | Yes | ✅ |
| `DEVELOPER_BRIEF.md` | Yes | ✅ |
| `docker-compose.yml` | Yes | ✅ |
| `api/migrations/` | Yes | ✅ |
| `api/src/` | Yes | ✅ |
| `api/tests/` | Yes | ✅ |
| `api/openapi.yaml` | Yes | ✅ |
| `flutter_app/lib/` | Yes | ✅ |
| `flutter_app/pubspec.yaml` | Yes | ✅ |
| `docs/API.md` | Yes | ✅ |
| `docs/INTEGRATION_CONTRACT.md` | Yes | ✅ |
| `docs/REFERENCE.md` | Yes | ✅ |

---

## REST API (`/api/v1`)

| Endpoint | Required | Status |
|----------|----------|--------|
| `POST /register` | Yes | ✅ |
| `GET /me` | Yes | ✅ |
| `POST /sessions` | Yes | ✅ |
| `GET /sessions` | Yes | ✅ |
| `PUT /steps/{date}` | Yes | ✅ |
| `GET /steps` | Yes | ✅ |
| `PUT /goals` | Yes | ✅ |
| `GET /goals` | Yes | ✅ |
| `GET/PUT /reminders` | Yes | ✅ |
| `PUT/GET /vitals/{date}` | Yes | ✅ |
| `GET /points/balance` | Yes | ✅ |
| `GET /points/ledger` | Yes | ✅ |
| `GET /history` | Yes | ✅ |
| `GET /health` | Yes | ✅ |
| Redemption endpoints | Must NOT exist | ✅ |

---

## Points engine

| Trigger | Required | Status |
|---------|----------|--------|
| +5 per new 100 steps (idempotent) | Yes | ✅ `credit_step_milestones` |
| Session completed | Yes | ✅ `POINTS_PER_SESSION` |
| Active minutes buckets | Yes | ✅ `credit_active_minutes` |
| Goal met (once/day) | Yes | ✅ `maybe_credit_goal_met` |
| `points_awarded[]` on writes | Yes | ✅ steps + sessions responses |

---

## Phase 1 demo flows

| # | Flow | API | Flutter UI |
|---|------|-----|------------|
| 1 | Register user + profile | ✅ | ✅ `register_screen.dart` |
| 2 | Log gentle walk | ✅ | ✅ `log_session_screen.dart` |
| 3 | Set daily goals | ✅ | ✅ `goals_screen.dart` |
| 4 | Save reminders | ✅ | ✅ `reminders_screen.dart` |
| 5 | Log BP + pulse (`needs_review`) | ✅ | ✅ `vitals_screen.dart` |
| 6 | Points balance + ledger | ✅ | ✅ `points_screen.dart` + SnackBar |
| 7 | Foreground pedometer → API | ✅ | ✅ `pedometer_service.dart` + home sync |

---

## Explicit exclusions

| Exclusion | Status |
|-----------|--------|
| NextStage / unknown parent app | ✅ Standalone repo only |
| Firebase | ✅ Postgres + REST |
| HIIT / weights / clinical training | ✅ Rejected at API |
| Points redemption / leaderboard | ✅ Not implemented |
| Old `activity-wellness` web prototype | ✅ Not used as deliverable |

---

## Gaps & follow-ups

| Item | Priority | Action |
|------|----------|--------|
| Flutter `android/` / `ios/` platform folders | Medium | Run `flutter create .` locally (see `flutter_app/README.md`) |
| End-to-end run on dev machine | Medium | Requires Python 3.12, Docker, Flutter SDK |
| Tenant filter on all read queries | — | ✅ via `filter_by_scope` |
| Mood / sleep in Flutter vitals UI | Low | API supports; UI can be extended |
| `openapi.yaml` vs live routes | Low | Hand-written spec; `/docs` is authoritative at runtime |

---

## Verification commands

```bash
docker compose up -d
cd api && pip install -r requirements.txt && alembic upgrade head
pytest tests/ -v
uvicorn src.main:app --reload --port 8000
cd ../flutter_app && flutter create . --project-name gentle_activity_demo && flutter pub get && flutter run
```

---

*Last cross-check: 2026-06-03. Paste additional requirements below or in a follow-up message to extend this matrix.*
