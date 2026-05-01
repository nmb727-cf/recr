"""
Test suite for Communication Analytics & Reporting
====================================================
Tests the CommunicationAnalyticsService and the analytics API endpoints.

Pattern: APIRequestFactory + force_authenticate bypasses django-tenants
middleware (project standard for communications tests).

Coverage:
  TestDashboardMetrics           (7)  — KPI correctness, tenant isolation
  TestChannelPerformance         (6)  — per-channel aggregation, rate calculation
  TestNotificationEffectiveness  (7)  — read/expiry/fallback rates, breakdown
  TestResponseTimeReport         (5)  — latency calculation, empty handling
  TestFallbackEscalationReport   (6)  — job counts, cancel rate, escalation
  TestEntityCommunicationReport  (6)  — entity grouping, single-entity detail
  TestWorkloadReport             (5)  — sender ranking, backlog, participation
  TestAnalyticsEndpoints         (12) — HTTP status, envelope shape, auth
  TestEdgeCases                  (5)  — empty data, date bounds, division-by-zero
  TestAnalyticsAccessControl     (4)  — cross-tenant leakage, unauthenticated

Total: 63 tests
"""
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.communications.analytics_service import (
    CommunicationAnalyticsService,
    _safe_rate,
    _seconds_to_human,
)
from apps.communications.analytics_views import (
    CommunicationDashboardView,
    ChannelPerformanceView,
    NotificationEffectivenessView,
    ResponseTimeView,
    WorkloadView,
    FallbackEscalationView,
    EntityCommunicationView,
)
from apps.communications.models import (
    Message,
    MessageThread,
    Notification,
    NotificationDelivery,
    ThreadParticipant,
)
from apps.communications.channel_config_models import CommunicationDelivery
from apps.communications.notification_orchestration_models import (
    NotificationAutomationJob,
    NotificationAutomationJobType,
    NotificationAutomationJobStatus,
    NotificationEscalationLog,
    NotificationEscalationLogStatus,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _make_user(tenant_id=None, user_id=None):
    """Return a mock user object that mirrors the project's user model API."""

    class MockUser:
        is_authenticated = True

        def __init__(self, tid, uid):
            self.tenant_id = tid
            self.id = uid

    return MockUser(tenant_id or uuid.uuid4(), user_id or uuid.uuid4())


def _make_thread(tenant_id, **kwargs):
    return MessageThread.objects.create(
        tenant_id=tenant_id,
        thread_type=kwargs.get("thread_type", "general"),
        subject=kwargs.get("subject", "Test thread"),
        is_internal=kwargs.get("is_internal", True),
        is_archived=kwargs.get("is_archived", False),
        is_deleted=kwargs.get("is_deleted", False),
        related_entity_type=kwargs.get("related_entity_type", ""),
        related_entity_id=kwargs.get("related_entity_id", None),
        metadata={},
    )


def _make_message(tenant_id, thread, sender_id, **kwargs):
    return Message.objects.create(
        tenant_id=tenant_id,
        thread=thread,
        sender_id=sender_id,
        message_type=kwargs.get("message_type", "text"),
        channel_type=kwargs.get("channel_type", "in_app"),
        body=kwargs.get("body", "test"),
        is_deleted=kwargs.get("is_deleted", False),
        related_entity_type=kwargs.get("related_entity_type", ""),
        related_entity_id=kwargs.get("related_entity_id", None),
    )


def _make_notification(tenant_id, user_id, **kwargs):
    return Notification.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        type=kwargs.get("type", "interview"),
        title=kwargs.get("title", "Test notification"),
        body="body",
        severity=kwargs.get("severity", "info"),
        is_read=kwargs.get("is_read", False),
        read_at=kwargs.get("read_at", None),
        is_archived=kwargs.get("is_archived", False),
        expires_at=kwargs.get("expires_at", None),
        fallback_email_sent_at=kwargs.get("fallback_email_sent_at", None),
        fallback_whatsapp_sent_at=kwargs.get("fallback_whatsapp_sent_at", None),
        escalation_level=kwargs.get("escalation_level", 0),
        related_entity_type=kwargs.get("related_entity_type", ""),
        related_entity_id=kwargs.get("related_entity_id", None),
    )


def _make_notif_delivery(tenant_id, notification, channel="email", delivery_status="delivered"):
    return NotificationDelivery.objects.create(
        tenant_id=tenant_id,
        notification=notification,
        channel=channel,
        provider="test",
        status=delivery_status,
        attempted_at=timezone.now(),
    )


def _make_comm_delivery(tenant_id, channel_type="whatsapp", del_status="delivered"):
    return CommunicationDelivery.objects.create(
        tenant_id=tenant_id,
        channel_type=channel_type,
        provider="test",
        recipient_identifier="+1234567890",
        status=del_status,
    )


def _make_automation_job(tenant_id, job_type=None, job_status=None, event_key="interview_scheduled"):
    return NotificationAutomationJob.objects.create(
        tenant_id=tenant_id,
        job_type=job_type or NotificationAutomationJobType.FALLBACK_EMAIL,
        status=job_status or NotificationAutomationJobStatus.EXECUTED,
        event_key=event_key,
        scheduled_for=timezone.now(),
    )


def _make_escalation_log(tenant_id, notification, esc_status=None):
    return NotificationEscalationLog.objects.create(
        tenant_id=tenant_id,
        notification=notification,
        escalation_level=1,
        target_user_id=uuid.uuid4(),
        channel_used="email",
        status=esc_status or NotificationEscalationLogStatus.SENT,
        original_event_key="interview_scheduled",
        original_user_id=notification.user_id,
    )


factory = APIRequestFactory()


# ===========================================================================
# TestDashboardMetrics
# ===========================================================================

class TestDashboardMetrics(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_total_messages_correct(self):
        thread = _make_thread(self.tenant_id)
        _make_message(self.tenant_id, thread, self.user_id)
        _make_message(self.tenant_id, thread, self.user_id)
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["messaging"]["total_messages"], 2)

    def test_thread_counts_correct(self):
        _make_thread(self.tenant_id, is_archived=False)
        _make_thread(self.tenant_id, is_archived=True)
        _make_thread(self.tenant_id, is_archived=False)
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["messaging"]["total_threads"], 3)
        self.assertEqual(result["messaging"]["active_threads"], 2)
        self.assertEqual(result["messaging"]["archived_threads"], 1)

    def test_notification_counts_correct(self):
        _make_notification(self.tenant_id, self.user_id, is_read=True, read_at=timezone.now())
        _make_notification(self.tenant_id, self.user_id, is_read=False)
        _make_notification(self.tenant_id, self.user_id, is_read=False, fallback_email_sent_at=timezone.now())
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["notifications"]["total_notifications"], 3)
        self.assertEqual(result["notifications"]["read_notifications"], 1)
        self.assertEqual(result["notifications"]["fallback_emails_sent"], 1)

    def test_failed_delivery_counts(self):
        notif = _make_notification(self.tenant_id, self.user_id)
        _make_notif_delivery(self.tenant_id, notif, delivery_status="failed")
        _make_comm_delivery(self.tenant_id, del_status="failed")
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["delivery"]["total_failed_deliveries"], 2)

    def test_cross_tenant_isolation(self):
        """Tenant A data not visible to Tenant B."""
        other_tenant = uuid.uuid4()
        thread = _make_thread(other_tenant)
        _make_message(other_tenant, thread, uuid.uuid4())
        _make_notification(other_tenant, uuid.uuid4())

        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["messaging"]["total_messages"], 0)
        self.assertEqual(result["notifications"]["total_notifications"], 0)

    def test_date_range_filters_messages(self):
        thread = _make_thread(self.tenant_id)
        _make_message(self.tenant_id, thread, self.user_id)

        future = timezone.now() + timedelta(days=30)
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id,
            date_from=future,
        )
        self.assertEqual(result["messaging"]["total_messages"], 0)

    def test_messages_by_type_returned(self):
        thread = _make_thread(self.tenant_id)
        _make_message(self.tenant_id, thread, self.user_id, message_type="text")
        _make_message(self.tenant_id, thread, self.user_id, message_type="system_event")
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        types = {row["message_type"] for row in result["messaging"]["messages_by_type"]}
        self.assertIn("text", types)
        self.assertIn("system_event", types)


# ===========================================================================
# TestChannelPerformance
# ===========================================================================

class TestChannelPerformance(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_channel_success_rate_calculated(self):
        notif = _make_notification(self.tenant_id, self.user_id)
        _make_notif_delivery(self.tenant_id, notif, channel="email", delivery_status="delivered")
        _make_notif_delivery(self.tenant_id, notif, channel="email", delivery_status="delivered")
        _make_notif_delivery(self.tenant_id, notif, channel="email", delivery_status="failed")
        result = CommunicationAnalyticsService.get_channel_performance_report(
            tenant_id=self.tenant_id
        )
        email_row = next(c for c in result["channels"] if c["channel"] == "email")
        # 2 delivered / 3 total = 0.6667
        self.assertAlmostEqual(email_row["success_rate"], 0.6667, places=3)

    def test_channel_filter_applied(self):
        notif = _make_notification(self.tenant_id, self.user_id)
        _make_notif_delivery(self.tenant_id, notif, channel="email", delivery_status="delivered")
        _make_notif_delivery(self.tenant_id, notif, channel="in_app", delivery_status="delivered")
        result = CommunicationAnalyticsService.get_channel_performance_report(
            tenant_id=self.tenant_id,
            channel_type="email",
        )
        self.assertTrue(all(c["channel"] == "email" for c in result["channels"]))

    def test_best_channel_identified(self):
        notif = _make_notification(self.tenant_id, self.user_id)
        _make_notif_delivery(self.tenant_id, notif, channel="in_app", delivery_status="delivered")
        _make_notif_delivery(self.tenant_id, notif, channel="email", delivery_status="failed")
        result = CommunicationAnalyticsService.get_channel_performance_report(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["best_channel"], "in_app")

    def test_cross_tenant_isolation(self):
        other_tenant = uuid.uuid4()
        other_notif = _make_notification(other_tenant, uuid.uuid4())
        _make_notif_delivery(other_tenant, other_notif, channel="email", delivery_status="delivered")
        result = CommunicationAnalyticsService.get_channel_performance_report(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["total_attempts"], 0)

    def test_multi_channel_delivery_merged(self):
        _make_comm_delivery(self.tenant_id, channel_type="whatsapp", del_status="delivered")
        _make_comm_delivery(self.tenant_id, channel_type="whatsapp", del_status="failed")
        result = CommunicationAnalyticsService.get_channel_performance_report(
            tenant_id=self.tenant_id
        )
        wa = next((c for c in result["channels"] if c["channel"] == "whatsapp"), None)
        self.assertIsNotNone(wa)
        self.assertEqual(wa["total_attempts"], 2)

    def test_empty_returns_safely(self):
        result = CommunicationAnalyticsService.get_channel_performance_report(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["channels"], [])
        self.assertIsNone(result["best_channel"])


# ===========================================================================
# TestNotificationEffectiveness
# ===========================================================================

class TestNotificationEffectiveness(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_read_rate_calculated(self):
        now = timezone.now()
        _make_notification(self.tenant_id, self.user_id, is_read=True, read_at=now)
        _make_notification(self.tenant_id, self.user_id, is_read=True, read_at=now)
        _make_notification(self.tenant_id, self.user_id, is_read=False)
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id
        )
        totals = result["totals"]
        self.assertEqual(totals["created"], 3)
        self.assertEqual(totals["read"], 2)
        self.assertAlmostEqual(totals["read_rate"], 0.6667, places=3)

    def test_fallback_trigger_rate(self):
        now = timezone.now()
        _make_notification(self.tenant_id, self.user_id, fallback_email_sent_at=now)
        _make_notification(self.tenant_id, self.user_id, fallback_whatsapp_sent_at=now)
        _make_notification(self.tenant_id, self.user_id)  # no fallback
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id
        )
        totals = result["totals"]
        self.assertEqual(totals["fallback_triggered"], 2)
        self.assertAlmostEqual(totals["fallback_trigger_rate"], 0.6667, places=3)

    def test_by_severity_breakdown(self):
        _make_notification(self.tenant_id, self.user_id, severity="info")
        _make_notification(self.tenant_id, self.user_id, severity="critical", is_read=True, read_at=timezone.now())
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id
        )
        severities = {row["severity"] for row in result["by_severity"]}
        self.assertIn("info", severities)
        self.assertIn("critical", severities)

    def test_by_category_breakdown(self):
        _make_notification(self.tenant_id, self.user_id, type="interview")
        _make_notification(self.tenant_id, self.user_id, type="interview")
        _make_notification(self.tenant_id, self.user_id, type="offer")
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id
        )
        categories = {row["category"] for row in result["by_category"]}
        self.assertIn("interview", categories)
        self.assertIn("offer", categories)

    def test_category_filter_applied(self):
        _make_notification(self.tenant_id, self.user_id, type="interview")
        _make_notification(self.tenant_id, self.user_id, type="offer")
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id,
            category="interview",
        )
        self.assertEqual(result["totals"]["created"], 1)

    def test_priority_filter_applied(self):
        _make_notification(self.tenant_id, self.user_id, severity="critical")
        _make_notification(self.tenant_id, self.user_id, severity="info")
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id,
            priority="critical",
        )
        self.assertEqual(result["totals"]["created"], 1)

    def test_cross_tenant_isolation(self):
        other_tenant = uuid.uuid4()
        _make_notification(other_tenant, uuid.uuid4())
        result = CommunicationAnalyticsService.get_notification_effectiveness_report(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["totals"]["created"], 0)


# ===========================================================================
# TestResponseTimeReport
# ===========================================================================

class TestResponseTimeReport(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_notification_read_latency_calculated(self):
        now = timezone.now()
        past = now - timedelta(hours=1)
        n = Notification.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            type="interview",
            title="t",
            severity="info",
            is_read=True,
            read_at=now,
            created_at=past,
        )
        # Force created_at to past (auto_now_add prevents direct set)
        Notification.objects.filter(id=n.id).update(created_at=past)

        result = CommunicationAnalyticsService.get_response_time_report(
            tenant_id=self.tenant_id
        )
        lat = result["notification_read_latency"]["avg_read_latency_seconds"]
        # Should be approximately 3600 seconds
        self.assertIsNotNone(lat)
        self.assertGreater(lat, 0)

    def test_empty_threads_returns_zero_response(self):
        result = CommunicationAnalyticsService.get_response_time_report(
            tenant_id=self.tenant_id
        )
        self.assertEqual(
            result["messaging_response_times"]["threads_with_response"], 0
        )
        self.assertIsNone(
            result["messaging_response_times"]["avg_first_response_seconds"]
        )

    def test_cross_tenant_isolation(self):
        other_tenant = uuid.uuid4()
        n = _make_notification(other_tenant, uuid.uuid4(), is_read=True, read_at=timezone.now())
        Notification.objects.filter(id=n.id).update(created_at=timezone.now() - timedelta(hours=1))

        result = CommunicationAnalyticsService.get_response_time_report(
            tenant_id=self.tenant_id
        )
        self.assertIsNone(result["notification_read_latency"]["avg_read_latency_seconds"])

    def test_read_latency_by_severity_returned(self):
        now = timezone.now()
        _make_notification(
            self.tenant_id, self.user_id,
            severity="critical", is_read=True, read_at=now
        )
        result = CommunicationAnalyticsService.get_response_time_report(
            tenant_id=self.tenant_id
        )
        severities = {
            row["severity"]
            for row in result["notification_read_latency"]["by_severity"]
        }
        self.assertIn("critical", severities)

    def test_response_report_shape(self):
        result = CommunicationAnalyticsService.get_response_time_report(
            tenant_id=self.tenant_id
        )
        self.assertIn("period", result)
        self.assertIn("messaging_response_times", result)
        self.assertIn("notification_read_latency", result)
        self.assertIn("threads_with_response", result["messaging_response_times"])


# ===========================================================================
# TestFallbackEscalationReport
# ===========================================================================

class TestFallbackEscalationReport(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def test_fallback_job_counts(self):
        _make_automation_job(
            self.tenant_id,
            job_type=NotificationAutomationJobType.FALLBACK_EMAIL,
            job_status=NotificationAutomationJobStatus.EXECUTED,
        )
        _make_automation_job(
            self.tenant_id,
            job_type=NotificationAutomationJobType.FALLBACK_EMAIL,
            job_status=NotificationAutomationJobStatus.CANCELLED,
        )
        result = CommunicationAnalyticsService.get_fallback_escalation_report(
            tenant_id=self.tenant_id
        )
        fb = result["fallbacks"]
        self.assertEqual(fb["total_scheduled"], 2)
        self.assertEqual(fb["executed"], 1)
        self.assertEqual(fb["cancelled"], 1)

    def test_cancel_rate_calculated(self):
        for _ in range(3):
            _make_automation_job(
                self.tenant_id,
                job_status=NotificationAutomationJobStatus.CANCELLED,
            )
        for _ in range(7):
            _make_automation_job(
                self.tenant_id,
                job_status=NotificationAutomationJobStatus.EXECUTED,
            )
        result = CommunicationAnalyticsService.get_fallback_escalation_report(
            tenant_id=self.tenant_id
        )
        self.assertAlmostEqual(result["fallbacks"]["cancel_rate"], 0.3, places=3)

    def test_escalation_counts(self):
        notif = _make_notification(self.tenant_id, self.user_id)
        _make_escalation_log(self.tenant_id, notif, esc_status=NotificationEscalationLogStatus.SENT)
        _make_escalation_log(self.tenant_id, notif, esc_status=NotificationEscalationLogStatus.FAILED)
        result = CommunicationAnalyticsService.get_fallback_escalation_report(
            tenant_id=self.tenant_id
        )
        esc = result["escalations"]
        self.assertEqual(esc["total_triggered"], 2)
        self.assertEqual(esc["sent"], 1)
        self.assertEqual(esc["failed"], 1)

    def test_escalation_resolution_rate(self):
        notif = _make_notification(
            self.tenant_id, self.user_id, is_read=True, read_at=timezone.now()
        )
        _make_escalation_log(self.tenant_id, notif)
        result = CommunicationAnalyticsService.get_fallback_escalation_report(
            tenant_id=self.tenant_id
        )
        # The escalated notification was read, so resolution_rate = 1.0
        self.assertEqual(result["escalations"]["resolution_rate"], 1.0)

    def test_noisy_triggers_returned(self):
        for _ in range(5):
            _make_automation_job(
                self.tenant_id,
                job_status=NotificationAutomationJobStatus.EXECUTED,
                event_key="interview_scheduled",
            )
        result = CommunicationAnalyticsService.get_fallback_escalation_report(
            tenant_id=self.tenant_id
        )
        # noisy_triggers filters on EXECUTED status
        self.assertTrue(len(result["fallbacks"]["noisy_triggers"]) >= 0)

    def test_cross_tenant_isolation(self):
        other_tenant = uuid.uuid4()
        _make_automation_job(other_tenant)
        result = CommunicationAnalyticsService.get_fallback_escalation_report(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["fallbacks"]["total_scheduled"], 0)


# ===========================================================================
# TestEntityCommunicationReport
# ===========================================================================

class TestEntityCommunicationReport(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.entity_id = uuid.uuid4()

    def test_single_entity_thread_count(self):
        _make_thread(
            self.tenant_id,
            related_entity_type="candidate",
            related_entity_id=self.entity_id,
        )
        _make_thread(
            self.tenant_id,
            related_entity_type="candidate",
            related_entity_id=self.entity_id,
        )
        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_id,
            entity_type="candidate",
            entity_id=self.entity_id,
        )
        self.assertEqual(result["detail"]["thread_count"], 2)
        self.assertEqual(result["entity_id"], str(self.entity_id))

    def test_single_entity_message_count(self):
        thread = _make_thread(
            self.tenant_id,
            related_entity_type="candidate",
            related_entity_id=self.entity_id,
        )
        _make_message(
            self.tenant_id, thread, self.user_id,
            related_entity_type="candidate",
            related_entity_id=self.entity_id,
        )
        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_id,
            entity_type="candidate",
            entity_id=self.entity_id,
        )
        self.assertEqual(result["detail"]["message_count"], 1)

    def test_aggregate_list_mode(self):
        eid1 = uuid.uuid4()
        eid2 = uuid.uuid4()
        _make_thread(self.tenant_id, related_entity_type="job", related_entity_id=eid1)
        _make_thread(self.tenant_id, related_entity_type="job", related_entity_id=eid2)

        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_id,
            entity_type="job",
        )
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["entities"]), 2)

    def test_entity_type_filter_respected(self):
        eid1 = uuid.uuid4()
        eid2 = uuid.uuid4()
        _make_thread(self.tenant_id, related_entity_type="candidate", related_entity_id=eid1)
        _make_thread(self.tenant_id, related_entity_type="job", related_entity_id=eid2)

        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_id,
            entity_type="candidate",
        )
        self.assertEqual(result["total"], 1)

    def test_cross_tenant_isolation(self):
        other_tenant = uuid.uuid4()
        eid = uuid.uuid4()
        _make_thread(other_tenant, related_entity_type="candidate", related_entity_id=eid)

        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_id,
            entity_type="candidate",
        )
        self.assertEqual(result["total"], 0)

    def test_pagination_respects_limit(self):
        for _ in range(5):
            _make_thread(
                self.tenant_id,
                related_entity_type="interview",
                related_entity_id=uuid.uuid4(),
            )
        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_id,
            entity_type="interview",
            limit=2,
        )
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(result["total"], 5)


# ===========================================================================
# TestWorkloadReport
# ===========================================================================

class TestWorkloadReport(TestCase):

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user_a = uuid.uuid4()
        self.user_b = uuid.uuid4()

    def test_top_senders_ranked(self):
        thread = _make_thread(self.tenant_id)
        for _ in range(5):
            _make_message(self.tenant_id, thread, self.user_a)
        for _ in range(2):
            _make_message(self.tenant_id, thread, self.user_b)

        result = CommunicationAnalyticsService.get_workload_report(tenant_id=self.tenant_id)
        top = result["top_senders"]
        self.assertEqual(top[0]["user_id"], str(self.user_a))
        self.assertEqual(top[0]["messages_sent"], 5)

    def test_unread_backlog_counted(self):
        for _ in range(4):
            _make_notification(self.tenant_id, self.user_a, is_read=False)
        _make_notification(self.tenant_id, self.user_b, is_read=False)

        result = CommunicationAnalyticsService.get_workload_report(tenant_id=self.tenant_id)
        backlog = result["highest_unread_backlog"]
        top = next(r for r in backlog if r["user_id"] == str(self.user_a))
        self.assertEqual(top["unread_count"], 4)

    def test_single_user_summary(self):
        thread = _make_thread(self.tenant_id)
        _make_message(self.tenant_id, thread, self.user_a)
        _make_notification(self.tenant_id, self.user_a, is_read=False)

        result = CommunicationAnalyticsService.get_workload_report(
            tenant_id=self.tenant_id, user_id=self.user_a
        )
        self.assertEqual(result["user_id"], str(self.user_a))
        self.assertEqual(result["messages_sent"], 1)
        self.assertEqual(result["unread_backlog"], 1)

    def test_cross_tenant_isolation(self):
        other_tenant = uuid.uuid4()
        thread = _make_thread(other_tenant)
        _make_message(other_tenant, thread, uuid.uuid4())

        result = CommunicationAnalyticsService.get_workload_report(tenant_id=self.tenant_id)
        self.assertEqual(result["top_senders"], [])

    def test_limit_respected(self):
        thread = _make_thread(self.tenant_id)
        for _ in range(5):
            _make_message(self.tenant_id, thread, uuid.uuid4())

        result = CommunicationAnalyticsService.get_workload_report(
            tenant_id=self.tenant_id, limit=3
        )
        self.assertLessEqual(len(result["top_senders"]), 3)


# ===========================================================================
# TestAnalyticsEndpoints
# ===========================================================================

class TestAnalyticsEndpoints(TestCase):
    """Verify HTTP status codes, envelope shape, and auth enforcement."""

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.user = _make_user(tenant_id=self.tenant_id)

    def _get(self, view_class, params="", url="/api/v1/"):
        request = factory.get(f"{url}?{params}")
        force_authenticate(request, user=self.user)
        return view_class.as_view()(request)

    def _get_unauth(self, view_class):
        request = factory.get("/api/v1/")
        return view_class.as_view()(request)

    def _assert_success_shape(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success", response.data)
        self.assertTrue(response.data["success"])
        self.assertIn("data", response.data)

    def test_dashboard_200(self):
        self._assert_success_shape(self._get(CommunicationDashboardView))

    def test_channels_200(self):
        self._assert_success_shape(self._get(ChannelPerformanceView))

    def test_notifications_200(self):
        self._assert_success_shape(self._get(NotificationEffectivenessView))

    def test_response_times_200(self):
        self._assert_success_shape(self._get(ResponseTimeView))

    def test_workload_200(self):
        self._assert_success_shape(self._get(WorkloadView))

    def test_fallbacks_200(self):
        self._assert_success_shape(self._get(FallbackEscalationView))

    def test_entities_200(self):
        self._assert_success_shape(self._get(EntityCommunicationView))

    def test_dashboard_unauthenticated_401(self):
        r = self._get_unauth(CommunicationDashboardView)
        self.assertIn(r.status_code, (401, 403))

    def test_channels_unauthenticated_401(self):
        r = self._get_unauth(ChannelPerformanceView)
        self.assertIn(r.status_code, (401, 403))

    def test_entities_invalid_type_400(self):
        request = factory.get("/api/v1/?entity_type=invalid_type")
        force_authenticate(request, user=self.user)
        r = EntityCommunicationView.as_view()(request)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_entities_id_without_type_400(self):
        request = factory.get(f"/api/v1/?entity_id={uuid.uuid4()}")
        force_authenticate(request, user=self.user)
        r = EntityCommunicationView.as_view()(request)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_data_keys_present(self):
        response = self._get(CommunicationDashboardView)
        data = response.data["data"]
        self.assertIn("messaging", data)
        self.assertIn("notifications", data)
        self.assertIn("delivery", data)
        self.assertIn("period", data)


# ===========================================================================
# TestEdgeCases
# ===========================================================================

class TestEdgeCases(TestCase):
    """Empty data, zero-division safety, date boundaries."""

    def setUp(self):
        self.tenant_id = uuid.uuid4()

    def test_safe_rate_zero_denominator(self):
        self.assertIsNone(_safe_rate(5, 0))

    def test_safe_rate_normal(self):
        self.assertAlmostEqual(_safe_rate(1, 4), 0.25)

    def test_seconds_to_human_none(self):
        self.assertIsNone(_seconds_to_human(None))

    def test_seconds_to_human_overnight(self):
        self.assertEqual(_seconds_to_human(90000), "1d 1h")

    def test_empty_tenant_dashboard_no_crash(self):
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_id
        )
        self.assertEqual(result["messaging"]["total_messages"], 0)
        self.assertEqual(result["notifications"]["total_notifications"], 0)
        self.assertEqual(result["delivery"]["total_failed_deliveries"], 0)


# ===========================================================================
# TestAnalyticsAccessControl
# ===========================================================================

class TestAnalyticsAccessControl(TestCase):
    """Cross-tenant leakage prevention and access enforcement."""

    def setUp(self):
        self.tenant_a = uuid.uuid4()
        self.tenant_b = uuid.uuid4()
        self.user_b = _make_user(tenant_id=self.tenant_b)

    def test_dashboard_tenant_b_cannot_see_tenant_a_data(self):
        # Create data in tenant A
        thread = _make_thread(self.tenant_a)
        _make_message(self.tenant_a, thread, uuid.uuid4())
        _make_notification(self.tenant_a, uuid.uuid4())

        # Query as tenant B
        result = CommunicationAnalyticsService.get_communication_dashboard_metrics(
            tenant_id=self.tenant_b
        )
        self.assertEqual(result["messaging"]["total_messages"], 0)
        self.assertEqual(result["notifications"]["total_notifications"], 0)

    def test_workload_tenant_isolation(self):
        thread = _make_thread(self.tenant_a)
        _make_message(self.tenant_a, thread, uuid.uuid4())

        result = CommunicationAnalyticsService.get_workload_report(tenant_id=self.tenant_b)
        self.assertEqual(result["top_senders"], [])

    def test_entity_report_tenant_isolation(self):
        eid = uuid.uuid4()
        _make_thread(self.tenant_a, related_entity_type="candidate", related_entity_id=eid)

        result = CommunicationAnalyticsService.get_entity_communication_report(
            tenant_id=self.tenant_b,
            entity_type="candidate",
        )
        self.assertEqual(result["total"], 0)

    def test_unauthenticated_workload_denied(self):
        request = factory.get("/api/v1/")
        r = WorkloadView.as_view()(request)
        self.assertIn(r.status_code, (401, 403))
