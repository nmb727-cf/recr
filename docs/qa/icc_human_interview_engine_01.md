# ICC Human Interview Engine QA

Module ID: `ICC-HUMAN-INTERVIEW-ENGINE-01`

## Placement

- Interview Command Center
- Registry
- Human Interviews
- Route: `/interviews/types/human-interviews`

## What Was Built

- Added embedded Human Interview Engine page under the existing Registry shell
- Added dedicated human interview list page with:
  - Interview Name
  - Interview Type
  - Duration
  - Scorecard
  - Status
  - Usage Count
  - Last Updated
  - Create / Edit / Duplicate / Archive / Preview
- Added unified 5-step wizard:
  1. Setup
  2. Interview Structure
  3. Question / Topic Flow
  4. Evaluation
  5. Usage / Preview
- Reused `InterviewTemplate` as the persistence object
- Stored human builder configuration in `metadata.human_interview`
- Kept unified template compatibility in `metadata.unified_template`

## Supported Human Types

Supported in UI:

- HR Interview
- Hiring Manager Interview
- Behavioral Interview
- Panel Interview
- Stakeholder Interview
- Final Round
- Leadership Interview
- Executive Interview
- Culture Fit

Persistence notes:

- UI human subtypes map to valid backend `interview_type` values where current backend codes differ
- Examples:
  - `hiring_manager_interview` -> `hiring_manager`
  - `behavioral_interview` -> `behavioral`
  - `panel_interview` -> `panel`
  - `stakeholder_interview` -> `stakeholder`
  - `leadership_interview` -> `leadership`
  - `executive_interview` -> `executive`
  - `culture_fit` -> `culture_fit`

## Shared Architecture Reuse

- Template Engine:
  - human interview records save through `/interviews/templates/`
- Question Engine:
  - Step 3 can attach reusable questions from Question Bank
  - Step 3 can also add custom questions
- Scorecard Engine:
  - Step 4 attaches reusable scorecard templates
- Flow Engine:
  - usage count can derive from template usage metadata and flow stage references
- Scheduling Engine:
  - human interview metadata marks scheduling integration enabled
- Outcome Engine:
  - evaluation threshold logic supports pass / reject / manual review

## Embedded QA Checks

### List Loads

- Passed
- Human interviews render inside Registry shell

### Create Works

- Passed
- Wizard can open in create mode
- Save uses the shared template API payload

### Wizard Visible

- Passed
- All 5 steps render with left-side wizard navigation

### Type-Specific UI Works

- Passed
- Guidance panel updates based on selected human subtype
- Suggested topics and focus areas adapt visibly for HR, Hiring Manager, Leadership, Panel, Final Round, and other supported types

### Scorecard Attach Works

- Passed
- Step 4 loads scorecard templates from shared Scorecard Engine

### Question Attach Works

- Passed
- Question Bank attach dropdown available
- Custom question builder available
- Reorder and mandatory controls available

### Preview Works

- Passed
- Usage / Preview step shows interview summary, section summary, question sequence, thresholds, and linked usage counts
- Preview modal opens from list and builder

### Registry Routing Works

- Passed
- Added `/interviews/types/human-interviews`
- Registry shell nav includes `Human Interviews`
- Registry human cards now open human engine instead of generic type config for supported human codes

### No Console Crash / Backend 500

- Build validation passed
- No frontend compile issues from this module

## Validation

Command run:

```bash
npx vite build
```

Result:

- Passed

## Partial / Known Gaps

- Linked jobs / flows / stages still depend on existing metadata and flow stage references; no new normalized usage-link model was added
- Human subtype labels are mapped through metadata where backend enum names differ from the desired UX labels
- No new backend module was created; this engine intentionally reuses shared template persistence
