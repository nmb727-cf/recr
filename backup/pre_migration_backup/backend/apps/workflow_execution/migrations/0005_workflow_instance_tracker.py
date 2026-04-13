import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0004_cross_entity_routing'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowinstance',
            name='failed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='workflowinstance',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('running', 'Running'),
                    ('waiting', 'Waiting'),
                    ('paused', 'Paused'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                    ('cancelled', 'Cancelled'),
                ],
                db_index=True,
                default='running',
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='workflowstageexecution',
            name='stage_name',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workflowstageexecution',
            name='failed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workflowstageexecution',
            name='actor_type',
            field=models.CharField(blank=True, default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workflowstageexecution',
            name='actor_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workflowwaitstate',
            name='timeout_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workflowtransitionlog',
            name='from_stage',
            field=models.CharField(blank=True, default='', max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workflowtransitionlog',
            name='to_stage',
            field=models.CharField(blank=True, default='', max_length=128),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='WorkflowFailureLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField()),
                ('error_type', models.CharField(blank=True, max_length=128)),
                ('retry_count', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(
                    choices=[('retrying', 'Retrying'), ('failed', 'Failed'), ('recovered', 'Recovered')],
                    db_index=True,
                    default='failed',
                    max_length=16,
                )),
                ('stage_execution', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='failure_logs',
                    to='workflow_execution.workflowstageexecution',
                )),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='failure_logs',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={
                'db_table': 'wf_exec_failure_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowTimeline',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('event_type', models.CharField(
                    choices=[
                        ('stage_started', 'Stage Started'),
                        ('stage_completed', 'Stage Completed'),
                        ('stage_failed', 'Stage Failed'),
                        ('transition', 'Transition'),
                        ('waiting', 'Waiting'),
                        ('resumed', 'Resumed'),
                        ('routing', 'Routing'),
                        ('actor_changed', 'Actor Changed'),
                        ('failure', 'Failure'),
                        ('retry', 'Retry'),
                    ],
                    db_index=True,
                    max_length=32,
                )),
                ('event_label', models.CharField(max_length=255)),
                ('actor_type', models.CharField(blank=True, max_length=64)),
                ('actor_id', models.UUIDField(blank=True, null=True)),
                ('occurred_at', models.DateTimeField(db_index=True)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('failure_log', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timeline_events',
                    to='workflow_execution.workflowfailurelog',
                )),
                ('stage_execution', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timeline_events',
                    to='workflow_execution.workflowstageexecution',
                )),
                ('transition_log', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timeline_events',
                    to='workflow_execution.workflowtransitionlog',
                )),
                ('wait_state', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timeline_events',
                    to='workflow_execution.workflowwaitstate',
                )),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='unified_timeline',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={
                'db_table': 'wf_exec_unified_timeline',
                'ordering': ['occurred_at', 'created_at'],
            },
        ),
    ]
