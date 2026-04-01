# ICC Registry Recount And Gapfix 03

Date: 2026-04-01
Module ID: `ICC-REGISTRY-RECOUNT-AND-GAPFIX-03`

## Result

The Interview Registry is now truthfully aligned to exactly `40` visible product registry items.

Implemented now:

- removed the extra visible registry item
- fixed AI subtype route handling
- fixed `final_round` routing
- fixed `take_home_assignment` category/routing alignment
- stopped `recruiter_screening` and `phone_interview` from opening prequalification incorrectly
- stopped undeveloped items from falling through to generic type config via registry click
- added honest registry status badges:
  - `Built`
  - `Partial`
  - `Not Developed`

## Phase 1: Exact 40 Recount

### Extra Item Removed

Removed from the visible registry list:

- `interview_cafe_live`

Reason:

- it was the `41st` hard-coded registry item
- it behaves like a proprietary branded variant rather than a core product-defined interview type
- keeping it in the main registry made the registry count false

Decision:

- keep backend support if needed later
- remove it from the visible core registry so the registry truthfully represents the product-defined 40

## A. Final Exact 40 Interview Types

1. `recruiter_screening`
2. `ai_screening`
3. `phone_interview`
4. `one_way_video`
5. `prerecorded_video`
6. `live_video`
7. `async_text_interview`
8. `technical_interview`
9. `coding_interview`
10. `system_design`
11. `take_home_assignment`
12. `debugging_interview`
13. `whiteboard_interview`
14. `technical_panel`
15. `behavioral_interview`
16. `cultural_fit`
17. `hr_interview`
18. `leadership_interview`
19. `executive_interview`
20. `hiring_manager_interview`
21. `panel_interview`
22. `sequential_round`
23. `stakeholder_interview`
24. `bar_raiser`
25. `final_round`
26. `group_discussion`
27. `mcq_assessment`
28. `aptitude_test`
29. `psychometric_test`
30. `cognitive_test`
31. `language_assessment`
32. `case_study`
33. `role_play`
34. `work_sample_test`
35. `presentation_interview`
36. `portfolio_review`
37. `assessment_center`
38. `mock_interview`
39. `campus_hiring`
40. `walkin_drive`

## B. Built Items

Count: `25`

- `ai_screening`
- `one_way_video`
- `async_text_interview`
- `technical_interview`
- `coding_interview`
- `system_design`
- `take_home_assignment`
- `debugging_interview`
- `technical_panel`
- `behavioral_interview`
- `cultural_fit`
- `hr_interview`
- `leadership_interview`
- `executive_interview`
- `hiring_manager_interview`
- `panel_interview`
- `stakeholder_interview`
- `final_round`
- `mcq_assessment`
- `aptitude_test`
- `psychometric_test`
- `cognitive_test`
- `language_assessment`
- `case_study`
- `work_sample_test`

## C. Partial Items

Count: `1`

- `prerecorded_video`
  - current state:
    - routes into the AI engine correctly
    - currently reuses the `one_way_video` AI builder
  - what is missing:
    - distinct prerecorded-video builder treatment
    - dedicated subtype-specific UX instead of alias reuse

## D. Not Developed Items

Count: `14`

- `recruiter_screening`
- `phone_interview`
- `live_video`
- `whiteboard_interview`
- `sequential_round`
- `bar_raiser`
- `group_discussion`
- `role_play`
- `presentation_interview`
- `portfolio_review`
- `assessment_center`
- `mock_interview`
- `campus_hiring`
- `walkin_drive`

## E. Fixes Completed Now

### Routing / Mapping

- AI route parameter handling fixed in:
  - [InterviewAIEngine.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewAIEngine.tsx)
- `final_round` moved off technical routing and into human routing
- `take_home_assignment` aligned to `Assessment` category and assessment routing
- `recruiter_screening` and `phone_interview` no longer open prequalification

### Registry Trust Fix

Updated registry behavior in:

- [InterviewCommandCenter.tsx](/home/nirav/projects/SaaS_Project/frontend/src/pages/interviews/InterviewCommandCenter.tsx)

Now:

- built items open the correct engine
- partial items remain clickable and are clearly marked
- undeveloped items stay visible but honest
- undeveloped items no longer open unrelated engines
- undeveloped items no longer fall through to fake generic config from registry click

## F. Remaining Gaps

### Partial

- `prerecorded_video`
  - missing a dedicated subtype layer instead of aliasing to one-way video

### Not Developed

Missing dedicated engine work for:

- screening interview engine
  - `recruiter_screening`
  - `phone_interview`
- video/live execution type builder
  - `live_video`
- technical variants
  - `whiteboard_interview`
- panel/group variants
  - `sequential_round`
  - `bar_raiser`
  - `group_discussion`
- simulation variants
  - `role_play`
  - `presentation_interview`
  - `portfolio_review`
- special programs
  - `assessment_center`
  - `mock_interview`
  - `campus_hiring`
  - `walkin_drive`

## G. Final Missing Types List

| Interview Type | Category | Current State | What Is Missing | Recommended Build Order |
| recruiter_screening | Screening | not developed | route only was wrong, no screening builder, no execution UI, no flow-aware screening engine | 1 |
| phone_interview | Screening | not developed | route only was wrong, no dedicated phone interview builder, no execution shell | 2 |
| prerecorded_video | Video | partial | distinct builder behavior, clearer prerecorded-only UX | 3 |
| live_video | Video | not developed | UI shell, builder, execution room linkage | 4 |
| whiteboard_interview | Technical | not developed | route, builder, technical structure, scorecard mapping | 5 |
| sequential_round | Panel | not developed | route, multi-round flow builder, stage orchestration | 6 |
| group_discussion | Panel | not developed | route, group execution shell, evaluation design | 7 |
| role_play | Simulation | not developed | builder, evaluator flow, scenario config | 8 |
| presentation_interview | Simulation | not developed | builder, instructions, review structure | 9 |
| portfolio_review | Simulation | not developed | builder, artifact review flow, scorecard mapping | 10 |
| bar_raiser | Panel | not developed | dedicated bar-raiser rubric and panel flow | 11 |
| assessment_center | Special | not developed | multi-exercise orchestration, evaluation model | 12 |
| walkin_drive | Special | not developed | high-volume event shell, scheduling/ops flow | 13 |
| campus_hiring | Special | not developed | campus event workflow and batch routing | 14 |
| mock_interview | Special | not developed | practice-mode engine and runtime behavior | 15 |

## Registry Status After Fix

- total visible registry items: `40`
- built: `25`
- partial: `1`
- not developed: `14`

## Embedded QA

Checked:

- total registry count is exactly `40`
- no extra visible registry item remains
- built items route to the correct engine
- fixed routes no longer open wrong engines
- partial item is visibly marked
- not-developed items remain visible and honest
- not-developed items do not redirect to dashboard
- not-developed items do not open unrelated engines
- no console-blocking build error
- no backend route change required

## Build Result

- `npx vite build` passed
