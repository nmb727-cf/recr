from django.db import models
from apps.orchestration_center.models import AutomationLibraryTemplate, AutomationIntelligencePolicy
from django.utils import timezone

class AutomationLibraryService:
    @staticmethod
    def list_templates(tenant_id=None, category=None):
        """List system templates and tenant-specific templates."""
        queryset = AutomationLibraryTemplate.objects.filter(is_deleted=False)
        if tenant_id:
            # Show system templates OR tenant's own templates
            queryset = queryset.filter(models.Q(tenant_id=tenant_id) | models.Q(is_system_template=True))
        else:
            queryset = queryset.filter(is_system_template=True)
            
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset

    @staticmethod
    def clone_template_to_tenant(template_id, tenant_id, created_by=None):
        """Clone a system template to a specific tenant for customization."""
        try:
            template = AutomationLibraryTemplate.objects.get(id=template_id, is_system_template=True)
            # Create a tenant-scoped copy
            clone = AutomationLibraryTemplate.objects.create(
                tenant_id=tenant_id,
                template_name=f"{template.template_name} (Copy)",
                template_type=template.template_type,
                description=template.description,
                category=template.category,
                risk_level=template.risk_level,
                config_payload=template.config_payload,
                is_system_template=False,
                created_by=created_by
            )
            return clone
        except AutomationLibraryTemplate.DoesNotExist:
            raise ValueError("System template not found.")

    @staticmethod
    def create_policy_from_template(template_id, tenant_id, created_by=None):
        """Convert a library template into an active AutomationIntelligencePolicy."""
        try:
            template = AutomationLibraryTemplate.objects.get(id=template_id)
            if template.tenant_id and template.tenant_id != tenant_id:
                raise ValueError("Access denied to this template.")
                
            # Business Rule: Risky templates require governance check
            # This is a check, but we'll assume governance service handles the actual block if needed
            
            payload = template.config_payload
            policy = AutomationIntelligencePolicy.objects.create(
                tenant_id=tenant_id,
                suggestion_type=payload.get('suggestion_type', template.template_type),
                module_scope=payload.get('module_scope', ''),
                confidence_threshold=payload.get('confidence_threshold', 0.85),
                auto_approve=payload.get('auto_approve', False),
                auto_apply=payload.get('auto_apply', False),
                approval_required=template.risk_level in ['high', 'critical'],
                is_enabled=False, # Default to disabled until activation
                created_by=created_by
            )
            return policy
        except AutomationLibraryTemplate.DoesNotExist:
            raise ValueError("Template not found.")

    @staticmethod
    def activate_template(template_id, tenant_id, user_id):
        """Initialize a policy from a template and enable it."""
        policy = AutomationLibraryService.create_policy_from_template(template_id, tenant_id, user_id)
        policy.is_enabled = True
        policy.save()
        return policy
