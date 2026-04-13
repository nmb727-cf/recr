"""
Migration 0008: Multi-Channel Config and Delivery Tracking
-----------------------------------------------------------
Adds:
  comms_tenant_channel_config   — per-tenant WA/SMS/Push provider credentials
  comms_communication_delivery  — unified delivery tracking for WA/SMS/Push
"""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0007_email_delivery_config'),
    ]

    operations = [

        # ── TenantChannelConfig ──────────────────────────────────────────────
        migrations.CreateModel(
            name='TenantChannelConfig',
            fields=[
                ('id',           models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',    models.UUIDField(db_index=True)),
                ('channel_type', models.CharField(max_length=20, db_index=True)),
                ('provider',     models.CharField(max_length=40, blank=True)),

                ('sender_name',        models.CharField(max_length=200, blank=True)),
                ('sender_identifier',  models.CharField(max_length=200, blank=True)),

                ('api_token_encrypted',       models.TextField(blank=True)),
                ('api_key_id',                models.CharField(max_length=255, blank=True)),
                ('webhook_secret_encrypted',  models.TextField(blank=True)),

                ('whatsapp_phone_number_id',      models.CharField(max_length=64, blank=True)),
                ('whatsapp_business_account_id',  models.CharField(max_length=64, blank=True)),
                ('whatsapp_api_version',          models.CharField(max_length=20, default='v19.0', blank=True)),

                ('sms_http_endpoint', models.CharField(max_length=500, blank=True)),
                ('sms_http_method',   models.CharField(max_length=10, default='POST', blank=True)),

                ('push_vapid_public_key',          models.TextField(blank=True)),
                ('push_vapid_private_key_encrypted', models.TextField(blank=True)),
                ('push_fcm_project_id',            models.CharField(max_length=255, blank=True)),

                ('is_active',   models.BooleanField(default=True, db_index=True)),
                ('is_default',  models.BooleanField(default=True)),
                ('config_json', models.JSONField(default=dict, blank=True)),
                ('metadata',    models.JSONField(default=dict, blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('created_by',  models.UUIDField(null=True, blank=True)),
                ('is_deleted',  models.BooleanField(default=False, db_index=True)),
                ('deleted_at',  models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'comms_tenant_channel_config',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='TenantChannelConfig',
            index=models.Index(
                fields=['tenant_id', 'channel_type', 'is_active'],
                name='comms_chcfg_tid_ch_active',
            ),
        ),
        migrations.AddIndex(
            model_name='TenantChannelConfig',
            index=models.Index(
                fields=['tenant_id', 'channel_type', 'is_deleted'],
                name='comms_chcfg_tid_ch_del',
            ),
        ),

        # ── CommunicationDelivery ────────────────────────────────────────────
        migrations.CreateModel(
            name='CommunicationDelivery',
            fields=[
                ('id',              models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',       models.UUIDField(db_index=True)),
                ('notification_id', models.UUIDField(null=True, blank=True, db_index=True)),
                ('automation_job_id', models.UUIDField(null=True, blank=True, db_index=True)),
                ('channel_type',    models.CharField(max_length=20, db_index=True)),
                ('provider',        models.CharField(max_length=80, blank=True)),
                ('recipient_identifier', models.CharField(max_length=255, blank=True)),
                ('recipient_user_id',    models.UUIDField(null=True, blank=True, db_index=True)),
                ('template_used',        models.CharField(max_length=255, blank=True)),
                ('rendered_body',        models.TextField(blank=True)),
                ('rendered_subject',     models.CharField(max_length=500, blank=True)),
                ('status',    models.CharField(max_length=20, default='pending', db_index=True)),
                ('priority',  models.CharField(max_length=20, default='medium', db_index=True)),
                ('scheduled_for',  models.DateTimeField(null=True, blank=True, db_index=True)),
                ('attempted_at',   models.DateTimeField(null=True, blank=True)),
                ('delivered_at',   models.DateTimeField(null=True, blank=True)),
                ('read_at',        models.DateTimeField(null=True, blank=True)),
                ('failed_at',      models.DateTimeField(null=True, blank=True)),
                ('attempt_number', models.PositiveSmallIntegerField(default=1)),
                ('max_attempts',   models.PositiveSmallIntegerField(default=3)),
                ('next_retry_at',  models.DateTimeField(null=True, blank=True)),
                ('external_message_id',     models.CharField(max_length=255, blank=True)),
                ('external_status_payload', models.JSONField(default=dict, blank=True)),
                ('error_message',   models.TextField(blank=True)),
                ('skip_reason',     models.CharField(max_length=200, blank=True)),
                ('metadata',    models.JSONField(default=dict, blank=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'comms_communication_delivery',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='CommunicationDelivery',
            index=models.Index(
                fields=['tenant_id', 'channel_type', 'status'],
                name='comms_delivery_tid_ch_stat',
            ),
        ),
        migrations.AddIndex(
            model_name='CommunicationDelivery',
            index=models.Index(
                fields=['tenant_id', 'created_at'],
                name='comms_delivery_tid_created',
            ),
        ),
        migrations.AddIndex(
            model_name='CommunicationDelivery',
            index=models.Index(
                fields=['notification_id', 'channel_type'],
                name='comms_delivery_notif_ch',
            ),
        ),
        migrations.AddIndex(
            model_name='CommunicationDelivery',
            index=models.Index(
                fields=['tenant_id', 'recipient_user_id', 'channel_type'],
                name='comms_delivery_tid_user_ch',
            ),
        ),
        migrations.AddIndex(
            model_name='CommunicationDelivery',
            index=models.Index(
                fields=['automation_job_id'],
                name='comms_delivery_job_id',
            ),
        ),
    ]
