# ICC-NEXT-MODULE-HANDOFF-37

## 1. Next Module Architecture

Next system: `Hiring Decision Command Center`

Purpose:
- convert interview outcomes into governed hiring decisions and offer workflows
- unify decisioning, committee review, compensation logic, approval routing, negotiation, and hiring intelligence

Core components:
1. Decision Engine
2. Hiring Committee Engine
3. Offer Engine
4. Compensation Engine
5. Approval Engine
6. Negotiation Engine
7. Hiring Intelligence Layer

Recommended architecture layers:
- Decision Layer
- Committee Layer
- Offer Layer
- Compensation Layer
- Approval Layer
- Negotiation Layer
- Intelligence Layer
- Governance Layer
- Analytics Layer
- Integration Layer

Operating model:
- Interview Command Center remains upstream source for interview execution, scorecards, feedback, composite flow results, automation signals, and interview analytics
- Hiring Decision Command Center consumes only valid, approved, tenant-scoped interview outcomes
- candidate remains a global entity with tenant association only
- decision and offer artifacts are governed, auditable, versioned, and approval-gated

## 2. System Placement

Placement in TOS:
- Candidate / Talent Data Layer
- Interview Command Center
- Hiring Decision Command Center
- Offer / Compensation / Approval Operations

Functional placement:
- Interview Command Center ends at evaluated interview outcomes, scorecards, decisions-ready summaries, analytics, and governance evidence
- Hiring Decision Command Center starts at decision intake, committee review, offer strategy, compensation workflows, approval chains, negotiation management, and post-decision intelligence

Workspace placement:
- Company Workspace
- Agency Workspace where permitted
- Governance / leadership views
- Candidate portal only for downstream approved outcomes later

## 3. Dependencies

Upstream dependencies from ICC:
- Interview Execution Engines
- Composite Flow Engine
- Scorecard Engine
- Feedback and reviewer outcomes
- Analytics Layer
- Governance Layer
- Audit and approval evidence

Required input domains:
- interview completion status
- scorecards and scoring summaries
- interviewer and panel feedback
- composite flow completion state
- candidate progression state
- analytics-based risk or quality indicators
- governance blocks, flags, and compliance constraints

Key dependency rules:
- only approved and valid interview outcomes can enter decision workflows
- decisioning must respect tenant isolation and governance policies
- compensation and offer logic must consume auditable interview evidence
- agency visibility must remain bounded by tenant and permission policy

## 4. Implementation Plan

Phase 1:
- define HDC core contracts, event model, decision entity model, approval model, and candidate/job linkage rules
- establish ICC to HDC handoff event contracts and source-of-truth mapping

Phase 2:
- build Decision Engine and Hiring Committee Engine
- ingest scorecards, feedback, analytics indicators, and governance flags

Phase 3:
- build Offer Engine and Compensation Engine
- implement compensation bands, offer drafting, policy controls, and approval prerequisites

Phase 4:
- build Approval Engine and Negotiation Engine
- support multi-step approval chains, negotiation states, audit trails, and exception handling

Phase 5:
- build Hiring Intelligence Layer
- add decision quality analytics, offer acceptance intelligence, compensation benchmarking, and recommendation support

Phase 6:
- final integration, rollout readiness, pilot, and production launch planning

Recommended first build order:
1. shared contracts and ICC-to-HDC handoff
2. Decision Engine
3. Hiring Committee Engine
4. Approval Engine
5. Offer Engine
6. Compensation Engine
7. Negotiation Engine
8. Hiring Intelligence Layer
9. rollout and go-live controls

Recommended next prompt:
- `HDC-ARCHITECTURE-01`
