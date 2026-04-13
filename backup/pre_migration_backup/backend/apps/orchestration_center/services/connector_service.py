from apps.orchestration_center.models import IntelligenceConnector


class ConnectorService:
    @staticmethod
    def get_connector(tenant_id, module_code):
        return (
            IntelligenceConnector.objects.filter(tenant_id__in=[tenant_id, None], module_code=module_code, is_deleted=False)
            .order_by('-tenant_id')
            .first()
        )

