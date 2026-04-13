# Automation Intelligence Analytics

## Overview
Phase 57 Step 6 adds comprehensive analytics and observability for the Automation Intelligence system. This includes metrics for AI suggestions, automation policies, execution health, and confidence levels.

## Key Metrics

### Suggestion Metrics
- **suggestions_created**: Total AI suggestions generated.
- **suggestions_approved**: Suggestions manually or automatically approved.
- **suggestions_rejected**: Suggestions manually or automatically rejected.
- **suggestions_dismissed**: Suggestions dismissed without a decision.
- **suggestions_applied**: Suggestions that were successfully applied to the business state.
- **suggestions_failed**: Suggestions that failed during application.

### Policy Metrics
- **policy_trigger_count**: How many times a policy was evaluated.
- **auto_approve_count**: Decisions made automatically by a policy.
- **auto_apply_count**: Applications triggered automatically by a policy.
- **policy_failure_count**: Failures originating from policy-driven actions.

### Execution Metrics
- **total_executions**: Combined AI and automation execution count.
- **successful_executions**: Executions that reached a terminal success state.
- **failed_executions**: Executions that failed.
- **retry_count**: Total number of retry attempts across all executions.

### Confidence Metrics
- **average_confidence**: Mean confidence score across all suggestions.
- **auto_approve_rate**: Percentage of suggestions automatically approved.
- **auto_apply_rate**: Percentage of suggestions automatically applied.

## Backend Endpoints
- `GET /api/v1/intelligence/analytics/overview/`: Top-level KPI summary.
- `GET /api/v1/intelligence/analytics/suggestions/`: Detailed suggestion lifecycle and confidence breakdown.
- `GET /api/v1/intelligence/analytics/policies/`: Policy-by-policy effectiveness metrics.
- `GET /api/v1/intelligence/analytics/executions/`: Health and performance of AI and automation runners.

## Permissions
- **Admin only**: Requires `analytics.view` or `intelligence.admin` permissions.
- **Tenant scoped**: Data is strictly filtered by the authenticated user's `tenant_id`.

## UI Components
- **Overview Cards**: Immediate visibility into top-level system state.
- **Suggestion Lifecycle Chart**: Visual breakdown of the transition from creation to application.
- **Policy Effectiveness Table**: Comparison of how different automation policies are performing.
- **Execution Health Panel**: Real-time status of system runners and success rates.
