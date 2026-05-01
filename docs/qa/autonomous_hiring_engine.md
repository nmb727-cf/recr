# QA Document: Autonomous Hiring Engine

## 1. Feature Overview
The Autonomous Hiring Engine is the human-in-the-loop control layer for AI-driven hiring decisions. It sits above the Automation Orchestrator and Hiring AI Brain to track suggested actions, manage pending approvals for sensitive operations, and provide an audit log of executed actions.

## 2. Purpose
To ensure safe, transparent, and controllable autonomous hiring. It allows the system to proactively recommend strategic actions (e.g., reassigning recruiters or widening agency distribution) while ensuring that critical decisions (e.g., rejecting candidates or approving offers) require explicit human approval.

## 3. Automation Action Categories
The engine categorizes actions into three distinct guardrails:
- **Safe Automation (Auto-Execute)**: Recruiter Assignment, Agency Assignment, Candidate Reminders, Interview Scheduling, SLA Escalation.
- **Approval Required (Human-in-the-Loop)**: Auto Reject Candidates, Auto Shortlist Candidates, Auto Close Job, Auto Change Priority.
- **Manual Only (No Automation)**: Offer Approval, Hiring Decision, Compensation Changes.

## 4. UI Sections Added
The dashboard (`/autonomous-hiring`) is composed of:
- **Overview Metrics**: At-a-glance counters for Suggested Actions, Pending Approvals, Executed Today, and Jobs Auto-Enabled.
- **Suggested Actions Tab**: Lists AI recommendations (via `AISuggestion`) with context and "Approve/Reject" quick actions.
- **Pending Approvals Tab**: Lists actions waiting on specific human clearance (via `ApprovalQueueItem`), showing the recommended decision and the approver role required.
- **Executed Actions Tab**: An operational log of recently processed automations, including their status (Success, Failed, Skipped).
- **Automation Guardrails Card**: A persistent, clear display of which actions fall into which safety category.

## 5. Menu / Route Access
- **Route**: `/autonomous-hiring`
- **Sidebar Placement**: Added under `Intelligence -> Autonomous Hiring`.

## 6. Role Visibility Rules (RBAC)
- **Allowed Roles**: `super_admin`, `tenant_admin`, `hr_manager`, `hiring_manager`.
- **Denied Roles**: `candidate`, `agency_owner`, `agency_admin`, `agency_recruiter`, and unauthenticated users. `recruiter` is also restricted from full global autonomous control to ensure leadership oversight.

## 7. Use Cases
- A Talent Ops Lead reviews the "Suggested Actions" tab daily to approve AI recommendations for rebalancing recruiter workloads.
- A Hiring Manager logs in to clear their "Pending Approvals" queue for auto-shortlisted candidates flagged by the system.
- An Administrator audits the "Executed Actions" tab to ensure that a newly enabled automation rule fired correctly.

## 8. Edge Cases
- **No Suggestions/Approvals**: The UI displays clean, informative `Empty` states rather than broken tables.
- **Invalid Action State**: Trying to approve an already approved action via the API will fail gracefully (based on the underlying model transition rules or simply update the timestamp).

## 9. Test Scenarios
1. **RBAC Validation**: Log in as a Candidate or Agency User. Attempt to access `/autonomous-hiring`. Verify a 403 Forbidden or redirection.
2. **Dashboard Rendering**: Log in as a `tenant_admin`. Navigate to the Autonomous Hiring Engine. Ensure all 4 metric cards render correctly and the tabs toggle without error.
3. **Approve Action**: Given a pending `AISuggestion` in the DB, click "Approve". Verify the success toast appears and the item is removed from the "Suggested Actions" list.
4. **Reject Action**: Given a pending `ApprovalQueueItem`, click "Reject". Verify the success toast appears and the item is removed from the list.
5. **Guardrail Visibility**: Ensure the "Automation Guardrails" card accurately reflects the hardcoded safety categories to users.
