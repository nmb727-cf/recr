# QA Document: Global Hiring Command Center

## 1. Overview
The Global Hiring Command Center (Mission Control) is the centralized orchestration layer for the entire recruitment organization. It aggregates high-level signals from all jobs, pipeline stages, SLA thresholds, and intelligence engines to provide a unified "Mission Control" view for Tenant Admins and Lead Recruiters.

## 2. Data Used
- **Jobs**: Aggregated counts of active, delayed, and near-completion requisitions.
- **Pipeline**: Global candidate volume, stalled lead detection, and interview backlog.
- **SLA Engine**: Global overdue action tracking and critical breach analysis.
- **AI Brain**: Synthesized recommendations based on multi-engine data aggregation.
- **Assignment Data**: Detection of unassigned jobs or overloaded recruiters.

## 3. Intelligence Blocks
- **Active Hiring Overview**: Quick-glance metrics on the state of the job catalog.
- **Global Pipeline Health**: Real-time distribution of candidates across the funnel.
- **SLA Engine Alerts**: High-priority section for managing process velocity and overdue tasks.
- **Risk Detection**: Automated flagging of delayed requisitions or high volumes of stalled leads.
- **Next Best Actions**: Operational directives for the team (e.g., "Address 10 overdue reviews").

## 4. Behavior
- **Tenant Isolation**: Data is strictly limited to the current tenant's global state.
- **Navigation**: Integrated as a top-level menu item ("Mission Control") for instant access.
- **Dynamic Refresh**: Metrics are calculated in real-time on page load to ensure accuracy.
- **Visual Urgency**: Uses a high-contrast theme (dark-mode blocks for actions) to drive recruiter focus.

## 5. Use Cases
- **Executive Review**: A Head of Talent opens Mission Control to check global hiring health and identify team-wide bottlenecks.
- **Task Prioritization**: A Lead Recruiter uses "Next Best Actions" to assign work to available recruiters.
- **Risk Mitigation**: The system flags "Delayed Requisitions" (> 30 days) for immediate review by hiring managers.

## 6. Edge Cases
- **Empty Tenant**: New accounts show baseline healthy signals with suggestions to create the first job.
- **Data Scaling**: Logic handles aggregation across hundreds of active jobs without significant performance degradation.
- **Permission Mapping**: Only accessible to administrative and recruiter roles; candidates and agencies see restricted or no access.

## 7. Test Scenarios
- **Scenario 1: Global Health Sync**
    - Action: Complete a hire in any job.
    - Expected: "Near Completion" count in Hiring Overview increments globally.
- **Scenario 2: SLA Breach Propagation**
    - Setup: Leave a candidate in "Applied" for > 48h in any job.
    - Expected: "Overdue Actions" count in the SLA block increases.
- **Scenario 3: Risk Detection (Delayed Job)**
    - Setup: Have an active job with `created_at` older than 30 days.
    - Expected: "Risk Detection" flags the delayed requisition.
- **Scenario 4: Navigation Flow**
    - Action: Click "Mission Control" from the top-level dropdown.
    - Expected: Redirects to `/hiring-command-center` and renders the global dashboard.
