"""
Migration: Notification Automation Orchestration
Adds:
  - NotificationAutomationJob — tracks scheduled fallback/escalation/reminder jobs
  - NotificationEscalationLog — immutable record of escalation actions taken
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0005_notification_control_center'),
    ]

    operations = [
        # ── NotificationAutomationJob ────────────────────────────────────────
        migrations.CreateModel(
            name='NotificationAutomationJob',
            fields=[
                ('id',                  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',           models.UUIDField(db_index=True)),
                ('notification',        models.ForeignKey(
                    to='communications.Notification',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='automation_jobs',
                    null=True,
                    blank=True,
                    db_column='notification_id',
                )),
                ('event_key',           models.CharField(max_length=120, blank=True, db_index=True)),
                ('job_type',            models.CharField(
                    max_length=30,
                    choices=[
                        ('fallback_email', 'Fallback Email'),
                        ('escalation',     'Escalation'),
                        ('reminder',       'Reminder'),
                        ('digest',         'Digest'),
                    ],
                    db_index=True,
                )),
                ('scheduled_for',       models.DateTimeField(db_index=True)),
                ('executed_at',         models.DateTimeField(null=True, blank=True)),
                ('status',              models.CharField(
                    max_length=20,
                    default='pending',
                    choices=[
                        ('pending',   'Pending'),
                        ('executed',  'Executed'),
                        ('cancelled', 'Cancelled'),
                        ('failed',    'Failed'),
                        ('skipped',   'Skipped'),
                    ],
                    db_index=True,
                )),
                ('cancel_reason',       models.CharField(max_length=200, blank=True)),
                ('retry_count',         models.PositiveSmallIntegerField(default=0)),
                ('celery_task_id',      models.CharField(max_length=255, blank=True)),
                ('related_entity_type', models.CharField(max_length=80, blank=True)),
                ('related_entity_id',   models.UUIDField(null=True, blank=True)),
                ('metadata',            models.JSONField(default=dict, blank=True)),
                ('created_at',          models.DateTimeField(auto_now_add=True)),
                ('updated_at',          models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'comms_notification_automation_job',
                'ordering': ['-scheduled_for'],
            },
        ),
        migrations.AddIndex(
            model_name='notificationautomationjob',
            index=models.Index(fields=['tenant_id', 'status', 'scheduled_for'],
                               name='comms_naj_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationautomationjob',
            index=models.Index(fields=['notification_id', 'status'],
                               name='comms_naj_notification_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationautomationjob',
            index=models.Index(fields=['tenant_id', 'job_type', 'status'],
                               name='comms_naj_type_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationautomationjob',
            index=models.Index(fields=['related_entity_type', 'related_entity_id', 'status'],
                               name='comms_naj_entity_idx'),
        ),

        # ── NotificationEscalationLog ────────────────────────────────────────
        migrations.CreateModel(
            name='NotificationEscalationLog',
            fields=[
                ('id',                  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',           models.UUIDField(db_index=True)),
                ('notification',        models.ForeignKey(
                    to='communications.Notification',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='escalation_logs',
                    db_column='notification_id',
                )),
                ('escalation_level',    models.PositiveSmallIntegerField(default=1)),
                ('target_user_id',      models.UUIDField(null=True, blank=True, db_index=True)),
                ('target_type',         models.CharField(max_length=40, blank=True)),
                ('triggered_at',        models.DateTimeField(auto_now_add=True)),
                ('channel_used',        models.CharField(max_length=20, default='in_app')),
                ('status',              models.CharField(
                    max_length=20,
                    default='sent',
                    choices=[
                        ('sent',    'Sent'),
                        ('failed',  'Failed'),
                        ('skipped', 'Skipped — target not resolved'),
                    ],
                    db_index=True,
                )),
                ('original_event_key',  models.CharField(max_length=120, blank=True)),
                ('original_user_id',    models.UUIDField(null=True, blank=True)),
                ('metadata',            models.JSONField(default=dict, blank=True)),
            ],
            options={
                'db_table': 'comms_notification_escalation_log',
                'ordering': ['-triggered_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notificationescalationlog',
            index=models.Index(fields=['tenant_id', 'notification_id'],
                               name='comms_nel_notification_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationescalationlog',
            index=models.Index(fields=['tenant_id', 'target_user_id', 'triggered_at'],
                               name='comms_nel_target_idx'),
        ),
    ]
