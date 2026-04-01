# QA Document: Hiring AI Brain

## 1. Feature Overview
The Hiring AI Brain is the high-level intelligence orchestration layer that sits above all existing recruitment engines (Job Automation, Interview Automation, Pipeline Decision, SLA, etc.). It synthesizes multiple data signals into a unified health index, risk assessment, and set of actionable recommendations.

## 2. Data Inputs Used
- **Pipeline Data**: Candidate counts and stage distribution.
- **Velocity**: Rate of movement through the hiring funnel.
- **SLA Metrics**: Real-time tracking of overdue actions and impending breaches.
- **Interview Signal**: Feedbacks and conversion rates per round.
- **Team Stats**: Recruiter workload and historical performance scores.
- **Agency Signal**: Historical submission quality and conversion from assigned agencies.

## 3. Scoring / Recommendation Logic
- **Hiring Health Score (0-100)**: 
    - 30% Pipeline Fill (Current vs Target Headcount x 10).
    - 30% Conversion Velocity (Success rate of moving to Interview or beyond).
    - 20% SLA Health (Penalty for overdue actions).
    - 20% Activity Multiplier (Bonus for recent candidate movement).
- **Health Labels**:
    - **Healthy (70-100)**: Process moving optimally.
    - **Watch (40-69)**: Slow velocity or high volume of stalled leads.
    - **At Risk (< 40)**: Critical shortage of candidates or significant SLA breaches.

## 4. Intelligence Blocks
- **Hiring Health Dashboard**: Unified index showing the current state of the job.
- **Risk Alerts**: Specific operational risks (e.g., "Insufficient candidate volume").
- **Next Best Actions**: Prioritized tasks (e.g., "Review 5 new applications", "Schedule 3 interviews").
- **Smart Suggestions**: Recommends the best internal recruiter or external agency for the job based on historical performance.

## 5. Behavior
- **Job Command Center**: Blocks appear at the top of the Overview tab for immediate scanning.
- **Pipeline Action Center**: Brain dashboard is accessible via a high-visibility toggle in the header.
- **Real-time Synthesis**: Intelligence refreshes whenever job-level or application-level data is updated.

## 6. Edge Cases
- **No Data**: Jobs without applications show a baseline score of 50 ("Watch") with recommendations to increase sourcing.
- **Headcount Fulfillment**: Health score increases as joined count approaches target headcount.
- **Overloaded Recruiter**: Recommendations logic will bypass overloaded recruiters even if they have high raw scores.

## 7. Test Scenarios
- **Scenario 1: Health Score Sensitivity**
    - Action: Move multiple candidates to "Rejected" in early stages.
    - Expected: Health Index decreases due to lower conversion velocity.
- **Scenario 2: Risk Trigger (Stalled)**
    - Setup: Leave 5 candidates in "Screening" for > 4 days.
    - Expected: "Risk Detection" block flags "Stalled Pipeline".
- **Scenario 3: Recommendation Quality**
    - Setup: Recruiter A has 100% hire rate on 1 candidate. Recruiter B has 80% hire rate on 50 candidates.
    - Expected: Recruiter B is recommended due to higher statistical confidence and proven capacity.
- **Scenario 4: Pipeline Integration**
    - Action: Toggle "Hiring Brain" in Pipeline Action Center.
    - Expected: Dashboard slides down, displaying the same intelligence as the Job Command Center.

## 8. Graceful Degradation
- If the backend service fails, the UI hides the brain dashboard and falls back to standard metric strips.
- If specific data (e.g., Agency performance) is missing, that factor is omitted from the health calculation without breaking the overall index.
