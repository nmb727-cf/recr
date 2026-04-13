"""
Migration: Notification Control Center
Adds NotificationRule, NotificationChannelSetting, TenantNotificationPreferenceDefaults
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0004_comms_notification_engine'),
    ]

    operations = [
        # ── NotificationRule ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='NotificationRule',
            fields=[
                ('id',                    models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',             models.UUIDField(null=True, blank=True, db_index=True)),
                ('event_key',             models.CharField(max_length=120, db_index=True)),
                ('business_label',        models.CharField(max_length=200)),
                ('category',              models.CharField(max_length=40, default='system',
                                              choices=[
                                                  ('candidate',   'Candidate'),
                                                  ('application', 'Application'),
                                                  ('interview',   'Interview'),
                                                  ('offer',       'Offer'),
                                                  ('approval',    'Approval'),
                                                  ('agency',      'Agency'),
                                                  ('deadline',    'Deadline / SLA'),
                                                  ('messaging',   'Messaging'),
                                                  ('passport',    'Passport'),
                                                  ('system',      'System'),
                                              ],
                                              db_index=True)),
                ('priority',              models.CharField(max_length=20, default='info',
                                              choices=[
                                                  ('info',     'Info'),
                                                  ('medium',   'Medium'),
                                                  ('high',     'High'),
                                                  ('critical', 'Critical'),
                                              ],
                                              db_index=True)),
                ('is_active',             models.BooleanField(default=True, db_index=True)),
                ('is_system',             models.BooleanField(default=False)),
                ('is_locked',             models.BooleanField(default=False)),
                ('in_app_enabled',        models.BooleanField(default=True)),
                ('email_enabled',         models.BooleanField(default=True)),
                ('whatsapp_enabled',      models.BooleanField(default=False)),
                ('sms_enabled',           models.BooleanField(default=False)),
                ('send_immediately',      models.BooleanField(default=True)),
                ('fallback_enabled',      models.BooleanField(default=False)),
                ('fallback_delay_minutes', models.PositiveIntegerField(default=40)),
                ('escalation_enabled',    models.BooleanField(default=False)),
                ('escalation_delay_minutes', models.PositiveIntegerField(default=60)),
                ('escalation_target_type', models.CharField(max_length=40, default='tenant_admin',
                                               choices=[
                                                   ('assigned_manager', "Assigned User Manager"),
                                                   ('hiring_manager',   'Hiring Manager'),
                                                   ('recruiter_lead',   'Recruiter Lead'),
                                                   ('tenant_admin',     'Tenant Admin'),
                                               ])),
                ('template_id',           models.UUIDField(null=True, blank=True)),
                ('template_name',         models.CharField(max_length=200, blank=True)),
                ('allow_user_override',   models.BooleanField(default=True)),
                ('admin_notes',           models.TextField(blank=True)),
                ('created_at',            models.DateTimeField(auto_now_add=True)),
                ('updated_at',            models.DateTimeField(auto_now=True)),
                ('updated_by',            models.UUIDField(null=True, blank=True)),
                ('is_deleted',            models.BooleanField(default=False, db_index=True)),
                ('deleted_at',            models.DateTimeField(null=True, blank=True)),
                ('metadata',              models.JSONField(default=dict, blank=True)),
            ],
            options={
                'db_table': 'comms_notification_rule',
                'ordering': ['category', 'business_label'],
            },
        ),
        migrations.AddConstraint(
            model_name='NotificationRule',
            constraint=models.UniqueConstraint(
                fields=['tenant_id', 'event_key'],
                name='unique_notification_rule_per_tenant',
            ),
        ),
        migrations.AddIndex(
            model_name='NotificationRule',
            index=models.Index(
                fields=['tenant_id', 'category', 'is_active'],
                name='nc_rule_tenant_cat_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='NotificationRule',
            index=models.Index(
                fields=['tenant_id', 'event_key', 'is_deleted'],
                name='nc_rule_tenant_key_idx',
            ),
        ),

        # ── NotificationChannelSetting ───────────────────────────────────────
        migrations.CreateModel(
            name='NotificationChannelSetting',
            fields=[
                ('id',                  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',           models.UUIDField(db_index=True)),
                ('channel_type',        models.CharField(max_length=20, db_index=True,
                                            choices=[
                                                ('in_app',   'In-App'),
                                                ('email',    'Email'),
                                                ('whatsapp', 'WhatsApp'),
                                                ('sms',      'SMS'),
                                                ('push',     'Push'),
                                            ])),
                ('is_enabled',          models.BooleanField(default=True)),
                ('provider',            models.CharField(max_length=80, blank=True)),
                ('quiet_hours_enabled', models.BooleanField(default=False)),
                ('quiet_hours_start',   models.TimeField(null=True, blank=True)),
                ('quiet_hours_end',     models.TimeField(null=True, blank=True)),
                ('sender_name',         models.CharField(max_length=200, blank=True)),
                ('sender_email',        models.EmailField(blank=True)),
                ('config_json',         models.JSONField(default=dict, blank=True)),
                ('created_at',          models.DateTimeField(auto_now_add=True)),
                ('updated_at',          models.DateTimeField(auto_now=True)),
                ('metadata',            models.JSONField(default=dict, blank=True)),
            ],
            options={
                'db_table': 'comms_notification_channel_setting',
            },
        ),
        migrations.AddConstraint(
            model_name='NotificationChannelSetting',
            constraint=models.UniqueConstraint(
                fields=['tenant_id', 'channel_type'],
                name='unique_channel_setting_per_tenant',
            ),
        ),
        migrations.AddIndex(
            model_name='NotificationChannelSetting',
            index=models.Index(
                fields=['tenant_id', 'channel_type', 'is_enabled'],
                name='nc_channel_tenant_idx',
            ),
        ),

        # ── TenantNotificationPreferenceDefaults ─────────────────────────────
        migrations.CreateModel(
            name='TenantNotificationPreferenceDefaults',
            fields=[
                ('id',                       models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',                models.UUIDField(unique=True, db_index=True)),
                ('default_in_app_enabled',   models.BooleanField(default=True)),
                ('default_email_enabled',    models.BooleanField(default=True)),
                ('default_reminder_enabled', models.BooleanField(default=True)),
                ('allow_user_override',      models.BooleanField(default=True)),
                ('digest_frequency',         models.CharField(max_length=20, default='immediate',
                                                 choices=[
                                                     ('immediate', 'Immediate'),
                                                     ('hourly',    'Hourly digest'),
                                                     ('daily',     'Daily digest'),
                                                 ])),
                ('created_at',               models.DateTimeField(auto_now_add=True)),
                ('updated_at',               models.DateTimeField(auto_now=True)),
                ('metadata',                 models.JSONField(default=dict, blank=True)),
            ],
            options={
                'db_table': 'comms_tenant_notification_prefs',
            },
        ),
    ]
