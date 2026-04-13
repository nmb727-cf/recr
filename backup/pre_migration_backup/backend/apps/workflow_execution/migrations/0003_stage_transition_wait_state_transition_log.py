import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0002_add_wait_reason'),
    ]

    operations = [
        # ---------------------------------------------------------------- #
        # WorkflowInstance — add context_data                              #
        # ---------------------------------------------------------------- #
        migrations.AddField(
            model_name='workflowinstance',
            name='context_data',
            field=models.JSONField(blank=True, default=dict),
        ),

        # ---------------------------------------------------------------- #
        # WorkflowExecutionTimeline — add actor field                      #
        # ---------------------------------------------------------------- #
        migrations.AddField(
            model_name='workflowexecutiontimeline',
            name='actor',
            field=models.CharField(default='system', max_length=64),
        ),
        migrations.AlterField(
            model_name='workflowexecutiontimeline',
            name='action',
            field=models.CharField(max_length=255),
        ),

        # ---------------------------------------------------------------- #
        # WorkflowStageTransition                                          #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowStageTransition',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',       models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
                ('created_by',      models.UUIDField(blank=True, null=True)),
                ('is_deleted',      models.BooleanField(db_index=True, default=False)),
                ('deleted_at',      models.DateTimeField(blank=True, null=True)),
                ('metadata',        models.JSONField(blank=True, default=dict)),
                ('workflow_id',     models.UUIDField(db_index=True)),
                ('from_stage_id',   models.UUIDField(db_index=True)),
                ('to_stage_id',     models.UUIDField(db_index=True)),
                ('transition_type', models.CharField(
                    choices=[('auto', 'Auto'), ('decision', 'Decision'), ('approval', 'Approval'),
                             ('event', 'Event'), ('manual', 'Manual'), ('wait', 'Wait')],
                    default='auto', max_length=16,
                )),
                ('condition_config', models.JSONField(blank=True, default=dict)),
                ('priority',         models.IntegerField(default=0)),
                ('label',            models.CharField(blank=True, max_length=128)),
                ('is_active',        models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'wf_exec_stage_transitions',
                'ordering': ['priority', 'created_at'],
            },
        ),

        # ---------------------------------------------------------------- #
        # WorkflowWaitState                                                #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowWaitState',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',       models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
                ('created_by',      models.UUIDField(blank=True, null=True)),
                ('is_deleted',      models.BooleanField(db_index=True, default=False)),
                ('deleted_at',      models.DateTimeField(blank=True, null=True)),
                ('metadata',        models.JSONField(blank=True, default=dict)),
                ('wait_type',       models.CharField(
                    choices=[('approval', 'Approval'), ('recruiter_review', 'Recruiter Review'),
                             ('candidate_response', 'Candidate Response'), ('client_feedback', 'Client Feedback'),
                             ('interview_schedule', 'Interview Schedule'), ('document_signature', 'Document Signature'),
                             ('manual', 'Manual')],
                    default='manual', max_length=32,
                )),
                ('wait_reason',     models.CharField(blank=True, max_length=255)),
                ('resume_event',    models.CharField(blank=True, max_length=128)),
                ('status',          models.CharField(
                    choices=[('waiting', 'Waiting'), ('resumed', 'Resumed'),
                             ('expired', 'Expired'), ('cancelled', 'Cancelled')],
                    db_index=True, default='waiting', max_length=16,
                )),
                ('resumed_at',      models.DateTimeField(blank=True, null=True)),
                ('resumed_by',      models.CharField(blank=True, max_length=64)),
                ('resume_context',  models.JSONField(blank=True, default=dict)),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='wait_states',
                    to='workflow_execution.workflowinstance',
                )),
                ('stage_execution',   models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='wait_states',
                    to='workflow_execution.workflowstageexecution',
                )),
            ],
            options={
                'db_table': 'wf_exec_wait_states',
                'ordering': ['-created_at'],
            },
        ),

        # ---------------------------------------------------------------- #
        # WorkflowTransitionLog                                            #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowTransitionLog',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',       models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
                ('created_by',      models.UUIDField(blank=True, null=True)),
                ('is_deleted',      models.BooleanField(db_index=True, default=False)),
                ('deleted_at',      models.DateTimeField(blank=True, null=True)),
                ('metadata',        models.JSONField(blank=True, default=dict)),
                ('from_stage_id',   models.UUIDField(blank=True, db_index=True, null=True)),
                ('to_stage_id',     models.UUIDField(blank=True, db_index=True, null=True)),
                ('from_stage_name', models.CharField(blank=True, max_length=128)),
                ('to_stage_name',   models.CharField(blank=True, max_length=128)),
                ('transition_type', models.CharField(blank=True, max_length=16)),
                ('label',           models.CharField(blank=True, max_length=128)),
                ('triggered_by',    models.CharField(
                    choices=[('system', 'System'), ('user', 'User'),
                             ('event', 'Event'), ('automation', 'Automation')],
                    default='system', max_length=16,
                )),
                ('actor_id',        models.UUIDField(blank=True, null=True)),
                ('reason',          models.TextField(blank=True)),
                ('condition_result', models.JSONField(blank=True, default=dict)),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transition_logs',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={
                'db_table': 'wf_exec_transition_logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
