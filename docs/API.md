# API reference

Base URL: `http://localhost:8000`  
Prefix: `/api/v1`  
OpenAPI: `/docs` or [openapi.yaml](../api/openapi.yaml)

**Disclaimer (all wellness responses):** For general wellness only — not a substitute for professional medical care.

## Authentication (Phase 1)

Demo registration returns IDs used as headers. Phase 2 replaces this with host auth — see [INTEGRATION_CONTRACT.md](INTEGRATION_CONTRACT.md).

## Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-User-Id` | Yes* | UUID from registration |
| `X-Profile-Id` | Yes* | Profile under user |
| `X-Tenant-Id` | No | Optional multi-tenant scope |

\*Not required for `POST /register`, `/health`, `/docs`.

## Endpoints

### `POST /api/v1/register`

Create demo user + default profile + default goals.

**Body:**
```json
{
  "display_name": "Alex",
  "email": "alex@example.com",
  "relationship_label": "self",
  "tenant_id": null
}
```

**Response:** `user_id`, `profile_id`, `tenant_id`, `display_name`, `disclaimer`

---

### `GET /api/v1/me`

Profile summary, balance, today's steps/active minutes, goals.

---

### `POST /api/v1/sessions`

Log a **wellness-only** session.

**Allowed `session_type`:** `walking`, `light_stretching`, `gentle_mobility`, `breathing_walk`

**Body:**
```json
{
  "session_type": "walking",
  "duration_minutes": 20,
  "started_at": "2026-06-03T10:00:00Z",
  "notes": "Morning park walk"
}
```

**Response:** session + `points_awarded[]`

---

### `GET /api/v1/sessions?from=YYYY-MM-DD&to=YYYY-MM-DD`

List sessions for profile.

---

### `PUT /api/v1/steps/{date}`

Upsert daily step count. Awards +5 points per **new** 100-step milestone.

**Body:** `{ "step_count": 3500 }`

---

### `GET /api/v1/steps?from=YYYY-MM-DD&to=YYYY-MM-DD`

List daily step records.

---

### `PUT /api/v1/goals` / `GET /api/v1/goals`

Set or read daily step + active-minute targets.

---

### `PUT /api/v1/reminders` / `GET /api/v1/reminders`

Reminder config (`walk_reminder_time`, `vitals_reminder_time` as `HH:MM`).

---

### `PUT /api/v1/vitals/{date}` / `GET /api/v1/vitals/{date}`

Log BP, pulse, optional mood/sleep.

**Response includes:** `needs_review`, `review_message` when out of configured bands.

---

### `GET /api/v1/points/balance`

Current wellness points balance (no redemption).

---

### `GET /api/v1/points/ledger?limit=50`

Immutable ledger entries.

---

### `GET /api/v1/history?days=14`

Unified timeline: sessions, steps, vitals, ledger.

---

### `GET /health`

`{ "status": "ok", "module": "gentle-activity" }`

## Points rules

| Trigger | Default credit |
|---------|----------------|
| Steps milestone | +5 per 100 steps (idempotent) |
| Session completed | +10 |
| Active minutes | +5 per 15 minutes |
| Goal met | +25 once per day |

Configure via API environment variables (see [README](../README.md)).

## Errors

| Code | Meaning |
|------|---------|
| 401 | Missing/invalid scope headers |
| 404 | Resource not found for profile |
| 422 | Validation (e.g. disallowed session type) |
