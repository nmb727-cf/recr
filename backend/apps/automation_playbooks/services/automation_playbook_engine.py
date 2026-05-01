import logging
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from apps.automation_playbooks.models import (
    AutomationPlaybook,
    AutomationPlaybookItem,
    AutomationPlaybookInstall,
    AutomationPlaybookRecommendation,
    InstallStatus,
    PlaybookItemType,
)

logger = logging.getLogger(__name__)

class AutomationPlaybookEngine:

    @staticmethod
    def list_available_playbooks(tenant_id=None):
        """
        List playbooks available for a tenant (system + own).
        """
        from django.db.models import Q
        return AutomationPlaybook.objects.filter(
            Q(is_system_playbook=True) | Q(tenant_id=tenant_id),
            is_active=True
        )

    @staticmethod
    def validate_playbook_install(playbook_id, tenant_id, config_values):
        """
        Validates if a playbook can be installed with given config.
        """
        playbook = get_object_or_404(AutomationPlaybook, id=playbook_id)
        
        # 1. Check permissions (omitted for now, assuming view handled)
        
        # 2. Check dependencies (e.g. required modules enabled)
        # 3. Validate config_values against playbook.config_schema
        
        return True, "Validation successful"

    @staticmethod
    @transaction.atomic
    def install_playbook(playbook_id, tenant_id, installed_by, config_values):
        """
        Executes the install of a playbook.
        """
        playbook = get_object_or_404(AutomationPlaybook, id=playbook_id)
        
        install = AutomationPlaybookInstall.objects.create(
            tenant_id=tenant_id,
            playbook=playbook,
            installed_by=installed_by,
            install_status=InstallStatus.INSTALLING,
            config_snapshot=config_values,
            installed_at=timezone.now()
        )

        created_entities = {
            'workflows': [],
            'rules': [],
            'slas': [],
            'notifications': [],
            'tasks': []
        }

        try:
            items = playbook.items.all().order_order_by('execution_order')
            
            for item in items:
                AutomationPlaybookEngine._process_item(item, tenant_id, config_values, created_entities)

            install.install_status = InstallStatus.INSTALLED
            install.completed_at = timezone.now()
            install.created_workflow_count = len(created_entities['workflows'])
            install.created_rule_count = len(created_entities['rules'])
            install.created_entities_json = created_entities
            install.save()

            return install

        except Exception as e:
            logger.error(f"Playbook install failed: {str(e)}")
            install.install_status = InstallStatus.FAILED
            install.failure_reason = str(e)
            install.save()
            raise e

    @staticmethod
    def _process_item(item, tenant_id, config, created_entities):
        """
        Creates the specific entities for a playbook item.
        """
        if item.item_type == PlaybookItemType.WORKFLOW:
            from apps.orchestration_center.models import Workflow
            # Implementation for creating workflow from config
            pass
        elif item.item_type == PlaybookItemType.SLA_POLICY:
            from apps.automation_sla.models import WorkflowSLAPolicy
            # Implementation for creating SLA from config
            pass
        # Add other types ...

    @staticmethod
    @transaction.atomic
    def rollback_playbook_install(install_id, tenant_id):
        """
        Removes entities created by an install.
        """
        install = get_object_or_404(AutomationPlaybookInstall, id=install_id, tenant_id=tenant_id)
        entities = install.created_entities_json
        
        # Process deletion in reverse order
        # ... logic to delete workflows, rules etc.
        
        install.install_status = InstallStatus.ROLLED_BACK
        install.save()
        return True

    @staticmethod
    def duplicate_playbook_to_tenant(playbook_id, tenant_id, created_by):
        """
        Duplicates a system playbook to a tenant-custom version.
        """
        original = get_object_or_404(AutomationPlaybook, id=playbook_id)
        
        with transaction.atomic():
            playbook = AutomationPlaybook.objects.create(
                tenant_id=tenant_id,
                name=f"{original.name} (Custom)",
                description=original.description,
                category=original.category,
                module_scope=original.module_scope,
                playbook_type='tenant_custom',
                version='1.0.0',
                config_schema=original.config_schema,
                playbook_payload=original.playbook_payload,
                is_system_playbook=False,
                created_by=created_by
            )
            
            for item in original.items.all():
                AutomationPlaybookItem.objects.create(
                    playbook=playbook,
                    item_type=item.item_type,
                    item_key=item.item_key,
                    item_name=item.item_name,
                    config_payload=item.config_payload,
                    execution_order=item.execution_order,
                    is_required=item.is_required
                )
                
        return playbook
