# Automation Operating System

## Overview
Phase 25 Step 18 implements the Automation Operating System (AOS), the master orchestration layer that unifies all automation engines (Workflow, Notification, Task, SLA, Recovery, Governance, etc.) into a single, cohesive runtime.

## Key Components

### 1. Runtime State (`AutomationRuntimeState`)
- **Master Status**: Tracks global automation health (Healthy, Degraded, Paused, Failed).
- **Orchestration Mode**: Unifies operation under different modes (Normal, Safe Mode, Maintenance, Emergency Override).
- **Metric Aggregation**: Provides real-time counts of active workflows, executions, and engine failures.

### 2. Engine Registry (`AutomationEngineRegistry`)
- **Inventory**: A central database of all available automation engines.
- **Heartbeat & Priority**: Monitors engine availability and defines execution priority for cross-engine triggers.
- **Granular Control**: Allows pausing or resuming specific engines (e.g., pausing the Task engine while keeping Notifications active).

### 3. Business Coverage Mapping
- **Automation Density**: Calculates what percentage of core business processes (Candidates, Jobs, Interviews, etc.) are covered by automated workflows.
- **Manual Gap Detection**: Identifies high-value areas currently handled manually that would benefit from automation.

### 4. Operating Insights & Events
- **AOS Kernel Feed**: A unified log of all critical runtime events (mode changes, engine failures, global pauses).
- **AI-Driven Insights**: Heuristic analysis of the global automation state to recommend optimizations or highlight bottlenecks.

## API Endpoints
- `GET /api/v1/automation-os/runtime/`: High-level kernel status.
- `POST /api/v1/automation-os/runtime/mode/{mode}/`: Switch orchestration modes (e.g., enable Safe Mode).
- `POST /api/v1/automation-os/runtime/control/{action}/`: Global pause/resume.
- `GET /api/v1/automation-os/engines/`: Manage the engine registry.
- `GET /api/v1/automation-os/coverage/`: View business automation density.

## UI Section: Intelligence Hub → Automation OS
- **Runtime Dashboard**: Mission control for global automation state with high-impact telemetry cards.
- **Kernel Monitor**: Real-time view of engine registry health and recent operating events.
- **Execution Policies**: Monitoring of concurrency and queue strategies (default kernel policies).
- **Business Coverage View**: Visual breakdown of automation maturity across modules.

## Governance & Permissions
- **Tenant Admin**: Full access to global controls and registry management.
- **Multi-Tenant Rule**: Strict isolation of runtime states, engine statuses, and coverage data.
