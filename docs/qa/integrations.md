# QA Document: Integration + Ecosystem Platform

## 1. Overview
The Integration Hub is a central platform for connecting the Recruitment Operating System with third-party tools across various categories including HRMS, Email, Calendar, Job Boards, Assessments, Background Verification, Payroll, and Offer tools.

## 2. Key Components

### 2.1 Backend Integration Model
- **Model**: `Integration` (`apps/integrations/models.py`)
- **Fields**: Name, Provider Key, Category, Status, Config (JSON), Auth Data (JSON), Is Connected, Last Sync.

### 2.2 Integration Hub (Frontend)
- **Route**: `/integrations`
- **Tabs/Categories**: 
    - **Email**: Gmail, Outlook
    - **Calendar**: Google Calendar, Outlook Calendar
    - **Job Boards**: LinkedIn, Indeed, Naukri
    - **Assessments**: HackerRank, Codility
    - **HRMS**: Workday, BambooHR
    - **Background Check**: Checkr
    - **Offer Tools**: DocuSign

## 3. Supported Integrations (Phase 1)
- **Email**: Gmail, Outlook Mail
- **Calendar**: Google Calendar, Outlook Calendar
- **Job Boards**: LinkedIn, Indeed, Naukri
- **Assessments**: HackerRank, Codility
- **HRMS**: Workday, BambooHR
- **Background Verification**: Checkr
- **Offer Tools**: DocuSign

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| INT-1 | Toggle Integration | Switching the toggle should call the backend to update the status and refetch the list. |
| INT-2 | Configure Modal | Clicking "Configure" should open a modal with fields for Client ID, Secret Key, and Environment. |
| INT-3 | Category Filter | Clicking a category in the sidebar should filter the provider cards. |
| INT-4 | OAuth Sandbox | Configuration should show a sandbox warning and mock successful authentication. |
| INT-5 | RBAC Access | Ensure only `tenant_admin`, `super_admin`, and `hr_manager` can access the hub. |

## 5. Technical Implementation
- **Backend App**: `apps/integrations/`
- **Frontend Page**: `src/pages/organisation/IntegrationHub.tsx`
- **API Endpoint**: `GET /api/v1/integrations/`
