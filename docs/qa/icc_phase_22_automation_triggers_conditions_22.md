# Phase 22: Automation Trigger & Condition Engine

Prompt ID: `ICC-AUTOMATION-TRIGGERS-CONDITIONS-22`  
Phase: `Interview Command Center / Automation Layer / Phase 22`  
Module: `Automation Trigger & Condition Engine`

## Scope

Tenant-scoped runtime decision layer for determining whether automation rules are eligible to execute.

Supports:

- event-based triggers
- delayed and scheduled triggers
- recurring and SLA-based triggers
- nested AND/OR/NOT condition logic
- entity state and event payload evaluation
- deduplication and idempotency checks
- simulation, traceability, and auditability

Candidate has no configuration access. This layer decides eligibility before any automation action executes.

## 1. System Architecture

- Shared runtime layer: `AutomationTriggerConditionEngine`
- Core components:
  - Trigger registry engine
  - Event matching engine
  - Schedule trigger engine
  - Condition definition engine
  - Condition evaluation engine
  - Nested logic resolver
  - Entity context resolver
  - State snapshot resolver
  - Deduplication / idempotency guard
  - Eligibility decision engine
  - Trigger simulation / test engine
  - Policy / safety check linkage
  - Audit / evaluation trace engine
  - Performance optimization layer

Architecture layers:

- trigger registry layer
- event match layer
- schedule layer
- context resolution layer
- condition tree layer
- eligibility layer
- simulation layer
- audit layer
- optimization layer

Evaluation model:

- Trigger-first evaluation order
- Match event or schedule to active trigger definitions
- Resolve context from event payload, entity state, runtime state, and tenant context
- Evaluate condition tree with short-circuit logic
- Run dedupe and idempotency checks
- Produce eligibility decision
- Pass only eligible executions to action engine

Context precedence:

1. Event payload
2. Fresh entity lookup when required
3. Runtime snapshot or cached context if policy allows
4. Tenant/environment policy context

Runtime behavior:

- Supports real-time and deferred evaluation
- Supports event-first and time-based trigger models
- Uses published and active automation artifacts only
- Maintains tenant isolation and environment-aware rule enforcement

## 2. Database Design

Primary entities:

- `automation_trigger_definition`
- `automation_trigger_event_binding`
- `automation_trigger_schedule_binding`
- `automation_condition_definition`
- `automation_condition_group`
- `automation_condition_clause`
- `automation_condition_operand`
- `automation_condition_evaluation_log`
- `automation_trigger_match_log`
- `automation_eligibility_decision_log`
- `automation_context_snapshot`
- `automation_deduplication_record`
- `automation_simulation_run`
- `automation_trigger_condition_audit_log`

Key fields:

- `tenant_id`
- `rule_id`
- `rule_version_id`
- `trigger_type`
- `event_name`
- `schedule_type`
- `schedule_payload`
- `condition_tree_payload`
- `condition_group_type`
- `left_operand`
- `operator`
- `right_operand`
- `context_source`
- `status`
- `evaluation_status`
- `match_status`
- `eligibility_status`
- `deduplication_status`
- `entity_type`
- `entity_id`
- `correlation_id`
- `source_event_id`
- `evaluated_at`
- `created_at`
- `updated_at`

Entity purposes:

- `automation_trigger_definition`: active trigger metadata
- `automation_trigger_event_binding`: event-driven trigger bindings
- `automation_trigger_schedule_binding`: schedule and relative-time trigger bindings
- `automation_condition_definition`: root condition tree definition
- `automation_condition_group`: AND/OR/NOT grouping nodes
- `automation_condition_clause`: executable condition clauses
- `automation_condition_operand`: operand descriptors and dynamic references
- `automation_condition_evaluation_log`: clause and group evaluation logs
- `automation_trigger_match_log`: trigger match attempts
- `automation_eligibility_decision_log`: final allow/block decision records
- `automation_context_snapshot`: evaluation-time context snapshot
- `automation_deduplication_record`: correlation and idempotency keys
- `automation_simulation_run`: dry-run and simulation outputs
- `automation_trigger_condition_audit_log`: full audit trail for evaluation behavior

## 3. API Structure

**Trigger APIs**

- Fetch trigger registry
- Fetch supported trigger types
- Fetch supported event names
- Create trigger definition
- Update trigger definition
- Fetch trigger details
- Validate trigger binding
- Simulate trigger match
- Pause trigger
- Resume trigger

**Condition APIs**

- Create condition tree
- Update condition tree
- Fetch condition tree
- Validate condition schema
- Validate condition operands
- Simulate condition evaluation
- Fetch supported operators
- Fetch supported operand types
- Clone condition tree
- Compare condition versions

**Evaluation APIs**

- Evaluate event against trigger
- Evaluate trigger + conditions against entity
- Fetch evaluation trace
- Fetch eligibility decision
- Fetch match logs
- Fetch deduplication logs
- Replay evaluation
- Dry-run trigger-condition stack

**Schedule APIs**

- Create schedule trigger
- Update schedule trigger
- Validate schedule
- Simulate scheduled trigger firing
- Fetch upcoming schedule evaluations

Responsibility split:

- Design-time APIs manage definition, validation, simulation, and version comparison.
- Runtime evaluation APIs operate on active published trigger/condition artifacts.
- Governance and enterprise controls remain upstream authorities for what can be activated.

## 4. UI Architecture

UI includes:

- Trigger registry screen
- Supported events browser
- Trigger builder shell
- Condition builder shell
- Nested logic group editor
- Operand selector
- Entity context selector
- Schedule trigger editor
- Validation issue panel
- Simulation / dry-run screen
- Evaluation trace viewer
- Deduplication / idempotency insight view
- Version history view
- Audit trail view

Key UI modes:

1. Build Trigger
2. Build Condition Tree
3. Add Schedule Trigger
4. Validate Logic
5. Simulate & Test
6. Review Evaluation Trace
7. Audit / Debug Runtime Matching

UI rules:

- enterprise operations oriented
- structured and readable logic builder
- nested logic must remain understandable
- simulation results explicit
- event, context, and condition sources clearly visible
- no black-box evaluation behavior

## 5. Execution Flow

1. Active automation rule exists.
2. Event or schedule fires.
3. Trigger registry resolves candidate trigger matches.
4. Context is gathered.
5. Condition tree evaluates.
6. Deduplication / idempotency checks run.
7. Eligibility decision is produced.
8. Action engine receives only eligible executions.
9. Evaluation trace is logged.
10. Simulation and audit views remain available for operators.

Supported flows:

- event-trigger flow
- schedule-trigger flow
- delayed relative-time flow
- condition-pass flow
- condition-fail flow
- dedupe-block flow
- missing-context flow
- paused-trigger flow
- policy-block flow

## 6. Edge Cases

- Event payload missing required fields
- Event arrives before entity state is fully committed
- Condition references field that no longer exists
- Multiple triggers match same event
- Schedule fires after entity already changed state
- Stale snapshot vs live lookup mismatch
- Duplicate event with same correlation id
- Nested condition group malformed
- Relative deadline based on null timestamp
- Trigger active but referenced artifact version superseded
- Environment / tenant policy changes between schedule creation and firing
- Simulation result differs from live evaluation because data changed

Handling rules:

- Missing required context must fail safe and block unsafe execution.
- Superseded or inactive trigger references are not evaluable.
- Schedule and delayed triggers re-check policy and state before final eligibility.
- Data drift between simulation and live evaluation is surfaced explicitly in trace outputs.

## 7. Enterprise Features

- Trigger-first runtime decision engine
- Event-based and time-based trigger support
- Nested condition tree with short-circuit evaluation
- Entity and runtime context resolution with precedence rules
- Idempotent event handling and deduplication guards
- Simulation and dry-run support
- Explainable evaluation trace
- Tenant-isolated runtime decisioning
- Policy and governance enforcement at eligibility layer
- Performance-safe context resolution and optimized lookup patterns
- Reusable architecture for broader automation growth

## 8. Integration Mapping

- `Automation Layer Foundation`
- `All Execution Engines`
- `Flow Engine`
- `Composite Flow Engine`
- `Publish & Governance Layer`
- `Enterprise Controls Layer`
- `Analytics Engine`
- `Audit / Governance Layer`
- `Notification / Communication Systems`

