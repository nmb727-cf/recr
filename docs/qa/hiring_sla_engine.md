# QA Document: Hiring SLA Engine

## 1. Feature Overview
The Hiring SLA Engine is an enterprise-grade monitoring layer designed to ensure recruitment velocity by detecting and surfacing action deadlines across the Jobs and Pipeline modules. It identifies candidates and actions that are on track, nearing breach (Due Soon), or already overdue.

## 2. Purpose
- Increase recruitment speed by highlighting bottlenecks and overdue tasks.
- Provide clear ownership of pending actions.
- Enable proactive management of candidate experience by preventing long wait times.

## 3. Existing Logic Reused
- `JobStage.action_deadline_hours`: Used as the primary threshold for stage-level SLAs.
- `Application.updated_at`: Used to calculate the "age" of the current action.
- `InterviewPanelist.deadline_at`: Reused for feedback SLA monitoring.

## 4. SLA Categories Supported
- **Candidate Review SLA**: New submissions not reviewed within stage deadline.
- **Interview Scheduling SLA**: Shortlisted candidates without a scheduled interview.
- **Interview Feedback SLA**: Completed interviews missing feedback.
- **Offer Response SLA**: Offers sent but not responded to by the candidate.
- **Job Progress SLA**: Overall job stagnation detection.

## 5. Detection Logic
- **On Track**: Action age is < (Deadline - 12 hours).
- **Due Soon**: Action age is within 12 hours of the deadline.
- **Overdue**: Action age exceeds the deadline (usually 48h default).
- **Escalated**: Action age exceeds 2x the deadline threshold.

## 6. UI Areas Impacted
- **Pipeline Header**: New "SLA Engine" block showing the 4-tier health snapshot.
- **Candidate Cards**: Visual border cues (Red for Overdue, Amber for Stalled/Due Soon).
- **Job Right-Rail**: "Hiring SLA Engine" section in Operational Intel.

## 7. Behavior Flow
1. Candidate enters a stage.
2. SLA clock starts based on `JobStage` configuration.
3. System monitors `updated_at` timestamp.
4. UI dynamically updates status from "On Track" to "Due Soon" to "Overdue".
5. Status is cleared once the candidate moves to a new stage or an action (like feedback) is recorded.

## 8. Ownership and Escalation
- Initial ownership stays with the assigned Recruiter or Hiring Manager.
- Escalated items are visually prioritized for Tenant Admins and Lead Recruiters.

## 9. Edge Cases
- **Stage Re-entry**: Clock resets when a candidate is moved back to a previous stage.
- **Weekend/Holiday**: Currently calculates based on absolute time (future phase will support business hours).

## 10. Use Cases & Test Scenarios
- **Scenario 1: Candidate submitted but not reviewed in 24h**
    - Setup: Application in 'Applied' stage for 25 hours (48h deadline).
    - Expected: Status remains "On Track".
- **Scenario 2: Action nearing breach**
    - Setup: Application in 'Screening' stage for 37 hours (48h deadline).
    - Expected: Header "Due Soon" count increases; card may show amber indicator.
- **Scenario 3: Interview completed but feedback missing**
    - Setup: Interview ended 49 hours ago with no feedback submitted.
    - Expected: "Overdue" count increases; card gets red border.
- **Scenario 4: Job stagnant with no movement**
    - Setup: All candidates in a job have no movement for > 7 days.
    - Expected: "Bottleneck Alert" flags the job in the right rail.
