# QA Document: Global Talent Control Tower

## 1. Feature Overview
The Global Talent Control Tower is the apex monitoring and command layer of the Talent Operating System. It aggregates real-time signals from every module—Jobs, Pipeline, Teams, Agencies, Automation, and AI—to provide a single, unified view of the entire hiring system's health and performance.

## 2. Purpose
To serve as the primary cockpit for Talent Leaders, VPs, and Admins to monitor global hiring system integrity, detect cross-module bottlenecks, and receive high-level strategic recommendations without diving into granular operational logs.

## 3. Control Tower Model
The tower is organized into six critical operational zones:
- **Global System Health**: Real-time counters for Active Jobs, Headcount, Pipeline Load, Scheduled Interviews, Pending Offers, and Monthly Hires.
- **Pipeline Integrity**: Detects high-risk jobs (e.g., aging roles with low volume) and provides an overall health score.
- **Team Throughput**: Macro view of recruiter capacity, highlighting overloaded team members and pending Hiring Manager reviews.
- **Sourcing Ecosystem**: Monitors active agency partners, identifies sourcing gaps (jobs with 0 candidates), and surfaces top-performing partners.
- **Process Autonomy**: High-level health of the automation engine, showing success rates vs. failed runs and blocked actions.
- **Neural Recommendations**: Strategic AI insights pulled from the Hiring AI Brain, including smart actions, critical opportunities, and system risks.

## 4. Data Inputs
- **Jobs**: `JobRequisition` (status, headcount, creation date).
- **Candidates/Pipeline**: `Application` (status distribution, joined dates).
- **Interviews**: `Interview` (scheduled counts).
- **Team**: `RecruiterIntelligenceService` (workload status, active candidates).
- **Source**: `AgencyPerformanceScore` (scores, hires).
- **Automation**: `AutomationLog`, `ActionDeadline` (success rates, failures, escalations).
- **AI**: `HiringAIBrainService` (generated insights).

## 5. UI Sections
- **Executive Summary Grid**: 6 metric cards with color-coded context.
- **Pipeline Integrity Card**: Risk alerts and health scoring.
- **Team Throughput Card**: Capacity progress bar and bottleneck counters.
- **Sourcing Ecosystem Card**: Partner stats and top agency leaderboard.
- **Process Autonomy Card**: Automation success rate visualization.
- **Neural Recommendations Panel**: Actionable smart action cards and system risks.

## 6. Menu / Route Access
- **Route**: `/control-tower`
- **Sidebar**: The absolute top item in the **Intelligence** category.

## 7. Role Visibility Rules (RBAC)
- **Allowed Roles**: `super_admin`, `tenant_admin`, `hr_manager`.
- **Restricted**: Hidden and API-blocked from `recruiter`, `hiring_manager` (standard), `candidate`, and `agency_user`.
- **Backend Enforcement**: Verified in `GlobalControlTowerView`.

## 8. Test Scenarios
1. **RBAC Check**: Log in as a standard Recruiter. Attempt to access `/control-tower`. Verify a 403 Forbidden or redirection to dashboard.
2. **Global Counters**: Verify that "Active Jobs" matches the total count of jobs in 'active' status.
3. **Pipeline Risk**: Create a high-priority job and leave it without applications for 15 days. Verify it appears in the "Pipeline Integrity" risk list.
4. **Automation Success**: Trigger a successful automation rule. Refresh the Control Tower. Verify the "Automation Success Rate" remains high or increases.
5. **AI Sync**: Ensure the "Neural Recommendations" section displays the same smart actions as the Hiring AI Brain dashboard.
6. **Data Integrity**: Verify the "Last Refresh" timestamp updates correctly on each page load.
