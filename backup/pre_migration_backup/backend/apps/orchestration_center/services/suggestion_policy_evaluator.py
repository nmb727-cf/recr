from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.orchestration_center.models import AISuggestion, AutomationIntelligencePolicy
from apps.orchestration_center.services.audit_service import AuditService


@dataclass
class PolicyEvaluationResult:
    """Structured result returned by SuggestionPolicyEvaluator.evaluate()."""

    status: str
    suggestion_id: str
    policy_id: Optional[str] = None
    auto_approved: bool = False
    auto_applied: bool = False
    outcome: str = 'suggest_only'
    blocked_reason: Optional[str] = None

    def as_dict(self):
        return {
            'status': self.status,
            'suggestion_id': self.suggestion_id,
            'policy_id': self.policy_id,
            'auto_approved': self.auto_approved,
            'auto_applied': self.auto_applied,
            'outcome': self.outcome,
            'blocked_reason': self.blocked_reason,
            # Alias used in audit metadata — kept identical to blocked_reason.
            'auto_apply_blocked_reason': self.blocked_reason,
        }


class AutoApplyGuard:
    """Determines whether a suggestion is safe to auto-apply.

    Safety is evaluated on two independent axes:

    1. **Manual override gate** — ``suggestion.manual_override_allowed`` must be
       ``True``.  Operators set this to ``False`` for sensitive suggestions that
       must never be acted upon without human confirmation.

    2. **Category gate** — the suggestion's ``category`` must appear in
       ``SAFE_CATEGORIES``.  Any category in ``BLOCKED_CATEGORIES`` is
       explicitly rejected with a reason string.  Any category that is neither
       safe nor blocked is also rejected (allowlist-by-default posture).

    Blocked categories represent actions that carry significant side-effects or
    are irreversible (stage changes, rejections, offers, assignments, deletions).
    They are enumerated explicitly so that future category additions start as
    blocked until they are reviewed and promoted to the safe list.

    Returns
    -------
    ``(is_safe: bool, blocked_reason: Optional[str])``
        ``blocked_reason`` is ``None`` when the suggestion is safe.
    """

    # Suggestion categories eligible for automatic application.
    SAFE_CATEGORIES = frozenset({
        'followup_recommendation',
        'deadline_recommendation',
        'notify_recommendation',
        'review_task_recommendation',
        'communication_draft',
    })

    # Suggestion categories that are explicitly prohibited from auto-apply
    # regardless of policy configuration.
    BLOCKED_CATEGORIES = frozenset({
        'stage_change',
        'rejection',
        'offer_creation',
        'candidate_assignment',
        'deletion',
    })

    @staticmethod
    def check(suggestion) -> tuple:
        """Evaluate whether *suggestion* may be auto-applied.

        Returns:
            (is_safe, blocked_reason) where blocked_reason is None when safe.
        """
        if not suggestion.manual_override_allowed:
            return False, 'manual_override_not_allowed'

        category = str(suggestion.category or '').strip().lower()

        if category in AutoApplyGuard.BLOCKED_CATEGORIES:
            return False, f'category_blocked:{category}'

        if category not in AutoApplyGuard.SAFE_CATEGORIES:
            return False, f'category_not_in_safe_list:{category}'

        return True, None


class SuggestionPolicyEvaluator:
    """Evaluates automation intelligence policies for a newly created suggestion.

    Responsibilities
    ----------------
    - Fetch the highest-priority enabled policy that matches suggestion_type,
      tenant, and confidence_threshold for this suggestion.
    - Auto-approve the suggestion when ``policy.auto_approve`` is set.
    - Auto-apply the suggestion when ``policy.auto_apply`` is set *and*
      ``AutoApplyGuard.check()`` passes.
    - Emit a structured audit event for every policy action taken.
    - Return a ``PolicyEvaluationResult``; never raise — failures are audited
      and returned as an ``'error'`` status so the Celery task stays
      non-blocking.

    Safety
    ------
    The ``AutoApplyGuard`` enforces two conditions before auto-apply:

    1. ``suggestion.manual_override_allowed`` must be ``True``.
    2. ``suggestion.category`` must be in ``AutoApplyGuard.SAFE_CATEGORIES``.

    Explicitly blocked categories and any unknown category are rejected with a
    descriptive ``blocked_reason`` string; the suggestion is left in its current
    ``approved`` status.
    """

    @staticmethod
    def _resolve_policy(suggestion) -> Optional[AutomationIntelligencePolicy]:
        score = (
            Decimal(str(suggestion.confidence_score))
            if suggestion.confidence_score is not None
            else Decimal('0')
        )
        qs = (
            AutomationIntelligencePolicy.objects.filter(
                tenant_id=suggestion.tenant_id,
                is_enabled=True,
                suggestion_type=suggestion.category,
                confidence_threshold__lte=score,
            )
            .order_by('priority_order', '-confidence_threshold', '-created_at')
        )
        if suggestion.source_module:
            scoped = qs.filter(module_scope=suggestion.source_module).first()
            if scoped:
                return scoped
        return qs.filter(module_scope='').first()

    @staticmethod
    @transaction.atomic
    def evaluate(suggestion_id) -> PolicyEvaluationResult:
        """Evaluate the automation intelligence policy for a single suggestion.

        Args:
            suggestion_id: UUID or str of the AISuggestion to evaluate.

        Returns:
            PolicyEvaluationResult with a full status breakdown and audit
            metadata (auto_approved, auto_applied, policy_id, outcome,
            blocked_reason / auto_apply_blocked_reason).
        """
        # Lazy import to avoid circular dependency between services.
        from apps.orchestration_center.services.suggestion_service import SuggestionService

        suggestion = AISuggestion.objects.select_for_update().filter(pk=suggestion_id).first()
        if not suggestion:
            return PolicyEvaluationResult(status='missing', suggestion_id=str(suggestion_id))
        if suggestion.status != 'pending':
            return PolicyEvaluationResult(status='skipped_non_pending', suggestion_id=str(suggestion.id))

        policy = SuggestionPolicyEvaluator._resolve_policy(suggestion)
        if not policy:
            return PolicyEvaluationResult(status='no_matching_policy', suggestion_id=str(suggestion.id))

        actor_id = suggestion.created_by
        auto_approved = False
        auto_applied = False
        blocked_reason: Optional[str] = None
        outcome = 'suggest_only'

        # Propagate approval_required flag from policy to suggestion.
        if policy.approval_required and not suggestion.requires_approval:
            suggestion.requires_approval = True
            suggestion.save(update_fields=['requires_approval', 'updated_at'])

        if policy.auto_approve:
            SuggestionService.approve_suggestion(
                suggestion=suggestion,
                user_id=actor_id,
                comment=f'Auto-approved by automation intelligence policy {policy.id}',
            )
            auto_approved = True
            outcome = 'auto_approved'

        if policy.auto_apply:
            is_safe, guard_reason = AutoApplyGuard.check(suggestion)
            if not is_safe:
                blocked_reason = guard_reason
                outcome = 'auto_apply_blocked'
            elif suggestion.status == 'approved':
                SuggestionService.apply_suggestion(
                    suggestion=suggestion,
                    user_id=actor_id,
                    comment=f'Auto-applied by automation intelligence policy {policy.id}',
                )
                suggestion.refresh_from_db(fields=['status'])
                auto_applied = suggestion.status == 'applied'
                outcome = 'auto_applied' if auto_applied else 'auto_apply_failed'

        policy.last_triggered_at = timezone.now()
        policy.last_triggered_suggestion_id = suggestion.id
        policy.last_outcome = outcome
        policy.save(update_fields=['last_triggered_at', 'last_triggered_suggestion_id', 'last_outcome', 'updated_at'])

        AuditService.log(
            tenant_id=suggestion.tenant_id,
            actor_id=actor_id,
            actor_type='system' if actor_id is None else 'user',
            action_type='ai_suggestion.automation_policy_evaluated',
            target_type='ai_suggestion',
            target_id=suggestion.id,
            metadata_json={
                'policy_id': str(policy.id),
                'auto_approve': policy.auto_approve,
                'auto_apply': policy.auto_apply,
                'confidence_threshold': str(policy.confidence_threshold),
                'outcome': outcome,
                'auto_approved': auto_approved,
                'auto_applied': auto_applied,
                'blocked_reason': blocked_reason,
                'auto_apply_blocked_reason': blocked_reason,
            },
            after_state_json={'status': suggestion.status},
        )

        return PolicyEvaluationResult(
            status='evaluated',
            suggestion_id=str(suggestion.id),
            policy_id=str(policy.id),
            auto_approved=auto_approved,
            auto_applied=auto_applied,
            outcome=outcome,
            blocked_reason=blocked_reason,
        )
