# HDC-DECISION-APPROVAL-05

## 1. System Architecture

Shared engine name: `DecisionApprovalEngine`

Purpose:
- control how hiring decisions move from recommendation to approved final decision
- enforce structured approval workflows, conditional approval paths, escalations, exceptions, overrides, and audit-safe signoff
- act as the enterprise control layer between decision recommendation and downstream offer, rejection, hold, or reconsideration actions

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
  - Decision Engine
  - Hiring Committee Engine
  - Candidate Comparison Engine
  - Decision Approval Engine
- Offer Management / Rejection / Hold / Reconsideration

Core components:
1. `Approval Workflow Engine`
2. `Approval Rule Engine`
3. `Approval Hierarchy Engine`
4. `Conditional Approval Engine`
5. `Escalation Engine`
6. `Exception / Override Engine`
7. `Approval Timeline Engine`
8. `Final Approval Resolver`
9. `Approval Audit Engine`
10. `Downstream Decision Trigger Engine`

Supported approval modes:
- `recruiter_approval`
- `hiring_manager_approval`
- `leadership_approval`
- `multi_step_approval_chain`
- `conditional_approval`
- `committee_recommendation_approval`
- `governance_required_approval`
- `exception_approval`
- `urgent_expedited_approval`

Role architecture:
- Recruiter
- Hiring Manager
- Department Head
- Business Leader
- Leadership Approver
- Governance Reviewer
- Tenant Admin
- Decision Owner

Operating model:
- approval workflows bind to a specific tenant, job, candidate, and decision context
- recommendation, committee outcome, comparison snapshot, and supporting evidence form the approval packet
- approval path can be sequential, parallel, conditional, or expedited
- final approval resolution is not complete until all mandatory approval conditions are satisfied
- candidate remains a global entity with tenant association only
- candidate never accesses approval UI or approval state

Approval policy defaults:
- recruiter cannot self-approve final hiring decision by default unless tenant policy explicitly allows low-risk internal workflows
- hiring manager approval is mandatory for standard hire decisions unless a tenant-specific exception policy exists
- leadership approval is required for critical hires, executive roles, or policy-defined high-risk decisions
- compensation band or grade can trigger additional approval path via conditional rules
- approval chain can reopen after rejection only through revision/reopen workflow with prior audit preserved
- revisions never overwrite prior approval history; they append a new approval cycle under the same decision lineage

Architecture layers:
- `Workflow Resolution Layer`
- `Assignment Layer`
- `Approver Action Layer`
- `Escalation & Exception Layer`
- `Final Resolution Layer`
- `Audit Layer`

## 2. Database Design

Primary entities:
- `decision_approval_workflow`
- `decision_approval_step`
- `decision_approval_assignment`
- `decision_approval_action`
- `decision_approval_condition`
- `decision_approval_escalation`
- `decision_approval_exception`
- `decision_approval_override`
- `decision_approval_timeline`
- `decision_approval_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `approval_workflow_id`
- `approval_step_id`
- `approver_role`
- `approver_user_id`
- `approval_status`
- `step_status`
- `condition_status`
- `escalation_status`
- `override_status`
- `exception_status`
- `effective_decision_type`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `decision_approval_workflow`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `workflow_type`
- `approval_status`
- `effective_decision_type`
- `workflow_version`
- `current_step_id`
- `submitted_by`
- `submitted_at`
- `created_at`
- `updated_at`

### `decision_approval_step`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `step_order`
- `step_type`
- `approver_role`
- `step_status`
- `is_mandatory`
- `is_parallel_group`
- `sla_due_at`
- `created_at`
- `updated_at`

### `decision_approval_assignment`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `approval_step_id`
- `approver_role`
- `approver_user_id`
- `assignment_status`
- `assigned_at`
- `responded_at`
- `created_at`
- `updated_at`

### `decision_approval_action`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `approval_step_id`
- `actor_user_id`
- `action_type`
- `approval_status`
- `action_note`
- `action_payload`
- `acted_at`
- `created_at`
- `updated_at`

### `decision_approval_condition`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `approval_step_id`
- `condition_type`
- `condition_payload`
- `condition_status`
- `evaluated_at`
- `created_at`
- `updated_at`

### `decision_approval_escalation`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `approval_step_id`
- `escalation_type`
- `escalation_status`
- `escalated_to_role`
- `escalated_to_user_id`
- `escalated_at`
- `resolved_at`
- `created_at`
- `updated_at`

### `decision_approval_exception`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `decision_id`
- `exception_type`
- `exception_status`
- `requested_by`
- `resolved_by`
- `created_at`
- `updated_at`

### `decision_approval_override`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `decision_id`
- `override_type`
- `override_status`
- `override_reason`
- `requested_by`
- `approved_by`
- `created_at`
- `updated_at`

### `decision_approval_timeline`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `decision_id`
- `timeline_event_type`
- `timeline_payload`
- `created_at`

### `decision_approval_audit_log`
- `id`
- `tenant_id`
- `approval_workflow_id`
- `decision_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Approval Workflow
- Purpose: create approval workflow template or instance
- Method: `POST`
- Path: `/api/hdc/approvals/workflows`
- Inputs:
  - `decision_id`
  - `workflow_type`
  - `effective_decision_type`
- Outputs:
  - `approval_workflow_id`
  - `approval_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Bind Approval Workflow To Decision
- Purpose: attach resolved approval path to a decision packet
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/bind`
- Inputs:
  - `decision_id`
  - `committee_recommendation_id`
  - `comparison_snapshot_id`
- Outputs:
  - `binding_status`
  - `step_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Fetch Approval Workflow
- Purpose: return full workflow details and states
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}`
- Outputs:
  - `workflow_details`
  - `steps`
  - `current_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Approvers
  - Governance Reviewer

### Fetch Current Approval Step
- Purpose: return active step requiring action
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/current-step`
- Outputs:
  - `current_step`
  - `pending_approvers`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Approvers
  - Decision Owner

### Advance Approval Step
- Purpose: force workflow progression when conditions are satisfied
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/advance`
- Inputs:
  - `advance_reason`
- Outputs:
  - `next_step`
  - `approval_status`
- Permissions:
  - System
  - Governance Reviewer
  - Decision Owner where allowed

### Reassign Approver
- Purpose: reassign unavailable or invalid approver
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/reassign`
- Inputs:
  - `new_approver_user_id`
  - `reassign_reason`
- Outputs:
  - `assignment_status`
  - `new_approver`
- Permissions:
  - Hiring Manager
  - Governance Reviewer
  - Tenant Admin

### Fetch Pending Approvals
- Purpose: fetch current pending approval queue
- Method: `GET`
- Path: `/api/hdc/approvals/pending`
- Outputs:
  - `pending_approvals`
- Permissions:
  - Approvers
  - Governance Reviewer
  - Recruiter for own submissions

### Fetch Approval Timeline
- Purpose: view full approval chain and events
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/timeline`
- Outputs:
  - `timeline_events`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Approvers
  - Governance Reviewer

### Resolve Final Approval State
- Purpose: compute final workflow outcome
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/resolve`
- Inputs:
  - `resolution_reason`
- Outputs:
  - `final_approval_state`
  - `downstream_trigger_status`
- Permissions:
  - System
  - Governance Reviewer
  - Authorized final resolver

### Approve Decision
- Purpose: record approval action
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/approve`
- Inputs:
  - `approval_note`
- Outputs:
  - `step_status`
  - `approval_status`
- Permissions:
  - Assigned approver

### Reject Decision
- Purpose: reject current approval step
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/reject`
- Inputs:
  - `rejection_reason`
- Outputs:
  - `step_status`
  - `approval_status`
- Permissions:
  - Assigned approver

### Send Back For Revision
- Purpose: return decision packet for rework
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/revise`
- Inputs:
  - `revision_note`
- Outputs:
  - `revision_status`
  - `returned_to_role`
- Permissions:
  - Assigned approver

### Hold Approval
- Purpose: pause active approval pending more evidence or dependency
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/hold`
- Inputs:
  - `hold_reason`
- Outputs:
  - `step_status`
  - `hold_state`
- Permissions:
  - Assigned approver
  - Governance Reviewer

### Request More Evidence
- Purpose: request more evidence without immediate rejection
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/evidence-request`
- Inputs:
  - `evidence_request_note`
- Outputs:
  - `request_status`
- Permissions:
  - Assigned approver

### Escalate Approval
- Purpose: escalate stalled or high-risk step
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/escalate`
- Inputs:
  - `escalation_reason`
  - `target_role`
- Outputs:
  - `escalation_id`
  - `escalation_status`
- Permissions:
  - Assigned approver
  - Governance Reviewer
  - Tenant Admin

### Add Approval Notes
- Purpose: attach rationale or additional context
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/notes`
- Inputs:
  - `note_payload`
- Outputs:
  - `note_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Approvers
  - Governance Reviewer

### Record Conditional Approval
- Purpose: approve with conditions that must be fulfilled
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/steps/{approval_step_id}/conditional-approve`
- Inputs:
  - `condition_payload`
  - `approval_note`
- Outputs:
  - `condition_status`
  - `step_status`
- Permissions:
  - Assigned approver
  - Leadership Approver

### Request Exception
- Purpose: request exception to standard approval policy
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/exceptions`
- Inputs:
  - `exception_type`
  - `exception_reason`
- Outputs:
  - `exception_id`
  - `exception_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Decision Owner

### Approve Exception
- Purpose: approve exception request
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/exceptions/{exception_id}/approve`
- Inputs:
  - `approval_note`
- Outputs:
  - `exception_status`
- Permissions:
  - Governance Reviewer
  - Leadership Approver

### Reject Exception
- Purpose: reject exception request
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/exceptions/{exception_id}/reject`
- Inputs:
  - `rejection_reason`
- Outputs:
  - `exception_status`
- Permissions:
  - Governance Reviewer
  - Leadership Approver

### Request Override
- Purpose: request override of blocked or rejected path
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/overrides`
- Inputs:
  - `override_type`
  - `override_reason`
- Outputs:
  - `override_id`
  - `override_status`
- Permissions:
  - Decision Owner
  - Hiring Manager
  - Tenant Admin where allowed

### Approve Override
- Purpose: approve override request
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/overrides/{override_id}/approve`
- Inputs:
  - `approval_note`
- Outputs:
  - `override_status`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Tenant Admin where policy allows

### Reject Override
- Purpose: reject override request
- Method: `POST`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/overrides/{override_id}/reject`
- Inputs:
  - `rejection_reason`
- Outputs:
  - `override_status`
- Permissions:
  - Governance Reviewer
  - Leadership Approver

### Fetch Override History
- Purpose: inspect prior override decisions
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/overrides`
- Outputs:
  - `override_history`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

### Fetch Approval Audit Log
- Purpose: retrieve immutable approval audit trail
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

### Fetch Approval Status Summary
- Purpose: retrieve workflow summary
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/status`
- Outputs:
  - `approval_status_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Approvers
  - Governance Reviewer

### Fetch Stalled Approvals
- Purpose: retrieve SLA-breached or inactive approval steps
- Method: `GET`
- Path: `/api/hdc/approvals/stalled`
- Outputs:
  - `stalled_approvals`
- Permissions:
  - Governance Reviewer
  - Tenant Admin
  - Leadership Approver

### Fetch Escalation History
- Purpose: inspect approval escalation events
- Method: `GET`
- Path: `/api/hdc/approvals/workflows/{approval_workflow_id}/escalations`
- Outputs:
  - `escalation_history`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

## 4. UI Architecture

Frontend principles:
- clear approval stage tracker
- SLA and pending-time visibility
- escalation badges
- full evidence packet access
- clean enterprise approval workflow layout
- immutable audit visibility for authorized users
- no candidate access

### Recruiter UI

#### Pending Approval Dashboard
- submitted decisions
- pending stage status
- blocked items
- revision requests

#### Decision Submission Screen
- decision packet review
- committee recommendation attachment
- comparison snapshot attachment
- submit-for-approval action

#### Approval Chain Visibility
- stage-by-stage chain
- current approver
- conditional path indicators
- skipped-step indicators

#### Approval Blocker Tracker
- missing evidence
- stalled approvals
- rejected steps
- escalation state

#### Revision / Evidence Upload Screen
- respond to evidence request
- attach additional rationale
- resubmit revised packet

### Hiring Manager / Approver UI

#### Approval Inbox
- assigned approvals
- urgency badges
- SLA timers
- priority sorting

#### Candidate Decision Summary
- decision recommendation
- decision rationale
- score and evidence summary

#### Committee Recommendation View
- committee outcome
- dissent and escalation context
- committee timeline

#### Candidate Comparison Evidence View
- frozen comparison snapshot
- ranking rationale
- risk highlights

#### Approve / Reject / Revise Action Panel
- approve
- reject
- return for revision
- hold
- request more evidence

#### Conditional Approval Form
- set approval conditions
- set due conditions or dependent requirements

#### Notes / Rationale Section
- decision notes
- approval rationale
- policy exceptions

### Leadership / Governance UI

#### High-Risk Approval Queue
- executive and critical-role approvals
- compensation-triggered approvals
- policy-flagged decisions

#### Exception And Override Review Screen
- exception request details
- override rationale
- policy context
- approve/reject actions

#### Escalation Dashboard
- stalled approvals
- escalated items
- reassignment controls

#### Final Approval Resolution Screen
- full approval chain state
- final resolution summary
- downstream trigger readiness

#### Approval Audit Visibility
- immutable timeline
- override history
- exception history
- reopen/resend history

## 5. Execution Flow

1. Decision engine generates hiring decision recommendation
2. Committee and comparison outputs are attached as evidence
3. Decision is submitted into approval workflow
4. Approval Rule Engine resolves required path based on role, criticality, salary/band conditions, governance needs, and decision type
5. Current approver receives decision in approval inbox
6. Approver reviews evidence and acts
7. Workflow advances, pauses, escalates, or returns for revision
8. Exception or override path is used if standard path cannot resolve the decision
9. Final Approval Resolver marks approved, rejected, held, revised, or blocked outcome
10. Approved outcome triggers downstream offer, rejection, hold, or reconsideration process

## 6. Edge Cases

- Approver unavailable
  - reassignment or escalation path activates after SLA threshold
- Stale approval after decision data changes
  - step marked stale and approver must reconfirm on latest evidence
- Approval rejected after committee approved
  - committee state remains historical evidence while approval outcome controls downstream result
- Tie or conflicting parallel approvals
  - mandatory-resolution rule or higher-level escalation applies
- Exception approved but main approval still pending
  - exception does not finalize workflow; remaining mandatory steps still apply
- Override without sufficient permission
  - hard-blocked and logged to governance audit
- Decision revised mid-approval
  - current cycle closes as revised; new cycle starts with preserved audit lineage
- Escalated approval after original approver responds
  - first valid resolution path wins according to escalation policy; late responses become informational audit events
- Final decision approved but downstream offer flow fails
  - approval stays final, downstream trigger failure creates incident/retry path without invalidating approval
- Audit trail continuity across reopen / resend cycles
  - append-only timeline preserved under decision lineage and workflow version

## 7. Enterprise Features

- sequential and parallel approvals
- mandatory and advisory approval steps
- condition-based approval routing
- committee recommendation prerequisite support
- auto-skip for non-applicable steps
- escalation on inactivity or risk
- exception and override handling
- immutable approval timeline and audit
- downstream trigger control after final approval
- tenant-scoped workflow with candidate-global rule preserved

## 8. Integration Mapping

### Decision Engine
- Consumes:
  - recommendation payload
  - decision context
- Produces:
  - approval resolution
  - revision or rejection feedback
- Events:
  - `hdc.approval.workflow.created`
  - `hdc.approval.final.resolved`
- Downstream:
  - decision lineage update

### Hiring Committee Engine
- Consumes:
  - committee recommendation
  - dissent and escalation summary
- Produces:
  - approval evidence packet enrichment
- Events:
  - `hdc.approval.committee.evidence.attached`
- Downstream:
  - approver review surfaces

### Candidate Comparison Engine
- Consumes:
  - frozen comparison snapshot
  - recommendation summary
- Produces:
  - approval-ready comparison evidence
- Events:
  - `hdc.approval.comparison.snapshot.attached`
- Downstream:
  - conditional and final approval review

### Governance Layer
- Consumes:
  - override requests
  - exception requests
  - policy-triggered approval conditions
- Produces:
  - governance-required approval stages
  - policy block/warn states
- Events:
  - `hdc.approval.override.requested`
  - `hdc.approval.exception.requested`
- Downstream:
  - escalation and audit flows

### Audit Layer
- Consumes:
  - all workflow, step, escalation, exception, override, and resolution actions
- Produces:
  - immutable approval audit history
- Events:
  - `hdc.approval.audit.logged`
- Downstream:
  - compliance reporting
  - governance review

### Analytics Layer
- Consumes:
  - approval throughput
  - rejection rate
  - stall and escalation signals
- Produces:
  - approval performance metrics
  - bottleneck analytics
- Events:
  - `hdc.approval.metric.updated`
- Downstream:
  - HDC intelligence and operational dashboards

### Offer Management
- Consumes:
  - final approved decision outcome
  - effective decision type
- Produces:
  - offer workflow initiation or downstream disposition status
- Events:
  - `hdc.approval.approved.downstream.triggered`
- Downstream:
  - Offer Intelligence
  - rejection/hold processing

### Notification / Communication Layer
- Consumes:
  - assignment events
  - SLA breach events
  - revision and escalation events
- Produces:
  - approval notifications
  - reminders
  - escalation messages
- Events:
  - `hdc.approval.notification.required`
- Downstream:
  - approvers
  - decision owners
