"""
Communication Analytics Service
================================
Central service for all communication analytics and reporting queries.

All methods are @staticmethod. They return plain dicts shaped for
dashboard/reporting use. No model instances or querysets are returned.

Metric definitions (authoritative):
  first_response_time
      Seconds between the first message in a thread and the first
      reply from a DIFFERENT participant.

  notification_read_rate
      read_count / total_created  (within the queried window).

  fallback_cancel_rate
      Fallback automation jobs cancelled (because the notification was
      read before the job fired) / fallback jobs scheduled.
      High cancel_rate = fallback was not needed → healthy signal.

  escalation_resolution_rate
      Escalation log entries where the original notification was later
      read / total escalation log entries.

  unread_backlog
      Active, unread, non-expired notification count per user.

Performance notes:
  • Every query applies tenant_id as the first filter.
  • Date-range arguments bound all heavy aggregation queries.
  • Raw SQL is used only for PERCENTILE_CONT (PostgreSQL-only window fn).
  • Heavy listing endpoints are paginated.
"""
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.db import connection
from django.db.models import (
    Avg,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Q,
    Sum,
    DurationField,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

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
from apps.communications.email_delivery_models import EmailDelivery

logger = logging.getLogger(__name__)

# Max seconds for a valid first-response-time (7 days).  Outliers above
# this are excluded from averages to prevent skew.
_RESPONSE_TIME_CAP_SECONDS = 7 * 24 * 3600

FALLBACK_JOB_TYPES = (
    NotificationAutomationJobType.FALLBACK_EMAIL,
    NotificationAutomationJobType.WHATSAPP_FALLBACK,
    NotificationAutomationJobType.SMS_ESCALATION,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_rate(numerator: int, denominator: int) -> Optional[float]:
    """Return numerator/denominator rounded to 4dp, or None when denom = 0."""
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _seconds_to_human(seconds) -> Optional[str]:
    """Convert a float second count to a human-readable string like '1h 23m'."""
    if seconds is None:
        return None
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m}m"
    d = s // 86400
    h = (s % 86400) // 3600
    return f"{d}d {h}h"


def _apply_date_filter(qs, field: str, date_from, date_to):
    if date_from:
        qs = qs.filter(**{f"{field}__gte": date_from})
    if date_to:
        qs = qs.filter(**{f"{field}__lte": date_to})
    return qs


def _period_label(date_from, date_to) -> Dict[str, Any]:
    return {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }


# ---------------------------------------------------------------------------
# Analytics Service
# ---------------------------------------------------------------------------

class CommunicationAnalyticsService:

    # ------------------------------------------------------------------ #
    # 1. Dashboard Metrics                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_communication_dashboard_metrics(
        *,
        tenant_id,
        date_from=None,
        date_to=None,
    ) -> Dict[str, Any]:
        """
        Return a unified dashboard KPI dict covering messaging, notifications,
        and delivery health for a tenant within the given date window.
        """
        # ── Messages ────────────────────────────────────────────────────
        msg_qs = Message.objects.filter(tenant_id=tenant_id, is_deleted=False)
        msg_qs = _apply_date_filter(msg_qs, "sent_at", date_from, date_to)

        total_messages = msg_qs.count()

        messages_by_type = list(
            msg_qs
            .values("message_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        messages_by_entity = list(
            msg_qs
            .exclude(related_entity_type="")
            .values("related_entity_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # ── Threads ─────────────────────────────────────────────────────
        thread_qs = MessageThread.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        )
        thread_qs = _apply_date_filter(thread_qs, "created_at", date_from, date_to)

        thread_agg = thread_qs.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_archived=False)),
            archived=Count("id", filter=Q(is_archived=True)),
            internal=Count("id", filter=Q(is_internal=True)),
            external=Count("id", filter=Q(is_internal=False)),
        )

        threads_by_type = list(
            thread_qs
            .values("thread_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # ── Notifications ────────────────────────────────────────────────
        notif_qs = Notification.objects.filter(tenant_id=tenant_id)
        notif_qs = _apply_date_filter(notif_qs, "created_at", date_from, date_to)

        now = timezone.now()
        notif_agg = notif_qs.aggregate(
            total=Count("id"),
            read=Count("id", filter=Q(is_read=True)),
            unread_active=Count(
                "id",
                filter=Q(is_read=False, is_archived=False)
                & (Q(expires_at__isnull=True) | Q(expires_at__gt=now)),
            ),
            fallback_email=Count(
                "id", filter=Q(fallback_email_sent_at__isnull=False)
            ),
            fallback_whatsapp=Count(
                "id", filter=Q(fallback_whatsapp_sent_at__isnull=False)
            ),
            escalated=Count("id", filter=Q(escalation_level__gt=0)),
        )

        notifications_by_category = list(
            notif_qs
            .exclude(type="")
            .values("type")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        notifications_by_severity = list(
            notif_qs
            .values("severity")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # ── Delivery health ──────────────────────────────────────────────
        # NotificationDelivery (in-app + email channel)
        nd_qs = NotificationDelivery.objects.filter(tenant_id=tenant_id)
        nd_qs = _apply_date_filter(nd_qs, "attempted_at", date_from, date_to)
        nd_failed = nd_qs.filter(status="failed").count()

        # CommunicationDelivery (whatsapp, sms, push)
        cd_qs = CommunicationDelivery.objects.filter(tenant_id=tenant_id)
        cd_qs = _apply_date_filter(cd_qs, "created_at", date_from, date_to)
        cd_failed = cd_qs.filter(status="failed").count()

        # Quick channel summary (sent counts)
        nd_channel_summary = list(
            nd_qs
            .values("channel")
            .annotate(
                sent=Count("id"),
                delivered=Count("id", filter=Q(status="delivered")),
                failed=Count("id", filter=Q(status="failed")),
            )
            .order_by("channel")
        )

        cd_channel_summary = list(
            cd_qs
            .values("channel_type")
            .annotate(
                sent=Count("id"),
                delivered=Count("id", filter=Q(status="delivered")),
                failed=Count("id", filter=Q(status="failed")),
            )
            .order_by("channel_type")
        )

        # Escalation log count
        esc_qs = NotificationEscalationLog.objects.filter(tenant_id=tenant_id)
        esc_qs = _apply_date_filter(esc_qs, "triggered_at", date_from, date_to)
        escalations_triggered = esc_qs.count()

        return {
            "period": _period_label(date_from, date_to),
            "messaging": {
                "total_messages": total_messages,
                "total_threads": thread_agg["total"],
                "active_threads": thread_agg["active"],
                "archived_threads": thread_agg["archived"],
                "internal_threads": thread_agg["internal"],
                "external_threads": thread_agg["external"],
                "messages_by_type": messages_by_type,
                "messages_by_entity": messages_by_entity,
                "threads_by_type": threads_by_type,
            },
            "notifications": {
                "total_notifications": notif_agg["total"],
                "read_notifications": notif_agg["read"],
                "unread_active": notif_agg["unread_active"],
                "fallback_emails_sent": notif_agg["fallback_email"],
                "fallback_whatsapp_sent": notif_agg["fallback_whatsapp"],
                "escalations_triggered": escalations_triggered,
                "notifications_escalated": notif_agg["escalated"],
                "by_category": notifications_by_category,
                "by_severity": notifications_by_severity,
            },
            "delivery": {
                "total_failed_deliveries": nd_failed + cd_failed,
                "notification_delivery_failed": nd_failed,
                "channel_delivery_failed": cd_failed,
                "notification_channel_summary": nd_channel_summary,
                "multi_channel_summary": cd_channel_summary,
            },
        }

    # ------------------------------------------------------------------ #
    # 2. Channel Performance                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_channel_performance_report(
        *,
        tenant_id,
        date_from=None,
        date_to=None,
        channel_type: str = "",
    ) -> Dict[str, Any]:
        """
        Return per-channel delivery statistics merged from NotificationDelivery
        (in_app, email) and CommunicationDelivery (whatsapp, sms, push).

        Each channel entry includes: sent, delivered, failed, pending,
        skipped, success_rate, failure_rate.
        """
        # NotificationDelivery aggregation
        nd_qs = NotificationDelivery.objects.filter(tenant_id=tenant_id)
        nd_qs = _apply_date_filter(nd_qs, "attempted_at", date_from, date_to)
        if channel_type:
            nd_qs = nd_qs.filter(channel=channel_type)

        nd_by_channel = {
            row["channel"]: row
            for row in nd_qs.values("channel").annotate(
                total=Count("id"),
                delivered=Count("id", filter=Q(status="delivered")),
                sent=Count("id", filter=Q(status="sent")),
                failed=Count("id", filter=Q(status="failed")),
                pending=Count("id", filter=Q(status="pending")),
                skipped=Count("id", filter=Q(status="skipped")),
            )
        }

        # CommunicationDelivery aggregation
        cd_qs = CommunicationDelivery.objects.filter(tenant_id=tenant_id)
        cd_qs = _apply_date_filter(cd_qs, "created_at", date_from, date_to)
        if channel_type:
            cd_qs = cd_qs.filter(channel_type=channel_type)

        cd_by_channel = {
            row["channel_type"]: row
            for row in cd_qs.values("channel_type").annotate(
                total=Count("id"),
                delivered=Count("id", filter=Q(status="delivered")),
                sent=Count("id", filter=Q(status="sent")),
                failed=Count("id", filter=Q(status="failed")),
                pending=Count("id", filter=Q(status="pending")),
                skipped=Count("id", filter=Q(status="skipped")),
            )
        }

        # Merge into unified channel map
        all_channels: Dict[str, Dict[str, int]] = {}

        def _merge(ch: str, row: dict, key: str = "channel"):
            entry = all_channels.setdefault(
                ch,
                {"total": 0, "delivered": 0, "sent": 0,
                 "failed": 0, "pending": 0, "skipped": 0},
            )
            for k in ("total", "delivered", "sent", "failed", "pending", "skipped"):
                entry[k] += row.get(k, 0)

        for ch, row in nd_by_channel.items():
            _merge(ch, row)
        for ch, row in cd_by_channel.items():
            _merge(ch, row)

        channels = []
        best_channel = None
        best_rate = -1.0
        worst_channel = None
        worst_rate = 2.0

        for ch, entry in sorted(all_channels.items()):
            # success_rate = (delivered + sent) / total attempts
            success_count = entry["delivered"] + entry["sent"]
            rate = _safe_rate(success_count, entry["total"])
            fail_rate = _safe_rate(entry["failed"], entry["total"])

            if rate is not None:
                if rate > best_rate:
                    best_rate, best_channel = rate, ch
                if rate < worst_rate:
                    worst_rate, worst_channel = rate, ch

            channels.append({
                "channel": ch,
                "total_attempts": entry["total"],
                "delivered": entry["delivered"],
                "sent": entry["sent"],
                "failed": entry["failed"],
                "pending": entry["pending"],
                "skipped": entry["skipped"],
                "success_rate": rate,
                "failure_rate": fail_rate,
            })

        # Notification category × channel breakdown (top 10 categories)
        nd_cat = list(
            nd_qs
            .values("channel")
            .annotate(
                by_type=Count("id"),
            )
            .order_by("-by_type")[:10]
        )

        return {
            "period": _period_label(date_from, date_to),
            "channels": channels,
            "best_channel": best_channel,
            "worst_channel": worst_channel if worst_channel != best_channel else None,
            "total_attempts": sum(c["total_attempts"] for c in channels),
            "total_failed": sum(c["failed"] for c in channels),
        }

    # ------------------------------------------------------------------ #
    # 3. Notification Effectiveness                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_notification_effectiveness_report(
        *,
        tenant_id,
        date_from=None,
        date_to=None,
        category: str = "",
        priority: str = "",
    ) -> Dict[str, Any]:
        """
        Return notification read/action/expiry rates, broken down by
        severity and category.

        Metrics:
          read_rate                = read / total
          expired_unread_rate      = expired_unread / total
          fallback_trigger_rate    = notifications with fallback fired / total
        """
        now = timezone.now()

        qs = Notification.objects.filter(tenant_id=tenant_id)
        qs = _apply_date_filter(qs, "created_at", date_from, date_to)
        if category:
            qs = qs.filter(type=category)
        if priority:
            qs = qs.filter(severity=priority)

        totals = qs.aggregate(
            total=Count("id"),
            read_count=Count("id", filter=Q(is_read=True)),
            archived_count=Count("id", filter=Q(is_archived=True)),
            expired_count=Count(
                "id", filter=Q(expires_at__isnull=False, expires_at__lte=now)
            ),
            expired_unread_count=Count(
                "id",
                filter=Q(is_read=False, expires_at__isnull=False, expires_at__lte=now),
            ),
            fallback_email_count=Count(
                "id", filter=Q(fallback_email_sent_at__isnull=False)
            ),
            fallback_whatsapp_count=Count(
                "id", filter=Q(fallback_whatsapp_sent_at__isnull=False)
            ),
            escalated_count=Count("id", filter=Q(escalation_level__gt=0)),
        )

        total = totals["total"]
        fallback_triggered = totals["fallback_email_count"] + totals["fallback_whatsapp_count"]

        # By severity
        by_severity = []
        for row in (
            qs
            .values("severity")
            .annotate(
                count=Count("id"),
                read_count=Count("id", filter=Q(is_read=True)),
                fallback_count=Count(
                    "id",
                    filter=Q(fallback_email_sent_at__isnull=False)
                    | Q(fallback_whatsapp_sent_at__isnull=False),
                ),
            )
            .order_by("-count")
        ):
            by_severity.append({
                "severity": row["severity"],
                "count": row["count"],
                "read_count": row["read_count"],
                "read_rate": _safe_rate(row["read_count"], row["count"]),
                "fallback_count": row["fallback_count"],
            })

        # By category (type field)
        by_category = []
        for row in (
            qs
            .exclude(type="")
            .values("type")
            .annotate(
                count=Count("id"),
                read_count=Count("id", filter=Q(is_read=True)),
                fallback_count=Count(
                    "id",
                    filter=Q(fallback_email_sent_at__isnull=False)
                    | Q(fallback_whatsapp_sent_at__isnull=False),
                ),
            )
            .order_by("-count")[:15]
        ):
            by_category.append({
                "category": row["type"],
                "count": row["count"],
                "read_count": row["read_count"],
                "read_rate": _safe_rate(row["read_count"], row["count"]),
                "fallback_count": row["fallback_count"],
            })

        return {
            "period": _period_label(date_from, date_to),
            "totals": {
                "created": total,
                "read": totals["read_count"],
                "read_rate": _safe_rate(totals["read_count"], total),
                "archived": totals["archived_count"],
                "expired": totals["expired_count"],
                "expired_unread": totals["expired_unread_count"],
                "expired_unread_rate": _safe_rate(totals["expired_unread_count"], total),
                "fallback_triggered": fallback_triggered,
                "fallback_trigger_rate": _safe_rate(fallback_triggered, total),
                "fallback_email": totals["fallback_email_count"],
                "fallback_whatsapp": totals["fallback_whatsapp_count"],
                "escalated": totals["escalated_count"],
                "escalation_rate": _safe_rate(totals["escalated_count"], total),
            },
            "by_severity": by_severity,
            "by_category": by_category,
        }

    # ------------------------------------------------------------------ #
    # 4. Response Time                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_response_time_report(
        *,
        tenant_id,
        date_from=None,
        date_to=None,
        thread_type: str = "",
        user_id=None,
    ) -> Dict[str, Any]:
        """
        Return first-response-time statistics and notification read-latency.

        first_response_time: seconds between the first message in a thread
        and the first reply from a DIFFERENT participant.  Computed via
        PostgreSQL CTE using PERCENTILE_CONT.

        notification_read_latency: average seconds between notification
        created_at and read_at, broken down by severity.
        """
        # ── Message response times (raw SQL for percentile support) ──────
        response_stats = CommunicationAnalyticsService._get_first_response_stats(
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to,
            thread_type=thread_type,
            user_id=user_id,
        )

        # ── Notification read latency (ORM) ──────────────────────────────
        notif_qs = Notification.objects.filter(
            tenant_id=tenant_id,
            is_read=True,
            read_at__isnull=False,
        )
        notif_qs = _apply_date_filter(notif_qs, "created_at", date_from, date_to)

        read_latency_agg = notif_qs.aggregate(
            avg_latency=Avg(
                ExpressionWrapper(
                    F("read_at") - F("created_at"),
                    output_field=DurationField(),
                )
            )
        )

        avg_lat = read_latency_agg["avg_latency"]
        avg_lat_seconds = avg_lat.total_seconds() if avg_lat else None

        # Read latency by severity
        read_latency_by_severity = []
        for row in (
            notif_qs
            .values("severity")
            .annotate(
                count=Count("id"),
                avg_latency=Avg(
                    ExpressionWrapper(
                        F("read_at") - F("created_at"),
                        output_field=DurationField(),
                    )
                ),
            )
            .order_by("severity")
        ):
            lat = row["avg_latency"]
            lat_s = lat.total_seconds() if lat else None
            read_latency_by_severity.append({
                "severity": row["severity"],
                "count": row["count"],
                "avg_read_latency_seconds": round(lat_s, 2) if lat_s else None,
                "avg_read_latency_human": _seconds_to_human(lat_s),
            })

        # ── Threads breakdown by response coverage ────────────────────────
        thread_qs = MessageThread.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        )
        thread_qs = _apply_date_filter(thread_qs, "created_at", date_from, date_to)
        if thread_type:
            thread_qs = thread_qs.filter(thread_type=thread_type)

        total_threads = thread_qs.count()

        return {
            "period": _period_label(date_from, date_to),
            "messaging_response_times": {
                "total_threads_in_period": total_threads,
                **response_stats,
                "avg_first_response_human": _seconds_to_human(
                    response_stats.get("avg_first_response_seconds")
                ),
                "p50_first_response_human": _seconds_to_human(
                    response_stats.get("p50_first_response_seconds")
                ),
                "p90_first_response_human": _seconds_to_human(
                    response_stats.get("p90_first_response_seconds")
                ),
            },
            "notification_read_latency": {
                "avg_read_latency_seconds": round(avg_lat_seconds, 2) if avg_lat_seconds else None,
                "avg_read_latency_human": _seconds_to_human(avg_lat_seconds),
                "by_severity": read_latency_by_severity,
            },
        }

    @staticmethod
    def _get_first_response_stats(
        *,
        tenant_id,
        date_from,
        date_to,
        thread_type: str,
        user_id,
    ) -> Dict[str, Any]:
        """
        PostgreSQL CTE that computes first-response-time percentiles.

        Excludes response times > 7 days (likely stale / re-opened threads).
        Returns avg, p50, p90 in seconds.
        """
        params: List[Any] = [str(tenant_id)]

        date_clauses: List[str] = []
        if date_from:
            date_clauses.append("AND m.sent_at >= %s")
            params.append(date_from)
        if date_to:
            date_clauses.append("AND m.sent_at <= %s")
            params.append(date_to)

        thread_type_clause = ""
        if thread_type:
            thread_type_clause = "AND t.thread_type = %s"
            params.append(thread_type)

        sender_clause = ""
        if user_id:
            sender_clause = "AND fm.original_sender = %s"
            params.append(str(user_id))

        date_filter = " ".join(date_clauses)

        sql = f"""
            WITH first_messages AS (
                SELECT DISTINCT ON (m.thread_id)
                    m.thread_id,
                    m.sender_id AS original_sender,
                    m.sent_at   AS first_sent_at
                FROM communications_message m
                JOIN communications_thread t ON t.id = m.thread_id
                WHERE m.tenant_id = %s
                  AND m.is_deleted = FALSE
                  AND t.is_deleted = FALSE
                  {date_filter}
                  {thread_type_clause}
                ORDER BY m.thread_id, m.sent_at
            ),
            first_replies AS (
                SELECT DISTINCT ON (m.thread_id)
                    m.thread_id,
                    m.sent_at AS reply_sent_at
                FROM communications_message m
                JOIN first_messages fm ON m.thread_id = fm.thread_id
                WHERE m.sender_id != fm.original_sender
                  AND m.is_deleted = FALSE
                  AND m.sent_at > fm.first_sent_at
                  {sender_clause}
                ORDER BY m.thread_id, m.sent_at
            ),
            deltas AS (
                SELECT
                    EXTRACT(EPOCH FROM (fr.reply_sent_at - fm.first_sent_at)) AS seconds
                FROM first_replies fr
                JOIN first_messages fm ON fr.thread_id = fm.thread_id
                WHERE EXTRACT(EPOCH FROM (fr.reply_sent_at - fm.first_sent_at))
                      BETWEEN 0 AND {_RESPONSE_TIME_CAP_SECONDS}
            )
            SELECT
                COUNT(*)                                                     AS threads_with_response,
                ROUND(AVG(seconds)::numeric, 2)                              AS avg_seconds,
                ROUND(
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY seconds)::numeric, 2
                )                                                            AS p50_seconds,
                ROUND(
                    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY seconds)::numeric, 2
                )                                                            AS p90_seconds
            FROM deltas
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
        except Exception as exc:
            logger.warning("first_response_time query failed: %s", exc)
            return {
                "threads_with_response": 0,
                "avg_first_response_seconds": None,
                "p50_first_response_seconds": None,
                "p90_first_response_seconds": None,
            }

        if not row or row[0] == 0:
            return {
                "threads_with_response": 0,
                "avg_first_response_seconds": None,
                "p50_first_response_seconds": None,
                "p90_first_response_seconds": None,
            }

        return {
            "threads_with_response": int(row[0]),
            "avg_first_response_seconds": float(row[1]) if row[1] is not None else None,
            "p50_first_response_seconds": float(row[2]) if row[2] is not None else None,
            "p90_first_response_seconds": float(row[3]) if row[3] is not None else None,
        }

    # ------------------------------------------------------------------ #
    # 5. Fallback & Escalation                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_fallback_escalation_report(
        *,
        tenant_id,
        date_from=None,
        date_to=None,
    ) -> Dict[str, Any]:
        """
        Return fallback automation job and escalation log analytics.

        fallback_cancel_rate: high value = fallback rarely needed (good).
        noisy_triggers: event_keys with the most fallback executions —
            candidates for rule tuning.
        """
        # ── Automation jobs ───────────────────────────────────────────────
        job_qs = NotificationAutomationJob.objects.filter(
            tenant_id=tenant_id,
            job_type__in=FALLBACK_JOB_TYPES,
        )
        job_qs = _apply_date_filter(job_qs, "created_at", date_from, date_to)

        job_agg = job_qs.aggregate(
            total_scheduled=Count("id"),
            executed=Count(
                "id", filter=Q(status=NotificationAutomationJobStatus.EXECUTED)
            ),
            cancelled=Count(
                "id", filter=Q(status=NotificationAutomationJobStatus.CANCELLED)
            ),
            failed=Count(
                "id", filter=Q(status=NotificationAutomationJobStatus.FAILED)
            ),
            skipped=Count(
                "id", filter=Q(status=NotificationAutomationJobStatus.SKIPPED)
            ),
            pending=Count(
                "id", filter=Q(status=NotificationAutomationJobStatus.PENDING)
            ),
        )

        by_job_type = list(
            job_qs
            .values("job_type")
            .annotate(
                count=Count("id"),
                executed=Count(
                    "id", filter=Q(status=NotificationAutomationJobStatus.EXECUTED)
                ),
                cancelled=Count(
                    "id", filter=Q(status=NotificationAutomationJobStatus.CANCELLED)
                ),
                failed=Count(
                    "id", filter=Q(status=NotificationAutomationJobStatus.FAILED)
                ),
            )
            .order_by("-count")
        )

        # Noisy triggers: event_keys with most executions
        noisy_triggers = list(
            job_qs
            .filter(status=NotificationAutomationJobStatus.EXECUTED)
            .exclude(event_key="")
            .values("event_key")
            .annotate(
                fallback_count=Count("id"),
                cancelled_count=Count(
                    "id", filter=Q(status=NotificationAutomationJobStatus.CANCELLED)
                ),
            )
            .order_by("-fallback_count")[:10]
        )

        scheduled = job_agg["total_scheduled"] or 0
        executed = job_agg["executed"] or 0
        cancelled = job_agg["cancelled"] or 0

        # ── Escalation logs ───────────────────────────────────────────────
        esc_qs = NotificationEscalationLog.objects.filter(tenant_id=tenant_id)
        esc_qs = _apply_date_filter(esc_qs, "triggered_at", date_from, date_to)

        esc_agg = esc_qs.aggregate(
            total=Count("id"),
            sent=Count("id", filter=Q(status=NotificationEscalationLogStatus.SENT)),
            failed=Count("id", filter=Q(status=NotificationEscalationLogStatus.FAILED)),
            skipped=Count("id", filter=Q(status=NotificationEscalationLogStatus.SKIPPED)),
        )

        by_escalation_level = list(
            esc_qs
            .values("escalation_level")
            .annotate(
                count=Count("id"),
                sent=Count("id", filter=Q(status=NotificationEscalationLogStatus.SENT)),
            )
            .order_by("escalation_level")
        )

        # Resolution rate: escalation → original notification was later read
        escalated_notif_ids = list(
            esc_qs.values_list("notification_id", flat=True).distinct()
        )
        resolved_count = 0
        if escalated_notif_ids:
            resolved_count = Notification.objects.filter(
                id__in=escalated_notif_ids,
                is_read=True,
            ).count()

        return {
            "period": _period_label(date_from, date_to),
            "fallbacks": {
                "total_scheduled": scheduled,
                "executed": executed,
                "cancelled": cancelled,
                "failed": job_agg["failed"],
                "skipped": job_agg["skipped"],
                "pending": job_agg["pending"],
                "cancel_rate": _safe_rate(cancelled, scheduled),
                "execution_rate": _safe_rate(executed, scheduled),
                "failure_rate": _safe_rate(job_agg["failed"], scheduled),
                "by_job_type": by_job_type,
                "noisy_triggers": noisy_triggers,
            },
            "escalations": {
                "total_triggered": esc_agg["total"],
                "sent": esc_agg["sent"],
                "failed": esc_agg["failed"],
                "skipped": esc_agg["skipped"],
                "send_rate": _safe_rate(esc_agg["sent"], esc_agg["total"]),
                "resolution_rate": _safe_rate(resolved_count, esc_agg["total"]),
                "by_level": by_escalation_level,
            },
        }

    # ------------------------------------------------------------------ #
    # 6. Entity Communication Report                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_entity_communication_report(
        *,
        tenant_id,
        entity_type: str = "",
        entity_id=None,
        date_from=None,
        date_to=None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Return communication activity rolled up by (entity_type, entity_id).

        If entity_id is provided, return a single-entity detailed breakdown.
        Otherwise, return the top `limit` entities sorted by total activity.
        """
        limit = min(int(limit), 100)

        if entity_id:
            # ── Single entity detail ─────────────────────────────────────
            thread_qs = MessageThread.objects.filter(
                tenant_id=tenant_id,
                is_deleted=False,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
            )
            thread_qs = _apply_date_filter(thread_qs, "created_at", date_from, date_to)
            thread_agg = thread_qs.aggregate(
                thread_count=Count("id"),
                active=Count("id", filter=Q(is_archived=False)),
                archived=Count("id", filter=Q(is_archived=True)),
            )

            msg_qs = Message.objects.filter(
                tenant_id=tenant_id,
                is_deleted=False,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
            )
            msg_qs = _apply_date_filter(msg_qs, "sent_at", date_from, date_to)
            msg_agg = msg_qs.aggregate(
                message_count=Count("id"),
                by_type=Count("message_type"),
            )

            msg_by_type = list(
                msg_qs.values("message_type").annotate(count=Count("id")).order_by("-count")
            )

            notif_qs = Notification.objects.filter(
                tenant_id=tenant_id,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
            )
            notif_qs = _apply_date_filter(notif_qs, "created_at", date_from, date_to)
            notif_agg = notif_qs.aggregate(
                notification_count=Count("id"),
                read=Count("id", filter=Q(is_read=True)),
            )

            threads_by_type = list(
                thread_qs
                .values("thread_type")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

            return {
                "period": _period_label(date_from, date_to),
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "detail": {
                    "thread_count": thread_agg["thread_count"],
                    "active_threads": thread_agg["active"],
                    "archived_threads": thread_agg["archived"],
                    "message_count": msg_agg["message_count"],
                    "notification_count": notif_agg["notification_count"],
                    "notification_read_count": notif_agg["read"],
                    "threads_by_type": threads_by_type,
                    "messages_by_type": msg_by_type,
                },
            }

        # ── Aggregate across all entities of given type ──────────────────
        # Use MessageThread as the primary driver for entity aggregation.
        thread_qs = MessageThread.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        )
        thread_qs = _apply_date_filter(thread_qs, "created_at", date_from, date_to)

        if entity_type:
            thread_qs = thread_qs.filter(related_entity_type=entity_type)
        else:
            thread_qs = thread_qs.exclude(related_entity_type="")

        # Group by (entity_type, entity_id)
        entity_threads = list(
            thread_qs
            .exclude(related_entity_id__isnull=True)
            .values("related_entity_type", "related_entity_id")
            .annotate(thread_count=Count("id"))
            .order_by("-thread_count")
        )

        total = len(entity_threads)
        page = entity_threads[offset: offset + limit]

        # Enrich with message + notification counts for paged entities
        entity_ids = [
            r["related_entity_id"] for r in page if r["related_entity_id"]
        ]
        et_filter = entity_type or None

        msg_counts: Dict[str, int] = {}
        notif_counts: Dict[str, int] = {}

        if entity_ids:
            et_q = Q(related_entity_id__in=entity_ids)
            if et_filter:
                et_q &= Q(related_entity_type=et_filter)

            for row in (
                Message.objects
                .filter(Q(tenant_id=tenant_id) & et_q & Q(is_deleted=False))
                .values("related_entity_id")
                .annotate(count=Count("id"))
            ):
                msg_counts[str(row["related_entity_id"])] = row["count"]

            for row in (
                Notification.objects
                .filter(Q(tenant_id=tenant_id) & et_q)
                .values("related_entity_id")
                .annotate(count=Count("id"))
            ):
                notif_counts[str(row["related_entity_id"])] = row["count"]

        entities = []
        for row in page:
            eid = str(row["related_entity_id"])
            entities.append({
                "entity_type": row["related_entity_type"],
                "entity_id": eid,
                "thread_count": row["thread_count"],
                "message_count": msg_counts.get(eid, 0),
                "notification_count": notif_counts.get(eid, 0),
            })

        return {
            "period": _period_label(date_from, date_to),
            "entity_type": entity_type or "all",
            "entity_id": None,
            "entities": entities,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # ------------------------------------------------------------------ #
    # 7. Workload Report                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_workload_report(
        *,
        tenant_id,
        date_from=None,
        date_to=None,
        user_id=None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Return per-user communication workload: messages sent, thread
        participation, unread notification backlog.

        Content is never exposed — only user_ids and counts.

        If user_id is provided, return that user's personal workload summary.
        Otherwise, return ranked lists of top senders / highest backlogs.
        """
        limit = min(int(limit), 50)
        now = timezone.now()

        # ── Messages sent per user ────────────────────────────────────────
        msg_qs = Message.objects.filter(tenant_id=tenant_id, is_deleted=False)
        msg_qs = _apply_date_filter(msg_qs, "sent_at", date_from, date_to)
        if user_id:
            msg_qs = msg_qs.filter(sender_id=user_id)

        top_senders = list(
            msg_qs
            .values("sender_id")
            .annotate(messages_sent=Count("id"))
            .order_by("-messages_sent")[offset: offset + limit]
        )

        # ── Unread backlog per user ───────────────────────────────────────
        backlog_qs = Notification.objects.filter(
            tenant_id=tenant_id,
            is_read=False,
            is_archived=False,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        if user_id:
            backlog_qs = backlog_qs.filter(user_id=user_id)

        unread_backlog = list(
            backlog_qs
            .values("user_id")
            .annotate(unread_count=Count("id"))
            .order_by("-unread_count")[offset: offset + limit]
        )

        # ── Thread participation per user ─────────────────────────────────
        part_qs = ThreadParticipant.objects.filter(
            tenant_id=tenant_id,
            is_active=True,
            thread__is_deleted=False,
            thread__is_archived=False,
        )
        if date_from or date_to:
            part_qs = part_qs.filter(
                thread__in=_apply_date_filter(
                    MessageThread.objects.filter(tenant_id=tenant_id, is_deleted=False),
                    "created_at",
                    date_from,
                    date_to,
                )
            )
        if user_id:
            part_qs = part_qs.filter(user_id=user_id)

        thread_participation = list(
            part_qs
            .values("user_id")
            .annotate(thread_count=Count("thread_id", distinct=True))
            .order_by("-thread_count")[offset: offset + limit]
        )

        # ── Distinct active users in period ───────────────────────────────
        active_users = (
            msg_qs.values("sender_id").distinct().count()
        )

        if user_id:
            # Single-user summary
            sent = top_senders[0]["messages_sent"] if top_senders else 0
            backlog = unread_backlog[0]["unread_count"] if unread_backlog else 0
            threads = thread_participation[0]["thread_count"] if thread_participation else 0

            # internal vs external mix
            internal_sent = msg_qs.filter(
                sender_id=user_id,
                thread__is_internal=True,
            ).count()
            external_sent = msg_qs.filter(
                sender_id=user_id,
                thread__is_internal=False,
            ).count()

            return {
                "period": _period_label(date_from, date_to),
                "user_id": str(user_id),
                "messages_sent": sent,
                "threads_participated": threads,
                "unread_backlog": backlog,
                "internal_messages_sent": internal_sent,
                "external_messages_sent": external_sent,
            }

        return {
            "period": _period_label(date_from, date_to),
            "active_users_in_period": active_users,
            "top_senders": [
                {"user_id": str(r["sender_id"]), "messages_sent": r["messages_sent"]}
                for r in top_senders
            ],
            "highest_unread_backlog": [
                {"user_id": str(r["user_id"]), "unread_count": r["unread_count"]}
                for r in unread_backlog
            ],
            "highest_thread_participation": [
                {"user_id": str(r["user_id"]), "thread_count": r["thread_count"]}
                for r in thread_participation
            ],
            "limit": limit,
            "offset": offset,
        }
