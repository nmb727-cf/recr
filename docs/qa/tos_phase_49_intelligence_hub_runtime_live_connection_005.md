# Talent Operating System
## Phase 49: Intelligence Hub Runtime Activation And Live Connection

Date: `2026-04-01`
Prompt Sequence:
- Runtime activation for `orchestration_center`
- Real AI execution layer
- Intelligence Hub live UI connection

## Scope Completed

This phase moved `orchestration_center` from scaffold/config state into live runtime operation.

Completed in order:
1. Runtime activation
2. Real AI execution path
3. Intelligence Hub live UI hookup

## Backend Runtime Activation

Implemented:
- Django signal consumer loading in `backend/apps/orchestration_center/apps.py`
- Live event consumers in `backend/apps/orchestration_center/consumers/event_consumers.py`
- Runtime dispatch and event mapping in `backend/apps/orchestration_center/services/runtime_event_service.py`
- Real Celery task entrypoints in:
  - `backend/apps/orchestration_center/tasks/ai_tasks.py`
  - `backend/apps/orchestration_center/tasks/automation_tasks.py`
  - `backend/apps/orchestration_center/tasks/retry_tasks.py`
  - `backend/apps/orchestration_center/tasks/health_tasks.py`

Runtime guarantees preserved:
- business modules remain primary
- orchestration failures stay non-blocking
- tenant scoping preserved
- AI and automation requests use idempotency / dedupe protection
- retry and dead-letter paths are available
- audit logs are written for runtime dispatch and execution transitions

## Connected Platform Events

Connected live signals:
- `job.created`
- `job.published`
- `application.created`
- `application.stage_changed`
- `application.shortlisted`
- `interview.scheduled`
- `interview.completed`
- `interview.feedback_submitted`
- `interview.decision_recorded`
- `agency.candidate_submitted`

Mapped triggers:
- `job.created` -> AI `job_enrichment` + automation rules
- `job.published` -> AI `candidate_matching` + automation rules
- `application.created` -> AI `candidate_ranking` + automation rules
- `application.stage_changed` -> AI `stage_recommendation` + automation rules
- `application.shortlisted` -> AI `shortlist_summary` + automation rules
- `interview.scheduled` -> automation rules
- `interview.completed` -> AI `interview_summary` + automation rules
- `interview.feedback_submitted` -> AI `decision_assist` + automation rules
- `interview.decision_recorded` -> AI `decision_quality_check` + automation rules
- `agency.candidate_submitted` -> AI `submission_intake_summary` + automation rules

Not wired because no live platform signal exists yet:
- `candidate.created`
- `candidate.updated`
- `message.sent`

## Real AI Execution Layer

Implemented:
- provider/model routing in `backend/apps/orchestration_center/services/provider_router.py`
- active prompt resolution and rendering in `backend/apps/orchestration_center/services/prompt_registry_service.py`
- live AI execution request lifecycle in `backend/apps/orchestration_center/services/ai_execution_service.py`
- improved automation action handling in `backend/apps/orchestration_center/services/automation_rule_service.py`

Capabilities now real:
- routing-rule-aware provider selection
- tenant provider restriction enforcement
- prompt registry resolution instead of hardcoded strings
- structured output validation
- fallback provider/model attempts
- execution result persistence
- approval/review queue creation where required
- failure capture and retry scheduling
- local/mock execution path for safe runtime behavior without external credentials
- generic external provider HTTP execution for OpenAI-compatible endpoints

## UI Live Connection

Live Intelligence Hub data hookup completed in:
- `frontend/src/api/intelligenceHub.ts`
- `frontend/src/pages/intelligence/IntelligenceHubWorkspace.tsx`

Sections now pull live backend data:
- Overview
- Automations
- AI Actions
- Prompt Studio
- Models & Providers
- Executions
- Failures & Queue
- Approvals
- Connectors
- Settings

Approach:
- preserved existing workspace layout
- replaced seeded section rows where live backend data exists
- kept fallback continuity when runtime data is sparse
- preserved naming: UI = `Intelligence Hub`, backend app = `orchestration_center`

## Database And Migration Note

The `orchestration_center` app migration had been created earlier but was not applied in the runtime database.

Applied:
- `orchestration_center.0001_initial`

Result:
- `python3 backend/manage.py showmigrations orchestration_center` shows `0001_initial` as applied

## Verification

Backend:
- `python3 backend/manage.py check`
- runtime dispatch smoke call through `IntelligenceRuntimeEventService.dispatch(...)`

Frontend:
- `npm run build`

Result:
- backend checks passed
- runtime dispatch path executed safely
- frontend build passed

## Real Vs Stubbed

Real now:
- event consumers
- runtime dispatch
- AI execution creation
- automation run creation
- provider routing
- prompt execution path
- fallback handling
- retry entrypoints
- dead-letter requeue path
- live Intelligence Hub read surfaces

Still intentionally light:
- non-AI automation actions beyond recording/scheduling are still basic
- provider integrations are generic rather than provider-specific adapters
- advanced prompt comparison tooling is still minimal
- some downstream business-side application of approved outputs remains future work

## Final Verdict

`orchestration_center` is now operational as live platform runtime infrastructure.

Locked conclusion:
- safe to keep in system context
- safe to verify in UI
- safe to continue building on without architecture drift

