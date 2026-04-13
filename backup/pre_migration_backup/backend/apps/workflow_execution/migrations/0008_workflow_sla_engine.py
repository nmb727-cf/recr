import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0007_workflow_execution_orchestrator_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowStageSLA',
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
                ('stage_id', models.UUIDField(db_index=True)),
                ('sla_duration', models.DurationField()),
                ('warning_duration', models.DurationField()),
                ('escalation_duration', models.DurationField()),
                ('escalation_role', models.CharField(blank=True, choices=[('hiring_manager', 'Hiring Manager'), ('hr', 'HR'), ('admin', 'Admin'), ('workflow_owner', 'Workflow Owner')], max_length=32)),
                ('escalation_user', models.UUIDField(blank=True, db_index=True, null=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={
                'db_table': 'wf_exec_stage_sla',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['workflow_id', 'stage_id', 'is_active'], name='wf_exec_sta_workflo_6a3147_idx')],
            },
        ),
        migrations.CreateModel(
            name='WorkflowSLAEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('event_type', models.CharField(choices=[('warning', 'Warning'), ('breach', 'Breach'), ('escalation', 'Escalation'), ('resolved', 'Resolved')], db_index=True, max_length=16)),
                ('stage_execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sla_events', to='workflow_execution.workflowstageexecution')),
                ('workflow_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sla_events', to='workflow_execution.workflowinstance')),
            ],
            options={
                'db_table': 'wf_exec_sla_events',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowSLATracker',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('sla_start', models.DateTimeField(db_index=True)),
                ('warning_at', models.DateTimeField(db_index=True)),
                ('breach_at', models.DateTimeField(db_index=True)),
                ('escalated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('warning', 'Warning'), ('breached', 'Breached'), ('escalated', 'Escalated'), ('resolved', 'Resolved')], db_index=True, default='active', max_length=16)),
                ('stage_execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sla_trackers', to='workflow_execution.workflowstageexecution')),
                ('stage_sla', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sla_trackers', to='workflow_execution.workflowstagesla')),
                ('workflow_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sla_trackers', to='workflow_execution.workflowinstance')),
            ],
            options={
                'db_table': 'wf_exec_sla_trackers',
                'ordering': ['-sla_start'],
                'indexes': [models.Index(fields=['workflow_instance', 'status'], name='wf_exec_sla_workflo_5f0cf7_idx'), models.Index(fields=['stage_execution', 'status'], name='wf_exec_sla_stage_e_4f808d_idx')],
            },
        ),
    ]
