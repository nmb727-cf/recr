# QA: Candidate Experience Layer (CEL)

## Overview
The Candidate Experience Layer (CEL) enhances transparency, guidance, and engagement for candidates within the portal and application lifecycle.

## Experience Enhancements

### 1. Status Visibility
- **Current Stage Name**: Candidates now see the human-readable name of their current stage (e.g., "Technical Interview" instead of `interview`).
- **Next Step Guidance**: Dynamic instructions based on the application's current state:
    - *Sourcing*: "Your profile is being reviewed for alignment."
    - *Screening*: "A recruiter will contact you for a brief screening."
    - *Interviewing*: "Interview scheduling is in progress."
    - *Offer*: "Your offer is being prepared."
- **Expected Timeline**: Transparent SLA-based expectations (e.g., "Expect an update within 48 hours").

### 2. Engagement Intelligence
- **Availability Labels**: Shows the candidate how the system perceives their availability (Active, Engaged, Passive).
- **Engagement Tips**: Actionable advice to improve profile visibility:
    - "Complete your profile to increase visibility to recruiters."
    - "Add your core skills to help our AI match you to the best jobs."
- **Next Action**: Single clearest step for the candidate to take next.

### 3. Application Clarity
- **Job Context**: Direct visibility of Job Title and Company Name in the application summary.
- **Process Conclusion**: Clear messaging when an application is rejected or joined ("Process concluded").

## UI / API Support
- **CandidateSelfSerializer**: Powers the candidate dashboard with engagement tips and profile status.
- **CandidateApplicationSerializer**: Powers the "My Applications" view with detailed stage guidance and timelines.

## Test Scenarios
1. **Stage Change**: Move an application from "Sourcing" to "Interview" and verify that `next_step_guidance` updates in the candidate API.
2. **Timeline Accuracy**: Ensure `expected_timeline` reflects the `action_deadline_hours` defined in the Job Stage.
3. **Engagement Triggers**: Empty a candidate's skills and verify that the "Add your core skills" tip appears in `engagement_intelligence`.
4. **Visibility Leak**: Verify that internal-only fields (match scores, recruiter notes) are NOT present in the candidate-facing serializers.
