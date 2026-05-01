# QA Document: HDC Operational Product Conversion (Phase 46)

## 1. Overview
The Hiring Decision Command Center (HDC) has been converted from a "UI shell / demo only" module into a fully operational product integrated with the backend and core system entities (Jobs, Candidates, Users).

## 2. Status Summary

| Section | Operational | Backend Connected | Jobs/Candidates Linkage | Role Access |
|---------|-------------|-------------------|--------------------------|-------------|
| Decision Dashboard | Yes | Yes | Yes (Metrics & Tasks) | Recruiter, HM, Admin |
| Hiring Committee | Yes | Yes | Yes (Create/Vote) | Recruiter, HM, Admin |
| Candidate Comparison | Yes | Yes | Yes (Sets/Weights) | Recruiter, HM, Admin |
| Decision Approval | Yes | Yes | Yes (Approvals Queue) | Finance, HR, Admin |
| Offer Intelligence | Yes | Yes | Yes (Scenario Modeling) | Recruiter, Admin |
| Compensation | Yes | Yes | Yes (Package Builder) | HR, Admin |
| Negotiation | Yes | Yes | Yes (Rounds/Status) | Recruiter, Admin |
| Offer Release | Yes | Yes | Yes (Dispatch Center) | HR, Admin |
| Offer Acceptance | Yes | Yes | Yes (Response Capture) | Recruiter, Admin |
| Joining Tracking | Yes | Yes | Yes (Handoff Console) | HR, Admin |

## 3. Key Operational Changes

### 3.1 Real Data Integration
- **HDC App**: New backend app `apps.hdc` implemented with models for all decision states.
- **Jobs & Candidates**: All creation modals (Committee, Comparison, Negotiation) now fetch real data from `requisitionsApi` and `candidatesApi`.
- **Org Users**: Committee member selection now fetches real team members via `organisationApi.listUsers`.

### 3.2 Workflow Persistence
- **Hiring Committee**: Committees created in the UI are now persisted in the database. Voting updates the `CommitteeMember` and `HiringCommittee` states.
- **Offer Release**: The "Dispatch" action now executes a backend mutation to update the release status and record the dispatcher ID.
- **Joining Tracking**: Status updates (Joined, Postponed, etc.) are persisted to `JoiningCase` model.

### 3.3 Task-Driven Dashboard
- Replaced `demoRows` with operational task panels:
    - **My Decision Committees**: Active committees the user is part of.
    - **Awaiting Offer Release**: Frozen offers ready for dispatch.
    - **Executive Metrics**: Live counts of active cases, modeling scenarios, and releases.

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| HDC-OP-1 | Create Committee | Open Committee tab, click "New Committee", select a real job and candidate, click Save. Check that it appears in the table. |
| HDC-OP-2 | Submit Vote | Click "Vote" on an active committee, select "Hire", add notes, submit. Quorum count should update. |
| HDC-OP-3 | Model Scenario | Open Offer Intelligence, click "Select Scenario" on a draft case, click "Lock Selection". Status should change to RECOMMENDED. |
| HDC-OP-4 | Confirm Joining | Open Joining Tracking, click "Update Status" on a pending case, change to "Joined", set date, save. Table should refresh with new status. |
| HDC-OP-5 | Menu Access | Log in as Recruiter. Verify "Hiring Decision Center" appears in sidebar and opens the operational console. |

## 5. Technical Implementation Details
- **Backend Model File**: `backend/apps/hdc/models.py`
- **Frontend Sections**: `frontend/src/pages/hdc/sections/`
- **API Client**: `frontend/src/api/hdc.ts`
- **Sidebar Integration**: `frontend/src/config/navigation.tsx`
- **Route Registration**: `frontend/src/App.tsx`
