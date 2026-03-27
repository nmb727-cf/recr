
---

## EVENT-DRIVEN ARCHITECTURE (CRITICAL)

### Why Event-Driven
Without this the system breaks at scale.
Instead of calling functions in sequence:
"Call A then B then C"
We emit events:
"Emit event → multiple systems react independently"

This means:
- Adding new reactions to events requires zero code change to existing code
- Systems are decoupled — one failure does not cascade
- Real-time updates happen naturally
- The 24-48 hour trigger system is just event listeners

### Core Events

Candidate Events:
- candidate.created
- candidate.updated
- candidate.imported_from_passport
- candidate.duplicate_detected

Application Events:
- application.submitted
- application.stage_changed
- application.shortlisted
- application.rejected
- application.withdrawn
- application.offer_sent
- application.offer_accepted
- application.offer_rejected
- application.joined

Interview Events:
- interview.scheduled
- interview.started
- interview.completed
- interview.cancelled
- interview.no_show
- interview.feedback_submitted

Job Events:
- job.created
- job.approved
- job.published
- job.distributed_to_agencies
- job.closed

Agency Events:
- agency.invited
- agency.joined
- agency.candidate_submitted
- agency.sla_breached

Deadline Events:
- deadline.created
- deadline.reminder_due
- deadline.overdue
- deadline.escalated
- deadline.completed

Cafe Events:
- cafe.session_started
- cafe.candidate_checked_in
- cafe.candidate_shortlisted
- cafe.interview_started
- cafe.offer_made

Passport Events:
- passport.viewed
- passport.imported
- passport.access_revoked
- passport.updated

### Event Processing Stack
Event producer: Django signals + explicit event publishing
Event broker: Redis (Celery broker)
Event consumers: Celery workers (async)
Real-time delivery: Django Channels (WebSocket push to browser)

### Event Flow Example
Candidate shortlisted:
1. HR clicks Shortlist button
2. Application status updated in PostgreSQL
3. application.shortlisted event emitted
4. Celery worker: Schedule interview within 48 hours (create deadline)
5. Celery worker: Notify candidate via email and in-app
6. Celery worker: Notify agency if agency submission
7. Celery worker: Update ClickHouse analytics
8. Django Channels: Push real-time update to HR dashboard
9. Meilisearch: Update candidate search index
All steps happen independently and asynchronously.
If step 6 fails, steps 4,5,7,8,9 still succeed.

---

## AI LAYER — PRODUCT AI (Not Agent AI)

### Two AI Systems (Important Distinction)
1. Development AI: Ollama agents that BUILD the platform (our multi-agent system)
2. Product AI: AI features INSIDE the platform that users interact with

This section covers Product AI — the AI that candidates, recruiters, and companies use.

### Product AI Components

#### Resume Parser
Input: CV file (PDF, Word, image)
Output: Structured JSON with all candidate data
Process:
- File text extraction
- LLM-based entity extraction (name, skills, experience, education)
- Normalization (standardize skill names, job titles, company names)
- Confidence scoring per extracted field
- Human review flag for low-confidence extractions
Stack: Ollama local model + custom parsing pipeline

#### Candidate Matching Engine
Input: Job requirements
Output: Ranked candidate list with match scores
Process:
- Job requirements vectorized
- Candidate profiles vectorized
- pgvector cosine similarity search
- Re-ranking based on experience, location, availability
- Explanation generation ("Matched because: Python 5 years, Django 3 years")
Stack: pgvector + Ollama for explanation generation

#### Similar Candidate Search (Graph Search)
Input: Candidate ID
Output: Top N similar candidates
Process:
- Candidate embedding retrieved from pgvector
- Nearest neighbor search
- Filter by availability and other criteria
- Relationship enrichment (shared agencies, companies, skills)
Query example:
"Find candidates similar to John Doe"
"Find candidates who worked at same companies as shortlisted candidates"
"Find candidates placed by agencies that have success with this company"
Stack: pgvector cosine similarity + PostgreSQL relationship tables

#### Interview Intelligence
Input: Interview recording + transcript
Output: AI evaluation scores + insights
Components:
- Speech-to-text transcription
- Answer quality scoring per question
- Keyword and concept mapping
- Confidence and communication scoring
- Anti-cheat behavioral analysis
- Comparison against successful past hires (learning over time)
Stack: Whisper (speech-to-text) + Ollama (scoring) + custom behavioral analysis

#### Recruiter Copilot
Features:
- Suggest top candidates for a job based on history
- Auto-generate candidate outreach emails
- Auto-suggest follow-up timing
- Predict time-to-fill based on historical data
- Suggest salary range based on market and past offers
Stack: Ollama + historical data from PostgreSQL + ClickHouse patterns

#### Hiring Success Prediction
Input: Candidate + Job combination
Output: Probability of successful hire (0-100%)
Trained on: Platform's historical hire outcomes over time
Improves automatically as more data accumulates
Stack: Scikit-learn model + PostgreSQL historical data + Ollama for insights

#### Profile Heat Score (Candidate Passport)
Factors:
- Profile completeness (20%)
- Verified credentials (25%)
- Interview performance scores (25%)
- Response rate and engagement (15%)
- Market demand for skills (15%)
Updates: Recalculated daily via Celery Beat
Stack: Weighted formula + ClickHouse market demand data

---

## AUTOMATION ENGINE (Core Module)

### Philosophy
The 24-48 hour trigger system is NOT just a feature.
It is a full rule engine that runs the operational backbone of the platform.

### Rule Engine Structure
Every rule follows this pattern:
IF [event] AND [conditions] THEN [actions]

Examples:
IF application.stage_changed AND new_stage = shortlisted AND no_interview_scheduled
THEN create_deadline(assign_to=hr_manager, hours=48, action=schedule_interview)

IF deadline.overdue AND action=schedule_interview
THEN escalate_to(hiring_manager) AND notify(recruiter) AND log_to_audit

IF interview.completed AND feedback_not_submitted AND hours_elapsed > 24
THEN remind(panelists) AND create_escalation_deadline(hours=24)

IF agency.candidate_submitted AND no_response AND hours_elapsed > 48
THEN remind(hr_manager) AND notify(agency)

IF offer.sent AND no_response AND hours_elapsed > 48
THEN remind(candidate) AND notify(hr_manager)

### Built-in Rules (Phase 1)
All rules below are pre-configured and active from day one:

| Trigger | Condition | Action | Deadline |
|---------|-----------|--------|----------|
| Application submitted | No review | Remind HR | 24 hours |
| Candidate shortlisted | No interview scheduled | Remind HR, Escalate | 48 hours |
| Interview completed | No feedback | Remind panelists | 24 hours |
| Offer sent | No response | Remind candidate | 48 hours |
| Offer accepted | No joining confirmed | Remind HR | 72 hours |
| Agency submitted | No acknowledgment | Remind company HR | 24 hours |
| Job approved | Not distributed to agencies | Remind admin | 24 hours |
| Deadline overdue | Assigned user inactive | Escalate to manager | Immediate |

### Custom Rules (Phase 2)
Companies and agencies can create custom rules.
Visual rule builder interface (drag and drop).
No code required.
Examples of custom rules companies create:
- IF candidate from preferred agency THEN auto-shortlist for phone screen
- IF candidate has 5+ years experience THEN assign to senior HR manager
- IF position is confidential THEN restrict to specific team only

### Rule Engine Stack
Rules stored in PostgreSQL (rules table)
Evaluated by Celery workers on every event
Complex conditions use Django Q objects
Scheduling via Celery Beat for time-based checks
Full execution log in audit_logs table

---

## SEARCH ARCHITECTURE

### Two Search Systems Working Together

#### 1. Meilisearch (Full-Text Search)
Use for: Name, title, company, skill keyword search
Example queries:
- "Find candidates named Rahul in Mumbai"
- "Find jobs with React in Bangalore"
- "Find agencies specializing in IT recruitment"
Speed: Under 50ms
Typo tolerant: Yes ("Pythn" finds "Python")

#### 2. pgvector (Semantic and Similarity Search)
Use for: Meaning-based and similarity search
Example queries:
- "Find candidates similar to this shortlisted candidate"
- "Find jobs that match this candidate's profile"
- "Find candidates who would be good for this role even if they don't use exact keywords"
Speed: Under 100ms for 1 million records

#### Combined Search (Most Powerful)
For complex queries both systems work together:
- Meilisearch filters by keywords first (fast, narrows to 1000 candidates)
- pgvector re-ranks by semantic similarity (smart, finds best matches)
- PostgreSQL relationship data enriches results
- Result: Fast, intelligent, relationship-aware search

---

## MULTI-TENANT ARCHITECTURE

### Approach: Shared Schema with Row Level Security
- tenant_id on every table (denormalized intentionally)
- PostgreSQL RLS enforces isolation at database level
- PgBouncer manages connection pooling
- Citus-ready for horizontal sharding when needed

### Enterprise Hierarchy
- Every company gets master_id and tenant_id
- Branch signs up independently → gets own tenant_id
- When HQ joins → branch tenant_ids linked to HQ master_id
- HQ gets global analytics view across all branches
- HQ defines governance policies (forced or flexible per branch)
- Admin panel handles manual verification and merging

### Growth Path (Cost-Aware)
Phase 1 (0-10k tenants): Single PostgreSQL + PgBouncer
Cost: Zero, already your hardware

Phase 2 (10k-100k tenants): Add read replica on i5 or spare PC
Cost: Zero, use existing machines

Phase 3 (100k+ tenants): Activate Citus extension (free, open source)
Cost: Just add more PCs, no code changes

Phase 4 (millions): Managed cluster or cloud
Cost: Covered by revenue at this point

---

## SECURITY AND TRUST LAYER

### Identity Verification
- Email verification on registration
- Phone verification via OTP
- Document verification for enterprise tenants (manual, admin-reviewed)
- Passport credential verification (employer verification of work history)

### Fraud Detection
- Fake candidate profile detection via:
  - Duplicate detection (same email, phone, profile across tenants)
  - CV inconsistency scoring (AI flags suspicious CVs)
  - Behavioral pattern analysis (too many applications too fast)
- Fake agency detection via:
  - Registration document verification
  - GST number verification for Indian agencies
  - Activity pattern monitoring

### Anti-Cheat for Interviews
- Screen capture and environment monitoring
- Eye tracking and attention analysis
- Keystroke and typing pattern analysis
- AI-generated answer detection via linguistic analysis
- Real-time behavioral scoring
- Flagging for manual review
- Integrity score shown to companies

### Data Security
- TLS 1.3 for all data in transit
- AES-256 for sensitive fields at rest
- JWT 15 minute expiry with refresh token rotation
- Rate limiting on all endpoints
- Input validation and sanitization
- ORM only — no raw SQL

### RBAC (Granular)
Every permission is individually configurable:
- View permission (can see the data)
- Create permission (can add new records)
- Edit permission (can modify existing records)
- Delete permission (soft delete only)
- Export permission (can download data)
- Admin permission (can change settings)

Roles are composable — create custom roles from individual permissions.
Pre-built roles: super_admin, tenant_admin, hr_manager, recruiter, interviewer, viewer, candidate

---

## INTEGRATION LAYER

### Phase 2 Integrations
- Gmail and Outlook sync (email tracking)
- Google Calendar and Outlook calendar (interview scheduling)
- Zoom, Google Meet, Teams (video interviews)
- WhatsApp Business API (critical for India)
- LinkedIn (manual profile import via extension initially)
- Naukri, Indeed, Monster (job posting)

### Phase 3 Integrations
- Background verification providers
- Digital signature providers
- SMS gateways (multiple providers per region)

### Future Integrations
- HRMS systems (Workday, SAP, Darwinbox)
- Payroll systems
- Campus recruitment platforms

### API for Enterprise
- REST API for all platform functions
- Webhook support for real-time events
- API key management with scoped permissions
- Rate limiting and usage analytics
- Developer documentation and sandbox

---

## INFRASTRUCTURE

### Current Development
Omen i9 32GB RTX5070 (192.168.1.11)
Ollama qwen2.5-coder:7b (GPU) — development AI
Redis (Docker port 6379) — cache, queue, channels
MinIO (Docker port 9000/9001) — file storage
ClickHouse (Docker port 8123) — analytics
Langfuse (Docker port 3000) — agent monitoring
Meilisearch (Docker port 7700) — full text search
Django dev server (port 8000)
React Vite dev server (port 5173)
CrewAI agents — development automation
DB PC (192.168.1.17)
PostgreSQL 17 (port 5432) — main database
PgBouncer (port 6432) — connection pooling (install soon)
pgvector extension — vector and graph search
agent_memory_db — agent knowledge base
recruitment_platform — main app database
langfuse database — monitoring data

### Next Infrastructure Steps
1. Install PgBouncer on DB PC (critical, do this soon)
2. Add Meilisearch to Omen Docker Compose
3. Set up static IP on DB PC (prevent IP changing again)

---

## MODULE ARCHITECTURE (Strict Separation for Agents)

Each module is owned by one agent during development.
No overlap between modules.
Communication between modules via events only.
Module 1: Core ATS Engine
Jobs, Applications, Pipeline, Companies
Module 2: Talent Passport Engine (THE MOAT)
Candidate identity, CV parsing, Access control, Sharing, Versioning
Module 3: Interview Engine
All interview types, AI evaluation, Recording, Anti-cheat
Module 4: Communication Engine
Email, WhatsApp, In-app chat, Notifications, SMS
Module 5: Automation Engine
Rule engine, 24-48 hour triggers, Event listeners, Workflows
Module 6: AI Intelligence Layer
Matching engine, Ranking, Graph search, Hiring prediction, Copilot
Module 7: Analytics Engine
Funnel metrics, Recruiter performance, Agency scoring, Insights
Module 8: Agency ERP
Agency management, Client relationships, Team ERP, Billing tracking
Module 9: Interview Cafe
Virtual job fair, POS mission control, Queue management
Module 10: Marketplace Engine (Phase 4)
Agency discovery, Recruiter marketplace, Candidate network

---

## DECISIONS LOG

| Decision | Choice | Reason |
|----------|--------|--------|
| Backend | Django 6.0 | Enterprise sweet spot, Instagram scale proven |
| Frontend | React 18 | Best for authenticated dashboards |
| UI | Ant Design + Tailwind | Data density + beautiful design |
| Primary DB | PostgreSQL 17 | Most popular 2025, multi-tenant, pgvector built in |
| Graph search | pgvector + PostgreSQL relationships | Already running, handles all graph queries, migrate to FalkorDB at scale |
| Full text search | Meilisearch | Lightweight, fast, typo-tolerant, self-hosted free |
| Multi-tenancy | Shared schema + RLS | Citus-ready, scales to millions of tenants |
| Connection pooling | PgBouncer | 81% latency improvement, 100x connections |
| Event system | Django signals + Celery | Decoupled, async, scales with Redis |
| Queue broker | Redis now, Kafka later | Redis handles millions of events/day, Kafka when truly needed |
| AI product layer | Ollama + pgvector + Whisper | Zero cost, self-hosted, improves with data |
| Cache | Redis | Industry standard, dual use |
| File storage | MinIO | Self-hosted, S3-compatible, zero cost |
| Analytics | ClickHouse | Best analytical query performance |
| Real-time | Django Channels + WebSockets | Instagram 2 billion users proven |
| Mobile future | React Native | Shared knowledge with React |
| Build tool | Vite | 60ms HMR, industry standard 2026 |
ENDOFFILE