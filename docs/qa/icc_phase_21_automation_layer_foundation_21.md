# Phase 21: Automation Layer Foundation

Prompt ID: `ICC-AUTOMATION-LAYER-FOUNDATION-21`  
Phase: `Interview Command Center / Automation Layer / Phase 21`  
Module: `Automation Layer Foundation`

## Scope

Tenant-scoped runtime automation backbone for Interview Command Center.

Supports:

- event-driven automation
- trigger-condition-action execution
- delayed and scheduled actions
- reminders and escalations
- routing and assignment actions
- status transition automation
- score / threshold based actions
- candidate communication triggers
- composite flow progression
- exception handling
- auditability and safe execution

Candidate has no configuration access. Candidate only experiences automation outcomes.

## 1. System Architecture

- Shared runtime layer: `InterviewAutomationRuntime`
- Core components:
  - Event intake layer
  - Rule evaluation engine
  - Trigger registry
  - Condition evaluation engine
  - Action execution engine
  - Delay / schedule engine
  - Escalation engine
  - Retry / failure handling engine
  - Approval-gated action engine
  - Notification / communication linkage
  - Composite flow progression linkage
  - Audit / execution log engine
  - Runtime safety / policy guard layer
  - Dead letter / recovery queue

Architecture layers:

- event layer
- trigger layer
- condition layer
- action layer
- scheduling layer
- escalation layer
- safety layer
- audit layer
- recovery layer

Operating model:

- Runtime consumes only published and active automation artifacts.
- Automation is tenant-isolated.
- Supports event-first and time-based trigger models.
- Executes synchronous and asynchronous actions depending on action type.
- Respects enterprise controls, publish/governance state, and tenant runtime policies.

Runtime pipeline:

1. Event emitted by execution engine, flow engine, or composite flow engine.
2. Event intake validates, deduplicates, and correlates entity context.
3. Matching active rules are resolved from trigger registry.
4. Conditions evaluate in deterministic order.
5. Candidate actions are produced.
6. Policy and approval checks run.
7. Actions execute now, schedule for later, or wait in approval gate.
8. Success, retry, escalation, failure, or dead-letter state is recorded.

## 2. Database Design

Primary entities:

- `automation_runtime_rule`
- `automation_runtime_trigger`
- `automation_runtime_condition`
- `automation_runtime_action`
- `automation_execution_instance`
- `automation_execution_step_log`
- `automation_scheduled_job`
- `automation_escalation_record`
- `automation_retry_record`
- `automation_dead_letter_record`
- `automation_policy_check`
- `automation_approval_gate`
- `automation_execution_audit_log`
- `automation_runtime_state`
- `automation_runtime_summary`

Key fields:

- `tenant_id`
- `rule_id`
- `rule_version_id`
- `artifact_source_id`
- `trigger_type`
- `event_name`
- `condition_payload`
- `action_payload`
- `status`
- `execution_status`
- `scheduled_for`
- `started_at`
- `completed_at`
- `failed_at`
- `retry_count`
- `max_retries`
- `escalation_status`
- `approval_status`
- `policy_status`
- `dead_letter_status`
- `correlation_id`
- `entity_type`
- `entity_id`
- `source_event_id`
- `created_at`
- `updated_at`

Entity purposes:

- `automation_runtime_rule`: materialized active rule definition
- `automation_runtime_trigger`: trigger records tied to active rules
- `automation_runtime_condition`: executable condition logic
- `automation_runtime_action`: executable actions and execution mode
- `automation_execution_instance`: one event-driven automation execution
- `automation_execution_step_log`: per-step action and evaluation logs
- `automation_scheduled_job`: delayed and scheduled jobs
- `automation_escalation_record`: escalation path tracking
- `automation_retry_record`: retry history and retry decisions
- `automation_dead_letter_record`: permanently failed or quarantined executions
- `automation_policy_check`: runtime policy evaluation result
- `automation_approval_gate`: approval-gated action state
- `automation_execution_audit_log`: full runtime decision and action trail
- `automation_runtime_state`: materialized runtime state for operations
- `automation_runtime_summary`: aggregated runtime health and throughput view

## 3. API Structure

**Runtime APIs**

- Fetch active automation rules
- Fetch rule execution status
- Fetch execution log
- Fetch scheduled jobs
- Fetch failed jobs
- Fetch dead letter queue
- Retry failed execution
- Cancel scheduled execution
- Pause automation rule
- Resume automation rule
- Deactivate automation rule
- Fetch automation runtime summary

**Event APIs**

- Ingest event
- Validate event payload
- Simulate trigger match
- Fetch trigger registry
- Fetch supported event types
- Test automation against event

**Approval / control APIs**

- Fetch approval-gated actions
- Approve runtime action
- Reject runtime action
- Override blocked action if policy allows
- Fetch policy evaluation result

**Recovery APIs**

- Replay dead letter event
- Reschedule failed job
- Mark execution permanently failed
- Fetch compensation candidates

Responsibilities:

- Runtime APIs operate on execution state only.
- Governance remains source of truth for artifact publication and policy definitions.
- Runtime control APIs enforce live safety, approval gating, and recovery handling.

## 4. UI Architecture

UI includes:

- Automation runtime dashboard
- Active rules monitor
- Execution activity stream
- Scheduled jobs queue
- Failed executions queue
- Dead letter queue
- Approval-gated actions queue
- Escalation monitor
- Rule pause / resume controls
- Runtime audit trail
- Policy block / warning view
- Replay / retry / recover controls
- Health and throughput summary

Key modes:

1. Runtime Monitoring
2. Scheduled Execution Management
3. Failure / Retry Handling
4. Dead Letter Recovery
5. Approval-Gated Action Review
6. Policy / Safety Monitoring
7. Execution Audit Review

UI rules:

- enterprise operations oriented
- dense but readable
- execution state must be explicit
- failed vs retried vs dead-lettered must be obvious
- every control action auditable
- no hidden automation state

## 5. Execution Flow

1. Event is emitted by execution engine, flow, or composite flow.
2. Automation foundation ingests the event.
3. Matching triggers are resolved.
4. Conditions are evaluated.
5. Allowed actions are generated.
6. Policy and approval checks run.
7. Action executes immediately or is scheduled / approval-gated.
8. Execution result is logged.
9. Failures retry or dead-letter if needed.
10. Escalations fire if SLA or retry thresholds are reached.
11. Audit and analytics update.
12. Runtime dashboards reflect current automation state.

Supported flows:

- normal event-driven flow
- delayed action flow
- approval-gated flow
- retry flow
- dead-letter flow
- escalation flow
- paused rule flow
- blocked-by-policy flow

## 6. Edge Cases

- Duplicate event received
- Event arrives out of order
- Rule active but dependency service unavailable
- Policy changed after job scheduled but before execution
- Approval not received before action deadline
- Action partially succeeds
- Notification channel fails repeatedly
- Composite step progressed manually while delayed automation still pending
- Same candidate entity hit by multiple rules simultaneously
- Tenant admin pauses rule during queued executions
- Retry storm / loop risk
- Dead letter replay causes version mismatch

Handling rules:

- Idempotency keying and correlation prevent duplicate execution.
- Policy is re-checked before delayed job execution.
- Partial success triggers compensation path when action is reversible.
- Manual state changes invalidate stale delayed actions before run where required.

## 7. Enterprise Features

- Event-driven tenant-scoped automation runtime
- Trigger-condition-action execution model
- Scheduled and delayed execution support
- Retry, escalation, and dead-letter handling
- Approval-gated runtime actions
- Runtime policy and safety enforcement
- Idempotent event handling
- Published-active-only automation materialization
- Full runtime auditability
- Reusable backbone for future cross-module automation

## 8. Integration Mapping

- `All Execution Engines`
- `Flow Engine`
- `Composite Flow Engine`
- `AI Builder Automation Generation Engine`
- `Publish & Governance Layer`
- `Enterprise Controls Layer`
- `Notification Engine`
- `Communication Engine`
- `Analytics Engine`
- `Audit / Governance Layer`
- `Task / Queue Layer`

