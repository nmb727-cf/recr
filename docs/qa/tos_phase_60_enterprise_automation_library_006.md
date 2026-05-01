# QA Document: Enterprise Automation Library (Final Step - Step 9)

## 1. Overview
The Enterprise Automation Library provides a centralized repository of reusable automation templates and workflow packs. It enables tenants to deploy battle-tested recruitment automations by cloning and activating system-provided templates.

## 2. Key Components

### 2.1 Template Library (Backend)
- **Model**: `AutomationLibraryTemplate` (`apps/orchestration_center/models/automation_intelligence.py`)
- **Types**: System Templates (Global, read-only for tenants) and Tenant Templates (Cloned copies, editable).
- **Metadata**: Includes Category, Template Type, Risk Level, and Configuration Payload.

### 2.2 Template Service
- **Functions**:
    - `clone_template_to_tenant()`: Creates a localized copy of a system template.
    - `activate_template()`: Converts a template into an active `AutomationIntelligencePolicy`.
    - `validate_template()`: Ensures the config payload matches system capabilities.

### 2.3 Library UI (Frontend)
- **Location**: Intelligence Hub -> Enterprise Library tab.
- **Views**:
    - **System Templates**: Marketplace-style list of global templates.
    - **My Library**: Personal collection of cloned and custom templates.
    - **Template Details**: Deep-dive into workflow logic and risk assessments.

## 3. API Endpoints
- `GET /api/v1/intelligence/library/templates/`: List available global templates.
- `POST /api/v1/intelligence/library/templates/{id}/clone/`: localized a template for the current tenant.
- `POST /api/v1/intelligence/library/templates/{id}/activate/`: Create and enable a policy from a template.
- `GET /api/v1/intelligence/library/tenant-templates/`: View the tenant's localized collection.

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| LIB-1 | Browse System Templates | User should see the seeded global templates (Follow-up, SLA, etc.) in the first tab. |
| LIB-2 | Clone Template | Clicking "Clone" on a system template should create a copy in the "My Library" tab. |
| LIB-3 | Activate Template | Activating a template from "My Library" should create a new record in the "Automation Intelligence" policies table. |
| LIB-4 | Risk Governance | Cloned templates with `high` or `critical` risk should still be subject to the governance rules defined in Phase 59. |
| LIB-5 | System Read-only | Attempting to update a `is_system_template=True` record via API should be blocked (Service layer check). |

## 5. Technical Implementation Details
- **Backend App**: `apps/orchestration_center/`
- **Frontend Workspace**: `projects/SaaS_Project/frontend/src/pages/intelligence/IntelligenceHubWorkspace.tsx`
- **Seeding**: Initial templates provided via `manage.py seed_automation_library`.
