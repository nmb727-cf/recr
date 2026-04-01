# Talent Operating System
## Phase 51: Intelligence Hub Downstream Contract Bindings

Date: `2026-04-01`
Prompt Basis: `Bind richer automation outputs to concrete downstream contracts where stable contracts already exist`

### Scope Completed

This phase bound only the automation outputs that already had stable downstream contracts.

### Bound Automation Actions

#### 1. `enqueue_communication`

Bound to:

- `apps.communications.email_dispatch.dispatch.EmailDispatchService.queue_send`

Binding type:

- direct stable write API

Implementation details:

- action resolves recipients from explicit emails or configured payload paths
- action resolves active email template by slug from communications templates
- action builds `EmailSendRequest`
- action queues email delivery through communications without taking ownership of email delivery logic

Failure behavior:

- if recipients are missing: action is marked `skipped`
- if template is missing and no direct subject/body exists: action is marked `skipped`
- if queue dispatch raises: automation action fails inside `orchestration_center`, audit remains preserved, originating business flow remains unaffected

#### 2. `schedule_followup`

Bound to:

- `EmailDispatchService.queue_send` indirectly through scheduled automation dispatch when channel is `email`

Binding type:

- internal scheduled action + direct stable write API on execution

Implementation details:

- follow-up action creates `AutomationScheduledAction`
- when the scheduled action becomes due, it executes as `enqueue_communication`
- email follow-ups therefore reuse the same stable communications queue contract

Failure behavior:

- failure is contained to the scheduled automation action
- scheduled action can fail/retry without blocking the originating business flow

#### 3. `create_review_task`

Bound to:

- `apps.orchestration_center.models.ApprovalQueueItem`

Binding type:

- internal stable write contract owned by `orchestration_center`

Implementation details:

- review task creation remains inside ICC governance ownership
- creates or reuses pending approval queue entries keyed by automation run and requested review action

Failure behavior:

- review task creation failure affects only automation action result state
- no business flow dependency is introduced

### Explicitly Unbound / Stubbed

#### 1. `create_deadline`

Status:

- intentionally left `stubbed_unbound`

Reason:

- pipeline currently has a concrete `ActionDeadline` model but does not yet expose a stable owner-side service or event sink for external deadline creation
- writing directly into pipeline models from `orchestration_center` would create hidden coupling and violate ownership boundaries

Current action result:

- returns `stubbed_unbound`
- reason code: `pipeline_deadline_contract_not_stable`

#### 2. `notify`

Status:

- still local/no external module binding

Reason:

- no dedicated stable notification-dispatch service contract was identified for generic in-app notification writes

#### 3. `escalate`, `assign`, `mark_flag`

Status:

- still structured-result only

Reason:

- no stable owner-side write APIs or event sinks were identified in target modules for these operations

### Verification

Runtime tests expanded and passed:

- `python3 manage.py test apps.orchestration_center.tests.test_runtime_engine -v 2`

System checks passed:

- `python3 manage.py check`

### Final Status

`orchestration_center` now binds automation output to stable downstream contracts only where safe:

- communication queue dispatch is live
- review queue ownership is live
- deadline ownership remains intentionally deferred until pipeline exposes a stable contract

### Recommended Next Step

Next work should be:

1. expose a stable pipeline-owned deadline service or event sink if deadline automation should become real
2. expose a communications notification-dispatch service if `notify` should bind beyond structured logging
3. add targeted tests for scheduled follow-up email execution through `scheduled_automation_dispatch`
