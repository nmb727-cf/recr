# QA Document: AI Governance & Approval System (Phase 59 - Step 8)

## 1. Overview
The AI Governance & Approval System provides enterprise-level control over autonomous actions. It enforces human-in-the-loop workflows for high-risk decisions and manages permission-based execution policies.

## 2. Key Components

### 2.1 Governance Rules (Backend)
- **Model**: `AIGovernanceRule` (`apps/orchestration_center/models/governance.py`)
- **Logic**: Defines which system actions require explicit approval based on risk level.
- **Rule Types**:
    - `suggestion_apply`: Applying an AI-generated suggestion.
    - `automation_execute`: Manual execution of an automation rule.
    - `policy_change`: Modifying automation intelligence policies.
    - `prompt_change`: Updating or activating AI prompt templates.
    - `execution_retry`: Retrying a failed background task.

### 2.2 Approval Workflow (Service)
- **Model**: `AIGovernanceApproval`
- **Service**: `AIGovernanceService` manages the creation and resolution of approval requests.
- **Enforcement**:
    - **High/Critical Risk**: Always requires manual approval.
    - **Auto-Apply**: Strictly forbidden for `critical` risk levels.

### 2.3 Governance UI (Frontend)
- **Location**: Intelligence Hub -> Governance tab.
- **Panels**:
    - **Governance Rules Engine**: Table view of all enforced guardrails.
    - **Active Approval Queue**: Management console for pending, approved, and rejected requests.
    - **Decision Justification**: Input area for recording rationales during approval/rejection.

## 3. API Endpoints
- `GET /api/v1/intelligence/governance/rules/`: List all governance guardrails.
- `GET /api/v1/intelligence/governance/approvals/`: View the approval request queue.
- `POST /api/v1/intelligence/governance/approve/`: Grant approval for a specific request.
- `POST /api/v1/intelligence/governance/reject/`: Deny an approval request.

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| GOV-1 | High-Risk Enforcement | Attempting a `critical` risk action should automatically generate a pending record in the Approval Queue. |
| GOV-2 | Approval Flow | Approving a request should update its status to `APPROVED` and log the `approved_by` user ID. |
| GOV-3 | Rejection Rationale | Rejecting a request without a rationale should still work, but ideally rationales are captured via the "Decision Justification" card. |
| GOV-4 | Rule Creation | Adding a new governance rule via the database or API should immediately reflect in the Governance Rules Engine table. |
| GOV-5 | Safety Override | Auto-apply should never be permitted for `critical` risk, even if configured in the rule (Service-level enforcement). |

## 5. Technical Implementation Details
- **Backend Service**: `projects/SaaS_Project/backend/apps/orchestration_center/services/ai_governance.py`
- **Frontend Workspace**: `projects/SaaS_Project/frontend/src/pages/intelligence/IntelligenceHubWorkspace.tsx`
- **Permissions**: Restricted to `intelligence.admin`.
