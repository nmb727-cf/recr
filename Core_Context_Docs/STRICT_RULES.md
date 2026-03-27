# STRICT_RULES.md

# Talent Operating System — AI Governance Rules

# Version 1.0

---

# 1. PURPOSE

This document defines strict development and design rules for the Talent Operating System.

All AI agents and developers must follow these rules.

These rules prevent:

* Architecture drift
* Data inconsistency
* UI inconsistency
* Logic duplication
* Broken enterprise workflows

These rules are mandatory.

---

# 2. ARCHITECTURE RULES

## 2.1 Multi-Tenant Rule

System is multi-tenant SaaS.

Every feature must:

* Respect tenant boundaries
* Never expose cross-tenant data
* Always use tenant-aware logic

---

## 2.2 Shared Architecture Rule

Company and Agency may share:

* UI components
* Layout
* Data structures

But logic must remain separate where required.

Same UI does NOT mean same logic.

---

## 2.3 Modular Architecture Rule

Each feature must belong to:

* One module only

Modules must not:

* Directly depend on each other
* Duplicate logic

Modules communicate via:

* Events
* Shared services

---

# 3. DESIGN RULES

## 3.1 Enterprise-Level UI Rule

UI must:

* Be consistent across system
* Use shared components
* Follow UI system guidelines

Do not create new UI patterns without approval.

---

## 3.2 Component Reuse Rule

Before creating:

* Form
* Table
* Modal
* Dropdown

Check if already exists.

Reuse existing component.

---

## 3.3 UI Consistency Rule

These must remain consistent:

* Layout
* Spacing
* Typography
* Colors
* Button styles

---

# 4. DATA CONSISTENCY RULES

## 4.1 Shared Master Data Rule

These fields must come from shared master tables:

* Skills
* Country
* City
* State
* Department
* Job stages
* Status
* Tags
* Roles
* Employment type
* Work mode

Never create duplicate dropdown values.

---

## 4.2 Repeated Fields Rule

If field appears in multiple modules:

It must be shared.

Examples:

* Skills
* Location
* Stages
* Status
* Tags

These must use shared data source.

---

## 4.3 Form Consistency Rule

If same form exists:

* Candidate form
* Job form
* Agency form

They must:

* Share logic
* Share validation
* Share structure

---

# 5. DEVELOPMENT RULES

## 5.1 Full Stack Rule

Every feature must include:

* Database
* Backend
* API
* Frontend

No backend-only features.

No frontend-only features.

---

## 5.2 No Duplicate Logic Rule

Before writing logic:

Check:

* Existing modules
* Shared logic
* Services

Reuse instead of duplicate.

---

## 5.3 Cross Module Validation Rule

When modifying:

* Candidate module

Check:

* Jobs
* Pipeline
* Agency
* Communication
* Automation

This prevents breaking system.

---

# 6. ENTERPRISE THINKING RULES

System must always consider:

* Large enterprise use
* Multi-team use
* Multi-location use
* Large data volume

Avoid:

* Single-user logic
* Hardcoded values
* Static dropdowns

---

# 7. AUTOMATION COMPATIBILITY RULE

All features must:

* Be automation friendly
* Emit events
* Support triggers

Example:

Candidate created → emit event

---

# 8. EVENT SYSTEM RULE

All major actions must:

Emit events.

Examples:

* Candidate created
* Job created
* Interview scheduled
* Candidate shortlisted

---

# 9. DATABASE RULES

## 9.1 No Hard Delete Rule

Use:

* Soft delete

Never:

* Hard delete data

---

## 9.2 Audit Rule

All critical changes must:

* Be auditable

---

## 9.3 Shared Fields Rule

Common fields must remain consistent:

* Country
* City
* Skills
* Stages

---

# 10. PERFORMANCE RULE

Avoid:

* Heavy queries
* Unoptimized joins

Design:

* Scalable queries

---

# 11. SECURITY RULES

Always enforce:

* Role based access
* Tenant access
* Permission validation

---

# 12. DOCUMENTATION RULE

After feature:

Update:

* Module context
* Core logic
* API contract (if required)

---

# 13. FEATURE COMPLETION RULE

Feature is complete only when:

* Backend built
* API built
* Frontend built
* Logic tested

---

# 14. SYSTEM CONSISTENCY RULE

Before marking feature complete:

Check:

* UI consistency
* Data consistency
* Logic consistency

---

# 15. DO NOT BREAK EXISTING FEATURES RULE

When adding feature:

* Do not modify unrelated modules
* Minimal changes only

---

# 16. SHARED LOGIC RULE

Common logic must go into:

* Shared services
* Shared modules

---

# 17. FUTURE SCALABILITY RULE

Design features with:

* Future scaling
* Multi-region support
* Multi-enterprise support

---

# 18. FINAL RULE

Always prioritize:

* Consistency
* Scalability
* Maintainability

Over:

* Quick fixes

---

# END OF FILE
