# TOS Phase 56: AI Governance 001 (Step 1 + Step 2)

## Objective
- introduce controlled, actionable governance for Suggestions in Intelligence Hub
- implement approve/reject/dismiss governance actions
- implement apply routing for approved suggestions with non-blocking failure handling

## Suggestion Lifecycle
- supported transitions:
  - `pending -> approved`
  - `pending -> rejected`
  - `pending -> dismissed`
- apply transitions:
  - `approved -> applied`
  - `approved -> apply_failed` (owner-contract failure path)
- invalid transitions are rejected with `400`

## APIs
- `POST /api/v1/intelligence/suggestions/{id}/approve/`
- `POST /api/v1/intelligence/suggestions/{id}/reject/`
- `POST /api/v1/intelligence/suggestions/{id}/dismiss/`
- `POST /api/v1/intelligence/suggestions/{id}/apply/`

Each endpoint enforces:
- tenant scoping (`tenant_id`-scoped lookup)
- permission checks (hub role + tenant visibility overrides)
- status transition validation (pending-only for this step)
- suggestion status update
- audit logging

Apply endpoint additionally enforces:
- role + tenant permission check for `apply`
- `approved`-only transition guard
- owner-module contract routing through orchestration service
- conversion/audit persistence even when owner module fails (non-blocking)

## Audit Fields
Tracked on suggestion records:
- `approved_by_id`, `approved_at`
- `rejected_by_id`, `rejected_at`
- `dismissed_by_id`, `dismissed_at`

Also tracked in audit logs:
- `ai_suggestion.approved`
- `ai_suggestion.rejected`
- `ai_suggestion.dismissed`
- `ai_suggestion.applied`
- `ai_suggestion.apply_failed`

## Permission Logic
- default role policy is enforced through hub permission mapping + action-level checks
- tenant overrides use `TenantIntelligenceSettings.visibility_permissions_json` keys:
  - `suggestion_approve_roles`
  - `suggestion_reject_roles`
  - `suggestion_dismiss_roles`
  - `suggestion_apply_roles`
- unauthorized users receive `403`

## UI Behavior (Suggestions Screen)
- added inline `Actions` column in the suggestions table
- row actions:
  - `Approve` (primary)
  - `Reject` (danger)
  - `Dismiss` (default)
- `Apply` (primary, shown only for `approved` rows)
- actions are only rendered when `status === pending`
- apply is rendered only when `status === approved`
- buttons are disabled while row action is in-flight
- rows refresh through query invalidation after action completion
- no modal dialogs are used in this step
- status badge now includes `applied` and `apply_failed`

## Apply Engine Routing
- `owner_module=communications` + `proposed_action_family=enqueue_communication` routes to communication dispatch contract
- `owner_module=pipeline` + `proposed_action_family=create_deadline` routes to pipeline deadline contract
- unsupported owner contracts produce `apply_failed` with conversion error metadata
- orchestration layer does not mutate owner-module business state directly; it uses owner contracts only
- failure is non-blocking: API returns success envelope with `applied=false`, suggestion marked `apply_failed`, and audit persisted

## Test Coverage
Backend (`apps.orchestration_center.tests.test_suggestion_engine`):
- approve success
- reject success
- dismiss success
- apply success from approved state
- apply failure produces non-blocking `apply_failed`
- invalid apply transition rejection
- apply permission enforcement
- apply tenant isolation
- invalid transition rejection
- permission enforcement
- tenant isolation
- audit creation

Frontend (`src/pages/intelligence/IntelligenceHubWorkspace.test.tsx`):
- approve action call from inline actions column
- reject action call from inline actions column
- dismiss action call from inline actions column
- apply action call for approved rows
- pending-only actions hidden on approved rows

## Out of Scope
- dedicated retry UX for `apply_failed`
- apply comment modal/editor
- automation/execution UI changes
