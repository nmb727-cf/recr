# QA Document: Governance + Audit + Compliance Layer

## 1. Overview
The Governance Layer provides enterprise-grade control and compliance monitoring for the Hiring Operating System. It ensures transparency in AI decisions, tracks human overrides, and maintains a tamper-evident audit ledger of all critical system actions.

## 2. Key Components

### 2.1 Audit Ledger
- **Model**: `IntelligenceAuditLog`
- **Logic**: Unified logging of all mutations including job status changes, candidate movements, interview decisions, and automation events.
- **Verification**: Ensure all significant actions call `AuditService.log()`.

### 2.2 Decision Tracking
- **Scope**: Tracks "Who", "What", and "When" for hiring lifecycle decisions.
- **Data Source**: Combined view of `ApprovalQueueItem` history and high-impact audit logs (e.g., `candidate.rejected`).

### 2.3 Automation Governance
- **Metrics**: Execution volume, Success/Failure ratios.
- **Control**: Tracking of manual overrides (retries, cancellations) to ensure human-in-the-loop oversight.

### 2.4 AI Transparency
- **Transparency**: Tracking of AI recommendations vs. applied suggestions.
- **Overrides**: Specific ledger for cases where human operators dismissed or significantly modified AI-driven proposals.

## 3. UI Implementation
- **Page**: `GovernanceCenter.tsx`
- **Route**: `/governance`
- **Tabs**: 
    - **Audit Ledger**: Comprehensive filterable table of system events.
    - **Decision Tracking**: Timeline of hiring approvals and rejections.
    - **Automation Governance**: Health summary and manual intervention logs.
    - **AI Transparency**: Execution stats and human override analysis.

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| GOV-1 | Perform Job Change | Action should immediately appear in the "Audit Ledger" tab with correct metadata. |
| GOV-2 | Approve AI Suggestion | Approval should be recorded in the "Decision Tracking" tab under "Approval History". |
| GOV-3 | Override Automation | Retrying a failed automation should be logged in "Automation Governance" -> "Manual Overrides". |
| GOV-4 | Access Restriction | A 'candidate' or 'recruiter' role (without permission) should receive a 403 or redirect. |
| GOV-5 | Metadata Inspection | Hovering/Clicking metadata in the audit table should reveal the before/after state JSON. |

## 5. Technical Implementation
- **Backend API**: `projects/SaaS_Project/backend/apps/orchestration_center/api/views.py`
- **Frontend Page**: `projects/SaaS_Project/frontend/src/pages/intelligence/GovernanceCenter.tsx`
- **Endpoints**:
    - `GET /api/v1/intelligence/governance/audit-logs/`
    - `GET /api/v1/intelligence/governance/decisions/`
    - `GET /api/v1/intelligence/governance/automation/`
    - `GET /api/v1/intelligence/governance/ai-transparency/`
