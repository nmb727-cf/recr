# QA Document: System Intelligence Memory Layer

## 1. Overview
The System Intelligence Memory Layer is a learning component that persists system-wide performance benchmarks and quality correlations. It enables the Recruitment Operating System to "learn" from historical data to optimize future autonomous decisions.

## 2. Key Components

### 2.1 Memory Storage (Backend)
- **Model**: `SystemIntelligenceMemory`
- **Table**: `icc_system_intelligence_memory`
- **Fields**: Category, Entity ID, Attribute Key, Attribute Value (JSON), Confidence Score, Learned At.

### 2.2 Learning Logic (`SystemIntelligenceMemoryService`)
- **Pipeline Learning**: Calculates global success rates based on Hires vs Rejections.
- **Recruiter Learning**: Records recruiter response velocity and overall performance scores.
- **Agency Learning**: Learns sourcing quality and shortlist-to-hire conversion rates for each partner agency.
- **Interview Learning**: Determines "Ideal Success Thresholds" based on historical interview scores of successful hires.

### 2.3 System Intelligence Page (Frontend)
- **Route**: `/system-intelligence`
- **Access**: Restricted to `tenant_admin`, `super_admin`, and `hr_manager`.
- **Features**:
    - **Highlights**: Pattern count, Confidence score, Velocity trends.
    - **Categorized Memories**: Tabs for Recruiter, Agency, Pipeline, and Interview.
    - **Trigger Learning Cycle**: Button to force the system to re-scan and learn from current data.

## 3. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| SIT-1 | First Access | System should trigger an initial learning cycle and populate memories. |
| SIT-2 | Trigger Learning Cycle | Clicking the button should update `learned_at` timestamps and refresh metrics. |
| SIT-3 | Tab Filtering | Switching between "Recruiter" and "Agency" tabs should show only relevant patterns. |
| SIT-4 | Confidence Logic | Memories derived from larger datasets (>50 apps) should show higher confidence scores. |
| SIT-5 | RBAC Verification | Recruiter or Candidate role should not be able to access the page. |

## 4. Technical Implementation
- **Backend Model**: `projects/SaaS_Project/backend/apps/analytics/models.py`
- **Backend Service**: `projects/SaaS_Project/backend/apps/analytics/memory_service.py`
- **Frontend Page**: `projects/SaaS_Project/frontend/src/pages/analytics/SystemIntelligenceMemory.tsx`
- **API Endpoint**: `GET /api/v1/analytics/intelligence-memory/`
