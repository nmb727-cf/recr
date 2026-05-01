# AI Governance & Safety Enhancements

## Overview
Phase 59 Step 8 implements enterprise-level governance, safety controls, and auditability for the Automation Intelligence system. This includes risk-based enforcement, usage limits, and a global kill switch.

## Governance Controls

### 1. Risk-Based Enforcement
Policies now include a `risk_level` (Low, Medium, High, Critical) that dictates allowed automation levels:
- **Low**: Auto-apply is permitted without restriction.
- **Medium**: Approval is required before any action is applied.
- **High**: Admin-level approval is required.
- **Critical**: Manual intervention only; autonomous execution is blocked.

### 2. AI Usage Limits
The `AutomationUsageLimit` model enforces tenant-level safety thresholds:
- **Daily Limit**: Maximum number of AI execution requests per 24 hours.
- **Hourly Limit**: Burst protection for AI requests.
- **Max Auto-Apply**: Daily cap on automated state changes.
- **Max Failures**: Safety threshold that pauses automation if error rates exceed limits.

### 3. Global Kill Switches
Three primary toggles provide immediate control over system behavior:
- **AI Core Enablement**: Disables all LLM-based features.
- **Autonomous Execution**: Stops all background automation rules.
- **Auto-Apply Enablement**: Disables direct state modification across the tenant.

## Backend Components
- **AIGovernanceService**: Provides logic for rule checking, limit enforcement, and audit logging.
- **AutomationGovernanceAudit**: Captures a permanent record of policy changes, limit violations, and kill switch events.

## API Endpoints
- `GET /api/v1/intelligence/governance/summary/`: Retrieves current switches and limits.
- `POST /api/v1/intelligence/governance/summary/`: Updates switches and limits (admin only).
- `GET /api/v1/intelligence/governance/audit/`: Retrieves the governance audit trail.

## UI Section: Intelligence Hub → Governance
- **Global Safety Switches Panel**: High-visibility toggles for core AI and automation features.
- **Usage & Rate Limits Panel**: Configuration for daily/hourly caps and failure thresholds.
- **Policy Risk Governance Table**: View of risk levels and enforcement rules across all policies.
- **Governance Audit Trail**: Chronological log of sensitive system actions and events.
