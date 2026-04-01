# ICC Prequalification Engine 02

Date: 2026-03-29
Module ID: `ICC-PREQUALIFICATION-ENGINE-02`

## Placement

Validated under:

- `Interview Command Center -> Registry -> Prequalification`
- Route: `/interviews/types/prequalification`

## What Was Built

- Enterprise list page with:
  - name
  - type
  - status
  - usage count
  - last updated
  - create / edit / duplicate / archive / preview actions
- Unified 5-step wizard:
  - Setup
  - Form Builder
  - Knockout Logic
  - Routing
  - Usage / Preview
- Supported types:
  - Screening Form
  - Knockout Form
  - Eligibility Form
  - Qualification Form
  - Job Fit Form
  - Skill Fit Form

## Backend Persistence

Real backend persistence is used for:

- prequalification forms
- sections
- questions
- rules

Stored in metadata:

- prequalification type
- associated role
- knockout summary
- routing summary
- usage shell
- integration flags

## Builder Coverage

Step 2 supports:

- nested sections
- yes / no
- dropdown
- multi select
- text
- numeric
- date
- file upload
- question ordering
- conditional rules
- show / hide question
- skip section
- route to outcome
- reject / manual review branching

Step 3 supports:

- auto reject enabled
- scoring enabled
- pass threshold
- reject threshold
- manual review enabled

Step 4 supports:

- move to AI Interview
- move to Technical Interview
- move to Human Interview
- reject
- manual review
- next stage naming
- recruiter review required

## Validation

Checked:

- registry tab loads
- prequalification route works
- registry card routing works for screening-related registry items
- wizard steps visible
- nested question/rule builder renders
- save works against backend APIs
- duplicate works
- archive works
- preview works
- no console-blocking build error
- no route conflict introduced

## Technical Notes

- Save uses a replace-on-save strategy for nested sections/questions/rules:
  - form metadata is updated
  - existing sections are removed
  - sections, questions, and rules are recreated in draft order
- This is simpler and safer than partial diff logic for the current product stage.

## Build Result

- `npx vite build` passed
