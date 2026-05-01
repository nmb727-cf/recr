# QA Document: Unified Operations View

## 1. Feature Overview
The Unified Operations View is the highest-level command center for the hiring ecosystem. it aggregates real-time signals from across all modules (Jobs, Pipeline, Teams, Agencies, Automation, and SLAs) into a single actionable dashboard.

## 2. Purpose
To enable hiring leadership and talent operations leads to monitor the health of the entire system, identify cross-module risks (e.g., a job at risk due to a weak agency and an overloaded recruiter), and execute recommended interventions.

## 3. Unified Operations Model
Signals are grouped into:
- **Executive Summary**: High-level load and health metrics.
- **Operational Module Health**: Traffic light indicators for Jobs, Pipeline, Team, Agencies, and Automation.
- **Cross-Module Risks**: Alerts that connect data from multiple entities (e.g., overloaded recruiters + high-priority jobs).
- **Team Workload**: Distribution of candidate load across recruiters.
- **Execution Health**: Automation success rates and recent failures.
- **Interview Flow**: Throughput monitoring for scheduled interviews and pending feedback.
- **Intervention Roadmap**: Actionable steps to resolve operational bottlenecks.

## 4. Cross-Module Relationships Surfaced
- **Team + Pipeline**: Identifies recruiters with excessive candidate volume.
- **Agency + Sourcing**: Highlights agencies with low conversion affecting top-of-funnel for active jobs.
- **SLA + Pipeline**: Detects stalled candidates where human intervention is overdue.
- **Job + Health**: Connects job priority with sourcing and processing speed.

## 5. Risk/Intervention Logic
- **High Risk**: Recruiters marked as 'overloaded' based on active candidate count.
- **Stalled Pipeline**: Candidates without movement for > 5 days in critical stages.
- **Weak Agency**: Partners with a performance score < 45.
- **Interventions**: Automated suggestions for reassignment, sourcing injections, or workflow adjustments.

## 6. UI Sections Added
- **Executive Summary Cards**: Active Hiring Load, Urgent Decisions, Pending Feedback, Operations Score.
- **Module Health Grid**: 5-column traffic light system.
- **Cross-Module Risk Alerts**: Cards with severity indicators, impact descriptions, and owner tags.
- **Team Workload Visual**: Balanced load bar chart.
- **Execution Health**: Circular progress for automation success and failed counts.
- **Interview Flow**: Real-time throughput counters.
- **Intervention Roadmap**: Grid of actionable next steps.

## 7. Menu / Route Access
- **Route**: `/unified-operations`
- **Sidebar**: Located under the **Intelligence** category as the primary dashboard.

## 8. Role Visibility Rules (RBAC)
- **Allowed Roles**: `super_admin`, `tenant_admin`, `hr_manager`, `hiring_manager`.
- **Denied Roles**: `recruiter` (restricted from global ops in some contexts, but allowed here for leads), `candidate`, `agency_user`.
- **Backend Enforcement**: Checked in `UnifiedOperationsView`.

## 9. Use Cases
- A Talent Ops Lead starting their week by reviewing the "Urgent Decisions" and "Stalled Candidates" to clear pipeline bottlenecks.
- An HR Manager identifying that two recruiters are overloaded while three are underutilized, triggering a reassignment intervention.
- Leadership monitoring the overall "Operations Score" to ensure system health targets are met.

## 10. Edge Cases
- **No Data**: Dashboard handles empty states gracefully with placeholders.
- **Missing Module Config**: If a module (like Agencies) has zero data, the traffic light shows 'Healthy' (or 'N/A' if appropriate, currently defaults to 'Healthy' if no weak items).
- **Timezone shifts**: Data timestamps are formatted relative to the user's local time.

## 11. Test Scenarios
1. **RBAC Validation**: Log in as a Candidate and navigate to `/unified-operations`. Verify 403 Forbidden.
2. **Signal Aggregation**: Move a candidate to a 'shortlisted' stage and wait for an SLA trigger. Verify the "Urgent Decisions" count increments.
3. **Risk Detection**: Intentionally overload a recruiter with 50+ candidates. Verify a "Recruiter Overloaded" risk alert appears.
4. **Intervention Action**: Verify that the "Intervention Roadmap" items appear when specific thresholds are met (e.g., at-risk jobs > 0).
5. **Real-time Sync**: Verify the "Last synced" timestamp updates on manual page refresh.
