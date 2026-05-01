# QA Document: Enterprise Workflow Automation Engine

## 1. Overview
The Enterprise Workflow Automation Engine is the core intelligence brain for the Talent Operating System. It provides a multi-tenant, node-based system for building and executing multi-step, event-driven automations.

## 2. Key Components

### 2.1 Database Models
- **Workflow**: Represents a distinct automated sequence bound to a specific trigger event (e.g., `candidate_applied`).
- **WorkflowNode**: Represents individual steps in the workflow (`start`, `action`, `condition`, `delay`, `end`).
- **WorkflowEdge**: Represents the connections between nodes, including conditional routing logic.
- **WorkflowExecution**: Tracks an active or completed workflow run against a specific entity.
- **WorkflowExecutionLog**: A granular audit trail of node-by-node execution state.

### 2.2 Workflow Engine Service
- **Service**: `WorkflowEngine` (`apps/orchestration_center/services/workflow_engine.py`)
- **Key Methods**:
    - `trigger_workflows(event, entity)`: Finds matching active workflows and initializes execution.
    - `execute_node(execution, node)`: Evaluates node logic, executes actions, and routes to the next node via edges.
    - `evaluate_condition(condition, context)`: Evaluates dynamic logic (e.g., `score > 80`).
    - `execute_action(config, context)`: Maps action payloads to backend services (e.g., `move_stage`, `assign_user`).

### 2.3 User Interface
- **Location**: `Intelligence Hub -> Workflows`
- **Features**:
    - **Active Workflows**: List view of configured workflows with active/inactive toggles.
    - **Workflow Builder (Phase 1)**: Modal interface for defining Trigger -> Action sequences.
    - **Execution History**: Table view showing the status (`completed`, `failed`, `paused`) of all triggered runs.

## 3. Supported Triggers & Actions
- **Triggers**: `candidate_applied`, `candidate_moved_stage`, `interview_completed`, `offer_sent`, `offer_accepted`, `job_created`.
- **Actions**: `move_stage`, `send_email`, `assign_user`, `reject_candidate`.
- **Conditions**: Value matching operators (`equals`, `greater_than`).

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| WF-1 | Trigger Candidate Applied | Firing the `candidate_applied` trigger should locate matching workflows and execute the "Assign Recruiter" node successfully. |
| WF-2 | Conditional Routing (Pass) | An `interview_completed` trigger with a score of 85 should pass a `score > 80` condition node and execute the next action. |
| WF-3 | Conditional Routing (Fail) | The same trigger with a score of 75 should stop execution at the condition node without firing the next action. |
| WF-4 | Status Toggle | Deactivating a workflow in the UI should immediately prevent it from triggering on subsequent events. |
| WF-5 | History Logging | Every executed workflow must appear in the "Execution History" tab with accurate timestamps. |

## 5. Technical Implementation Details
- **Backend Application**: `apps/orchestration_center/`
- **Frontend Workspace**: `projects/SaaS_Project/frontend/src/pages/intelligence/IntelligenceHubWorkspace.tsx`
- **Permissions**: Restricted to users with `intelligence.admin` / `workflows.manage` privileges.
- **Tests**: Validated via `pytest` in `backend/apps/orchestration_center/tests/test_workflow_engine.py`.
