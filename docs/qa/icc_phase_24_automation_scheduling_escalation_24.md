# Phase 24: Automation Scheduling & Escalation Engine

Prompt ID: `ICC-AUTOMATION-SCHEDULING-ESCALATION-24`  
Phase: `Interview Command Center / Automation Layer / Phase 24`  
Module: `Automation Scheduling & Escalation Engine`

## Scope

Tenant-scoped time-governed runtime layer for delayed execution, scheduled execution, recurring reminders, SLA tracking, and escalation handling across Interview Command Center.

Supports:

- delayed execution
- absolute and relative schedule execution
- recurring execution
- reminder chains
- escalation ladders
- overdue and breach handling
- approval timeout handling
- reviewer inactivity timeout
- pause / resume / cancel scheduling logic
- safe rescheduling and recomputation

Candidate has no configuration access. Candidate only experiences scheduled reminders, deadlines, and escalations as outcomes.

## 1. System Architecture

- Shared runtime layer: `AutomationSchedulingEscalationEngine`
- Core components:
  - Schedule registry engine
  - Delayed execution planner
  - Relative time calculator
  - Absolute time scheduler
  - Recurring schedule engine
  - SLA deadline engine
  - Reminder chain engine
  - Escalation ladder engine
  - Overdue detection engine
  - Pause / resume / cancel scheduler
  - Resolution & suppression engine
  - Reschedule / recompute engine
  - Audit / timeline engine
  - Scheduling health monitor

Architecture layers:

- schedule definition layer
- time computation layer
- queue / timer layer
- reminder layer
- escalation layer
- resolution layer
- recompute layer
- audit layer
- health monitoring layer

Execution model:

- Scheduling is derived only from published and active automation artifacts.
- Supports:
  - relative-time schedules
  - absolute calendar schedules
  - recurring schedules
  - chained reminders
  - escalation ladders
  - SLA and deadline timers
- Scheduled executions are revalidated at fire time before action dispatch.
- Resolution and state changes suppress or cancel stale future work.

Time model:

- tenant-local time zone aware
- deterministic `next_fire_at` computation
- relative offsets based on anchor events and anchor timestamps
- absolute schedule validation against tenant calendar / environment policy if applicable
- recurring schedule progression stored and auditable

Operating behavior:

- company and agency tenants can differ in schedule strictness, reminder cadence, escalation depth, and SLA policy
- all time computations and recomputations are auditable
- escalation stops safely when resolution occurs

## 2. Database Design

Primary entities:

- `automation_schedule_definition`
- `automation_scheduled_execution`
- `automation_schedule_anchor_record`
- `automation_schedule_time_computation`
- `automation_reminder_chain_record`
- `automation_escalation_ladder_record`
- `automation_escalation_step_record`
- `automation_deadline_tracker`
- `automation_overdue_record`
- `automation_resolution_record`
- `automation_schedule_recompute_record`
- `automation_schedule_pause_record`
- `automation_schedule_cancel_record`
- `automation_schedule_audit_log`
- `automation_schedule_runtime_summary`

Key fields:

- `tenant_id`
- `rule_id`
- `rule_version_id`
- `schedule_id`
- `schedule_type`
- `anchor_type`
- `anchor_entity_type`
- `anchor_entity_id`
- `anchor_timestamp`
- `time_zone`
- `relative_offset_payload`
- `absolute_schedule_payload`
- `recurrence_payload`
- `deadline_at`
- `next_fire_at`
- `last_fired_at`
- `status`
- `execution_status`
- `resolution_status`
- `suppression_status`
- `escalation_status`
- `escalation_level`
- `retry_count`
- `correlation_id`
- `source_event_id`
- `created_at`
- `updated_at`

Entity purposes:

- `automation_schedule_definition`: runtime schedule metadata
- `automation_scheduled_execution`: concrete scheduled job instances
- `automation_schedule_anchor_record`: source anchor event/entity binding
- `automation_schedule_time_computation`: stored time calculation and recompute results
- `automation_reminder_chain_record`: reminder sequence definitions and state
- `automation_escalation_ladder_record`: escalation policy definition at runtime
- `automation_escalation_step_record`: per-escalation step schedule and result
- `automation_deadline_tracker`: SLA/deadline tracking records
- `automation_overdue_record`: overdue and breached item tracking
- `automation_resolution_record`: resolution and suppression decisions
- `automation_schedule_recompute_record`: recomputation history after state changes
- `automation_schedule_pause_record`: pause/resume state history
- `automation_schedule_cancel_record`: cancellation history
- `automation_schedule_audit_log`: full scheduling and escalation audit trail
- `automation_schedule_runtime_summary`: aggregate runtime health and timing metrics

## 3. API Structure

**Scheduling APIs**

- Create schedule definition
- Validate schedule definition
- Fetch schedule registry
- Fetch upcoming scheduled executions
- Fetch schedule details
- Pause schedule
- Resume schedule
- Cancel schedule
- Reschedule execution
- Recompute schedule from new anchor
- Fetch schedule runtime summary

**Reminder / escalation APIs**

- Create reminder chain
- Fetch reminder chain
- Update reminder chain
- Create escalation ladder
- Fetch escalation ladder
- Update escalation ladder
- Fetch overdue items
- Trigger escalation manually if allowed
- Resolve escalation
- Suppress future reminders / escalations
- Fetch escalation history

**Deadline / SLA APIs**

- Create deadline tracker
- Fetch deadline status
- Recompute SLA deadline
- Mark deadline resolved
- Fetch breached deadlines
- Fetch SLA health summary

**Recovery / control APIs**

- Replay missed scheduled execution
- Recover failed scheduled action
- Expire stale scheduled execution
- Fetch paused / cancelled schedules
- Fetch recompute log
- Fetch suppression / resolution history

Responsibilities:

- Scheduling layer computes and manages time-governed work.
- Action execution layer performs actual action dispatch at fire time.
- Governance and controls remain upstream authorities for policy and activation state.

## 4. UI Architecture

UI includes:

- Scheduling dashboard
- Upcoming actions queue
- Deadline / SLA board
- Reminder chain editor
- Escalation ladder editor
- Overdue items monitor
- Resolution / suppression panel
- Reschedule / recompute console
- Paused / cancelled schedules view
- Escalation timeline view
- Schedule audit trail view
- Scheduling health dashboard

Key UI modes:

1. Schedule Monitoring
2. Deadline / SLA Management
3. Reminder Chain Management
4. Escalation Ladder Management
5. Overdue / Breach Operations
6. Resolution / Suppression Handling
7. Audit / Timeline Review

UI rules:

- enterprise operations oriented
- time state must be obvious
- overdue, breached, resolved, and suppressed states clearly distinct
- escalation path visibility required
- every pause, resume, and reschedule action auditable
- no hidden timer state

## 5. Execution Flow

1. Automation rule becomes eligible.
2. Scheduling layer computes delayed, recurring, or deadline-based work.
3. Scheduled execution is created with anchor and `next_fire_at`.
4. Reminder chain or escalation ladder is linked if configured.
5. At fire time, scheduled execution is revalidated.
6. If still valid, action execution engine runs.
7. If unresolved after reminder or deadline breach, escalation step is computed.
8. If entity resolves, pending schedules are suppressed or cancelled.
9. Recompute occurs if anchor state changes, such as interview reschedule.
10. Audit, health monitoring, and dashboards update continuously.

Supported flows:

- relative delay flow
- absolute schedule flow
- recurring reminder flow
- escalation-on-breach flow
- resolution suppression flow
- recompute after state change flow
- paused schedule flow
- failed scheduled execution recovery flow

## 6. Edge Cases

- Interview rescheduled after reminder chain already created
- Schedule fires after entity already resolved
- Escalation actor no longer available
- Time zone changes after schedule creation
- Recurring schedule overlaps with manual follow-up
- Approval arrives after escalation already started
- Reminder fired but notification channel failed
- Same deadline computed twice from duplicate event
- Paused schedule misses intended window
- Resuming schedule after stale anchor
- Escalation step references deactivated role / user
- Active artifact version superseded while scheduled jobs exist
- Breach computed during system downtime and replayed later

Handling rules:

- Fire-time revalidation prevents stale schedules from executing unsafe actions.
- Duplicate deadline computation is blocked by correlation and dedupe controls.
- Reschedule and recompute preserve full audit history.
- Superseded artifact-linked schedules are revalidated against current activation state before firing.

## 7. Enterprise Features

- Tenant-scoped time-governed scheduling runtime
- Relative, absolute, recurring, and SLA-based scheduling support
- Reminder chains and escalation ladders
- Explicit resolution and suppression logic
- Deterministic `next_fire_at` computation
- Auditable recompute after anchor state changes
- Pause, resume, cancel, and reschedule controls
- Overdue and breach detection
- Runtime policy and governance enforcement
- Reusable backbone for future cross-module SLA and escalation orchestration

## 8. Integration Mapping

- `Automation Layer Foundation`
- `Automation Trigger & Condition Engine`
- `Automation Action Execution Engine`
- `All Execution Engines`
- `Flow Engine`
- `Composite Flow Engine`
- `Approval / Governance Layer`
- `Enterprise Controls Layer`
- `Notification Engine`
- `Communication Engine`
- `Analytics Engine`
- `Audit / Governance Layer`
- `Calendar / Deadline Services`

