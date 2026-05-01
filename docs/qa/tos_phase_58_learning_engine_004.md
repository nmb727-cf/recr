# QA Document: Automation Learning Engine (Phase 58 - Step 7)

## 1. Overview
The Automation Learning Engine is a closed-loop optimization system that captures outcomes of AI suggestions and automated workflows to refine future decision-making thresholds and identify policy improvements.

## 2. Key Components

### 2.1 Learning Signals (Backend)
- **Model**: `AutomationLearningSignal` (`apps/orchestration_center/models/automation_learning.py`)
- **Captured Data**: Outcome Type (Success, Failure, Approved, Rejected, etc.), Confidence Score, Execution Time, User Action.
- **Service**: `AutomationLearningService.record_outcome()` logs these signals across the system.

### 2.2 Policy Effectiveness (Service)
- **Function**: `get_policy_learning_data()`
- **Logic**: Aggregates signals per policy to calculate:
    - **Success Rate**: Terminal success/approval vs total attempts.
    - **Recommendation Engine**:
        - `Increase confidence`: If success rate > 95% over 10+ signals.
        - `Lower confidence`: If success rate < 70% or multiple failures.
        - `Review required`: High frequency of manual user overrides.

### 2.3 Learning UI (Frontend)
- **Location**: Intelligence Hub -> Learning tab.
- **Panels**:
    - **Policy Effectiveness Learning**: Table showing success rates and AI-generated recommendations.
    - **Recent Learning Signals**: Audit ledger of the last 100 outcome signals.
    - **AI Recommendations**: Actionable cards for optimizing or risky policies.

## 3. API Endpoints
- `GET /api/v1/intelligence/learning/signals/`: List recent outcome signals.
- `GET /api/v1/intelligence/learning/policies/`: Get effectiveness data per policy.
- `GET /api/v1/intelligence/learning/recommendations/`: Get high-level AI optimization proposals.

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| LRN-1 | Signal Capture | Approving an AI suggestion should trigger a `record_outcome('approved')` call visible in the Signals table. |
| LRN-2 | Success Threshold | A policy with 100% success rate over multiple signals should display "Increase confidence / Enable Auto-Apply" recommendation. |
| LRN-3 | Risk Detection | A policy with multiple "failure" signals should be flagged with "Lower confidence threshold". |
| LRN-4 | Override Tracking | Dismissing a suggestion should record an `overridden` outcome, contributing to "Review required" logic. |
| LRN-5 | Manual Intervention | Recommendations should not automatically update policies; they must remain as proposals in the UI for Admin review. |

## 5. Technical Implementation Details
- **Backend Service**: `projects/SaaS_Project/backend/apps/orchestration_center/services/automation_learning.py`
- **Frontend Workspace**: `projects/SaaS_Project/frontend/src/pages/intelligence/IntelligenceHubWorkspace.tsx`
- **Permissions**: Restricted to `intelligence.admin` role.
