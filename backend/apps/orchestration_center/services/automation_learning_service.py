"""
Automation Learning Engine.

Analyses per-policy suggestion outcome metrics and generates AISuggestion
records that recommend policy configuration improvements.  The engine is
intentionally stateless and idempotent — running it multiple times within the
same ISO week window produces at most one suggestion per (policy, rule).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class PolicyMetrics:
    policy_id: str
    suggestion_type: str
    module_scope: str
    auto_approve: bool
    auto_apply: bool
    total: int
    approved: int
    rejected: int
    applied: int
    apply_failed: int

    @property
    def total_decided(self) -> int:
        return self.approved + self.rejected

    @property
    def approval_rate(self) -> float:
        if self.total_decided == 0:
            return 0.0
        return round(self.approved / self.total_decided * 100, 2)

    @property
    def rejection_rate(self) -> float:
        if self.total_decided == 0:
            return 0.0
        return round(self.rejected / self.total_decided * 100, 2)

    @property
    def apply_success_rate(self) -> float:
        denominator = self.applied + self.apply_failed
        if denominator == 0:
            return 0.0
        return round(self.applied / denominator * 100, 2)


@dataclass
class LearningRecommendation:
    rule_key: str
    policy_id: str
    suggestion_type: str
    module_scope: str
    category: str       # 'automation_recommendation' | 'policy_improvement'
    title: str
    summary: str
    confidence_score: float
    idempotency_key: str


# ---------------------------------------------------------------------------
# LearningEvaluator
# ---------------------------------------------------------------------------

class LearningEvaluator:
    """
    Applies rule-based heuristics to a single policy's metrics and returns
    a list of LearningRecommendation objects.
    """

    # Minimum number of decided (approved + rejected) suggestions required
    # before a learning rule fires.
    MIN_SAMPLE_DECIDED = 5

    # Minimum applied suggestions before apply-level rules fire.
    MIN_SAMPLE_APPLIED = 3

    @classmethod
    def evaluate(cls, metrics: PolicyMetrics, iso_week: str) -> list[LearningRecommendation]:
        recommendations: list[LearningRecommendation] = []

        scope_label = metrics.module_scope if metrics.module_scope else 'all modules'
        type_label = metrics.suggestion_type.replace('_', ' ')

        def _idem(rule_key: str) -> str:
            return f'learning:{metrics.policy_id}:{rule_key}:{iso_week}'

        # Rule 1 — Enable auto-approve
        # Fires when approval rate is high but auto-approve is still off.
        if (
            not metrics.auto_approve
            and metrics.total_decided >= cls.MIN_SAMPLE_DECIDED
            and metrics.approval_rate > 90.0
        ):
            score = min(0.99, metrics.approval_rate / 100 * 1.05)
            recommendations.append(LearningRecommendation(
                rule_key='enable_auto_approve',
                policy_id=metrics.policy_id,
                suggestion_type=metrics.suggestion_type,
                module_scope=metrics.module_scope,
                category='automation_recommendation',
                title=f'Enable auto-approve for {type_label} ({scope_label})',
                summary=(
                    f'Over the last 30 days, {metrics.approval_rate:.1f}% of '
                    f'{type_label} suggestions were approved '
                    f'({metrics.approved}/{metrics.total_decided} decisions). '
                    f'Enabling auto-approve on this policy would reduce manual review '
                    f'workload without significant risk of incorrect approvals.'
                ),
                confidence_score=round(score, 2),
                idempotency_key=_idem('enable_auto_approve'),
            ))

        # Rule 2 — Enable auto-apply
        # Fires when apply success rate is very high but auto-apply is still off.
        if (
            not metrics.auto_apply
            and metrics.applied >= cls.MIN_SAMPLE_APPLIED
            and metrics.apply_success_rate > 95.0
        ):
            score = min(0.97, metrics.apply_success_rate / 100 * 1.02)
            recommendations.append(LearningRecommendation(
                rule_key='enable_auto_apply',
                policy_id=metrics.policy_id,
                suggestion_type=metrics.suggestion_type,
                module_scope=metrics.module_scope,
                category='automation_recommendation',
                title=f'Enable auto-apply for {type_label} ({scope_label})',
                summary=(
                    f'Over the last 30 days, {metrics.apply_success_rate:.1f}% of '
                    f'applied {type_label} suggestions succeeded '
                    f'({metrics.applied} applied, {metrics.apply_failed} failed). '
                    f'The high success rate makes this policy a strong candidate for '
                    f'fully autonomous execution.'
                ),
                confidence_score=round(score, 2),
                idempotency_key=_idem('enable_auto_apply'),
            ))

        # Rule 3 — Disable auto-approve (performance degradation signal)
        # Fires when auto-approve is on but approval rate has dropped below 30%.
        if (
            metrics.auto_approve
            and metrics.total_decided >= cls.MIN_SAMPLE_DECIDED
            and metrics.approval_rate < 30.0
        ):
            recommendations.append(LearningRecommendation(
                rule_key='disable_auto_approve',
                policy_id=metrics.policy_id,
                suggestion_type=metrics.suggestion_type,
                module_scope=metrics.module_scope,
                category='policy_improvement',
                title=f'Review auto-approve for {type_label} ({scope_label})',
                summary=(
                    f'Only {metrics.approval_rate:.1f}% of auto-approved '
                    f'{type_label} suggestions were correct '
                    f'({metrics.approved}/{metrics.total_decided} decisions). '
                    f'Consider disabling auto-approve and reviewing the policy '
                    f'confidence threshold to reduce incorrect automation.'
                ),
                confidence_score=0.85,
                idempotency_key=_idem('disable_auto_approve'),
            ))

        # Rule 4 — High rejection rate on non-automated policy (accuracy signal)
        # Fires when the rejection rate is very high and no auto-approve is active.
        if (
            not metrics.auto_approve
            and metrics.total_decided >= cls.MIN_SAMPLE_DECIDED
            and metrics.rejection_rate > 70.0
        ):
            recommendations.append(LearningRecommendation(
                rule_key='high_rejection_rate',
                policy_id=metrics.policy_id,
                suggestion_type=metrics.suggestion_type,
                module_scope=metrics.module_scope,
                category='policy_improvement',
                title=f'High rejection rate for {type_label} ({scope_label}) — review policy',
                summary=(
                    f'{metrics.rejection_rate:.1f}% of {type_label} suggestions were '
                    f'rejected ({metrics.rejected}/{metrics.total_decided} decisions). '
                    f'Consider raising the confidence threshold or narrowing the module '
                    f'scope to improve suggestion quality.'
                ),
                confidence_score=0.75,
                idempotency_key=_idem('high_rejection_rate'),
            ))

        return recommendations


# ---------------------------------------------------------------------------
# AutomationLearningService
# ---------------------------------------------------------------------------

class AutomationLearningService:
    """
    Entry point for the learning engine.  Call `run_for_tenant` (or
    `run_for_all_tenants`) from a Celery task.
    """

    ANALYTICS_WINDOW_DAYS = 30

    @staticmethod
    def _collect_metrics(policy) -> PolicyMetrics:
        from apps.orchestration_center.models import AISuggestion

        since = timezone.now() - timedelta(days=AutomationLearningService.ANALYTICS_WINDOW_DAYS)
        qs = AISuggestion.objects.filter(
            tenant_id=policy.tenant_id,
            category=policy.suggestion_type,
            created_at__gte=since,
            is_deleted=False,
        )
        # If module_scope is set, restrict to that module; otherwise use all.
        if policy.module_scope:
            qs = qs.filter(source_module=policy.module_scope)

        return PolicyMetrics(
            policy_id=str(policy.id),
            suggestion_type=policy.suggestion_type,
            module_scope=policy.module_scope or '',
            auto_approve=policy.auto_approve,
            auto_apply=policy.auto_apply,
            total=qs.count(),
            approved=qs.filter(status='approved').count(),
            rejected=qs.filter(status='rejected').count(),
            applied=qs.filter(status='applied').count(),
            apply_failed=qs.filter(last_apply_status='failed').count(),
        )

    @staticmethod
    def _persist_recommendation(tenant_id, rec: LearningRecommendation) -> Optional[str]:
        """
        Create an AISuggestion for the recommendation.  Returns the suggestion
        id on creation, or None if the idempotency key already exists.
        """
        from apps.orchestration_center.models import AISuggestion

        if AISuggestion.objects.filter(idempotency_key=rec.idempotency_key).exists():
            return None

        try:
            suggestion = AISuggestion.objects.create(
                tenant_id=tenant_id,
                suggestion_key=rec.rule_key,
                category=rec.category,
                status='pending',
                source_module='automation_learning_engine',
                source_event='learning.policy_analysis',
                source_entity_type='automation_intelligence_policy',
                source_entity_id=rec.policy_id,
                owner_module='automation_learning_engine',
                proposed_action_family='policy_configuration',
                title=rec.title,
                summary=rec.summary,
                confidence_score=Decimal(str(round(rec.confidence_score, 2))),
                requires_approval=False,
                manual_override_allowed=True,
                idempotency_key=rec.idempotency_key,
                payload_json={
                    'policy_id': rec.policy_id,
                    'rule_key': rec.rule_key,
                    'suggestion_type': rec.suggestion_type,
                    'module_scope': rec.module_scope,
                },
            )
            return str(suggestion.id)
        except IntegrityError:
            # Race condition — another worker created it first.
            return None

    @staticmethod
    def run_for_tenant(tenant_id) -> dict:
        """
        Evaluate all enabled policies for the given tenant and generate
        learning suggestions.  Returns a summary dict.
        """
        from apps.orchestration_center.models import AutomationIntelligencePolicy

        # ISO week string used in idempotency keys (one suggestion per rule per week).
        now = timezone.now()
        iso_week = now.strftime('%G-W%V')  # e.g. '2026-W14'

        policies = AutomationIntelligencePolicy.objects.filter(
            tenant_id=tenant_id,
            is_enabled=True,
            is_deleted=False,
        )

        created_ids: list[str] = []
        skipped = 0

        for policy in policies:
            metrics = AutomationLearningService._collect_metrics(policy)
            recommendations = LearningEvaluator.evaluate(metrics, iso_week)
            for rec in recommendations:
                sid = AutomationLearningService._persist_recommendation(tenant_id, rec)
                if sid:
                    created_ids.append(sid)
                else:
                    skipped += 1

        return {
            'tenant_id': str(tenant_id),
            'policies_evaluated': policies.count(),
            'suggestions_created': len(created_ids),
            'suggestions_skipped_idempotent': skipped,
            'suggestion_ids': created_ids,
        }

    @staticmethod
    def run_for_all_tenants() -> dict:
        """
        Evaluate all tenants that have at least one enabled policy.
        Intended for the periodic Celery beat task.
        """
        from apps.orchestration_center.models import AutomationIntelligencePolicy

        tenant_ids = (
            AutomationIntelligencePolicy.objects
            .filter(is_enabled=True, is_deleted=False, tenant_id__isnull=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )

        total_created = 0
        results = []
        for tenant_id in tenant_ids:
            result = AutomationLearningService.run_for_tenant(tenant_id)
            total_created += result['suggestions_created']
            results.append(result)

        return {
            'tenants_processed': len(results),
            'total_suggestions_created': total_created,
            'tenant_results': results,
        }
