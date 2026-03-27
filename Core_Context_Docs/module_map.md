cat > /home/nirav/projects/AI/docs/module_map.md << 'ENDOFFILE'
# Module Map — Talent Operating System
# Version: 2.0 — Updated with reviewer feedback
# Research Date: March 2026

## Document Purpose
Defines all modules of the Talent Operating System.
Each module is owned by exactly one agent during development.
No overlap between modules.
Modules communicate via events only — never direct function calls between modules.
All agents must reference this before building any feature.

---

## SYSTEM PHILOSOPHY

This is NOT an ATS.
This is a Talent Operating System (TOS).

Five engines power everything:
1. Data Engine — PostgreSQL + pgvector + Meilisearch
2. Event Engine — Celery + Redis + Django Signals
3. AI Engine — Ollama + pgvector + Whisper
4. Automation Engine — Rule engine + Trigger system
5. Communication Engine — Email + WhatsApp + WebSockets

---

## MODULE 1: CORE ATS ENGINE

### Purpose
The foundational recruitment workflow.
Jobs, applications, pipeline management.
This is the skeleton everything else connects to.

### Sub-modules
- Job requisition lifecycle (draft to closed)
- Job approval workflows
- Application management
- Pipeline kanban and list views
- Stage management and movement
- Offer management
- Joining management

### Events Emitted
- job.created, job.approved, job.published, job.closed
- application.submitted, application.stage_changed
- application.shortlisted, application.rejected
- offer.sent, offer.accepted, offer.rejected
- application.joined

### Connects To
All modules via events. Central hub of the system.

---

## MODULE 2: TALENT PASSPORT ENGINE

### Purpose
THE MOAT. Global portable professional identity for candidates.
The single feature no competitor has.
Everything revolves around candidate identity.

### Sub-modules
- Passport profile builder and management
- CV upload, parsing and normalization
- Profile versioning (full history of every change)
- Shareable link generation and management
- Granular privacy and visibility controls
- Data access log and audit trail
- Access revocation system (per viewer or bulk)
- One-click import for companies and agencies
- Passport public page for non-platform viewers
- Profile completeness scoring
- Heat score calculation
- Credential verification workflow

### Graph Data in Passport
Every passport stores relationship data:
- Candidate → worked_at → Companies
- Candidate → has_skill → Skills
- Candidate → placed_by → Agencies
- Candidate → interviewed_at → Companies
- Candidate → similar_to → Candidates (via pgvector)

This enables queries like:
"Find candidates similar to John Doe"
"Find candidates who worked at same company as this shortlisted candidate"
"Find candidates placed by agencies successful with this company"

### Events Emitted
- passport.created, passport.updated, passport.viewed
- passport.imported, passport.access_revoked
- passport.heat_score_updated, passport.credential_verified

### Connects To
Module 1 (ATS), Module 6 (AI), Module 3 (interviews), Module 9 (job search)

---

## MODULE 3: INTERVIEW ENGINE

### Purpose
Complete interview lifecycle management.
All interview types in one system.
Anti-cheat. AI scoring. Results to Passport.

### Interview Types
1. AI Screening — async, anytime, anywhere, AI evaluated
2. One-way Video — candidate records, company reviews later
3. Live Video — real-time, scheduled, recorded
4. Panel Interview — multiple interviewers, one candidate
5. Technical Assessment — coding, problem solving, live environment
6. Group Discussion — multiple candidates simultaneously
7. Psychometric Assessment — personality and aptitude
8. Case Study Interview — structured business problem
9. Mock Interview — candidate practice with AI feedback

### Sub-modules
- Interview template builder with question bank
- Threshold score configuration
- Auto-shortlist and auto-reject rules
- Interview scheduling with calendar sync
- Panel coordinator (assign multiple interviewers)
- Feedback collection from all panelists
- Interview recording storage (MinIO)
- Recording playback with transcript
- AI scoring and evaluation engine
- Anti-cheat behavioral analysis system
- Interview results sync to Talent Passport
- Interviewer performance tracking

### Anti-Cheat System
The 2025-2026 AI cheating crisis is real.
Our system detects:
- Screen capture and environment monitoring
- Eye tracking and attention pattern analysis
- Keystroke timing and typing pattern analysis
- AI-generated answer detection via linguistic fingerprinting
- Real-time behavioral confidence scoring
- Automatic flagging for human review
- Result integrity score shown to companies

### Events Emitted
- interview.scheduled, interview.started, interview.completed
- interview.cancelled, interview.no_show
- interview.feedback_submitted, interview.ai_scored
- interview.cheat_detected, interview.cheat_flagged

### Connects To
Module 1 (ATS), Module 2 (passport), Module 5 (automation), Module 10 (cafe)

---

## MODULE 4: COMMUNICATION ENGINE

### Purpose
All communication between all parties on the platform.
Email, WhatsApp, in-app, SMS, push notifications.
Single communication history per candidate per relationship.

### Sub-modules
- In-platform messaging (threaded, like email)
- Email integration and tracking (Gmail, Outlook)
- WhatsApp Business API integration (critical for India)
- SMS gateway integration (multiple providers per region)
- Push notification system (web and mobile)
- In-app notification centre
- Email template builder with variables
- Automated communication sequences
- Bulk communication tools
- Communication scheduling
- Read receipt and engagement tracking
- Communication history per candidate (full timeline)

### WhatsApp Integration Details
WhatsApp is non-negotiable for Indian market.
Features:
- Send job opportunities to candidates via WhatsApp
- Receive passport link via WhatsApp
- Interview scheduling confirmation via WhatsApp
- Stage update notifications via WhatsApp
- Two-way conversation (candidate replies tracked)
- Template messages for automated outreach
- Bulk WhatsApp campaigns for agencies

### Events Consumed
- application.shortlisted → send candidate notification
- interview.scheduled → send calendar invite to all parties
- deadline.overdue → send escalation notification
- offer.sent → send offer notification to candidate
- passport.viewed → notify candidate of new viewer

### Connects To
All modules consume communication engine.

---

## MODULE 5: AUTOMATION ENGINE

### Purpose
The operational backbone of the platform.
Rule-based workflows that eliminate manual coordination.
The 24-48 hour trigger system lives here.

### Core Concept
Every action in the platform has a consequence.
Instead of humans remembering to follow up,
the automation engine handles it automatically.

### Rule Engine Structure
Every rule follows this pattern:
IF [event] AND [conditions] THEN [actions] WITH [deadline]

### Built-in Rules (Active from Day 1)

Recruitment Rules:
- Application submitted AND no review in 24h → remind HR
- Candidate shortlisted AND no interview in 48h → remind HR, escalate to manager
- Interview completed AND no feedback in 24h → remind panelists
- Interview feedback in AND no stage decision in 24h → remind HR manager
- Offer sent AND no response in 48h → remind candidate
- Offer accepted AND no joining confirmed in 72h → remind HR
- Agency submitted candidate AND no acknowledgment in 24h → remind company HR
- Job approved AND not distributed to agencies in 24h → remind admin

Escalation Rules:
- Any deadline overdue AND assigned user not responded → escalate to manager
- Manager deadline overdue → escalate to department head
- Department head overdue → escalate to platform admin

Agency Rules:
- Agency SLA breached → reduce agency score, notify agency manager
- Agency submission quality below threshold → flag for review

Passport Rules:
- Passport not updated in 90 days → remind candidate
- Profile completeness below 60% → suggest completion steps

### Custom Rules (Phase 2)
Companies and agencies create their own rules.
Visual drag-and-drop rule builder (no code).
Examples:
- IF preferred agency submits AND score above 80 → auto-schedule phone screen
- IF candidate has 10+ years experience → assign to senior recruiter
- IF role is confidential → restrict visibility to specific team

### Automation Stack
- Rules stored in PostgreSQL (automation_rules table)
- Event listeners via Django signals + Celery
- Time-based checks via Celery Beat (runs every 5 minutes)
- Rule evaluation via Python rule engine
- Full execution log in audit_logs
- Failed automations in dead letter queue for manual review

### Events Consumed
All events from all modules.

### Events Emitted
- deadline.created, deadline.reminder_sent
- deadline.overdue, deadline.escalated, deadline.completed
- automation.rule_triggered, automation.action_taken

### Connects To
All modules. Automation engine listens to everything.

---

## MODULE 6: AI INTELLIGENCE LAYER

### Purpose
AI as a first-class system, not scattered features.
Powers matching, ranking, predictions, and copilot features.
Improves automatically as platform data grows.

### Components

#### Resume Parser
Input: CV file (PDF, Word, image, plain text)
Output: Structured JSON (name, skills, experience, education, contact)
Process: File extraction → LLM parsing → normalization → confidence scoring
Normalizes: Job titles, company names, skill names to standard forms
Stack: Ollama local model + custom extraction pipeline

#### Candidate Matching Engine
Input: Job requirements description
Output: Ranked candidate list with match scores and explanations
Process:
- Job vectorized via embedding model
- pgvector similarity search against all candidates
- Re-ranked by experience, location, availability, salary
- Explanation generated per match
Result: "Matched because: Python 5 years (required 3+), Django 3 years, Mumbai (required)"
Stack: pgvector + Ollama explanation generation

#### Similar Candidate Search (Graph Search)
Your requirement: "Find candidates similar to XYZ"
Input: Candidate ID or profile
Output: Top N similar candidates with similarity score and connection path
Process:
- Retrieve candidate embedding from pgvector
- Nearest neighbor search (cosine similarity)
- Filter by availability, location preferences
- Enrich with relationship data (shared agencies, companies, skills)
- Return ranked list with explanation of similarity
Example queries:
"Find candidates similar to this shortlisted candidate"
"Find candidates who worked at same companies as our best performers"
"Find candidates placed by agencies with good track record for this role"
Stack: pgvector cosine similarity + PostgreSQL relationship JOIN

#### Interview Intelligence
Input: Interview recording + candidate responses
Output: Comprehensive AI evaluation
Components:
- Whisper (OpenAI open source) for speech-to-text
- Answer quality scoring per question via Ollama
- Keyword and concept coverage mapping
- Communication and confidence scoring
- Comparison against successful past hires
- Anti-cheat behavioral score integration
Output stored in Talent Passport permanently

#### Recruiter Copilot
Features:
- Suggest top 10 candidates when job is posted
- Auto-generate personalized outreach emails
- Predict best time to follow up per candidate
- Predict time-to-fill based on similar past jobs
- Suggest salary range based on market data and past offers
- Flag stale applications that need attention
Stack: Ollama + ClickHouse historical patterns + PostgreSQL data

#### Hiring Success Prediction
Input: Candidate profile + Job requirements + Company history
Output: Probability of successful hire (0-100%)
How it learns:
- Every hire outcome stored (joined, left within 90 days, long-term retention)
- Model trained on platform's own historical data
- Improves accuracy as more data accumulates
- Starts useful at 1000 hires, very accurate at 10000+
Stack: Scikit-learn model + PostgreSQL historical outcomes

#### Profile Heat Score
Calculated daily for every candidate passport.
Factors:
- Profile completeness (20%)
- Verified credentials (25%)
- Interview performance scores (25%)
- Response rate and engagement (15%)
- Market demand for skills (15%)
Higher score = more visibility in recruiter searches
Updates: Celery Beat daily recalculation
Stack: Weighted formula + ClickHouse market demand signals

#### Market Demand Intelligence
Aggregates anonymized platform data to show:
- Which skills are in highest demand right now
- Which roles are hardest to fill
- Average time to fill by role and location
- Salary trends by role and region
Shown to: Candidates (career guidance) + Companies (benchmarking) + Agencies (strategy)

### Events Consumed
- candidate.created → trigger resume parsing
- interview.completed → trigger AI evaluation
- job.published → trigger candidate matching
- application.joined → record outcome for prediction model

### Events Emitted
- ai.resume_parsed, ai.candidate_ranked
- ai.match_scores_updated, ai.heat_score_updated
- ai.interview_evaluated, ai.prediction_calculated

---

## MODULE 7: ANALYTICS ENGINE

### Purpose
Data intelligence for all three user types.
Role-appropriate dashboards showing focused, relevant metrics.
Powers decision-making, not just reporting.

### Company Analytics
Primary metrics:
- Time to hire (by department, role, location, seniority)
- Funnel conversion rates (applied → screened → interviewed → offered → joined)
- Drop-off analysis (where candidates quit the process)
- Source of hire effectiveness (which channels bring best candidates)
- Agency performance comparison and ranking
- Cost per hire (when billing data available)
- Offer acceptance rates and reasons for rejection
- Interview-to-offer conversion per interviewer
- Diversity metrics (configurable, opt-in)
- Pipeline health (open positions, bottlenecks, overdue actions)

### Agency Analytics
Primary metrics:
- Recruiter performance dashboard (submissions, shortlists, placements)
- Client revenue tracking (future when billing added)
- Submission to selection ratio per client
- Time to fill per job type
- Source effectiveness (which channels bring placed candidates)
- Team productivity and target tracking
- Pipeline health per client

### Candidate Analytics (in Passport)
- Profile view count and trends
- Application status across all active applications
- Interview performance history and scores
- Profile heat score trend over time
- Skills in demand vs skills they have

### Platform Analytics (Admin)
- Platform growth (new tenants, users, candidates per day/week/month)
- Feature adoption rates
- User engagement and retention
- Most active tenants
- System health metrics

### Technical Stack
- Transactional counts: PostgreSQL
- Time-series analytics: ClickHouse
- Pre-aggregated metrics: Celery Beat jobs that run nightly
- Real-time counters: Redis
- Dashboard delivery: REST API to React frontend

---

## MODULE 8: AGENCY ERP

### Purpose
Complete business management for recruitment agencies.
Not just a recruitment tool — a full business operating system for agencies.

### Sub-modules
- Client company profiles and relationship management
- Client contact management and communication history
- Contract and SLA management per client
- Job management (received from clients)
- Internal recruiter management and assignment
- Team performance dashboards
- Candidate database management
- Candidate sourcing and tracking
- Submission management to clients
- Stage visibility (what company did with submitted candidate)
- Commission tracking (manual until billing module)
- Invoice management (manual until billing module)

### Agency-Specific Pipeline
Agency sees different pipeline than company:
- Sourcing → Screening → Submitted → Company Reviewing →
  Shortlisted → Interview Scheduled → Interview Done →
  Offered → Joined → Placed (Commission earned)

Each stage has its own 24-48 hour triggers.

### Events Emitted
- agency.candidate_submitted
- agency.client_relationship_changed
- agency.sla_breached
- agency.placement_confirmed

### Connects To
Module 1 (ATS), Module 2 (passport), Module 5 (automation), Module 7 (analytics)

---

## MODULE 9: INTERVIEW CAFE

### Purpose
Virtual real-time job fair with instant hiring capability.
First of its kind globally.
The feature that makes headline news.

### Concept
Candidate in Delhi interviews with company in Bangalore on Sunday evening.
No travel. No time off work. Hired in 30 minutes.

### Sub-modules
- Cafe session scheduling and management
- Company booth setup and management
- Live job listings during session
- Candidate registration and check-in
- Live CV screening by HR (shortlist or reject instantly)
- Interview queue management
- POS-style mission control (company view)
- Real-time WebSocket updates (queue positions, wait times)
- Interview room management
- Same-day offer capability
- Post-session analytics and hiring report
- Session recording for compliance

### POS Mission Control
Full-screen interface during live session.
Left: Queue of waiting candidates with passport data
Center: Active interview rooms (live status)
Right: Quick stats (applications, shortlisted, interviewed, offers)
Top bar: Session timer, live counts, alert bell, pause button
Real-time updates every second via WebSockets.
Drag candidates from queue to interview rooms.
Sound alert when candidate joins queue.

### Events Emitted
- cafe.session_started, cafe.session_ended
- cafe.candidate_registered, cafe.candidate_checked_in
- cafe.candidate_shortlisted, cafe.candidate_rejected
- cafe.interview_started, cafe.interview_completed
- cafe.offer_made

### Connects To
Module 1 (ATS), Module 2 (passport), Module 3 (interviews), Module 5 (automation)

---

## MODULE 10: JOB SEARCH AND DISCOVERY

### Purpose
Candidate-facing job discovery and application.
One-click apply using Talent Passport.

### Sub-modules
- Full-text job search (Meilisearch)
- Smart filters (role, location, work mode, salary, experience)
- Semantic job recommendations (pgvector matching)
- One-click apply via passport
- Application tracking dashboard
- Saved jobs and companies
- Job alerts via email and WhatsApp
- Company profile pages
- Salary insights and benchmarking
- Interview Cafe discovery and registration
- Career guidance based on market demand data

### Connects To
Module 2 (passport), Module 1 (ATS), Module 9 (cafe), Module 6 (AI)

---

## MODULE 11: COMMUNICATION HUB
(See Module 4 — Communication Engine)
Module 11 is the frontend interface for Module 4.
Inbox, thread view, notification centre, template management.

---

## MODULE 12: DOCUMENT MANAGEMENT

### Purpose
Secure management of all documents across all user types.

### Sub-modules
- CV storage and versioning
- Offer letter generation from templates
- Offer letter digital signing
- Contract management
- Background verification document collection
- Compliance document storage
- Document expiry tracking and alerts
- Secure document sharing with expiring links
- Document audit trail
- GDPR-compliant document deletion

---

## MODULE 13: ADMIN AND PLATFORM MANAGEMENT

### Purpose
Internal platform administration for us (the platform owner).
Also where all subscription limits are managed until billing is built.

### Sub-modules
- Tenant registration and verification
- Tenant suspension and termination
- Enterprise HQ verification and manual approval
- Tenant merger (branch to HQ linking)
- Feature flag management per tenant
- Usage limit management per tenant (replaces billing for now)
- Platform-wide settings
- User impersonation for support
- Platform analytics and growth metrics
- Audit log search and export
- Fraud detection alerts
- Manual verification workflows

### Feature Limit Management
Until billing module is built:
Every tenant has a tenant_settings record.
Admin sets limits per tenant manually:
- max_users
- max_jobs
- max_candidates
- max_agencies
- features_enabled (JSON object of feature flags)

This becomes the subscription enforcement layer later.
No code changes needed when billing is added —
billing module just updates tenant_settings automatically.

---

## MODULE 14: COMPLIANCE AND SECURITY

### Purpose
Platform-wide compliance and security management.

### Sub-modules
- GDPR compliance tools and right to erasure
- Data residency configuration per tenant
- Consent management and tracking
- Security audit logging
- Data encryption management
- Compliance reporting
- Privacy policy versioning
- Cookie and tracking consent

---

## MODULE 15: INTEGRATION LAYER

### Purpose
Connect platform with external tools.
API for enterprise customers.

### Built-in Integrations (Phase 2)
- Gmail and Outlook email sync
- Google Calendar and Outlook calendar
- Zoom, Google Meet, Teams
- WhatsApp Business API
- LinkedIn manual profile import
- Naukri, Indeed, Monster job posting

### API Platform
- REST API for all platform functions
- Webhook support for real-time events
- API key management with scoped permissions
- Developer documentation
- Sandbox environment

---

## MODULE 16: MOBILE APPLICATION (Phase 4)

### Purpose
Native mobile experience for all user types.

### Apps
- Candidate app (job search, passport, interviews)
- Recruiter app (pipeline, communication, tasks)
- Hiring manager app (approvals, interview feedback)

### Technology
- React Native for iOS and Android
- Shared component library with web
- Progressive Web App as immediate fallback (Phase 3)

---

## MODULE 17: MARKETPLACE ENGINE (Phase 4)

### Purpose
Transform platform from tool to network.
Agency discovery, recruiter marketplace, candidate visibility network.

### Sub-modules
- Agency directory and discovery
- Agency ratings and reviews
- Recruiter profiles and marketplace
- Candidate visibility network (opt-in)
- Talent pool communities
- Industry-specific talent networks

### Why This Is The Monopoly Move
Current state: Companies find agencies via referrals and word of mouth.
Our platform state: Companies discover, evaluate, and hire agencies on platform.
This creates massive lock-in.
Once companies manage agencies here, they never leave.

---

## MODULE DEPENDENCY MAP
Event Bus (Celery + Redis) — connects everything
Core ATS (1) ←→ All modules
Talent Passport (2) ←→ AI (6), Interviews (3), Job Search (10), ATS (1)
Interviews (3) ←→ ATS (1), Passport (2), Cafe (9), AI (6)
Communication (4) ← consumed by all modules
Automation (5) ← listens to all events, triggers all modules
AI Layer (6) ←→ Passport (2), Interviews (3), Analytics (7), Search
Analytics (7) ← reads from all modules
Agency ERP (8) ←→ ATS (1), Passport (2), Automation (5)
Interview Cafe (9) ←→ Interviews (3), ATS (1), Passport (2)
Job Search (10) ←→ Passport (2), ATS (1), AI (6)
Documents (12) ←→ ATS (1), Passport (2), Interviews (3)
Admin (13) → configures all modules
Compliance (14) → enforces rules on all modules
Integrations (15) ↔ all external connections
Mobile (16) → frontend for all modules
Marketplace (17) ←→ Agency ERP (8), Analytics (7)

---

## BUILD ORDER FOR AGENTS

Phase 1 — Foundation (Months 1-3):
Module 13: Admin and Platform Management (first — controls everything)
Module 1: Core ATS Engine
Module 8: Agency ERP
Module 2: Talent Passport Engine (basic)
Module 5: Automation Engine (built-in rules only)

Phase 2 — Core Features (Months 3-6):
Module 3: Interview Engine (all types)
Module 4: Communication Engine
Module 10: Job Search and Discovery
Module 6: AI Intelligence Layer (basic matching and parsing)
Module 7: Analytics Engine

Phase 3 — Differentiators (Months 6-9):
Module 9: Interview Cafe
Module 6: AI Intelligence Layer (advanced — predictions, copilot)
Module 12: Document Management
Module 15: Integration Layer
Module 5: Automation Engine (custom rules, visual builder)
Module 16: Progressive Web App

Phase 4 — Scale (Months 9-12):
Module 14: Compliance and Security (advanced)
Module 16: Mobile Apps (React Native)
Module 17: Marketplace Engine
Billing Module (designed but not started)

---

## KEY RULES FOR ALL AGENTS

1. Every module communicates via events — never direct function calls between modules
2. Every module has its own Django app in the backend
3. Every module has its own folder in the frontend
4. No module imports from another module directly (use shared utilities only)
5. Every action emits an event — even if nothing listens to it yet
6. Every module's data has tenant_id on all tables
7. Every module respects the 24-48 hour trigger system
8. Every module writes to audit_logs on all data changes
9. The automation engine owns all workflow logic — no workflow logic in other modules
10. The AI layer owns all intelligence — no AI logic scattered in other modules
ENDOFFILE