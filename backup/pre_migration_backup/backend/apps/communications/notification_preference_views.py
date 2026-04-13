"""
User Notification Preference Views
====================================
Endpoints for users to manage their personal notification settings.

Endpoints:
  GET  /api/v1/notifications/preferences/         — full matrix (all categories × channels)
  PUT  /api/v1/notifications/preferences/         — single preference update
  POST /api/v1/notifications/preferences/bulk/    — bulk update (list)
  POST /api/v1/notifications/preferences/reset/   — reset to system defaults
  GET  /api/v1/notifications/settings/            — global settings
  PUT  /api/v1/notifications/settings/            — update settings (partial OK)
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.communications.notification_preference_service import (
    UserNotificationPreferenceService,
)
from apps.communications.notification_preference_serializers import (
    UserNotificationPreferenceSerializer,
    UserNotificationPreferenceUpdateSerializer,
    UserNotificationPreferenceBulkUpdateSerializer,
    UserNotificationSettingSerializer,
    UserNotificationSettingUpdateSerializer,
)
from apps.core.responses import success_response, error_response


class UserNotificationPreferenceView(APIView):
    """
    GET  /api/v1/notifications/preferences/
         Returns the full preference matrix (all categories × all channels).
         System defaults are used for any row without an explicit DB entry.

    PUT  /api/v1/notifications/preferences/
         Update a single category+channel preference.
         Body: { category, channel_type, is_enabled?, min_priority? }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        matrix = UserNotificationPreferenceService.get_preference_matrix(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
        )
        # Also return explicit rows for clients that want the raw list
        raw_prefs = UserNotificationPreferenceService.get_user_preferences(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
        )
        return success_response(data={
            'matrix': matrix,
            'preferences': UserNotificationPreferenceSerializer(raw_prefs, many=True).data,
        })

    def put(self, request):
        ser = UserNotificationPreferenceUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(
                message="Invalid preference data.",
                errors=ser.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = ser.validated_data
        try:
            pref = UserNotificationPreferenceService.update_user_preference(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
                category=data['category'],
                channel_type=data['channel_type'],
                is_enabled=data.get('is_enabled'),
                min_priority=data.get('min_priority'),
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(data={
            'preference': UserNotificationPreferenceSerializer(pref).data,
        })


class UserNotificationPreferenceBulkUpdateView(APIView):
    """
    POST /api/v1/notifications/preferences/bulk/

    Body:
      { "updates": [ {category, channel_type, is_enabled?, min_priority?}, ... ] }

    Applies all updates atomically.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = UserNotificationPreferenceBulkUpdateSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(
                message="Invalid bulk preference data.",
                errors=ser.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            prefs = UserNotificationPreferenceService.bulk_update_preferences(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
                updates=ser.validated_data['updates'],
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(data={
            'updated': UserNotificationPreferenceSerializer(prefs, many=True).data,
            'count': len(prefs),
        })


class UserNotificationPreferenceResetView(APIView):
    """
    POST /api/v1/notifications/preferences/reset/

    Deletes all explicit category+channel preference rows for the user,
    reverting to system defaults.
    Global settings (quiet hours, digest, global channel toggles) are preserved.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserNotificationPreferenceService.reset_preferences(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
        )
        return success_response(message="Preferences reset to system defaults.")


class UserNotificationSettingView(APIView):
    """
    GET /api/v1/notifications/settings/
        Returns the user's global notification settings.

    PUT /api/v1/notifications/settings/
        Partial update (PATCH semantics — only provided fields are changed).
        Body: any subset of {
          quiet_hours_enabled, quiet_hours_start, quiet_hours_end, timezone,
          digest_mode, all_email_enabled, all_sms_enabled,
          all_whatsapp_enabled, all_push_enabled
        }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings = UserNotificationPreferenceService.get_user_settings(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
        )
        return success_response(data={
            'settings': UserNotificationSettingSerializer(settings).data,
        })

    def put(self, request):
        current_settings = UserNotificationPreferenceService.get_user_settings(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
        )
        ser = UserNotificationSettingUpdateSerializer(
            instance=current_settings,
            data=request.data,
            partial=True,
        )
        if not ser.is_valid():
            return error_response(
                message="Invalid settings data.",
                errors=ser.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            updated = UserNotificationPreferenceService.update_user_settings(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
                **ser.validated_data,
            )
        except ValueError as exc:
            return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(data={
            'settings': UserNotificationSettingSerializer(updated).data,
        })
