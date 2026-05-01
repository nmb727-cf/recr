# Automation Sandbox & Test Lab

## Overview
Phase 65 Step 14 implements the Automation Sandbox & Test Lab module within the Intelligence Hub. This module provides a secure environment for enterprise users to simulate, validate, and inspect hiring workflows before they are activated in production.

## Key Components

### 1. Sandbox Models
- **WorkflowSandboxRun**: Records the execution of a simulation, including input context, expected outcomes, and actual results.
- **WorkflowSandboxStepLog**: Provides a detailed trace of each node processed during the simulation.
- **WorkflowSandboxScenario**: Defines reusable test cases (e.g., "Candidate Applied") with mock data payloads.
- **WorkflowSandboxArtifact**: Stores simulated outputs like notification previews, task previews, and SLA initiations.
- **WorkflowSandboxApproval**: Manages the governance sign-off process for critical workflows after successful testing.

### 2. Sandbox Engine (`WorkflowSandboxEngine`)
The central simulation logic that:
- **Dry Runs**: Traverses workflow nodes without triggering real side effects (no emails sent, no data mutated).
- **Artifact Generation**: Produces "Simulated Artifacts" that show exactly what would have happened in production.
- **Trace Analysis**: Logs each step's duration and output for deep inspection.
- **Comparison**: Validates actual simulation results against user-defined expected outcomes.

### 3. Scenario Library
Initial system-provided scenarios for rapid testing:
- **Candidate Applied — Standard**: Basic profile application.
- **Interview Completed — High Score**: Positive panel feedback simulation.
- **Deadline Missed — Escalation**: SLA breach and multi-level notification testing.

## API Endpoints
- `GET /api/v1/workflow-sandbox/runs/`: List and manage simulation history.
- `POST /api/v1/workflow-sandbox/simulate/`: Execute a new workflow simulation.
- `GET /api/v1/workflow-sandbox/scenarios/`: Access the test case library.
- `POST /api/v1/workflow-sandbox/approvals/{id}/approve/`: Grant sign-off for production activation.

## UI Section: Intelligence Hub → Sandbox Lab
- **Sandbox Runs Tab**: Monitor and inspect previous simulation results.
- **Run Builder**: Configure new simulations by selecting workflows, versions, and test scenarios.
- **Run Inspector (Drawer)**: View node-by-node trace logs and preview simulated artifacts (Emails, Tasks, SLAs).
- **Scenario Library**: Manage reusable mock datasets for consistent testing.
- **Approval Queue**: Review sandbox results and provide administrative sign-off.

## Governance Integration
- **Safety First**: Zero mutation of production tables during sandbox runs.
- **Activation Block**: Critical workflows can be configured to require a "Success" sandbox run and manual "Approval" before they can be toggled to `active` in the Workflow Hub.
