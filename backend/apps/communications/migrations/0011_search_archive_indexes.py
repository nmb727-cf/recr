# Generated manually — search & archive performance indexes
# Adds composite indexes to support the search, archive, and history
# query patterns added in COMMS-SEARCH-AND-ARCHIVE-01.

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Performance indexes for Communication Search & Archive module.

    All indexes use tenant_id as the leading column where appropriate
    so the planner can prune partitions and use index-only scans when
    RLS / tenant filters are applied first.

    Tables touched:
        communications_thread       — MessageThread
        communications_message      — Message
        communications_notification — Notification
    """

    dependencies = [
        ('communications', '0010_remove_notificationchannelsetting_unique_channel_setting_per_tenant_and_more'),
    ]

    operations = [

        # ── MessageThread ────────────────────────────────────────────────────

        # Archive management: list archived threads per tenant
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'is_archived', 'is_deleted', 'archived_at'],
                name='comms_thread_archive_idx',
            ),
        ),

        # Retention / compliance: find threads eligible for purge
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'purge_eligible_at', 'is_deleted'],
                name='comms_thread_purge_idx',
            ),
        ),

        # Legal hold list
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'legal_hold', 'is_deleted'],
                name='comms_thread_legal_hold_idx',
            ),
        ),

        # Entity history: threads linked to a specific entity
        # (supplements the existing index on tenant_id, related_entity_type,
        # related_entity_id by adding is_deleted and is_archived for filtering)
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=[
                    'tenant_id',
                    'related_entity_type',
                    'related_entity_id',
                    'is_deleted',
                    'is_archived',
                ],
                name='comms_thread_entity_filter_idx',
            ),
        ),

        # Inbox ordering: active threads most-recently-active-first
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'is_deleted', 'is_archived', 'last_message_at'],
                name='comms_thread_inbox_order_idx',
            ),
        ),

        # ── Message ──────────────────────────────────────────────────────────

        # Thread-message join: list all active messages in a thread (timeline)
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['thread_id', 'is_deleted', 'sent_at'],
                name='comms_msg_thread_timeline_idx',
            ),
        ),

        # Entity history: messages directly linked to an entity
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'related_entity_type', 'related_entity_id', 'is_deleted'],
                name='comms_msg_entity_idx',
            ),
        ),

        # Sender filter (global search / thread search by sender)
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'sender_id', 'is_deleted', 'sent_at'],
                name='comms_msg_sender_idx',
            ),
        ),

        # Channel + message type filter for global search
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'channel_type', 'message_type', 'is_deleted'],
                name='comms_msg_channel_type_idx',
            ),
        ),

        # ── Notification ─────────────────────────────────────────────────────

        # Notification history: per user, ordered by date (most common query)
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user_id', 'is_archived', 'created_at'],
                name='comms_notif_history_idx',
            ),
        ),

        # Unread-only filter (inbox badge count + filtering)
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user_id', 'is_read', 'is_archived', 'created_at'],
                name='comms_notif_unread_idx',
            ),
        ),

        # Expiry management (exclude expired from active view)
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user_id', 'expires_at'],
                name='comms_notif_expiry_idx',
            ),
        ),

        # Entity history: notifications linked to an entity
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'related_entity_type', 'related_entity_id'],
                name='comms_notif_entity_idx',
            ),
        ),

        # Severity filter (escalation / compliance views)
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'severity', 'is_read'],
                name='comms_notif_severity_idx',
            ),
        ),
    ]
