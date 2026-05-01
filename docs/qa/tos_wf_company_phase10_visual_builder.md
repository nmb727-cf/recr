# QA Document: Visual Workflow Builder (Phase 10)

## 1. Overview
The Visual Workflow Builder is an enterprise-grade UI layer that allows users to create, edit, and manage complex recruitment automations visually. It sits on top of the existing graph-based engine, allowing multi-step logic with conditions and delays.

## 2. Key Features Verified

### 2.1 Visual Canvas (Frontend)
- **Location**: `/intelligence/workflows/:id/builder`
- **Capabilities**:
    - **Draggable Nodes**: Nodes can be repositioned on the canvas using `framer-motion`.
    - **Node Palette**: Support for `Start`, `Trigger`, `Condition`, `Action`, `Delay`, and `End` nodes.
    - **Visual Connections**: Simple SVG edges connecting source and target nodes (Phase 1).
    - **Properties Panel**: Dynamic configuration form based on the selected node type.

### 2.2 Workflow Management (Backend)
- **Status Lifecycle**: Support for `Draft`, `Active`, `Paused`, and `Archived` statuses.
- **Save/Publish**: Persistence of node positions, configurations, and graph edges.
- **Validation**:
    - Ensures exactly one `Start` node.
    - Ensures at least one `End` node.
    - Detects orphan and disconnected nodes.
- **Duplication**: Deep-cloning of workflows including all nodes and edges.

### 2.3 Execution Inspector
- **Functionality**: Users can click "Inspect" on any workflow execution in the history tab to see a step-by-step trace of the execution path and logs.

## 3. API Endpoints
- `GET /api/v1/intelligence/workflows/{id}/builder/`: Retrieve graph data.
- `POST /api/v1/intelligence/workflows/{id}/builder/save/`: Persist visual changes.
- `POST /api/v1/intelligence/workflows/{id}/validate/`: Run graph integrity checks.
- `POST /api/v1/intelligence/workflows/{id}/duplicate/`: Create a copy of the workflow.
- `POST /api/v1/intelligence/workflows/{id}/{action}/`: Perform status actions (`activate`, `pause`, `archive`).

## 4. Test Cases

| ID | Test Case | Expected Result |
|---|---|---|
| VIS-1 | Node Drag & Drop | Dragging a node on the canvas updates its position state and persists on "Save Draft". |
| VIS-2 | Connection Creation | Selecting a target node in the properties panel creates a visual line and an `icc_workflow_edges` record. |
| VIS-3 | Duplicate Workflow | Clicking "Duplicate" in the list creates a new workflow with identical nodes and edges in `Draft` state. |
| VIS-4 | Execution Trace | Opening the inspector for a failed execution should highlight the specific node where the failure occurred. |
| VIS-5 | Validation Fail | Attempting to save a workflow without an `End` node should trigger a validation alert. |

## 5. Technical Implementation Details
- **Frontend Page**: `projects/SaaS_Project/frontend/src/pages/intelligence/WorkflowVisualBuilder.tsx`
- **Backend Views**: `projects/SaaS_Project/backend/apps/orchestration_center/api/views.py`
- **Icons**: Powered by `lucide-react` and `antd` icons.
- **Animations**: Node dragging implemented via `framer-motion`.
