# ICC-INTERVIEW-QUESTION-ENGINE-01 QA

## Scope
Centralized interview question engine with global/tenant/template bank, question attributes, grouping, reorder support, and attachment mappings to template/interview type/assessment.

## Embedded QA Checks

### 1) Question Create Works
- Endpoint: `POST /api/v1/interviews/questions/bank/`
- Verified question record persists with required attributes:
  - title/description/type/difficulty/tags/skills/expected answer/scoring weight.

Result: PASS

### 2) Question Attach Works
- Endpoint: `POST /api/v1/interviews/questions/attachments/`
- Verified attach to template stores attachment and syncs question into template question JSON.
- Verified attach to interview type seeds runtime interview questions during manual scheduling.

Result: PASS

### 3) Grouping Works
- Endpoint: `POST /api/v1/interviews/questions/groups/`
- Verified group/section creation with ordered items (`order_index`) and required flags.
- Verified grouped listing via `GET /api/v1/interviews/questions/groups/`.

Result: PASS

### 4) No Console Crash
- Interview Question Bank UI loads:
  - question bank page
  - question builder
  - question grouping UI
- No runtime frontend crash during create/attach/group actions.

Result: PASS

### 5) No Backend 500
- Invalid/edge requests return validation errors.
- No 500 observed in create/attach/grouping/scheduling-linked question seed flows.

Result: PASS

## Automated Validation Executed
- `python3 manage.py test apps.interviews.tests.test_question_engine apps.interviews.tests.test_candidate_runtime_engine apps.interviews.tests.test_security_engine -v 2`
- `npm run -s build`

Both completed successfully.
