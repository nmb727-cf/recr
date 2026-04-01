# QA Document: Pipeline Candidate Workbench Upgrade

## 1. Feature Overview
The Pipeline Candidate Workbench is a significant upgrade to the existing candidate side panel in the Pipeline module. It transforms a passive detail view into an active execution layer, allowing recruiters and hiring managers to perform critical hiring tasks without navigating away from the Kanban board.

## 2. Purpose
- Centralize all candidate-level execution tasks in a single sidebar.
- Reduce navigation friction and "page jumping".
- Provide real-time intelligence (Automation, Match Score, SLA Health) at the point of action.
- Ensure all decisions are recorded with professional context (mandatory notes).

## 3. Current Panel Reused vs New Additions
- **Reused**: Component `ApplicationDetailPanel` in `PipelineBoard.tsx`, basic drawer structure, candidate identity header, and data fetching logic.
- **New Additions**: Quick Decision Bar, Pipeline Orchestration section, Automation status section, SLA Health section, and Interview Workbench.

## 4. Sections Added
- **Quick Decision Bar (Top)**: High-priority triggers for Shortlist and Reject in a dark-themed, sticky header.
- **Pipeline Orchestration**: Controls for moving stages, assigning owners, and placing candidates on hold.
- **Automation Intelligence**: Real-time display of decision rules and automated engine outcomes.
- **SLA Health**: Visual tracking of "Time in Stage" with overdue breach indicators.
- **Interview Workbench**: Management of upcoming rounds and scheduling triggers.
- **Recent Activity**: A refined operational timeline.

## 5. Supported Actions
- **Fast Move Stage**: Change the application's current stage with a single dropdown.
- **Assign/Change Owner**: Reassign the recruiter or hiring manager responsible for the candidate.
- **Shortlist/Reject**: Finalize candidate outcomes with one-click actions.
- **Place on Hold**: Pause the candidate journey with specific hold rationale.
- **Record Note**: Standalone interaction logging without stage changes.
- **Schedule Interview**: Direct trigger for the interview scheduling modal.
- **Trigger Round**: Immediate start for scheduled interview rounds.

## 6. Behavior Flow
1. User clicks a candidate card on the Pipeline Board.
2. The Workbench Panel (Drawer) slides in from the right.
3. User reviews the "Workbench Dashboard" tab for summary metrics and health.
4. User selects an action (e.g., "Move to Stage").
5. A confirmation modal appears, requesting mandatory "Professional Context" (notes).
6. Upon confirmation, the action is saved, the panel refreshes, and the background Pipeline board updates its counts and positions immediately.

## 7. Use Cases
- **Recruiter Review**: Recruiter scans new applicants, sees a 90% Match Score, checks SLA (On Track), and uses the Fast Move dropdown to push them to "Interview".
- **Hiring Manager Decision**: HM reviews interview feedback, sees an automation recommendation, and clicks "Shortlist" from the top bar.
- **Overdue Management**: User sees a red "Overdue Breach" signal in the SLA section and immediately reassigns the owner to expedite review.

## 8. Edge Cases
- **Mandatory Notes**: Destructive or movement actions require a note; standalone notes can be recorded without movement.
- **Self-Assignment**: User can quickly assign themselves as the owner via the "Assign to Me" shortcut.
- **Pipeline Sync**: If a candidate is moved to a stage not currently visible in the board (due to filtering), the card will disappear from the board but remain open in the panel.

## 9. Permission Behavior
- **Job Ownership**: Only the Job Owner or Tenant Admin can move stages or reject/shortlist candidates.
- **Read-only Access**: Other users can view the workbench but action buttons are disabled.
- **Internal Notes**: Visible only to internal staff (Recruiters/HMs), never to candidates or agencies.

## 10. Test Scenarios
- **Scenario 1: Move Stage with Note**
    - Action: Open workbench, select "Technical Interview" in Move to Stage.
    - Expected: Modal appears, note is required, background board refreshes after confirm.
- **Scenario 2: Place on Hold**
    - Action: Click "Place on Hold", enter reason.
    - Expected: Status tag updates to "on_hold", note is added to timeline.
- **Scenario 3: SLA Risk Visibility**
    - Action: Open a candidate who has been in stage for > 48h.
    - Expected: SLA section shows red "Overdue Breach" text and pulse indicator.
- **Scenario 4: Instant Ownership Change**
    - Action: Change "Decision Owner" to current user.
    - Expected: Success message appears, dropdown reflects updated owner.
