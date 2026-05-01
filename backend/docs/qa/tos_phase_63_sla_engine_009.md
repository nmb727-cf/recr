# Automation SLA Engine

## Overview
Phase 63 Step 12 implements the Automation SLA Engine, a core module within the Intelligence Hub designed to enforce, track, and measure time-bound recruitment actions. This ensures accountability and responsiveness across the entire Talent OS.

## Key Components

### 1. SLA Models
- **WorkflowSLAPolicy**: Defines the rules (deadline, warning window, priority) for specific events.
- **WorkflowSLAExecution**: Tracks individual instances of an SLA for a specific entity (e.g., a candidate or interview).
- **WorkflowSLAReminder**: Manages scheduled and sent notifications before and after breaches.
- **WorkflowSLAEscalationRule**: Defines the multi-level path for unaddressed breaches.
- **WorkflowSLABreachInsight**: System-generated analysis of where and why SLAs are failing.

### 2. SLA Engine (`WorkflowSLAEngine`)
The central service handling:
- **Execution Lifecycle**: Creating, completing, and cancelling SLA trackers.
- **Breach Detection**: Identifying overdue actions and initiating escalations.
- **Reminders**: Calculating and scheduling warning notifications.
- **Insights**: Proactively analyzing patterns to suggest policy optimizations.

### 3. Background Processing
- `check_sla_reminders`: Celery task to dispatch scheduled warnings.
- `check_sla_breaches`: Periodic scanner to mark breaches and trigger escalation levels.
- `run_sla_daily_maintenance`: Aggregates cross-tenant analytics and generates daily insights.

## API Endpoints
- `GET /api/v1/workflow-sla/policies/`: Manage SLA rules.
- `GET /api/v1/workflow-sla/executions/`: View live trackers and their remaining time.
- `POST /api/v1/workflow-sla/executions/{id}/complete/`: Manually resolve an SLA tracker.
- `GET /api/v1/workflow-sla/analytics/`: High-level summary of completion and breach rates.
- `GET /api/v1/workflow-sla/breach-insights/`: AI-driven bottleneck identification.

## UI Section: Intelligence Hub → SLA Engine
- **SLA Policies Tab**: Create and configure event-based deadlines.
- **Live Trackers Tab**: Real-time view of active deadlines with countdowns.
- **Breach Dashboard**: Comparative analysis of SLA performance by module and team.
- **System Insights**: Actionable recommendations based on repeated breach patterns.

## Governance & Permissions
- **Tenant Admin / HR Manager**: Full configuration access.
- **Recruiters**: Visibility into SLAs assigned to their active candidates/jobs.
- **Data Scoping**: Strict multi-tenant isolation across all SLA records and logs.
