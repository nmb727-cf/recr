from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from apps.orchestration_center.models import (
    AIExecutionRequest,
    AISuggestion,
    AutomationExecutionRun,
    AutomationIntelligencePolicy,
)


class AutomationAnalyticsService:

    @staticmethod
    def get_overview_analytics(tenant_id, days=30):
        """Top-level KPI summary across suggestions, policies, and executions."""
        since = timezone.now() - timedelta(days=days)
        suggestions = AISuggestion.objects.filter(tenant_id=tenant_id, created_at__gte=since)

        total_s = suggestions.count()
        approved = suggestions.filter(status='approved').count()
        rejected = suggestions.filter(status='rejected').count()
        applied = suggestions.filter(status='applied').count()
        dismissed = suggestions.filter(status='dismissed').count()
        failed_apply = suggestions.filter(last_apply_status='failed').count()
        total_decided = approved + rejected

        avg_conf_result = suggestions.aggregate(avg=Avg('confidence_score'))
        avg_confidence = round(float(avg_conf_result['avg'] or 0), 4)

        auto_approve_rate = round(approved / total_s * 100, 2) if total_s > 0 else 0.0
        auto_apply_rate = round(applied / total_s * 100, 2) if total_s > 0 else 0.0
        accuracy_rate = round(approved / total_decided * 100, 2) if total_decided > 0 else 100.0

        ai_runs = AIExecutionRequest.objects.filter(tenant_id=tenant_id, created_at__gte=since)
        auto_runs = AutomationExecutionRun.objects.filter(tenant_id=tenant_id, created_at__gte=since)

        ai_total = ai_runs.count()
        ai_successful = ai_runs.filter(status='completed').count()
        ai_failed = ai_runs.filter(status='failed').count()
        ai_retry_sum = ai_runs.aggregate(total=Sum('retry_count'))['total'] or 0

        auto_total = auto_runs.count()
        auto_successful = auto_runs.filter(status='completed').count()
        auto_failed = auto_runs.filter(status='failed').count()
        auto_retry_sum = auto_runs.aggregate(total=Sum('retry_count'))['total'] or 0

        total_executions = ai_total + auto_total
        total_successful = ai_successful + auto_successful
        total_failed = ai_failed + auto_failed
        total_retries = int(ai_retry_sum) + int(auto_retry_sum)

        exec_success_rate = round(total_successful / total_executions * 100, 2) if total_executions > 0 else 100.0
        policies = AutomationIntelligencePolicy.objects.filter(tenant_id=tenant_id, is_enabled=True)
        auto_approve_enabled = policies.filter(auto_approve=True).count()
        auto_apply_enabled = policies.filter(auto_apply=True).count()

        return {
            'period_days': days,
            # Legacy shape expected by tests and existing clients
            'suggestions': {
                'total': total_s,
                'approved': approved,
                'rejected': rejected,
                'applied': applied,
                'dismissed': dismissed,
                'failed': failed_apply,
                'accuracy_rate': accuracy_rate,
                'average_confidence': avg_confidence,
            },
            'executions': {
                'total': total_executions,
                'ai_total': ai_total,
                'automation_total': auto_total,
                'successful': total_successful,
                'failed': total_failed,
                'retry_count': total_retries,
                'success_rate': exec_success_rate,
            },
            'policies': {
                'active': policies.count(),
                'auto_approve_enabled': auto_approve_enabled,
                'auto_apply_enabled': auto_apply_enabled,
            },
            # Newer shape
            'suggestion_metrics': {
                'suggestions_created': total_s,
                'suggestions_approved': approved,
                'suggestions_rejected': rejected,
                'suggestions_dismissed': dismissed,
                'suggestions_applied': applied,
                'suggestions_failed': failed_apply,
                'accuracy_rate': accuracy_rate,
            },
            'execution_metrics': {
                'total_executions': total_executions,
                'successful_executions': total_successful,
                'failed_executions': total_failed,
                'retry_count': total_retries,
                'success_rate': exec_success_rate,
            },
            'confidence_metrics': {
                'average_confidence': avg_confidence,
                'auto_approve_rate': auto_approve_rate,
                'auto_apply_rate': auto_apply_rate,
            },
        }

    @staticmethod
    def get_suggestion_analytics(tenant_id, days=30):
        """Suggestion lifecycle breakdown and confidence distribution."""
        since = timezone.now() - timedelta(days=days)
        suggestions = AISuggestion.objects.filter(tenant_id=tenant_id, created_at__gte=since)

        lifecycle = list(suggestions.values('status').annotate(count=Count('id')).order_by('-count'))

        by_category = list(
            suggestions.values('category').annotate(
                total=Count('id'),
                approved=Count('id', filter=Q(status='approved')),
                rejected=Count('id', filter=Q(status='rejected')),
                applied=Count('id', filter=Q(status='applied')),
            ).order_by('-total')
        )

        by_module = list(
            suggestions.values('source_module').annotate(
                total=Count('id'),
                approved=Count('id', filter=Q(status='approved')),
            ).order_by('-total')
        )

        avg_conf_result = suggestions.aggregate(avg=Avg('confidence_score'))
        avg_confidence = round(float(avg_conf_result['avg'] or 0), 4)

        high = suggestions.filter(confidence_score__gte=0.8).count()
        medium = suggestions.filter(confidence_score__gte=0.5, confidence_score__lt=0.8).count()
        low = suggestions.filter(confidence_score__lt=0.5).count()

        return {
            'period_days': days,
            'lifecycle': lifecycle,
            'by_category': by_category,
            'by_module': by_module,
            'confidence': {
                'average': avg_confidence,
                'high_count': high,
                'medium_count': medium,
                'low_count': low,
            },
        }

    @staticmethod
    def get_policy_analytics(tenant_id):
        """Automation intelligence policy effectiveness analytics."""
        policies = AutomationIntelligencePolicy.objects.filter(tenant_id=tenant_id)
        policy_metrics = []
        for policy in policies:
            base_qs = AISuggestion.objects.filter(tenant_id=tenant_id, category=policy.suggestion_type)
            if policy.module_scope:
                base_qs = base_qs.filter(source_module=policy.module_scope)

            total = base_qs.count()
            approved = base_qs.filter(status='approved').count()
            applied = base_qs.filter(status='applied').count()
            failed = base_qs.filter(last_apply_status='failed').count()

            policy_metrics.append({
                'id': str(policy.id),
                'suggestion_type': policy.suggestion_type,
                'module_scope': policy.module_scope or 'Global',
                'auto_approve': policy.auto_approve,
                'auto_apply': policy.auto_apply,
                'trigger_count': total,
                'policy_trigger_count': total,
                'auto_approve_count': approved,
                'auto_apply_count': applied,
                'failure_count': failed,
                'policy_failure_count': failed,
                'success_rate': round(applied / total * 100, 2) if total > 0 else 100.0,
                'last_triggered_at': policy.last_triggered_at.isoformat() if policy.last_triggered_at else None,
                'last_outcome': policy.last_outcome,
            })

        return {'policies': policy_metrics, 'total_policies': len(policy_metrics)}

    @staticmethod
    def get_execution_analytics(tenant_id, days=30):
        """AI and automation execution health metrics."""
        since = timezone.now() - timedelta(days=days)

        ai_runs = AIExecutionRequest.objects.filter(tenant_id=tenant_id, created_at__gte=since)
        auto_runs = AutomationExecutionRun.objects.filter(tenant_id=tenant_id, created_at__gte=since)

        ai_total = ai_runs.count()
        ai_successful = ai_runs.filter(status='completed').count()
        ai_failed = ai_runs.filter(status='failed').count()
        ai_retried = ai_runs.filter(retry_count__gt=0).count()
        ai_retry_sum = ai_runs.aggregate(total=Sum('retry_count'))['total'] or 0
        ai_success_rate = round(ai_successful / ai_total * 100, 2) if ai_total > 0 else 100.0

        auto_total = auto_runs.count()
        auto_successful = auto_runs.filter(status='completed').count()
        auto_failed = auto_runs.filter(status='failed').count()
        auto_retried = auto_runs.filter(retry_count__gt=0).count()
        auto_retry_sum = auto_runs.aggregate(total=Sum('retry_count'))['total'] or 0
        auto_success_rate = round(auto_successful / auto_total * 100, 2) if auto_total > 0 else 100.0

        total = ai_total + auto_total
        total_successful = ai_successful + auto_successful
        overall_success_rate = round(total_successful / total * 100, 2) if total > 0 else 100.0

        return {
            'period_days': days,
            'overall': {
                'total_executions': total,
                'successful_executions': total_successful,
                'failed_executions': ai_failed + auto_failed,
                'retry_count': int(ai_retry_sum) + int(auto_retry_sum),
                'success_rate': overall_success_rate,
            },
            'ai': {
                'total': ai_total,
                'successful': ai_successful,
                'failed': ai_failed,
                'retried_runs': ai_retried,
                'total_retries': int(ai_retry_sum),
                'success_rate': ai_success_rate,
            },
            'automation': {
                'total': auto_total,
                'successful': auto_successful,
                'failed': auto_failed,
                'retried_runs': auto_retried,
                'total_retries': int(auto_retry_sum),
                'success_rate': auto_success_rate,
            },
        }

    # ------------------------------------------------------------------
    # Legacy endpoints (kept for backwards compat if needed, but updated internal names)
    # ------------------------------------------------------------------

    @staticmethod
    def get_automation_analytics(tenant_id, days=30):
        # This was used by AutomationAnalyticsView - I'll keep it for now but point to new ones
        return AutomationAnalyticsService.get_overview_analytics(tenant_id, days)
