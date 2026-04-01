# QA Document: Pipeline Decision Engine

## 1. Overview
The Pipeline Decision Engine is an intelligence layer integrated into the Pipeline Action Center. It automatically detects urgent tasks, identifies process bottlenecks, flags stalled candidates, and surfaces automation outcomes to help recruiters prioritize their work.

## 2. Architecture
- **Data Provider**: Consumes standard application, stage, and interview data.
- **Intelligence Layer**: A React-based decision logic embedded in `PipelineBoard.tsx` that evaluates candidate state in real-time.
- **Visual Feedback**: Granular metrics in the header and status indicators on candidate cards.

## 3. Detection Logic
- **Urgent Actions**: 
    - Candidates in 'applied' or 'screening' stages.
    - Candidates whose last update was > 48 hours ago (Overdue).
- **Bottlenecks**: 
    - Identifies the stage with the highest candidate volume.
    - Flags stages with candidates aging > 4 days.
- **Stalled Leads**: 
    - Detects candidates with no activity/movement for > 4 days.
- **Automation Detection**:
    - Scans `metadata.automation_triggered` or `metadata.workflow_mode === 'automated'`.

## 4. Use Cases
- **Prioritization**: Recruiter opens the pipeline and immediately sees they have 5 "Urgent Actions".
- **Process Optimization**: Hiring manager sees a bottleneck in the "Technical Interview" stage and allocates more interviewers.
- **Candidate Nurturing**: System flags "Stalled Leads" that need a touchpoint to prevent drop-off.

## 5. Behavior
- **Header Summary**: Updates dynamically based on current job filter.
- **Candidate Cards**: 
    - Red left-border for Overdue (> 48h).
    - Amber left-border for Stalled (> 4 days).
    - Recommendation text displayed at the bottom of the card (e.g., "Schedule Next Round").
    - Automation icon (Zap) shown for candidates moved by the engine.

## 6. Edge Cases
- **Fresh Jobs**: Metrics show "Healthy" or "Clear" when no data is present.
- **Bulk Movements**: Intelligence row updates immediately after bulk stage changes.
- **Automation Mismatch**: If automation fails, the lead is automatically flagged as "Urgent" for manual review.

## 7. Test Scenarios
- **Scenario 1: Urgent Action Detection**
    - Setup: Add a new candidate to 'Applied' stage.
    - Expected: "Urgent Actions" count increases; card shows "Review Candidate".
- **Scenario 2: Bottleneck Identification**
    - Setup: Move 10 candidates into "Interview" stage.
    - Expected: "Bottleneck Alert" flags the "Interview" stage.
- **Scenario 3: Stalled Lead Flagging**
    - Setup: Use a candidate with `updated_at` from 5 days ago.
    - Expected: Card gets amber border and "Stalled" tooltip; header count increases.
- **Scenario 4: Automation Visibility**
    - Setup: Set `metadata.automation_triggered` to `true` on an application.
    - Expected: Zap icon appears on card; "Automation" count in header increases.
