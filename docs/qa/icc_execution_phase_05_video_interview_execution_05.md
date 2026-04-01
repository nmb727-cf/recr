# ICC Phase 05: Video Interview Execution Engine

Prompt ID: `ICC-VIDEO-INTERVIEW-EXECUTION-05`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 05 - Video Interview Execution`

## Scope

Shared execution engine for:

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

Core components:

- Video Interview Execution Shell
- Instructions / Readiness Screen
- Device Check Engine
- Practice Recording Engine
- Question Renderer
- Prep Timer Engine
- Recording Engine
- Upload / Sync Engine
- Retake Policy Engine
- Submission Engine
- Transcript / Analysis Linkage
- Reviewer Playback Shell
- Suspicious Activity / Integrity Log
- Recruiter Review Linkage

Architecture:

- browser capture layer
- recording session layer
- chunk upload layer
- media storage layer
- transcript layer
- review/evaluation layer
- candidate runtime separated from reviewer playback shell

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
- `video_result_summary`
- `video_score_breakdown`
- `resume_state`

## 3. API Structure

Candidate APIs:

- start interview
- run device check
- save readiness state
- fetch questions
- start recording session
- stop recording
- upload chunk
- finalize upload
- save question completion
- next/previous question
- retake answer
- autosave progress
- resume interview
- submit interview
- force submit on timeout
- fetch completion state

Transcript / processing APIs:

- request transcript
- fetch transcript status
- request media processing
- fetch processing status

Reviewer APIs:

- fetch attempt status
- fetch submitted attempts
- fetch flagged attempts
- fetch playback data
- fetch transcript
- fetch review shell
- submit reviewer notes/scoring
- mark integrity concern

## 4. UI Architecture

Candidate UI:

- instructions
- readiness / consent
- camera + mic device check
- practice recording
- video shell
- question panel
- prep timer
- recording timer
- upload/sync status
- retake controls
- progress navigator
- submit confirmation
- completed screen
- interrupted/resume screen

Reviewer UI:

- attempt status list
- submitted attempts
- flagged attempts
- playback shell
- transcript panel
- per-question review
- notes/scoring shell
- integrity flag panel

## 5. Execution Flow

1. Candidate opens video interview
2. Instructions, readiness, consent
3. Device check
4. Practice recording
5. Real attempt starts
6. Question shown
7. Prep timer runs
8. Candidate records answer
9. Recording uploads and finalizes
10. Candidate continues through questions
11. Submit or auto-submit
12. Media processing and transcript pipeline start
13. Reviewer reviews playback/transcript
14. Score/result stored
15. Decision engine consumes outcome

## 6. Edge Cases

- disconnect during upload
- browser refresh
- camera denied
- microphone denied
- recording not saved
- chunk upload failure
- timeout during final upload
- partial media recovery
- duplicate session
- expired window
- empty question set
- retake mismatch
- corrupt media
- reviewer opens before transcript ready
- submitted attempt reopened

## 7. Enterprise Features

- per-question structured recording
- practice round support
- prep timer + answer timer
- resumable uploads
- chunk-level integrity validation
- transcript-ready architecture
- AI analysis-ready hooks
- tenant-scoped media governance
- full recording/upload audit trail

## 8. Integration Mapping

Connected systems:

- Video Question Engine
- Transcript Engine
- Scorecard Engine
- Decision Engine
- Candidate Interview Results
- Analytics Engine
- Automation Engine
- Media Storage / Processing Layer

