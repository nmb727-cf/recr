# QA Document: Hiring Decision Command Center (HDC) Operational Conversion

## 1. Overview
The Hiring Decision Command Center (HDC) has been converted from a demo/placeholder module into a functional operational suite. This conversion includes new backend models, API endpoints, and interactive frontend components for the entire post-interview hiring lifecycle.

## 2. Status Summary

| Section | Status | Create Flow | Edit Flow | Save/Submit | Action Buttons | State Transitions | Route/Page |
|---------|--------|-------------|-----------|-------------|----------------|-------------------|------------|
| Decision Engine | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions` |
| Hiring Committee | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/committee` |
| Candidate Comparison | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/comparison` |
| Decision Approval | Fully operational | N/A (Review) | Yes | Yes | Yes | Yes | `/hiring-decisions/approvals` |
| Offer Intelligence | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/offer-intelligence` |
| Compensation | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/compensation` |
| Negotiation | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/negotiation` |
| Final Offer Release | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/offer-release` |
| Offer Acceptance | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/offer-acceptance` |
| Joining Tracking | Fully operational | Yes | Yes | Yes | Yes | Yes | `/hiring-decisions/joining` |

## 3. Technical Implementation Details

### 3.1 Backend (HDC App)
- **Models**: Implemented `HiringCommittee`, `CommitteeMember`, `ComparisonSet`, `ComparisonCandidate`, `OfferRecommendation`, `OfferScenario`, `NegotiationCase`, `NegotiationRound`, and `OfferReleasePacket`.
- **API Base**: `/api/v1/hdc/`
- **Actions**:
    - `POST /hdc/committees/{id}/submit_vote/`: Submit panelist vote and notes.
    - `POST /hdc/comparisons/{id}/freeze/`: Freeze comparison set.
    - `POST /hdc/offer-recommendations/{id}/select_scenario/`: Lock a specific scenario.
    - `POST /hdc/negotiations/{id}/add_round/`: Record a new negotiation round.
    - `POST /hdc/offer-release/{id}/release/`: Dispatch final offer.

### 3.2 Frontend (HDC Sections)
- **Location**: `src/pages/hdc/sections/`
- **Components**: Replaced `VisibilityShellPage` with dedicated components:
    - `DecisionDashboard.tsx`: Executive overview.
    - `HiringCommittee.tsx`: Committee creation and voting.
    - `CandidateComparison.tsx`: Set management and scoring.
    - `DecisionApproval.tsx`: Multi-step approval review.
    - `OfferIntelligence.tsx`: Scenario modeling and recommendation.
    - `Compensation.tsx`: Detailed package construction.
    - `Negotiation.tsx`: Multi-round negotiation logger.
    - `OfferRelease.tsx`: Packet assembly and dispatch.
    - `OfferAcceptance.tsx`: External response capture.
    - `JoiningTracking.tsx`: Handoff and date management.

## 4. Operational Verification Steps
1. Navigate to **Hiring Decisions**.
2. Click **Initialize Committee** in the Committee tab; fill the form and submit.
3. In **Compensation**, create a new package using the wizard modal.
4. In **Negotiation**, record a candidate's ask and a company counter.
5. In **Offer Release**, run the dispatch flow for a ready offer.
6. Verify all "Demo Only" labels are replaced with "Operational Console" or similar product-grade headers.

## 5. Remaining Blockers
- Integration with live HRMS for automatic "Joined" status sync (currently manual in HDC).
- Real-time notification triggers for Committee votes (logic exists, needs websocket/push wiring).
- Document generation for "Offer Release" packets (currently uses metadata/attachments).
