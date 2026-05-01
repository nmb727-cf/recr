# Automation AI Brain

## Overview
Phase 29 implements the **Automation AI Brain**, the central intelligence layer that governs and orchestrates all automation decisions across the system. It uses contextual analysis, predictive outcomes, and risk assessments to determine the best actions for any situation.

## Key Components

### AutomationAIBrainEngine
The central decision engine responsible for:
- **Context Analysis**: Fetching and interpreting state from various sources (candidates, jobs, SLAs).
- **Predictive Decision Making**: Forecasting outcome success and potential risks.
- **Smart Workflow Selection**: Choosing the optimal workflow among competing triggers.
- **Intelligent Prioritization**: Reordering execution queues based on business impact and SLA risk.
- **Risk Detection**: Automatically identifying conditions requiring escalation or pausing.

### Models
1. **AutomationAIDecision**: Audit log of all AI-driven decisions (Execute, Delay, Escalate, Retry, Fallback, Pause).
2. **AutomationAIContext**: Snapshots of environmental state at decision time.
3. **AutomationAIReasoning**: Detailed reasoning and confidence logs supporting every decision.
4. **AutomationAIRecommendation**: AI-driven suggestions for workflow creation or optimization.

## API Endpoints
- `GET /api/v1/automation-ai/decisions/`: History of all AI-governed actions.
- `GET /api/v1/automation-ai/recommendations/`: AI-generated suggestions for business optimization.
- `GET /api/v1/automation-ai/predictions/`: Predictive reasoning audit log.
- `GET /api/v1/automation-ai/context/`: Context snapshots supporting the AI decisions.
- `POST /api/v1/automation-ai/recalculate/`: Force recalculation of AI decisions for a specific context.

## Decision Flow
1. **Collect Context**: Gather candidate, job, and workload data.
2. **Analyze Patterns**: Compare current state with historical behavior patterns.
3. **Predict Outcomes**: Forecast success/failure and SLA breach risks.
4. **Choose Action**: Select the best workflow or decide to escalate/wait.
5. **Execute/Log**: Finalize decision and record reasoning for auditability.

## Dashboard Integration: Intelligence Hub → AI Brain
- **AI Decisions Feed**: Real-time log of autonomous system actions.
- **AI Reasoning Logs**: Deep dive into the "Why" behind AI decisions.
- **AI Recommendations**: Critical suggestions for process improvement.
- **AI Confidence Metrics**: Accuracy and reliability scores for decision models.

## Command Center Integration
- Added **AI Brain Summary** to the Automation Command Center (`/api/v1/automation-center/ai-brain-summary/`), providing operators with immediate visibility into the latest AI-driven decisions and risks.

## Governance
- Tenant-scoped and role-restricted.
- Requires `CanManage` for data access.
- Provides "Explainable AI" via reasoning logs to satisfy audit requirements.
