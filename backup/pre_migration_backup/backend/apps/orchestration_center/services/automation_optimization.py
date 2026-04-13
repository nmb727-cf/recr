from django.utils import timezone
from django.db.models import Avg, Count, Q
from apps.orchestration_center.models import (
    AutomationIntelligencePolicy,
    AutomationLearningSignal,
    AutomationOptimizationRecommendation,
)

class AutomationOptimizationService:
    @staticmethod
    def generate_recommendations(tenant_id):
        """
        Analyze policy performance and generate optimization recommendations.
        """
        policies = AutomationIntelligencePolicy.objects.filter(tenant_id=tenant_id, is_enabled=True)
        recommendations = []

        for policy in policies:
            # Aggregate performance metrics for the last 30 days
            signals = AutomationLearningSignal.objects.filter(
                tenant_id=tenant_id,
                policy_id=policy.id,
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            )
            
            total_signals = signals.count()
            if total_signals < 10:  # Minimum data threshold
                continue

            success_rate = signals.filter(outcome_type__in=['success', 'approved', 'applied']).count() / total_signals * 100
            failure_rate = signals.filter(outcome_type='failure').count() / total_signals * 100
            
            # Optimization Rules
            
            # 1. Enable Auto-Apply
            if success_rate > 95 and failure_rate < 2 and not policy.auto_apply:
                recommendation, created = AutomationOptimizationRecommendation.objects.get_or_create(
                    tenant_id=tenant_id,
                    policy=policy,
                    recommendation_type='enable_auto_apply',
                    applied_at__isnull=True,
                    defaults={
                        'current_value': False,
                        'recommended_value': True,
                        'reason': f"Consistently high success rate ({success_rate:.1f}%) and low failure rate ({failure_rate:.1f}%). Auto-apply will reduce manual work.",
                        'confidence': 0.95
                    }
                )
                if created: recommendations.append(recommendation)

            # 2. Disable Auto-Apply due to high failure
            elif failure_rate > 15 and policy.auto_apply:
                recommendation, created = AutomationOptimizationRecommendation.objects.get_or_create(
                    tenant_id=tenant_id,
                    policy=policy,
                    recommendation_type='disable_auto_apply',
                    applied_at__isnull=True,
                    defaults={
                        'current_value': True,
                        'recommended_value': False,
                        'reason': f"High failure rate ({failure_rate:.1f}%) detected. Disabling auto-apply to prevent further errors.",
                        'confidence': 0.98
                    }
                )
                if created: recommendations.append(recommendation)

            # 3. Increase Confidence Threshold
            if success_rate < 85 and failure_rate > 5:
                 new_threshold = float(policy.confidence_threshold) + 0.05
                 if new_threshold <= 1.0:
                    recommendation, created = AutomationOptimizationRecommendation.objects.get_or_create(
                        tenant_id=tenant_id,
                        policy=policy,
                        recommendation_type='increase_confidence_threshold',
                        applied_at__isnull=True,
                        defaults={
                            'current_value': float(policy.confidence_threshold),
                            'recommended_value': new_threshold,
                            'reason': f"Success rate ({success_rate:.1f}%) is below target. Increasing confidence threshold to filter out low-quality suggestions.",
                            'confidence': 0.88
                        }
                    )
                    if created: recommendations.append(recommendation)

        return recommendations

    @staticmethod
    def apply_recommendation(recommendation_id, tenant_id, performed_by=None):
        """
        Apply a specific optimization recommendation.
        """
        recommendation = AutomationOptimizationRecommendation.objects.get(id=recommendation_id, tenant_id=tenant_id)
        if recommendation.applied_at:
            return False, "Recommendation already applied."

        policy = recommendation.policy
        rec_type = recommendation.recommendation_type
        val = recommendation.recommended_value

        if rec_type == 'enable_auto_apply':
            policy.auto_apply = True
            policy.auto_approve = True # Auto-apply requires auto-approve
            policy.approval_required = False
        elif rec_type == 'disable_auto_apply':
            policy.auto_apply = False
        elif rec_type == 'enable_auto_approve':
            policy.auto_approve = True
        elif rec_type == 'disable_auto_approve':
            policy.auto_approve = False
            policy.auto_apply = False
        elif rec_type == 'increase_confidence_threshold' or rec_type == 'decrease_confidence_threshold':
            policy.confidence_threshold = val
        elif rec_type == 'change_risk_level':
            policy.risk_level = val

        policy.save()
        recommendation.applied_at = timezone.now()
        recommendation.save()

        # Log governance audit
        from apps.orchestration_center.services.ai_governance import AIGovernanceService
        AIGovernanceService.log_audit(
            tenant_id, 
            'policy_change', 
            performed_by=performed_by, 
            target_id=policy.id,
            details={'recommendation_type': rec_type, 'applied_value': val}
        )

        return True, "Recommendation applied successfully."

    @staticmethod
    def get_optimization_overview(tenant_id):
        return {
            'pending_count': AutomationOptimizationRecommendation.objects.filter(tenant_id=tenant_id, applied_at__isnull=True).count(),
            'applied_total': AutomationOptimizationRecommendation.objects.filter(tenant_id=tenant_id, applied_at__isnull=False).count(),
            'last_run': timezone.now() # Mocking last run for now
        }
