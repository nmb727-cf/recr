# Phase 23: Automation Action Execution Engine

Prompt ID: `ICC-AUTOMATION-ACTIONS-EXECUTION-23`  
Phase: `Interview Command Center / Automation Layer / Phase 23`  
Module: `Automation Action Execution Engine`

## Scope

Tenant-scoped runtime execution layer for eligible automation actions inside Interview Command Center.

Supports actions such as:

- reminders
- escalations
- assignments
- task creation
- status transitions
- composite progression
- approvals
- notifications
- queue item creation
- hold / resume paths
- analytics and governance update triggers

Candidate has no configuration access. Candidate only experiences outcomes of executed automation.

## 1. System Architecture

- Shared runtime layer: `AutomationActionExecutionEngine`
- Core components:
  - Action registry engine
  - Action dispatch engine
  - Action handler execution layer
  - Action sequencing engine
  - Immediate vs deferred action router
  - Approval-gated action executor
  - Retry / backoff engine
  - Compensation / recovery engine
  - Side-effect tracking engine
  - Idempotency guard layer
  - Policy / safety enforcement linkage
  - Execution result engine
  - Audit / trace engine
  - Action health / throughput monitor

Architecture layers:

- action registry layer
- dispatch layer
- execution layer
- sequencing layer
- approval gate layer
- retry layer
- compensation layer
- audit layer
- health monitoring layer

Execution model:

- Only published and active automation artifacts can dispatch actions.
- Action payloads are validated before dispatch and revalidated at execution boundary when delayed.
- Immediate, deferred, scheduled, and approval-gated execution are supported.
- Single action and ordered multi-action sequences are supported.
- Runtime is tenant-isolated and policy-aware.

Handler model:

- Each action type maps to versioned handler contract
- Handlers declare:
  - action type
  - payload schema
  - synchronous or asynchronous capability
  - retryability
  - reversibility
  - compensation support
  - approval requirement

Action dispatch lifecycle:

1. Receive eligible action payload from trigger-condition layer.
2. Validate payload and handler compatibility.
3. Run policy, approval, and idempotency checks.
4. Dispatch immediate, deferred, or approval-pending execution.
5. Execute handler(s) in sequence if multi-step.
6. Record result, side effects, and trace.
7. Retry, compensate, or dead-end based on failure rules.

## 2. Database Design

Primary entities:

- `automation_action_definition`
- `automation_action_handler_mapping`
- `automation_action_execution_instance`
- `automation_action_execution_step`
- `automation_action_payload_snapshot`
- `automation_action_result_record`
- `automation_action_retry_record`
- `automation_action_compensation_record`
- `automation_action_approval_wait`
- `automation_action_side_effect_record`
- `automation_action_idempotency_record`
- `automation_action_policy_check`
- `automation_action_trace_log`
- `automation_action_runtime_summary`

Key fields:

- `tenant_id`
- `rule_id`
- `rule_version_id`
- `action_id`
- `action_type`
- `handler_key`
- `execution_instance_id`
- `step_order`
- `payload_snapshot`
- `status`
- `execution_status`
- `approval_status`
- `policy_status`
- `idempotency_key`
- `entity_type`
- `entity_id`
- `correlation_id`
- `source_event_id`
- `scheduled_for`
- `started_at`
- `completed_at`
- `failed_at`
- `retry_count`
- `max_retries`
- `compensation_status`
- `side_effect_status`
- `result_payload`
- `error_payload`
- `created_at`
- `updated_at`

Entity purposes:

- `automation_action_definition`: action type metadata and schema
- `automation_action_handler_mapping`: action-to-handler binding
- `automation_action_execution_instance`: root execution object
- `automation_action_execution_step`: per-step execution state in sequence
- `automation_action_payload_snapshot`: immutable payload at dispatch time
- `automation_action_result_record`: success/failure result payload
- `automation_action_retry_record`: retry attempts and backoff state
- `automation_action_compensation_record`: compensation actions and outcomes
- `automation_action_approval_wait`: actions paused for approval
- `automation_action_side_effect_record`: side effects and downstream mutations
- `automation_action_idempotency_record`: dedupe and duplicate prevention keys
- `automation_action_policy_check`: runtime policy evaluation results
- `automation_action_trace_log`: full execution trace
- `automation_action_runtime_summary`: aggregate operational summary

## 3. API Structure

**Action execution APIs**

- Fetch action registry
- Fetch supported action types
- Validate action payload
- Dispatch action
- Dispatch action sequence
- Fetch execution instance
- Fetch execution step status
- Fetch action result
- Fetch side effects
- Cancel pending action if allowed
- Pause action queue if allowed
- Resume action queue if allowed
- Fetch action runtime summary

**Approval-gated action APIs**

- Fetch approval-pending actions
- Approve action execution
- Reject action execution
- Expire approval-pending action
- Override blocked action if policy allows
- Fetch approval decision trail

**Retry / recovery APIs**

- Retry failed action
- Retry failed sequence step
- Run compensation action
- Mark action permanently failed
- Reschedule deferred action
- Replay action with new payload if policy allows
- Fetch compensation history

**Audit / trace APIs**

- Fetch action trace
- Fetch execution logs
- Fetch idempotency record
- Fetch policy evaluation
- Fetch action health metrics

Responsibility split:

- Runtime APIs manage live execution state and recovery.
- Governance remains source of truth for artifact publication and approval policy.
- Runtime must re-check policy and artifact validity at protected execution points.

## 4. UI Architecture

UI includes:

- Action registry screen
- Supported actions browser
- Action execution monitor
- Multi-step action sequence viewer
- Approval-pending action queue
- Failed actions queue
- Retry / compensation console
- Side-effect audit panel
- Idempotency / duplicate prevention insight view
- Policy block / warning view
- Execution trace viewer
- Runtime health dashboard

Key UI modes:

1. Action Monitoring
2. Approval-Gated Action Review
3. Failed Action Recovery
4. Compensation / Side-Effect Review
5. Policy / Safety Monitoring
6. Audit / Trace Inspection
7. Runtime Health Operations

UI rules:

- enterprise operations oriented
- dense but readable
- execution path must be clear
- side effects must be visible
- irreversible actions must be clearly marked
- every retry, override, and compensation action auditable
- no hidden runtime action state

## 5. Execution Flow

1. Trigger-condition engine marks automation as eligible.
2. Action execution engine receives action payloads.
3. Action payloads are validated.
4. Policy, approval, and idempotency checks run.
5. Action dispatch occurs.
6. Action executes immediately or is scheduled / approval-gated.
7. Result and side effects are recorded.
8. If failure occurs, retry or compensation path starts.
9. Final execution outcome is logged.
10. Runtime dashboards, audit, analytics, and downstream systems update.

Supported flows:

- single-action immediate flow
- multi-action sequence flow
- delayed action flow
- approval-gated action flow
- failure and retry flow
- compensation flow
- idempotency-block flow
- policy-block flow

## 6. Edge Cases

- Action payload valid at queue time but invalid at execution time
- Target entity changed state before delayed action fires
- Approval arrives after deadline
- First action succeeds and second action fails
- Retry would duplicate external side effect
- Paused rule has queued actions waiting
- Same action triggered twice with same correlation id
- Compensation itself fails
- Manual override conflicts with auto retry
- Tenant policy changes between schedule and execution
- Active artifact version superseded while deferred action still pending
- Analytics/governance downstream unavailable

Handling rules:

- Deferred actions re-check payload, entity state, policy, and source artifact validity.
- Duplicate side effects are prevented through idempotency keys and side-effect records.
- Partial sequence failure can stop, continue with warning, or compensate based on sequence policy.
- Downstream analytics or governance failures must not corrupt primary execution state.

## 7. Enterprise Features

- Tenant-scoped action execution runtime
- Typed and versioned action registry
- Immediate, deferred, scheduled, and approval-gated execution
- Ordered multi-action sequence support
- Retry, backoff, and compensation support
- Side-effect tracking and idempotency protection
- Runtime policy and governance enforcement
- Full traceability and auditability
- Health, throughput, and failure visibility
- Reusable architecture for future cross-module action execution growth

## 8. Integration Mapping

- `Automation Layer Foundation`
- `Automation Trigger & Condition Engine`
- `All Execution Engines`
- `Flow Engine`
- `Composite Flow Engine`
- `Notification Engine`
- `Communication Engine`
- `Publish & Governance Layer`
- `Enterprise Controls Layer`
- `Analytics Engine`
- `Audit / Governance Layer`
- `Task / Queue Layer`

