# TOS Phase 56: AI Governance & Approvals 012

## Objective
- introduce governed suggestion lifecycle management
- add explicit approve, reject, dismiss, and apply flows
- keep orchestration_center orchestration-only during apply
- preserve non-blocking failure behavior and tenant isolation

## Governance Architecture
- suggestion lifecycle is now centered on:
  - `pending`
  - `approved`
  - `rejected`
  - `dismissed`
  - `applied`
  - `apply_failed`
- governance writes are implemented in `SuggestionService`
- apply execution records are stored in `AISuggestionConversion` with `conversion_type='apply'`
- owner-module mutation remains outside orchestration through existing owner-contract bindings

## Backend Endpoints Used
- `GET /intelligence/suggestions/`
- `GET /intelligence/suggestions/:id/`
- `POST /intelligence/suggestions/:id/approve/`
- `POST /intelligence/suggestions/:id/reject/`
- `POST /intelligence/suggestions/:id/dismiss/`
- `POST /intelligence/suggestions/:id/apply/`

## Permission Model
- baseline role enforcement remains RBAC-backed through Intelligence Hub permissions
- suggestion action permissions add tenant-level overrides from `TenantIntelligenceSettings.visibility_permissions_json`
- supported tenant override keys:
  - `suggestion_approve_roles`
  - `suggestion_reject_roles`
  - `suggestion_dismiss_roles`
  - `suggestion_apply_roles`
- default action access:
  - approve: `super_admin`, `tenant_admin`, `hr_manager`
  - reject: `super_admin`, `tenant_admin`, `hr_manager`
  - dismiss: `super_admin`, `tenant_admin`, `hr_manager`, `hiring_manager`, `recruiter`
  - apply: `super_admin`, `tenant_admin`, `hr_manager`, `hiring_manager`

## Apply Flow
- apply is only allowed when a suggestion is already `approved`
- orchestration builds normalized owner-contract context and delegates to the owner module
- current owner-module apply bindings implemented:
  - `communications / enqueue_communication`
  - `pipeline / create_deadline`
- no direct model mutation occurs inside orchestration_center
- failed apply attempts remain non-blocking:
  - suggestion is marked `apply_failed`
  - failed apply conversion is recorded
  - latest apply error/result metadata is surfaced on the suggestion
  - response remains operational (`200`) with failure payload and audit trail

## Audit Behavior
- suggestion audit events now include:
  - `ai_suggestion.approved`
  - `ai_suggestion.rejected`
  - `ai_suggestion.dismissed`
  - `ai_suggestion.applied`
  - `ai_suggestion.apply_failed`
- tracked metadata includes actor, timestamps, status changes, and conversion references
- suggestion records now store:
  - approval actor/time
  - rejection actor/time
  - dismissal actor/time
  - apply actor/time
  - latest apply result status
  - latest apply error/result payload
  - downstream action trace fields (`converted_artifact_type`, `converted_artifact_id`) when apply succeeds

## Suggestions UI
- suggestions list remains backed by real suggestion APIs only
- added operational filters for:
  - category
  - status
  - module
  - confidence min/max
- detail drawer now shows:
  - lifecycle status
  - approval metadata
  - rejection metadata
  - dismissal metadata
  - apply metadata
  - owner action support flag (supported vs read-only contract)
  - downstream action reference
  - apply outcome summary
  - owner contract information
  - conversion / retry history
- drawer actions now expose:
  - approve
  - reject
  - dismiss
  - apply (approved + supported owner contract only)
  - no fake retry button for apply failures when retry endpoint is unavailable

## Current Capabilities
- approve flow is functional end to end
- reject flow is functional end to end
- dismiss flow is functional end to end
- apply flow is functional end to end for supported owner contracts
- apply failures are recorded without blocking the suggestion surface
- tenant isolation is enforced on detail and action routes

## Actionable vs Read-Only Suggestion Types
- actionable today (apply supported end to end):
  - suggestions mapped to `communications/enqueue_communication`
  - suggestions mapped to `pipeline/create_deadline`
- governed but read-only for apply today:
  - suggestions with unsupported `owner_module/proposed_action_family` pairs
  - these remain reviewable and can still be approved/rejected/dismissed
  - the UI shows read-only messaging (`Apply not supported for this owner contract`) instead of exposing fake controls

## Apply Failure Recovery UI Rules
- when status is `apply_failed`, the list/detail surfaces explicit failure state and reason
- retry apply is currently read-only in UI because no safe retry endpoint is exposed for this phase
- retry visibility rule:
  - show no retry control when backend retry endpoint is absent
  - show explanatory read-only message in detail panel

## Boundaries
- no bulk governance actions yet
- no custom comment history timeline beyond stored metadata and audit logs
- no generic owner-module apply adapter for every possible action family yet
- unsupported owner-module/action-family combinations fail safely and remain non-blocking
- UI does not fake action availability beyond the backend-supported lifecycle

## Validation
- backend:
  - `python3 backend/manage.py test apps.orchestration_center.tests.test_suggestion_engine -v 1`
- frontend:
  - `npm test -- --run src/pages/intelligence/IntelligenceHubWorkspace.test.tsx`

## Current Limitations
- no dedicated `POST /intelligence/suggestions/:id/retry-apply/` endpoint yet
- apply retries require a future explicit safe-retry contract and idempotency policy
- unsupported owner-module/action-family pairs stay governed but non-actionable
