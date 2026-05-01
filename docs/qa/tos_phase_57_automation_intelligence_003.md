# QA Document: Automation Intelligence Analytics (Phase 57 - Step 6)

## 1. Overview
The Automation Intelligence Analytics suite provides a comprehensive monitoring layer for the Recruitment Operating System's autonomous capabilities. It tracks AI-driven suggestion accuracy, policy effectiveness, and overall execution health across the platform.

## 2. Key Components

### 2.1 Backend Analytics Service
- **Service**: `AutomationAnalyticsService` (`apps/orchestration_center/services/automation_analytics.py`)
- **Key Metrics Tracked**:
    - **Suggestions**: Created, Approved, Rejected, Dismissed, Applied, Failed.
    - **Policies**: Trigger count, Auto-approve count, Auto-apply count, Policy-specific failures.
    - **Executions**: Total runs, Success rate, Retry count, AI vs. Automation distribution.
    - **Confidence**: Average model confidence, auto-conversion rates.

### 2.2 API Endpoints
- `GET /api/v1/intelligence/analytics/overview/`: KPI summary for the dashboard.
- `GET /api/v1/intelligence/analytics/suggestions/`: Detailed lifecycle and category data.
- `GET /api/v1/intelligence/analytics/policies/`: Per-policy performance metrics.
- `GET /api/v1/intelligence/analytics/executions/`: Health and resilience metrics for background tasks.

### 2.3 UI Implementation
- **Section**: Intelligence Hub -> Analytics
- **Layout**: 
    - **KPI Cards**: Real-time summary of Suggestions, Conversions, and Failures.
    - **Lifecycle Chart**: Visual distribution of AI decisions (Created -> Approved -> Applied).
    - **Engagement Performance**: Horizontal bar chart comparing suggestion volume vs. approval rate per category.
    - **Governance Table**: Detailed view of all active automation intelligence policies.
    - **Execution Health**: Success rates and retry counts for AI and rule-based tasks.

## 3. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| ANA-1 | Tenant Isolation | Analytics should only show data belonging to the logged-in user's tenant. |
| ANA-2 | Suggestion Flow | Moving a suggestion from PENDING to APPROVED should immediately update the Lifecycle chart upon refresh. |
| ANA-3 | Policy Triggering | Triggering an automation policy should increment the "Triggered" count in the Policy Effectiveness table. |
| ANA-4 | Failure Tracking | An execution that fails should increment the "Failures" card and update the Success Rate metric. |
| ANA-5 | Period Filtering | Changing from "Last 30 Days" to "Last 7 Days" should adjust all metrics and chart data points. |

## 4. Technical Implementation
- **Frontend**: `projects/SaaS_Project/frontend/src/pages/intelligence/IntelligenceHubWorkspace.tsx`
- **Charts**: Powered by `recharts` for responsive SVG visualization.
- **Backend Permissions**: Restricted to `intelligence.admin` (Admin only).
