# Automation Self Learning Engine

## Overview
Phase 28 implements the **Automation Self Learning Engine**, a continuous optimization layer that allows the system to learn from behavior, outcomes, failures, and usage to improve automation performance over time.

## Key Components

### AutomationSelfLearningEngine
The core engine responsible for:
- **Capturing Learning Events**: Tracking successes, failures, manual overrides, and retries.
- **Pattern Detection**: Identifying repeated failures, manual actions, and delay patterns.
- **Optimization Suggestions**: Generating actionable recommendations based on detected patterns.
- **Model Training**: Managing and updating learning models for failure and delay prediction.

### Models
1. **AutomationLearningEvent**: Audit log of all automation-related outcomes and human interventions.
2. **AutomationLearningPattern**: High-level insights derived from event analysis (e.g., "Repeated Failure Pattern").
3. **AutomationOptimizationSuggestion**: Specific recommendations like "Add Fallback" or "Automate Manual Task".
4. **AutomationLearningModel**: Tracks the health and accuracy of predictive algorithms.

## API Endpoints
- `GET /api/v1/automation-learning/overview/`: Summary of learning events, patterns, and pending suggestions.
- `GET /api/v1/automation-learning/patterns/`: List of all detected execution and behavior patterns.
- `GET /api/v1/automation-learning/suggestions/`: Optimization recommendations with confidence scores.
- `GET /api/v1/automation-learning/predictions/`: Predictive analysis for specific workflows (failure/delay probability).
- `GET /api/v1/automation-learning/models/`: Status of active learning models.
- `POST /api/v1/automation-learning/retrain/`: Manually trigger retraining of a specific model type.

## Dashboard Integration: Intelligence Hub → Self Learning
- **Learning Overview**: KPI cards showing total events and learning status.
- **Detected Patterns**: Visual list of identified system behaviors.
- **Optimization Suggestions**: Actionable recommendations for system improvement.
- **Predictive Insights**: Forecasts for system reliability and potential bottlenecks.

## Command Center Integration
- Added **Learning Summary** to the Automation Command Center (`/api/v1/automation-center/learning-summary/`), showing the top suggestions and patterns directly to automation operators.

## Governance
- Multi-tenant scoped.
- Requires `CanView` for data access and `CanAdmin` for model retraining.
- Suggestions are non-binding and require administrative review.
