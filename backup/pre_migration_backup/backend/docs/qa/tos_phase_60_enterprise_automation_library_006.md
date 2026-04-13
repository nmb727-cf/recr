# Enterprise Automation Library

## Overview
Phase 60 Step 9 implements the Enterprise Automation Library, providing enterprise users with a repository of reusable, prebuilt automation templates. This system enables rapid deployment of industry-standard automation workflows while maintaining tenant-level control and safety.

## Key Components

### AutomationTemplate Model
Stores both system-wide and tenant-specific templates:
- `template_key`: Unique identifier for the template.
- `category`: Classification (e.g., candidate followup, escalation).
- `trigger_type`: The event that initiates the automation.
- `action_set` / `condition_set`: JSON configurations for the automation behavior.
- `default_risk_level`: Pre-assigned risk (Low, Medium, High, Critical).
- `is_system_template`: Boolean indicating if it's a platform-provided template.

### AutomationTemplateService
Manages the template lifecycle:
- `list_templates()`: Retrieves available templates based on tenant and system scope.
- `clone_template()`: Copies a system template to a tenant's private library for customization.
- `activate_template()`: Creates an active `AutomationIntelligencePolicy` from a template, applying risk-based defaults.

## Governance & Safety
- **System Templates**: Read-only and immutable for all tenants.
- **Tenant Clones**: Editable and customizable within the tenant's workspace.
- **Risk Integration**: Templates with High or Critical risk levels are created as 'disabled' by default, requiring administrative review before activation.
- **Tenant Isolation**: Activation and custom templates are strictly scoped to the tenant who created them.

## API Endpoints
- `GET /api/v1/intelligence/templates/`: Lists system-provided templates.
- `POST /api/v1/intelligence/templates/{id}/clone/`: Clones a template to the tenant library.
- `POST /api/v1/intelligence/templates/{id}/activate/`: Deploys a template into an active policy.
- `GET /api/v1/intelligence/templates/tenant/`: Lists the tenant's custom or cloned templates.

## UI Section: Intelligence Hub → Automation Library
- **System Templates Tab**: Browsable grid of prebuilt automations categorized by use case.
- **My Templates Tab**: Manage and activate cloned or custom templates.
- **Deployment Flow**: One-click "Use" or "Activate" actions to instantly turn a template into an active automation policy.
