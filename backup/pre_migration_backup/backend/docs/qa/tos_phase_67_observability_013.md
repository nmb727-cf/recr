# Automation Observability Center

## Overview
Phase 67 Step 16 implements the Automation Observability Center within the Intelligence Hub. This module provides real-time monitoring, failure tracking, latency analysis, and dependency heartbeats for the entire Talent OS automation cluster.

## Key Components

### 1. Observability Models
- **WorkflowExecutionTrace**: Captures granular, step-by-step execution data including node-level latency and status.
- **WorkflowObservabilityEvent**: A centralized log for system events categorized by severity (Info to Critical).
- **WorkflowDependencyHealth**: Real-time status tracking for internal and external dependencies (e.g., AI Engine, Notification Service).
- **WorkflowAnomaly**: AI-driven detection of unusual patterns such as sudden failure spikes or execution loops.

### 2. Observability Engine (`WorkflowObservabilityEngine`)
The central logic layer responsible for:
- **Trace Management**: Recording the detailed path of every workflow execution.
- **Health Monitoring**: Periodically checking the heartbeat of critical sub-services.
- **Anomaly Detection**: Running heuristic checks against recent execution data to identify performance or stability issues.
- **Alerting**: Triggering system notifications when critical failures or anomalies are detected.

## API Endpoints
- `GET /api/v1/workflow-observability/live/`: Monitor currently active and running workflow traces.
- `GET /api/v1/workflow-observability/failures/`: Access a detailed log of failed workflow steps.
- `GET /api/v1/workflow-observability/latency/`: Analyze average execution times across workflows.
- `GET /api/v1/workflow-observability/dependencies/`: View the real-time health status of all automation dependencies.
- `GET /api/v1/workflow-observability/anomalies/`: Review system-detected unusual behaviors.

## UI Section: Intelligence Hub → Observability
- **Live Monitor Tab**: Auto-refreshing table showing real-time workflow activity.
- **Failure Logs Tab**: Centralized view for debugging automation errors.
- **Dependency Health**: Visual grid showing the operational status of the cluster heartbeats.
- **Anomaly Alerts**: Severity-coded alerts for performance bottlenecks or systemic failures.

## Command Center Integration
The Observability Center feeds critical telemetry into the Automation Command Center, highlighting:
- Total live executions.
- Active system anomalies.
- Global system health status.
