from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from datetime import timedelta
from apps.orchestration_center.models.workflow import Workflow, WorkflowVersion, WorkflowExecution, WorkflowExecutionLog
from apps.orchestration_center.models.governance import WorkflowApproval, WorkflowSafetyRule, WorkflowRollbackLog, WorkflowAuditLog

class WorkflowGovernanceService:
    @staticmethod
    def create_version(workflow, config_snapshot, changed_by_id, change_summary=""):
        """Creates a new version of the workflow and updates the current version number."""
        with transaction.atomic():
            last_version = WorkflowVersion.objects.filter(workflow=workflow).order_by('-version_number').first()
            new_version_num = (last_version.version_number + 1) if last_version else 1
            
            # Deactivate all old versions
            WorkflowVersion.objects.filter(workflow=workflow).update(is_active=False)
            
            version = WorkflowVersion.objects.create(
                workflow=workflow,
                version_number=new_version_num,
                config_snapshot=config_snapshot,
                change_summary=change_summary,
                is_active=True,
                created_by=changed_by_id,
                tenant_id=workflow.tenant_id
            )
            
            workflow.current_version = new_version_num
            workflow.save()
            
            WorkflowAuditLog.objects.create(
                workflow=workflow,
                action='version_created',
                performed_by=changed_by_id,
                version_number=new_version_num,
                tenant_id=workflow.tenant_id
            )
            return version

    @staticmethod
    def request_approval(workflow, version_id, requested_by_id):
        """Requests approval for a critical workflow version."""
        version = WorkflowVersion.objects.get(pk=version_id)
        approval = WorkflowApproval.objects.create(
            workflow=workflow,
            version=version,
            requested_by=requested_by_id,
            status='pending',
            tenant_id=workflow.tenant_id
        )
        
        WorkflowAuditLog.objects.create(
            workflow=workflow,
            action='approval_requested',
            performed_by=requested_by_id,
            version_number=version.version_number,
            tenant_id=workflow.tenant_id
        )
        return approval

    @staticmethod
    def decide_approval(approval_id, approved_by_id, status, comment=""):
        """Approves or rejects a workflow version."""
        with transaction.atomic():
            approval = WorkflowApproval.objects.get(pk=approval_id)
            approval.status = status
            approval.approved_by = approved_by_id
            approval.comment = comment
            approval.decided_at = timezone.now()
            approval.save()
            
            action = 'approved' if status == 'approved' else 'rejected'
            
            WorkflowAuditLog.objects.create(
                workflow=approval.workflow,
                action=action,
                performed_by=approved_by_id,
                version_number=approval.version.version_number,
                metadata={'comment': comment},
                tenant_id=approval.workflow.tenant_id
            )
            
            # If approved, we might want to automatically activate it or 
            # let the user do it. Typically approvals for critical workflows
            # block the 'active' status.
            
            return approval

    @staticmethod
    def check_safety_limits(workflow):
        """Checks if the workflow has exceeded its execution limits."""
        try:
            rule = workflow.safety_rule
        except WorkflowSafetyRule.DoesNotExist:
            return True, ""

        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        hour_count = WorkflowExecution.objects.filter(
            workflow=workflow, 
            started_at__gte=hour_ago
        ).count()
        
        day_count = WorkflowExecution.objects.filter(
            workflow=workflow, 
            started_at__gte=day_ago
        ).count()
        
        if hour_count >= rule.max_executions_per_hour:
            WorkflowGovernanceService._handle_limit_violation(workflow, "Hourly limit exceeded")
            return False, f"Hourly limit of {rule.max_executions_per_hour} reached."
            
        if day_count >= rule.max_executions_per_day:
            WorkflowGovernanceService._handle_limit_violation(workflow, "Daily limit exceeded")
            return False, f"Daily limit of {rule.max_executions_per_day} reached."
            
        return True, ""

    @staticmethod
    def _handle_limit_violation(workflow, reason):
        workflow.status = 'paused'
        workflow.is_active = False
        workflow.save()
        
        rule = workflow.safety_rule
        rule.is_paused_by_system = True
        rule.last_violation_at = timezone.now()
        rule.save()
        
        WorkflowAuditLog.objects.create(
            workflow=workflow,
            action='limit_exceeded',
            metadata={'reason': reason},
            tenant_id=workflow.tenant_id
        )

    @staticmethod
    def detect_conflicts(workflow, event_type):
        """Detects other active workflows triggered by the same event."""
        other_workflows = Workflow.objects.filter(
            tenant_id=workflow.tenant_id,
            trigger_event=event_type,
            is_active=True
        ).exclude(pk=workflow.id)
        
        if other_workflows.exists():
            # In a real system, we'd compare the actions to see if they conflict
            # (e.g. one rejects, one moves to next stage)
            return list(other_workflows)
        return []

    @staticmethod
    def rollback_execution(execution_id, performed_by_id):
        """Rolls back the effects of a workflow execution."""
        with transaction.atomic():
            execution = WorkflowExecution.objects.get(pk=execution_id)
            logs = WorkflowExecutionLog.objects.filter(execution=execution).order_by('-executed_at')
            
            rollback_details = []
            
            for log in logs:
                if log.state_before:
                    # Logic to restore the state would go here.
                    # This is highly specific to the entity type (Candidate, Job, etc.)
                    # For Phase 11, we'll log the intention and details.
                    rollback_details.append({
                        'node_id': str(log.node_id),
                        'message': log.message,
                        'restored_state': log.state_before
                    })
            
            execution.status = 'rolled_back'
            execution.save()
            
            rollback_log = WorkflowRollbackLog.objects.create(
                execution=execution,
                performed_by=performed_by_id,
                status='completed',
                details={'steps': rollback_details},
                tenant_id=execution.tenant_id
            )
            
            WorkflowAuditLog.objects.create(
                workflow=execution.workflow,
                action='rollback',
                performed_by=performed_by_id,
                execution_id=execution.id,
                tenant_id=execution.tenant_id
            )
            
            return rollback_log

    @staticmethod
    def log_activity(workflow, action, performed_by=None, execution_id=None, metadata=None):
        """Utility to log any workflow activity."""
        return WorkflowAuditLog.objects.create(
            workflow=workflow,
            action=action,
            performed_by=performed_by,
            execution_id=execution_id,
            metadata=metadata or {},
            tenant_id=workflow.tenant_id
        )
