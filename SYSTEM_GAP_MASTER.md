# SYSTEM_GAP_MASTER.md

## 1. Executive Summary
- Consolidation source: all `*_VERIFICATION_REPORT.md` files present in repo root.
- Reports found: `ADMIN`, `AGENCY`, `AUTH`, `COMPANY`, `SEARCH`, `RESUME_PARSER`, `CANDIDATE_MATCHING`, `GRAPH_SEARCH`, `INTERVIEW_INTELLIGENCE`, `RECRUITER_COPILOT`, `HIRING_SUCCESS`, `PROFILE_HEAT_SCORE`, `MARKET_INTELLIGENCE`.
- Expected-but-missing reports in current workspace: `CANDIDATE_VERIFICATION_REPORT.md`, `PIPELINE_VERIFICATION_REPORT.md`, `INTERVIEW_VERIFICATION_REPORT.md`, `OFFER_VERIFICATION_REPORT.md`, `MESSAGING_VERIFICATION_REPORT.md`, `NOTIFICATION_VERIFICATION_REPORT.md`, `AUTOMATION_VERIFICATION_REPORT.md`, `EVENT_SYSTEM_VERIFICATION_REPORT.md`, `ANALYTICS_VERIFICATION_REPORT.md`.
- Overall state:
  - Phase 1 core platform is mostly operational but has critical reliability/security gaps (endpoint mismatches, tenant-safety risk patterns, missing admin control surfaces).
  - Phase 2 intelligence foundation is largely incomplete (vector/semantic/graph/search, resume parsing, interview AI scoring, heat score engine).
  - Phase 3 prediction/intelligence modules are mostly heuristic placeholders, not true trained/continuous systems.
- System trust level: **moderate for internal engineering validation**, **low for external pilot with intelligence-heavy claims**.

## 2. Module-by-Module Completion Status

| Module | Completion | Complete Items | Partial Items | Missing Items | Logic Issues | Architecture Issues | UI/Discoverability Issues | Phase Blockers |
|---|---:|---|---|---|---|---|---|---|
| Auth & Roles | 78% | Unified login/registration/OTP/RBAC/tenant scoping | Multi-user invite flow, candidate creation lifecycle | `agency_sourcer` role | manual tenant-filter risk, dedupe edge paths | role string coupling, public-tenant candidate sensitivity | agency roles absent in invite UI | P1 quality + security hardening |
| Company | 74% | Job/pipeline/agency/interview/offer basics | shallow clone, bulk-stage ops, fragmented offer UI | job renewal depth, advanced approval depth | ownership conflict edge cases | offer logic fragmented across modules | offer UX fragmented | P1 stabilization |
| Agency | 62% | Relationship/assignment/submission/performance core | filtering/export/trends, docs upload, dashboard route | team mgmt APIs/model, reactivation endpoint, submission governance endpoint, internal recruiter assignment | resend invite bug, stale submission count, potential score exposure | missing agency membership model; frontend/backed endpoint drift | dashboard unrouted, guarantee UI absent | **P1 blockers active** |
| Admin | 58% | tenant creation/status/isolation, usage limit primitives | master data/admin audit workflow | master admin UI, platform analytics, fraud engine | schema auto-create bypasses approval workflow | free-text master data risks analytics | no super-admin screens | P1 + P2 blockers |
| Search | 52% | SQL instant multi-field filtered search with tenant scope | no global unified search, partial advanced filters | typo tolerance, semantic/vector, Meilisearch indexing | scale bottlenecks | docs vs implementation mismatch | no command-style global discovery | P1 typo/global search; P2 engine/vector |
| Resume Parser | 28% | storage fields + orchestration placeholders | none | actual parsing/transcription/normalization/confidence/human review | dead automation path for candidate-created trigger | missing media/OCR dependency architecture | upload flow disabled | P2 blocker |
| Candidate Matching | 49% | heuristic match engine + UI + basic explanation/actions | AI prompt exists but not operational; limited reranking | salary/availability/employment fit, vector semantics | Python-loop scaling, dual heuristic divergence, frontend default score bias | not event-driven/intelligence-hub integrated | none critical | P2 blocker |
| Graph Search | 12% | prerequisites only (candidate metadata/global hash) | none | full similarity/relationship engine + APIs | documentation overpromise | no graph/vector substrate | no UI entrypoints for similar candidates | P2 blocker |
| Interview Intelligence | 43% | AI/human score fields, anti-cheat telemetry, config surfaces | summary prompt placeholders | STT pipeline, per-question AI scoring, keyword/concept mapping | ai_score mostly unused in completion flow | no media processing pipeline | AI metrics not surfaced well | P2 blocker |
| Profile Heat Score | 36% | score fields + completeness calc + basic display | completeness suggestions, verification/interview fields present | weighted multi-factor daily recalculation, trend/history, heat explainability | heat behaves placeholder; market-demand label mismatch; candidate-global matching sensitivity | no scoring service/batch engine/factor integration | heat not visible in primary recruiter/company flows; no trend charts | P2 + P3 blockers |
| Hiring Success Prediction | 34% | match score field + heuristic scoring + missing-skills output | explanation/range only partial | trained model, confidence score, continuous learning, required feature ingestion | work-mode field bug; payload mismatch; possible wrong submit path; AI-labeling risk | no model registry/feature store/training path | prediction confidence absent in UI | P3 blocker |
| Recruiter Copilot | 46% | stale flags, time-to-fill heuristics, suggestion surfaces | outreach/follow-up logic exists but detached | actionable in-context copilot sidebar and workbench wiring | heuristics marketed as AI; suggestions trapped in separate hub | dashboard tied to mocks not real AI suggestions | intelligence hidden from daily recruiter flow | P3 blocker |
| Market Intelligence | 22% | basic analytics infra + source entities | time-to-hire signal only | in-demand skills by region, role difficulty, salary trends, benchmark engine, data pipeline | hardcoded analytics values (e.g., 24 days, fixed rates/health) | no market intelligence domain model/pipeline | no job-create/recruiter market surfaces | P3 blocker |

### 2.1 Normalized Notes Per Module
- Each module above already normalized into: complete, partial, missing, logic, architecture, UI/discoverability, phase blockers.
- Reports unavailable in repository were not inferred and remain **unassessed**.

## 3. Foundation Blockers
These must be fixed before high-confidence reliance on advanced modules.

1. **Tenant-safety enforcement model is fragile (manual filtering pattern).**
- Severity: CRITICAL
- Type: RBAC/Security, Business Logic
- Why foundation: repeated manual `.filter(tenant_id=...)` pattern is leak-prone as codebase grows.

2. **Frontend/backed contract drift on core agency workflows (404 endpoints).**
- Severity: CRITICAL
- Type: Backend/API, UI/UX, Workflow/Automation
- Why foundation: users invoke non-existent APIs for relationship reactivation, recruiter assignment, submission governance.

3. **Agency performance data exposure scope gap (`agency_id` query risk).**
- Severity: CRITICAL
- Type: RBAC/Security
- Why foundation: sensitive partner metrics potentially queryable beyond authorized scope.

4. **Candidate identity lifecycle inconsistency (lazy candidate record creation after signup).**
- Severity: HIGH
- Type: Data Model, Business Logic
- Why foundation: weakens reliability of downstream pipeline/search/matching/intelligence triggers.

5. **Master admin control plane missing.**
- Severity: HIGH
- Type: UI/UX, RBAC/Security, Discoverability/Menu
- Why foundation: no first-class super-admin operations for tenant lifecycle and platform controls.

6. **Event/intelligence execution disconnect for core automations (dead placeholder paths).**
- Severity: HIGH
- Type: Event System, Workflow/Automation, AI/Intelligence
- Why foundation: higher-level AI modules depend on events that are not wired end-to-end.

## 4. Phase 1 Blockers

1. **Agency relationship reactivation API missing (`/reactivate/`).**
- Severity: HIGH
- Type: Backend/API, Workflow/Automation

2. **Guest portal resend invite resets token but sends no email.**
- Severity: HIGH
- Type: Business Logic, Workflow/Automation

3. **Agency team management APIs and model absent.**
- Severity: HIGH
- Type: Data Model, Backend/API, UI/UX

4. **Internal recruiter assignment for agency jobs missing end-to-end.**
- Severity: HIGH
- Type: Data Model, Backend/API

5. **Submission governance endpoint missing while policy field exists.**
- Severity: HIGH
- Type: Business Logic, Backend/API

6. **Master Admin UI missing (tenant control, feature controls).**
- Severity: HIGH
- Type: UI/UX, Discoverability/Menu, RBAC/Security

7. **Search typo tolerance + unified global search not implemented.**
- Severity: HIGH
- Type: Backend/API, UI/UX, Performance

8. **Agency dashboard route not wired.**
- Severity: MEDIUM
- Type: Discoverability/Menu, UI/UX

9. **Offer management UX fragmented across modules.**
- Severity: MEDIUM
- Type: UI/UX, Business Logic

## 5. Phase 2 Blockers

1. **Resume parser not implemented (OCR/PDF/docx extraction, normalization, confidence, review).**
- Severity: CRITICAL
- Type: AI/Intelligence, Backend/API, Data Model

2. **Vector/semantic search foundation missing (`pgvector` / Meilisearch integration).**
- Severity: CRITICAL
- Type: Data Model, Backend/API, Performance

3. **Graph similarity engine missing (shared employers/agencies/trajectory).**
- Severity: HIGH
- Type: AI/Intelligence, Backend/API

4. **Interview intelligence engine gaps (STT, per-question scoring, keyword mapping).**
- Severity: HIGH
- Type: AI/Intelligence, Workflow/Automation

5. **Candidate matching missing salary/availability/employment-type features + auto suggestion generation.**
- Severity: HIGH
- Type: Business Logic, AI/Intelligence, Event System

6. **Profile heat score core missing (daily recompute + weighted factors + source integration).**
- Severity: HIGH
- Type: Business Logic, Data Model, Workflow/Automation

7. **Global platform analytics and fraud detection engine missing (admin phase 2).**
- Severity: HIGH
- Type: Backend/API, AI/Intelligence, RBAC/Security

## 6. Phase 3 Blockers

1. **Hiring Success model not a trained predictive model (heuristic only).**
- Severity: CRITICAL
- Type: AI/Intelligence, Business Logic

2. **No continuous learning/retraining pipeline for hiring success.**
- Severity: CRITICAL
- Type: Workflow/Automation, AI/Intelligence

3. **No candidate-job prediction confidence output and explainability depth.**
- Severity: HIGH
- Type: AI/Intelligence, UI/UX

4. **Market Intelligence engine missing (demand/role difficulty/salary/time-to-fill benchmarks).**
- Severity: CRITICAL
- Type: AI/Intelligence, Data Model, Backend/API

5. **Market analytics currently include hardcoded heuristic values in key metrics.**
- Severity: HIGH
- Type: Business Logic, AI/Intelligence

6. **Recruiter Copilot not integrated into recruiter workflow; intelligence remains detached.**
- Severity: HIGH
- Type: UI/UX, Discoverability/Menu, AI/Intelligence

7. **Profile heat score trends/history/actionable heat recommendations not implemented.**
- Severity: HIGH
- Type: Data Model, UI/UX, AI/Intelligence

## 7. Severity Matrix

| Gap | Severity | Type Tags | Module |
|---|---|---|---|
| Tenant filtering manual leak risk | CRITICAL | RBAC/Security, Business Logic | Auth/Company/Cross-cutting |
| Agency API contract drift (404 workflows) | CRITICAL | Backend/API, Workflow/Automation, UI/UX | Agency |
| Agency performance scope exposure risk | CRITICAL | RBAC/Security | Agency |
| Resume parser core absent | CRITICAL | AI/Intelligence, Backend/API | Resume Parser |
| Vector/semantic search substrate absent | CRITICAL | Data Model, Backend/API, Performance | Search/Matching/Graph |
| Hiring success lacks trained model | CRITICAL | AI/Intelligence, Business Logic | Hiring Success |
| No retraining/continuous learning for hiring success | CRITICAL | Workflow/Automation, AI/Intelligence | Hiring Success |
| Market intelligence engine absent | CRITICAL | AI/Intelligence, Data Model, Backend/API | Market Intelligence |
| Candidate lifecycle inconsistency (lazy candidate create) | HIGH | Data Model, Business Logic | Auth/Candidate |
| Master admin UI absent | HIGH | UI/UX, Discoverability/Menu | Admin |
| Search typo tolerance/global search absent | HIGH | Backend/API, UI/UX | Search |
| Interview STT + scoring pipeline absent | HIGH | AI/Intelligence, Workflow/Automation | Interview Intelligence |
| Profile heat weighted daily engine absent | HIGH | Business Logic, Workflow/Automation | Profile Heat |
| Recruiter copilot detached from real workflows | HIGH | UI/UX, AI/Intelligence | Recruiter Copilot |
| Offer UX fragmentation | MEDIUM | UI/UX, Business Logic | Company |
| Agency dashboard route missing | MEDIUM | Discoverability/Menu | Agency |
| No agency performance timeseries endpoint | MEDIUM | Backend/API, Documentation/QA | Agency |

## 8. Recommended Fix Order
Ordered for execution readiness and dependency safety.

1. **Enforce tenant-safe access patterns at framework level** (manager/mixin/permission policy; audit high-risk endpoints first).
2. **Patch agency security and workflow breakages**:
   - lock `AgencyPerformanceListView` scope,
   - add missing endpoints (`reactivate`, `assign-recruiter`, `submission-governance`),
   - fix resend invite email.
3. **Introduce agency membership data model + team APIs** (enable recruiter assignment and per-user scoping).
4. **Deliver Master Admin control plane MVP** (tenant list/actions, feature controls, audit view).
5. **Stabilize identity lifecycle** (create/link candidate entity at registration, not deferred only to passport save).
6. **Phase 1 search reliability** (global search entry + typo tolerance baseline).
7. **Phase 2 intelligence substrate**:
   - vector index/embeddings foundation,
   - event wiring reliability for intelligence triggers.
8. **Resume parser MVP** (ingestion + extraction + review UI + confidence fields).
9. **Interview intelligence MVP** (STT + per-question scoring + keyword/concept mapping).
10. **Candidate matching v2** (salary/availability/employment features + automated suggestion generation).
11. **Profile heat score engine** (weighted factors, daily scheduler, stale-data handling).
12. **Hiring success modelization** (training pipeline, prediction confidence, explainability contracts).
13. **Market intelligence engine** (aggregates, benchmarks, trend storage, freshness jobs).
14. **Recruiter copilot integration** (embed actionable suggestions in workbench/dashboard).
15. **Enhancements and polish** (timeseries exports, advanced dashboards, UI refinements).

## 9. Release Readiness

### Safe for Internal Testing
- Core ATS workflows: job creation, pipeline basics, agency assignment/submission, interview scheduling, base offers.
- Conditions: internal users aware of known broken agency actions and intelligence placeholders.

### Safe for Pilot Customers (Limited)
- **Not yet broadly safe**.
- Narrow pilot only possible if scope excludes:
  - advanced agency operations (reactivation/governance/team assignment),
  - AI/intelligence claims (resume parsing, true predictions, market intelligence).

### Not Ready
- Any launch promising Phase 2/Phase 3 intelligence capabilities as production-grade.
- Any environment needing strict confidence on tenant-safe controls without additional hardening.

### Biggest Launch Risks Now
1. Security/commercial exposure risk in agency performance scoping.
2. Broken user flows from frontend-backend endpoint mismatch.
3. Intelligence feature trust gap (heuristics/placeholder values presented as AI insights).
4. Scale/performance bottlenecks in search and matching loops.

## 10. Immediate Next Module to Fix
- **Next module: Agency (Security + Core Workflow Integrity).**

### Why this module first
- It contains both security-sensitive and user-visible broken flows.
- It blocks Phase 1 trust (reactivation, governance, recruiter assignment, invite resend).
- It has clear bounded fixes that immediately reduce operational and reputational risk.

### Immediate work package (no implementation here; planning only)
1. Scope-fix `AgencyPerformanceListView` to authorized agency context.
2. Implement missing endpoints and wire existing frontend calls.
3. Add resend invite email dispatch.
4. Add agency membership + recruiter assignment persistence.
5. Add tests for endpoint availability and authorization boundaries.

