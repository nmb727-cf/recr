# Today Context — 2026-03-29

## Scope completed

Primary focus today was Interview Question Engine stabilization and UX rebuild under Interview Command Center.

## Backend status

- Verified and applied `interviews` migrations (`0001` to `0010`) including question engine schema.
- Confirmed question endpoints are wired and returning success in local view-level checks:
  - `/api/v1/interviews/questions/bank/`
  - `/api/v1/interviews/questions/attachments/`
  - `/api/v1/interviews/questions/groups/`
- Re-ran interview question engine tests successfully:
  - `apps.interviews.tests.test_question_engine`

## Frontend changes

### Placement updates

- Enforced placement rule: Question Bank is accessed from
  `Interview Command Center -> Interview Types -> Question Bank`.
- Removed Question Engine from main sidebar navigation (company + agency).

Files:
- `frontend/src/config/navigation.tsx`
- `frontend/src/pages/interviews/InterviewCommandCenter.tsx`

### Question Engine rebuild (enterprise UI)

Replaced the previous CRUD-style page with a builder-style workspace:

- Explorer panel with filters:
  - question type
  - difficulty
  - skill
  - tag
  - scope
- Main dynamic builder area:
  - visibly changes controls by selected question type
  - supports `yes_no`, `single_select`, `multi_select`, `short_text`, `long_text`, `number`, `rating`, `file_upload`, `coding_question`, `video_question`
- Right configuration panel:
  - metadata
  - scoring weight
  - tags/skills
  - usage snapshot
- Secondary tabs:
  - Question Builder
  - Attach & Usage
  - Sections / Grouping
  - Preview
- Option builder upgraded:
  - add/edit/delete/reorder options
  - preferred option
  - score per option
  - removed comma-separated options UX
- Grouping/sections UX upgraded:
  - section name/description/instructions
  - attach section to template/interview type/assessment
  - add/reorder/required question selection
  - removed raw JSON as primary UX
- Attach flow upgraded:
  - selector-driven destination mapping
  - template and interview type selectors
  - assessment ref input for assessment mode

Main file:
- `frontend/src/pages/interviews/InterviewQuestionBank.tsx`

## QA documents added

- `docs/qa/icc_question_engine_02.md`
- `docs/qa/icc_question_engine_fix_03.md`

## Validation run today

- Frontend build passed (`npm run -s build`).
- Backend question engine tests passed.
- Placement sanity check passed:
  - no question engine in main sidebar
  - command-center Interview Types has Question Bank access

## Notes / assumptions

- Existing backend model/API contracts were reused; no broad refactor of interview type registry.
- Question engine remains a supporting module under Interview Types hierarchy, not merged into type registry logic.
