from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.responses import success_response, error_response
from apps.integrations.models import Integration, IntegrationCategory, IntegrationStatus
from apps.integrations.serializers import IntegrationSerializer

class IntegrationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        integrations = Integration.objects.filter(tenant_id=request.user.tenant_id)
        serializer = IntegrationSerializer(integrations, many=True)
        return success_response(data={'integrations': serializer.data}, message="Integrations retrieved.")

    def post(self, request):
        # Initializing or updating an integration
        provider_key = request.data.get('provider_key')
        if not provider_key:
            return error_response("provider_key is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        integration, created = Integration.objects.get_or_create(
            tenant_id=request.user.tenant_id,
            provider_key=provider_key,
            defaults={
                'name': request.data.get('name', provider_key.capitalize()),
                'category': request.data.get('category'),
                'status': IntegrationStatus.INACTIVE
            }
        )
        
        if not created:
            if 'name' in request.data: integration.name = request.data['name']
            if 'category' in request.data: integration.category = request.data['category']
            if 'status' in request.data: integration.status = request.data['status']
            if 'config_json' in request.data: integration.config_json = request.data['config_json']
            if 'is_connected' in request.data: integration.is_connected = request.data['is_connected']
            integration.save()

        serializer = IntegrationSerializer(integration)
        return success_response(data=serializer.data, message="Integration updated.")

class IntegrationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            integration = Integration.objects.get(pk=pk, tenant_id=request.user.tenant_id)
            serializer = IntegrationSerializer(integration)
            return success_response(data=serializer.data)
        except Integration.DoesNotExist:
            return error_response("Integration not found", status_code=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            integration = Integration.objects.get(pk=pk, tenant_id=request.user.tenant_id)
            integration.delete()
            return success_response(message="Integration removed.")
        except Integration.DoesNotExist:
            return error_response("Integration not found", status_code=status.HTTP_404_NOT_FOUND)
