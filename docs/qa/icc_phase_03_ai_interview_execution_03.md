# Phase 03: AI Interview Execution Engine

Prompt ID: `ICC-AI-INTERVIEW-EXECUTION-03`  
Phase: `Interview Command Center / Execution Engine / Phase 03`  
Module: `AI Interview Execution Engine`

## Scope

Shared tenant-scoped AI interview runtime for:

- `ai_screening_interview`
- `ai_technical_interview`
- `ai_behavioral_interview`
- `ai_hr_interview`
- `ai_voice_interview`
- `ai_video_interview`
- `ai_chat_interview`
- `ai_adaptive_interview`
- `ai_case_interview`
- `ai_multi_round_interview`

## 1. System Architecture

- Shared engine: `AIInterviewExecutionEngine`
- Core components:
  - AI interview shell
  - Instructions/readiness
  - AI conversation engine
  - Question generation engine
  - Voice engine
  - Video capture engine
  - Text chat engine
  - Adaptive flow engine
  - Response capture engine
  - AI scoring engine
  - AI evaluation engine
  - Interview timeline engine
  - Suspicious activity engine
  - Recruiter review shell
- Modalities supported:
  - text
  - voice
  - video
  - hybrid
- Pipeline layers:
  - prompt assembly
  - LLM generation
  - STT
  - TTS
  - response analysis
  - scoring/evaluation
- Prompt set, evaluation config, and follow-up tree are attempt-bound and resume-safe.

## 2. Database Design

Primary entities:

- `ai_interview_attempt`
- `ai_interview_messages`
- `ai_response_records`
- `ai_followup_questions`
- `ai_interview_state`
- `ai_score_breakdown`
- `ai_score_summary`
- `ai_interview_result`
- `ai_resume_state`
- `ai_suspicious_activity_log`

Key fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `status`
- `started_at`
- `completed_at`
- `duration_seconds`
- `ai_model_used`
- `language`
- `confidence_score`
- `evaluation_status`
- `active_mode`
- `anti_cheat_flags`

## 3. API Structure

Candidate APIs:

- Start interview
- Generate first question
- Send response
- Generate follow-up
- Fetch next question
- Autosave
- Resume interview
- Submit interview
- Fetch result

Internal AI APIs:

- Generate question
- Generate follow-up
- Evaluate answer
- Score answer
- Summarize interview

Reviewer APIs:

- Fetch interview shell
- Fetch responses/transcript
- Fetch score
- Fetch AI evaluation
- Flag interview

## 4. UI Architecture

Candidate UI:

- Instructions screen
- Readiness screen
- Interview shell
- Question panel
- Response panel
- Voice recording UI
- Video recording UI
- Chat UI
- Progress indicator
- Timer
- Submit screen
- Completed screen

Reviewer UI:

- Interview overview
- Transcript and playback
- AI scoring view
- Evaluation breakdown
- Confidence score
- Flagged answers
- Decision panel

## 5. Execution Flow

1. Candidate opens AI interview.
2. Readiness and media checks run.
3. Attempt starts.
4. AI generates first question from prompt, JD, resume, and flow context.
5. Candidate responds in supported modality.
6. Response is normalized and saved.
7. AI evaluates and generates follow-up or next question.
8. Flow repeats until completion.
9. Submission or auto-completion triggers final summary and scoring.
10. Result is stored and reviewer opens dedicated review shell.

## 6. Edge Cases

- Internet disconnect
- Mic permission denied
- Camera denied
- Silence / long pause
- Timeout
- Browser refresh
- Resume interview
- Duplicate session
- Expired window
- AI generation failure
- STT failure
- TTS failure
- Background noise spike
- Reviewer opens before evaluation completion
- Candidate reopens submitted attempt

## 7. Enterprise Features

- Shared multimodal AI interview engine
- Adaptive questioning
- Resume-aware and JD-aware prompting
- Multi-language support
- Confidence scoring
- Suspicious signal logging
- Reviewer override-ready design
- AI proctor-ready integration points
- Audit logs for generation, capture, and scoring

## 8. Integration Mapping

- `AI Builder`
- `Flow Engine`
- `Scorecard Engine`
- `Decision Engine`
- `Analytics Engine`
- `Automation Engine`

