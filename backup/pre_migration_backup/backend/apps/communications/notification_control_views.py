"""
Notification Control Center — Views
=====================================
Admin-facing API for managing notification rules, channel settings,
and tenant preference defaults.

All endpoints require tenant admin role (enforced via permission classes).
Tenant isolation is ensured by using request.user.tenant_id throughout.
"""
import logging

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.communications.permissions import can_manage_notification_rules, can_view_notification_rules
from apps.rbac.utils import user_has_permission


def _can_manage(request) -> bool:
    return user_has_permission(request.user, 'communication.notification_rules.manage')
from apps.communications.notification_control_service import NotificationControlService
from apps.communications.notification_control_serializers import (
    NotificationRuleSerializer,
    NotificationRuleWriteSerializer,
    NotificationChannelSettingSerializer,
    NotificationChannelSettingUpdateSerializer,
    TenantNotificationPreferenceDefaultsSerializer,
)
from apps.core.responses import success_response, error_response

logger = logging.getLogger(__name__)


def _tenant_id(request):
    return request.user.tenant_id


# ---------------------------------------------------------------------------
# Notification Rules
# ---------------------------------------------------------------------------

class NotificationRuleListView(APIView):
    """
    GET  /api/v1/communications/notification-control/rules/
         Returns merged rule list (system defaults + tenant overrides).

    POST /api/v1/communications/notification-control/rules/
         Create a new tenant-level rule (or override an existing system rule).
    """
    permission_classes = [IsAuthenticated, can_view_notification_rules]

    def get(self, request):
        tid = _tenant_id(request)
        category = request.query_params.get('category')
        search = request.query_params.get('search', '').strip().lower()

        rules = NotificationControlService.list_rules(tenant_id=tid)

        if category:
            rules = [r for r in rules if r.category == category]
        if search:
            rules = [
                r for r in rules
                if search in r.business_label.lower() or search in r.event_key.lower()
            ]

        return success_response(data={
            'rules': NotificationRuleSerializer(rules, many=True).data,
            'total': len(rules),
        })

    def post(self, request):
        if not _can_manage(request):
            return error_response(message="Permission denied.", status_code=403)
        tid = _tenant_id(request)
        ser = NotificationRuleWriteSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(message='Validation error', errors=ser.errors, status_code=400)

        rule = NotificationControlService.upsert_rule(
            tenant_id=tid,
            updated_by=request.user.id,
            **ser.validated_data,
        )
        return success_response(
            data={'rule': NotificationRuleSerializer(rule).data},
            status_code=201,
        )


class NotificationRuleDetailView(APIView):
    """
    GET    /api/v1/communications/notification-control/rules/<event_key>/
    PUT    /api/v1/communications/notification-control/rules/<event_key>/
    DELETE /api/v1/communications/notification-control/rules/<event_key>/
    """
    permission_classes = [IsAuthenticated, can_view_notification_rules]

    def _get_rule(self, tenant_id, event_key):
        rule = NotificationControlService.get_rule(
            tenant_id=tenant_id,
            event_key=event_key,
        )
        return rule

    def get(self, request, event_key):
        tid = _tenant_id(request)
        rule = self._get_rule(tid, event_key)
        if not rule:
            return error_response(message='Rule not found.', status_code=404)
        return success_response(data={'rule': NotificationRuleSerializer(rule).data})

    def put(self, request, event_key):
        if not _can_manage(request):
            return error_response(message='Permission denied.', status_code=403)
        tid = _tenant_id(request)
        ser = NotificationRuleWriteSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return error_response(message='Validation error', errors=ser.errors, status_code=400)

        rule = NotificationControlService.upsert_rule(
            tenant_id=tid,
            event_key=event_key,
            updated_by=request.user.id,
            **ser.validated_data,
        )
        return success_response(data={'rule': NotificationRuleSerializer(rule).data})

    def delete(self, request, event_key):
        if not _can_manage(request):
            return error_response(message='Permission denied.', status_code=403)
        tid = _tenant_id(request)
        # Find the tenant-specific rule id
        from apps.communications.notification_control_models import NotificationRule
        rule = NotificationRule.objects.filter(
            tenant_id=tid,
            event_key=event_key,
            is_deleted=False,
        ).first()
        if not rule:
            return error_response(message='Tenant rule not found (system defaults cannot be deleted).', status_code=404)
        try:
            NotificationControlService.delete_rule(
                tenant_id=tid,
                rule_id=rule.id,
                deleted_by=request.user.id,
            )
        except ValueError as e:
            return error_response(message=str(e), status_code=400)
        return success_response(data={'deleted': True})


# ---------------------------------------------------------------------------
# Channel Settings
# ---------------------------------------------------------------------------

class NotificationChannelSettingsView(APIView):
    """
    GET /api/v1/communications/notification-control/channel-settings/
    PUT /api/v1/communications/notification-control/channel-settings/
        Body: { settings: [{channel_type, is_enabled, ...}, ...] }
    """
    permission_classes = [IsAuthenticated, can_view_notification_rules]

    def get(self, request):
        tid = _tenant_id(request)
        settings = NotificationControlService.get_channel_settings(tenant_id=tid)
        return success_response(data={
            'channel_settings': NotificationChannelSettingSerializer(settings, many=True).data,
        })

    def put(self, request):
        if not _can_manage(request):
            return error_response(message='Permission denied.', status_code=403)
        tid = _tenant_id(request)
        raw = request.data.get('settings', [])
        if not isinstance(raw, list):
            return error_response(message='`settings` must be a list.', status_code=400)

        updated = NotificationControlService.update_channel_settings(
            tenant_id=tid,
            settings=raw,
            updated_by=request.user.id,
        )
        return success_response(data={
            'channel_settings': NotificationChannelSettingSerializer(updated, many=True).data,
        })


# ---------------------------------------------------------------------------
# Default Preferences
# ---------------------------------------------------------------------------

class NotificationPreferenceDefaultsView(APIView):
    """
    GET /api/v1/communications/notification-control/default-preferences/
    PUT /api/v1/communications/notification-control/default-preferences/
    """
    permission_classes = [IsAuthenticated, can_view_notification_rules]

    def get(self, request):
        tid = _tenant_id(request)
        prefs = NotificationControlService.get_preference_defaults(tenant_id=tid)
        return success_response(data={
            'preferences': TenantNotificationPreferenceDefaultsSerializer(prefs).data,
        })

    def put(self, request):
        if not _can_manage(request):
            return error_response(message='Permission denied.', status_code=403)
        tid = _tenant_id(request)
        ser = TenantNotificationPreferenceDefaultsSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return error_response(message='Validation error', errors=ser.errors, status_code=400)
        prefs = NotificationControlService.update_preference_defaults(
            tenant_id=tid,
            **{k: v for k, v in ser.validated_data.items() if k not in ('id', 'tenant_id', 'updated_at')},
        )
        return success_response(data={
            'preferences': TenantNotificationPreferenceDefaultsSerializer(prefs).data,
        })


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class NotificationControlSummaryView(APIView):
    """
    GET /api/v1/communications/notification-control/summary/
    Returns high-level stats for the summary cards on the admin page.
    """
    permission_classes = [IsAuthenticated, can_view_notification_rules]

    def get(self, request):
        tid = _tenant_id(request)
        summary = NotificationControlService.get_summary(tenant_id=tid)
        return success_response(data={'summary': summary})
