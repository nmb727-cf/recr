# TOS Phase 52 - AI Suggestion Engine

## Purpose

The AI Suggestion Engine introduces a structured intelligence layer inside `orchestration_center` for producing auditable, reviewable recommendations without executing business mutations automatically.

Its purpose is to:
- generate AI-backed operational suggestions from platform events, entity context, and prompt-driven analysis
- keep suggestions separate from automation runs and owner-module state changes
- support human review, optional approval, and manual override before any downstream action is taken
- provide a reusable suggestion-to-action path for future workflows without turning `orchestration_center` into a source of truth

The Suggestion Engine is not an automation engine. It does not directly create, update, or resolve owner-domain records as part of suggestion generation.

## Separation Between Automation and Suggestions

Automation and suggestions serve different roles and must remain distinct.

Automation:
- executes preconfigured rules
- may call hardened owner contracts
- is designed for deterministic orchestration paths
- can produce real downstream actions when the rule allows it

Suggestions:
- produce proposed actions, insights, or recommendations
- do not mutate business state automatically
- may require review or approval before conversion
- preserve manual operator choice, including decline, defer, or edit-before-convert

Boundary rules:
- `orchestration_center` remains orchestration-only
- owner modules remain the only source of truth for business state
- a suggestion record is informational until explicitly converted through an approved path
- suggestion generation and suggestion conversion must be separately auditable

## Suggestion Lifecycle

Suggested lifecycle states:
- `draft`: suggestion object created but not yet fully evaluated or published
- `pending_review`: suggestion is available for human inspection
- `pending_approval`: suggestion requires governed approval before conversion
- `approved`: governance approval granted, but no business mutation has happened yet
- `rejected`: suggestion explicitly declined
- `converted`: suggestion was intentionally converted into an action, task, draft, or approval item
- `expired`: suggestion aged out or is no longer relevant
- `superseded`: newer suggestion replaced the prior one for the same context
- `failed`: generation or normalization failed after retries

Lifecycle principles:
- generation and conversion are separate state transitions
- approval is optional and policy-driven, not implicit
- converted does not mean auto-applied; it means a downstream orchestration or owner-contract handoff was intentionally created
- rejected, expired, and superseded suggestions remain visible for audit purposes

## Suggestion Categories

Initial category families should stay broad and operationally safe:
- `followup_recommendation`: suggests reminder, outreach, or follow-up timing
- `escalation_recommendation`: suggests operational escalation when deadlines or response windows are at risk
- `review_recommendation`: suggests creating a review task or routing for human review
- `assignment_recommendation`: suggests assignment or reassignment to a role or operator
- `communication_draft`: suggests message content, channel, or audience without sending it
- `risk_flag_recommendation`: suggests flagging attention areas for manual handling
- `deadline_recommendation`: suggests creating, adjusting, or prioritizing an owner-managed deadline
- `insight_summary`: provides intelligence only, with no conversion target required

Category design rules:
- categories should map to stable operational intents, not transient UI labels
- categories should support owner-module routing metadata
- unsafe lifecycle-changing categories should not be introduced until separately governed

## Confidence Scoring

Each suggestion should carry a normalized confidence score.

Recommended structure:
- `confidence_score`: decimal from `0.00` to `1.00`
- `confidence_band`: `low`, `medium`, `high`
- `confidence_explanation_json`: optional structured reasons, signals, or caveats

Scoring principles:
- confidence informs prioritization, not authority
- low-confidence suggestions may still be useful if transparent
- confidence must be stored with the suggestion snapshot for auditability
- downstream approval policy may use confidence thresholds, but confidence alone must not trigger mutation

## Approval and Governance Model

Approval remains optional and policy-based.

Governance model:
- low-risk suggestions may be `pending_review` and manually converted by authorized users
- medium or higher-risk suggestions may move to `pending_approval`
- approval may be satisfied through `ApprovalQueueItem` or a suggestion-specific review record
- approval decisions must record approver identity, timestamp, and decision rationale
- approved suggestions still require explicit conversion to downstream action

Governance requirements:
- manual override must always be supported
- users must be able to reject, defer, or edit a suggestion before conversion
- approval and conversion must be separate auditable events
- suggestion policies should be tenant-configurable over time

## Tenant Isolation

Suggestions are strictly tenant-scoped.

Isolation rules:
- all suggestion records must carry `tenant_id`
- list, detail, approval, and conversion endpoints must filter by tenant
- any linked AI execution request, approval item, or converted orchestration artifact must belong to the same tenant
- duplicate keys and conversion idempotency must be tenant-scoped
- cross-tenant references must be rejected as ownership violations

## Retry and Failure Handling

Suggestion generation should be retry-safe and failure-aware without blocking platform operations.

Recommended approach:
- suggestion generation requests may reuse `AIExecutionRequest` / `AIExecutionResult`
- failures should use structured categories such as `validation`, `ownership`, `provider_transient`, `provider_terminal`, `normalization`, `conversion`, and `governance`
- retryable failures should be marked explicitly with `retry_safe=true`
- non-retryable failures should preserve reason and remain visible for operators
- repeated failures may route into `ExecutionFailure` and eventually dead-letter handling if needed

Failure design rules:
- failed suggestions must not mutate owner-module state
- suggestion generation failure must not block automation execution, event ingestion, or owner workflows
- conversion failures must preserve the original suggestion and record a separate conversion attempt outcome

## Non-Blocking Design Principles

The Suggestion Engine is advisory by default and must be non-blocking.

Principles:
- event processing should continue even if suggestion generation fails
- owner workflows must not depend on suggestion success
- UI should surface missing or failed suggestions without breaking the underlying entity view
- approval queues and manual review should remain operable if AI generation is degraded
- future automation may consume suggestions, but suggestion creation itself must never be a hard dependency for business-critical execution

## Owner-Module Interaction Rules

Owner modules remain the only source of truth.

Interaction rules:
- suggestions may reference owner entities by type and id, but must not write owner-domain rows directly
- suggestion conversion may only call hardened owner contracts or create orchestration-owned review/approval artifacts
- `orchestration_center` must not bypass owner services or write cross-module models directly
- suggestion payloads should declare intended owner module, target entity type, and proposed action family
- if the owner contract does not exist or the path is unsupported, conversion must remain safely stubbed

## Data Model (High Level)

Recommended high-level model set:

### `AISuggestion`
Core suggestion record.

Suggested fields:
- `tenant_id`
- `suggestion_key`
- `category`
- `status`
- `source_event`
- `source_module`
- `source_entity_type`
- `source_entity_id`
- `owner_module`
- `proposed_action_family`
- `title`
- `summary`
- `confidence_score`
- `confidence_band`
- `payload_json`
- `rationale_json`
- `audit_metadata_json`
- `idempotency_key`
- `expires_at`
- `superseded_by_id`
- `ai_request` FK
- `approval_item` FK nullable
- `converted_artifact_type`
- `converted_artifact_id`
- `reviewed_by_id`, `reviewed_at`
- `approved_by_id`, `approved_at`
- `rejected_by_id`, `rejected_at`
- `converted_by_id`, `converted_at`

### `AISuggestionConversion`
Tracks conversion attempts and outcomes separately from the suggestion.

Suggested fields:
- `suggestion` FK
- `tenant_id`
- `conversion_type`
- `status`
- `requested_by_id`
- `requested_action_payload_json`
- `result_payload_json`
- `error_category`
- `error_message`
- `retry_safe`

### Optional `AISuggestionFeedback`
Operator feedback loop for future quality tuning.

Suggested fields:
- `suggestion` FK
- `feedback_type` such as accepted, edited, rejected, not_useful
- `comment`
- `submitted_by_id`

Model design rules:
- suggestion records store the recommendation snapshot, not owner truth
- conversion records store downstream orchestration or owner-contract handoff outcomes
- audit fields must be complete enough to reconstruct who saw, approved, rejected, or converted what and when

## API Shape (High Level)

Suggested API surface under orchestration APIs:

- `GET /api/v1/orchestration/suggestions/`
  - list suggestions for tenant with filters: category, status, source module, entity, confidence band
- `GET /api/v1/orchestration/suggestions/{id}/`
  - retrieve full suggestion detail, rationale, approval state, and conversion history
- `POST /api/v1/orchestration/suggestions/{id}/review/`
  - record review decision such as defer or reject
- `POST /api/v1/orchestration/suggestions/{id}/approve/`
  - optional governance approval
- `POST /api/v1/orchestration/suggestions/{id}/convert/`
  - create a downstream orchestration artifact, approval item, or owner-contract request
- `POST /api/v1/orchestration/suggestions/{id}/supersede/`
  - mark stale suggestion as superseded when appropriate
- `GET /api/v1/orchestration/suggestions/overview/`
  - summary counts by lifecycle state, category, confidence, and aging

API rules:
- write endpoints must be permission-gated and tenant-scoped
- conversion must be idempotent with a tenant-scoped dedupe key
- response payloads should include status, confidence, governance state, and linked artifacts
- conversion responses must show whether the result is draft-only, approved-only, queued, converted, deduplicated, or failed

## UI Integration (Intelligence Hub)

The Intelligence Hub should present suggestions as a separate operational surface, not mixed into automation execution logs.

Recommended UI areas:
- suggestions queue: sortable list by age, confidence, category, and status
- suggestion detail drawer/page: rationale, AI context, source entity, proposed action, audit timeline
- governance actions: approve, reject, defer, convert, or edit-before-convert
- conversion outcome panel: linked approval item, draft communication, or orchestration artifact
- filters for tenant-safe views by owner module, category, and confidence band

UI design rules:
- never imply that a suggestion has already changed business state
- clearly distinguish `suggested`, `approved`, and `converted`
- surface manual override actions prominently
- expose confidence and reasoning, but avoid representing them as deterministic facts

## Integration Hooks for Future Workflows

The Suggestion Engine should establish reusable integration hooks without forcing immediate workflow expansion.

Recommended hooks:
- event-to-suggestion generation trigger from runtime events
- AI execution result normalization into suggestion payloads
- optional approval queue creation based on policy
- suggestion-to-owner-contract conversion adapters for safe action families
- selector support for entity-level suggestion summaries in candidate, interview, pipeline, and agency views

These hooks should remain additive and non-blocking.

## Future Extensibility

The design should support future growth without collapsing suggestions into uncontrolled automation.

Expected extensions:
- category-specific conversion adapters
- tenant policy controls for approval thresholds and confidence thresholds
- feedback loops for suggestion quality tracking
- suggestion grouping, deduplication, and supersession strategies
- batched review workflows in the Intelligence Hub
- richer entity timelines that combine suggestions, approvals, conversions, and resulting owner actions

Extension guardrails:
- suggestion generation remains advisory
- owner modules remain the source of truth
- new conversion paths require explicit owner-contract support
- no future extension should allow suggestions to auto-mutate owner state without a separately approved governance change

## Summary

Phase 52 introduces a formal AI Suggestion Engine inside `orchestration_center` as an auditable, tenant-safe, non-blocking recommendation layer. It is intentionally separate from automation execution. Suggestions provide structured intelligence, optional approval, and explicit conversion into governed downstream actions while preserving manual override and owner-module authority at every step.
