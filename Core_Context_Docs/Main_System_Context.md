# SYSTEM_CONTEXT.md

# Talent Operating System — Master Context

# Version 1.0

---

# 1. PURPOSE OF THIS DOCUMENT

This document provides complete system understanding for any AI or developer working on this project.

This file must be read before:

* Designing features
* Writing backend logic
* Writing frontend logic
* Making architectural decisions

This file contains:

* System vision
* Architecture understanding
* Tech stack
* Infrastructure
* Core rules
* Design philosophy
* Decision log

This document does NOT contain:

* Session logs (see SESSION_CONTEXT.md)
* Module-specific logic (see module context files)
* Strict rules (see STRICT_RULES.md)

---

# 2. SYSTEM OVERVIEW

System Name: Talent Operating System (TOS)

This is NOT just an ATS.

This is a complete recruitment operating system connecting:

1. Companies
2. Agencies
3. Candidates

This creates a three-sided recruitment ecosystem.

---

# 3. SYSTEM PHILOSOPHY

The system is designed with enterprise-grade architecture from day one.

Core Philosophy:

* Enterprise-level architecture
* Modular design
* Event-driven architecture
* Multi-tenant SaaS architecture
* Automation-first approach
* AI-ready architecture
* Scalable design

---

# 4. CORE USER TYPES

Three main users:

## 4.1 Companies

Companies can:

* Create jobs
* Manage agencies
* Hire candidates
* Manage pipeline
* Conduct interviews

## 4.2 Agencies

Agencies can:

* Manage clients
* Submit candidates
* Track placements
* Manage recruitment workflow

## 4.3 Candidates

Candidates can:

* Create profile
* Manage passport
* Apply to jobs
* Attend interviews

---

# 5. SYSTEM ARCHITECTURE

Architecture Type:

* Multi-tenant SaaS
* Shared schema
* Tenant-based data isolation

Architecture Approach:

* Event-driven architecture
* Modular system
* Shared component architecture

---

# 6. TECH STACK

Backend:

* Django
* Django REST Framework

Frontend:

* React
* TypeScript

UI:

* Ant Design
* Tailwind CSS

Database:

* PostgreSQL

Search:

* pgvector
* Meilisearch (future)

AI:

* Ollama
* LLM integrations

---

# 7. INFRASTRUCTURE

Development Setup:

Single PC development environment

AI Used:

* ChatGPT
* Claude
* Gemini
* CLI AI tools

Testing:

* Automated testing system
* Documentation automation

---

# 8. KNOWLEDGE DOCUMENTS

Core Understanding Documents:

* architecture.md
* api_contracts.md
* database_schema.md
* features.md
* module_map.md
* ui_system.md
* user_personas.md
* market_research.md

These documents define:

* System architecture
* Database schema
* Features
* UI design
* User behavior

These must always be referenced.

---

# 9. DATABASE DESIGN PRINCIPLES

Core Database Rules:

* Multi-tenant architecture
* tenant_id on tenant-specific tables
* Soft delete only
* Audit logging
* UUID primary keys
* Metadata JSON support

Shared Master Data:

System must use shared master tables for:

* Skills
* Country
* City
* States
* Job stages
* Status
* Tags

These must remain consistent across system.

---

# 10. UI DESIGN PHILOSOPHY

UI must follow:

* Enterprise-level UX
* Clean layout
* Consistent components
* Shared UI components

Key UI Principles:

* Consistency across modules
* Dense but readable UI
* Side panel layout
* No duplicated UI logic

---

# 11. EVENT-DRIVEN SYSTEM

System uses event-driven architecture.

Examples:

* Candidate created
* Job created
* Candidate shortlisted
* Interview scheduled

These events trigger:

* Automation
* Notifications
* Workflow updates

---

# 12. MODULE ARCHITECTURE

System divided into modules:

Core Modules:

* Authentication
* Organization
* Candidates
* Jobs
* Pipeline
* Interviews
* Agencies
* Communication
* Automation
* Passport

Modules communicate via:

* Events
* Shared logic

---

# 13. AUTOMATION FIRST DESIGN

System built with automation-first approach.

Examples:

* Interview reminders
* Follow-ups
* SLA tracking
* Escalation rules

---

# 14. ENTERPRISE DESIGN PRINCIPLES

System must:

* Support large enterprises
* Support multi-team usage
* Support multi-location usage
* Support high data volume

---

# 15. DECISION LOG

Confirmed Decisions:

Architecture:

* Multi-tenant SaaS
* Shared schema

Backend:

* Django

Frontend:

* React

Database:

* PostgreSQL

UI:

* Ant Design

Development:

* Multi-AI assisted development

---

# 16. DEVELOPMENT APPROACH

Development Model:

* Feature based development
* Module context driven
* Strict rule enforcement

---

# 17. DOCUMENT STRUCTURE

Context System:

SYSTEM_CONTEXT.md
STRICT_RULES.md
CORE_SYSTEM_LOGIC.md
SESSION_CONTEXT.md

Module Context:

Each module has its own context file.

---

# 18. IMPORTANT NOTE

This system is being built incrementally.

Each feature must:

* Follow architecture
* Follow UI rules
* Follow DB rules
* Follow strict rules

---

# END OF FILE
