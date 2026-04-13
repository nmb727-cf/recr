from apps.orchestration_center.constants.execution_statuses import AIExecutionStatus, ApprovalStatus, AutomationExecutionStatus, FailureStatus, HealthStatus
from apps.orchestration_center.models import AIExecutionRequest, AIProvider, ApprovalQueueItem, AutomationExecutionRun, ExecutionFailure, TenantIntelligenceSettings


def get_overview_snapshot(tenant_id):
    settings = TenantIntelligenceSettings.objects.filter(tenant_id=tenant_id).first()
    return {
        'provider_health': {
            'healthy': AIProvider.objects.filter(tenant_id__in=[tenant_id, None], health_status=HealthStatus.HEALTHY).count(),
            'warning': AIProvider.objects.filter(tenant_id__in=[tenant_id, None], health_status=HealthStatus.WARNING).count(),
            'unhealthy': AIProvider.objects.filter(tenant_id__in=[tenant_id, None], health_status=HealthStatus.UNHEALTHY).count(),
        },
        'queued_ai_count': AIExecutionRequest.objects.filter(tenant_id=tenant_id, status=AIExecutionStatus.QUEUED).count(),
        'queued_automation_count': AutomationExecutionRun.objects.filter(tenant_id=tenant_id, status__in=[AutomationExecutionStatus.QUEUED, AutomationExecutionStatus.SCHEDULED]).count(),
        'failed_count': ExecutionFailure.objects.filter(tenant_id=tenant_id, status__in=[FailureStatus.NEW, FailureStatus.TRIAGED, FailureStatus.RETRYING]).count(),
        'pending_approvals': ApprovalQueueItem.objects.filter(tenant_id=tenant_id, status=ApprovalStatus.PENDING).count(),
        'tenant_enablement': {
            'ai_enabled': getattr(settings, 'ai_enabled', False),
            'automation_enabled': getattr(settings, 'automation_enabled', False),
            'default_approval_mode': getattr(settings, 'default_approval_mode', 'suggestion_only'),
        },
    }

