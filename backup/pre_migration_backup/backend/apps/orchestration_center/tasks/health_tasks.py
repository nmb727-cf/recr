from celery import shared_task

from apps.orchestration_center.constants.execution_statuses import HealthStatus
from apps.orchestration_center.models import AIProvider
from apps.orchestration_center.services.provider_router import ProviderRouter


@shared_task(bind=True)
def health_check_provider(self, provider_id):
    provider = AIProvider.objects.get(pk=provider_id)
    try:
        ProviderRouter.update_provider_health(provider=provider, health_status=HealthStatus.HEALTHY)
        return {'provider_id': str(provider_id), 'status': 'healthy'}
    except Exception:
        ProviderRouter.update_provider_health(provider=provider, health_status=HealthStatus.UNHEALTHY)
        return {'provider_id': str(provider_id), 'status': 'unhealthy'}
