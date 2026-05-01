# Intelligence Substrate QA

## 1) Audit Summary
- Stable components:
  - `apps.jobs.intelligence_engine.JobIntelligenceEngine` computes real job/pipeline metrics from DB state.
  - Existing domain events already exist in `apps.core.events` and are emitted in jobs/pipeline/interviews/candidates/agencies.
- Mocked/fragile components:
  - `apps.analytics.ai_brain.HiringAIBrainService` mixed static thresholds and heuristic outputs.
  - `apps.jobs.services.GlobalHiringCommandCenterService` includes hardcoded conversion/velocity placeholders.
  - Candidate intelligence was computed locally in `CandidateIntelligenceService` with no shared cache/events.
- Missing intelligence data sources before this change:
  - No shared tenant-scoped intelligence cache layer.
  - No common signal abstraction consumed across jobs/candidates/pipeline/recruiter intelligence.
  - No event-driven invalidation path dedicated to intelligence snapshots.
- Missing triggers before this change:
  - Intelligence updates were not centrally invalidated on candidate/application/interview/job lifecycle events.

## 2) Signal Definitions
- Job signals:
  - `application_rate`
  - `pipeline_movement_14d`
  - `stage_bottlenecks`
  - `aging_candidates`
  - `sla_violations`
  - `approval_delays`
- Candidate signals:
  - `engagement_signals`
  - `skill_match_signals`
  - `experience_signals`
  - `activity_signals`
  - `interview_signals`
- Pipeline signals:
  - `stuck_stage`
  - `drop_rate`
  - `conversion_rate`
  - `recruiter_activity`
  - `status_breakdown`
- System signals:
  - `recruiter_load`
  - `hiring_velocity_30d`
  - `active_jobs`
  - `recruiter_count`

## 3) Aggregator Architecture
- Shared substrate implemented in:
  - `backend/apps/analytics/intelligence_substrate.py`
- Core components:
  - `IntelligenceSignals` (independent reusable signal builders)
  - `IntelligenceAggregator` (job/candidate/pipeline/recruiter/global intelligence snapshots)
  - `IntelligenceCache` (tenant-safe namespace cache keys + versioned invalidation)
  - `IntelligenceEventTriggers` (domain-event invalidation + intelligence snapshot update emission)

## 4) Event Triggers
- Added intelligence event channel:
  - `apps.core.events.IntelligenceEvents.snapshot_updated`
- Added substrate signal consumers:
  - `backend/apps/analytics/signals.py`
- Triggered on:
  - `candidate.created`
  - `application.created`
  - `application.stage_changed`
  - `application.interviewed`
  - `interview.completed`
  - `job.created`
  - `job.approved`
  - `job.published`
  - `agency.recruiter_assigned`
  - `approval.requested`

## 5) Caching Strategy
- Uses Django cache (`django.core.cache`) with tenant-safe keying:
  - `intel:snapshot:{tenant}:{kind}:v{namespace}:{entity}`
- Namespace counters per tenant+kind:
  - `intel:ns:{tenant}:{kind}`
- Invalidation is O(1) per kind by namespace increment; avoids key scans.
- Supports memory cache fallback and Redis-backed cache transparently via Django settings.

## 6) API Endpoints
- New substrate APIs in analytics module:
  - `GET /api/v1/analytics/intelligence/jobs/{job_id}/`
  - `GET /api/v1/analytics/intelligence/candidates/{candidate_id}/`
  - `GET /api/v1/analytics/intelligence/pipeline/?requisition_id={id}`
  - `GET /api/v1/analytics/intelligence/recruiters/?recruiter_id={id}`
- Also exposed under existing intelligence namespace:
  - `GET /api/v1/intelligence/jobs/{job_id}/`
  - `GET /api/v1/intelligence/candidate/{candidate_id}/`
  - `GET /api/v1/intelligence/pipeline/`
  - `GET /api/v1/intelligence/recruiters/`

## 7) Multi-Tenant Safety
- All substrate reads are scoped by explicit `tenant_id`.
- Cache keys include tenant namespace.
- Event invalidation is tenant-scoped only.
- No cross-tenant entity lookups for snapshot computations.

## 8) Existing Panel Wiring
- Job Intelligence panel:
  - `apps.jobs.services.HiringAIBrainService` now hydrates from substrate snapshot + existing engine output.
- Pipeline intelligence:
  - `apps.jobs.views.JobPipelineSnapshotView` now consumes substrate pipeline/job signals for bottleneck/SLA-risk signals.
- Candidate intelligence:
  - `apps.candidates.services.CandidateIntelligenceService` now derives profile from substrate candidate signals while preserving existing response shape.
- Hiring AI Brain analytics:
  - `apps.analytics.ai_brain.HiringAIBrainService` now includes substrate-driven global/pipeline signals.

## 9) Tests Added
- `backend/apps/analytics/tests/test_intelligence_substrate.py`
  - event-driven recompute after domain event
  - cache invalidation behavior
  - tenant isolation
  - job intelligence signal payload
  - candidate intelligence signal payload
  - pipeline intelligence payload

## 10) Future Roadmap (Deferred)
- Asynchronous recomputation workers (Celery) for pre-warming high-traffic intelligence snapshots.
- Persisted time-series signal store for trend and anomaly detection.
- Advanced recommendation ranking and semantic matching layer (Phase 2+).
- Governance policy hooks for configurable trigger-to-refresh behavior.
