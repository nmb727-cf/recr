from django.db import transaction, models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.orchestration_center.models import (
    AutomationTemplate,
    AutomationIntelligencePolicy,
)

class AutomationTemplateService:
    @staticmethod
    def list_templates(tenant_id=None, include_system=True):
        """
        List templates available for a tenant.
        """
        queryset = AutomationTemplate.objects.filter(is_active=True)
        if tenant_id and include_system:
            queryset = queryset.filter(models.Q(tenant_id=tenant_id) | models.Q(is_system_template=True))
        elif tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        elif include_system:
            queryset = queryset.filter(is_system_template=True)
            
        return queryset

    @staticmethod
    def clone_template(template_id, tenant_id, performed_by=None):
        """
        Clones a system template to a tenant-specific template.
        """
        original = get_object_or_404(AutomationTemplate, id=template_id, is_active=True)
        
        # Don't clone if it's already a tenant template unless specific override is needed
        if not original.is_system_template and original.tenant_id == tenant_id:
            return original

        cloned = AutomationTemplate.objects.create(
            tenant_id=tenant_id,
            template_key=f"{original.template_key}_cloned_{timezone.now().timestamp()}",
            name=f"{original.name} (Tenant Copy)",
            description=original.description,
            category=original.category,
            trigger_type=original.trigger_type,
            action_set=original.action_set,
            condition_set=original.condition_set,
            default_risk_level=original.default_risk_level,
            recommended_confidence_threshold=original.recommended_confidence_threshold,
            is_system_template=False,
            is_active=True
        )
        return cloned

    @staticmethod
    def activate_template(template_id, tenant_id, performed_by=None):
        """
        Activates a template by creating or updating an AutomationIntelligencePolicy.
        """
        template = get_object_or_404(AutomationTemplate, id=template_id, is_active=True)
        
        # Security: ensure tenant can only activate system templates or their own
        if not template.is_system_template and template.tenant_id != tenant_id:
            raise PermissionError("Cannot activate another tenant's template.")

        with transaction.atomic():
            # Create the policy
            policy, created = AutomationIntelligencePolicy.objects.update_or_create(
                tenant_id=tenant_id,
                suggestion_type=template.trigger_type, # Using trigger_type as suggestion_type for mapping
                defaults={
                    'confidence_threshold': template.recommended_confidence_threshold,
                    'risk_level': template.default_risk_level,
                    'is_enabled': True,
                    'origin_template': template,
                    # Default enforcement based on risk level
                    'auto_approve': template.default_risk_level in ['low', 'medium'],
                    'auto_apply': template.default_risk_level == 'low',
                    'approval_required': template.default_risk_level != 'low',
                }
            )
            
            # Governance check would be integrated here if risk is high/critical
            if template.default_risk_level in ['high', 'critical']:
                # For now just set as disabled/requires review
                policy.is_enabled = False
                policy.save()

            # Audit Logging
            from apps.orchestration_center.services.ai_governance import AIGovernanceService
            AIGovernanceService.log_audit(
                tenant_id=tenant_id,
                action='policy_change',
                performed_by=performed_by,
                target_id=policy.id,
                details={
                    'event': 'template_activation',
                    'template_id': str(template.id),
                    'policy_created': created
                }
            )

            return policy

    @staticmethod
    def create_policy_from_template(template_id, tenant_id, config_overrides=None):
        """
        Specifically creates a policy with potential overrides.
        """
        template = get_object_or_404(AutomationTemplate, id=template_id, is_active=True)
        
        policy_data = {
            'tenant_id': tenant_id,
            'suggestion_type': template.trigger_type,
            'confidence_threshold': template.recommended_confidence_threshold,
            'risk_level': template.default_risk_level,
            'origin_template': template,
            'is_enabled': True
        }
        
        if config_overrides:
            policy_data.update(config_overrides)
            
        return AutomationIntelligencePolicy.objects.create(**policy_data)
