# TOS Phase 55: Intelligence Hub MVP UI 011

## Objective
- replace placeholder/demo Intelligence Hub UI with functional screens backed by real backend endpoints
- keep the UI operational, enterprise, and limited to backend-supported capabilities only
- make the current orchestration, suggestion, execution, prompt, failure, automation, and tenant settings surfaces usable before any deeper backend expansion

## Implemented Scope

### 1. Suggestions
- real list view backed by `GET /intelligence/suggestions/`
- real detail drawer backed by `GET /intelligence/suggestions/:id/`
- surfaced fields:
  - title
  - category
  - subtype from `payload_json.suggestion_subtype` or `suggestion_key`
  - confidence band and score
  - rationale JSON
  - source execution via linked AI request
  - current status
  - payload and audit metadata

### 2. Automations
- real automation rule list backed by `GET /intelligence/automations/`
- rule detail backed by `GET /intelligence/automations/:id/`
- run history backed by `GET /intelligence/automations/:id/runs/`
- last-run and run-count visibility derived from real automation execution data
- surfaced fields:
  - rule title and key
  - module scope
  - trigger
  - mode
  - status
  - duplicate window
  - conditions/actions counts
  - recent run history where present

### 3. Executions
- real AI execution list backed by `GET /intelligence/executions/ai/`
- real automation execution list backed by `GET /intelligence/executions/automation/`
- real execution detail backed by `GET /intelligence/executions/:id/`
- surfaced fields:
  - execution type
  - status
  - source module
  - source entity type and id
  - source event
  - created/started/completed timestamps
  - raw execution payload detail

### 4. Failures
- real failure list backed by `GET /intelligence/failures/`
- surfaced fields:
  - failure type
  - category
  - status
  - retryable indicator
  - linked execution id
  - reason
  - created timestamp

### 5. Prompts
- real prompt list backed by `GET /intelligence/prompts/`
- real prompt detail backed by `GET /intelligence/prompts/:id/`
- surfaced fields:
  - prompt title
  - module scope
  - use case key
  - version count
  - active version
  - active/inactive state
  - version inventory

### 6. Settings
- real tenant settings view backed by `GET /intelligence/settings/`
- real settings update backed by `PUT /intelligence/settings/`
- surfaced fields:
  - `ai_enabled`
  - `automation_enabled`
  - `default_approval_mode`
  - `allowed_provider_ids_json`
  - `feature_flags_json`
  - `notification_preferences_json`
  - `retry_policy_overrides_json`
  - `connector_enablement_json`
  - `visibility_permissions_json`

## UI Behavior
- no demo data is used
- old Intelligence Hub demo-only navigation breadth was reduced to the currently functional backend-backed sections
- empty states are explicit for no-data situations
- loading states are explicit per screen
- backend error states are explicit per screen
- no fake actions were added for unsupported backend operations
- settings save is the only write path exposed because it is already supported by the backend

## Placeholder/Demo Removal
- Intelligence Hub workspace demo content was replaced with real endpoint-driven rendering
- unused demo artifact `frontend/src/data/intelligenceHubDemo.ts` was removed
- navigation was narrowed to functional Intelligence Hub MVP sections only

## Current Functional Boundaries
- Intelligence Hub is now operational as a read-first orchestration console plus tenant settings editor
- suggestions remain review-oriented only
- automations are visible, not editable from this MVP
- execution detail is inspectable, not controllable from this MVP
- failures are inspectable, not retryable from this MVP
- prompts are inspectable, not editable from this MVP

## Explicitly Unwired Boundaries
- no orchestration event mapping expansion
- no automation execution coupling beyond visibility into real runs
- no auto-enqueue or auto-send behavior from suggestions
- no acceptance/apply path from suggestions into owner modules
- no approval workflow UI yet
- no prompt authoring/version editing UI yet
- no automation rule creation/editing UI yet
- no failure retry UI yet

## Validation
- targeted frontend tests added for:
  - suggestions load and detail drawer
  - automations section navigation and rule loading
  - executions empty state
  - failures empty state
  - prompts error state
  - settings load state
  - settings save path
- test command:
  - `npm test -- --run src/pages/intelligence/IntelligenceHubWorkspace.test.tsx`

## Notes On Build Verification
- targeted Intelligence Hub tests pass
- a repo-wide TypeScript pass still fails due to unrelated pre-existing frontend type errors outside Intelligence Hub MVP scope
- those unrelated failures do not block the new Intelligence Hub screen wiring itself

## Status
- Intelligence Hub backend deepening is intentionally paused after the current bounded suggestion work
- Intelligence Hub frontend is now minimally usable against real backend capabilities
- this phase locks the UI baseline needed before AI Governance & Approvals work begins

## Recommended Next Step
- move to AI Governance & Approvals MVP on top of this now-usable operational UI
- scope that work to real approval inventory, approval detail, approve/reject actions, and governance-safe owner boundaries rather than expanding suggestion breadth
