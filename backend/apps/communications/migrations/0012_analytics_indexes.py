# Generated manually — analytics performance indexes
# Adds composite indexes to support the analytics query patterns introduced
# in COMMS-ANALYTICS-AND-REPORTING-01.
#
# All indexes are tenant_id-leading (where applicable) so the PostgreSQL
# planner can apply tenant isolation before scanning.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0011_search_archive_indexes'),
    ]

    operations = [

        # ── Message analytics indexes ─────────────────────────────────────
        # messages_by_type with date range
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'message_type', 'sent_at'],
                name='comms_msg_type_sent_idx',
            ),
        ),
        # entity communication report
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'related_entity_type', 'related_entity_id', 'sent_at'],
                name='comms_msg_entity_sent_idx',
            ),
        ),
        # workload: sender activity
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'sender_id', 'is_deleted', 'sent_at'],
                name='comms_msg_sender_workload_idx',
            ),
        ),

        # ── MessageThread analytics indexes ───────────────────────────────
        # thread counts over time
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'is_deleted', 'is_archived', 'created_at'],
                name='comms_thread_analytics_idx',
            ),
        ),
        # thread type breakdown with date range
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'thread_type', 'is_deleted', 'created_at'],
                name='comms_thread_type_analytics_idx',
            ),
        ),

        # ── Notification analytics indexes ────────────────────────────────
        # category (type) breakdown over time
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'type', 'created_at'],
                name='comms_notif_type_analytics_idx',
            ),
        ),
        # effectiveness: severity × read × date
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'severity', 'is_read', 'created_at'],
                name='comms_notif_severity_read_idx',
            ),
        ),
        # fallback email tracking
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'fallback_email_sent_at'],
                name='comms_notif_fallback_email_idx',
            ),
        ),
        # escalation level tracking
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'escalation_level', 'created_at'],
                name='comms_notif_escalation_idx',
            ),
        ),
        # read latency: filter read notifications with read_at populated
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'is_read', 'created_at', 'read_at'],
                name='comms_notif_read_latency_idx',
            ),
        ),

        # ── NotificationDelivery analytics indexes ────────────────────────
        # channel performance: channel × status × attempted_at
        migrations.AddIndex(
            model_name='notificationdelivery',
            index=models.Index(
                fields=['tenant_id', 'channel', 'status', 'attempted_at'],
                name='comms_nd_channel_analytics_idx',
            ),
        ),

        # ── NotificationEscalationLog analytics indexes ───────────────────
        # escalation counts over time
        migrations.AddIndex(
            model_name='notificationescalationlog',
            index=models.Index(
                fields=['tenant_id', 'status', 'triggered_at'],
                name='comms_esclog_analytics_idx',
            ),
        ),
    ]
