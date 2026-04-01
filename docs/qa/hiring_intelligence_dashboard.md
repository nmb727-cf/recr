# QA Document: Hiring Intelligence Dashboard

## 1. Overview
The Hiring Intelligence Dashboard provides real-time, data-driven insights into the recruitment process for a specific job. It is integrated into the Job Command Center (Overview tab) to surface hiring health, risks, momentum, and actionable recommendations at a glance.

## 2. Intelligence Blocks
- **Hiring Health Block**: 
    - **Balance Index**: Percentage of candidates in advanced stages (Interview, Offer, Joined).
    - **Velocity**: Qualitative speed of the hiring process (e.g., "Optimal").
    - **Health Score**: A 1-10 quantitative rating of the job's overall process status.
- **Hiring Risk Block**:
    - **Stalled Leads**: Count of candidates without activity for > 7 days.
    - **SLA Breaches**: Count of candidates who have exceeded the 48h response/action window.
    - **Process Delay**: Indicator of overall process friction.
- **Pipeline Momentum Block**:
    - **New Today**: Real-time count of applications received in the last 24 hours.
    - **Vs Last Week**: Percentage growth trend compared to the previous 7-day window.
- **Intelligence Insights (AI Recommendations)**:
    - Actionable suggestions based on pipeline state (e.g., "Review 5+ new applicants", "Nudge stalled candidates").

## 3. Behavior
- **Dynamic Updates**: The dashboard refreshes whenever the job context or application dataset changes.
- **Actionability**: Recommendations are designed to be actionable, with links or clear directives.
- **Visual Hierarchy**: Uses color-coded signals (Emerald for Health, Rose for Risk, Indigo for Momentum) to guide user attention.

## 4. Use Cases
- **Morning Standup**: Recruiter opens the job and checks "Hiring Health" and "Intelligence Insights" to prioritize the day's tasks.
- **Leadership Review**: Hiring Manager views "Hiring Risk" to identify where they need to provide feedback or nudge stakeholders.
- **Sourcing Strategy**: Teams check "Pipeline Momentum" to see if a recent sourcing campaign is yielding results.

## 5. Edge Cases
- **No Applications**: Dashboard displays 0s or "Low" signals gracefully without breaking.
- **Stale Data**: Uses `dayjs` relative time to ensure "New Today" and "Stalled" logic is always accurate to the current timestamp.
- **Permissions**: The dashboard is visible to any user with "View Job" permissions, but recommendations may vary based on role.

## 6. Test Scenarios
- **Scenario 1: New Application Sensed**
    - Action: Submit a new application for the job.
    - Expected: "New Today" count in Momentum block increments immediately.
- **Scenario 2: SLA Breach Detection**
    - Setup: Application updated 50 hours ago.
    - Expected: "SLA Breaches" count in Hiring Risk block increments.
- **Scenario 3: Pipeline Rebalance**
    - Action: Move a candidate from "Applied" to "Interview".
    - Expected: "Balance Index" in Hiring Health increments.
- **Scenario 4: Recommendation Generation**
    - Setup: 10 candidates sitting in "Applied" for > 24h.
    - Expected: "Intelligence Insights" surfaces "Review 5+ new applicants".
