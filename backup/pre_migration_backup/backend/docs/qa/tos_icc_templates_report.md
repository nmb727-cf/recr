# ICC Templates Generation Report

## Overview
As part of the Intelligence Control Center (ICC) operationalization, a suite of 15 templates has been generated for each of the core modules to provide a production-ready starting point for tenants.

## 1. Job Registry Templates
- **Model**: `apps.jobs.models.JobRequisition`
- **Count**: 15
- **Template Roles**: Senior Software Engineer, Product Manager, UX Designer, DevOps Lead, Data Scientist, Marketing Manager, Sales Executive, HR Business Partner, Solutions Architect, Frontend Developer, Backend Developer, Mobile Engineer, QA Automation Engineer, Project Coordinator, Customer Success Manager.
- **Key Fields**: Unique `job_ref_id` (TPL-JOB-*), pre-configured job types, work modes, and experience ranges.

## 2. Prequalification Templates
- **Model**: `apps.prequalification.models.PrequalForm`
- **Count**: 15
- **Template Names**: Engineering Core Skills, Management Experience, Design Portfolio Review, Cultural Alignment, Technical Proficiency Test, Sales Target History, Logistics & Operations, Remote Work Readiness, Leadership Competency, Entry Level Aptitude, Executive Strategy, Security Compliance, Customer Handling Skills, Marketing Analytics, Agile Methodology.
- **Key Fields**: Linked `PrequalSection` and `PrequalQuestion` (e.g., "Years of relevant experience?").

## 3. Scorecard Templates
- **Model**: `apps.interviews.models.InterviewScorecardTemplate`
- **Count**: 15
- **Template Names**: Technical Coding Rubric, Soft Skills Evaluation, Leadership Assessment, System Design Grade, Behavioral Interview Scorecard, Sales Pitch Evaluation, Analytical Thinking, Team Collaboration Score, Product Strategy Matrix, Visual Design Critique, DevOps Knowledge, QA Process Audit, HR Policy Review, Client Interaction Score, Executive Presence.
- **Key Fields**: Linked `InterviewScorecardAttribute` (Technical Accuracy, Communication) with standard weights and scales.

## 4. Live Interview Templates
- **Model**: `apps.interviews.models.InterviewTemplate`
- **Count**: 15
- **Template Names**: Standard Coding Interview, Deep Dive Architecture, Behavioral Round 1, Hiring Manager Meet, UX Whiteboarding, Sales Simulation, Executive Strategy Session, HR Culture Round, Peer Technical Review, Final Leadership Interview, Case Study Discussion, Bug Squash Session, Product Thinking, Stakeholder Alignment, Team Fit Lunch.
- **Key Fields**: Pre-configured `duration_minutes` (60), instructions, and scoring types.

## Verification
- All templates are scoped to `tenant_id: f26e9892-d729-45a2-a673-4133ce3b4326`.
- Idempotency verified via `get_or_create`.
- Integrity constraints (unique `job_ref_id`) enforced.
