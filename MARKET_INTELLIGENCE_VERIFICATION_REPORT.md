# MARKET_INTELLIGENCE_VERIFICATION_REPORT

## 1. Implemented

- **Core analytics foundation exists (tenant-scoped dashboards/APIs):**
  - Analytics endpoints and dashboards are implemented (`/api/v1/analytics/*`).
  - Evidence: `backend/apps/analytics/urls.py`, `backend/apps/analytics/views.py`, `frontend/src/api/analytics.ts`, `frontend/src/pages/analytics/HiringIntelligenceDashboard.tsx`.

- **Base data entities needed for future market intelligence are present:**
  - Job demand-related entities: `JobRequisition` (role, location, salary range, skills).
  - Hiring outcome entities: `Application` (`status`, `joined_at`, stage transitions).
  - Salary offer entities exist: `OfferLetter.offered_salary`.
  - Evidence: `backend/apps/jobs/models.py`, `backend/apps/pipeline/models.py`, `backend/apps/documents/models.py`.

- **Tenant isolation is generally applied in analytics query entry points:**
  - Most analytics endpoints and services scope by `request.user.tenant_id` / `tenant_id`.
  - Evidence: `backend/apps/analytics/views.py`, `backend/apps/jobs/services.py`, `backend/apps/agencies/services.py`.

## 2. Partial

- **Average time-to-hire signal exists, but not Phase 3 benchmark grade:**
  - Computed in interview analytics (`time_to_hire_hours`) and surfaced in hiring dashboard.
  - Not provided as **benchmark by role + region**.
  - Evidence: `backend/apps/analytics/views.py` (InterviewIntelligenceAnalyticsView), `frontend/src/pages/analytics/HiringIntelligenceDashboard.tsx`.

- **Candidate supply / job demand proxies exist, but not market-intelligence analytics:**
  - Candidate pipeline and active job counts are available.
  - Missing advanced aggregation by region/role/skill trend.
  - Evidence: `backend/apps/jobs/services.py` (`get_global_intelligence`), `backend/apps/analytics/views.py`.

- **Recruiter/agency intelligence exists, but not market intelligence:**
  - Performance dashboards are operational.
  - They do not deliver in-demand skills, role fill difficulty, or salary trend analytics.
  - Evidence: `backend/apps/agencies/services.py`, `backend/apps/agencies/views.py`, `frontend/src/pages/analytics/RecruiterIntelligenceDashboard.tsx`, `frontend/src/pages/analytics/AgencyIntelligenceDashboard.tsx`.

## 3. Missing

- **Most in-demand skills by region:** Missing.
  - No model/service/API computes skill demand grouped by region with trend deltas.

- **Hardest roles to fill analytics:** Missing.
  - No dedicated role difficulty index (longest time-to-hire + lowest conversion + supply gap) by role.

- **Salary trend data by role and location:** Missing.
  - Salary fields exist in models, but no trend pipeline/API/UI for role-location trend curves.

- **Average time-to-fill benchmarks (overall + role + region):** Missing.
  - No benchmark dataset/materialized table/service endpoint for per-role/per-region benchmarks.

- **Market data source layer (required): Missing.**
  - No explicit market intelligence pipeline that consolidates:
    - platform job demand,
    - candidate supply,
    - salary offers,
    - hiring outcomes,
    into reusable market aggregates.

- **Job creation suggestion panel using market intelligence:** Missing.
  - Job creation/setup screens have no market-intelligence suggestions.
  - Evidence: `frontend/src/pages/jobs/JobCreate.tsx`, `frontend/src/pages/jobs/JobSetupStudio.tsx`.

- **Recruiter intelligence panel with market intelligence modules:** Missing.
  - Current recruiter dashboard is workload/performance only.
  - Evidence: `frontend/src/pages/analytics/RecruiterIntelligenceDashboard.tsx`.

- **Dedicated market-intelligence module/app:** Missing.
  - `apps/marketplace` contains only `__init__.py`; no models/services/APIs.
  - Evidence: `backend/apps/marketplace/__init__.py`.

## 4. Logic Issues

- **Heuristic/static values are used where real analytics are expected (Phase 3 blocker):**
  - Hardcoded values in global intelligence:
    - `avg_time_to_hire_days: 24`
    - static stage conversion rates
  - Evidence: `backend/apps/jobs/services.py` (`GlobalHiringCommandCenterService.get_global_intelligence`).

- **Additional heuristic placeholders in higher-level analytics:**
  - `system_health_score: 88` is fixed.
  - Evidence: `backend/apps/analytics/operations.py`.

- **No fallback strategy for market intelligence data unavailability:**
  - No explicit fallback path when market aggregates are missing because market aggregate pipeline itself is absent.

- **Data freshness for market metrics is undefined:**
  - No scheduled task for market-demand/salary/time-to-fill benchmark recomputation.
  - Evidence: `backend/config/settings/base.py` (no market-intelligence beat tasks), `backend/apps/orchestration_center/tasks/analytics_tasks.py` (workflow analytics only).

- **Role/job-level intelligence is not equivalent to market intelligence:**
  - Existing job intelligence computes job health/risk, not market-wide analytics by region/role.
  - Evidence: `backend/apps/jobs/intelligence_engine.py`.

## 5. Architecture Issues

- **No dedicated market intelligence domain model:**
  - Missing normalized storage for demand trends, salary trend snapshots, benchmark tables, and confidence metadata.

- **No data pipeline contract for market aggregation:**
  - No ETL/aggregation service generating periodic market snapshots.

- **No explicit privacy-preserving aggregation layer for market benchmarks:**
  - No minimum-cohort threshold, anonymization policy, or suppression rules found for benchmark outputs.

- **Performance risk from repeated on-demand deep calculations:**
  - Global analytics iterates active jobs and repeatedly invokes per-job intelligence, leading to N+1 style scaling pressure.
  - Evidence: `backend/apps/jobs/services.py`.

- **UI discoverability gap for market intelligence surfaces:**
  - Analytics dashboard exists, but no dedicated market intelligence dashboard modules for required Phase 3 outputs.

## 6. Phase 3 blockers

1. **No implemented Market Intelligence Engine** that computes:
   - in-demand skills by region,
   - hardest roles to fill,
   - salary trends by role/location,
   - time-to-fill benchmarks by role/region.

2. **No validated market data pipeline** combining required data sources into aggregate outputs.

3. **Presence of placeholder/fixed analytics values** violates requirement to avoid fake/static analytics.

4. **No market-intelligence API contract** for dashboard + job creation suggestions + recruiter panel consumption.

5. **No market-intelligence UI components** for required placements (analytics dashboard detail modules, job creation suggestion panel, recruiter intelligence panel).

6. **No freshness/retraining schedule** for market metrics (snapshot/rollup jobs and SLAs absent).

