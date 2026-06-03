# Product rules (non-negotiable)

Authoritative mapping of product rules to implementation in `gentle-activity-module`.

**Legend:** ✅ Enforced in code · 📝 Documented only

---

## 1. Wellness only

**Rule:** Allowed: walking, light stretching, gentle mobility, breathing walks. **No** HIIT, weight programs, or clinician-prescribed training.

| Enforcement | Location |
|-------------|----------|
| ✅ API enum | `api/src/models.py` → `GentleSessionType` (4 values only) |
| ✅ Request validation | `api/src/schemas.py` → `GentleSessionTypeLiteral` |
| ✅ 422 on invalid type | `api/src/routes.py` → `create_session` |
| ✅ Tests | `test_reject_invalid_session_type` (hiit), `test_reject_weight_program_session` |
| ✅ Flutter dropdown | `flutter_app/lib/core/constants.dart` → `gentleSessionTypes` |

---

## 2. No medical advice

**Rule:** All copy: “general wellness”, “not a substitute for professional care”. APIs flag out-of-range vitals as `needs_review` only — **no diagnosis**.

| Enforcement | Location |
|-------------|----------|
| ✅ API disclaimer constant | `api/src/schemas.py` → `WELLNESS_DISCLAIMER` |
| ✅ Vitals review message | `VITALS_REVIEW_MESSAGE` — flagged for review, not medical advice |
| ✅ Server-side bands | `api/src/services.py` → `evaluate_vitals_needs_review` |
| ✅ Configurable thresholds | `api/src/config.py` → `vitals_pulse_min/max`, BP max |
| ✅ Flutter disclaimer | `flutter_app/lib/core/constants.dart` → `wellnessDisclaimer` |
| ✅ UI screens | register, home, sessions, goals, reminders, vitals, points, history |
| ✅ Test | `test_vitals_needs_review` |

---

## 3. User-scoped data

**Rule:** Every record belongs to **`user_id`** and **`profile_id`**. API must accept these on every call.

| Enforcement | Location |
|-------------|----------|
| ✅ DB columns | `ScopeMixin` on all business tables |
| ✅ Middleware | `api/src/middleware/scoping.py` → `X-User-Id`, `X-Profile-Id` required |
| ✅ Query helper | `api/src/services.py` → `filter_by_scope` (user + profile on all reads) |
| ✅ Profile validation | `get_profile_or_404` verifies user owns profile |
| ✅ Flutter headers | `scope_storage.dart`, `api_client.dart` Dio interceptors |
| ✅ Test | `test_missing_scope_headers`, `test_wrong_user_scope_rejected` |

---

## 4. Tenant-ready

**Rule:** Optional **`tenant_id`** on all rows and headers for future multi-tenant host without schema changes.

| Enforcement | Location |
|-------------|----------|
| ✅ Nullable column | All business tables + `users` / `profiles` |
| ✅ Optional header | `X-Tenant-Id` in scoping middleware |
| ✅ Stored on writes | All create/upsert routes pass `scope.tenant_id` |
| ✅ Read filter when set | `filter_by_scope` applies tenant when header present |
| ✅ Registration | `RegisterRequest.tenant_id` optional |
| ✅ Test | `test_register_with_tenant_id` |

---

## 5. Points

**Rule:** Award for steps, sessions, active minutes, goals. **Redemption out of scope** — balance + ledger only.

| Enforcement | Location |
|-------------|----------|
| ✅ Steps milestone | `credit_step_milestones` — +5 per 100 steps |
| ✅ Session | `POINTS_PER_SESSION` on gentle session complete |
| ✅ Active minutes | `credit_active_minutes` — bucket credits |
| ✅ Goal met | `maybe_credit_goal_met` — once per day |
| ✅ Balance endpoint | `GET /points/balance` |
| ✅ Ledger endpoint | `GET /points/ledger` |
| ✅ No redeem routes | Confirmed — `test_no_redemption_endpoints` |
| ✅ Flutter UI | points screen notes “no redemption in Phase 1” |

---

## 6. Platform

**Rule:** **Android/iOS:** pedometer in **foreground**. **Web/desktop:** manual session entry only.

| Enforcement | Location |
|-------------|----------|
| ✅ Platform gate | `pedometer_service.dart` → `!kIsWeb && (Android \|\| iOS)` |
| ✅ Lifecycle | `home_screen.dart` → stop on `paused`, start on `resumed` |
| ✅ Manual sessions | `log_session_screen.dart` — all platforms |
| ✅ Home UI | Pedometer status hidden on web/desktop (`isSupported`) |

---

## Verification

```bash
cd api && pytest tests/ -v
```

See also: [REQUIREMENTS_CROSSCHECK.md](REQUIREMENTS_CROSSCHECK.md), [DEVELOPER_BRIEF.md](../DEVELOPER_BRIEF.md).
