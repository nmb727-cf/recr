# Automation Playbooks

## Overview
Phase 64 Step 13 implements the Automation Playbooks module within the Intelligence Hub. Playbooks are expert-crafted, reusable bundles of automation (Workflows, SLAs, Tasks, Notifications) that can be deployed by enterprise users with a guided setup flow.

## Key Components

### 1. Playbook Definition
- **AutomationPlaybook Model**: Stores the high-level bundle metadata, including category, version, and the guided setup configuration schema.
- **AutomationPlaybookItem Model**: Defines individual components (Workflows, SLAs, etc.) that belong to a playbook.
- **AutomationPlaybookInstall Model**: Tracks the deployment status, configuration values, and created entities for a specific tenant.

### 2. Playbook Engine (`AutomationPlaybookEngine`)
The core service logic responsible for:
- **Discovery**: Listing system-provided and tenant-custom playbooks.
- **Installation**: Orchestrating the creation of multiple underlying automation entities (Workflows, SLAs, Rules) based on user-provided configuration.
- **Rollback**: Safely removing entities created by a playbook installation if needed.
- **Customization**: Enabling tenants to duplicate and customize system playbooks for their unique needs.

### 3. System Playbooks (Fast Start)
Seeded initial system playbooks including:
- **Candidate Follow-up**: Automated engagement sequences.
- **Interview Coordination**: Handling panel feedback and scheduling SLAs.
- **Agency SLA Control**: Ensuring timely responses from external partners.
- **Fast Hiring**: A cross-module accelerator for pipeline velocity.

## API Endpoints
- `GET /api/v1/automation-playbooks/playbooks/library/`: Access the global playbook vault.
- `GET /api/v1/automation-playbooks/playbooks/installed/`: Monitor currently deployed bundles.
- `POST /api/v1/automation-playbooks/playbooks/{id}/install/`: Launch the installation wizard backend.
- `GET /api/v1/automation-playbooks/recommendations/`: AI-driven playbook suggestions.

## UI Section: Intelligence Hub → Playbooks
- **Playbook Library**: Grid view of available automation bundles with preview and one-click install.
- **Playbook Preview**: Detailed breakdown of included components and expected business impact.
- **Install Wizard**: Guided modal for configuring playbook parameters (e.g., SLA windows, notification channels).
- **Recommendations**: Proactive AI suggestions based on tenant usage patterns and gaps.
- **Analytics**: Performance tracking and impact summary for installed playbooks.

## Governance & Isolation
- **System Playbooks**: Read-only global templates provided by the platform.
- **Tenant Scope**: All installed instances and customized playbooks are strictly isolated to the creating tenant.
- **Auditing**: Every installation and customization action is captured in the system audit trail.
