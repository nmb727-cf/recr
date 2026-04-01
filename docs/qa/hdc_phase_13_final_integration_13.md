# HDC-FINAL-INTEGRATION-13

## 1. System Architecture

Shared layer name: `HiringDecisionSystemIntegrationLayer`

Purpose:
- unify the full Hiring Decision Command Center into one coherent operational system
- connect Interview Command Center outputs, HDC engines, offer lifecycle, joining tracking, analytics, governance, audit, company workspace, agency workspace, and candidate-facing offer response experience
- provide the final architecture integration pass for end-to-end hiring decision operations

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
- Offer Lifecycle / Joining Tracking / Hiring Outcome Closure
- Analytics / Governance / Executive Intelligence

Core components:
1. `HDC System Integration Orchestrator`
2. `Cross-Engine State Coordination Layer`
3. `Interview-to-Decision Binding Layer`
4. `Decision-to-Offer Lifecycle Binding Layer`
5. `Offer-to-Joining Continuity Layer`
6. `Role-Based Operational Integration Layer`
7. `Analytics Signal Integration Layer`
8. `Governance & Policy Enforcement Integration Layer`
9. `Audit & Evidence Continuity Layer`
10. `Dependency & Consistency Validation Layer`

Architecture layers:
- `Decision Layer`
- `Committee Layer`
- `Comparison Layer`
- `Approval Layer`
- `Offer Intelligence Layer`
- `Compensation Layer`
- `Negotiation Layer`
- `Offer Release Layer`
- `Acceptance Layer`
- `Joining Layer`
- `Analytics Layer`
- `Governance Layer`
- `Audit Layer`
- `Experience Layer`

Operating model:
- ICC final outputs become the only valid upstream inputs for HDC decision creation
- each HDC engine owns its write model, while integration projections provide unified read models
- strict consistency is required for activation, approvals, frozen snapshots, final release, and accepted/joined state transitions
- eventual consistency is acceptable for dashboards, trend views, and some analytics projections
- analytics and governance consume finalized, versioned runtime signals only
- candidate remains a global entity with tenant association only
- all runtime execution remains tenant scoped

Source of truth model:
- interview outcomes and scorecards: ICC
- decision record: Decision Engine
- committee state and recommendation: Hiring Committee Engine
- comparison snapshot and ranking rationale: Candidate Comparison Engine
- final approval chain: Decision Approval Engine
- offer recommendation and scenario selection: Offer Intelligence Engine
- frozen compensation package: Compensation Engine
- negotiated package lineage: Negotiation Engine
- final release packet and release state: Final Offer Release Engine
- candidate response and acceptance state: Offer Acceptance Engine
- joining outcome state: Joining Tracking Engine
- cross-module unified state and readiness views: Integration projections
- governance and policy enforcement: Governance Layer
- audit evidence continuity: Audit Layer

State consistency model:
- write models remain engine-owned
- read models are integration-owned projections
- event versioning is mandatory
- replay and retry are allowed only with idempotent event handling and lineage checks
- stale projections never override authoritative engine state

Workspace separation model:
- company workspace has full internal operating view subject to role
- agency workspace gets bounded visibility only where policy permits, especially around offer, joining, and performance views
- candidate-facing experience is limited to released offer review, response, and optional joining confirmation

## 2. Database Design

Primary entities:
- `hdc_integration_registry`
- `hdc_runtime_binding`
- `hdc_event_contract`
- `hdc_state_projection`
- `hdc_artifact_binding`
- `hdc_dependency_map`
- `hdc_consistency_validation`
- `hdc_operational_snapshot`
- `hdc_release_readiness_record`
- `hdc_integration_audit_log`

Required fields across entities:
- `tenant_id`
- `module_name`
- `artifact_type`
- `artifact_id`
- `runtime_binding_type`
- `event_name`
- `event_version`
- `source_entity_type`
- `source_entity_id`
- `target_entity_type`
- `target_entity_id`
- `binding_status`
- `projection_status`
- `consistency_status`
- `validation_status`
- `release_status`
- `readiness_status`
- `created_at`
- `updated_at`

Recommended entity details:

### `hdc_integration_registry`
- `id`
- `tenant_id`
- `module_name`
- `artifact_type`
- `artifact_id`
- `binding_status`
- `created_at`
- `updated_at`

### `hdc_runtime_binding`
- `id`
- `tenant_id`
- `module_name`
- `runtime_binding_type`
- `source_entity_type`
- `source_entity_id`
- `target_entity_type`
- `target_entity_id`
- `binding_status`
- `created_at`
- `updated_at`

### `hdc_event_contract`
- `id`
- `tenant_id`
- `module_name`
- `event_name`
- `event_version`
- `contract_status`
- `created_at`
- `updated_at`

### `hdc_state_projection`
- `id`
- `tenant_id`
- `projection_type`
- `source_entity_type`
- `source_entity_id`
- `projection_status`
- `projection_payload`
- `created_at`
- `updated_at`

### `hdc_artifact_binding`
- `id`
- `tenant_id`
- `artifact_type`
- `artifact_id`
- `binding_target_type`
- `binding_status`
- `created_at`
- `updated_at`

### `hdc_dependency_map`
- `id`
- `tenant_id`
- `module_name`
- `dependency_module_name`
- `dependency_status`
- `created_at`
- `updated_at`

### `hdc_consistency_validation`
- `id`
- `tenant_id`
- `validation_scope`
- `consistency_status`
- `validation_status`
- `validation_payload`
- `created_at`
- `updated_at`

### `hdc_operational_snapshot`
- `id`
- `tenant_id`
- `snapshot_type`
- `snapshot_payload`
- `snapshot_status`
- `created_at`
- `updated_at`

### `hdc_release_readiness_record`
- `id`
- `tenant_id`
- `readiness_scope`
- `release_status`
- `readiness_status`
- `readiness_payload`
- `created_at`
- `updated_at`

### `hdc_integration_audit_log`
- `id`
- `tenant_id`
- `event_name`
- `event_version`
- `audit_payload`
- `created_at`

## 3. API Structure

### Integration APIs

#### Fetch HDC System Integration Map
- Purpose: return HDC module interaction map
- Method: `GET`
- Path: `/api/hdc/integration/map`
- Outputs:
  - `integration_map`
- Permissions:
  - Leadership Viewer
  - Governance Reviewer
  - Tenant Admin

#### Fetch Module Bindings
- Purpose: return current module bindings
- Method: `GET`
- Path: `/api/hdc/integration/bindings`
- Outputs:
  - `module_bindings`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - HR / HRBP

#### Fetch Artifact Runtime Bindings
- Purpose: return runtime artifact bindings
- Method: `GET`
- Path: `/api/hdc/integration/artifact-bindings`
- Outputs:
  - `artifact_runtime_bindings`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Fetch Event Contracts
- Purpose: return event contract registry
- Method: `GET`
- Path: `/api/hdc/integration/event-contracts`
- Outputs:
  - `event_contracts`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Validate Module Integration
- Purpose: validate module connectivity
- Method: `POST`
- Path: `/api/hdc/integration/validate-modules`
- Outputs:
  - `validation_result`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Validate Artifact Binding Readiness
- Purpose: validate artifact/runtime binding readiness
- Method: `POST`
- Path: `/api/hdc/integration/validate-artifacts`
- Outputs:
  - `artifact_binding_validation`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Validate End-To-End Decision Lifecycle
- Purpose: validate end-to-end HDC lifecycle continuity
- Method: `POST`
- Path: `/api/hdc/integration/validate-lifecycle`
- Outputs:
  - `lifecycle_validation`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - HR / HRBP

#### Fetch System Consistency Summary
- Purpose: fetch consistency health summary
- Method: `GET`
- Path: `/api/hdc/integration/consistency-summary`
- Outputs:
  - `consistency_summary`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Fetch Cross-Module Dependency Graph
- Purpose: fetch dependency graph
- Method: `GET`
- Path: `/api/hdc/integration/dependency-graph`
- Outputs:
  - `dependency_graph`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Fetch Operational Snapshot
- Purpose: fetch unified operational snapshot
- Method: `GET`
- Path: `/api/hdc/integration/operational-snapshot`
- Outputs:
  - `operational_snapshot`
- Permissions:
  - HR / HRBP
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

### Runtime State APIs

#### Fetch Unified Candidate Hiring Journey
- Purpose: fetch end-to-end candidate journey across HDC
- Method: `GET`
- Path: `/api/hdc/integration/journey/candidate/{candidate_id}`
- Outputs:
  - `candidate_hiring_journey`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Hiring Manager
  - Governance Reviewer

#### Fetch Unified Recruiter Operational State
- Purpose: fetch recruiter-facing operational state
- Method: `GET`
- Path: `/api/hdc/integration/state/recruiter`
- Outputs:
  - `recruiter_operational_state`
- Permissions:
  - Recruiter
  - HR / HRBP

#### Fetch Unified Hiring Decision State
- Purpose: fetch decision-centric unified state
- Method: `GET`
- Path: `/api/hdc/integration/state/decision/{decision_id}`
- Outputs:
  - `hiring_decision_state`
- Permissions:
  - Recruiter
  - Hiring Manager
  - HR / HRBP
  - Governance Reviewer

#### Fetch Unified Offer Lifecycle State
- Purpose: fetch offer lifecycle across intelligence, comp, negotiation, release, and acceptance
- Method: `GET`
- Path: `/api/hdc/integration/state/offer/{decision_id}`
- Outputs:
  - `offer_lifecycle_state`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Compensation Analyst
  - Governance Reviewer

#### Fetch Unified Joining Lifecycle State
- Purpose: fetch join tracking lifecycle
- Method: `GET`
- Path: `/api/hdc/integration/state/joining/{decision_id}`
- Outputs:
  - `joining_lifecycle_state`
- Permissions:
  - Recruiter
  - HR / HRBP
  - Leadership Viewer

#### Fetch Cross-Module Event Timeline
- Purpose: fetch ordered event timeline
- Method: `GET`
- Path: `/api/hdc/integration/timeline/{decision_id}`
- Outputs:
  - `event_timeline`
- Permissions:
  - Governance Reviewer
  - HR / HRBP
  - Leadership Viewer

#### Fetch Integration Incident State
- Purpose: retrieve active integration incidents
- Method: `GET`
- Path: `/api/hdc/integration/incidents`
- Outputs:
  - `integration_incident_state`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

### Validation / Rollout APIs

#### Run Final HDC Integration Validation
- Purpose: run final HDC validation suite
- Method: `POST`
- Path: `/api/hdc/integration/run-validation`
- Outputs:
  - `validation_run_result`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Run Consistency Audit
- Purpose: run state consistency audit
- Method: `POST`
- Path: `/api/hdc/integration/run-consistency-audit`
- Outputs:
  - `consistency_audit_result`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Run Dependency Validation
- Purpose: validate module dependencies
- Method: `POST`
- Path: `/api/hdc/integration/run-dependency-validation`
- Outputs:
  - `dependency_validation_result`
- Permissions:
  - Governance Reviewer
  - Tenant Admin

#### Run Readiness Checks
- Purpose: run rollout readiness checks
- Method: `POST`
- Path: `/api/hdc/integration/run-readiness`
- Outputs:
  - `readiness_result`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer where allowed

#### Publish HDC Integration Release Record
- Purpose: store integration release state
- Method: `POST`
- Path: `/api/hdc/integration/release`
- Inputs:
  - `release_payload`
- Outputs:
  - `release_record`
- Permissions:
  - Tenant Admin
  - Governance Reviewer

#### Activate Rollout Profile
- Purpose: activate rollout profile
- Method: `POST`
- Path: `/api/hdc/integration/rollout/activate`
- Inputs:
  - `rollout_profile`
- Outputs:
  - `rollout_status`
- Permissions:
  - Tenant Admin
  - Governance Reviewer

#### Pause Rollout If Critical Issues Detected
- Purpose: pause rollout
- Method: `POST`
- Path: `/api/hdc/integration/rollout/pause`
- Inputs:
  - `pause_reason`
- Outputs:
  - `rollout_status`
- Permissions:
  - Tenant Admin
  - Governance Reviewer

#### Fetch Validation Evidence
- Purpose: fetch evidence for validation results
- Method: `GET`
- Path: `/api/hdc/integration/validation-evidence`
- Outputs:
  - `validation_evidence`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

#### Fetch Rollout Blockers
- Purpose: fetch blockers for rollout
- Method: `GET`
- Path: `/api/hdc/integration/rollout/blockers`
- Outputs:
  - `rollout_blockers`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Viewer

## 4. UI Architecture

Frontend principles:
- cross-module architecture view
- unified candidate hiring journey map
- event lifecycle viewer
- binding and dependency visibility
- system readiness checklist
- consistency status badges
- clean enterprise system operations layout
- role-scoped visibility

### Executive / Leadership UI
- HDC system integration dashboard
- end-to-end hiring lifecycle summary
- approval-to-joining conversion view
- decision risk and delay visibility
- executive blocker and readiness summary

### Recruiter / HR UI
- unified hiring decision operations dashboard
- decision-to-offer tracker
- offer-to-joining tracker
- blocker and dependency tracker
- candidate lifecycle continuity view

### Governance / Admin UI
- integration validation dashboard
- dependency graph viewer
- policy enforcement status
- consistency audit screen
- release and rollout readiness panel
- cross-module issue monitor

## 5. Execution Flow

1. Interview Command Center final outputs are completed
2. Decision engine creates hiring decision context
3. Committee, comparison, and approval chain executes
4. Approved decision flows into offer intelligence and compensation
5. Negotiation executes where needed
6. Final offer is released
7. Candidate accepts, rejects, or queries
8. Joining tracking lifecycle begins
9. Final hiring outcome closes with joined, not joined, withdrawn, or dropped state
10. Analytics captures lifecycle signals
11. Governance and audit preserve control and evidence
12. Recruiters, leaders, and admins operate through role-specific interfaces
13. Cross-module consistency checks remain active throughout

Supported flows:
- straight-through no-negotiation flow
- committee-driven flow
- negotiated offer flow
- approval-gated offer flow
- accepted-to-joined flow
- rejected, expired, or dropped flow
- blocked-by-governance flow
- analytics and governance feedback flow
- rollout validation flow

## 6. Edge Cases

- interview outcome exists but decision context missing
- committee recommendation frozen on stale candidate evidence
- approval completed but offer intelligence not refreshed
- compensation snapshot changed during negotiation
- offer released on outdated approval version
- candidate accepts stale offer version
- joining case created twice from same accepted offer
- job closes before joining outcome finalized
- analytics misses one lifecycle event
- governance blocks release after negotiation closure
- agency and company views diverge in unsupported way
- integration validation passes earlier but fails after dependency change

Handling rules:
- stale or duplicate lineage is blocked by runtime binding and version validation
- candidate-facing response is valid only against active release lineage
- duplicate downstream case creation is prevented through idempotency keys on accepted offer linkage
- analytics gaps are flagged in validation and do not mutate authoritative write state

## 7. Enterprise Features

- unified HDC runtime state model
- versioned cross-module event contracts
- engine-owned write models with integration-owned read projections
- tenant-scoped runtime execution and analytics/governance consumption
- role-specific UI and operational separation
- consistency audits and dependency validation
- rollout readiness scoring and blocker detection
- governance-before-activation enforcement
- audit and evidence continuity across the full offer and joining lifecycle
- reusable integration model for future onboarding and employee system connectors

## 8. Integration Mapping

### Interview Command Center
- Consumes:
  - finalized interview outputs
  - scorecards
  - analytics flags
- Produces:
  - decision input context
- Events:
  - `hiring.decision.created`
- Downstream:
  - Decision Engine
- Validation before activation:
  - interview outcome completeness
  - scorecard availability

### Decision Engine
- Consumes:
  - ICC evidence
- Produces:
  - decision context
  - decision events
- Events:
  - `hiring.decision.created`
- Downstream:
  - Committee
  - Comparison
- Validation before activation:
  - valid decision lineage

### Hiring Committee Engine
- Consumes:
  - decision context
- Produces:
  - committee recommendation
  - committee state
- Events:
  - `hiring.committee.formed`
  - `hiring.committee.recommendation.completed`
- Downstream:
  - Approval
  - Governance
- Validation before activation:
  - member assignment
  - quorum rule validity

### Candidate Comparison Engine
- Consumes:
  - candidate pool and evidence
- Produces:
  - frozen comparison snapshot
- Events:
  - `hiring.comparison.snapshot.frozen`
- Downstream:
  - Approval
  - Committee review context
- Validation before activation:
  - role and job compatibility
  - snapshot freshness

### Decision Approval Engine
- Consumes:
  - decision context
  - committee recommendation
  - comparison snapshot
- Produces:
  - approval completion or rejection
- Events:
  - `hiring.approval.started`
  - `hiring.approval.completed`
- Downstream:
  - Offer Intelligence
  - Governance
- Validation before activation:
  - approval chain completeness

### Offer Intelligence Engine
- Consumes:
  - approved decision
- Produces:
  - offer recommendation and scenarios
- Events:
  - `hiring.offer.recommendation.generated`
- Downstream:
  - Compensation
- Validation before activation:
  - approved decision reference
  - expectation and policy context presence

### Compensation Engine
- Consumes:
  - selected offer scenario
- Produces:
  - frozen compensation package
- Events:
  - `hiring.compensation.frozen`
- Downstream:
  - Negotiation
  - Final Release
- Validation before activation:
  - policy fit
  - band fit
  - approval dependency closure

### Negotiation Engine
- Consumes:
  - frozen compensation baseline
- Produces:
  - negotiated package outcome
- Events:
  - `hiring.negotiation.started`
  - `hiring.negotiation.closed`
- Downstream:
  - Final Release
- Validation before activation:
  - baseline package lineage
  - approval-linked counters valid

### Final Offer Release Engine
- Consumes:
  - final approved package
  - negotiation closure
- Produces:
  - released offer packet
- Events:
  - `hiring.offer.released`
- Downstream:
  - Offer Acceptance
- Validation before activation:
  - release readiness
  - document binding
  - approval closure

### Offer Acceptance Engine
- Consumes:
  - released offer snapshot
- Produces:
  - accepted, rejected, queried, expired states
- Events:
  - `hiring.offer.accepted`
  - `hiring.offer.rejected`
- Downstream:
  - Joining
  - Governance
- Validation before activation:
  - candidate journey continuity
  - active release lineage

### Joining Tracking Engine
- Consumes:
  - accepted offer case
- Produces:
  - joining lifecycle outcomes
- Events:
  - `hiring.joining.pending`
  - `hiring.joined`
  - `hiring.not_joined`
  - `hiring.outcome.closed`
- Downstream:
  - Analytics
  - Job closure
- Validation before activation:
  - accepted offer uniqueness
  - joining case consistency

### Analytics Layer
- Consumes:
  - finalized lifecycle events
- Produces:
  - metrics, trends, and performance views
- Events:
  - analytics snapshot update events
- Downstream:
  - dashboards
  - intelligence
- Validation before activation:
  - signal completeness
  - metric lineage validity

### Governance Layer
- Consumes:
  - policy-sensitive events
  - overrides
  - exceptions
- Produces:
  - warn/block/escalate states
- Events:
  - governance policy and violation events
- Downstream:
  - all governed engines
- Validation before activation:
  - policy linkage present

### Audit Layer
- Consumes:
  - all major state transitions
- Produces:
  - immutable evidence continuity
- Events:
  - audit log events
- Downstream:
  - governance
  - compliance
- Validation before activation:
  - audit continuity checks

### Candidate Portal
- Consumes:
  - released offer and joining confirmation surfaces
- Produces:
  - candidate response and confirmation events
- Events:
  - candidate response events
- Downstream:
  - Acceptance
  - Joining
- Validation before activation:
  - candidate view version accuracy

### Company Workspace
- Consumes:
  - full company-side operational projections
- Produces:
  - user actions and governance controls
- Events:
  - role-based action events
- Downstream:
  - respective HDC modules
- Validation before activation:
  - role separation

### Agency Workspace
- Consumes:
  - bounded agency projections
- Produces:
  - permitted updates and tracking actions
- Events:
  - agency-side action events
- Downstream:
  - Acceptance
  - Joining
  - performance analytics
- Validation before activation:
  - policy-bounded visibility

### Notification / Communication Systems
- Consumes:
  - dispatch, approval, query, expiry, joining reminder events
- Produces:
  - notifications and reminders
- Events:
  - communication-required events
- Downstream:
  - candidate and internal users
- Validation before activation:
  - channel routing readiness

### Job Pipeline / Hiring Closure State
- Consumes:
  - joined, not-joined, withdrawn, dropped outcomes
- Produces:
  - job closure or reopen actions
- Events:
  - hiring closure status events
- Downstream:
  - requisition lifecycle
- Validation before activation:
  - outcome mapping correctness
