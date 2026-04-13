# TOS Phase 53: Bounded Suggestion Integrations 009

## Scope
This phase wires the second bounded AI suggestion use case: `followup_recommendation`.

The integration remains suggestion-only and is created strictly downstream of completed AI execution. It does not auto-apply business state, does not invoke automation execution, and keeps owner modules as the source of truth if a suggestion is later accepted.

## Use Case Wired
- AI execution mapper: `communications / followup_recommendation`
- Suggestion category: `followup_recommendation`
- Suggestion subtype: `followup_recommendation`
- Owner module: `communications`
- Proposed action family: `enqueue_communication`

## Suggestion Payload Shape
The bounded mapper stores a review-friendly payload in `payload_json` with the following keys:

- `suggestion_subtype`: `followup_recommendation`
- `recommended_action`: `enqueue_communication`
- `channel`: defaults to `email` when absent
- `followup_type`: bounded subtype such as `candidate_followup`
- `template_key`: defaults to `followup` when absent
- `recipient_hint`: optional review hint such as `candidate`
- `recommended_window`: optional timing guidance
- `delay_hours`: optional numeric timing hint from the AI result
- `urgency`: optional urgency/priority hint
- `summary`: primary review text
- `reason`: bounded rationale text
- `source_event`
- `source_entity_type`
- `source_entity_id`
- `use_case_key`

The mapper also stores `rationale_json` with:

- `ai_execution_id`
- `module_scope`
- `use_case_key`
- optional `reason`
- optional `signals`
- optional `decision_factors`

`audit_metadata_json` records that the suggestion originated from AI execution and marks the bounded use case as `followup_recommendation`.

## Confidence And Rationale Handling
- Confidence is inherited from the AI execution result when present.
- Confidence below the safe bounded threshold (`0.40`) causes suggestion creation to be skipped.
- Missing or incomplete output is skipped when both `summary` and `reason` are empty.
- The mapper captures rationale when available and keeps it structured for review in Intelligence Hub UI.

## Duplicate Suppression
- Suggestion creation is idempotent per AI execution.
- The idempotency key is `ai-suggestion:{ai_execution_id}:followup_recommendation`.
- Re-processing the same completed execution returns the existing suggestion instead of creating another row.
- Tenant isolation is preserved because suggestion lookup and creation remain tenant-scoped.

## Non-Blocking Failure Behavior
- Invalid or low-confidence output raises a bounded `ValueError` in the mapper.
- The execution service converts that into `ai_suggestion.skipped` audit logging and leaves the AI execution completed.
- Unexpected mapper failures are converted into `ai_suggestion.generation_failed` audit logging and also do not block the originating AI execution from completing.

## Tests Added
- successful suggestion creation
- duplicate suppression
- invalid output handling
- low-confidence handling
- tenant isolation
- non-blocking failure behavior

These cases are covered in `apps/orchestration_center/tests/test_runtime_engine.py`.

## Intentionally Unwired
- no orchestration event mapping changes
- no automation execution coupling
- no auto-send, auto-enqueue, or auto-apply behavior
- no owner-module mutation on suggestion creation
- no suggestion acceptance/apply workflow for follow-up execution in this phase

## Recommendation For Next Bounded Suggestion Use Case
`deadline_recommendation` is the next clean bounded use case.

Reason:
- still suggestion-only
- operationally useful
- review-friendly payload is straightforward
- owner module can remain the source of truth on acceptance
- it continues proving reuse of the same suggestion creation path without coupling to automation
