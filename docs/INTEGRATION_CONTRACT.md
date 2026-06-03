# Integration contract (Phase 2)

This document describes how the **product owner's team** integrates the standalone Gentle Activity module into a host application. Phase 1 ships without any host dependencies.

## What Phase 1 delivers

- REST API (`api/`) with Postgres schema
- Standalone Flutter demo (`flutter_app/`)
- OpenAPI spec and human-readable [API.md](API.md)

## Host app obligations

### 1. Request scoping

Every API call (except `/health`, `/docs`, `/register`) must include:

```
X-User-Id: <uuid>
X-Profile-Id: <uuid>
X-Tenant-Id: <uuid>   # optional
```

The host replaces demo `POST /register` with real authentication but **must preserve** the same header contract so no schema migration is required.

### 2. Profile model

- One `user_id` may have multiple `profile_id` values (family accounts).
- Host UI selects active profile and injects headers via HTTP client interceptors (see Flutter `ApiClient` for reference).

### 3. Tenant readiness

When multi-tenancy is enabled, pass `X-Tenant-Id` on all requests. Nullable `tenant_id` on all tables supports gradual rollout.

### 4. Wellness-only writes

If the host proxies session creation, it must not send disallowed session types. API returns 422 for non-wellness types.

### 5. Vitals display

When `needs_review: true`, show `review_message` — never auto-generate diagnosis or treatment text.

### 6. Points

Phase 1 exposes **balance + ledger only**. Do not build redemption UI against this API — endpoints do not exist.

### 7. Mobile vs web

| Platform | Behavior |
|----------|----------|
| Android / iOS | Foreground pedometer → periodic `PUT /steps/{date}` |
| Web / desktop | Manual gentle session logging only |

## Suggested integration paths

### Option A — Flutter module

Extract `flutter_app/lib/features/*` and `core/*` into a package. Host app provides auth and mounts routes.

### Option B — REST only

Any client (React Native, native iOS/Android) calls the API with scope headers.

### Option C — Embedded WebView

Not recommended for pedometer access; use native mobile for step sync.

## Auth migration (Phase 2)

1. Host auth service maps authenticated user → `user_id`
2. Host profile picker → `profile_id`
3. Optional org/tenant middleware → `tenant_id`
4. Disable or protect demo `/register` in production

## Environment

Host deploys API with managed Postgres. See [README](../README.md) for env vars.

## Out of scope for host (Phase 1 API)

- Points redemption, partners, IAP
- Leaderboards
- HIIT / clinical exercise programs
- Medical diagnosis from vitals

## Support artifacts

| File | Purpose |
|------|---------|
| [API.md](API.md) | Endpoint reference |
| [../api/openapi.yaml](../api/openapi.yaml) | Machine-readable contract |
| [REFERENCE.md](REFERENCE.md) | Steps-Tracker parity notes |
