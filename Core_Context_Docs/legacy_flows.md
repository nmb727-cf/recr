# Legacy Recruitment Platform (Django 2021) - Business Logic & Flows

This document serves as a comprehensive guide for AI agents and developers to understand the legacy recruitment platform's business logic, user flows, and technical architecture.

---

## 1. System Architecture & Context
- **Framework:** Django (Python 3.9+)
- **Architecture:** Monolithic with specialized apps: `company`, `agency`, `candidate`, `accounts`, `chat`, `videochat`.
- **Primary Actors:** Companies (Employers), Agencies (Recruiters/Headhunters), Candidates (Job Seekers), and Internal Users (Recruiter staff).
- **Key Modules:** Applicant Tracking System (ATS), Assessment Engine (MCQ, Coding, Audio/Video, Descriptive, Image), Interview Management, Offer Negotiation.

---

## 2. Core User Roles & Permissions

### A. Company (Employer)
- **Goal:** Find and hire talent efficiently.
- **Powers:** Create jobs, configure multi-stage workflows, manage internal recruitment teams, invite/connect with agencies, view analytics, and issue offers.
- **Structure:** `Company` -> `Department` -> `Employee`.

### B. Agency (Third-party Recruiter)
- **Goal:** Source candidates for multiple companies and manage their own talent pool.
- **Powers:** Connect with companies, submit candidates to company jobs, manage internal database (`InternalCandidateBasicDetail`), and track recruiter performance (`DailySubmission`).
- **Unique Feature:** **Secure Resumes** (Redacted) to protect candidate contact info until a company expresses serious interest.

### C. Candidate (Job Seeker)
- **Goal:** Apply for jobs and showcase skills.
- **Powers:** Build rich profiles (QR-coded), take automated assessments, track application status, and negotiate offers.
- **Structure:** Multiple `Profiles` per user (e.g., one for Java Dev, one for Architect).

---

## 3. The "Golden Thread" Flow: From Job Creation to Hire

### Stage 1: Job Lifecycle
1. **Creation:** User creates a `JobCreation` entry. Key fields: title, type, salary (or "market rate"), experience, requirements, and `JCR` (Job Context Ratio) targets.
2. **Workflow Configuration:** The user assigns a `Workflows` sequence.
   - Example: `Application Review` -> `MCQ Assessment` -> `Technical Interview` -> `HR Interview`.
3. **Template Assignment:** Each stage is linked to a `Template_creation` (e.g., a specific Python MCQ exam or a specific Interview Scorecard).
4. **Recruiter Assignment:** Jobs are assigned to internal recruiters (`AssignInternal`) or external agencies (`AssignExternal`).

### Stage 2: Candidate Sourcing
1. **Direct Application:** Candidate applies via a job link.
2. **Agency Submission:** Agency recruiters submit a candidate from their internal database. 
   - **The "Secure" Flow:** Agency submits a `DailySubmission` with a redacted resume. The company must "Request Details" to see the full candidate profile.
3. **Internal Database:** Companies/Agencies can upload `InternalCandidate` records for future use.

### Stage 3: Assessment Engine (The Core IP)
The system relies heavily on automated screening:
- **MCQ:** Supports random/custom question papers, negative marking, and difficulty levels (Basic, Intermediate, Advanced).
- **Coding Assessment:** Supports Frontend (HTML/CSS/JS) and Backend coding with automated marking or manual rating.
- **Audio/Video Assessment:** Candidates record responses to prompts.
- **Image-based Assessment:** Questions/Answers involving image files.
- **Logic:** Scoring results (`ExamTemplate_result`, etc.) determine if a candidate meets the "Shortlist" threshold for the next stage.

### Stage 4: Interview & Tracking
1. **Scheduling:** `InterviewSchedule` handles the logistics (Date, Time, Participants, Interview Link).
2. **Scorecarding:** Interviewers use `InterviewScorecard` to rate candidates on specific criteria.
3. **Tracking:** The `Tracker` and `CandidateJobStagesStatus` models keep a real-time record of where a candidate is in the pipeline.

### Stage 5: Offer & Finalization
1. **Offer Generation:** `JobOffer` is created with designation, CTC, bond/NDA terms, and an offer letter file.
2. **Negotiation:** `OfferNegotiation` allows back-and-forth on terms (Joining date, salary).
3. **Closure:** Once accepted, the `CandidateJobStatus` is updated to "Hired," and the `JobCreation` status can be closed.

---

## 4. Recruitment Industry Specifics

### A. Candidate Ownership & Privacy
- **Secure Resumes:** Agencies use redacted resumes to prevent "candidate poaching" by companies.
- **Hide Fields:** Candidates can selectively hide their email, contact, or experience from public view until requested.

### B. Matchmaking Logic (JCR)
- **Job Context Ratio (JCR):** A custom matching algorithm (`JCR` and `JCRFill`) that compares candidate profiles against job requirements to provide a compatibility score.

### C. Agency-Company Partnerships
- **Connections:** `CompanyAgencyConnection` stores commission rates and contracts.
- **Job Requests:** Companies can specifically request an agency to work on a high-priority role.

---

## 5. Known Quirks & Incomplete Features

- **Duplicate Logic:** Many models are duplicated between `agency` and `company` apps (e.g., `Agency_Mcq_Exam` vs `Mcq_Exam`). This suggests a divergence in features between the two user types that was never unified.
- **"On-The-Go" Stages:** A simplified workflow system (`OnTheGoStages`) exists alongside the main templated `WorkflowStages`, likely for quick hiring without full assessment setups.
- **Legacy Components:** Some models like `Paragraph_subject` appear under-utilized compared to the more robust MCQ and Coding modules.
- **QR Profiles:** Candidate profiles have a built-in QR code generation logic for physical resumes to link back to the web profile.

---

*This document is generated by Gemini CLI for documentation purposes.*
