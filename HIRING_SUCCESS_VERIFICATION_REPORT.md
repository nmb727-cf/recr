# HIRING SUCCESS VERIFICATION REPORT

Scope verified against requested Phase 3 Hiring Success Prediction requirements across:
- Models
- APIs
- Services
- ML pipeline
- UI screens

## 1. Implemented

- Candidate-job score field exists in pipeline model.
  - Evidence: `Application.match_score` in `backend/apps/pipeline/models.py:35`.
- Candidate-job scoring API exists (heuristic match suggestions).
  - Evidence: `CRMSuggestionsView` in `backend/apps/candidates/crm_views.py:240`.
- Candidate-job score output is numeric and percentile-styled (0-100 style) in UI.
  - Evidence:
    - Job candidate list column: `frontend/src/pages/jobs/JobFullView.tsx:389`
    - Pipeline board column: `frontend/src/pages/pipeline/PipelineBoard.tsx:1370`
- Missing skills are exposed in suggestion output/UI.
  - Evidence:
    - API: `missing_skills` in `backend/apps/candidates/crm_views.py:302`
    - UI: `frontend/src/components/JobMatchSuggestions.tsx:97`
- Tenant scoping is present for core suggestion retrieval.
  - Evidence: candidate/job filtering by `request.user.tenant_id` in `backend/apps/candidates/crm_views.py:246-257`.

## 2. Partial

- Probability score for candidate-job combination: partially implemented as `match_score` heuristic, but not a calibrated probability.
  - Evidence: weighted rule formula in `backend/apps/candidates/crm_views.py:274-288`.
- Prediction explanation: partial.
  - Implemented: matched/missing skills.
  - Missing: structured success rationale, risk factors, confidence per candidate-job prediction.
- Score range definition: implicit only.
  - Formula max is 100 (60 + 25 + 15), but no explicit validation contract for range.
  - Evidence: `backend/apps/candidates/crm_views.py:274-288`.
- Candidate profile intelligence includes confidence/explanation, but not candidate-job success prediction.
  - Evidence: `CandidateIntelligenceService` outputs `confidence` and `explainable_ai` in `backend/apps/candidates/services.py:355-390`.

## 3. Missing

- Model trained on historical hiring outcomes (candidate-job success model): missing.
  - No training pipeline or model artifacts for hiring success found.
  - No ML framework/model fit usage found in hiring path.
- Continuous learning for hiring success model: missing.
  - Existing retraining endpoints are for workflow automation, not candidate-job hiring success.
- Confidence score for candidate-job prediction: missing.
  - `Application` contract has `match_score` but no prediction confidence field.
  - Evidence: `frontend/src/types/index.ts:471-487`.
- Required Phase 3 input coverage is incomplete.
  - Not used in candidate-job scoring: education, interview score, response rate, past hiring outcomes.
  - Not used from job side: level/seniority, location, role type.
  - Not used historical features: similar hires, successful placements, past job outcomes.
- Retraining mechanism for hiring success model: missing.
- Fallback for no historical data in hiring-success prediction: missing (no historical-model path exists).
- Confidence level in explanations: missing.

## 4. Logic Issues

- Work-mode scoring bug: wrong field name used.
  - Code checks `preferred_work_mode`, but model field is `work_mode_preference`.
  - Evidence:
    - Buggy check: `backend/apps/candidates/crm_views.py:284-286`
    - Actual model field: `backend/apps/candidates/models.py:139`
- UI contract mismatch in suggestion card.
  - Backend returns `candidate.name`, UI reads `candidate.full_name`.
  - Evidence:
    - API payload: `backend/apps/candidates/crm_views.py:294`
    - UI read: `frontend/src/components/JobMatchSuggestions.tsx:67,70`
- Direct submit endpoint appears incorrect from suggestions UI.
  - UI posts to `/applications/`, while pipeline create route is under `/pipeline/pipeline/applications/`.
  - Evidence:
    - UI call: `frontend/src/components/JobMatchSuggestions.tsx:32`
    - API route pattern: `backend/apps/pipeline/urls.py:6`
- AI labeling risk (fake prediction perception).
  - UI labels heuristic matches as "AI-powered" though engine is deterministic rule scoring.
  - Evidence: `frontend/src/components/JobMatchSuggestions.tsx:46` + formula in `backend/apps/candidates/crm_views.py:274-288`.

## 5. Architecture Issues

- No dedicated hiring success prediction architecture (model registry/versioning/feature store/training jobs) in hiring path.
- `calculate_job_fit` exists but appears unused in active candidate-job scoring flow.
  - Evidence: method in `backend/apps/candidates/services.py:401`; no active caller found.
- Heuristic intelligence mixed with predictive naming.
  - Example: hardcoded/global heuristics in hiring intelligence service (not learned model).
  - Evidence: `backend/apps/jobs/services.py:147-152`.
- Scalability concern in suggestions engine.
  - Loads all tenant candidates and scores in Python loop, no pagination/top-k prefilter.
  - Evidence: `backend/apps/candidates/crm_views.py:254-260`.

## 6. Phase 3 blockers

1. No trained candidate-job success model from historical outcomes.
2. No hiring-specific continuous learning/retraining pipeline.
3. No candidate-job confidence score output.
4. Incomplete feature ingestion vs Phase 3 spec (candidate, job, historical inputs).
5. Explainability gaps (risk factors + confidence + reasoned success likelihood not complete).
6. Active logic defects in suggestion flow (field mismatch + payload mismatch + likely wrong submit endpoint) that reduce reliability of current scoring UI.

