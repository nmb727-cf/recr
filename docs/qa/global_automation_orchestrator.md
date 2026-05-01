# QA Document: Global Automation Orchestrator

## 1. Feature Overview
The Global Automation Orchestrator is the central cross-module execution and monitoring layer for the enterprise hiring ecosystem. It aggregates automation data from Jobs, Interviews, Pipelines, SLAs, and AI-driven recommendations.

## 2. Purpose
To provide administrators, hiring managers, and HR leaders with a single pane of glass into all autonomous actions happening within the system. It clarifies what is automated vs. manual, highlights pipeline risks, and tracks system health via execution success rates.

## 3. Automation Categories Covered
- **Job Automation Engine**: Status transitions and stage movements.
- **Pipeline Decision Engine**: Auto-shortlist, auto-reject, and interview progression.
- **Interview Automation**: Auto-scheduling, panel assignment, and reminder notifications.
- **SLA Engine**: Time-to-action deadlines and escalations.
- **Hiring AI Brain**: High-level orchestrator actions.

## 4. Inventory Model
The **Automation Registry** tab lists all configured `AutomationRule` objects across the tenant. 
- Displays trigger event (e.g., `application.submitted`, `interview.completed`).
- Shows active/inactive status.
- Displays the number of actions configured per rule.
- Tracks lifetime execution count and last executed timestamp.

## 5. Execution Visibility Model
The **Execution Logs** tab displays recent `AutomationLog` entries.
- Displays execution status (Success, Failed, Skipped).
- Identifies the target entity (e.g., Application ID, Job ID).
- Shows execution timestamp and error details if any.

## 6. Failed/Blocked Automation Handling
- The dashboard highlights a **Failed Executions** metric.
- A dedicated **Blocked / Failed Automations** card lists recent errors, allowing ops teams to quickly identify misconfigurations (e.g., missing email templates, deleted interviewers).

## 7. UI Sections Added
- **Overview Metrics**: Active Rules, Execution Success Rate, Failed Executions, Manual Reviews.
- **Coverage & Health**: Progress bars showing the percentage of active jobs with automation and SLA tracking enabled.
- **Blocked/Failed Card**: Immediate visibility into recent automation failures.
- **Detailed Tabs**:
  - **Automation Registry**: Full inventory.
  - **Execution Logs**: Operational activity.
  - **Manual Review Queue**: Inbox for overdue SLA items (ActionDeadlines).

## 8. Menu / Route Access
- **Menu Route**: `/automation-orchestrator`
- **Sidebar Placement**: Added under `Intelligence -> Automation Orchestrator` in the main navigation menu.

## 9. Role Visibility Rules (RBAC)
- **Allowed Roles**: `super_admin`, `tenant_admin`, `hr_manager`, `hiring_manager`, `recruiter`.
- **Denied Roles**: `candidate`, `agency_owner`, `agency_admin`, `agency_recruiter`, and unauthenticated users.

## 10. Use Cases
- A Recruiter Manager checking why candidates aren't receiving auto-reject emails (can view failed execution logs).
- A Hiring Manager confirming that SLA reminders are enabled for their newly created requisition (via Coverage card).
- An Admin auditing all active rules in the system.

## 11. Edge Cases
- No active jobs (Coverage safely returns 0% rather than dividing by zero).
- No automation logs yet (Dashboard displays Empty state placeholders cleanly).
- Missing entity references (Logs handle deleted or missing entity IDs gracefully).

## 12. Test Scenarios
1. **RBAC Test**: Attempt to access `/automation-orchestrator` as a Candidate. Verify redirection or 403 Forbidden error.
2. **Dashboard Load**: Access as an Admin. Verify the page loads without 500 errors and all 4 overview metric cards populate.
3. **Execution Tracking**: Trigger an automation (e.g., move candidate stage). Refresh the Orchestrator. Verify the execution appears in the "Execution Logs" tab.
4. **Failure Tracking**: Intentionally configure an invalid automation rule. Trigger it. Verify the failure appears in the "Blocked / Failed Automations" card and the Execution Logs tab.
5. **Coverage Metrics**: Create a new Job Requisition with `automation_enabled = False`. Verify the "Job Automation Coverage" percentage adjusts accordingly.
