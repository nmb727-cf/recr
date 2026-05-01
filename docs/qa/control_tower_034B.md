# QA Document: Talent Control Tower Phase 034B

## 1. Overview
The Talent Control Tower has been upgraded from a passive dashboard to a real-time Hiring Command Center. This phase (034B) focuses on real-time monitoring, an advanced alert & risk engine, drill-down navigation, and global control capabilities.

## 2. Key Features Verified

### 2.1 Real-Time Activity Feed
- **Logic**: Aggregates data from `IntelligenceAuditLog` in the backend.
- **Visuals**: A compact, actionable list showing candidate movements, interview schedules, offers, and system events.
- **Real-time**: Near real-time synchronization with a manual "Sync" override.

### 2.2 Alert & Risk Engine
- **Severity Levels**: 
    - **Critical (Red)**: No candidates after 30 days, extreme SLA breaches.
    - **High (Orange)**: Recruiter overload, high-risk jobs.
    - **Medium (Yellow)**: Sourcing gaps, weak pipelines.
    - **Low (Blue)**: Minor system anomalies.
- **Logic**: Backend `ControlTowerService` scans active jobs, application volumes, and recruiter workloads to generate dynamic alerts.

### 2.3 Drill-Down Navigation
- **Behavior**: Every metric card and alert is clickable.
- **Paths**:
    - Active Jobs -> `/jobs`
    - Pipeline Load -> `/pipeline`
    - Interviews -> `/interviews`
    - Offers -> `/pipeline?status=offer`
    - Alerts -> Specific Job Detail or relevant module.

### 2.4 Global & Time-Based Filters
- **Filters**: Department, Recruiter, Priority.
- **Time Intelligence**: Today, This Week, This Month, Custom Range.
- **Scope**: Filters apply globally across all metrics, activity feeds, and alerts in the Control Tower.

### 2.5 Quick Actions (Control Tower Behavior)
- **Actions**: Assign Recruiter, Add Partner Agency, Escalate Job, Change Priority, Broadcast Drive.
- **UI**: Opens a unified command modal to execute actions without leaving the Control Tower.

### 2.6 RBAC (Role-Based Access Control)
- **Visible to**: `tenant_admin`, `super_admin`, `hr_manager`, `hiring_manager`.
- **Restricted**: Candidates, standard Recruiters (unless granted specific permission), and Guests.

## 3. Technical Implementation
- **Frontend**: `frontend/src/pages/analytics/TalentControlTower.tsx` (Enhanced with 10-section layout).
- **Backend Service**: `backend/apps/analytics/control_tower.py` (Added `get_control_tower_data` with filters, activity, and alerts).
- **API**: `GET /api/v1/analytics/control-tower/` (Accepts query params for filtering).

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| TC-1 | Apply Department Filter | All metrics and alerts should refresh to show only data for that department. |
| TC-2 | Click "Active Jobs" Card | Should navigate to the `/jobs` page. |
| TC-3 | Execute "Assign Recruiter" Action | Modal should open, allow selection, and show success message. |
| TC-4 | Verify Activity Feed Timing | Activity should show "just now" or "X minutes ago" based on `IntelligenceAuditLog`. |
| TC-5 | Access as Recruiter | Should be blocked or redirected if role is not in the allowed list in `App.tsx`. |

## 5. Remaining Blocks / Future Scope
- Integration with live WebSockets for "Push" real-time updates (currently pull-based/manual sync).
- Direct "Execute" logic for all AI Recommendations (currently opens relevant module).
