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
- list filtering is supported in the UI from real list payloads for:
  - status
  - module scope
  - trigger event
  - tenant scope derived from `tenant_id`
  - built-in vs custom derived from `is_builtin`
- last-run, next-run, and run-count visibility are derived from real automation execution data
- surfaced fields:
  - rule title and key
  - module scope
  - trigger
  - mode
  - status
  - built-in/custom
  - tenant/platform scope
  - owner/created by when available
  - updated timestamp
  - next scheduled run where present
  - duplicate window
  - full conditions
  - full actions
  - full scopes
  - recent run history where present
  - last execution result summary
  - execution stats where present
  - raw run payload/audit-oriented detail where present

### 3. Executions
- segmented executions screen with separate read-only views for:
  - AI Executions
  - Automation Runs
- real AI execution list backed by `GET /intelligence/executions/ai/`
- real automation execution list backed by `GET /intelligence/executions/automation/`
- real execution detail backed by `GET /intelligence/executions/:id/`
- UI filters supported from real list payloads for:
  - execution type via segmented AI vs automation view selection
  - status
  - source module
  - source entity type
  - provider on AI executions
  - created date range
- surfaced list fields:
  - execution id short reference
  - execution type
  - source module
  - source entity type and id
  - status
  - provider/model for AI executions
  - source event for automation runs
  - created timestamp
  - completed timestamp
  - duration when available
- surfaced detail fields:
  - execution type
  - execution id
  - status lifecycle
  - source module and source entity context
  - request/source context
  - use case, prompt version, provider, and model for AI executions
  - rule, mode, and scheduled time for automation runs
  - result summary
  - failure category and reason
  - retry count
  - linked suggestion/downstream reference visibility when present in payload
  - audit/metadata block
  - raw execution payload detail

### 4. Failures
- real failure list backed by `GET /intelligence/failures/`
- linked execution enrichment backed by:
  - `GET /intelligence/executions/ai/`
  - `GET /intelligence/executions/automation/`
  - `GET /intelligence/executions/:id/` for selected failure detail
- retry action backed by `POST /intelligence/failures/:id/retry/` for retryable, non-terminal failures only
- UI filters supported from real list payloads for:
  - retryable vs terminal classification
  - execution type
  - source module
  - status
  - created date range
- surfaced list fields:
  - failure id short reference
  - execution type
  - source module
  - source entity reference
  - failure classification
  - error category
  - short error message
  - created timestamp
  - retry count when linked execution data exposes it
  - status
- surfaced detail fields:
  - full error message
  - stack / technical detail block from stored operator notes and linked execution failure metadata when present
  - execution reference
  - retry history using retry count, max retries, and next retry time when present
  - related automation rule / AI execution reference when linked execution detail exposes it
  - source entity metadata
  - tenant context
  - failure classification
  - raw failure metadata and linked execution payload

### 5. Prompts
- real prompt list backed by `GET /intelligence/prompts/`
- real prompt detail backed by `GET /intelligence/prompts/:id/`
- UI filters supported from real list payloads for:
  - module scope
  - use case key
  - status
  - active/inactive derived from prompt status
  - versioned/unversioned derived from version inventory
- surfaced list fields:
  - prompt title and key
  - module scope
  - use case key
  - active version
  - status
  - updated timestamp
  - created by when available
- surfaced detail fields:
  - prompt summary / description
  - module and use case
  - active version
  - version visibility across all available versions
  - derived status history from version statuses
  - variables schema info when available on active version
  - output schema and validation rules when available on active version
  - scope, metadata, tenant context, safety notes, owner role, and version audit detail

### 6. Settings
- real tenant settings view backed by `GET /intelligence/settings/`
- real settings update backed by `PUT /intelligence/settings/`
- provider inventory enrichment backed by `GET /intelligence/providers/`
- connector inventory enrichment backed by `GET /intelligence/connectors/`
- surfaced editable fields:
  - `ai_enabled`
  - `automation_enabled`
  - `default_approval_mode`
  - `allowed_provider_ids_json` through real provider selection
  - `connector_enablement_json` through real connector toggles
  - `feature_flags_json`
  - `notification_preferences_json`
  - `retry_policy_overrides_json`
  - `visibility_permissions_json`
- surfaced read-side summary fields:
  - tenant id
  - allowed provider names/count
  - enabled connector count
  - connector enablement state
  - updated timestamp

## UI Behavior
- no demo data is used
- old Intelligence Hub demo-only navigation breadth was reduced to the currently functional backend-backed sections
- empty states are explicit for no-data situations
- loading states are explicit per screen
- backend error states are explicit per screen
- no fake actions were added for unsupported backend operations
- settings save is the only write path exposed because it is already supported by the backend
- automations are intentionally read-only even though backend write endpoints exist, because this MVP is scoped to safe operational visibility rather than rule management
- executions are intentionally read-only even where retry/cancel semantics may exist deeper in the platform, because those controls are not yet exposed as supported Intelligence Hub UI actions
- failures expose only the backend-supported retry path; broader failure management remains intentionally limited
- prompts are intentionally read-only in the frontend even though backend prompt-management routes exist, because Phase 55 is scoped to operational registry visibility rather than authoring
- settings expose the supported backend write path, with structured controls for providers/connectors and validated JSON editors for advanced policy objects

## Auth Wiring Correction (Post-MVP Stabilization)
- Intelligence Hub API calls are confirmed to use the shared authenticated `http` client only
- token extraction is now resilient to persisted auth-store shape variants via `frontend/src/utils/authSession.ts`
- request interceptor now restores legacy `access_token` key from persisted auth-store token when needed
- protected route gating now requires:
  - hydrated auth store
  - authenticated session state
  - present access token
- app bootstrap now re-runs `fetchMe` after auth-store hydration when a session is restored
- result:
  - logged-in users can load Suggestions, Automations, Executions, Failures, Prompts, and Settings with authenticated requests
  - unauthenticated or token-missing users are redirected to `/login`
  - no direct unauthenticated Intelligence Hub fetch path remains in the page implementation

## Placeholder/Demo Removal
- Intelligence Hub workspace demo content was replaced with real endpoint-driven rendering
- unused demo artifact `frontend/src/data/intelligenceHubDemo.ts` was removed
- navigation was narrowed to functional Intelligence Hub MVP sections only

## Current Functional Boundaries
- Intelligence Hub is now operational as a read-first orchestration console plus tenant settings editor
- suggestions remain review-oriented only
- automations are visible, not editable from this MVP
- execution detail is inspectable, not controllable from this MVP
- failures are inspectable and selectively retryable from this MVP when the backend marks them retryable
- prompts are inspectable with version/schema visibility, not editable from this MVP
- settings are editable from this MVP through the live tenant settings endpoint only

## Explicitly Unwired Boundaries
- no orchestration event mapping expansion
- no automation execution coupling beyond visibility into real runs
- no auto-enqueue or auto-send behavior from suggestions
- no acceptance/apply path from suggestions into owner modules
- no approval workflow UI yet
- no prompt authoring/version editing UI yet
- no automation rule creation/editing UI yet
- no automation toggle/simulate UI yet
- no failure resolve UI yet
- no execution retry/cancel UI yet

## Validation
- targeted frontend tests added for:
  - suggestions load and detail drawer
  - automations section navigation and rule loading
  - automations detail drawer
  - automations filters
  - automations empty, loading, and error states
  - AI executions list load
  - automation runs list load via segmented view switch
  - execution detail drawer
  - executions filters
  - executions empty, loading, and error states
  - failures list load with linked execution context
  - failure detail drawer
  - failures filters
  - failures empty, loading, and error states
  - failure retry path
  - prompts list load
  - prompt detail drawer
  - prompts filters
  - prompts empty, loading, and error states
  - prompts error state
  - settings load state with provider/connector inventory
  - settings save path
- test command:
  - `npm test -- --run src/pages/intelligence/IntelligenceHubWorkspace.test.tsx`
  - `npm test -- --run src/components/common/ProtectedRoute.test.tsx src/pages/intelligence/IntelligenceHubWorkspace.test.tsx`

## Notes On Build Verification
- targeted Intelligence Hub tests pass
- a repo-wide TypeScript pass still fails due to unrelated pre-existing frontend type errors outside Intelligence Hub MVP scope
- those unrelated failures do not block the new Intelligence Hub screen wiring itself

## Status
- Intelligence Hub backend deepening is intentionally paused after the current bounded suggestion work
- Intelligence Hub frontend is now minimally usable against real backend capabilities
- executions now expose distinct operational inspection for AI requests and automation runs without pretending mutation controls exist
- failures now expose enriched operational triage with backend-safe retry where supported, without adding unsupported resolve flows
- prompts now expose filtered registry inspection with version/schema visibility while keeping authoring actions out of scope
- settings now expose provider and connector-backed operational controls while keeping advanced policy objects in validated JSON editors
- this phase locks the UI baseline needed before AI Governance & Approvals work begins

## Recommended Next Step
- move to AI Governance & Approvals MVP on top of this now-usable operational UI
- scope that work to real approval inventory, approval detail, approve/reject actions, and governance-safe owner boundaries rather than expanding suggestion breadth
