"""
Migration: Communication + Notification Engine Phase 1
Adds:
  - ThreadType, ChannelType, ParticipantType, NotificationSeverity choices
  - MessageThread.thread_type, is_internal, is_archived, last_message_preview
  - Message.body, channel_type, delivered_at, is_system_generated, is_deleted,
    deleted_at, attachments_json, related_entity_type, related_entity_id,
    thread FK (nullable), body field
  - Notification.type, severity, fallback_email_sent_at, fallback_whatsapp_sent_at,
    escalation_level, updated_at
  - New model: ThreadParticipant
  - New model: NotificationDelivery
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0003_emailmessage_emailattachment_emailsendingaccount_and_more'),
    ]

    operations = [
        # ── MessageThread enhancements ──────────────────────────────────────
        migrations.AddField(
            model_name='messagethread',
            name='thread_type',
            field=models.CharField(
                choices=[
                    ('internal', 'Internal'),
                    ('company_agency', 'Company ↔ Agency'),
                    ('recruiter_candidate', 'Recruiter ↔ Candidate'),
                    ('company_candidate', 'Company ↔ Candidate'),
                    ('agency_candidate', 'Agency ↔ Candidate'),
                    ('interview_coordination', 'Interview Coordination'),
                    ('submission_context', 'Submission / Application Context'),
                    ('general', 'General'),
                ],
                default='general',
                max_length=40,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='messagethread',
            name='is_internal',
            field=models.BooleanField(default=True, db_index=True),
        ),
        migrations.AddField(
            model_name='messagethread',
            name='is_archived',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='messagethread',
            name='last_message_preview',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'thread_type', 'is_deleted'],
                name='comm_thread_tenant_type_del_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'related_entity_type', 'related_entity_id'],
                name='comm_thread_entity_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(
                fields=['tenant_id', 'last_message_at'],
                name='comm_thread_tenant_last_msg_idx',
            ),
        ),

        # ── Message enhancements ────────────────────────────────────────────
        migrations.AddField(
            model_name='message',
            name='body',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='message',
            name='channel_type',
            field=models.CharField(
                choices=[
                    ('in_app', 'In-App'),
                    ('email', 'Email'),
                    ('whatsapp', 'WhatsApp'),
                    ('sms', 'SMS'),
                ],
                default='in_app',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='is_system_generated',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='message',
            name='is_deleted',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='message',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='attachments_json',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='message',
            name='related_entity_type',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='message',
            name='related_entity_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='thread_id_legacy',
            field=models.UUIDField(blank=True, null=True, db_column='thread_id_legacy'),
        ),
        migrations.AddField(
            model_name='message',
            name='thread',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='messages',
                to='communications.messagethread',
                db_column='thread_id_fk',
            ),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'sent_at'],
                name='comm_msg_tenant_sent_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(
                fields=['tenant_id', 'is_system_generated'],
                name='comm_msg_tenant_system_idx',
            ),
        ),

        # ── Notification enhancements ───────────────────────────────────────
        migrations.AddField(
            model_name='notification',
            name='type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='notification',
            name='severity',
            field=models.CharField(
                choices=[
                    ('info', 'Info'),
                    ('medium', 'Medium'),
                    ('high', 'High'),
                    ('critical', 'Critical / SLA'),
                ],
                default='info',
                max_length=20,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='fallback_email_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='fallback_whatsapp_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='escalation_level',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user_id', 'is_read', 'created_at'],
                name='comm_notif_user_unread_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['tenant_id', 'is_read'],
                name='comm_notif_tenant_read_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user_id', 'expires_at'],
                name='comm_notif_user_expiry_idx',
            ),
        ),

        # ── New model: ThreadParticipant ────────────────────────────────────
        migrations.CreateModel(
            name='ThreadParticipant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('thread', models.ForeignKey(
                    db_column='thread_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='participants',
                    to='communications.messagethread',
                )),
                ('user_id', models.UUIDField(db_index=True)),
                ('participant_type', models.CharField(
                    choices=[
                        ('owner', 'Owner'),
                        ('member', 'Member'),
                        ('observer', 'Observer'),
                        ('external', 'External Tenant'),
                    ],
                    default='member',
                    max_length=20,
                )),
                ('external_tenant_id', models.UUIDField(blank=True, null=True)),
                ('last_read_at', models.DateTimeField(blank=True, null=True)),
                ('is_muted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'communications_thread_participant',
            },
        ),
        migrations.AddConstraint(
            model_name='threadparticipant',
            constraint=models.UniqueConstraint(
                fields=['thread', 'user_id'],
                name='unique_thread_user_participant',
            ),
        ),
        migrations.AddIndex(
            model_name='threadparticipant',
            index=models.Index(
                fields=['tenant_id', 'user_id', 'is_active'],
                name='comm_participant_user_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='threadparticipant',
            index=models.Index(
                fields=['thread_id', 'user_id'],
                name='comm_participant_thread_user_idx',
            ),
        ),

        # ── New model: NotificationDelivery ─────────────────────────────────
        migrations.CreateModel(
            name='NotificationDelivery',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('notification', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='deliveries',
                    to='communications.notification',
                )),
                ('channel', models.CharField(
                    choices=[
                        ('in_app', 'In-App'),
                        ('email', 'Email'),
                        ('whatsapp', 'WhatsApp'),
                        ('sms', 'SMS'),
                        ('push', 'Push'),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ('provider', models.CharField(blank=True, max_length=80)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('sent', 'Sent'),
                        ('delivered', 'Delivered'),
                        ('failed', 'Failed'),
                        ('skipped', 'Skipped'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('attempted_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('failed_at', models.DateTimeField(blank=True, null=True)),
                ('external_message_id', models.CharField(blank=True, max_length=255)),
                ('error_message', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'communications_notification_delivery',
            },
        ),
        migrations.AddIndex(
            model_name='notificationdelivery',
            index=models.Index(
                fields=['notification_id', 'channel'],
                name='comm_delivery_notif_channel_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='notificationdelivery',
            index=models.Index(
                fields=['tenant_id', 'status', 'channel'],
                name='comm_delivery_tenant_status_idx',
            ),
        ),
    ]
