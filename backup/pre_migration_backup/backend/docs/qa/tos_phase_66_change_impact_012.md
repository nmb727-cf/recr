# Automation Change Impact Center

## Overview
Phase 66 Step 15 implements the Automation Change Impact Center within the Intelligence Hub. This module acts as the enterprise safety layer for making adjustments to workflows, allowing teams to preview the exact scope, risk, and ripple effects of any automation change before it hits production.

## Key Components

### 1. Impact Models
- **WorkflowChangeSet**: Represents a proposed set of changes between two versions of a workflow, including an overall risk score and impact level.
- **WorkflowImpactAnalysis**: Stores the results of the change impact scan, mapping exactly which modules, users, SLAs, notifications, and tasks will be affected.
- **WorkflowDependencyMap**: Tracks upstream and downstream dependencies across workflows (e.g., Cross-module chains).
- **WorkflowDeploymentPlan**: Configurable rollout strategies (Immediate, Staged, Canary) generated based on the change's risk score.
- **WorkflowRollbackPreview**: Pre-deployment validation confirming if the changes can be safely rolled back in case of failure.

### 2. Change Impact Engine (`WorkflowChangeImpactEngine`)
The analytical core responsible for:
- **Dependency Detection**: Tracing relationships to identify what other workflows or systems might break.
- **Heuristic Risk Scoring**: Calculating a 0-100 risk score based on the breadth of the impact (number of users, SLAs touched, cross-module actions).
- **Strategy Generation**: Automatically suggesting safer deployment methods (like "Staged" or "Manual Approval") for High and Critical risk changes.

## API Endpoints
- `GET /api/v1/workflow-change/analysis/`: List historical and active change analyses.
- `POST /api/v1/workflow-change/analyze/`: Trigger a new impact scan for a specific workflow version change.
- `GET /api/v1/workflow-change/dependencies/`: Expose the dependency map for graph rendering.
- `GET /api/v1/workflow-change/deployment-plan/`: Retrieve suggested rollout strategies.
- `POST /api/v1/workflow-change/deploy/`: Execute a deployment plan.
- `GET /api/v1/workflow-change/rollback-preview/`: Retrieve rollback safety assertions.

## UI Section: Intelligence Hub → Change Impact
- **Impact Dashboard**: High-level metrics on active changes, high-risk deployments, and safe rollbacks.
- **Analysis Grid**: List of all analyzed workflow changes with their risk scores and calculated impact levels.
- **Analysis Drawer (Inspector)**: Deep dive into the dependency map, showing exact counts of affected users, workflows, and modules, alongside risk justifications.
- **Deployment Plans**: Interactive table allowing administrators to review and execute staged or canary rollouts.
- **Rollback Preview**: Visibility into the safety and potential data impact of reverting a specific change set.

## Governance & Safety
- **Risk-Based Rollout**: Changes scoring > 75 (Critical) are automatically forced into `Manual Approval` deployment strategies. Changes > 50 (High) default to `Staged` percentage rollouts.
- **Pre-Flight Confidence**: No production workflow is overwritten until the deployment strategy is executed, ensuring zero downtime during the analysis phase.
