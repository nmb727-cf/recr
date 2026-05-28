from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from apps.orchestration_center.models import (
    AutomationIntelligencePolicy,
    AutomationUsageLimit,
    TenantIntelligenceSettings,
    AutomationGovernanceAudit,
    AIExecutionRequest,
    AutomationExecutionRun,
    AIGovernanceApproval,
)

class AIGovernanceService:
    @staticmethod
    def approve_request(tenant_id, approval_id, approved_by_id, reason=''):
        approval = AIGovernanceApproval.objects.filter(
            id=approval_id,
            tenant_id=tenant_id,
        ).first()
        if not approval:
            raise ValueError('Approval request not found.')
        if approval.approval_status != 'pending':
            raise ValueError('Approval request is not pending.')

        approval.approval_status = 'approved'
        approval.approved_by = approved_by_id
        approval.rejected_by = None
        approval.reason = reason or ''
        approval.save(update_fields=['approval_status', 'approved_by', 'rejected_by', 'reason', 'updated_at'])

        AIGovernanceService.log_audit(
            tenant_id,
            'manual_override',
            performed_by=approved_by_id,
            target_id=approval.id,
            details={'request_type': approval.request_type, 'decision': 'approved'},
        )
        return approval

    @staticmethod
    def reject_request(tenant_id, approval_id, rejected_by_id, reason=''):
        approval = AIGovernanceApproval.objects.filter(
            id=approval_id,
            tenant_id=tenant_id,
        ).first()
        if not approval:
            raise ValueError('Approval request not found.')
        if approval.approval_status != 'pending':
            raise ValueError('Approval request is not pending.')

        approval.approval_status = 'rejected'
        approval.rejected_by = rejected_by_id
        approval.approved_by = None
        approval.reason = reason or ''
        approval.save(update_fields=['approval_status', 'rejected_by', 'approved_by', 'reason', 'updated_at'])

        AIGovernanceService.log_audit(
            tenant_id,
            'manual_override',
            performed_by=rejected_by_id,
            target_id=approval.id,
            details={'request_type': approval.request_type, 'decision': 'rejected'},
        )
        return approval

    @staticmethod
    def check_governance_rules(tenant_id, policy_id=None, action_type='auto_apply'):
        """
        Validates if an action is allowed based on risk levels and kill switches.
        """
        settings = TenantIntelligenceSettings.objects.filter(tenant_id=tenant_id).first()
        if not settings:
            return False, "Tenant settings not found."
        
        # Kill Switches
        if not settings.ai_enabled:
            return False, "AI is disabled for this tenant."
        
        if action_type in ['auto_approve', 'auto_apply']:
            if not settings.automation_enabled:
                return False, "Automation is disabled for this tenant."
            
            if action_type == 'auto_apply' and not settings.auto_apply_enabled:
                return False, "Auto-apply is disabled for this tenant."

        # Policy Risk Levels
        if policy_id:
            policy = AutomationIntelligencePolicy.objects.filter(id=policy_id, tenant_id=tenant_id).first()
            if not policy:
                return False, "Policy not found."
            
            if not policy.is_enabled:
                return False, "Policy is disabled."

            # Enforcement Rules:
            # low → auto apply allowed
            # medium → approval required
            # high → admin approval required
            # critical → manual only
            
            if policy.risk_level == 'critical':
                return False, "Critical risk level requires manual intervention."
            
            if action_type == 'auto_apply':
                if not policy.auto_apply_allowed:
                    return False, "Auto-apply not allowed for this policy."
                
                if policy.risk_level in ['medium', 'high']:
                    return False, f"{policy.risk_level.capitalize()} risk requires explicit approval."

        return True, "Action allowed."

    @staticmethod
    def check_usage_limits(tenant_id):
        """
        Checks if the tenant has exceeded daily or hourly limits.
        """
        limits = AutomationUsageLimit.objects.filter(tenant_id=tenant_id).first()
        if not limits:
            return True, "No limits configured."

        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        # Count executions in last hour/day
        hourly_count = AIExecutionRequest.objects.filter(tenant_id=tenant_id, created_at__gte=hour_ago).count()
        daily_count = AIExecutionRequest.objects.filter(tenant_id=tenant_id, created_at__gte=day_ago).count()

        if hourly_count >= limits.hourly_limit:
            AIGovernanceService.log_audit(tenant_id, 'limit_exceeded', details={'limit': 'hourly', 'count': hourly_count})
            return False, "Hourly automation limit exceeded."
        
        if daily_count >= limits.daily_limit:
            AIGovernanceService.log_audit(tenant_id, 'limit_exceeded', details={'limit': 'daily', 'count': daily_count})
            return False, "Daily automation limit exceeded."

        return True, "Within limits."

    @staticmethod
    def log_audit(tenant_id, action, performed_by=None, target_id=None, details=None):
        return AutomationGovernanceAudit.objects.create(
            tenant_id=tenant_id,
            action=action,
            performed_by=performed_by,
            target_id=target_id,
            details=details or {}
        )

    @staticmethod
    def get_governance_summary(tenant_id):
        settings = TenantIntelligenceSettings.objects.filter(tenant_id=tenant_id).first()
        limits = AutomationUsageLimit.objects.filter(tenant_id=tenant_id).first()
        
        return {
            'settings': {
                'ai_enabled': settings.ai_enabled if settings else False,
                'automation_enabled': settings.automation_enabled if settings else False,
                'auto_apply_enabled': settings.auto_apply_enabled if settings else False,
            },
            'limits': {
                'daily_limit': limits.daily_limit if limits else 1000,
                'hourly_limit': limits.hourly_limit if limits else 100,
                'max_auto_apply': limits.max_auto_apply if limits else 500,
                'max_failures': limits.max_failures if limits else 50,
            }
        }
