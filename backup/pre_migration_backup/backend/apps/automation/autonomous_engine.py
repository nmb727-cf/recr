from django.utils import timezone
from datetime import timedelta
from apps.orchestration_center.models.suggestion import AISuggestion
from apps.orchestration_center.models.governance import ApprovalQueueItem
from apps.automation.models import AutomationLog, AutomationRule
from apps.jobs.models import JobRequisition

class AutonomousHiringService:
    @staticmethod
    def get_autonomous_dashboard(tenant_id):
        # 1. Suggested Actions (from AISuggestion)
        suggestions_qs = AISuggestion.objects.filter(
            tenant_id=tenant_id,
            status='pending',
            requires_approval=False,
            is_deleted=False
        ).order_by('-created_at')[:20]

        suggested_actions = []
        for s in suggestions_qs:
            suggested_actions.append({
                'id': str(s.id),
                'title': s.title,
                'category': s.category,
                'summary': s.summary,
                'confidence': float(s.confidence_score) if s.confidence_score else 0,
                'created_at': s.created_at,
            })

        # 2. Pending Approvals (from ApprovalQueueItem or AISuggestion requiring approval)
        approvals_qs = ApprovalQueueItem.objects.filter(
            tenant_id=tenant_id,
            status='pending',
            is_deleted=False
        ).order_by('-created_at')[:20]

        pending_approvals = []
        for a in approvals_qs:
            pending_approvals.append({
                'id': str(a.id),
                'item_type': a.item_type,
                'requested_action': a.requested_action,
                'recommended_decision': a.recommended_decision,
                'approver_role': a.approver_role,
                'created_at': a.created_at,
            })

        # 3. Executed Actions (from AutomationLog and applied AISuggestions)
        executed_qs = AutomationLog.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False
        ).order_by('-executed_at')[:50]

        executed_actions = []
        for e in executed_qs:
            executed_actions.append({
                'id': str(e.id),
                'action_name': e.trigger_event,
                'status': e.status,
                'entity_type': e.entity_type,
                'error_message': e.error_message,
                'executed_at': e.executed_at,
            })

        # 4. Automation Settings Summary (Categories)
        settings = {
            'safe_automation': ['Recruiter Assignment', 'Agency Assignment', 'Candidate Reminders', 'Interview Scheduling', 'SLA Escalation'],
            'approval_required': ['Auto Reject Candidates', 'Auto Shortlist Candidates', 'Auto Close Job', 'Auto Change Priority'],
            'manual_only': ['Offer Approval', 'Hiring Decision', 'Compensation Changes']
        }

        # 5. Job Level Autonomous Control Summary
        active_jobs = JobRequisition.objects.filter(tenant_id=tenant_id, status='active', is_deleted=False).count()
        jobs_with_auto = JobRequisition.objects.filter(tenant_id=tenant_id, status='active', auto_distribute_to_agencies=True, is_deleted=False).count()

        overview = {
            'pending_suggestions': AISuggestion.objects.filter(tenant_id=tenant_id, status='pending', is_deleted=False).count(),
            'pending_approvals': ApprovalQueueItem.objects.filter(tenant_id=tenant_id, status='pending', is_deleted=False).count(),
            'executed_today': AutomationLog.objects.filter(tenant_id=tenant_id, executed_at__gte=timezone.now() - timedelta(days=1), is_deleted=False).count(),
            'jobs_auto_enabled': jobs_with_auto,
            'total_active_jobs': active_jobs
        }

        return {
            'overview': overview,
            'suggested_actions': suggested_actions,
            'pending_approvals': pending_approvals,
            'executed_actions': executed_actions,
            'settings': settings
        }

    @staticmethod
    def approve_action(tenant_id, user_id, action_id, item_type='suggestion'):
        if item_type == 'suggestion':
            item = AISuggestion.objects.get(id=action_id, tenant_id=tenant_id)
            item.status = 'approved'
            item.approved_by_id = user_id
            item.approved_at = timezone.now()
            item.save()
            return {"status": "approved", "id": str(item.id)}
        elif item_type == 'approval':
            item = ApprovalQueueItem.objects.get(id=action_id, tenant_id=tenant_id)
            item.status = 'approved'
            item.decided_by_id = user_id
            item.decided_at = timezone.now()
            item.save()
            return {"status": "approved", "id": str(item.id)}
        raise ValueError("Invalid item type")

    @staticmethod
    def reject_action(tenant_id, user_id, action_id, item_type='suggestion'):
        if item_type == 'suggestion':
            item = AISuggestion.objects.get(id=action_id, tenant_id=tenant_id)
            item.status = 'rejected'
            item.rejected_by_id = user_id
            item.rejected_at = timezone.now()
            item.save()
            return {"status": "rejected", "id": str(item.id)}
        elif item_type == 'approval':
            item = ApprovalQueueItem.objects.get(id=action_id, tenant_id=tenant_id)
            item.status = 'rejected'
            item.decided_by_id = user_id
            item.decided_at = timezone.now()
            item.save()
            return {"status": "rejected", "id": str(item.id)}
        raise ValueError("Invalid item type")
