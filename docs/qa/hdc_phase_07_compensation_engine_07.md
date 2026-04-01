# HDC-COMPENSATION-ENGINE-07

## 1. System Architecture

Shared engine name: `CompensationEngine`

Purpose:
- convert approved offer intelligence recommendations into structured, policy-safe, approval-ready compensation packages
- support compensation assembly across bands, grades, geographies, currencies, and special hiring scenarios
- act as the enterprise compensation structuring layer before negotiation and final offer release

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
  - Decision Engine
  - Hiring Committee Engine
  - Candidate Comparison Engine
  - Decision Approval Engine
  - Offer Intelligence Engine
  - Compensation Engine
- Negotiation Engine / Offer Release / Final Offer Workflow

Core components:
1. `Compensation Structure Engine`
2. `Salary Band Engine`
3. `Fixed / Variable Split Engine`
4. `Allowance & Benefit Engine`
5. `Bonus / Sign-on Engine`
6. `Geography / Policy Engine`
7. `Compensation Rule Validation Engine`
8. `Exception / Overflow Engine`
9. `Compensation Approval Dependency Engine`
10. `Compensation Audit Engine`

Supported compensation modes:
- `standard_full_time_compensation`
- `contract_freelance_compensation`
- `campus_fresher_compensation`
- `leadership_executive_compensation`
- `urgent_hire_compensation`
- `replacement_hire_compensation`
- `global_regional_compensation`
- `exception_based_compensation`
- `internal_transfer_aligned_compensation`
- `budget_capped_compensation`

Role architecture:
- Recruiter
- Hiring Manager
- Compensation Analyst
- HRBP / HR Manager
- Finance Reviewer
- Business Head
- Leadership Approver
- Governance Reviewer

Operating model:
- compensation package creation starts from a selected offer intelligence scenario
- compensation package is structured using role band, grade, geography, currency, policy, budget, and component rules
- package is validated continuously against policy and approval thresholds
- frozen package snapshots become the approval and negotiation source of truth
- candidate remains a global entity with tenant association only
- candidate never accesses compensation authoring UI

Policy defaults:
- recruiter can propose package changes only within allowed edit scope; high-impact changes require comp or HR ownership
- compensation analyst review is mandatory for policy-sensitive, exception-based, executive, or high-value packages
- finance review becomes mandatory over configured budget or component thresholds
- policy overflow blocks by default for hard caps and warns for soft thresholds
- band exceedance can be allowed only through exception mode with audit and approval dependency
- compensation structure locks after approval/freeze unless reopened by authorized rework workflow
- package recalculates when role, location, grade, band, currency, or approved scenario changes

Architecture layers:
- `Package Assembly Layer`
- `Band & Policy Layer`
- `Computation Layer`
- `Exception & Approval Dependency Layer`
- `Snapshot & Audit Layer`

## 2. Database Design

Primary entities:
- `compensation_package`
- `compensation_component`
- `compensation_band`
- `compensation_band_mapping`
- `compensation_rule`
- `compensation_exception`
- `compensation_adjustment`
- `compensation_approval_dependency`
- `compensation_policy_snapshot`
- `compensation_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `compensation_package_id`
- `band_id`
- `grade_id`
- `geo_policy_id`
- `currency_code`
- `base_pay`
- `fixed_pay`
- `variable_pay`
- `joining_bonus`
- `retention_bonus`
- `allowance_total`
- `benefit_total`
- `gross_total`
- `ctc_total`
- `policy_fit_status`
- `budget_fit_status`
- `exception_status`
- `approval_dependency_status`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `compensation_package`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `compensation_package_status`
- `band_id`
- `grade_id`
- `geo_policy_id`
- `currency_code`
- `base_pay`
- `fixed_pay`
- `variable_pay`
- `joining_bonus`
- `retention_bonus`
- `allowance_total`
- `benefit_total`
- `gross_total`
- `ctc_total`
- `policy_fit_status`
- `budget_fit_status`
- `selected_scenario_type`
- `created_by`
- `created_at`
- `updated_at`

### `compensation_component`
- `id`
- `tenant_id`
- `compensation_package_id`
- `component_type`
- `component_value`
- `component_currency`
- `component_status`
- `created_at`
- `updated_at`

### `compensation_band`
- `id`
- `tenant_id`
- `band_code`
- `grade_id`
- `geo_policy_id`
- `currency_code`
- `band_floor`
- `band_ceiling`
- `band_status`
- `created_at`
- `updated_at`

### `compensation_band_mapping`
- `id`
- `tenant_id`
- `job_id`
- `band_id`
- `grade_id`
- `mapping_status`
- `created_at`
- `updated_at`

### `compensation_rule`
- `id`
- `tenant_id`
- `geo_policy_id`
- `rule_type`
- `rule_payload`
- `rule_status`
- `created_at`
- `updated_at`

### `compensation_exception`
- `id`
- `tenant_id`
- `compensation_package_id`
- `exception_type`
- `exception_status`
- `exception_reason`
- `created_at`
- `updated_at`

### `compensation_adjustment`
- `id`
- `tenant_id`
- `compensation_package_id`
- `adjustment_type`
- `adjustment_payload`
- `created_at`
- `updated_at`

### `compensation_approval_dependency`
- `id`
- `tenant_id`
- `compensation_package_id`
- `approval_dependency_status`
- `dependency_payload`
- `created_at`
- `updated_at`

### `compensation_policy_snapshot`
- `id`
- `tenant_id`
- `compensation_package_id`
- `snapshot_payload`
- `snapshot_status`
- `created_at`
- `updated_at`

### `compensation_audit_log`
- `id`
- `tenant_id`
- `compensation_package_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Compensation Package
- Purpose: initialize compensation package from approved offer intelligence
- Method: `POST`
- Path: `/api/hdc/compensation/packages`
- Inputs:
  - `decision_id`
  - `offer_intelligence_id`
  - `scenario_id`
- Outputs:
  - `compensation_package_id`
  - `compensation_package_status`
- Permissions:
  - Recruiter
  - Compensation Analyst
  - Offer Owner

### Fetch Compensation Package
- Purpose: fetch full package and status
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}`
- Outputs:
  - `compensation_package`
  - `component_breakdown`
  - `validation_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - HRBP / HR Manager
  - Finance Reviewer
  - Business Head
  - Leadership Approver
  - Governance Reviewer

### Update Compensation Package
- Purpose: update editable package inputs
- Method: `PATCH`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}`
- Inputs:
  - `package_update_payload`
  - `change_reason`
- Outputs:
  - `updated_package`
  - `recomputed_totals`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager
  - Recruiter within allowed scope

### Generate Compensation Structure
- Purpose: generate structured package from scenario and policy
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/generate-structure`
- Inputs:
  - `generation_mode`
  - `use_latest_policy`
- Outputs:
  - `generated_structure`
  - `component_breakdown`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager

### Fetch Package Breakdown
- Purpose: fetch detailed component-wise package breakdown
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/breakdown`
- Outputs:
  - `breakdown`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - Finance Reviewer

### Clone Compensation Package
- Purpose: clone package for alternate scenario or revision cycle
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/clone`
- Inputs:
  - `clone_reason`
- Outputs:
  - `new_compensation_package_id`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager
  - Governance Reviewer where required

### Freeze Compensation Package Snapshot
- Purpose: freeze package for approval or negotiation
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/freeze`
- Inputs:
  - `freeze_reason`
- Outputs:
  - `snapshot_status`
  - `policy_snapshot_id`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager
  - Offer Owner
  - Governance Reviewer where policy requires

### Fetch Compensation Bands
- Purpose: fetch available compensation bands
- Method: `GET`
- Path: `/api/hdc/compensation/bands`
- Outputs:
  - `band_list`
- Permissions:
  - Recruiter
  - Compensation Analyst
  - HRBP / HR Manager
  - Finance Reviewer

### Fetch Band Mapping For Role
- Purpose: fetch mapped band for job/role
- Method: `GET`
- Path: `/api/hdc/compensation/bands/mapping`
- Inputs:
  - `job_id`
  - `geo_policy_id`
- Outputs:
  - `band_mapping`
- Permissions:
  - Recruiter
  - Compensation Analyst
  - HRBP / HR Manager

### Validate Package Against Band
- Purpose: validate package against mapped band
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/validate-band`
- Inputs:
  - `band_id`
- Outputs:
  - `band_validation_result`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager
  - Governance Reviewer

### Validate Package Against Policy
- Purpose: validate package against compensation policy rules
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/validate-policy`
- Outputs:
  - `policy_validation_result`
- Permissions:
  - Compensation Analyst
  - Finance Reviewer
  - Governance Reviewer

### Validate Package Against Budget
- Purpose: validate budget fit
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/validate-budget`
- Outputs:
  - `budget_validation_result`
- Permissions:
  - Compensation Analyst
  - Finance Reviewer
  - Business Head

### Fetch Policy Snapshot
- Purpose: retrieve frozen policy snapshot applied to package
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/policy-snapshot`
- Outputs:
  - `policy_snapshot`
- Permissions:
  - Compensation Analyst
  - Governance Reviewer
  - Leadership Approver

### Detect Compensation Exception
- Purpose: detect required exceptions
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/detect-exception`
- Outputs:
  - `exception_summary`
- Permissions:
  - Compensation Analyst
  - Governance Reviewer
  - Finance Reviewer

### Add Compensation Adjustment
- Purpose: add structured package adjustment
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/adjustments`
- Inputs:
  - `adjustment_type`
  - `adjustment_payload`
- Outputs:
  - `adjustment_status`
  - `recomputed_totals`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager

### Update Component Split
- Purpose: update fixed/variable split
- Method: `PATCH`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/components/split`
- Inputs:
  - `fixed_pay`
  - `variable_pay`
- Outputs:
  - `split_status`
  - `recomputed_totals`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager

### Update Allowance / Benefits
- Purpose: update allowance and benefits components
- Method: `PATCH`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/components/allowances-benefits`
- Inputs:
  - `allowance_payload`
  - `benefit_payload`
- Outputs:
  - `component_update_status`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager

### Add Joining Bonus
- Purpose: add joining bonus component
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/components/joining-bonus`
- Inputs:
  - `joining_bonus`
  - `bonus_reason`
- Outputs:
  - `bonus_status`
  - `approval_dependency_delta`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager

### Add Variable Component
- Purpose: add variable pay component
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/components/variable`
- Inputs:
  - `variable_component_payload`
- Outputs:
  - `variable_status`
  - `recomputed_totals`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager

### Recompute Package Totals
- Purpose: recompute package totals after changes
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/recompute`
- Outputs:
  - `gross_total`
  - `ctc_total`
  - `fit_statuses`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager
  - System

### Compare Package Versions
- Purpose: compare versions or clones of package
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/compare-versions`
- Outputs:
  - `version_comparison`
- Permissions:
  - Compensation Analyst
  - Finance Reviewer
  - Governance Reviewer

### Fetch Compensation Approval Dependencies
- Purpose: fetch required package-side approvals
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/approval-dependencies`
- Outputs:
  - `approval_dependencies`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - Finance Reviewer
  - Governance Reviewer

### Route Package For Approval
- Purpose: route package to approval engine
- Method: `POST`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/route-for-approval`
- Inputs:
  - `route_reason`
- Outputs:
  - `routing_status`
  - `approval_workflow_id`
- Permissions:
  - Compensation Analyst
  - HRBP / HR Manager
  - Offer Owner

### Fetch Compensation Readiness
- Purpose: fetch package readiness for downstream negotiation/release
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/readiness`
- Outputs:
  - `compensation_readiness`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - Finance Reviewer
  - Governance Reviewer

### Fetch Exception Approval Requirement
- Purpose: retrieve exception approval requirements
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/exception-approval`
- Outputs:
  - `exception_approval_requirement`
- Permissions:
  - Compensation Analyst
  - Governance Reviewer
  - Finance Reviewer

### Fetch Compensation Audit Trail
- Purpose: retrieve immutable compensation audit history
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

### Fetch Rule Validation Rationale
- Purpose: retrieve explainability for band/policy/budget validation
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/validation-rationale`
- Outputs:
  - `validation_rationale`
- Permissions:
  - Compensation Analyst
  - Finance Reviewer
  - Governance Reviewer

### Fetch Exception History
- Purpose: retrieve exception history for package
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/exceptions`
- Outputs:
  - `exception_history`
- Permissions:
  - Compensation Analyst
  - Governance Reviewer
  - Leadership Approver

### Fetch Frozen Package Snapshot
- Purpose: retrieve frozen package state
- Method: `GET`
- Path: `/api/hdc/compensation/packages/{compensation_package_id}/snapshot`
- Outputs:
  - `frozen_snapshot`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Analyst
  - Finance Reviewer
  - Governance Reviewer

## 4. UI Architecture

Frontend principles:
- structured compensation breakdown
- component-wise editable table
- gross and CTC summary cards
- budget and policy badges
- approval dependency warning panel
- frozen snapshot visibility
- clean enterprise approval-ready layout
- no candidate access

### Recruiter UI

#### Compensation Package Dashboard
- active package queue
- linked offer state
- readiness state
- pending exceptions

#### Offer-Linked Compensation Screen
- selected offer scenario
- high-level compensation package
- lock and freeze visibility

#### Package Summary Card
- base/fixed/variable totals
- joining bonus
- total CTC

#### Policy / Budget Fit Warnings
- band mismatch
- budget overflow
- exception required

#### Exception Tracker
- package-level exception status
- approval dependency visibility

### Hiring Manager UI

#### Compensation Summary View
- final recommended structure
- component overview
- readiness state

#### Budget Impact Panel
- role budget impact
- overflow amount
- urgency premium impact

#### Scenario Comparison View
- compare package versions
- cost tradeoffs
- business impact

#### Compensation Readiness View
- ready for approval
- ready for negotiation
- blocked by policy or exception

### Compensation / Finance UI

#### Detailed Package Builder
- package components editor
- editable split controls
- version compare access

#### Component Breakdown Editor
- base, fixed, variable, bonus, allowance, benefit components
- line-item edit state

#### Band Validation Screen
- band floor/ceiling
- overflow state
- grade mapping visibility

#### Geo / Policy Mapping Screen
- location-specific rules
- currency view
- policy snapshot view

#### Exception Review Panel
- exception reason
- threshold breach
- required approvals

#### Approval Dependency Summary
- who must approve
- why approval is required
- readiness to route

### Leadership / Governance UI

#### High-Value Compensation Approval Queue
- high-value and exception packages
- executive packages
- regional overflow cases

#### Policy Overflow Dashboard
- packages breaching caps/floors
- hard-block and soft-warning states

#### Exception Approval Screen
- exception details
- policy rationale
- approve/reject actions

#### Compensation Audit Trail
- edit history
- freeze history
- version lineage
- approval dependency history

## 5. Execution Flow

1. Approved hiring decision flows into offer intelligence
2. Compensation engine receives selected recommended scenario
3. Internal bands, budget, geography, currency, and policy data are loaded
4. Compensation structure is generated
5. Package totals and component splits are computed
6. Policy, band, and budget validation run
7. Exceptions and approval dependencies are identified
8. User refines or confirms package within permitted edit scope
9. Package snapshot is frozen for approval or negotiation
10. Final structured package passes to negotiation or offer release workflows

## 6. Edge Cases

- Missing compensation band
  - package cannot finalize; band mapping resolution or exception path required
- Job band changed after decision approval
  - package marked stale and recomputation required
- Currency conversion unavailable
  - package generation pauses or falls back to base currency with warning per policy
- Package exceeds budget but within market suggestion
  - budget exception or additional approval required
- High joining bonus requires extra approval
  - approval dependency added automatically
- Package valid earlier but invalid after policy update
  - frozen snapshot remains historical; live package marked out-of-policy and requires review
- Compensation component removed after snapshot freeze
  - frozen package preserved; new edit cycle creates new version
- Contract compensation mapped to full-time structure incorrectly
  - hard validation block on compensation mode mismatch
- Stale package after offer intelligence recomputation
  - package marked stale until regenerated or explicitly reconciled
- Multiple package versions in approval simultaneously
  - only one active approval-eligible version allowed by default; others remain draft or superseded
- Approved package later rejected in final approval
  - package stays frozen and auditable, but downstream state reopens for revision
- Audit continuity across edits, freeze, and rework cycles
  - append-only audit and version lineage retained

## 7. Enterprise Features

- tenant-scoped compensation packages
- multiple compensation modes
- band, grade, geo, and currency-aware structuring
- fixed/variable/bonus/allowance/benefit composition
- policy, band, and budget validation
- exception and overflow handling
- approval dependency detection
- frozen snapshot and version comparison
- role-based package editing
- auditable compensation lifecycle

## 8. Integration Mapping

### Offer Intelligence Engine
- Consumes:
  - selected scenario
  - recommendation rationale
  - expectation and competitiveness context
- Produces:
  - structured compensation package
- Events:
  - `hdc.compensation.package.created`
- Downstream:
  - approval and negotiation preparation

### Decision Engine
- Consumes:
  - final approved decision type
  - job and candidate context
- Produces:
  - decision linkage for compensation package
- Events:
  - `hdc.compensation.decision.context.linked`
- Downstream:
  - package traceability

### Decision Approval Engine
- Consumes:
  - approval lineage
  - final decision approval state
- Produces:
  - prerequisite clearance for compensation routing
- Events:
  - `hdc.compensation.decision.approval.confirmed`
- Downstream:
  - compensation readiness

### Negotiation Engine
- Consumes:
  - frozen compensation package
  - editable negotiation bounds where allowed
- Produces:
  - negotiation context
- Events:
  - `hdc.compensation.ready.for.negotiation`
- Downstream:
  - negotiation workflows

### Offer Management
- Consumes:
  - approved or negotiation-finalized compensation package
- Produces:
  - offer creation input
- Events:
  - `hdc.compensation.ready.for.offer.release`
- Downstream:
  - final offer workflow

### Governance Layer
- Consumes:
  - policy overflow, exceptions, freezes, edits
- Produces:
  - governance block/warn states
  - exception approval requirements
- Events:
  - `hdc.compensation.exception.required`
- Downstream:
  - approval and audit flows

### Approval Engine
- Consumes:
  - compensation approval dependencies
  - frozen package snapshot
- Produces:
  - approval workflow binding
- Events:
  - `hdc.compensation.routed.for.approval`
- Downstream:
  - package approvals

### Analytics Layer
- Consumes:
  - package patterns
  - exception rates
  - budget overflow metrics
- Produces:
  - comp intelligence metrics
  - approval bottleneck signals
- Events:
  - `hdc.compensation.metric.updated`
- Downstream:
  - HDC intelligence and operations

### Audit Layer
- Consumes:
  - all edits, validations, freeze events, version changes, exception actions
- Produces:
  - immutable compensation audit trail
- Events:
  - `hdc.compensation.audit.logged`
- Downstream:
  - compliance and governance review

### Notification / Communication Layer
- Consumes:
  - exception states
  - approval dependency states
  - stale package signals
- Produces:
  - routed notifications
  - reminders
- Events:
  - `hdc.compensation.notification.required`
- Downstream:
  - recruiter, comp, finance, governance users
