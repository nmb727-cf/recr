import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0003_stage_transition_wait_state_transition_log'),
    ]

    operations = [
        # ---------------------------------------------------------------- #
        # WorkflowEntityRoute                                              #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowEntityRoute',
            fields=[
                ('id',               models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',        models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
                ('created_by',       models.UUIDField(blank=True, null=True)),
                ('is_deleted',       models.BooleanField(db_index=True, default=False)),
                ('deleted_at',       models.DateTimeField(blank=True, null=True)),
                ('metadata',         models.JSONField(blank=True, default=dict)),
                ('from_entity_type', models.CharField(
                    choices=[('company', 'Company'), ('agency', 'Agency'), ('candidate', 'Candidate'),
                             ('recruiter', 'Recruiter'), ('hiring_manager', 'Hiring Manager'), ('hr', 'HR'),
                             ('interviewer', 'Interviewer'), ('panel', 'Interview Panel'),
                             ('onboarding', 'Onboarding'), ('hrms', 'HRMS')],
                    max_length=32,
                )),
                ('from_entity_id',   models.UUIDField(blank=True, null=True)),
                ('to_entity_type',   models.CharField(
                    choices=[('company', 'Company'), ('agency', 'Agency'), ('candidate', 'Candidate'),
                             ('recruiter', 'Recruiter'), ('hiring_manager', 'Hiring Manager'), ('hr', 'HR'),
                             ('interviewer', 'Interviewer'), ('panel', 'Interview Panel'),
                             ('onboarding', 'Onboarding'), ('hrms', 'HRMS')],
                    max_length=32,
                )),
                ('to_entity_id',     models.UUIDField(blank=True, null=True)),
                ('route_type',       models.CharField(
                    choices=[('ownership_transfer', 'Ownership Transfer'), ('action_handoff', 'Action Handoff'),
                             ('approval_handoff', 'Approval Handoff'), ('scheduling_handoff', 'Scheduling Handoff'),
                             ('communication_handoff', 'Communication Handoff'),
                             ('onboarding_handoff', 'Onboarding Handoff'),
                             ('workflow_continuation', 'Workflow Continuation')],
                    default='workflow_continuation', max_length=32,
                )),
                ('route_reason',     models.TextField(blank=True)),
                ('status',           models.CharField(
                    choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed'),
                             ('failed', 'Failed'), ('cancelled', 'Cancelled')],
                    db_index=True, default='pending', max_length=16,
                )),
                ('stage_id',         models.UUIDField(blank=True, db_index=True, null=True)),
                ('completed_at',     models.DateTimeField(blank=True, null=True)),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='entity_routes',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={'db_table': 'wf_exec_entity_routes', 'ordering': ['-created_at']},
        ),

        # ---------------------------------------------------------------- #
        # WorkflowActorAssignment                                          #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowActorAssignment',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',       models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
                ('created_by',      models.UUIDField(blank=True, null=True)),
                ('is_deleted',      models.BooleanField(db_index=True, default=False)),
                ('deleted_at',      models.DateTimeField(blank=True, null=True)),
                ('metadata',        models.JSONField(blank=True, default=dict)),
                ('stage_id',        models.UUIDField(db_index=True)),
                ('actor_type',      models.CharField(
                    choices=[('recruiter', 'Recruiter'), ('hiring_manager', 'Hiring Manager'), ('hr', 'HR'),
                             ('agency_manager', 'Agency Manager'), ('agency_recruiter', 'Agency Recruiter'),
                             ('interviewer', 'Interviewer'), ('candidate', 'Candidate'), ('system', 'System')],
                    db_index=True, max_length=32,
                )),
                ('actor_id',        models.UUIDField(blank=True, db_index=True, null=True)),
                ('assignment_type', models.CharField(
                    choices=[('responsible', 'Responsible'), ('reviewer', 'Reviewer'), ('approver', 'Approver'),
                             ('scheduler', 'Scheduler'), ('coordinator', 'Coordinator'), ('observer', 'Observer')],
                    default='responsible', max_length=16,
                )),
                ('assigned_at',     models.DateTimeField(auto_now_add=True)),
                ('status',          models.CharField(
                    choices=[('active', 'Active'), ('completed', 'Completed'),
                             ('revoked', 'Revoked'), ('expired', 'Expired')],
                    db_index=True, default='active', max_length=16,
                )),
                ('notes',           models.TextField(blank=True)),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='actor_assignments',
                    to='workflow_execution.workflowinstance',
                )),
            ],
            options={'db_table': 'wf_exec_actor_assignments', 'ordering': ['-assigned_at']},
        ),

        # ---------------------------------------------------------------- #
        # WorkflowHandoffCheckpoint                                        #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowHandoffCheckpoint',
            fields=[
                ('id',                      models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',               models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',              models.DateTimeField(auto_now_add=True)),
                ('updated_at',              models.DateTimeField(auto_now=True)),
                ('created_by',              models.UUIDField(blank=True, null=True)),
                ('is_deleted',              models.BooleanField(db_index=True, default=False)),
                ('deleted_at',              models.DateTimeField(blank=True, null=True)),
                ('metadata',                models.JSONField(blank=True, default=dict)),
                ('handoff_from',            models.CharField(max_length=64)),
                ('handoff_to',              models.CharField(max_length=64)),
                ('handoff_type',            models.CharField(
                    choices=[('agency_to_company', 'Agency → Company'), ('company_to_agency', 'Company → Agency'),
                             ('company_to_candidate', 'Company → Candidate'), ('candidate_to_company', 'Candidate → Company'),
                             ('company_to_hr', 'Company → HR'), ('workflow_to_hrms', 'Workflow → HRMS'),
                             ('recruiter_to_manager', 'Recruiter → Hiring Manager'), ('manager_to_hr', 'Manager → HR')],
                    max_length=32,
                )),
                ('payload',                 models.JSONField(blank=True, default=dict)),
                ('expected_response_event', models.CharField(blank=True, max_length=128)),
                ('status',                  models.CharField(
                    choices=[('pending', 'Pending'), ('delivered', 'Delivered'), ('acknowledged', 'Acknowledged'),
                             ('completed', 'Completed'), ('failed', 'Failed'), ('expired', 'Expired')],
                    db_index=True, default='pending', max_length=16,
                )),
                ('responded_at',    models.DateTimeField(blank=True, null=True)),
                ('response_payload', models.JSONField(blank=True, default=dict)),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='handoff_checkpoints',
                    to='workflow_execution.workflowinstance',
                )),
                ('stage_execution',   models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='handoff_checkpoints',
                    to='workflow_execution.workflowstageexecution',
                )),
            ],
            options={'db_table': 'wf_exec_handoff_checkpoints', 'ordering': ['-created_at']},
        ),

        # ---------------------------------------------------------------- #
        # WorkflowRoutingRule                                              #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowRoutingRule',
            fields=[
                ('id',                   models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',            models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',           models.DateTimeField(auto_now_add=True)),
                ('updated_at',           models.DateTimeField(auto_now=True)),
                ('created_by',           models.UUIDField(blank=True, null=True)),
                ('is_deleted',           models.BooleanField(db_index=True, default=False)),
                ('deleted_at',           models.DateTimeField(blank=True, null=True)),
                ('metadata',             models.JSONField(blank=True, default=dict)),
                ('workflow_id',          models.UUIDField(db_index=True)),
                ('stage_id',             models.UUIDField(blank=True, db_index=True, null=True)),
                ('condition_config',     models.JSONField(blank=True, default=dict)),
                ('route_to_entity_type', models.CharField(
                    choices=[('company', 'Company'), ('agency', 'Agency'), ('candidate', 'Candidate'),
                             ('recruiter', 'Recruiter'), ('hiring_manager', 'Hiring Manager'), ('hr', 'HR'),
                             ('interviewer', 'Interviewer'), ('panel', 'Interview Panel'),
                             ('onboarding', 'Onboarding'), ('hrms', 'HRMS')],
                    max_length=32,
                )),
                ('route_to_actor_type',  models.CharField(blank=True, max_length=32)),
                ('route_config',         models.JSONField(blank=True, default=dict)),
                ('priority',             models.IntegerField(default=0)),
                ('label',                models.CharField(blank=True, max_length=128)),
                ('is_active',            models.BooleanField(default=True)),
            ],
            options={'db_table': 'wf_exec_routing_rules', 'ordering': ['priority', 'created_at']},
        ),

        # ---------------------------------------------------------------- #
        # WorkflowRouteTimelineLog                                         #
        # ---------------------------------------------------------------- #
        migrations.CreateModel(
            name='WorkflowRouteTimelineLog',
            fields=[
                ('id',              models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id',       models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
                ('created_by',      models.UUIDField(blank=True, null=True)),
                ('is_deleted',      models.BooleanField(db_index=True, default=False)),
                ('deleted_at',      models.DateTimeField(blank=True, null=True)),
                ('metadata',        models.JSONField(blank=True, default=dict)),
                ('action',          models.CharField(max_length=255)),
                ('from_actor',      models.CharField(blank=True, max_length=128)),
                ('to_actor',        models.CharField(blank=True, max_length=128)),
                ('reason',          models.TextField(blank=True)),
                ('workflow_instance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='route_timeline',
                    to='workflow_execution.workflowinstance',
                )),
                ('route',           models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timeline_logs',
                    to='workflow_execution.workflowentityroute',
                )),
            ],
            options={'db_table': 'wf_exec_route_timeline', 'ordering': ['-created_at']},
        ),
    ]
