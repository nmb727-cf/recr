# HDC-OFFER-INTELLIGENCE-06

## 1. System Architecture

Shared engine name: `OfferIntelligenceEngine`

Purpose:
- transform approved hiring decisions into intelligent offer recommendations
- combine decision signals, candidate expectations, internal compensation structures, approval policies, negotiation readiness, market positioning, and hiring urgency into structured offer guidance
- act as the intelligence layer before actual offer generation and release

System placement:
- Candidate Pipeline
- Interview Command Center
- Hiring Decision Command Center
  - Decision Engine
  - Hiring Committee Engine
  - Candidate Comparison Engine
  - Decision Approval Engine
  - Offer Intelligence Engine
- Offer Management / Compensation / Negotiation / Final Release

Core components:
1. `Offer Recommendation Engine`
2. `Compensation Intelligence Engine`
3. `Candidate Expectation Matching Engine`
4. `Internal Band Mapping Engine`
5. `Offer Risk Engine`
6. `Offer Competitiveness Engine`
7. `Offer Scenario Engine`
8. `Approval Dependency Engine`
9. `Negotiation Readiness Engine`
10. `Offer Audit & Intelligence Log Engine`

Supported intelligence modes:
- `standard_offer_recommendation`
- `aggressive_offer_recommendation`
- `market_aligned_offer_recommendation`
- `budget_capped_offer_recommendation`
- `urgent_hire_offer_mode`
- `executive_leadership_offer_mode`
- `bulk_hiring_offer_guidance_mode`
- `campus_fresher_offer_mode`
- `replacement_retention_sensitive_offer_mode`
- `exception_required_offer_mode`

Role architecture:
- Recruiter
- Hiring Manager
- Compensation Reviewer
- Finance Reviewer
- Business Head
- Leadership Approver
- Governance Reviewer
- Offer Owner

Operating model:
- offer intelligence starts only after final hiring decision is approved
- decision evidence, candidate expectation profile, band rules, market signals, and budget constraints are merged into an offer intelligence context
- recommendation output is structured, explainable, auditable, and approval-aware
- actual offer creation happens downstream in Offer Management or Compensation workflows
- candidate remains a global entity with tenant association only
- candidate never accesses offer intelligence authoring UI

Offer policy defaults:
- recruiter can review and propose scenario selection but cannot override governance-locked compensation rules by default
- market signal is advisory by default, but can become mandatory for policy-controlled roles or regions
- internal band exceedance is blocked or exception-gated depending on tenant compensation policy
- exception path is mandatory when compensation overflow breaches configured thresholds
- candidate expectation mismatch can warn or block based on severity and role criticality
- governance can lock compensation rules, scenario logic, and editability
- recommendation can be regenerated after decision change or expectation update, with full audit lineage preserved

Architecture layers:
- `Offer Context Layer`
- `Compensation & Expectation Layer`
- `Scenario & Recommendation Layer`
- `Risk & Competitiveness Layer`
- `Approval Dependency Layer`
- `Audit & Explainability Layer`

## 2. Database Design

Primary entities:
- `offer_intelligence_record`
- `offer_recommendation`
- `offer_compensation_band_match`
- `offer_expectation_profile`
- `offer_market_signal`
- `offer_risk_assessment`
- `offer_scenario_option`
- `offer_approval_dependency`
- `offer_negotiation_readiness`
- `offer_intelligence_audit_log`

Required fields across entities:
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_id`
- `recommended_ctc`
- `recommended_fixed_pay`
- `recommended_variable_pay`
- `recommended_bonus`
- `compensation_band_id`
- `band_fit_status`
- `candidate_expectation_min`
- `candidate_expectation_max`
- `market_position_status`
- `budget_fit_status`
- `risk_level`
- `scenario_type`
- `approval_dependency_status`
- `negotiation_readiness_status`
- `created_by`
- `created_at`
- `updated_at`

Recommended entity details:

### `offer_intelligence_record`
- `id`
- `tenant_id`
- `job_id`
- `candidate_id`
- `decision_id`
- `offer_intelligence_status`
- `intelligence_mode`
- `selected_scenario_id`
- `created_by`
- `created_at`
- `updated_at`

### `offer_recommendation`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `recommended_ctc`
- `recommended_fixed_pay`
- `recommended_variable_pay`
- `recommended_bonus`
- `recommendation_score`
- `recommendation_status`
- `generated_at`
- `created_at`
- `updated_at`

### `offer_compensation_band_match`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `compensation_band_id`
- `band_fit_status`
- `band_floor`
- `band_ceiling`
- `overflow_amount`
- `created_at`
- `updated_at`

### `offer_expectation_profile`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `candidate_expectation_min`
- `candidate_expectation_max`
- `expectation_source`
- `expectation_confidence`
- `created_at`
- `updated_at`

### `offer_market_signal`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `market_position_status`
- `market_signal_payload`
- `signal_staleness_status`
- `created_at`
- `updated_at`

### `offer_risk_assessment`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `risk_level`
- `risk_payload`
- `acceptance_probability_shell`
- `created_at`
- `updated_at`

### `offer_scenario_option`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `scenario_type`
- `scenario_payload`
- `scenario_rank`
- `scenario_score`
- `scenario_status`
- `created_at`
- `updated_at`

### `offer_approval_dependency`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `approval_dependency_status`
- `dependency_payload`
- `exception_required`
- `created_at`
- `updated_at`

### `offer_negotiation_readiness`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `negotiation_readiness_status`
- `readiness_payload`
- `created_at`
- `updated_at`

### `offer_intelligence_audit_log`
- `id`
- `tenant_id`
- `offer_intelligence_id`
- `decision_id`
- `event_type`
- `actor_user_id`
- `audit_payload`
- `created_at`

## 3. API Structure

### Create Offer Intelligence Context
- Purpose: initialize offer intelligence for an approved hiring decision
- Method: `POST`
- Path: `/api/hdc/offers/intelligence`
- Inputs:
  - `decision_id`
  - `job_id`
  - `candidate_id`
  - `intelligence_mode`
- Outputs:
  - `offer_intelligence_id`
  - `offer_intelligence_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Offer Owner

### Fetch Offer Intelligence Record
- Purpose: fetch context, state, and selected scenario
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}`
- Outputs:
  - `offer_intelligence_record`
  - `selected_scenario`
  - `status_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Finance Reviewer
  - Business Head
  - Leadership Approver
  - Governance Reviewer

### Generate Offer Recommendation
- Purpose: compute structured recommended offer
- Method: `POST`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/recommendation`
- Inputs:
  - `regeneration_reason`
  - `use_latest_expectation`
  - `use_latest_market_signal`
- Outputs:
  - `offer_recommendation`
  - `recommendation_rationale`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Offer Owner

### Fetch Compensation Band Match
- Purpose: inspect internal band fit and overflow state
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/band-match`
- Outputs:
  - `band_match`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Finance Reviewer
  - Governance Reviewer

### Fetch Market Competitiveness View
- Purpose: inspect market position and competitiveness indicators
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/market`
- Outputs:
  - `market_view`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Business Head
  - Leadership Approver

### Fetch Candidate Expectation Match
- Purpose: compare recommendation to candidate expectation range
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/expectation-match`
- Outputs:
  - `expectation_match`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Offer Owner

### Generate Offer Scenarios
- Purpose: create multiple recommendation scenarios
- Method: `POST`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/scenarios`
- Inputs:
  - `scenario_types`
  - `scenario_constraints`
- Outputs:
  - `scenario_options`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Business Head

### Compare Offer Scenarios
- Purpose: compare generated scenarios side by side
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/scenarios/compare`
- Outputs:
  - `scenario_comparison`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Finance Reviewer
  - Leadership Approver

### Fetch Negotiation Readiness
- Purpose: inspect negotiation risk and readiness state
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/negotiation-readiness`
- Outputs:
  - `negotiation_readiness`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Offer Owner
  - Compensation Reviewer

### Lock Recommended Scenario
- Purpose: select and lock scenario for downstream offer workflow
- Method: `POST`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/lock-scenario`
- Inputs:
  - `scenario_id`
  - `lock_reason`
- Outputs:
  - `selected_scenario`
  - `lock_status`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Offer Owner
  - Governance Reviewer if locked model applies

### Fetch Offer Approval Dependencies
- Purpose: fetch offer-side approval requirements
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/approval-dependencies`
- Outputs:
  - `approval_dependencies`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Finance Reviewer
  - Governance Reviewer

### Validate Offer Against Policy
- Purpose: validate recommendation against compensation and governance policy
- Method: `POST`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/validate-policy`
- Inputs:
  - `scenario_id`
- Outputs:
  - `policy_validation_result`
- Permissions:
  - Compensation Reviewer
  - Finance Reviewer
  - Governance Reviewer

### Flag Exception Requirement
- Purpose: create exception-required state for overflow or special cases
- Method: `POST`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/flag-exception`
- Inputs:
  - `exception_reason`
- Outputs:
  - `exception_status`
- Permissions:
  - Compensation Reviewer
  - Finance Reviewer
  - Governance Reviewer

### Route Offer For Approval
- Purpose: send selected scenario into downstream approval/offer flow
- Method: `POST`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/route-for-approval`
- Inputs:
  - `scenario_id`
  - `route_reason`
- Outputs:
  - `routing_status`
  - `downstream_workflow_id`
- Permissions:
  - Offer Owner
  - Compensation Reviewer
  - Recruiter where permitted

### Fetch Offer Readiness Summary
- Purpose: retrieve readiness summary for downstream offer creation
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/readiness`
- Outputs:
  - `offer_readiness_summary`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Finance Reviewer
  - Offer Owner

### Fetch Offer Intelligence Audit Trail
- Purpose: retrieve immutable intelligence actions
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/audit`
- Outputs:
  - `audit_events`
- Permissions:
  - Governance Reviewer
  - Leadership Approver
  - Authorized admins

### Fetch Recommendation Rationale
- Purpose: retrieve explainability for recommended scenario
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/rationale`
- Outputs:
  - `rationale_payload`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Leadership Approver

### Fetch Risk Explanation
- Purpose: retrieve offer risk explanation
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/risk`
- Outputs:
  - `risk_explanation`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Finance Reviewer
  - Governance Reviewer

### Fetch Scenario History
- Purpose: retrieve regenerated and locked scenario history
- Method: `GET`
- Path: `/api/hdc/offers/intelligence/{offer_intelligence_id}/scenario-history`
- Outputs:
  - `scenario_history`
- Permissions:
  - Recruiter
  - Hiring Manager
  - Compensation Reviewer
  - Governance Reviewer

## 4. UI Architecture

Frontend principles:
- structured recommendation cards
- scenario comparison table
- compensation breakdown visibility
- risk and competitiveness badges
- approval dependency warning panel
- rationale and explainability panel
- clean enterprise decision layout
- no candidate access

### Recruiter UI

#### Offer Intelligence Dashboard
- active offer intelligence queue
- status by candidate and role
- pending readiness issues

#### Candidate Expectation Summary
- expected range
- mismatch state
- source confidence

#### Offer Recommendation Screen
- recommended package
- fixed / variable / bonus split
- scenario selector

#### Scenario Comparison Panel
- compare standard, aggressive, market, and capped scenarios
- tie and risk indicators

#### Offer Risk Indicators
- acceptance risk
- approval risk
- expectation mismatch
- competitiveness risk

#### Approval Dependency Tracker
- extra approvals required
- exception flags
- policy blockers

### Hiring Manager / Business UI

#### Offer Recommendation View
- final recommended scenario
- decision rationale
- urgency impact

#### Budget Fit Summary
- budget fit state
- overflow amount
- business impact summary

#### Competitiveness Indicators
- market position state
- premium requirements
- risk-to-close signal

#### Offer Scenario Comparison
- scenario table
- role-criticality lens
- budget tradeoff view

#### Hiring Urgency Impact View
- urgency premium logic
- replacement sensitivity
- time-to-close considerations

### Compensation / Leadership UI

#### Compensation Intelligence View
- detailed compensation mix
- internal policy fit
- compensation rationale

#### Internal Band Mapping Panel
- band floor/ceiling
- overflow state
- exception threshold

#### Exception Flag Screen
- exception-required cases
- reason and impact
- governance lock state

#### Risk / Competitiveness Balance Screen
- risk versus market competitiveness
- approval burden
- acceptance probability shell

#### Approval Dependency Summary
- compensation and finance dependencies
- leadership dependency
- downstream approval routing

## 5. Execution Flow

1. Final hiring decision is approved
2. Offer intelligence context is created
3. Candidate expectation, role band, budget, urgency, and market inputs are loaded
4. Offer Recommendation Engine generates structured offer recommendation
5. Multiple scenarios are produced if configured
6. Risk, competitiveness, and negotiation readiness are calculated
7. User reviews recommendation and selects or refines scenario
8. Approval Dependency Engine validates policy and downstream approval path
9. Approved intelligence output passes to Offer Management or Compensation workflow
10. Audit trail and rationale are preserved

## 6. Edge Cases

- Candidate expectation missing
  - fallback uses policy defaults and marks recommendation confidence lower
- Budget unavailable
  - recommendation can compute with warning, but readiness blocks downstream release
- Compensation band mismatch
  - band overflow triggers warning, block, or exception path per policy
- High recommendation exceeds approval threshold
  - additional approval dependency added automatically
- Market data missing or stale
  - advisory output downgraded and risk explanation updated
- Urgent hire conflicts with budget cap
  - scenario engine produces capped and urgency-premium alternatives with explicit tradeoff
- Decision approved but job compensation structure changed
  - recommendation marked stale and regeneration required
- Multiple scenarios tie on recommendation score
  - explicit tie state shown; user or policy selects via secondary criteria
- Candidate already has competing offer flag
  - negotiation readiness and competitiveness risk escalate
- Recommendation locked but approval later rejects
  - locked scenario preserved in audit, readiness reopens for revision/regeneration
- Stale recommendation after candidate updates expectation
  - expectation mismatch invalidates readiness until recompute
- Audit continuity across recomputation cycles
  - every recomputation appends a new scenario/version lineage without overwriting prior state

## 7. Enterprise Features

- tenant-scoped offer intelligence contexts
- multiple recommendation modes and scenarios
- structured compensation mix support
- internal band validation and overflow logic
- candidate expectation matching
- market competitiveness guidance
- urgency and critical-role premium logic
- negotiation readiness output
- approval dependency and exception detection
- explainable, auditable offer recommendation history

## 8. Integration Mapping

### Decision Engine
- Consumes:
  - approved decision outcome
  - decision rationale
- Produces:
  - offer intelligence context
- Events:
  - `hdc.offer.intelligence.created`
- Downstream:
  - recommendation and scenario generation

### Hiring Committee Engine
- Consumes:
  - committee recommendation summary
  - dissent context if relevant
- Produces:
  - committee-derived offer sensitivity signals
- Events:
  - `hdc.offer.committee.context.attached`
- Downstream:
  - risk and scenario scoring

### Candidate Comparison Engine
- Consumes:
  - comparison snapshot
  - ranking rationale
- Produces:
  - offer competitiveness context
- Events:
  - `hdc.offer.comparison.context.attached`
- Downstream:
  - recommendation and approval readiness

### Decision Approval Engine
- Consumes:
  - final approved decision type
  - approval lineage
- Produces:
  - approved decision prerequisite state
- Events:
  - `hdc.offer.decision.approved`
- Downstream:
  - offer intelligence activation

### Compensation Engine
- Consumes:
  - compensation bands
  - salary structures
  - policy thresholds
- Produces:
  - band fit
  - comp mix guidance
- Events:
  - `hdc.offer.compensation.validated`
- Downstream:
  - scenario and approval dependency logic

### Approval Engine
- Consumes:
  - offer approval dependencies
  - selected scenario
- Produces:
  - downstream approval routing state
- Events:
  - `hdc.offer.routed.for.approval`
- Downstream:
  - compensation and release workflows

### Negotiation Engine
- Consumes:
  - negotiation readiness output
  - expectation mismatch
  - competing offer signals
- Produces:
  - negotiation starting context
- Events:
  - `hdc.offer.negotiation.readiness.generated`
- Downstream:
  - negotiation workflow

### Governance Layer
- Consumes:
  - locked rules
  - overflow cases
  - exception triggers
- Produces:
  - policy blocks
  - governance review requirements
- Events:
  - `hdc.offer.exception.required`
- Downstream:
  - approval and audit consumers

### Analytics Layer
- Consumes:
  - recommendation patterns
  - scenario selection trends
  - risk and competitiveness outcomes
- Produces:
  - offer intelligence metrics
  - acceptance trend analytics
- Events:
  - `hdc.offer.metric.updated`
- Downstream:
  - HDC intelligence layers

### Audit Layer
- Consumes:
  - all recommendation, selection, recompute, lock, and routing actions
- Produces:
  - immutable intelligence audit history
- Events:
  - `hdc.offer.audit.logged`
- Downstream:
  - governance and compliance reporting

### Offer Management
- Consumes:
  - selected locked scenario
  - readiness state
- Produces:
  - offer generation workflow initiation
- Events:
  - `hdc.offer.intelligence.ready.for.offer`
- Downstream:
  - offer authoring and release

### Notification / Communication Layer
- Consumes:
  - readiness changes
  - exception flags
  - approval dependency changes
- Produces:
  - routed notifications and reminders
- Events:
  - `hdc.offer.notification.required`
- Downstream:
  - recruiter, comp, finance, and leadership users
