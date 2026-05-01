import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0006_alter_workflowwaitstate_wait_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowExecutionContext',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('context_key', models.CharField(db_index=True, max_length=128)),
                ('context_value', models.JSONField(blank=True, default=dict)),
                ('source_type', models.CharField(
                    choices=[
                        ('workflow', 'Workflow'),
                        ('event', 'Event'),
                        ('stage', 'Stage'),
                        ('actor', 'Actor'),
                        ('routing', 'Routing'),
                        ('system', 'System'),
                    ],
                    db_index=True,
                    default='workflow',
                    max_length=16,
                )),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='execution_contexts',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={
                'db_table': 'wf_exec_contexts',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowExecutionDecision',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('decision_type', models.CharField(
                    choices=[
                        ('transition_select', 'Transition Select'),
                        ('wait_required', 'Wait Required'),
                        ('resume_allowed', 'Resume Allowed'),
                        ('routing_required', 'Routing Required'),
                        ('retry_required', 'Retry Required'),
                        ('completion_check', 'Completion Check'),
                        ('failure_classification', 'Failure Classification'),
                    ],
                    db_index=True,
                    max_length=32,
                )),
                ('decision_result', models.CharField(max_length=255)),
                ('decision_reason', models.TextField(blank=True)),
                ('stage_execution', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='execution_decisions',
                    to='workflow_execution.workflowstageexecution',
                )),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='execution_decisions',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={
                'db_table': 'wf_exec_decisions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowOrchestratorLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('log_type', models.CharField(
                    choices=[
                        ('start', 'Start'),
                        ('stage_enter', 'Stage Enter'),
                        ('stage_exit', 'Stage Exit'),
                        ('wait', 'Wait'),
                        ('resume', 'Resume'),
                        ('route', 'Route'),
                        ('retry', 'Retry'),
                        ('fail', 'Fail'),
                        ('complete', 'Complete'),
                        ('debug', 'Debug'),
                    ],
                    db_index=True,
                    max_length=16,
                )),
                ('message', models.TextField()),
                ('stage_execution', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='orchestrator_logs',
                    to='workflow_execution.workflowstageexecution',
                )),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='orchestrator_logs',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={
                'db_table': 'wf_exec_orchestrator_logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
