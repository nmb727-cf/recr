# QA: Candidate Intelligence Layer (CIL v2)

## Overview
The Candidate Intelligence Layer (CIL) v2 is a robust, multi-factor intelligence engine that moves beyond simple experience-based scoring to provide a holistic, data-driven view of candidate potential, fit, and readiness.

## Multi-Factor Scoring Model

### 1. Intelligence Dimensions
- **Skill Match (60% weight in Job Fit)**: Direct intersection of candidate skills with job requirements.
- **Knowledge Evidence (20% weight)**: Verified through interview performance and assessment scores.
- **Interview Intelligence**: Aggregated panel feedback and weighted decision logic.
- **Availability & Engagement (25% weight in Readiness)**: Real-time tracking of responsiveness, search activity, and notice periods.
- **Experience & Seniority (Reduced to 20% weight)**: Normalized experience scoring to prevent over-reliance on tenure.

### 2. Core Scores
- **Fit Score**: Measures alignment with specific job requirements (Skills + Role Relevance).
- **Readiness Score**: Measures how "ready to hire" a candidate is (Availability + Engagement + Profile Completeness).
- **Potential Score**: Predicts growth based on career trajectory and interview signals.
- **Confidence Score**: Indicates the reliability of the intelligence based on the volume of available data points.

### 3. Candidate Categorization
- **Best Fit**: High match + High readiness.
- **Fast Hire**: Good match + Fast moving in pipeline.
- **High Potential**: High readiness + Strong learning signals (even if fit is lower).
- **Fallback**: Candidates matching basic criteria but lacking strong differentiating signals.

## Explainable AI (XAI)
Every score is accompanied by a **Rationale Block**, explaining the primary drivers behind the number (e.g., "Strong interview performance", "High hiring velocity").

## UI Integration
- **Candidate Database**: Compact intelligence scores and category labels.
- **Job Pipeline**: "Fast Moving" and "Strong Candidate" visual indicators.
- **Hiring AI Brain**: Top 5 "Best Fit" candidates recommended per job.

## Test Scenarios
1. **Experience Weight Test**: Verify that a candidate with 20 years experience but 0 matching skills does NOT rank as a "Best Fit".
2. **Interview Signal Test**: Submit high-scoring feedback for a candidate and verify their "Potential Score" and "Interview Performance" factor increase.
3. **Availability Detection**: Set `is_actively_looking` to `True` and verify the "Readiness Score" jumps.
4. **XAI Rationale**: Ensure the `explainable_ai` summary correctly reflects the top-scoring factors.
5. **Categorization Logic**: Verify that a candidate moving stages every 2 days is correctly labeled as "Fast Hire".

## Current Implementation Notes
- Execution-phase context is indexed in [tos_execution_phase_index.md](/home/nirav/projects/SaaS_Project/backend/docs/qa/tos_execution_phase_index.md).
- Session lock state is summarized in [tos_session_context_summary.md](/home/nirav/projects/SaaS_Project/backend/docs/qa/tos_session_context_summary.md).
- Safe action hardening is locked in [tos_phase_53_safe_action_hardening_009.md](/home/nirav/projects/SaaS_Project/backend/docs/qa/tos_phase_53_safe_action_hardening_009.md).
- Bounded suggestion work is locked in [tos_phase_54_bounded_suggestion_integrations_010.md](/home/nirav/projects/SaaS_Project/backend/docs/qa/tos_phase_54_bounded_suggestion_integrations_010.md).
- The bounded suggestion layer is intentionally paused after `communication_draft` and `followup_recommendation`.
