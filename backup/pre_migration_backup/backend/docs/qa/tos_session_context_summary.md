# TOS Session Context Summary

## Locked State
- safe action hardening and contract normalization are complete enough for the current stage
- bounded suggestion integrations are paused after two live use cases
- Intelligence Hub backend deepening is paused after the current bounded suggestion milestone
- Intelligence Hub frontend now has a real MVP UI for currently supported backend capabilities
- AI Governance & Approvals is now implemented for the current bounded suggestion set
- Automation Intelligence policy layer is now introduced for governed auto-approve/auto-apply tiers
- no further suggestion breadth should be added until the platform returns to this layer deliberately

## Hardened Action Layer Summary
- orchestration stays coordination-only
- owner modules remain source of truth for owner-owned state
- shared `OwnerActionContext`, `OwnerActionResult`, and `OwnerContractError` define the normalized contract surface
- retry, duplicate, and error semantics are tenant-scoped and serialized into execution results
- unsupported paths remain intentionally stubbed instead of mutating state

## Bounded Suggestion Layer Summary
- live use cases:
  - `communication_draft`
  - `followup_recommendation`
- suggestion creation remains downstream of AI execution
- suggestions now support governed approve, reject, dismiss, and apply actions
- confidence and rationale are captured when available
- duplicate suggestion creation is execution-scoped and tenant-scoped
- apply remains owner-contract driven and non-blocking on failure

## Governance Layer Summary
- lifecycle states actively used by the platform:
  - `pending`
  - `approved`
  - `rejected`
  - `dismissed`
  - `applied`
  - `apply_failed`
- suggestion action APIs now exist for approve, reject, dismiss, and apply
- tenant-level governance permissions can be overridden through `visibility_permissions_json`
- apply attempts are recorded in suggestion conversions and suggestion audit metadata
- apply success now stores downstream owner-action traceability (`converted_artifact_type`, `converted_artifact_id`, enriched last apply result payload)
- apply failures are non-blocking and surfaced as first-class operational state (`apply_failed`) with stored failure reason/retry-safe metadata
- supported live apply bindings currently cover:
  - communications enqueue
  - pipeline deadline creation

## Automation Intelligence Layer Summary
- tenant-scoped `AutomationIntelligencePolicy` model is now active
- policy evaluation is asynchronous from suggestion creation via on-commit task dispatch
- policy tiers supported:
  - suggest only
  - auto approve
  - auto apply (restricted, explicit configuration)
- policy matching includes suggestion type, module scope, and confidence threshold
- auto-apply remains owner-contract based and non-blocking on downstream failure
- Intelligence Hub now exposes an `Automation Intelligence` section for policy configuration and lifecycle visibility

## Intelligence Hub MVP UI Summary
- live sections:
  - suggestions
  - automations
  - executions
  - failures
  - prompts
  - settings
- all six sections are wired to real backend endpoints only
- placeholder/demo Intelligence Hub content has been removed
- empty, loading, and error states are present across the MVP screens
- only backend-supported interactivity is exposed
- tenant settings editing is functional; suggestions now expose governed action controls while other sections remain intentionally read-first
- automations now expose operational list filters plus detailed rule/runs inspection, while remaining read-only
- executions now expose separate AI and automation views, client-side operational filters, and read-only detail inspection from unified execution detail payloads
- failures now expose enriched list/detail triage with linked execution context and a guarded retry action for backend-marked retryable failures only
- prompts now expose filtered prompt-registry inspection with version, schema, and audit visibility while remaining read-only in the frontend
- settings now expose real provider and connector-backed controls while leaving advanced policy objects as validated JSON editors
- automation intelligence policies are now configurable from a dedicated section (type/module/threshold/level/enablement)
- Intelligence Hub auth wiring is now hardened for restored sessions:
  - shared `http` client remains the only IH transport
  - token/tenant extraction is resilient to persisted auth-store shape variants
  - protected routes require hydrated auth state plus a present access token
  - app bootstrap re-fetches `/auth/me` after hydration when authenticated

## Explicit UI Boundaries
- no orchestration event mapping expansion in this phase
- no automation execution coupling beyond runtime visibility
- no unsupported direct orchestration mutation paths
- no generic owner-contract apply adapter for every possible owner module yet
- no dedicated apply-retry endpoint in this phase; failed apply recovery remains read-only in the UI
- no policy simulation/dry-run UI yet for automation intelligence rules
- no prompt authoring/editor yet
- no automation rule editor yet
- no automation rule toggle/test/simulate UI yet
- no failure resolve UI yet

## Explicit Pause
- no new bounded suggestion use cases should be wired in the immediate next step
- no deadline recommendation expansion at this stage
- resume the original planned platform build flow next, with Automation Intelligence (AI-driven workflows) as the recommended next bounded area
