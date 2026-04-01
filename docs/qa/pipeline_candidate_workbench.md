# QA Document: Pipeline Candidate Workbench

## 1. Overview
The Pipeline Candidate Workbench is the execution layer of the Pipeline Action Center. It allows recruiters and hiring managers to interact with candidates and perform critical hiring actions directly from the Kanban board without navigating away.

## 2. Purpose
- Centralize all candidate-level execution tasks in a single sidebar.
- Reduce navigation friction by keeping the user within the Pipeline context.
- Provide immediate access to intelligence (Match Score, Automation) and history.

## 3. UI Behavior
- **Trigger**: Clicks a candidate card on the Pipeline Board or selects from the List View.
- **Interface**: A persistent right-side Drawer (Workbench) that covers approximately 40% of the screen.
- **Execution Bar**: A sticky header containing the most frequent actions (Move, Shortlist, Reject, Schedule, Note).

## 4. Actions Supported
- **Fast Move Stage**: Dropdown to instantly trigger a stage transition.
- **Shortlist**: One-click star action to mark as shortlisted.
- **Reject**: Direct rejection flow with reason/category.
- **Schedule**: Instant modal to schedule interviews without leaving the workbench.
- **Internal Note**: Record professional observations directly into the candidate's activity timeline.
- **Assign Owner**: Update the internal recruiter or hiring manager responsible for the candidate.

## 5. Use Cases
- **Recruiter Review**: Recruiter opens workbench, reviews the AI match score and profile summary, adds an internal note, and moves to "Screening".
- **Hiring Manager Decision**: HM reviews interview feedback in the "Interviews" tab, uses the Workbench to "Shortlist" or "Reject".
- **High-Velocity Sourcing**: Recruiter quickly scans new applications, using the Fast Action bar to process dozens of candidates in minutes.

## 6. Edge Cases
- **Self-Assignment**: Fast "Assign to Self" option for owners.
- **Draft States**: Modal confirmation for all destructive or movement actions to prevent accidental changes.
- **Syncing**: Board counts and intelligence row metrics update automatically after workbench actions.

## 7. Test Scenarios
- **Scenario 1: Add Standalone Note**
    - Setup: Open workbench for any candidate.
    - Action: Click "Add Note", enter text, and confirm.
    - Expected: Note appears at the top of the Activity Timeline immediately.
- **Scenario 2: Instant Stage Movement**
    - Setup: Open workbench for a candidate in "Applied".
    - Action: Select "Interview" from the Fast Move Stage dropdown.
    - Expected: Application moves stage; Pipeline board background refreshes counts.
- **Scenario 3: Interview Visibility**
    - Setup: Candidate has an upcoming interview.
    - Expected: "Interview Status" card shows the round title and time prominently.
- **Scenario 4: Owner Assignment**
    - Setup: Candidate is currently unassigned.
    - Action: Select a user from the "Internal Owner" dropdown.
    - Expected: Metadata updated; owner reflected in data lookups.
- **Scenario 5: Automation Detection**
    - Setup: Candidate was moved by a rule.
    - Expected: "Automation Intelligence" card shows the triggered rule and verdict.
