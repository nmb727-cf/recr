# Phase 25: Automation Monitoring & Recovery Layer

Prompt ID: `ICC-AUTOMATION-MONITORING-RECOVERY-25`  
Phase: `Interview Command Center / Automation Layer / Phase 25`  
Module: `Automation Monitoring & Recovery Layer`

## Scope

Tenant-scoped observability, diagnostics, and recovery layer for the automation runtime across Interview Command Center.

Supports:

- runtime health monitoring
- execution telemetry
- queue and throughput monitoring
- scheduled job health
- failure diagnostics
- dead-letter inspection
- retry and replay recovery
- stuck execution detection
- manual intervention workflows
- compensation tracking
- alerting and incident handling
- tenant-aware observability

Candidate has no access. This is operational reliability infrastructure for ops, governance, and support users.

## 1. System Architecture

- Shared layer: `AutomationMonitoringRecoveryLayer`
- Core components:
  - Runtime health monitor
  - Execution telemetry engine
  - Queue & throughput monitor
  - Scheduled job health monitor
  - Failure diagnostics engine
  - Dead letter inspection layer
  - Retry / replay recovery engine
  - Stuck execution detector
  - Manual intervention control layer
  - Safe compensation trigger layer
  - Alerting / incident signal engine
  - Policy-aware recovery guard
  - Audit & recovery trace engine
  - Tenant-isolated observability layer

Architecture layers:

- telemetry layer
- metrics layer
- trace layer
- diagnostics layer
- recovery layer
- intervention layer
- alerting layer
- audit layer
- isolation layer

Observability pipeline:

1. Automation runtime emits execution, schedule, queue, failure, and policy telemetry.
2. Monitoring layer aggregates real-time and historical signals.
3. Diagnostics classify failures and degradation patterns.
4. Recovery engine determines safe retry, replay, compensation, or manual intervention path.
5. Alerts and incidents are raised when severity thresholds are crossed.
6. Recovery actions and outcomes are audited and reflected back into dashboards.

Operating model:

- Tenant-local observability by default
- Platform-level operations view only where permitted and safely isolated
- Real-time and aggregated monitoring both supported
- Warning, degraded, incident, recovered, and quarantined states explicitly modeled
- Recovery respects publish/governance state, enterprise controls, active artifact versions, and idempotency rules

## 2. Database Design

Primary entities:

- `automation_runtime_metric_snapshot`
- `automation_execution_telemetry`
- `automation_queue_health_record`
- `automation_schedule_health_record`
- `automation_failure_record`
- `automation_failure_classification`
- `automation_dead_letter_inspection`
- `automation_recovery_operation`
- `automation_retry_replay_record`
- `automation_stuck_execution_record`
- `automation_manual_intervention_record`
- `automation_compensation_trigger_record`
- `automation_alert_record`
- `automation_incident_record`
- `automation_recovery_audit_log`
- `automation_observability_summary`

Key fields:

- `tenant_id`
- `rule_id`
- `rule_version_id`
- `execution_instance_id`
- `schedule_id`
- `queue_name`
- `metric_type`
- `metric_value`
- `status`
- `health_status`
- `failure_type`
- `failure_severity`
- `root_cause_payload`
- `dead_letter_status`
- `recovery_type`
- `recovery_status`
- `intervention_status`
- `compensation_status`
- `alert_status`
- `incident_status`
- `entity_type`
- `entity_id`
- `correlation_id`
- `source_event_id`
- `occurred_at`
- `created_at`
- `updated_at`

Entity purposes:

- `automation_runtime_metric_snapshot`: aggregated runtime metric samples
- `automation_execution_telemetry`: per-execution telemetry events
- `automation_queue_health_record`: queue depth, lag, and throughput health
- `automation_schedule_health_record`: scheduled job timeliness and lateness
- `automation_failure_record`: normalized failure events
- `automation_failure_classification`: root cause classification and severity
- `automation_dead_letter_inspection`: dead-letter inspection and review state
- `automation_recovery_operation`: retry, replay, reschedule, or compensation operations
- `automation_retry_replay_record`: retry/replay lifecycle records
- `automation_stuck_execution_record`: stuck execution detection and state
- `automation_manual_intervention_record`: manual ops actions and approvals
- `automation_compensation_trigger_record`: compensation attempts and outcomes
- `automation_alert_record`: alerts and notification state
- `automation_incident_record`: incident grouping, severity, ownership, and closure
- `automation_recovery_audit_log`: full audit trail for monitoring and recovery
- `automation_observability_summary`: materialized dashboard summary

## 3. API Structure

**Monitoring APIs**

- Fetch runtime health summary
- Fetch rule health status
- Fetch execution telemetry
- Fetch queue health
- Fetch schedule health
- Fetch failure trends
- Fetch dead letter summary
- Fetch stuck executions
- Fetch alert feed
- Fetch incident summary
- Fetch tenant observability dashboard data

**Recovery APIs**

- Retry failed execution
- Replay dead letter event
- Recover stuck execution
- Cancel stuck execution if allowed
- Reschedule missed job
- Trigger compensation action
- Suppress duplicate recovery if unsafe
- Fetch recovery recommendation
- Mark manual resolution
- Close recovery record

**Diagnostics APIs**

- Fetch failure detail
- Fetch root cause classification
- Fetch execution trace
- Fetch policy block reason
- Fetch dependency failure reason
- Fetch downstream service failure detail
- Simulate recovery safety

**Intervention / control APIs**

- Request manual intervention
- Approve intervention if required
- Execute manual intervention
- Pause problematic rule
- Resume rule after recovery
- Mute / unmute alerts
- Escalate incident to governance / ops

Responsibilities:

- Monitoring APIs expose health, telemetry, and incident state.
- Recovery APIs execute safe operational recovery paths.
- Diagnostics APIs provide explainable failure detail.
- Intervention APIs handle human-in-the-loop recovery and containment.

## 4. UI Architecture

UI includes:

- Automation health dashboard
- Rule health monitor
- Execution telemetry explorer
- Queue backlog screen
- Scheduled jobs health screen
- Failure diagnostics panel
- Dead letter queue viewer
- Stuck execution console
- Recovery operations panel
- Manual intervention workspace
- Alert / incident dashboard
- Recovery audit trail
- Compensation / replay history view
- Tenant observability summary

Key UI modes:

1. Runtime Monitoring
2. Failure Diagnosis
3. Dead Letter Review
4. Recovery Operations
5. Manual Intervention
6. Alert / Incident Management
7. Audit / Postmortem Review

UI rules:

- enterprise operations oriented
- real-time status must be obvious
- health, warning, incident, recovered states clearly distinct
- retry / replay / compensate actions clearly marked with risk
- every recovery action auditable
- no hidden operational state

## 5. Execution Flow

1. Automation runtime emits telemetry.
2. Monitoring layer aggregates health and traces.
3. Failure or anomaly is detected.
4. Diagnostics classify root cause and severity.
5. Recovery options are computed.
6. Safe automatic recovery executes if allowed.
7. Otherwise manual intervention or approval path starts.
8. Retry, replay, compensation, or reschedule occurs.
9. Outcome is logged and dashboards update.
10. Audit and incident history remain preserved.

Supported flows:

- normal healthy monitoring flow
- warning-only flow
- auto-recovery flow
- manual recovery flow
- blocked recovery flow
- dead-letter replay flow
- incident escalation flow
- post-recovery closure flow

## 6. Edge Cases

- Retry would repeat irreversible side effect
- Dead-letter replay uses stale entity state
- Queue clears but stale incident remains open
- Same execution marked stuck and failed simultaneously
- Downstream dependency recovers mid-retry cycle
- Manual intervention conflicts with auto recovery
- Tenant policy changes while recovery pending
- Artifact version superseded while recovery investigating older execution
- Compensation partially succeeds
- High-volume failure storm creates alert flood
- Incident spans multiple related rules
- Platform-level outage impacts many tenant-local schedules

Handling rules:

- Irreversible side effects block unsafe retry and require explicit operator path.
- Recovery uses current policy and version compatibility checks before action.
- Alert storm control and incident correlation prevent operational overload.
- Incident closure requires validation that recovery succeeded or was explicitly accepted.

## 7. Enterprise Features

- Tenant-scoped observability and recovery
- Real-time and historical health views
- Failure classification and root cause analysis
- Dead-letter inspection and controlled replay
- Stuck execution detection
- Safe retry, replay, reschedule, and compensation workflows
- Policy-aware recovery guards
- Incident and alert management
- Full auditability and postmortem traceability
- Reusable reliability layer for future cross-module automation operations

## 8. Integration Mapping

- `Automation Layer Foundation`
- `Automation Trigger & Condition Engine`
- `Automation Action Execution Engine`
- `Automation Scheduling & Escalation Engine`
- `All Execution Engines`
- `Flow Engine`
- `Composite Flow Engine`
- `Publish & Governance Layer`
- `Enterprise Controls Layer`
- `Analytics Engine`
- `Audit / Governance Layer`
- `Notification / Communication Engine`
- `Queue / Worker Infrastructure`
- `Incident / Alerting Systems`

