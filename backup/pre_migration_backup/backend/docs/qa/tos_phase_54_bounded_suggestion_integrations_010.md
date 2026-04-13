# TOS Phase 54: Bounded Suggestion Integrations 010

## Scope
This phase locks the bounded suggestion milestone and intentionally pauses further suggestion breadth after two live use cases.

Suggestion creation remains strictly downstream of AI execution. It does not couple to automation execution and does not mutate owner-module business state.

## Live Bounded Suggestion Use Cases
- `communication_draft`
  - AI mapper: `communications / email_draft`
  - category: `communication_draft`
  - subtype: `email_draft`
  - owner module: `communications`
  - proposed action family: `enqueue_communication`
- `followup_recommendation`
  - AI mapper: `communications / followup_recommendation`
  - category: `followup_recommendation`
  - subtype: `followup_recommendation`
  - owner module: `communications`
  - proposed action family: `enqueue_communication`

## Suggestion Payload Shape
Suggestion rows are review-first and bounded for Intelligence Hub UI.

Shared fields:
- `suggestion_key`
- `category`
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

Current payload details:

- `communication_draft`
  - `suggestion_subtype`
  - `channel`
  - `subject`
  - `body`
  - source event/entity metadata
  - `use_case_key`
- `followup_recommendation`
  - `suggestion_subtype`
  - `recommended_action`
  - `channel`
  - `followup_type`
  - `template_key`
  - `recipient_hint`
  - `recommended_window`
  - `delay_hours`
  - `urgency`
  - `summary`
  - `reason`
  - source event/entity metadata
  - `use_case_key`

## Confidence And Rationale Handling
- Confidence is inherited from the AI execution result when available.
- Low-confidence output below the bounded threshold (`0.40`) is skipped.
- Invalid or incomplete output is skipped rather than stored as a suggestion.
- `rationale_json` stores structured reasoning such as:
  - `ai_execution_id`
  - `module_scope`
  - `use_case_key`
  - optional `reason`
  - optional `signals`
  - optional `decision_factors`

## Duplicate Suppression Behavior
- Suggestion creation is idempotent per AI execution.
- Communication draft uses:
  - `ai-suggestion:{ai_execution_id}:communication_draft`
- Follow-up recommendation uses:
  - `ai-suggestion:{ai_execution_id}:followup_recommendation`
- Re-processing the same execution returns the existing suggestion instead of creating a duplicate row.
- Duplicate suppression remains tenant-scoped.

## Non-Blocking Failure Behavior
- Invalid or weak outputs raise bounded mapper validation errors.
- The execution layer records `ai_suggestion.skipped` and leaves the AI execution completed.
- Unexpected mapper failures record `ai_suggestion.generation_failed` and also leave the AI execution completed.
- Suggestion generation never blocks the originating AI execution from reaching its terminal execution status.

## Explicitly Unwired Boundaries
- no orchestration event mapping expansion
- no automation execution coupling
- no auto-enqueue or auto-send behavior
- no suggestion acceptance or apply path into owner modules
- no auto-mutation of business state from suggestion creation
- no expansion beyond the two live bounded use cases in this stage

## Pause Decision
This layer is intentionally paused after:
- `communication_draft`
- `followup_recommendation`

Reason:
- current suggestion progress is sufficient for this platform stage
- core platform areas remain under construction
- additional suggestion breadth is deferred until the original platform build flow returns to it
