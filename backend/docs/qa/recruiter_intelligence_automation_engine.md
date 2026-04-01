# QA: Recruiter Intelligence & Automation Engine

## 1. Feature Overview
The Recruiter Intelligence & Automation Engine provides real-time visibility into recruiter performance, workload balance, and candidate pipeline momentum. It acts as the foundation for smart, data-driven assignments by measuring empirical outcomes rather than just raw volume.

## 2. Purpose
To equip Talent Leads and Hiring Managers with actionable insights into team capacity. This prevents recruiter burnout, unblocks stalled pipelines, and ensures jobs are assigned to the individuals statistically most likely to close them quickly based on domain fit and current bandwidth.

## 3. Data Inputs Used
- **Jobs Assigned**: Real active `JobRequisition` counts owned by a recruiter.
- **Submissions & Conversions**: Aggregates from `Application` tracking shortlisted, interviewed, offered, and joined statuses.
- **Speed**: Heuristic approximations of time taken for a candidate to move from 'applied' to subsequent active states (`updated_at` - `created_at`).
- **Action Deadlines**: Count of overdue tasks tracked via the `ActionDeadline` model.

## 4. Scoring Logic
The Recruiter Performance Score (0-100) is a weighted metric:
- **Shortlist Rate (10%)**: Quality of initial screening.
- **Interview Rate (20%)**: Hiring Manager alignment.
- **Hire Rate (40%)**: Ultimate closing effectiveness.
- **Response Speed (20%)**: Time to first action, bounded.
- **Overdue Actions (10%)**: Penalty for dropped SLA balls.

## 5. Workload Logic
Workload status is categorized as:
- **Overloaded**: >60 active candidates OR >10 overdue actions.
- **Underutilized**: <15 active candidates.
- **Balanced**: Operating within the 15-60 candidate threshold with acceptable SLA adherence.
- **Risks Flagged**: >30% of active candidates stalled for more than 5 days, or high overdue action counts.

## 6. Assignment Recommendation Logic
Smart assignments blend historical performance with current capacity.
- **Domain Fit Bonus**: +15 points if the recruiter already owns jobs in the target requisition's department.
- **Capacity Adjustment**: Weighs the base performance score (50%) against remaining bandwidth (30%).
- **Avoidance Filters**: Automatically flags any overloaded recruiter as 'Avoid'.

## 7. UI Areas Added
- **Recruiter Intelligence Dashboard**: A dedicated mission-control page displaying team metrics, workload distribution, risk alerts, and assignment recommendations.
- **Job Command Center**: Integrated the `RecruiterIntelligenceSection` to provide job-specific recommendations and team capacity at a glance.
- **Pipeline Action Center**: Upgraded candidate cards on the `PipelineBoard` to include a distinct visual indicator (UserCheck icon) when explicitly owned by a recruiter.

## 8. Menu / Route Access
- **Menu Location**: Main Sidebar -> Intelligence -> Recruiter Intelligence (icon: TeamOutlined).
- **Route**: `/recruiter-intelligence` (mapped to `GET /api/analytics/recruiter-intelligence/`).

## 9. Role Visibility Rules
- **Backend Enforced**: Accessible strictly to `super_admin`, `tenant_admin`, `hr_manager`, and `hiring_manager`.
- **Frontend Protected**: Route explicitly guarded by `ProtectedRoute` specifying the exact permitted roles. Hidden entirely from `candidate` and external `agency` scopes.

## 10. Use Cases
1. A Talent Lead uses the dashboard to review which recruiters have capacity before distributing newly approved headcount.
2. A Hiring Manager checks the Job Command Center and clicks "Assign" based on the system's top recommended, non-overloaded recruiter.
3. An Admin spots a 'stalled pipeline' risk on the dashboard and reallocates a job to free up a bottleneck.

## 11. Edge Cases
- **No History**: New recruiters will default to a 0% conversion rate but benefit from maximum bandwidth scoring, encouraging early assignment.
- **No Available Recruiters**: The smart assignment engine safely degrades, explicitly noting "No available recruiters" while listing all team members under 'Avoid'.

## 12. Test Scenarios
1. **Load Testing**: Create a scenario where a recruiter hits 61 active candidates and verify their status flips to 'Overloaded' and they appear in the 'Avoid' list for new jobs.
2. **Scoring Logic**: Move a test candidate from `applied` to `joined` and confirm the specific recruiter's `hire_rate` and `overall_score` jump proportionally.
3. **RBAC Isolation**: Attempt to navigate directly to `/recruiter-intelligence` logged in as a candidate and ensure successful redirection/blocking by the `ProtectedRoute`.
4. **Pipeline UI Verification**: Assign a candidate to a specific recruiter and verify the small green `UserCheck` tooltip appears on the Pipeline Kanban card.
