# Phase 10: Portfolio Review Execution Engine

Prompt ID: `ICC-PORTFOLIO-EXECUTION-10`  
Phase: `Interview Command Center / Execution Engine / Phase 10`  
Module: `Portfolio Review Execution Engine`

## Scope

Shared tenant-scoped portfolio review runtime for:

- `portfolio_review_round`
- `design_portfolio_review`
- `creative_portfolio_review`
- `ux_ui_portfolio_review`
- `architecture_portfolio_review`
- `product_portfolio_review`
- `writing_portfolio_review`
- `media_portfolio_review`
- `developer_project_portfolio_review`
- `portfolio_with_walkthrough_round`

Supports async portfolio submission, live walkthrough, mixed file/link portfolio packages, and immutable reviewer snapshotting.

## 1. System Architecture

- Shared engine: `PortfolioReviewExecutionEngine`
- Core components:
  - Portfolio review execution shell
  - Instructions/readiness
  - Portfolio submission engine
  - Asset/link validation engine
  - Portfolio viewer shell
  - Walkthrough/session engine
  - Notes/annotation engine
  - Reviewer evaluation engine
  - Scorecard engine
  - Feedback/recommendation engine
  - Result/decision engine
  - Integrity log
  - Resume/autosave state engine
  - Recruiter monitoring linkage
- Architecture layers:
  - portfolio asset layer
  - submission layer
  - validation layer
  - viewer layer
  - walkthrough layer
  - evaluation layer
  - review layer

Execution model:

- Candidate is global.
- Attempt, submission snapshot, review, result, and decision are tenant-scoped.
- Candidate runtime, assessor runtime, and recruiter runtime are separate.
- Submission snapshot becomes immutable once locked/submitted.
- Resume restores exact submission state, viewer state, and walkthrough state where applicable.

Supported delivery modes:

- file-upload portfolio
- external-link portfolio
- mixed asset portfolio
- async-only review
- live walkthrough review
- hybrid async + walkthrough review

Future-ready extensions:

- recorded walkthrough
- transcript layer
- AI summarization
- originality/similarity analysis
- artifact comparison layer

## 2. Database Design

Primary entities:

- `portfolio_review_attempt`
- `portfolio_asset_record`
- `portfolio_link_record`
- `portfolio_submission_snapshot`
- `portfolio_validation_log`
- `portfolio_walkthrough_session`
- `portfolio_reviewer_observation`
- `portfolio_scorecard_response`
- `portfolio_notes_record`
- `portfolio_annotation_record`
- `portfolio_decision_summary`
- `portfolio_integrity_log`
- `portfolio_result_summary`
- `portfolio_resume_state`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `portfolio_template_id`
- `submission_snapshot_id`
- `asset_id`
- `asset_type`
- `status`
- `started_at`
- `completed_at`
- `submitted_at`
- `auto_submitted_at`
- `last_seen_at`
- `mode_type`
- `validation_status`
- `review_status`
- `score_status`
- `decision_status`
- `walkthrough_status`
- `integrity_flags`
- `version_number`
- `storage_url`
- `external_url`

Entity purposes:

- `portfolio_review_attempt`: root execution record
- `portfolio_asset_record`: uploaded asset metadata and storage binding
- `portfolio_link_record`: external portfolio/project links
- `portfolio_submission_snapshot`: immutable portfolio package bound for review
- `portfolio_validation_log`: validation outcomes for files and links
- `portfolio_walkthrough_session`: live walkthrough session state
- `portfolio_reviewer_observation`: qualitative reviewer observations
- `portfolio_scorecard_response`: rubric scoring records
- `portfolio_notes_record`: structured/freeform notes
- `portfolio_annotation_record`: asset-level annotations or markups
- `portfolio_decision_summary`: consolidated recommendation state
- `portfolio_integrity_log`: suspicious events and audit trail
- `portfolio_result_summary`: final evaluated result
- `portfolio_resume_state`: exact restore state for candidate or walkthrough reconnect

## 3. API Structure

**Candidate APIs**

`POST /candidate/portfolio-reviews/{execution_id}/start`
- Purpose: start attempt
- Method: `POST`
- Inputs:
  - secure execution token
  - readiness confirmation
- Outputs:
  - `attempt_id`
  - mode config
  - submission rules
  - walkthrough config if enabled
- Access: candidate only

`GET /candidate/portfolio-reviews/{attempt_id}/instructions`
- Purpose: fetch portfolio instructions
- Method: `GET`
- Outputs:
  - allowed formats
  - required items
  - file/link rules
  - walkthrough requirement state
- Access: candidate only

`POST /candidate/portfolio-reviews/{attempt_id}/assets`
- Purpose: upload portfolio asset
- Method: `POST`
- Inputs:
  - file metadata
  - binary file or upload session reference
- Outputs:
  - `asset_id`
  - upload state
  - validation pending state
- Access: candidate only

`POST /candidate/portfolio-reviews/{attempt_id}/links`
- Purpose: add external portfolio link
- Method: `POST`
- Inputs:
  - `external_url`
  - title
  - project grouping metadata
- Outputs:
  - `link_id`
  - link validation state
- Access: candidate only

`POST /candidate/portfolio-reviews/{attempt_id}/validate`
- Purpose: validate submission items
- Method: `POST`
- Inputs:
  - selected item ids
- Outputs:
  - validation results
  - accepted/rejected warnings
  - partial pass/fail state
- Access: candidate only

`GET /candidate/portfolio-reviews/{attempt_id}/status`
- Purpose: fetch submission status
- Method: `GET`
- Outputs:
  - upload states
  - validation states
  - required item completeness
- Access: candidate only

`PATCH /candidate/portfolio-reviews/{attempt_id}/submission`
- Purpose: update submission before final lock if allowed
- Method: `PATCH`
- Inputs:
  - asset or link changes
  - grouping/order updates
- Outputs:
  - updated draft portfolio state
- Access: candidate only

`POST /candidate/portfolio-reviews/{attempt_id}/submit`
- Purpose: submit and lock portfolio
- Method: `POST`
- Inputs:
  - final confirmation
- Outputs:
  - snapshot locked
  - review pending state
- Access: candidate only

`GET /candidate/portfolio-reviews/{attempt_id}/snapshot`
- Purpose: fetch candidate-visible snapshot
- Method: `GET`
- Outputs:
  - locked portfolio package
  - asset/link ordering
- Access: candidate only

`POST /candidate/portfolio-reviews/{attempt_id}/walkthrough/join`
- Purpose: join walkthrough session if configured
- Method: `POST`
- Inputs:
  - session token
  - device/network summary
- Outputs:
  - walkthrough session payload
- Access: candidate only

`POST /candidate/portfolio-reviews/{attempt_id}/heartbeat`
- Purpose: reconnect check
- Method: `POST`
- Inputs:
  - connection metadata
- Outputs:
  - session validity
  - restore guidance
- Access: candidate only

`GET /candidate/portfolio-reviews/{attempt_id}/completion`
- Purpose: fetch completion state
- Method: `GET`
- Outputs:
  - submitted/review/result state
- Access: candidate only

`GET /candidate/portfolio-reviews/{attempt_id}/result`
- Purpose: fetch candidate-visible result if allowed
- Method: `GET`
- Outputs:
  - visibility-safe result summary
- Access: candidate only

**Assessor / reviewer APIs**

`GET /interviews/portfolio-reviews/attempts/{attempt_id}/status`
- Purpose: fetch attempt status
- Method: `GET`
- Outputs:
  - submission status
  - walkthrough state
  - review progress
- Access: assessor/reviewer only

`GET /interviews/portfolio-reviews/attempts`
- Purpose: fetch submitted portfolio attempts
- Method: `GET`
- Inputs:
  - tenant filters
- Outputs:
  - attempt queue
- Access: assessor/reviewer only

`GET /interviews/portfolio-reviews/attempts/flagged`
- Purpose: fetch flagged attempts
- Method: `GET`
- Outputs:
  - flagged attempt list
- Access: assessor/reviewer only

`GET /interviews/portfolio-reviews/attempts/{attempt_id}/snapshot`
- Purpose: fetch immutable portfolio snapshot
- Method: `GET`
- Outputs:
  - assets
  - links
  - grouping
  - metadata
- Access: assessor/reviewer only

`GET /interviews/portfolio-reviews/attempts/{attempt_id}/assets/{asset_id}`
- Purpose: fetch asset metadata
- Method: `GET`
- Outputs:
  - asset metadata
  - preview permissions
- Access: assessor/reviewer only

`GET /interviews/portfolio-reviews/attempts/{attempt_id}/walkthrough`
- Purpose: fetch walkthrough details
- Method: `GET`
- Outputs:
  - session timeline
  - attendee states
  - walkthrough notes linkage
- Access: assessor/reviewer only

`POST /interviews/portfolio-reviews/attempts/{attempt_id}/notes`
- Purpose: add notes
- Method: `POST`
- Inputs:
  - note content
  - scope
  - asset reference if applicable
- Outputs:
  - saved note
- Access: assessor/reviewer only

`POST /interviews/portfolio-reviews/attempts/{attempt_id}/annotations`
- Purpose: add annotations
- Method: `POST`
- Inputs:
  - asset id
  - annotation payload
- Outputs:
  - saved annotation
- Access: assessor/reviewer only

`POST /interviews/portfolio-reviews/attempts/{attempt_id}/scorecard`
- Purpose: submit scorecard
- Method: `POST`
- Inputs:
  - rubric scoring payload
- Outputs:
  - score submission state
- Access: assessor/reviewer only

`POST /interviews/portfolio-reviews/attempts/{attempt_id}/review/draft`
- Purpose: save partial review
- Method: `POST`
- Inputs:
  - partial notes
  - draft recommendation
- Outputs:
  - draft saved
- Access: assessor/reviewer only

`POST /interviews/portfolio-reviews/attempts/{attempt_id}/review/finalize`
- Purpose: finalize evaluation
- Method: `POST`
- Inputs:
  - final recommendation
  - final notes
- Outputs:
  - evaluation finalized
- Access: assessor/reviewer only

`POST /interviews/portfolio-reviews/attempts/{attempt_id}/recommendation`
- Purpose: submit recommendation
- Method: `POST`
- Inputs:
  - `hire|hold|reject|escalate`
- Outputs:
  - recommendation state
- Access: assessor/reviewer only

`GET /interviews/portfolio-reviews/attempts/{attempt_id}/result`
- Purpose: fetch final consolidated result
- Method: `GET`
- Outputs:
  - score summary
  - recommendation distribution
  - conflict state
- Access: assessor/reviewer only

**Recruiter APIs**

`GET /interviews/portfolio-reviews/{attempt_id}/monitor`
- Purpose: monitor attempt status
- Method: `GET`
- Outputs:
  - submission state
  - walkthrough state
  - review progress
- Access: recruiter only

`GET /interviews/portfolio-reviews/{attempt_id}/reviews`
- Purpose: fetch submission and pending review tracker
- Method: `GET`
- Outputs:
  - reviewer completion tracker
- Access: recruiter only

`GET /interviews/portfolio-reviews/flagged`
- Purpose: fetch flagged attempts
- Method: `GET`
- Outputs:
  - flagged queue
- Access: recruiter only

`GET /interviews/portfolio-reviews/{attempt_id}/decision-review`
- Purpose: fetch score/decision review shell
- Method: `GET`
- Outputs:
  - consolidated score
  - recommendation summary
  - override eligibility
- Access: recruiter only

`GET /interviews/portfolio-reviews/{attempt_id}/analytics`
- Purpose: fetch analytics summary
- Method: `GET`
- Outputs:
  - validation stats
  - reviewer completion stats
  - walkthrough analytics
- Access: recruiter only

Separation rules:

- Candidate APIs never expose reviewer notes, annotations, or internal scores.
- Assessor APIs expose immutable submission snapshot and review tools only to authorized reviewers.
- Recruiter APIs remain monitoring and decision-oriented only.

## 4. UI Architecture

**Candidate UI**

- Instructions screen
- Readiness/start screen
- Portfolio submission screen
- Upload/link add shell
- Validation/status shell
- Portfolio summary screen
- Submit confirmation
- Walkthrough join screen if configured
- Completed screen
- Interrupted/resume screen

Candidate UI behavior:

- Wizard-based flow
- Clear required vs optional submission items
- Stable upload and validation visibility
- No reviewer concepts exposed
- Resume-safe draft submission state

**Assessor / reviewer UI**

- Attempt list
- Portfolio viewer shell
- Asset navigator
- Link/file preview shell
- Notes panel
- Annotation panel
- Scorecard panel
- Recommendation panel
- Walkthrough review shell if applicable
- Finalize evaluation state

Reviewer UI behavior:

- Side-by-side asset and scoring layout
- Supports file, link, and grouped project views
- Annotation-ready without changing source asset
- Review visibility controlled by policy

**Recruiter UI**

- Attempt status monitor
- Submitted/pending review tracker
- Flagged attempt view
- Consolidated score view
- Decision review shell
- Flow linkage panel

## 5. Execution Flow

1. Portfolio review round is assigned.
2. Candidate receives instructions and requirements.
3. Candidate opens readiness screen.
4. Candidate uploads assets and/or adds links.
5. Validation runs.
6. Candidate reviews submission summary.
7. Candidate submits and locks portfolio package.
8. Immutable submission snapshot is created.
9. Reviewer accesses snapshot.
10. Live walkthrough occurs if configured.
11. Assessors capture notes, annotations, and scores.
12. Evaluation finalizes.
13. Consolidation runs if multi-reviewer.
14. Final result and decision are stored.
15. Recruiter reviews through dedicated shell.
16. Decision engine consumes outcome.

Special flows:

- Upload failure flow:
  - failed assets remain unbound
  - retry allowed before lock
- Validation failure flow:
  - invalid files/links are rejected with reasons
  - candidate can replace before lock if policy allows
- Interrupted flow:
  - candidate resumes exact draft submission state
- Walkthrough reconnect flow:
  - candidate/reviewer rejoins same walkthrough context
- Suspicious activity path:
  - duplicate session, asset tamper, unauthorized access, or anomalous edits are logged
- Consolidation pending path:
  - final result waits until required reviewer submissions complete or override occurs

## 6. Edge Cases

- File upload fails
- External link invalid
- Unsupported format
- Candidate submits incomplete portfolio
- Validation passes partially
- Walkthrough session fails to start
- Candidate disconnects during walkthrough
- Reviewer disconnects during review
- Duplicate login/session
- Expired attempt window
- Missing asset in snapshot
- Annotation save failure
- Assessor opens review before submission finalized
- Multi-reviewer conflict
- Candidate tries reopening submitted attempt

Handling rules:

- Incomplete portfolio can only submit if policy allows partial completion.
- Assets cannot be replaced after review starts unless explicitly reopened and logged by policy.
- Missing snapshot asset creates review-blocking integrity flag.
- Review before finalization shows `submission_pending` or `snapshot_pending`.

## 7. Enterprise Features

- Shared portfolio review engine across creative, design, writing, media, and project-review rounds
- Immutable submission snapshot for audit-safe review
- Mixed file and link portfolio support
- Project grouping and ordered portfolio package support
- Async review and live walkthrough support
- Notes and annotation-ready reviewer shell
- Rubric-based manual scoring
- Asset-level and portfolio-level review support
- Multi-reviewer consolidation and conflict handling
- Secure preview and download permissions
- Link safety validation and file integrity validation
- Full audit trail for:
  - uploads
  - link changes
  - submission lock
  - annotations
  - score edits
  - decision edits
- Future hooks for:
  - recorded walkthrough
  - transcript
  - AI summarization
  - originality/similarity analysis
  - artifact comparison

## 8. Integration Mapping

- `Portfolio Template / Asset Engine`
  - Consumes: portfolio rules, grouping config, required item rules
  - Produces: submission template and validation rules
  - Events: `portfolio_template_bound`

- `Document / Storage Layer`
  - Consumes: uploaded portfolio files, preview generation requests
  - Produces: durable `storage_url`, previews, checksums
  - Events: `portfolio_asset_uploaded`, `portfolio_asset_preview_ready`

- `Live Session / Meeting Layer`
  - Consumes: walkthrough roster and session controls
  - Produces: walkthrough room/session state
  - Events: `portfolio_walkthrough_started`, `portfolio_walkthrough_ended`

- `Scorecard Engine`
  - Consumes: rubric config and reviewer score submissions
  - Produces: normalized score outputs and aggregation inputs
  - Events: `portfolio_scorecard_submitted`, `portfolio_review_finalized`

- `Decision Engine`
  - Consumes: consolidated result, recommendation distribution, override state
  - Produces: final decision and next-step routing
  - Events: `portfolio_decision_ready`, `portfolio_decision_finalized`

- `Candidate Interview Results`
  - Consumes: candidate-visible portfolio result summary
  - Produces: candidate result state
  - Events: `candidate_portfolio_result_published`

- `Analytics Engine`
  - Consumes: upload metrics, validation outcomes, review timing, walkthrough usage, score patterns
  - Produces: operational and evaluation analytics
  - Events: `portfolio_attempt_started`, `portfolio_snapshot_locked`, `portfolio_result_finalized`

- `Automation Engine`
  - Consumes: validation failures, missing reviews, flagged attempts, final results
  - Produces: reminders, escalations, next-stage movement
  - Events: `portfolio_review_pending`, `portfolio_attempt_flagged`, `portfolio_result_ready`

- `Notification Engine`
  - Consumes: assignment, reminders, walkthrough scheduling, result-ready state
  - Produces: candidate/reviewer/recruiter notifications
  - Events: `portfolio_round_assigned`, `portfolio_walkthrough_reminder`, `portfolio_result_published`

