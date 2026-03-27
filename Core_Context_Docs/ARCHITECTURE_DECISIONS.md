# ARCHITECTURE_DECISIONS.md

# Talent Operating System — Architecture Decisions

# Version 1.0

---

# PURPOSE

This document tracks major architecture decisions.

This prevents:

* Decision conflicts
* Architecture drift
* AI confusion

All future development must follow these decisions.

---

# DECISION FORMAT

Each decision must include:

Decision ID
Title
Status
Decision
Reason
Impact

---

# DECISION 001 — Multi-Tenant Architecture

Status: Confirmed

Decision:

System uses multi-tenant architecture.

Tenant types:

* Company
* Agency

Reason:

System supports multiple organizations.

Impact:

All data must respect tenant boundaries.

---

# DECISION 002 — Candidate Global Entity

Status: Confirmed

Decision:

Candidate is global entity.

Candidate not owned by:

* Company
* Agency

Reason:

Candidate can work with multiple tenants.

Impact:

Candidate must exist system-wide.

---

# DECISION 003 — Shared Schema

Status: Confirmed

Decision:

System uses shared schema multi-tenant.

Reason:

Simplify architecture.

Impact:

Tenant filtering required.

---

# DECISION 004 — Backend Framework

Status: Confirmed

Decision:

Backend uses Django.

Reason:

Scalable and robust.

---

# DECISION 005 — Frontend Framework

Status: Confirmed

Decision:

Frontend uses React.

Reason:

Component-based architecture.

---

# DECISION 006 — Database

Status: Confirmed

Decision:

PostgreSQL database.

Reason:

Scalable and powerful.

---

# DECISION 007 — Candidate Entry Methods

Status: Confirmed

Decision:

Candidates can enter via:

* Company add
* Agency add
* Signup
* Link

---

# DECISION 008 — Automation First Architecture

Status: Confirmed

Decision:

System built automation-first.

Reason:

Enterprise workflows.

---

# DECISION 009 — Shared Master Data

Status: Confirmed

Decision:

Shared master tables for:

* Skills
* Country
* City
* Stages

---

# DECISION 010 — Event Driven Architecture

Status: Confirmed

Decision:

System emits events.

Example:

Candidate created
Interview scheduled

---

# FUTURE DECISIONS

New decisions must be added here.

---

# END OF FILE
