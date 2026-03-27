# CORE_SYSTEM_LOGIC.md

# Talent Operating System — Core System Logic

# Version 1.0

---

# 1. PURPOSE

This document defines the core business logic of the Talent Operating System.

This file defines:

* Candidate lifecycle
* Job lifecycle
* Agency lifecycle
* Interview lifecycle
* Communication logic
* Automation logic

This file ensures:

* System-wide logic consistency
* Module alignment
* AI development clarity

---

# 2. SYSTEM CORE ENTITIES

Primary system entities:

1. Candidate
2. Job
3. Company
4. Agency
5. Application
6. Interview
7. Offer
8. Placement

All system behavior revolves around these entities.

---

# 3. CANDIDATE CORE LOGIC

## 3.1 Candidate is Global Entity

Candidate is:

* Global user
* Not owned by company
* Not owned by agency

Candidate exists independently.

Tenant-level association allowed.

---

## 3.2 Candidate Entry Methods

Candidates can enter system via:

### Method 1 — Company Add

Company adds candidate:

* Quick form
* Detailed form
* Import from Link
* Adding resume parsing
* Share Link

Candidate receives:

* Notification
* Account creation request

---

### Method 2 — Agency Add

Agency adds candidate:

* Quick form
* Detailed form
* Import from Link
* Adding resume parsing
* Share Link

Candidate receives:

* Notification
* Account creation request

---

### Method 3 — Candidate Signup

Candidate signs up directly.

Candidate becomes:

* Global entity

---

### Method 4 — Candidate Link

Company/Agency sends link:

Candidate fills details.

---

## 3.3 Candidate Ownership Logic

Candidate is:

* Global entity (core level)
* Associated entity (tenant level)

Same candidate:

* Can belong to multiple companies
* Can belong to multiple agencies

---

# 4. CANDIDATE LIFECYCLE

Candidate lifecycle: only example it can be change based on tenant logic

Lead
↓
Screened
↓
Shortlisted
↓
Interview
↓
Offer
↓
Placed
↓
Joined

---

# 5. JOB CORE LOGIC

## 5.1 Job Creation

Jobs created by:

* Company
* Agency (if allowed)

Job includes: example but can be change based on tenant 

* Title
* Department
* Location
* Skills
* Experience

---

## 5.2 Job Lifecycle

Draft
↓
Approved
↓
Active
↓
Closed

---

## 5.3 Job Distribution

Jobs may:

* Stay internal
* Share with agencies

---

# 6. APPLICATION CORE LOGIC

Application created when:

* Candidate applied
* Company adds candidate to job
* Agency submits candidate

---

## 6.1 Application Lifecycle

Applied
↓
Screening
↓
Shortlisted
↓
Interview
↓
Offer
↓
Placed

---

# 7. AGENCY CORE LOGIC

## 7.1 Agency Relationship

Agency can:

* Invite company
* Be invited by company

Relationship created.

Multiple iteration and logic apply for commercial, retention, data sharing etc

---

## 7.2 Agency Candidate Submission

Agency submits candidate to job.

Submission includes:

* Candidate
* Job
* Notes
* Ownership rules

---

## 7.3 Candidate Protection

After submission:

Candidate protected for:

* Defined period
* Defined scope

Need system for resume secured and data secured

---

# 8. INTERVIEW CORE LOGIC

## 8.1 Interview Types

System supports:

* AI interview
* Live interview
* Panel interview
* One-way video

---

## 8.2 Interview Lifecycle

Scheduled
↓
Completed
↓
Feedback
↓
Decision

---

# 9. OFFER CORE LOGIC

Offer created after:

* Final interview

Offer lifecycle:

Draft
↓
Sent
↓
Accepted / Rejected

---

# 10. PLACEMENT CORE LOGIC

Placement occurs when:

* Candidate joins

Placement includes:

* Guarantee period
* Retention clause

---

# 11. COMMUNICATION CORE LOGIC

System communication:

* Email
* WhatsApp
* In-app

Communication triggers:

* Candidate added
* Interview scheduled
* Offer sent

---

# 12. AUTOMATION CORE LOGIC

System automation triggers:

Candidate added
↓
Send notification

Candidate shortlisted
↓
Schedule interview

Interview completed
↓
Collect feedback

These are only example so be prepare for every function logically

---

# 13. COMPANY CORE LOGIC

Company can:

* Create jobs
* Manage agencies
* Manage candidates
* Conduct interviews

---

# 14. DATA RELATIONSHIP LOGIC

Relationships:

Candidate → Application
Application → Job
Job → Company
Agency → Submission

---

# 15. SYSTEM EVENT LOGIC

Events:

Candidate created
Job created
Candidate shortlisted
Interview scheduled

---

# 16. CORE RULES

Candidate is global entity
Company and agency logic separate
Shared stages across system

---

# 17. FUTURE LOGIC EXTENSIONS

Future additions:

* AI scoring
* Automation engine
* Workflow engine

---

# END OF FILE
