"""
Communication Analytics API Views
===================================
Seven reporting endpoints backed entirely by CommunicationAnalyticsService.

All views:
  • Require authentication (IsAuthenticated)
  • Gate on tenant_id from request.user — no cross-tenant data possible
  • Delegate all query logic to the service layer
  • Return standard success_response / error_response envelopes

Permission model (Phase 1):
  Tenant isolation is enforced via tenant_id scoping.
  Any authenticated user may query analytics scoped to their tenant.
  The workload report exposes only user_ids and counts — no message content.
"""
import logging
from uuid import UUID

from django.utils.dateparse import parse_datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.analytics_service import CommunicationAnalyticsService
from apps.core.responses import success_response, error_response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_dt(value: str):
    """Parse an ISO-8601 datetime string. Returns None on failure."""
    if not value:
        return None
    try:
        return parse_datetime(value)
    except (ValueError, TypeError):
        return None


def _parse_uuid(value: str):
    """Return UUID if value is a valid UUID string, else None."""
    if not value:
        return None
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        return None


def _parse_int(value, default: int, minimum: int = 0, maximum: int = 200) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(n, maximum))


# ---------------------------------------------------------------------------
# 1. Dashboard
# ---------------------------------------------------------------------------

class CommunicationDashboardView(APIView):
    """
    GET /api/v1/communication-analytics/dashboard/

    Returns a unified KPI dict: messaging volume, thread counts, notification
    summary (read-rates, fallbacks, escalations), and delivery health.

    Query params:
      date_from  — ISO-8601 datetime (inclusive lower bound)
      date_to    — ISO-8601 datetime (inclusive upper bound)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))

        try:
            data = CommunicationAnalyticsService.get_communication_dashboard_metrics(
                tenant_id=tenant_id,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as exc:
            logger.exception("Dashboard metrics failed for tenant %s: %s", tenant_id, exc)
            return error_response(
                "Failed to load dashboard metrics.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)


# ---------------------------------------------------------------------------
# 2. Channel Performance
# ---------------------------------------------------------------------------

class ChannelPerformanceView(APIView):
    """
    GET /api/v1/communication-analytics/channels/

    Per-channel delivery statistics merged from NotificationDelivery and
    CommunicationDelivery.  Includes success_rate, failure_rate, and a
    best/worst channel summary.

    Query params:
      date_from, date_to  — date range
      channel_type        — filter to a single channel (email, whatsapp, sms, push, in_app)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))
        channel_type = request.query_params.get("channel_type", "")

        try:
            data = CommunicationAnalyticsService.get_channel_performance_report(
                tenant_id=tenant_id,
                date_from=date_from,
                date_to=date_to,
                channel_type=channel_type,
            )
        except Exception as exc:
            logger.exception("Channel performance failed for tenant %s: %s", tenant_id, exc)
            return error_response(
                "Failed to load channel performance report.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)


# ---------------------------------------------------------------------------
# 3. Notification Effectiveness
# ---------------------------------------------------------------------------

class NotificationEffectivenessView(APIView):
    """
    GET /api/v1/communication-analytics/notifications/

    Read rates, expiry rates, fallback trigger rates broken down by
    category (notification type) and severity.

    Query params:
      date_from, date_to  — date range
      category            — filter by notification type string
      priority            — filter by severity (info, medium, high, critical)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))
        category = request.query_params.get("category", "")
        priority = request.query_params.get("priority", "")

        try:
            data = CommunicationAnalyticsService.get_notification_effectiveness_report(
                tenant_id=tenant_id,
                date_from=date_from,
                date_to=date_to,
                category=category,
                priority=priority,
            )
        except Exception as exc:
            logger.exception(
                "Notification effectiveness failed for tenant %s: %s", tenant_id, exc
            )
            return error_response(
                "Failed to load notification effectiveness report.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)


# ---------------------------------------------------------------------------
# 4. Response Times
# ---------------------------------------------------------------------------

class ResponseTimeView(APIView):
    """
    GET /api/v1/communication-analytics/response-times/

    First-response-time percentiles (avg, p50, p90) computed via PostgreSQL
    CTE, plus notification read-latency by severity.

    Query params:
      date_from, date_to  — date range
      thread_type         — filter by thread_type
      user_id             — filter to a specific sender's threads
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))
        thread_type = request.query_params.get("thread_type", "")
        user_id = _parse_uuid(request.query_params.get("user_id"))

        try:
            data = CommunicationAnalyticsService.get_response_time_report(
                tenant_id=tenant_id,
                date_from=date_from,
                date_to=date_to,
                thread_type=thread_type,
                user_id=user_id,
            )
        except Exception as exc:
            logger.exception("Response time report failed for tenant %s: %s", tenant_id, exc)
            return error_response(
                "Failed to load response time report.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)


# ---------------------------------------------------------------------------
# 5. Workload
# ---------------------------------------------------------------------------

class WorkloadView(APIView):
    """
    GET /api/v1/communication-analytics/workload/

    Per-user communication load: messages sent, thread participation, and
    unread notification backlog.  Returns ranked lists suitable for team
    visibility widgets.  No message content is exposed.

    Query params:
      date_from, date_to  — date range
      user_id             — return single-user summary if provided
      limit               — max rows per ranked list (default 20, max 50)
      offset              — pagination offset
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))
        user_id = _parse_uuid(request.query_params.get("user_id"))
        limit = _parse_int(request.query_params.get("limit"), default=20, maximum=50)
        offset = _parse_int(request.query_params.get("offset"), default=0)

        try:
            data = CommunicationAnalyticsService.get_workload_report(
                tenant_id=tenant_id,
                date_from=date_from,
                date_to=date_to,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        except Exception as exc:
            logger.exception("Workload report failed for tenant %s: %s", tenant_id, exc)
            return error_response(
                "Failed to load workload report.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)


# ---------------------------------------------------------------------------
# 6. Fallback / Escalation
# ---------------------------------------------------------------------------

class FallbackEscalationView(APIView):
    """
    GET /api/v1/communication-analytics/fallbacks/

    Fallback automation job analytics and escalation log analytics.

    cancel_rate: fraction of fallback jobs cancelled because the
    notification was read before the job fired — a high value is healthy.

    noisy_triggers: event_keys that most frequently trigger executed
    fallbacks — candidates for rule tuning.

    Query params:
      date_from, date_to  — date range
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))

        try:
            data = CommunicationAnalyticsService.get_fallback_escalation_report(
                tenant_id=tenant_id,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as exc:
            logger.exception(
                "Fallback/escalation report failed for tenant %s: %s", tenant_id, exc
            )
            return error_response(
                "Failed to load fallback/escalation report.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)


# ---------------------------------------------------------------------------
# 7. Entity Communication
# ---------------------------------------------------------------------------

class EntityCommunicationView(APIView):
    """
    GET /api/v1/communication-analytics/entities/

    Communication activity grouped by business entity.

    With entity_id: detailed breakdown for a single entity.
    Without entity_id: ranked list of most active entities.

    Query params:
      entity_type  — candidate, job, application, interview, offer, agency
      entity_id    — UUID (optional, narrows to single entity)
      date_from, date_to  — date range
      limit        — max entities in list mode (default 20, max 100)
      offset       — pagination offset
    """
    permission_classes = [IsAuthenticated]

    VALID_ENTITY_TYPES = {
        "candidate", "job", "application", "interview", "offer", "agency", ""
    }

    def get(self, request):
        tenant_id = request.user.tenant_id
        entity_type = request.query_params.get("entity_type", "")
        entity_id = _parse_uuid(request.query_params.get("entity_id"))
        date_from = _parse_dt(request.query_params.get("date_from"))
        date_to = _parse_dt(request.query_params.get("date_to"))
        limit = _parse_int(request.query_params.get("limit"), default=20, maximum=100)
        offset = _parse_int(request.query_params.get("offset"), default=0)

        if entity_type not in self.VALID_ENTITY_TYPES:
            return error_response(
                f"Invalid entity_type '{entity_type}'. "
                f"Must be one of: {', '.join(sorted(self.VALID_ENTITY_TYPES) - {''})}.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if entity_id and not entity_type:
            return error_response(
                "entity_type is required when entity_id is provided.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = CommunicationAnalyticsService.get_entity_communication_report(
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
            )
        except Exception as exc:
            logger.exception(
                "Entity communication report failed for tenant %s: %s", tenant_id, exc
            )
            return error_response(
                "Failed to load entity communication report.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(data=data)
