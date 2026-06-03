# Reference study — Flutter-Steps-Tracker (mandatory)

**Repository:** [TarekAlabd/Flutter-Steps-Tracker](https://github.com/TarekAlabd/Flutter-Steps-Tracker)  
**License:** Apache License 2.0  
**Study date:** 2026-06-03  
**Attribution:** Patterns studied and adapted; no verbatim code copy. See [LICENSE](../LICENSE).

This document satisfies the **mandatory open-source reference study** required before extending the Gentle Activity module.

---

## 1. Reference overview

Flutter-Steps-Tracker is a cross-platform (Android/iOS) step-tracking app using:

| Layer | Technology |
|-------|------------|
| UI | Flutter, `flutter_bloc` (Cubit), Syncfusion radial gauge |
| Steps | `pedometer` package — `Pedometer.stepCountStream` |
| Backend | Firebase Auth (anonymous) + Cloud Firestore |
| Architecture | Clean Architecture — `data` / `domain` / `presentation` per feature |
| DI | `get_it` + `injectable` |

**Reference README features studied:**

- Foreground step tracking while app is open
- **5 health points per 100 steps**
- Snackbar visual feedback when points are earned
- Exchange history listing point gains (and rewards)
- Rewards catalog + QR redeem (excluded in our module)
- Leaderboard (excluded in our module)
- **Customized goals** — listed as *future* in reference; we implement in Phase 1

---

## 2. Reference architecture (Clean Architecture)

```
lib/
├── core/
│   ├── data/           # Database abstraction, Firestore, models
│   ├── domain/         # Base UseCase
│   └── presentation/   # Shared widgets
├── di/                 # injectable / get_it
├── features/
│   ├── intro/          # Auth (anonymous Firebase)
│   └── bottom_navbar/
│       ├── data/       # models, mappers, repositories impl
│       ├── domain/     # repositories (abstract), use cases
│       └── presentation/  # pages, cubits, widgets
└── utilities/
```

**Gentle Activity mapping:**

```
flutter_app/lib/
├── core/                    # ApiClient, scope headers, constants, step utilities
└── features/
    ├── steps/               # data + domain (reference-aligned)
    │   ├── domain/
    │   └── data/
    ├── pedometer/           # foreground stream (reference: home_cubit)
    ├── auth/, sessions/, goals/, reminders/, vitals/, points/, history/
    └── home/                # presentation — dashboard + gauge
```

API side mirrors Clean Architecture as: `routes` → `services` → `models` (Firestore replaced by Postgres).

---

## 3. Key reference files studied

| File | What we learned |
|------|-----------------|
| `lib/features/bottom_navbar/presentation/manager/home/home_cubit.dart` | Subscribes to `Pedometer.stepCountStream`; on each step event calls `setStepsAndPointsUseCase`; detects 100-step boundary for Snackbar + exchange history |
| `lib/features/bottom_navbar/data/repositories/bottom_navbar_repository_impl.dart` | Points formula: `healthPoints = (steps ~/ 100) * 5`; daily doc ID via `DateFormat.yMMMMd()`; persists to Firestore |
| `lib/core/data/data_sources/database.dart` | Abstract `Database` with streams for user, daily steps, exchange history |
| `lib/features/bottom_navbar/presentation/pages/exchanges_page.dart` | History UI — list of exchange items with date, title, points |
| `lib/features/bottom_navbar/presentation/widgets/exchanges_item.dart` | ListTile layout for each ledger/history row |
| `pubspec.yaml` | Dependencies: `pedometer`, `flutter_bloc`, Firestore (we use `dio` + REST instead) |

---

## 4. Pedometer pattern (foreground)

**Reference (`home_cubit.dart`):**

```dart
_stepCountStream = Pedometer.stepCountStream;
_stepCountStream.listen(onStepCount).onError(onStepCountError);

void onStepCount(StepCount event) async {
  var oldSteps = int.tryParse(_steps) ?? 0;
  _steps = event.steps.toString();
  await _setStepsAndPointsUseCase(event.steps);
  await onFeedbackState(oldSteps, event.steps);
}
```

**Reference milestone detection (`onFeedbackState`):**

```dart
if ((oldSteps % 100) > (newSteps % 100)) {
  emit(HomeState.feedbackGain(steps: _steps));
  await _setExchangeHistoryUseCase(/* +5 points entry */);
}
```

Crossing 100, 200, 300… steps triggers feedback (equivalent to `(old ~/ 100) < (new ~/ 100)`).

**Gentle Activity adaptation (`pedometer_service.dart` + `home_screen.dart`):**

| Reference | Our module |
|-----------|------------|
| Uses device **total** step count | Uses **session baseline** subtracted from total → daily steps while app is foreground (addresses reference “Future: Daily steps” gap) |
| Points computed client-side in repository | Points computed **server-side** in `credit_step_milestones()` — idempotent via `last_credited_hundreds` |
| Snackbar on milestone | Snackbar when API returns `points_awarded`; client also detects milestone for immediate `+5 wellness points` message |
| Stops when app backgrounded | `WidgetsBindingObserver` stops stream on `paused`, restarts on `resumed` |

---

## 5. Points per 100 steps

**Reference formula** (`bottom_navbar_repository_impl.dart`):

```dart
int healthPoints = (steps ~/ 100) * 5;
```

**Our API** (`api/src/services.py`):

- `POINTS_PER_100_STEPS = 5` (configurable)
- Credits +5 for each **new** 100-step milestone only (not recredited on re-sync)
- Ledger reason: `steps_milestone`

**Why server-side:** Reference README notes cloud functions were planned but client-side workarounds were used. Our REST API implements the intended server-side behavior from day one.

---

## 6. History / exchanges UI

| Reference | Gentle Activity |
|-----------|-----------------|
| `ExchangesHistoryPage` + `ExchangesItem` | `history_screen.dart` — unified timeline including ledger rows with `+N` points |
| Separate exchanges vs rewards icons | Ledger-only (rewards removed per product rules) |
| `ExchangeHistoryModel`: title, date, points | `GET /history` + `GET /points/ledger` |

---

## 7. Goals

| Reference | Gentle Activity |
|-----------|-----------------|
| “Customized Goals” in **Future Steps** | Implemented: `PUT /goals`, `goals_screen.dart`, home progress gauge toward daily target |

---

## 8. Parity matrix

| Reference feature | Status in Gentle Activity | Notes |
|-------------------|---------------------------|-------|
| Foreground pedometer | ✅ | `pedometer` package, lifecycle-aware |
| 5 pts / 100 steps | ✅ | Server ledger + client milestone feedback |
| Snackbar on points | ✅ | Home + session screens |
| History of point gains | ✅ | History + points ledger screens |
| Clean Architecture | ✅ | `features/steps/domain` + `data`; API layered |
| Daily step count | ✅ | Baseline approach + `daily_steps.date` |
| Custom goals | ✅ | Ahead of reference |
| Firebase / Firestore | ➡️ Replaced | Postgres + REST |
| Anonymous auth | ➡️ Replaced | `POST /register` → scope headers |
| Rewards / QR redeem | ❌ Excluded | Product rule — balance + ledger only |
| Leaderboard | ❌ Excluded | Out of scope |
| Background pedometer | ❌ Not planned | Reference also lists as future |
| Multilingual / themes | ❌ Phase 2 | Not required Phase 1 |

---

## 9. Wellness-only extensions (not in reference)

Our module adds product rules **beyond** the reference app:

- Gentle session types only (no HIIT/weights)
- Vitals (BP/pulse) with `needs_review` — no diagnosis
- Family-ready `user_id` + `profile_id` scoping
- Optional `tenant_id` for host integration

---

## 10. Implementation checklist (post-study)

- [x] Document reference architecture and key files (this doc)
- [x] Pedometer foreground stream with lifecycle handling
- [x] 5 points / 100 steps (server + client milestone utility)
- [x] Snackbar feedback on point gains
- [x] History / ledger UI
- [x] Goals with home progress indicator
- [x] Clean Architecture layers for steps (`features/steps/`)
- [x] Apache-2.0 attribution in LICENSE

---

## Further reading

- [API.md](API.md) — REST contract replacing Firestore
- [INTEGRATION_CONTRACT.md](INTEGRATION_CONTRACT.md) — Phase 2 host obligations
- [REQUIREMENTS_CROSSCHECK.md](REQUIREMENTS_CROSSCHECK.md) — full requirements matrix
