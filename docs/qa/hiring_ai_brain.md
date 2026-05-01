# QA Document: Hiring AI Brain

## Overview
Hiring AI Brain provides a top-layer intelligence dashboard (`/hiring-ai`) orchestrating job, candidate, recruiter, and agency intelligence to provide actionable insights, mitigate risks, and recommend smart actions.

## Key Features
1. **Top-Level Dashboard**: `/hiring-ai` provides a bird's-eye view of active hiring metrics.
2. **Risk Detection**: Automated detection of bottlenecks and stalled candidates in the pipeline.
3. **Opportunities**: Identification of strategic improvements (e.g., engaging more agencies).
4. **Smart Actions**: AI-driven recommendations prioritized by impact.
5. **Job Orchestration**: Job-specific intelligence for stuck requisitions.

## Test Scenarios

### 1. View Dashboard
- **Scenario**: Navigate to `/hiring-ai` as a Hiring Manager or Admin.
- **Expected Result**: Dashboard renders successfully with 4 key metric cards: Actionable Insights, Critical Risks, Opportunities, and System Health Score. Smart Action Center, Active Risks, Opportunities, and Job Orchestration sections should populate accurately based on current tenant data.

### 2. Candidate Bottleneck Risk
- **Scenario**: Have 6+ candidates stuck in 'applied', 'screening', or 'interview' statuses without movement for 10+ days.
- **Expected Result**: "Active Risks" section displays "Candidate Bottleneck Detected" with high severity. "Smart Action Center" suggests clearing the pipeline.

### 3. Agency Network Opportunity
- **Scenario**: Active job count > 5, but connected active agencies < 2.
- **Expected Result**: "Opportunities" section displays "Expand Agency Network" highlighting the potential to reduce time-to-fill by ~15%.

### 4. Job Sourcing Recommendation
- **Scenario**: A job has been open for 7+ days with fewer than 3 applications.
- **Expected Result**: "Job Orchestration" lists the specific job title with suggestions to boost sourcing efforts or assign to a top-performing agency.

### 5. RBAC Enforcement
- **Scenario**: Login as a `candidate`. Navigate to `/hiring-ai`.
- **Expected Result**: System redirects to the Unauthorized view (or returns 403 API response), preventing access to the intelligence dashboard.

## Technical Implementation Details
- **Frontend**: `HiringAIBrainDashboard.tsx` fetches data from `/analytics/hiring-ai-brain/` and visualizes using responsive Ant Design components.
- **Backend**: `HiringAIBrainService` handles all aggregation logic.
- **Menu**: Accessible under Intelligence / Hiring AI Brain.
