# SYSTEM_GLOSSARY.md

# Talent Operating System — System Glossary

# Version 1.0

---

# PURPOSE

This document defines system-wide terminology.

This prevents:

* AI misunderstanding
* Developer confusion
* Logic inconsistencies

All modules must follow these definitions.

---

# CORE ENTITIES

## Candidate

A candidate is a global entity.

A candidate:

* Exists independently
* Not owned by company
* Not owned by agency
* Can be associated with multiple tenants

Candidate is system-level user.

---

## Company

Company is hiring organization.

Company can:

* Create jobs
* Invite agencies
* Hire candidates

Company is tenant.

---

## Agency

Agency is recruitment partner.

Agency can:

* Submit candidates
* Work with companies
* Track placements

Agency is tenant.

---

## Tenant

Tenant is isolated workspace.

Tenant can be:

* Company
* Agency

Tenant isolation enforced.

---

# RECRUITMENT ENTITIES

## Job

Job is hiring requirement.

Job belongs to:

* Company
* Agency (if allowed)

---

## Application

Application created when:

* Candidate applied to job

Application belongs to:

* Candidate
* Job

---

## Submission

Submission created when:

* Agency submits candidate

Submission includes:

* Candidate
* Job
* Agency

Submission different from application.

---

## Pipeline

Pipeline tracks candidate progress.

Stages:

* Applied
* Shortlisted
* Interview
* Offer

Pipeline belongs to:

* Job

---

## Stage

Stage is recruitment step.

Examples:

* Applied
* Screening
* Shortlisted

Stages should be configurable.

---

# INTERVIEW ENTITIES

## Interview

Interview scheduled for candidate.

Types:

* AI Interview
* Live Interview
* Panel Interview

---

## Interview Round

Interview round within interview.

Example:

* Technical round
* HR round

---

# OFFER ENTITIES

## Offer

Offer created after selection.

Offer lifecycle:

* Draft
* Sent
* Accepted

---

## Placement

Placement occurs when:

Candidate joins company.

---

# COMMUNICATION ENTITIES

## Message

Communication message.

Types:

* Email
* WhatsApp
* In-app

---

## Template

Reusable communication template.

---

# AUTOMATION ENTITIES

## Trigger

Event that starts automation.

Example:

* Candidate created

---

## Workflow

Automation workflow.

Example:

* Interview scheduling

---

# RELATIONSHIP ENTITIES

## Agency Relationship

Relationship between:

* Agency
* Company

---

## Candidate Protection

Protection applied after:

* Agency submission

---

# DATA ENTITIES

## Master Data

Shared data across system:

* Skills
* Country
* City
* Stages
* Tags

---

# SYSTEM CONCEPTS

## Global Entity

Entity exists system-wide.

Example:

* Candidate

---

## Tenant Entity

Entity belongs to tenant.

Example:

* Job

---

# FUTURE ENTITIES

Future additions:

* Talent Passport
* Talent Marketplace
* AI scoring

---

# END OF FILE
