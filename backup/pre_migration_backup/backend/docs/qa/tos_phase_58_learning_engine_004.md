# Automation Learning Engine

## Overview
Phase 58 Step 7 implements the Automation Learning Engine, a proactive system that monitors the outcomes of AI suggestions and automation executions to recommend optimizations to the tenant's intelligence policies.

## Key Components

### AutomationLearningService
The core service responsible for:
- Recording learning signals (outcomes) from suggestions and executions.
- Analyzing signal history against defined thresholds.
- Generating policy-specific recommendations (Auto-Approve, Auto-Apply, or Disable).

### Learning Rules
1. **Enable Auto-Approve**: Recommended if a suggestion type has an approval rate > 90% over at least 5 signals and auto-approve is currently disabled.
2. **Enable Auto-Apply**: Recommended if an execution success rate > 95% over at least 5 signals and auto-apply is currently disabled.
3. **Disable Risky Policy**: Recommended if an automation failure rate exceeds 20%.

### AutomationLearningSignal Model
Tracks the history of outcomes and system-generated recommendations:
- `suggestion_type`: The category of automation being tracked.
- `success_rate` / `failure_rate`: Performance metrics at the time of signal generation.
- `override_rate`: How often human users manually changed the AI's proposed action.
- `recommendation`: The specific action suggested by the learning engine.

## API Endpoints
- `GET /api/v1/intelligence/learning/overview/`: KPI summary of learning progress.
- `GET /api/v1/intelligence/learning/recommendations/`: Active policy optimization suggestions.
- `GET /api/v1/intelligence/learning/signals/`: Audit log of recent outcomes.
- `GET /api/v1/intelligence/learning/policy-table/`: Per-policy performance and recommendation status.

## UI Section: Intelligence Hub → Learning
- **Learning Recommendations Panel**: Actionable cards for optimizing or securing policies.
- **Policy Learning Table**: Comparative view of success/failure rates across all active policies.
- **Learning Signals List**: Real-time feed of automation outcomes and user actions.

## Governance
- The Learning Engine **only provides recommendations**.
- No automatic policy changes are made by the system.
- Administrator review and manual approval are required to apply any recommendation.
