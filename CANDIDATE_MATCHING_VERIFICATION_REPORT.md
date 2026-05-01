# CANDIDATE_MATCHING_VERIFICATION_REPORT.md

This report provides a comprehensive verification of the **Candidate Matching Engine** implementation against Phase 2 requirements.

## 1. Implemented
- **Basic Matching Engine**: A heuristic-based matching system is implemented in `CRMSuggestionsView` (`apps/candidates/crm_views.py`).
- **Ranking Logic**: Candidates are ranked based on a composite score derived from:
    - **Skills Overlap (60%)**: Ratio of matched vs. required skills.
    - **Experience Range (25%)**: Checks if candidate experience falls within job min/max requirements.
    - **Work Mode Match (15%)**: Alignment of preferred vs. required work mode (e.g., Remote, On-site).
- **UI Integration**: The `JobMatchSuggestions.tsx` component provides a high-fidelity interface for recruiters to view matched candidates, integrated into the Job List and Job Detail views.
- **Match Explanation (Basic)**: The UI explicitly lists "Matched Skills" and "Missing Skills" for each suggestion, providing basic transparency into the score.
- **Actionable Workflow**: Recruiters can one-click "Add to CRM" or "Submit" a candidate directly from the suggestions panel.

## 2. Partial
- **AI-Driven Matching**: The `OrchestrationCenter` includes a `candidate_matching` prompt definition designed to provide deep reasoning (`top_reasons`, `gaps`). However, this is currently an architectural placeholder and not the primary engine driving the UI.
- **Re-ranking**: While experience is part of the heuristic, dynamic re-ranking via UI controls (e.g., "Sort by Salary Fit") is not yet implemented.

## 3. Missing
- **Vector Search**: No `pgvector` or embedding-based similarity scoring exists in the system. The "equivalent matching" requirement is met via SQL/Python heuristics, but the performance and semantic depth of vector search are missing.
- **Advanced Inputs**: Match logic does not yet utilize **Salary Range**, **Availability**, or **Employment Type** (Contract vs Full-time) from either the job or candidate side.
- **Meaning-based Search**: Typo-tolerant or semantic matching (e.g., matching "Python Developer" to "Django Engineer") is not supported by the current exact-match skill logic.
- **Explanation Depth**: Explanations are limited to skill lists; they do not include reasoning for salary mismatches, availability issues, or experience gaps beyond the score.

## 4. Logic Issues
- **Scaling Bottleneck**: `CRMSuggestionsView` performs a Python loop over all candidates in the tenant. This will lead to significant latency once the candidate database exceeds ~5,000 records.
- **Logic Fragmentation**: `CandidateIntelligenceService.calculate_job_fit` contains a different heuristic than `CRMSuggestionsView`, but appears to be unused, creating a maintenance risk.
- **Default Score Bias**: The frontend defaults missing scores to "85%", which may mislead users if the backend fails to return a calculated score.

## 5. Architecture Issues
- **Missing Integration Hub**: The matching engine should ideally be a consumer of the `IntelligenceRuntimeEventService`, triggered automatically when a job is published, rather than a synchronous API call.

## 6. Phase 2 Blockers
1.  **Vector Foundation**: Implementation of `pgvector` or Meilisearch is required to meet the "Similarity scoring using vector or equivalent matching" requirement for large talent pools.
2.  **Advanced Filter Integration**: Integrate Salary and Availability into the matching heuristic to ensure fitment accuracy.
3.  **Automated Suggestion Generation**: Wire the `candidate_matching` AI prompt to generate `AISuggestion` records automatically upon job creation/publication.
