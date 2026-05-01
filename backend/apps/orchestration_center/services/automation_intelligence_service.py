from apps.orchestration_center.services.suggestion_policy_evaluator import (  # noqa: F401
    AutoApplyGuard,
    PolicyEvaluationResult,
    SuggestionPolicyEvaluator,
)


class AutomationIntelligenceService:
    """Thin façade kept for backward compatibility.

    All evaluation logic lives in SuggestionPolicyEvaluator.  Call that class
    directly for new code; this service translates its structured result into
    the plain-dict format that the existing task and tests expect.
    """

    @staticmethod
    def evaluate_suggestion_policy(*, suggestion_id):
        result = SuggestionPolicyEvaluator.evaluate(suggestion_id)
        return result.as_dict()
