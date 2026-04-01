# QA Document: Recruiter Intelligence + Automation Engine

## 1. Overview
The Recruiter Intelligence Engine provides data-driven insights into recruiter performance, workload, and assignment optimization. It automates the calculation of performance scores, detects capacity bottlenecks, and provides AI-powered assignment recommendations at the job level.

## 2. Scoring Logic
The **Recruiter Performance Score** (0-100) is calculated based on weighted historical outcomes from applications they own or handle:
- **Shortlist Rate (20%)**: Conversion from application to shortlisted/screening.
- **Interview Rate (30%)**: Conversion from application to interview.
- **Hire/Join Rate (50%)**: Conversion from application to joined.

The score reflects the recruiter's effectiveness in progressing candidates and closing hires.

## 3. Workload Detection
- **Idle**: < 10 active candidates.
- **Balanced**: 10-50 active candidates.
- **Overloaded**: > 50 active candidates.

Workload status is used to balance team capacity and ensure no recruiter is a process bottleneck.

## 4. Intelligence Blocks
- **Smart Recommendations**: Suggests top 3 recruiters for a job based on a blend of their performance score (70%) and available capacity (30%).
- **Team Capacity**: Surfaces a high-level overview of team load, flagging overloaded members to prevent SLA breaches.

## 5. Behavior
- **Job-Level Context**: The Job Command Center displays recommendations specific to the selected requisition.
- **Dynamic Refresh**: Intelligence updates as recruiters move candidates through stages or take ownership of new leads.
- **Capacity Guardrails**: Overloaded recruiters are visually flagged with high-priority risk indicators.

## 6. Use Cases
- **Smart Assignment**: HR Manager opens a new job and uses "Smart Recommendations" to assign the best available recruiter.
- **Load Balancing**: Lead recruiter checks the "Team Capacity" block to identify who can take on more roles vs who needs help.
- **Performance Coaching**: Individual recruiters view their own metrics to understand their conversion efficiency.

## 7. Edge Cases
- **New Recruiter**: Recruiters with very few historical candidates will have scores that reflect limited data (High Volatility).
- **Metadata Sync**: Relies on `assigned_owner_id` being correctly set in application metadata.
- **Role Permissions**: Recruiter intelligence is visible only to internal staff roles (Recruiters, HMs, Admins).

## 8. Test Scenarios
- **Scenario 1: Score Update on Join**
    - Action: Move a candidate owned by Recruiter A to "Joined" status.
    - Expected: Recruiter A's "Hire Rate" and "Overall Score" increase in the intelligence view.
- **Scenario 2: Overload Detection**
    - Setup: Assign 51 active candidates to Recruiter B.
    - Expected: Recruiter B's status changes to "overloaded" and appears in the "Overloaded Recruiters" list.
- **Scenario 3: Smart Recommendation Ranking**
    - Setup: Recruiter A has a score of 90 and 40 candidates. Recruiter B has a score of 80 and 5 candidates.
    - Expected: Recruiter B might rank higher or similar to A due to significantly better capacity, despite a lower raw score.
- **Scenario 4: Recommendation Reason**
    - Action: View recommendations for a job.
    - Expected: Each recommendation includes a clear reason (e.g., "Optimal performance and capacity balance").
