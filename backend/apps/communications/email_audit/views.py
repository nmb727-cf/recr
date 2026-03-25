from django.db import DatabaseError, ProgrammingError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.feature_readiness import email_not_ready_response, get_email_feature_status
from apps.communications.email_audit.serializers import EmailUsageAuditSerializer
from apps.communications.models import EmailUsageAudit
from apps.communications.permissions import can_view_email_audit
from apps.core.responses import success_response


class EmailAuditListView(APIView):
    permission_classes = [IsAuthenticated, can_view_email_audit]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_audit': []})
        try:
            qs = EmailUsageAudit.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_audit': []})
        action = request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)
        return success_response(data={'email_audit': EmailUsageAuditSerializer(qs[:500], many=True).data}, meta={'total': qs.count()})
