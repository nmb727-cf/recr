"""
Migration 0007: Email Delivery Models
=======================================
Creates:
  comms_tenant_email_config  — per-tenant automation email provider config
  comms_email_delivery       — per-message tracking for automation emails
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0006_notification_automation_jobs'),
    ]

    operations = [

        # ------------------------------------------------------------------
        # TenantEmailConfig
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='TenantEmailConfig',
            fields=[
                ('id',           models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',    models.UUIDField(db_index=True)),
                ('provider',     models.CharField(
                    choices=[
                        ('smtp',     'SMTP'),
                        ('sendgrid', 'SendGrid'),
                        ('ses',      'Amazon SES'),
                        ('system',   'System Default'),
                    ],
                    default='system',
                    max_length=20,
                )),
                ('from_email',     models.EmailField(blank=True)),
                ('from_name',      models.CharField(blank=True, max_length=255)),
                ('reply_to_email', models.EmailField(blank=True)),

                # SMTP
                ('smtp_host',               models.CharField(blank=True, max_length=255)),
                ('smtp_port',               models.IntegerField(default=587)),
                ('smtp_username',           models.CharField(blank=True, max_length=255)),
                ('smtp_password_encrypted', models.TextField(blank=True)),
                ('smtp_use_tls',            models.BooleanField(default=True)),
                ('smtp_use_ssl',            models.BooleanField(default=False)),

                # SendGrid
                ('sendgrid_api_key_encrypted', models.TextField(blank=True)),

                # SES
                ('ses_region',                      models.CharField(blank=True, max_length=30)),
                ('ses_access_key_id',               models.CharField(blank=True, max_length=128)),
                ('ses_secret_access_key_encrypted', models.TextField(blank=True)),

                # Status
                ('is_active',  models.BooleanField(db_index=True, default=True)),
                ('metadata',   models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'comms_tenant_email_config',
                'ordering': ['-created_at'],
                'app_label': 'communications',
            },
        ),

        # ------------------------------------------------------------------
        # EmailDelivery
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='EmailDelivery',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',       models.UUIDField(db_index=True)),
                ('notification_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('recipient_email', models.EmailField()),
                ('subject',         models.CharField(max_length=500)),
                ('template_used',   models.CharField(blank=True, max_length=255)),
                ('provider',        models.CharField(blank=True, max_length=20)),
                ('status', models.CharField(
                    choices=[
                        ('pending',   'Pending'),
                        ('sending',   'Sending'),
                        ('sent',      'Sent'),
                        ('delivered', 'Delivered'),
                        ('failed',    'Failed'),
                        ('bounced',   'Bounced'),
                        ('deferred',  'Deferred'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('priority', models.CharField(
                    choices=[
                        ('low',    'Low'),
                        ('normal', 'Normal'),
                        ('high',   'High'),
                        ('urgent', 'Urgent'),
                    ],
                    db_index=True,
                    default='normal',
                    max_length=10,
                )),
                ('error_message',       models.TextField(blank=True)),
                ('retry_count',         models.IntegerField(default=0)),
                ('max_retries',         models.IntegerField(default=4)),
                ('sent_at',             models.DateTimeField(blank=True, null=True)),
                ('delivered_at',        models.DateTimeField(blank=True, null=True)),
                ('next_retry_at',       models.DateTimeField(blank=True, null=True)),
                ('provider_message_id', models.CharField(blank=True, max_length=255)),
                ('metadata',            models.JSONField(blank=True, default=dict)),
                ('created_at',          models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at',          models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'comms_email_delivery',
                'ordering': ['-created_at'],
                'app_label': 'communications',
            },
        ),

        # Composite indexes
        migrations.AddIndex(
            model_name='emaildelivery',
            index=models.Index(fields=['tenant_id', 'status'], name='comms_edel_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='emaildelivery',
            index=models.Index(fields=['tenant_id', 'created_at'], name='comms_edel_tenant_created_idx'),
        ),
    ]
