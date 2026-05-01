# QA Document: Agency Intelligence + Distribution Engine

## Overview
The Agency Intelligence + Distribution Engine provides data-driven insights into agency performance and automates the distribution of job requisitions based on historical success and intelligent balancing.

## Key Features
1. **Agency Performance Scoring**: Automated calculation of metrics including submission volume, shortlist rate, hire rate, and response time.
2. **Intelligent Distribution**: Automated job assignment to agencies based on their performance scores and current workload.
3. **Agency Risk Detection**: Identification of weak or inactive agencies.
4. **Job-Level Intelligence**: Real-time recommendations and performance data within the Job Command Center.
5. **Dashboard**: Comprehensive overview of the agency ecosystem.

## Test Scenarios

### 1. Performance Calculation
- **Scenario**: Agency submits a candidate.
- **Expected Result**: `AgencyPerformanceScore` is updated (via background task) to reflect the new submission. Shortlist rate and other metrics are recalculated.

### 2. Intelligent Distribution (Automated)
- **Scenario**: Create a new job with `auto_distribute_to_agencies` enabled and policy set to `performance_ranked`. Publish the job.
- **Expected Result**: The system automatically assigns the job to the top-performing agencies (score > 60) and creates `AgencyJobAssignment` records.

### 3. Manual Backfill Assignment
- **Scenario**: Select agencies manually in Step 3 (Sourcing) of Job Setup Studio. Publish the job.
- **Expected Result**: The system creates `AgencyJobAssignment` records for all manually selected agencies.

### 4. Job Command Center Intelligence
- **Scenario**: Open a specific job in the Jobs Hub.
- **Expected Result**: The "Agency Intelligence" section shows assigned agency performance, recommended agencies, and any underperforming/inactive agency alerts.

### 5. Agency Intelligence Dashboard
- **Scenario**: Navigate to `/agency-intelligence`.
- **Expected Result**: Dashboard displays:
    - Overview stats (Connected, Active, Submissions, Hires, Weak, Avg Score).
    - Performance table with all agencies.
    - Distribution recommendations and load balancing status.
    - Risk alerts.
    - Comparison metrics.
    - Pipeline contribution analysis.

### 6. RBAC Verification
- **Scenario**: Access `/agency-intelligence` as a Recruiter or Candidate.
- **Expected Result**: Access denied (403 or redirect to unauthorized). Access should only be allowed for Admin, Hiring Manager, and HR Manager roles.

## Technical Implementation Details
- **Service**: `AgencyIntelligenceService` handles all logic.
- **Signals**: `on_job_published_agency_distribution`, `on_agency_candidate_submitted_refresh`, `on_application_stage_changed_refresh`.
- **Tasks**: `refresh_agency_performance_scores_task` handles heavy calculations asynchronously.
- **UI Components**: `AgencyIntelligenceDashboard`, `AgencyIntelligenceSection` (Job level), `Assign Agencies` modal.
