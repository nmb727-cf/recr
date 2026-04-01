# QA Document: Agency Intelligence Engine

## 1. Overview
The Agency Intelligence Engine provides data-driven insights into agency performance and collaboration. It automates the calculation of performance scores, detects collaboration risks, and provides AI-powered agency recommendations at the job level.

## 2. Scoring Logic
The **Agency Performance Score** (0-100) is calculated based on weighted historical outcomes:
- **Shortlist Rate (20%)**: Conversion from submission to shortlisted/screening.
- **Interview Rate (30%)**: Conversion from submission to interview.
- **Hire/Join Rate (50%)**: Conversion from submission to joined.

The score reflects the agency's ability to provide high-quality candidates that progress through the funnel.

## 3. Intelligence Blocks
- **Assigned Performance**: Real-time score and submission count for agencies currently assigned to a specific job.
- **AI Recommendations**: Suggestions for top-performing agencies based on global performance metrics.
- **Agency Risk Detection**: Flags agencies with:
    - **Low Quality**: High volume of submissions but very low shortlist rate (< 15%).
    - **Inactivity**: No submissions within the last 30 days.
    - **Poor Conversion**: High interview volume but zero hires.

## 4. Behavior
- **Job-Level Context**: The Job Command Center displays intelligence specific to the selected requisition.
- **Dynamic Refresh**: Intelligence updates as candidates move through stages or new applications are submitted.
- **Tier Integration**: Respects agency tiers (Preferred, Standard, Probation) in summary views.

## 5. Use Cases
- **Agency Selection**: Recruiter selects a new job and reviews "AI Recommendations" to decide which agencies to assign.
- **Performance Audit**: HR Manager views the "Agency Intelligence" section to identify low-performing agencies for contract review.
- **Sourcing Strategy**: Teams nudge inactive agencies flagged by the Risk Detection system.

## 6. Edge Cases
- **New Agency**: Agencies with < 5 submissions will have scores that may fluctuate significantly (High Volatility).
- **Multiple Tenants**: Performance scores are tenant-isolated; an agency's performance with Client A does not affect their score with Client B.
- **Deleted Data**: Soft-deleted applications are excluded from performance calculations.

## 7. Test Scenarios
- **Scenario 1: Performance Score Update**
    - Action: Move an agency-submitted candidate to "Joined" status.
    - Expected: The agency's "Overall Score" and "Hire Rate" increase in subsequent intelligence lookups.
- **Scenario 2: Risk Detection (Inactivity)**
    - Setup: Agency has not submitted a candidate for 31 days.
    - Expected: "inactive" risk flag appears in the agency performance detail view.
- **Scenario 3: Recommendation Ranking**
    - Setup: Agency A has a score of 85, Agency B has a score of 60.
    - Expected: Agency A appears higher in the "AI Recommendations" list.
- **Scenario 4: Submission Count Sync**
    - Action: Agency submits a new candidate for a job.
    - Expected: "Submission Count" in the Assigned Performance block increments immediately.
