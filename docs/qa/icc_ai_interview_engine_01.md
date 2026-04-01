# ICC-AI-INTERVIEW-ENGINE-01 QA

## Scope
- Placement: `Interview Command Center -> Interview Types -> AI Interviews`
- AI interview builder, template, and preview UI
- Supported types:
  - `one_way_video`
  - `async_text`
  - `async_audio`
  - `ai_screening`
  - `ai_technical`
  - `ai_behavioral`
- Template save flow with question engine, scorecard engine, flow engine, and decision engine wiring

## Embedded QA Checks

### 1. AI interview builder loads
- Open `Interview Command Center`.
- Go to `Interview Types`.
- Click `AI Interviews`.
- Confirm builder screen renders without crash.

Result: PASS/FAIL

### 2. Response types selectable
- In builder, change `Response type` across video, audio, and text.
- Confirm preview updates and response handling tags switch accordingly.

Result: PASS/FAIL

### 3. AI config saves
- Create or update an AI interview template.
- Verify:
  - template save returns success
  - linked interview type config persists `ai_interview` payload
  - no backend 500 in logs

Result: PASS/FAIL

### 4. Preview works
- Update intro message, instructions, question set, retries, prep time, and scoring weight.
- Confirm preview cards update immediately.

Result: PASS/FAIL

### 5. Stability
- Open browser console while switching templates and saving.
- Confirm no console crash.
- Confirm no backend 500 from:
  - `GET /api/v1/interviews/types/`
  - `GET /api/v1/interviews/templates/`
  - `GET /api/v1/interviews/questions/groups/`
  - `GET /api/v1/interviews/scorecards/templates/`
  - `GET /api/v1/interviews/flows/`
  - `PUT /api/v1/interviews/types/{id}/config/`
  - `POST /api/v1/interviews/templates/` or `PUT /api/v1/interviews/templates/{id}/`

Result: PASS/FAIL

## Validation Run
- `python3 manage.py test apps.interviews.tests.test_interview_types_engine -v 2`
- `npm run build`
