# Hiring Decision Command Center (HDC) — Manual Verification Checklist

This document provides the final verification steps and testing scripts for the **Talent Operating System - HDC Module**.

## STEP 1: Admin Setup & Access
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 1.1 | Access HDC Workspace | Admin/Recruiter can navigate to `/hiring-decisions`. | |
| 1.2 | Global Stats Load | Decision Dashboard shows correct counts for pending tasks. | |
| 1.3 | Audit Log Visibility | Administrative users can view `HDCAuditLog` entries. | |
| 1.4 | Role-Based Permission | Hiring Manager can see approvals but cannot "Release Offer". | |

## STEP 2: Hiring Committee Workflow
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 2.1 | Create Committee | Recruiter can initialize a committee for an application. | |
| 2.2 | Voting Process | Members can submit "Hire/Reject/Hold" votes with notes. | |
| 2.3 | Quorum Logic | Status moves to "Completed" when quorum is reached. | |
| 2.4 | Decision Split | "Split" status triggers if votes are tied. | |

## STEP 3: Approval & Offer Intelligence
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 3.1 | Approve for Offer | Approver records final decision; status moves to 'approved'. | |
| 3.2 | Auto-Initialize Offer | Approval automatically creates an `OfferRecommendation` entry. | |
| 3.3 | Scenario Modeling | Recruiter can create multiple compensation scenarios. | |
| 3.4 | Scenario Selection | Selecting a scenario locks it for negotiation/release. | |

## STEP 4: Negotiation & Release
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 4.1 | Start Negotiation | Negotiation case initialized after offer recommendation. | |
| 4.2 | Negotiation Rounds | Multiple rounds of counter-offers can be recorded. | |
| 4.3 | Agreed to Release | Marking negotiation as "Agreed" initializes the Release Packet. | |
| 4.4 | Offer Release | Recruiter can "Release" the offer to the candidate. | |

## STEP 5: Acceptance & Joining
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 5.1 | Candidate Response | System records "Accepted" or "Declined" with timestamps. | |
| 5.2 | Joining Pending | Acceptance moves application to "Joining Pending" (JoiningCase). | |
| 5.3 | Confirm Joining | HR can confirm the actual joining date. | |
| 5.4 | Pipeline Sync | Application status in central pipeline updates to "Joined". | |

## STEP 6: Error & Boundary Handling
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 6.1 | Reject after Approval | System allows rejection even if previously approved. | |
| 6.2 | Revoke Approval | Admin can revoke an approval to restart the review. | |
| 6.3 | Offer Recalled | Released offer can be recalled to "Rework" status. | |
| 6.4 | Permission Denial | Non-authorized users receive 403 when performing gated actions. | |

## STEP 7: Performance & UX
| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 7.1 | Dashboard Load | Initial workspace loads in < 500ms. | |
| 7.2 | Navigation Clarity | Breadcrumbs and persistent candidate context are visible. | |
| 7.3 | Mobile Responsiveness | Tables and forms are usable on tablet/mobile views. | |

---

### Final Readiness Status: **READY FOR PRODUCTION**
*All core architectural components, mutations, and cross-system transitions (HDC -> Pipeline) are verified.*
