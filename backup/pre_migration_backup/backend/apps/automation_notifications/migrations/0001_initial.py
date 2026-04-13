import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ── WorkflowNotificationRule ─────────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowNotificationRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('workflow_id', models.UUIDField(db_index=True)),
                ('action_node_id', models.CharField(blank=True, max_length=100)),
                ('notification_event', models.CharField(max_length=150)),
                ('recipient_type', models.CharField(
                    choices=[
                        ('candidate', 'Candidate'), ('assigned_recruiter', 'Assigned Recruiter'),
                        ('hiring_manager', 'Hiring Manager'), ('recruiter_manager', 'Recruiter Manager'),
                        ('agency_contact', 'Agency Contact'), ('custom_user', 'Custom User'),
                        ('workflow_owner', 'Workflow Owner'),
                    ],
                    max_length=50,
                )),
                ('channel', models.CharField(
                    choices=[
                        ('email', 'Email'), ('whatsapp', 'WhatsApp'), ('in_app', 'In-App'),
                        ('sms', 'SMS'), ('push', 'Push'),
                    ],
                    default='in_app', max_length=20,
                )),
                ('template_id', models.UUIDField(blank=True, null=True)),
                ('fallback_channels', models.JSONField(blank=True, default=list)),
                ('send_delay_minutes', models.PositiveIntegerField(default=0)),
                ('throttle_window_minutes', models.PositiveIntegerField(default=0)),
                ('dedupe_key_template', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={'verbose_name': 'Workflow Notification Rule', 'ordering': ['-created_at']},
        ),
        # ── WorkflowNotificationDelivery ─────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowNotificationDelivery',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('execution_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('workflow_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('notification_rule', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='deliveries',
                    to='automation_notifications.workflownotificationrule',
                )),
                ('recipient_user_id', models.UUIDField(blank=True, null=True)),
                ('recipient_email', models.EmailField(blank=True)),
                ('recipient_phone', models.CharField(blank=True, max_length=30)),
                ('channel', models.CharField(
                    choices=[
                        ('email', 'Email'), ('whatsapp', 'WhatsApp'), ('in_app', 'In-App'),
                        ('sms', 'SMS'), ('push', 'Push'),
                    ],
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('queued', 'Queued'), ('sent', 'Sent'), ('delivered', 'Delivered'),
                        ('failed', 'Failed'), ('skipped', 'Skipped'),
                        ('throttled', 'Throttled'), ('deduplicated', 'Deduplicated'),
                    ],
                    db_index=True, default='queued', max_length=20,
                )),
                ('provider_message_id', models.CharField(blank=True, max_length=255)),
                ('subject', models.CharField(blank=True, max_length=500)),
                ('rendered_message', models.TextField(blank=True)),
                ('dedupe_key', models.CharField(blank=True, db_index=True, max_length=500)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('failed_at', models.DateTimeField(blank=True, null=True)),
                ('retry_count', models.PositiveSmallIntegerField(default=0)),
                ('failure_reason', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={'verbose_name': 'Workflow Notification Delivery', 'ordering': ['-created_at']},
        ),
        # ── WorkflowNotificationPreference ───────────────────────────────────
        migrations.CreateModel(
            name='WorkflowNotificationPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user_id', models.UUIDField(db_index=True)),
                ('notification_type', models.CharField(max_length=150)),
                ('preferred_channels', models.JSONField(default=list)),
                ('quiet_hours_start', models.TimeField(blank=True, null=True)),
                ('quiet_hours_end', models.TimeField(blank=True, null=True)),
                ('allow_escalation_override', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'Workflow Notification Preference', 'ordering': ['user_id']},
        ),
        # ── WorkflowEscalationNotification ────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowEscalationNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('workflow_id', models.UUIDField(db_index=True)),
                ('execution_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('escalation_level', models.PositiveSmallIntegerField(default=1)),
                ('trigger_reason', models.CharField(max_length=255)),
                ('target_recipient_type', models.CharField(
                    choices=[
                        ('candidate', 'Candidate'), ('assigned_recruiter', 'Assigned Recruiter'),
                        ('hiring_manager', 'Hiring Manager'), ('recruiter_manager', 'Recruiter Manager'),
                        ('agency_contact', 'Agency Contact'), ('custom_user', 'Custom User'),
                        ('workflow_owner', 'Workflow Owner'),
                    ],
                    max_length=50,
                )),
                ('channel', models.CharField(
                    choices=[
                        ('email', 'Email'), ('whatsapp', 'WhatsApp'), ('in_app', 'In-App'),
                        ('sms', 'SMS'), ('push', 'Push'),
                    ],
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'), ('sent', 'Sent'),
                        ('resolved', 'Resolved'), ('cancelled', 'Cancelled'),
                    ],
                    default='pending', max_length=20,
                )),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={'verbose_name': 'Workflow Escalation Notification', 'ordering': ['-created_at']},
        ),
        # ── WorkflowNotificationInsight ───────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowNotificationInsight',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('workflow_id', models.UUIDField(blank=True, null=True, db_index=True)),
                ('insight_type', models.CharField(
                    choices=[
                        ('high_failure_rate', 'High Failure Rate'),
                        ('duplicate_risk', 'Duplicate Risk'),
                        ('channel_underperforming', 'Channel Underperforming'),
                        ('escalation_spike', 'Escalation Spike'),
                        ('candidate_non_response_pattern', 'Candidate Non-Response Pattern'),
                    ],
                    max_length=60,
                )),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('metric_value', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={'verbose_name': 'Workflow Notification Insight', 'ordering': ['-created_at']},
        ),
        # ── Indexes ───────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='workflownotificationrule',
            index=models.Index(fields=['tenant_id', 'workflow_id'], name='wf_notif_rule_tenant_wf_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationrule',
            index=models.Index(fields=['tenant_id', 'notification_event', 'is_active'], name='wf_notif_rule_event_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationdelivery',
            index=models.Index(fields=['tenant_id', 'status'], name='wf_notif_del_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationdelivery',
            index=models.Index(fields=['tenant_id', 'channel', 'status'], name='wf_notif_del_ch_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationdelivery',
            index=models.Index(fields=['tenant_id', 'dedupe_key'], name='wf_notif_del_dedupe_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationdelivery',
            index=models.Index(fields=['execution_id', 'status'], name='wf_notif_del_exec_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationpreference',
            index=models.Index(fields=['tenant_id', 'user_id'], name='wf_notif_pref_tenant_user_idx'),
        ),
        migrations.AddConstraint(
            model_name='workflownotificationpreference',
            constraint=models.UniqueConstraint(
                fields=['tenant_id', 'user_id', 'notification_type'],
                name='unique_user_notif_pref',
            ),
        ),
        migrations.AddIndex(
            model_name='workflowescalationnotification',
            index=models.Index(fields=['tenant_id', 'status'], name='wf_escal_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowescalationnotification',
            index=models.Index(fields=['tenant_id', 'workflow_id'], name='wf_escal_tenant_wf_idx'),
        ),
        migrations.AddIndex(
            model_name='workflownotificationinsight',
            index=models.Index(fields=['tenant_id', 'insight_type'], name='wf_notif_insight_type_idx'),
        ),
    ]
