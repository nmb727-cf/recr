# ICC Phase 03: AI Interview Execution Engine

Prompt ID: `ICC-AI-INTERVIEW-EXECUTION-03`  
Project: `Talent Operating System`  
Module: `Interview Command Center`  
Phase Name: `Phase 03 - AI Interview Execution`

## Scope

Shared execution engine for:

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

Core components:

- AI Interview Execution Shell
- Instructions / Readiness Screen
- AI Conversation Engine
- Question Generation Engine
- Voice Engine
- Video Capture Engine
- Text Chat Engine
- Adaptive Flow Engine
- Response Capture Engine
- AI Scoring Engine
- AI Evaluation Engine
- Interview Timeline Engine
- Suspicious Activity Engine
- Recruiter Review Shell

Architecture:

- shared multi-modal engine
- prompt-layer + LLM-layer + STT/TTS + scoring/evaluation layers
- resume-aware conversation continuity
- JD-aware and resume-aware prompt assembly
- adaptive follow-up persistence per attempt
- candidate runtime separated from reviewer transcript/scoring shell

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

Required fields:

- `tenant_id`
- `candidate_id`
- `interview_id`
- `execution_id`
- `status`
- `started_at`
- `completed_at`
- `duration`
- `ai_model_used`
- `language`
- `confidence_score`
- `evaluation_status`

## 3. API Structure

Candidate APIs:

- start interview
- generate first question
- send candidate response
- generate follow-up
- fetch next question
- autosave
- resume interview
- submit interview
- fetch result

AI service APIs:

- generate question
- generate followup
- evaluate answer
- score answer
- summarize interview

Reviewer APIs:

- fetch interview
- fetch responses
- fetch score
- fetch AI evaluation
- flag interview

## 4. UI Architecture

Candidate UI:

- instructions screen
- readiness screen
- interview shell
- question panel
- response panel
- voice recording UI
- video recording UI
- chat UI
- progress indicator
- timer
- submit screen

Reviewer UI:

- interview review
- response playback
- AI scoring view
- evaluation breakdown
- confidence score
- flagged answers
- decision panel

## 5. Execution Flow

1. Candidate opens AI interview
2. Readiness validated
3. Attempt starts
4. AI generates first question
5. Candidate responds
6. Response saved and evaluated
7. AI generates follow-up or next question
8. Repeat until completion
9. Candidate submits or flow ends
10. AI scoring and summary run
11. Result stored
12. Reviewer reviews transcript, scores, flags

## 6. Edge Cases

- disconnect
- mic denied
- camera denied
- silence
- timeout
- refresh
- resume
- duplicate session
- expired window
- AI generation failure
- STT/TTS failure
- reviewer opens before evaluation complete
- submitted interview reopened

## 7. Enterprise Features

- adaptive questioning
- multi-language support
- confidence scoring
- suspicious signal logging
- future proctor-ready hooks
- reviewer override-ready architecture
- auditable generation/scoring trail

## 8. Integration Mapping

Connected systems:

- AI Builder
- Flow Engine
- Scorecard Engine
- Decision Engine
- Analytics Engine
- Automation Engine

