# ICC Question Engine Fix 03 QA

Module ID: `ICC-INTERVIEW-QUESTION-ENGINE-01`

## Placement Checks

- Question engine accessible from `Interview Command Center -> Interview Types -> Question Bank`.
- Question engine is not present in main sidebar navigation.
- 40 interview types registry remains separate and not merged with question builder.

## Functional Checks

1. Dynamic question logic
- Open Question Builder.
- Change question type between: `yes_no`, `single_select`, `multi_select`, `short_text`, `long_text`, `number`, `rating`, `file_upload`, `coding_question`, `video_question`.
- Verify builder fields visibly change per selected type.

2. Option builder
- For `single_select` / `multi_select`, verify:
  - add option
  - edit option
  - reorder option
  - delete option
  - preferred option toggle
  - score per option
- Confirm no comma-separated option input is used as primary UX.

3. Grouping / sections UX
- Create section with:
  - section name
  - section description
  - instructions
  - destination (template/interview type/assessment)
  - selected questions
  - reorder + required toggle
- Confirm no raw JSON editor is required for normal flow.

4. Attach flow
- Attach selected question to:
  - interview template
  - interview type default bank
  - assessment
- Confirm selector-driven UX works and attachment list updates.

5. Preview
- Open Preview tab.
- Verify preview updates based on current question type and builder state.

## Stability Checks

- No frontend console crash while switching tabs and editing builder fields.
- No backend 500 for:
  - `GET /api/v1/interviews/questions/bank/`
  - `GET /api/v1/interviews/questions/attachments/`
  - `GET /api/v1/interviews/questions/groups/`

## Result

- Placement under Interview Types: PASS/FAIL
- Sidebar exclusion: PASS/FAIL
- Dynamic type UI: PASS/FAIL
- Option builder UX: PASS/FAIL
- Grouping UX without JSON dependency: PASS/FAIL
- Attach flow UX: PASS/FAIL
- Preview behavior: PASS/FAIL
- Console/backend stability: PASS/FAIL
