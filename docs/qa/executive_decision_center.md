# QA Document: Executive Decision Center

## 1. Feature Overview
The Executive Decision Center is a top-level leadership module designed for Head of Talent, VPs, and Executive teams. It provides a strategic, decision-focused view of critical hiring priorities, bottlenecks, team performance, and actionable executive interventions, cutting out operational noise.

## 2. Purpose
To enable executives to immediately see where the hiring engine is failing, which business-critical jobs are at risk, which teams or agencies need support or rebalancing, and to highlight exact decisions that are blocked.

## 3. Executive Decision Model
The center is structured into specific decision areas:
- **Executive Summary Cards**: Instant high-level read on critical roles open, total open headcount, bottlenecked decisions, and hiring velocity.
- **Business-Critical Hiring**: High-priority and urgent jobs tracked by days open and fill rate to flag roles that are "At Risk" or "Critical".
- **Decision Bottlenecks**: SLA violations and stalled candidate approvals explicitly surfacing the "Owner" and "Age" to drive accountability.
- **Team Capacity**: Macro view of overloaded vs. underutilized recruiters, surfacing the top contributors handling the active candidate load.
- **Agency Strategy**: Identifies the overall source mix health, top-performing agency partners, and underperforming partners that require relationship review.
- **Executive Interventions**: Auto-generated strategic recommendations such as workload rebalancing, widening distribution for aging roles, or enforcing SLA workflows.

## 4. Data Inputs Used
- **Jobs Engine**: Job Requisitions (status, priority, headcount, created_at).
- **Pipeline Engine**: Applications and Stage Histories (days in stage, joined status).
- **SLA Engine**: Action Deadlines (overdue tasks, missing feedbacks).
- **Recruiter & Agency Intelligence**: Load balancing states and performance scores.

## 5. Risk / Bottleneck / Recommendation Logic
- **Job Risk State**: A high-priority job is marked "Critical" if it has 0 pipeline candidates. It is marked "At Risk" if it has been open > 30 days and filled < headcount.
- **Decision Bottleneck**: Any SLA deadline currently overdue or candidate stalled in pipeline > 5 days.
- **Intervention - Rebalance**: Triggered if any recruiter has a workload status of "overloaded".
- **Intervention - Sourcing**: Triggered if any critical job has been open > 45 days.
- **Intervention - Partnership**: Triggered if any agency falls below a performance score of 45.

## 6. UI Sections Added
- **Top Bar**: Live status indicator, Last Synced timestamp, and a Quick Navigation row.
- **Summary Cards**: 4 key executive metrics with trend indicators.
- **Critical Path Column**: Business-Critical Hiring list and Decision Bottleneck list.
- **Capacity & Strategy Column**: Executive Interventions, Team Capacity breakdown, and Agency Strategy review.

## 7. Menu / Route Access
- **Route**: `/executive-decision`
- **Sidebar**: The top-most link in the "Intelligence" group.
- **Quick Links**: Available from within the page to navigate quickly to the Unified Operations, AI Brain, Global Orchestrator, and Hiring Intelligence.

## 8. Role Visibility Rules (RBAC)
- **Allowed Roles**: `super_admin`, `tenant_admin`, `hr_manager`.
- **Denied Roles**: `recruiter`, `hiring_manager` (unless specifically granted extended executive view depending on tenant config), `candidate`, `agency_user`.
- **Backend Enforcement**: Verified via the `ExecutiveDecisionView` endpoint permissions.

## 9. Use Cases
- A VP of Talent logging in on Monday morning to see exactly which high-priority roles are stalled and who is blocking them.
- A CHRO checking if the recruitment team has enough capacity for an upcoming hiring sprint or if external agencies need to be engaged.
- An Executive reviewing whether a specific department head is bottlenecking the pipeline by sitting on candidate feedback.

## 10. Edge Cases
- **No Critical Roles**: The "Business-Critical Hiring" section displays an empty state cleanly instead of breaking.
- **No Bottlenecks**: The "Decision Bottlenecks" section highlights "No Blockers Detected" with a positive status message.
- **Zero SLA Rules Configured**: Safe fallback, displaying 0 bottlenecks.

## 11. Test Scenarios
1. **RBAC Validation**: Log in as a Recruiter and navigate to `/executive-decision`. Ensure the system redirects or returns 403.
2. **Dashboard Load**: Log in as `tenant_admin` and load the page. Verify the 4 summary cards and all sections render correctly without 500 errors.
3. **Risk Detection**: Create a high-priority job with 0 applications. Verify it appears in "Business-Critical Hiring" with a "Critical" tag.
4. **Bottleneck Surfacing**: Create an overdue ActionDeadline for a specific Hiring Manager. Verify it appears under "Decision Bottlenecks" showing the Manager's name as the Owner.
5. **Quick Navigation**: Click the "Unified Operations" quick link at the top of the dashboard and ensure it navigates correctly.
