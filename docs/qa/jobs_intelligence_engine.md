# QA Document: Jobs Intelligence Engine

## 1. Feature Overview

The Jobs Intelligence Engine is an internal analytics and decision-support system designed to make the hiring process smarter, faster, and more effective. It provides real-time, actionable intelligence on individual jobs, surfacing health scores, hiring velocity, bottlenecks, and risks.

This engine integrates with multiple parts of the platform, including the Job Command Center and the Talent Control Tower, to provide a unified and consistent view of hiring performance.

## 2. Job Health Model

The health of a job is calculated on a scale of 0-100 and categorized into one of four levels.

- **Categories:**
  - `Healthy` (85-100)
  - `Watch` (60-84)
  - `At Risk` (40-59)
  - `Critical` (0-39)

- **Input Factors:**
  - **Pipeline Strength (30 pts):** Compares the current number of candidates to a target (10x headcount). A smaller pipeline results in a penalty.
  - **Overdue Actions (20 pts):** Checks for any `ActionDeadline` records that are past their due date. Each overdue item incurs a penalty.
  - **Pipeline Bottlenecks (20 pts):** Detects structural problems in the pipeline (e.g., too many candidates in one stage). Each detected bottleneck incurs a penalty.
  - **Hiring Velocity (30 pts):** Evaluates the pace of hiring against the target fill date. A 'Behind' or 'At Risk' pace incurs a penalty.

## 3. Velocity Logic

Hiring velocity measures the speed at which candidates are moving through the pipeline.

- **Pace Status:**
  - `On Track`: Hiring progress is aligned with the expected timeline based on the target fill date.
  - `At Risk`: Progress is falling behind the expected timeline.
  - `Behind`: Progress is significantly behind the expected timeline.
- **Stage-level Velocity:**
  - The engine calculates the average time (in days) that candidates spend in each stage of the pipeline.
  - This is calculated by analyzing the `ApplicationStageHistory` for all candidates in the job.
  - The average duration is compared to the `sla_target_hours` configured for that stage.
  - **Status:** `Optimal`, `Slow`, or `Critical`.

## 4. Bottleneck Logic

The engine automatically detects several types of bottlenecks:

- **Volume Bottleneck:**
  - **Trigger:** More than 50% of the active pipeline is concentrated in a single stage (with at least 3 candidates).
  - **Severity:** High
  - **Action:** Suggests batch review or reassignment.
- **Interview Conversion Bottleneck:**
  - **Trigger:** The pass rate for completed interviews (recommendation = 'hire') is less than 20% (with at least 5 interviews completed).
  - **Severity:** Medium
  - **Action:** Suggests reviewing interview criteria or sourcing quality.
- **Offer Conversion Bottleneck:**
  - **Trigger:** The offer acceptance rate is below 70% (with at least 3 offers made).
  - **Severity:** High
  - **Action:** Suggests reviewing compensation, benefits, or role clarity.
- **Decision Bottleneck:**
  - **Trigger:** More than 3 pending hiring decisions are overdue.
  - **Severity:** High
  - **Action:** Suggests nudging the responsible hiring managers.

## 5. Source Intelligence Logic

This module evaluates the effectiveness of different sourcing channels for the specific job.

- **Metrics per Source:**
  - `total_count`: Total candidates from that source.
  - `qualified_count`: Candidates who reached 'shortlisted' status or beyond.
  - `hired_count`: Candidates who were hired.
  - `conversion_rate`: Percentage of total candidates who were qualified.
- **Effectiveness Rating:**
  - `High`: At least one hire from the source.
  - `Medium`: Conversion rate is over 30%.
  - `Low`: Otherwise.
- **Agency Breakdown:** When the source is 'agency', the engine provides a breakdown of performance for each individual agency.

## 6. Team Impact Logic

This module assesses the impact of the assigned recruiter and hiring manager.

- **Recruiter Load:**
  - **Metric:** Counts the total number of active jobs assigned to the recruiter.
  - **Impact:** `Low` (<8 jobs), `Medium` (8-15 jobs), `High` (>15 jobs).
- **Recruiter Contribution:**
  - **Metric:** Shows the number of candidates for this job submitted by the primary recruiter vs. other sources.
- **Hiring Manager Responsiveness:**
  - **Metric:** Counts the number of overdue actions assigned to the hiring manager.
  - **Status:** `Responsive` (0-2 overdue), `Slow` (3-5 overdue), `Bottleneck` (>5 overdue).
- **Reassignment Suggested:** A boolean flag is raised if recruiter load is High or the HM is a Bottleneck.

## 7. Fill Risk Logic

This module provides a practical, explainable prediction of the job's likelihood to be filled on time.

- **Fill Probability:** A percentage score starting at a baseline of 80% and adjusted down based on negative signals.
- **Risk Indicators:**
  - Critical job health (`-40 pts`)
  - 'At Risk' job health (`-20 pts`)
  - 'Behind' hiring velocity (`-20 pts`)
  - Thin pipeline (fewer than 3 candidates per headcount) (`-15 pts`)
  - High dependency on a single source (`-10 pts`)
- **Risk Level:** `High` (<50%), `Medium` (50-74%), `Low` (>=75%).

## 8. UI Placement

- **Primary View:** The intelligence is displayed in the **Job Command Center**, which is the primary tab on the **Job Detail** page (`/jobs/:id`).
- **Component:** The `HiringAIBrainDashboard` component is responsible for fetching and rendering all intelligence widgets.
- **Integration:** Key risk signals (e.g., jobs 'At Risk') are surfaced in the global **Talent Control Tower** (`/control-tower`) in the "Alerts & Risks" panel. Clicking an alert navigates directly to the relevant Job Command Center.

## 9. Use Cases

- **Recruiter:** Quickly assesses the health of their assigned jobs, identifies which jobs need immediate attention, and sees recommended actions to get them back on track.
- **Hiring Manager:** Understands the velocity and bottlenecks in their hiring process without needing to manually analyze pipeline data.
- **Head of Talent:** Uses the Talent Control Tower to get a global overview of at-risk jobs and systemic bottlenecks across the organization.

## 10. Edge Cases

- **New Job:** A newly created job will have a low pipeline and low health score initially. The engine is designed to become more accurate as more data (candidates, stage movements) is gathered.
- **No Target Date:** If a job has no `target_date`, the velocity calculation will use a default of 45 days, which may be inaccurate.
- **No SLA Configured:** If `sla_target_hours` is not set on stages, the stage velocity status will be less meaningful.
- **Low Volume:** For jobs with very few candidates, some statistical measures (like conversion rates) may not be significant. The engine applies thresholds (e.g., min 5 interviews) to avoid making judgments on insufficient data.

## 11. Test Scenarios

1.  **Healthy Job:** Create a job, add 20 candidates, move them through stages in a timely manner. **Expected:** Health Score > 85, 'Healthy' label, no bottlenecks.
2.  **Stalled Job:** Create a job, add 10 candidates to the 'Applied' stage, and leave them for several days past the stage SLA. **Expected:** Health Score drops, 'At Risk' or 'Critical' label, 'Slow Movement' factor, 'Volume Bottleneck' detected.
3.  **Low Interview Pass Rate:** Create a job, move 10 candidates to the interview stage, complete 6 interviews and have only 1 pass. **Expected:** 'Interview Conversion Bottleneck' detected, negative impact on health score.
4.  **Low Offer Acceptance:** Create a job, make 4 offers, have only 2 accept. **Expected:** 'Offer Conversion Bottleneck' detected.
5.  **Overloaded Recruiter:** Assign a job to a recruiter who already has 16 active jobs. **Expected:** Team Impact shows 'High' load and suggests reassignment.
6.  **Unresponsive HM:** Assign a job to an HM, create 6 overdue 'decision' actions for them. **Expected:** Team Impact shows HM as 'Bottleneck'.
7.  **Control Tower Alert:** Trigger a 'Critical' health state for a job. **Expected:** An alert for this job should appear in the Talent Control Tower UI. Clicking it should navigate to the job's detail page.
8.  **No Data:** View the Job Command Center for a brand new job with 0 candidates. **Expected:** UI renders gracefully, showing 0s and 'N/A' where appropriate, without crashing. Health score will be low due to pipeline strength.
9.  **Agency Source:** Add candidates from two different agencies. **Expected:** Source Intelligence widget should show two separate entries, one for each agency, with their respective stats.
