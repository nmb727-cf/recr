# Phase 05: Video Interview Execution Engine

Prompt ID: `ICC-VIDEO-INTERVIEW-EXECUTION-05`  
Phase: `Interview Command Center / Execution Engine / Phase 05`  
Module: `Video Interview Execution Engine`

## Scope

Shared tenant-scoped recorded video runtime for:

- `one_way_video_interview`
- `async_video_screening`
- `recorded_behavioral_interview`
- `recorded_hr_interview`
- `recorded_managerial_interview`
- `recorded_language_interview`
- `recorded_intro_interview`
- `structured_video_assessment`
- `timed_video_response_round`
- `video_questionnaire_round`

## 1. System Architecture

- Shared engine: `VideoInterviewExecutionEngine`
- Core components:
  - Video interview shell
  - Instructions/readiness
  - Device check engine
  - Practice recording engine
  - Question renderer
  - Prep timer engine
  - Recording engine
  - Upload/sync engine
  - Retake policy engine
  - Submission engine
  - Transcript/analysis linkage
  - Reviewer playback shell
  - Suspicious activity log
  - Recruiter review linkage
- Platform layers:
  - browser capture
  - recording session
  - chunk upload
  - media storage
  - transcript processing
  - evaluation/review
- Candidate and reviewer UI remain separate.

## 2. Database Design

Primary entities:

- `video_interview_attempt`
- `video_question_progress`
- `video_response_record`
- `video_upload_session`
- `video_chunk_log`
- `device_check_log`
- `suspicious_activity_log`
- `transcript_record`
- `video_score_breakdown`
- `video_result_summary`
- `resume_state`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `status`
- `started_at`
- `completed_at`
- `submitted_at`
- `auto_submitted_at`
- `last_seen_at`
- `question_id`
- `attempt_number`
- `retake_used`
- `upload_status`
- `recording_duration_seconds`
- `prep_duration_seconds`
- `storage_url`
- `transcript_status`
- `review_status`
- `integrity_flags`

## 3. API Structure

Candidate APIs:

- Start interview
- Run device check
- Save readiness state
- Fetch questions
- Start recording session
- Stop recording
- Upload chunk
- Finalize upload
- Save question completion
- Navigate next/previous
- Retake answer
- Autosave progress
- Resume interview
- Submit interview
- Force submit on timeout
- Fetch completion state

Processing APIs:

- Request transcript
- Fetch transcript status
- Request media processing
- Fetch processing status

Reviewer APIs:

- Fetch attempt status
- Fetch submitted attempts
- Fetch flagged attempts
- Fetch playback data
- Fetch transcript
- Fetch review shell
- Submit reviewer notes/scoring
- Mark integrity concern

## 4. UI Architecture

Candidate UI:

- Instructions screen
- Readiness/consent screen
- Camera and mic device check
- Practice recording
- Video interview shell
- Question panel
- Prep timer
- Recording timer
- Recording controls
- Upload/sync status
- Retake controls
- Progress navigator
- Submit confirmation
- Completed screen
- Interrupted/resume screen

Reviewer UI:

- Attempt status list
- Submitted attempts
- Flagged attempts
- Video playback shell
- Per-question review panel
- Transcript panel
- Notes and scoring shell
- Integrity flag panel
- Final decision linkage

## 5. Execution Flow

1. Candidate opens video interview.
2. Instructions, readiness, and consent are completed.
3. Device check runs.
4. Practice recording runs if enabled.
5. Real attempt starts.
6. Question is shown, prep timer runs, candidate records answer.
7. Recording uploads in chunks and finalizes.
8. Candidate progresses through all questions.
9. Resume restores exact question and upload state if interrupted.
10. Candidate submits or auto-submit runs.
11. Media processing and transcript pipeline start.
12. Reviewer reviews playback and scoring.
13. Result is stored and decision layer consumes it.

## 6. Edge Cases

- Disconnect during upload
- Browser refresh
- Camera denied
- Microphone denied
- Recording not saved
- Chunk upload failure
- Timeout during final upload
- Partial media recovery
- Duplicate session
- Expired interview window
- Empty question set
- Retake policy mismatch
- Media corruption after upload
- Reviewer opens before transcript ready
- Candidate reopens submitted attempt

## 7. Enterprise Features

- Shared per-question recorded interview engine
- Practice round support
- Prep and answer timing controls
- Retake policy enforcement
- Resumable chunk uploads
- Chunk-level integrity validation
- Transcript-ready architecture
- AI analysis-ready hooks
- Reviewer playback separation
- Media-safe recovery and audit trail

## 8. Integration Mapping

- `Video Question Engine`
- `Transcript Engine`
- `Scorecard Engine`
- `Decision Engine`
- `Candidate Interview Results`
- `Analytics Engine`
- `Automation Engine`
- `Media Storage / Processing Layer`

