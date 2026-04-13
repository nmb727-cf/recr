from django.utils import timezone
from django.db.models import Count, Q
from apps.automation.models import AutomationRule, AutomationLog
from apps.jobs.models import JobRequisition
from apps.pipeline.models import ActionDeadline

class GlobalAutomationOrchestratorService:
    @staticmethod
    def get_orchestrator_dashboard(tenant_id):
        # 1. Overview Metrics
        total_rules = AutomationRule.objects.filter(tenant_id=tenant_id, is_deleted=False).count()
        active_rules = AutomationRule.objects.filter(tenant_id=tenant_id, is_active=True, is_deleted=False).count()
        
        total_executions = AutomationLog.objects.filter(tenant_id=tenant_id, is_deleted=False).count()
        failed_executions = AutomationLog.objects.filter(tenant_id=tenant_id, status='failed', is_deleted=False).count()
        
        overview = {
            'total_rules': total_rules,
            'active_rules': active_rules,
            'total_executions': total_executions,
            'failed_executions': failed_executions,
            'success_rate': round(((total_executions - failed_executions) / total_executions * 100) if total_executions else 100, 1)
        }

        # 2. Automation Inventory (Grouped by trigger or active status)
        inventory_qs = AutomationRule.objects.filter(tenant_id=tenant_id, is_deleted=False).order_by('-created_at')
        inventory = []
        for rule in inventory_qs:
            inventory.append({
                'id': str(rule.id),
                'name': rule.name,
                'trigger_event': rule.trigger_event,
                'is_active': rule.is_active,
                'execution_count': rule.execution_count,
                'last_executed_at': rule.last_executed_at,
                'actions_count': len(rule.actions) if rule.actions else 0,
            })

        # 3. Execution Activity (Recent)
        recent_logs = AutomationLog.objects.filter(tenant_id=tenant_id, is_deleted=False).order_by('-executed_at')[:50]
        execution_activity = []
        for log in recent_logs:
            execution_activity.append({
                'id': str(log.id),
                'rule_id': str(log.rule_id),
                'trigger_event': log.trigger_event,
                'status': log.status,
                'error_message': log.error_message,
                'executed_at': log.executed_at,
                'entity_type': log.entity_type,
                'entity_id': str(log.entity_id) if log.entity_id else None,
            })

        # 4. Failed/Blocked Automations
        failed_logs = AutomationLog.objects.filter(
            tenant_id=tenant_id, status='failed', is_deleted=False
        ).order_by('-executed_at')[:20]
        failed_blocked = []
        for log in failed_logs:
            failed_blocked.append({
                'id': str(log.id),
                'rule_id': str(log.rule_id),
                'trigger_event': log.trigger_event,
                'error_message': log.error_message,
                'executed_at': log.executed_at,
                'entity_type': log.entity_type,
            })

        # 5. Job-Level Automation Summary & Coverage
        active_jobs = JobRequisition.objects.filter(tenant_id=tenant_id, status='active', is_deleted=False)
        total_active_jobs = active_jobs.count()
        jobs_with_automation = active_jobs.filter(auto_distribute_to_agencies=True).count()
        jobs_with_sla = active_jobs.filter(sla_automation_enabled=True).count()
        
        coverage = {
            'total_active_jobs': total_active_jobs,
            'jobs_with_automation': jobs_with_automation,
            'jobs_with_sla': jobs_with_sla,
            'automation_coverage_pct': round((jobs_with_automation / total_active_jobs * 100) if total_active_jobs else 0, 1),
            'sla_coverage_pct': round((jobs_with_sla / total_active_jobs * 100) if total_active_jobs else 0, 1)
        }

        # 6. Manual Review Queue (Pending SLA Deadlines)
        overdue_deadlines = ActionDeadline.objects.filter(
            tenant_id=tenant_id,
            deadline_at__lt=timezone.now(),
            completed_at__isnull=True,
            status='pending'
        ).order_by('-deadline_at')[:20]
        
        manual_review_queue = []
        for dl in overdue_deadlines:
            manual_review_queue.append({
                'id': str(dl.id),
                'entity_type': dl.entity_type,
                'action_required': dl.action_required,
                'deadline_at': dl.deadline_at,
            })

        return {
            'overview': overview,
            'inventory': inventory,
            'execution_activity': execution_activity,
            'failed_blocked': failed_blocked,
            'coverage': coverage,
            'manual_review_queue': manual_review_queue
        }
