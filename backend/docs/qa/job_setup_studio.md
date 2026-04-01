# QA: Job Setup Studio — System Parity Verification

## Overview
This document summarizes the audit and corrections made to ensure the Job Setup Studio (Wizard) is fully aligned with the backend system, Job Command Center, and downstream operational modules.

## System Parity Audit Summary

### 1. Information Step (Core Job Definition)
- **Status**: Aligned.
- **Fields Verified**: 
    - `title`, `job_ref_id` (auto-generated, immutable)
    - `department_id`, `department_name` (resolved)
    - `location_id`, `location_name` (resolved)
    - `job_category` (added to model)
    - `job_type` (Choices: Full Time, Part Time, Contract, Internship, Freelance)
    - `work_mode` (Choices: Onsite, Remote, Hybrid)
    - `experience_min/max`, `salary_min/max/currency/visible`
    - `headcount`, `priority`, `is_confidential`
    - `hiring_manager_id`, `hiring_manager_name` (added to model/serializer)
    - `recruiter_id`, `recruiter_name` (added to model/serializer)
    - `target_date`, `budget_code`
    - `description`, `requirements`, `responsibilities`, `skills_required` (JSON)

### 2. Hiring Ownership Step
- **Status**: Aligned.
- **Primary Roles**:
    - `job_owner_id`: Explicit ownership (overrides creator if set).
    - `hiring_manager_id`: Business-side owner.
    - `recruiter_id`: Primary recruiter.
- **Extended Roles**:
    - `backup_recruiter_id`: Coverage role.
    - `coordinator_id`, `coordinator_name` (added to model/serializer)
    - **Collaborative Team**:
    - `JobHiringTeamMember` model added to support multiple interviewers, approvers, and stakeholders.
    - **Ownership Hierarchy**:
    - `Job Owner -> Hiring Manager -> Recruiter -> Hiring Team` (implemented in `resolve_job_owner`).
    - **Automation Impact**:
    - Escalations and notifications target these roles based on `recipient_scope`.

    ### 3. Sourcing Step
    - **Status**: Aligned.
    - **Sourcing Modes**:
        - `sourcing_mode`: Supports `internal_only`, `external_only`, and `hybrid`.
        - `is_published_to_agencies`: Explicit visibility toggle for agency partners.
    - **Agency Governance**:
        - `agency_submission_governance`: Supports `direct`, `approval_required`, and `draft_only`.
    - **Agency Assignments**:
        - `AgencyJobAssignment` model verified for `deadline`, `max_submissions`, and `notes`.
    - **Downstream Behavior**:
        - Agency submission logic (`AgencySubmitCandidateView`) respects `max_submissions` and assignment status.

    ### 4. Pipeline / Workflow Step
    - **Status**: Aligned.
    - **Stage Zones**:
        - `stage_zone`: Supports `pre_submission`, `submitted`, `hiring_flow`, and `closed`.
        - Mapping is dynamic and defined at the stage level.
    - **Movement Rules**:
        - `movement_restriction`: Supports `open`, `job_owner_only`, `recruiter_only`, and `automation_only`.
        - Enforced during candidate stage transitions.
    - **SLA & Tracking**:
        - `is_critical_path`: Flag for core hiring stages.
        - `sla_target_hours`: Granular target for stage-specific response times.
        - `action_deadline_hours`: Hard deadline for escalation triggers.
        - **Automation Integration**:
        - `auto_actions`: Supports per-stage triggers for emails, interview scheduling, and rejections.

        ### 5. Interview Setup Step
        - **Status**: Aligned.
        - **Interview Package Binding**:
        - `InterviewPackageBinding` model used to link a job to a process template.
        - Supports `automation_enabled` toggle.
        - **Round Configuration**:
        - Defined within `InterviewPackage.rounds` (JSONField).
        - Supports multi-round logic (Round 1, Round 2, etc.).
        - **Interview Types**:
        - `INTERVIEW_TYPE_REGISTRY_DEFAULTS` includes 40+ types (AI, Technical, HR, Panel, etc.).
        - Execution modes: `native`, `manual`, `async`, `third_party`.
        - **Threshold Automation**:
        - `InterviewTemplate` supports `auto_shortlist_above` and `auto_reject_below`.
        - Integrated with `InterviewDecisionService.evaluate`.
        - **Evaluator Configuration**:
        - Roles: `lead`, `panelist`, `observer`, `note_taker`.
        - Weight-based decision logic supported.

        ### 6. Automation Setup Step
        - **Status**: Aligned.
        - **Recruiter Automation**:
        - `auto_assign_recruiter`: Master switch for automated internal routing.
        - `recruiter_assignment_policy`: Supports `round_robin`, `workload_balanced`, and `performance_based`.
        - **Agency Automation**:
        - `auto_distribute_to_agencies`: Automated job broadcast to partners.
        - `agency_distribution_policy`: Supports `all` and `performance_ranked`.
        - **Pipeline & Interview Automation**:
        - `auto_schedule_interviews`: Triggers scheduling engine upon stage entry.
        - `auto_match_candidates`: Enables AI matching brain for the requisition.
        - **SLA Automation**:
        - `sla_automation_enabled`: Controls whether overdue triggers and escalations are active for the job.
        - **Overrides**:
        - `override_workflow_mode`: Allows forcing `manual`, `semi_automated`, or `fully_automated` logic regardless of global defaults.

        ### 7. Offer / Closure Setup Step
        - **Status**: Aligned.
        - **Offer Defaults**:
        - `offer_salary_default`: Baseline salary for offer generation.
        - `offer_currency_default`: Standard currency for the role.
        - **Joining & Fulfillment**:
        - `auto_close_on_fulfillment`: Job automatically moves to `closed` when headcount is met.
        - **Agency Commercials**:
        - `agency_commission_model`: Supports `percentage`, `fixed`, and `inherited`.
        - `agency_commission_percentage` / `agency_commission_fixed_fee`: Job-specific commercial overrides.
        - `agency_payment_terms_days`: Default payment window for agency invoices.
        - **Downstream Behavior**:
        - `Placement` records in the pipeline inherit these commercial defaults.
        - `CommissionRecord` generation uses these values for automated billing/tracking.

        ### 8. Review & Launch Step
        - **Status**: Aligned.
        - **Validation Engine**:
        - `JobRequisitionReviewView` provides a unified readiness audit.
        - **Critical Errors**: Blocks publishing if Hiring Manager, Recruiter, or Description are missing.
        - **Warnings**: Flags missing pipeline stages, interview bindings, or inactive sourcing modes.
        - **Readiness Score**:
        - `Ready` (Green): No errors or warnings.
        - `Needs Attention` (Amber): No errors, but warnings exist.
        - `Incomplete` (Red): Critical errors present.
        - **Publish Behavior**:
        - `JobRequisitionPublishView` enforces readiness before creating the public `JobPosting`.
        - Supports publishing directly from `draft` (if permitted) or `approved` status.

        ### 9. Wizard Step Boundaries- **Step 1: Information**: Basic job details and hiring team.
- **Step 2: Content**: Description, requirements, and responsibilities.
- **Step 3: Sourcing**: Source mode, agency assignments (`AgencyJobAssignment` integration).
- **Step 4: Pipeline**: Custom stages (`JobStage` integration) and default templates.
- **Step 5: Automation**: Recruiter/Agency routing, auto-scheduling, and SLA controls.
- **Step 6: Review**: Final summary before submission/approval.

### 3. Save / Load / Edit Parity
- **Draft Support**: Jobs are created as `draft` by default. Partial saves are supported.
- **Edit Mode**: All fields are correctly loaded via `JobRequisitionSerializer` with resolved names for IDs.
- **Persistence**: Verified that all fields added to the model are included in the serializer's `fields` list.

### 4. Downstream Integrations
- **Job Command Center**: Uses `headcount`, `priority`, and `status` for intelligence scoring.
- **Intelligence (Hiring AI Brain)**: Uses `skills_required` and `experience` for candidate matching.
- **Automation Engine**: Uses `override_workflow_mode` and `auto_*` flags.
- **RBAC**: `to_representation` redacts sensitive fields (salary, budget code, internal owners) for external users.

## Mismatches Found & Corrected
1. **Missing Hiring Team**: Added `hiring_manager_id` and `recruiter_id` to `JobRequisition`.
2. **Missing Job Category**: Added `job_category` for better reporting and matching.
3. **Resolved Names**: Serializer now returns names for Dept, Location, and Users to avoid extra frontend lookups.
4. **Redaction Parity**: Ensured new internal fields are redacted for candidate-facing views.

## Test Scenarios
1. **Create Draft**: Start job creation, fill only title, save and verify it appears in draft list.
2. **Full Setup**: Complete all steps, verify all fields persist in backend.
3. **Edit Job**: Change hiring manager and priority, verify update reflects in Job Command Center.
4. **Confidential Job**: Set `is_confidential=True`, verify description is redacted for candidates.
5. **Automation Trigger**: Enable `auto_match_candidates`, verify intelligence service uses this flag.

## Deferred / Out of Scope
- **Custom Field UI**: The `CustomFieldDefinition` model exists, but dynamic rendering in the wizard is deferred to the next UI iteration.
- **Interview Package Selection**: Explicit selection of pre-defined interview packages is pending the completion of the `InterviewPackage` module.
