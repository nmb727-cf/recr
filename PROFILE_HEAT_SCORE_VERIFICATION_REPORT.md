# PROFILE_HEAT_SCORE_VERIFICATION_REPORT

Scope verified against requested Phase 2 + Phase 3 requirements across models, APIs, services/jobs, scheduling, UI, and business logic.

## 1. Implemented

- Passport score storage fields exist:
  - `heat_score`, `completeness_score`, `market_demand_score` on `TalentPassport`.
  - Evidence: `backend/apps/passport/models.py:84-86`.
- Completeness calculation logic exists and is persisted.
  - Evidence:
    - Recompute on passport `PUT`: `backend/apps/passport/views.py:59-67`
    - Completeness formula: `backend/apps/passport/views.py:146-158`
- Score data is retrievable through passport APIs.
  - Candidate/private serializer includes heat/completeness/market demand: `backend/apps/passport/serializers.py:49`
  - Public serializer includes heat/completeness: `backend/apps/passport/serializers.py:79`
  - API routes for passport retrieval: `backend/apps/passport/urls.py:8,16`
- Passport UI shows completeness and a heat score label when non-zero.
  - Candidate passport view: `frontend/src/pages/candidate/Passport.tsx:123,170-188,260-264`
  - Public passport view: `frontend/src/pages/public/PublicPassportPage.tsx:989-1000,1003-1013`

## 2. Partial

- Improvement suggestions exist, but they are completeness-oriented, not full heat-factor-oriented.
  - Evidence: `ProfileStrengthSuggestions` suggests headline/summary/skills/resume/experience/education in `frontend/src/pages/candidate/CandidateCommandCenter.tsx:499-531`.
- Verification signals are modeled and displayed (identity/background/employment/education), but not wired into heat score calculation.
  - Model fields: `backend/apps/passport/models.py:75-79`
  - UI display: `frontend/src/pages/candidate/Passport.tsx:117-120`
- Interview/assessment score storage fields exist, but no consumption in heat computation.
  - Evidence: `backend/apps/passport/models.py:82-83`.

## 3. Missing

### Phase 2 required factors not implemented in heat score logic

- Daily calculation for every passport: missing.
- Verified credentials factor in heat score: missing.
- Interview performance factor in heat score: missing.
- Response/engagement rate factor in heat score: missing.
- Market demand for skills factor in heat score: missing.
- Multi-factor weighted heat score engine: missing.

### Heat score core gaps

- No implemented heat score recalculation flow (only completeness recalculates on `PUT`).
  - `heat_score` is read-only in serializer and never computed in service logic.
  - Evidence:
    - Read-only: `backend/apps/passport/serializers.py:54-59`
    - No heat assignment found; only completeness assignment at `backend/apps/passport/views.py:60`
- No scheduled daily heat recomputation job.
  - Evidence: Celery beat has no passport/heat task in `backend/config/settings/base.py:262-323`.
- No stale-data handling for heat score freshness.
- No explicit heat score range validation/contract (field supports decimal, but no guard logic around 0-100 semantics).

### Phase 3 missing features

- Heat score trend history storage: missing (no history model/table/service).
- Trend graph in passport: missing.
- Time-period filtering for trend: missing.
- Heat-score-specific improvement guidance based on missing factors (verification/interview/market demand/engagement): missing.

## 4. Logic Issues

- `heat_score` behaves like a placeholder value in current code path.
  - Field exists and UI displays it, but no active computation path updates it.
  - Evidence:
    - Field exists: `backend/apps/passport/models.py:84`
    - UI displays if >0: `frontend/src/pages/candidate/Passport.tsx:260-264`
    - No heat calculation assignment in views/services.
- Public UI labels `heat_score` as "Market Demand", while separate `market_demand_score` field exists and is not used.
  - Evidence:
    - Market demand field exists: `backend/apps/passport/models.py:86`
    - Public UI uses `passport.heat_score` for "Market Demand": `frontend/src/pages/public/PublicPassportPage.tsx:1006-1008`.
- Manual-only recalculation behavior for implemented score component.
  - Completeness recalculates only during profile `PUT`, not via daily background refresh.
  - Evidence: `backend/apps/passport/views.py:35-67`.
- Candidate-global matching can violate tenant-safe expectations.
  - Passport candidate linking and onboarding prefill match `Candidate` globally by `user_id/email/phone` without tenant filters.
  - Evidence:
    - `backend/apps/passport/candidate_sync_views.py:45-67`
    - `backend/apps/passport/views.py:177-181`
    - `backend/apps/candidates/identity_service.py:39-60`
- No explicit fallback behavior when market intelligence is unavailable.
  - Current behavior is effectively static `0` because no market-demand computation path exists.

## 5. Architecture Issues

- No dedicated heat-score calculation service/module; score logic is embedded in request-time passport update flow.
- No batch processing architecture for “every passport daily” requirement.
- No factor-source integration layer for:
  - credential verification system,
  - interview performance ingestion,
  - engagement/response analytics,
  - market intelligence service.
- No score lineage/explainability artifact persisted (e.g., factor breakdown JSON, weight version, calc timestamp).
- No test coverage for passport scoring engine in `backend/apps/passport` (no tests present).
- Recalculation performance path for a true daily all-passport run is not designed (no batch scorer, no incremental strategy, no queue partitioning).

## 6. UI / discoverability issues

- Candidate dashboard surfaces only completeness, not heat score.
  - Evidence: dashboard fetch contract and display use `completeness_score` only in `frontend/src/pages/dashboard/Dashboard.tsx:318-324,348-351`.
- Recruiter/company candidate views do not expose passport heat score in primary candidate list flows.
  - Candidate DB mapping includes `completeness_score`, not passport heat score: `frontend/src/pages/candidates/CandidateDatabase.tsx:136-140`.
- No passport trend chart widget for heat score (candidate or public view).
- Improvement tips are not shown on Passport page itself; they are in Candidate Command Center and focused on profile completion.
- Explainability is minimal and not heat-specific; no factor-by-factor heat explanation is shown in passport surfaces.

## 7. Phase 2 blockers

1. No daily automated recalculation for every passport.
2. No implemented weighted heat-score engine using required factors.
3. Missing data-source integration for response rate and market demand.
4. Verification and interview factors are not applied in heat-score computation.
5. Heat score freshness lifecycle (stale handling / periodic refresh) is absent.

## 8. Phase 3 blockers

1. No heat score history/trend persistence.
2. No heat score trend graph in passport UI.
3. No time-range trend filtering.
4. No heat-score-specific actionable recommendations tied to missing factors and weighted drivers.
5. Explainability for heat score (factor contributions and "how to improve") is not implemented.
