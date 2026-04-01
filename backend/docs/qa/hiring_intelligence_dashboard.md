# QA: Hiring Intelligence Dashboard (HID)

## Overview
The Hiring Intelligence Dashboard (HID) serves as the central command center for leadership and recruiting teams, providing real-time data on hiring health, pipeline velocity, and team performance.

## Intelligence Sections

### 1. Hiring Overview
- **Active Jobs**: Total count of jobs currently in `active` status.
- **Open Positions**: Total headcount remaining to be fulfilled across active jobs.
- **Pipeline Volume**: Total count of non-concluded applications.
- **Interviews & Offers**: Real-time tracking of scheduled interviews and pending offers.
- **Monthly Velocity**: Cumulative hires for the current calendar month.

### 2. Job Health Intelligence
- **At-Risk Jobs**: Identifies jobs with no activity in 7 days or insufficient candidate volume.
- **Stuck Jobs**: Flagging requisitions that have been open for more than 60 days without fulfillment.

### 3. Pipeline Intelligence
- **Bottleneck Detection**: (In Development) Identifies stages where candidates spend more than 5 days on average.
- **Stalled Candidates**: Count of active applications with no updates in the last 5 days.

### 4. Performance Intelligence
- **Recruiter Metrics**: Aggregated shortlist rates, hire rates, and current workload.
- **Agency Metrics**: Comparison of submission quality and volume across agency partners.

## Access & RBAC
- **Visible To**: Super Admin, Tenant Admin, HR Manager, Hiring Manager, Recruiter.
- **Hidden From**: Candidate, Guest, External Evaluator.

## UI Navigation
- **Menu Location**: Intelligence -> Hiring Intelligence
- **Route**: `/hiring-intelligence` (mapped to `GET /api/analytics/hiring-intelligence/`)

## Test Scenarios
1. **RBAC Verification**: Attempt to access the dashboard as a `candidate` user and verify `403 Forbidden`.
2. **Monthly Hires Check**: Conclude a hire today and verify the "Hires This Month" counter increments.
3. **Risk Detection**: Create a job with 0 applications and verify it appears in the "At Risk" list after the threshold period.
4. **Data Consistency**: Cross-verify "Active Jobs" count with the Jobs module list.
