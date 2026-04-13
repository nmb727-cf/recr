from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.responses import success_response, error_response
from django.utils import timezone
from datetime import timedelta
from apps.automation_tasks.models import WorkflowTaskExecution
from apps.candidates.crm_models import CandidatePipelineStatus

class WorkspaceTaskActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        action = request.data.get('action') # 'complete', 'snooze'
        tenant_id = request.user.tenant_id
        
        if task_id.startswith('crm-'):
            # Handle CRM task
            crm_id = task_id.replace('crm-', '')
            try:
                entry = CandidatePipelineStatus.objects.get(id=crm_id, tenant_id=tenant_id)
                if action == 'complete':
                    entry.next_action = 'Completed'
                    entry.next_action_date = None
                    entry.save()
                elif action == 'snooze':
                    days = request.data.get('days', 1)
                    entry.next_action_date = timezone.now().date() + timedelta(days=days)
                    entry.save()
                return success_response(message=f"CRM Task {action}ed")
            except CandidatePipelineStatus.DoesNotExist:
                return error_response(message="Task not found", status=404)
        
        # Handle Workflow task
        try:
            task = WorkflowTaskExecution.objects.get(id=task_id, tenant_id=tenant_id)
            if action == 'complete':
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.save()
            elif action == 'snooze':
                days = request.data.get('days', 1)
                task.due_at = timezone.now() + timedelta(days=days)
                task.save()
            return success_response(message=f"Task {action}ed")
        except WorkflowTaskExecution.DoesNotExist:
            return error_response(message="Task not found", status=404)
