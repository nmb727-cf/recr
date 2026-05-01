# QA Test Case: Job Interview Binding

## Objective
Verify that an Interview Package can be bound to a Job Requisition with job-level overrides for round configuration and automation.

## Prerequisites
- Tenant exists.
- At least one Interview Package exists.
- A Job Requisition exists.

## Test Steps

### 1. Bind Interview Package to Job
- **Action**: Call `POST /interviews/jobs/requisitions/{job_id}/interview-binding/` with `package_id`.
- **Expected Result**: 
    - `InterviewPackageBinding` is created.
    - Default automation settings are applied.
    - Response contains `effective_rounds` matching the package rounds.

### 2. Override Round Configuration
- **Action**: Call `POST /interviews/jobs/requisitions/{job_id}/interview-binding/` with `rounds_override` containing modified round configurations (e.g., changed `threshold_score` or disabled `auto_pass_enabled`).
- **Expected Result**:
    - `InterviewPackageBinding.rounds_override` is updated.
    - `effective_rounds` in response shows the overridden values.

### 3. Global Automation Overrides
- **Action**: Call `PUT /interviews/jobs/requisitions/{job_id}/interview-binding/` with `automation_enabled: false`.
- **Expected Result**:
    - `automation_enabled` is updated to `false`.

### 4. UI: Job Setup Studio
- **Action**: Navigate to Job Setup Studio -> Interview Configuration.
- **Expected Result**:
    - Can select an interview package.
    - Can see a preview of rounds.
    - Can toggle automation and manual review settings (Verify these are saved to the backend).

### 5. UI: Job Command Center
- **Action**: Navigate to Job Command Center.
- **Expected Result**:
    - "Interview Automation" card shows the active package and round overview.
    - "Interview Intelligence" card shows real-time stats (Pending interviews, Candidates in interview stage).

## Automated Verification
- Run backend tests: `pytest apps/interviews/tests/test_job_binding.py` (To be created)
