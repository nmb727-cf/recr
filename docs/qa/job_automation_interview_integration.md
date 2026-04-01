# QA Document: Job Automation Engine — Interview Engine Integration

## 1. Feature Overview
The Job Automation Engine now integrates directly with the Interview Engine by allowing jobs to attach predefined **Interview Packages**. This integration automates candidate movement based on interview performance thresholds and predefined round configurations.

## 2. Architecture
- **Data Layer**:
    - `InterviewPackage`: Stores a collection of interview rounds and threshold rules.
    - `InterviewPackageBinding`: Links an `InterviewPackage` to a `JobRequisition`.
- **Logic Layer**:
    - `AutomationEngine`: Evaluates interview results against binding thresholds.
    - `PipelineHooks`: Listens for interview completion to trigger stage moves.
- **UI Layer**:
    - `JobAutomationView`: Central dashboard for all job-level automation.
    - `InterviewAutomationSummary`: Quick-glance panel in Job Command Center.

## 3. Use Cases
- High-volume screening where AI scores above 80% auto-move to the next round.
- Leadership roles requiring manual review regardless of score.
- Ensuring consistent evaluation criteria across different departments.

## 4. Behavior Flow
1. Recruiter attaches an `InterviewPackage` to a `JobRequisition`.
2. Candidate completes an interview round.
3. Interview Engine records the score and decision recommendation.
4. Job Automation Engine compares the score against the round's `threshold_score`.
5. If `auto_pass_enabled` is ON and threshold met: Candidate moves to the next stage.
6. If score is below `auto_reject_below`: Candidate is marked as rejected.

## 5. Automation Scenarios
- **Scenario 1: AI Screening Auto-Pass**
    - Input: AI Score = 85%, Threshold = 70%, Auto-Pass = ON.
    - Expected: Candidate automatically moves to "Technical Interview" stage.
- **Scenario 2: Low Score Auto-Reject**
    - Input: Overall Score = 35%, Reject Threshold = 40%.
    - Expected: Candidate marked as "Rejected" with reason "System Threshold Compliance".
- **Scenario 3: Manual Review Required**
    - Input: `manual_review_required` = ON for the round.
    - Expected: Automation pauses; Recruiter must manually decide the next step.

## 6. Edge Cases
- **No Binding**: If no package is attached, all movements remain manual.
- **Deleted Package**: If a template is deleted after binding, existing jobs retain a frozen copy of the logic in metadata.
- **Conflicting Rules**: If multiple rules trigger, the most restrictive rule (Reject) takes precedence.

## 7. Manual vs Auto Behavior
- **Manual**: Recruiter must click "Move to Stage" after every round.
- **Auto**: System triggers move events immediately upon feedback submission.

## 8. Pipeline Integration
- Every automated decision creates an entry in `ApplicationStageHistory`.
- Pipeline Kanban view updates counts in real-time when automation moves a candidate.

## 9. UI Screens Impacted
- **Job Detail -> Automation Tab**: Detailed rules and round summaries.
- **Job Detail -> Overview**: New "Interview Automation" summary widget.
- **Pipeline Board**: Automated movement indicators on cards.

## 10. Test Scenarios
1. **Verification of Attachment**: Ensure attaching a package correctly updates the Job Automation summary.
2. **Threshold Enforcement**: Test that a candidate with 75% score moves when threshold is 70%.
3. **RBAC Check**: Verify that only Job Owners can change the `automation_enabled` toggle.
4. **Empty State**: Ensure "No Package Attached" is shown clearly when applicable.
