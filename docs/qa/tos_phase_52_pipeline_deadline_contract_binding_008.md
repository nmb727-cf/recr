# Talent Operating System
## Phase 52: Pipeline-Owned Deadline Contract Binding

Date: `2026-04-01`
Prompt Basis: `Implement a pipeline-owned deadline service so create_deadline becomes a real downstream binding`

### Chosen Integration Style

Chosen style:

- direct write contract through a pipeline-owned service boundary

Implemented contract:

- `apps.pipeline.services.PipelineDeadlineService.create_automation_deadline(...)`

This was chosen instead of a new event sink because Pipeline already owns the `ActionDeadline` domain and a stable service boundary is the cleanest minimal contract without inventing new cross-module event semantics.

### Contract Shape

Service:

- `PipelineDeadlineService.create_automation_deadline`

Inputs:

- `tenant_id`
- `entity_type`
- `entity_id`
- `action_required`
- `due_in_hours`
- `assigned_to`
- `escalate_to`
- `metadata`
- `external_source`
- `external_reference`

Outputs:

- `(deadline, created)`

Behavior:

- validates UUID-based entity ids
- creates a new pipeline `ActionDeadline` when no active matching external reference exists
- deduplicates when the same `external_reference` is already active for that entity

### Ownership Boundary

Boundary remains clean:

- `ActionDeadline` records remain owned by Pipeline
- `orchestration_center` does not write directly to `ActionDeadline`
- `orchestration_center` only calls the pipeline-owned service
- idempotency logic for deadline creation now lives inside Pipeline, where the deadline domain is owned

### Idempotency And Failure Behavior

Idempotency:

- dedupe key is passed as `external_reference`
- service checks existing active deadlines using:
  - `tenant_id`
  - `entity_type`
  - `entity_id`
  - `metadata.external_source`
  - `metadata.external_reference`

Failure behavior:

- invalid entity id or bad config raises service-level validation error
- automation execution captures failure without blocking the originating business flow
- ICC audit trail still records the automation action result
- no business write path is blocked by deadline binding failure

Auditability:

- deadline metadata stores:
  - `external_source=orchestration_center`
  - `external_reference`
  - automation run and rule references
- ICC audit trail still records automation action execution

### Automation Binding Change

`create_deadline` in:

- `backend/apps/orchestration_center/services/automation_action_executor.py`

now uses:

- `PipelineDeadlineService.create_automation_deadline`

Returned statuses:

- `completed`
- `deduplicated`

### Automation Rules Now Using Real create_deadline Binding

Current built-in seeded rule using real deadline binding:

- `jobs_publish_followup`

This rule now creates real pipeline-owned operational deadlines through the new service contract.

### Tests Added

Pipeline-side tests:

- `backend/apps/pipeline/tests/test_deadline_service.py`

Coverage:

- idempotent deadline creation
- invalid entity id validation

ICC runtime tests updated:

- `backend/apps/orchestration_center/tests/test_runtime_engine.py`

Coverage:

- real deadline creation via pipeline-owned service
- deduplicated create_deadline behavior

### Verification

Executed successfully:

- `python3 manage.py test apps.pipeline.tests.test_deadline_service apps.orchestration_center.tests.test_runtime_engine -v 1`
- `python3 manage.py check`

### Final Status

`create_deadline` is no longer stubbed.

It now creates real `ActionDeadline` records through a Pipeline-owned, idempotent, tenant-aware service contract without violating module ownership boundaries.
