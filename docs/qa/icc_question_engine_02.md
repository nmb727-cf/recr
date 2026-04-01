# ICC Question Engine 02 QA

Module ID: `ICC-INTERVIEW-QUESTION-ENGINE-01`  
Placement: `Interview Command Center -> Interview Types -> Question Bank`

## Scope

- Verify Question Bank is accessible from Interview Types section in Interview Command Center.
- Verify Question Bank is **not** present in main sidebar navigation.
- Verify question attachment and grouping flows.
- Verify no frontend crash and no backend 500 for question APIs.

## Preconditions

- Backend running with interviews migrations applied.
- Frontend running on local environment.
- Authenticated company or agency user.

## Checks

1. Placement validation
- Open Interview Command Center.
- Go to `Interview Types`.
- Confirm `Question Bank` action button is visible.
- Click button and verify it opens `/interviews/questions`.

2. Sidebar validation
- Check main sidebar Work section.
- Confirm there is no `Interview Questions` menu item.

3. Question create
- In Question Bank tab, create a question with required fields.
- Expect success toast and row appears in list.

4. Attach usage
- In Attach & Usage tab, attach created question to:
  - template
  - interview_type
  - assessment
- Expect success toast and entry appears in attachment table.

5. Grouping
- In Grouping tab, create a group with section and item JSON.
- Expect success toast and group row appears with item count.

6. API stability
- Verify these requests return successful responses:
  - `GET /api/v1/interviews/questions/bank/`
  - `GET /api/v1/interviews/questions/attachments/`
  - `GET /api/v1/interviews/questions/groups/`
- Confirm no backend 500 in logs.

7. UI stability
- Switch tabs repeatedly and refresh page.
- Confirm no console crash.

## Result Template

- Placement under Interview Types: PASS/FAIL
- Not in main sidebar: PASS/FAIL
- Attach works: PASS/FAIL
- Grouping works: PASS/FAIL
- No console crash: PASS/FAIL
- No backend 500: PASS/FAIL
