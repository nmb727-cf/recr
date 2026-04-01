# ICC Registry Audit 01

Date: 2026-04-01
Module ID: `ICC-REGISTRY-AUDIT-01`

## Scope

Audited the hard-coded interview registry in:

- [InterviewCommandCenter.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx)

Validated against:

- route coverage in [App.tsx](/home/nirav/projects/SaaS_Project/frontend/src/App.tsx)
- registry shell behavior in [InterviewTypes.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypes.tsx)
- dedicated engines:
  - [InterviewAIEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewAIEngine.tsx)
  - [InterviewTechnicalEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTechnicalEngine.tsx)
  - [InterviewHumanEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewHumanEngine.tsx)
  - [InterviewAssessmentEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewAssessmentEngine.tsx)
  - [InterviewPrequalificationEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewPrequalificationEngine.tsx)
- generic config fallback:
  - [InterviewTypeConfig.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypeConfig.tsx)

## Key Truths

- The frontend registry currently contains `41` hard-coded items, not `40`.
- In the current seeded backend data set, every registry code audited here has a matching backend `InterviewType` record, so there are no current failed-load cases from missing type records.
- A large portion of the registry is still falling back to generic type configuration, not a true type-specific engine.
- Some registry types are routed to the wrong engine entirely.
- The AI registry mapping is not fully subtype-aware because the AI engine does not consume the registry `?type=` route parameter.

## Status Counts

- `Built`: 21
- `Partial`: 3
- `Placeholder`: 13
- `Wrong Route`: 1
- `Reusing Wrong Engine`: 3
- `Failed Load`: 0

## Summary

### A. Fully working

- 21 items open a dedicated engine with a subtype-aware or reasonably mapped builder.

### B. Partially working

- 3 items open the AI engine, but the requested subtype is not actually initialized from the route.

### C. Broken / wrong route

- 4 items route incorrectly:
  - `recruiter_screening`
  - `phone_interview`
  - `take_home_assignment`
  - `final_round`

### D. Not yet implemented

- 13 items still fall back to generic `InterviewTypeConfig` and do not have a dedicated engine.

## Full Matrix

| Registry Item | Category | Current Route | Actual Destination Page | Current Behavior | Status Classification | Notes |
| recruiter_screening | Screening | /interviews/prequalification?type=recruiter_screening | InterviewPrequalificationEngine | Opens prequalification wizard instead of a recruiter screening interview engine. | Reusing Wrong Engine | Screening call is being treated as a form builder. |
| ai_screening | Screening | /interviews/ai?type=ai_screening | InterviewAIEngine | Opens AI Interview engine on the correct AI screening path. | Built | This is the cleanest AI registry mapping currently in place. |
| phone_interview | Screening | /interviews/prequalification?type=phone_interview | InterviewPrequalificationEngine | Opens prequalification wizard instead of phone interview execution/config. | Reusing Wrong Engine | Phone interview is not a prequalification form. |
| one_way_video | Video | /interviews/ai?type=one_way_video | InterviewAIEngine | Opens AI engine, but the requested subtype is not actually initialized from the route. | Partial | User lands in AI builder but not reliably in one-way video mode. |
| prerecorded_video | Video | /interviews/ai?type=prerecorded_video | InterviewAIEngine | Opens AI engine, but subtype is not consumed and prerecorded video is not in supported AI type list. | Partial | Builder defaults back toward generic AI setup. |
| live_video | Video | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No live-video-specific engine is wired from registry. |
| async_text_interview | Async | /interviews/ai?type=async_text_interview | InterviewAIEngine | Opens AI engine, but route subtype is ignored and internal supported code is async_text, not async_text_interview. | Partial | Close conceptually, but not truly subtype-aware. |
| technical_interview | Technical | /interviews/technical?type=technical_interview | InterviewTechnicalEngine | Opens technical wizard and maps to technical screening flow. | Built | Subtype-aware technical builder exists. |
| coding_interview | Technical | /interviews/technical?type=coding_interview | InterviewTechnicalEngine | Opens coding interview technical builder. | Built | Dedicated subtype guidance exists. |
| system_design | Technical | /interviews/technical?type=system_design | InterviewTechnicalEngine | Opens system design technical builder. | Built | Dedicated subtype guidance exists. |
| take_home_assignment | Technical | /interviews/assessments?type=take_home_assignment | InterviewAssessmentEngine | Routes into assessments instead of technical engine. | Reusing Wrong Engine | The engine supports it, but registry category and destination are inconsistent. |
| debugging_interview | Technical | /interviews/technical?type=debugging_interview | InterviewTechnicalEngine | Opens debugging technical builder. | Built | Dedicated subtype guidance exists. |
| whiteboard_interview | Technical | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No whiteboard-specific engine mapping exists. |
| technical_panel | Technical | /interviews/technical?type=technical_panel | InterviewTechnicalEngine | Opens technical panel builder. | Built | Subtype-aware technical flow exists. |
| behavioral_interview | Behavioral | /interviews/human?type=behavioral_interview | InterviewHumanEngine | Opens behavioral human interview builder. | Built | Dedicated human subtype exists. |
| cultural_fit | Behavioral | /interviews/human?type=cultural_fit | InterviewHumanEngine | Opens culture-fit human interview builder. | Built | Alias mapping handles cultural fit. |
| hr_interview | HR | /interviews/human?type=hr_interview | InterviewHumanEngine | Opens HR interview builder. | Built | Dedicated human subtype exists. |
| leadership_interview | HR | /interviews/human?type=leadership_interview | InterviewHumanEngine | Opens leadership interview builder. | Built | Dedicated human subtype exists. |
| executive_interview | HR | /interviews/human?type=executive_interview | InterviewHumanEngine | Opens executive interview builder. | Built | Dedicated human subtype exists. |
| hiring_manager_interview | HR | /interviews/human?type=hiring_manager_interview | InterviewHumanEngine | Opens hiring manager interview builder. | Built | Dedicated human subtype exists. |
| panel_interview | Panel | /interviews/human?type=panel_interview | InterviewHumanEngine | Opens panel interview builder. | Built | Dedicated human subtype exists. |
| sequential_round | Panel | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No sequential-round-specific engine exists. |
| stakeholder_interview | Panel | /interviews/human?type=stakeholder_interview | InterviewHumanEngine | Opens stakeholder interview builder. | Built | Dedicated human subtype exists. |
| bar_raiser | Panel | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No bar-raiser-specific engine exists. |
| final_round | Panel | /interviews/technical?type=final_round | InterviewTechnicalEngine | Routes to technical engine even though human engine also supports final round and registry category is panel/human. | Wrong Route | Current mapping is inconsistent and likely incorrect. |
| group_discussion | Panel | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No group-discussion-specific engine exists. |
| mcq_assessment | Assessment | /interviews/assessments?type=mcq_assessment | InterviewAssessmentEngine | Opens MCQ assessment builder. | Built | Dedicated assessment subtype exists. |
| aptitude_test | Assessment | /interviews/assessments?type=aptitude_test | InterviewAssessmentEngine | Opens aptitude assessment builder. | Built | Dedicated assessment subtype exists. |
| psychometric_test | Assessment | /interviews/assessments?type=psychometric_test | InterviewAssessmentEngine | Opens psychometric assessment builder. | Built | Alias mapping handles psychometric_test -> psychometric_assessment. |
| cognitive_test | Assessment | /interviews/assessments?type=cognitive_test | InterviewAssessmentEngine | Opens cognitive assessment builder. | Built | Alias mapping handles cognitive_test -> cognitive_assessment. |
| language_assessment | Assessment | /interviews/assessments?type=language_assessment | InterviewAssessmentEngine | Opens language assessment builder. | Built | Dedicated assessment subtype exists. |
| case_study | Simulation | /interviews/assessments?type=case_study | InterviewAssessmentEngine | Opens case study assessment builder. | Built | Assessment engine explicitly supports case study. |
| role_play | Simulation | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No role-play engine exists. |
| work_sample_test | Simulation | /interviews/assessments?type=work_sample_test | InterviewAssessmentEngine | Opens work sample assessment builder. | Built | Assessment engine explicitly supports work sample. |
| presentation_interview | Simulation | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No presentation-specific engine exists. |
| portfolio_review | Simulation | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No portfolio-review-specific engine exists. |
| assessment_center | Special | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No assessment-center engine exists. |
| mock_interview | Special | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No mock-interview engine exists. |
| campus_hiring | Special | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No campus-hiring engine exists. |
| walkin_drive | Special | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No walk-in engine exists. |
| interview_cafe_live | Special | /interviews/types/:id/config | InterviewTypeConfig | Loads generic type configuration only. | Placeholder | No interview-cafe-live engine exists. |

## Major Routing Issues

1. AI subtype routing is not real yet.
   - `one_way_video`
   - `prerecorded_video`
   - `async_text_interview`
   - Cause:
     - [InterviewAIEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewAIEngine.tsx) does not read the `?type=` route parameter, unlike the technical, human, assessment, and prequalification engines.

2. Screening items are misrouted into prequalification.
   - `recruiter_screening`
   - `phone_interview`
   - Cause:
     - both are included in `PREQUALIFICATION_ENGINE_CODES` in [InterviewCommandCenter.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx)

3. `final_round` is mapped to the technical engine.
   - Cause:
     - `final_round` is included in `TECHNICAL_ENGINE_CODES`
     - but the human engine also explicitly supports `final_round`

4. `take_home_assignment` is routed to assessments even though the registry classifies it under Technical.
   - Cause:
     - it is in `ASSESSMENT_ENGINE_CODES`, not `TECHNICAL_ENGINE_CODES`

5. Thirteen registry items are still generic placeholders.
   - They route only to [InterviewTypeConfig.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewTypeConfig.tsx)
   - They do not have a real type-specific engine UX

## Route / Config Truth

- Route exists:
  - yes for all audited registry items in the current app state
- Backend type record exists:
  - yes for all audited registry items in the current seeded environment
- Generic config page exists:
  - yes
- Type-specific engine exists for all registry items:
  - no

## Recommended Fixes In Priority Order

1. Fix AI subtype routing.
   - Make [InterviewAIEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewAIEngine.tsx) read `?type=` and initialize:
     - `ai_screening`
     - `one_way_video`
     - `prerecorded_video`
     - `async_text_interview`
   - Also normalize code differences:
     - `async_text_interview` vs `async_text`
     - `prerecorded_video` vs current AI supported type list

2. Remove screening items from prequalification routing.
   - `recruiter_screening`
   - `phone_interview`
   - Either build a screening engine or map them into the correct human/registry engine.

3. Fix `final_round` routing.
   - Decide whether `final_round` belongs to human or technical.
   - Current code is inconsistent and should not remain ambiguous.

4. Fix `take_home_assignment` ownership.
   - Either move it to Assessment in registry/category UX or route it to technical consistently.

5. Replace generic config fallbacks with real engines for the remaining placeholders.
   - Highest-value missing types:
     - `live_video`
     - `whiteboard_interview`
     - `sequential_round`
     - `group_discussion`
     - `role_play`
     - `presentation_interview`

6. Reconcile registry count.
   - Frontend registry says `40`
   - Hard-coded frontend registry currently contains `41`

## Honest Conclusion

The registry is not fully implemented end-to-end. In the current state:

- 21 items are genuinely usable through dedicated engines
- 3 items open the right domain but not the right subtype
- 4 items are routed incorrectly
- 13 items are still generic placeholders behind type config

So the registry is materially functional, but it is not truthful to present all items as fully implemented engines.
