from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from apps.orchestration_center.models import (
    AutomationLearningSignal,
    AutomationIntelligencePolicy,
    AISuggestion,
    AutomationExecutionRun,
)

class AutomationLearningService:
    @staticmethod
    def record_outcome(tenant_id, outcome_type, automation_id=None, suggestion_id=None, policy_id=None, confidence_score=0.0, execution_time_ms=None, user_action='', metadata=None):
        """Record a learning signal for future optimization."""
        suggestion_type = ''
        if suggestion_id:
            try:
                suggestion = AISuggestion.objects.get(id=suggestion_id)
                suggestion_type = suggestion.suggestion_type
            except AISuggestion.DoesNotExist:
                pass
        elif policy_id:
            try:
                policy = AutomationIntelligencePolicy.objects.get(id=policy_id)
                suggestion_type = policy.suggestion_type
            except AutomationIntelligencePolicy.DoesNotExist:
                pass

        return AutomationLearningSignal.objects.create(
            tenant_id=tenant_id,
            automation_id=automation_id,
            suggestion_id=suggestion_id,
            policy_id=policy_id,
            suggestion_type=suggestion_type,
            outcome_type=outcome_type,
            confidence_score=confidence_score,
            execution_time_ms=execution_time_ms,
            user_action=user_action,
            metadata=metadata or {}
        )

    @staticmethod
    def generate_policy_recommendations(tenant_id):
        """Analyze outcomes and generate recommendations for each policy."""
        policies = AutomationIntelligencePolicy.objects.filter(tenant_id=tenant_id)
        signals_created = []

        for policy in policies:
            # Aggregate stats for this policy
            signals = AutomationLearningSignal.objects.filter(tenant_id=tenant_id, policy_id=policy.id)
            total = signals.count()
            
            if total < 5:  # Need minimum signals to learn
                continue

            approved_count = signals.filter(outcome_type__in=['approved', 'applied']).count()
            rejected_count = signals.filter(outcome_type='rejected').count()
            success_count = signals.filter(outcome_type__in=['success', 'applied']).count()
            failure_count = signals.filter(outcome_type='failure').count()
            override_count = signals.filter(outcome_type='overridden').count()

            approval_rate = (approved_count / total) * 100
            rejection_rate = (rejected_count / total) * 100
            success_rate = (success_count / (success_count + failure_count)) * 100 if (success_count + failure_count) > 0 else 100
            failure_rate = (failure_count / (success_count + failure_count)) * 100 if (success_count + failure_count) > 0 else 0
            override_rate = (override_count / total) * 100

            recommendation = ""
            
            # Rule 1: approval_rate > 90% AND auto_approve disabled -> Recommend enabling auto approve
            if approval_rate > 90 and not policy.auto_approve:
                recommendation = "Recommend enabling auto approve"
            
            # Rule 2: success_rate > 95% AND auto_apply disabled -> Recommend enabling auto apply
            elif success_rate > 95 and not policy.auto_apply:
                recommendation = "Recommend enabling auto apply"
            
            # Rule 3: failure_rate > 20% -> Recommend disabling automation
            elif failure_rate > 20:
                recommendation = "Recommend disabling automation"

            if recommendation:
                signal = AutomationLearningSignal.objects.create(
                    tenant_id=tenant_id,
                    policy_id=policy.id,
                    suggestion_type=policy.suggestion_type,
                    outcome_type='governance', # Special type for system-generated signals
                    success_rate=success_rate,
                    failure_rate=failure_rate,
                    override_rate=override_rate,
                    confidence_score=policy.confidence_threshold,
                    recommendation=recommendation
                )
                signals_created.append(signal)

        return signals_created

    @staticmethod
    def get_learning_overview(tenant_id):
        now = timezone.now()
        last_30d = now - timedelta(days=30)
        signals = AutomationLearningSignal.objects.filter(tenant_id=tenant_id, created_at__gte=last_30d)
        
        return {
            'total_signals': signals.count(),
            'avg_success_rate': signals.aggregate(Avg('success_rate'))['success_rate__avg'] or 0,
            'avg_failure_rate': signals.aggregate(Avg('failure_rate'))['failure_rate__avg'] or 0,
            'recommendation_count': signals.exclude(recommendation='').count()
        }

    @staticmethod
    def get_policy_learning_table(tenant_id):
        policies = AutomationIntelligencePolicy.objects.filter(tenant_id=tenant_id)
        results = []
        for policy in policies:
            # Get latest signal with recommendation for this policy
            latest_signal = AutomationLearningSignal.objects.filter(
                tenant_id=tenant_id, 
                policy_id=policy.id
            ).exclude(recommendation='').first()
            
            # Get general stats
            stats = AutomationLearningSignal.objects.filter(
                tenant_id=tenant_id, 
                policy_id=policy.id
            ).aggregate(
                avg_success=Avg('success_rate'),
                avg_failure=Avg('failure_rate')
            )

            results.append({
                'policy_id': str(policy.id),
                'suggestion_type': policy.suggestion_type,
                'success_rate': round(stats['avg_success'] or 0, 2),
                'failure_rate': round(stats['avg_failure'] or 0, 2),
                'recommendation': latest_signal.recommendation if latest_signal else "No recommendation yet"
            })
        return results

    @staticmethod
    def get_recent_signals(tenant_id, limit=50):
        signals = AutomationLearningSignal.objects.filter(tenant_id=tenant_id).order_by('-created_at')[:limit]
        return signals
