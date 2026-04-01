# ICC Technical Interview Engine QA

Module ID: `ICC-TECHNICAL-INTERVIEW-ENGINE-01`

## Placement

- Interview Command Center
- Registry
- Technical Interviews
- Route: `/interviews/types/technical-interviews`

## What Was Built

- Added embedded Technical Interview Engine page under the existing Registry shell
- Added dedicated technical interview list page with:
  - Interview Name
  - Technical Type
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
- Stored technical builder configuration in `metadata.technical_interview`
- Kept unified template compatibility in `metadata.unified_template`

## Type Support

Supported in UI:

- Technical Screening
- Coding Interview
- System Design
- Architecture Discussion
- Debugging Interview
- Pair Programming
- Technical Panel
- Technical Final Round

Persistence notes:

- UI-specific technical subtypes are mapped to valid backend `interview_type` values where needed
- Examples:
  - `technical_screening` -> `technical_interview`
  - `architecture_discussion` -> `technical_interview`
  - `pair_programming` -> `technical_interview`
  - `technical_final_round` -> `final_round`

## Shared Architecture Reuse

- Template Engine:
  - technical interview records save through `/interviews/templates/`
- Scorecard Engine:
  - Step 4 attaches reusable scorecard templates
- Question Engine:
  - Step 3 can attach from Question Bank
  - Step 3 can also add custom technical questions
- Flow Engine:
  - usage count can derive from template usage metadata and flow stage references
- Scheduling Engine:
  - technical metadata marks scheduling integration enabled
- Outcome Engine:
  - evaluation threshold logic supports pass / reject / manual review

## Embedded QA Checks

### List Page Loads

- Passed
- Technical interviews render inside Registry shell

### Create Works

- Passed
- Wizard can open in create mode
- Save uses the shared template API payload

### Wizard Steps Visible

- Passed
- All 5 steps render with left-side wizard navigation

### Type-Specific UI Works

- Passed
- Guidance panel updates based on selected technical subtype
- Suggested topics and focus areas adapt visibly

### Question Attach Works

- Passed
- Question Bank attach dropdown available
- Custom question builder available
- Order / remove / mandatory toggles available

### Scorecard Attach Works

- Passed
- Step 4 loads scorecard templates from shared Scorecard Engine

### Preview Works

- Passed
- Usage / Preview step shows interview summary, section summary, question sequence, thresholds, and linked usage counts
- Preview modal opens from list and builder

### Registry Routing Works

- Passed
- Added `/interviews/types/technical-interviews`
- Registry shell nav includes `Technical Interviews`
- Registry technical cards now open technical engine instead of generic type config for supported technical codes

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

- Linked jobs / flows / stages depend on existing metadata and flow stage references; no new normalized usage-link model was introduced
- Technical subtype labels beyond current backend interview type choices are mapped through metadata rather than new backend enum additions
- No new backend module was created; this engine intentionally reuses shared template persistence
