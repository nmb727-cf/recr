import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ── WorkflowTaskRule ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowTaskRule',
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
                ('node_id', models.CharField(blank=True, max_length=100)),
                ('task_title_template', models.CharField(max_length=500)),
                ('task_description_template', models.TextField(blank=True)),
                ('assignee_type', models.CharField(
                    choices=[
                        ('assigned_recruiter', 'Assigned Recruiter'),
                        ('hiring_manager', 'Hiring Manager'),
                        ('recruiter_manager', 'Recruiter Manager'),
                        ('workflow_owner', 'Workflow Owner'),
                        ('specific_user', 'Specific User'),
                        ('dynamic_field', 'Dynamic Field'),
                    ],
                    max_length=30,
                )),
                ('assignee_field', models.CharField(blank=True, max_length=100)),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent'),
                    ],
                    default='medium', max_length=10,
                )),
                ('due_in_minutes', models.PositiveIntegerField(default=1440)),
                ('escalate_after_minutes', models.PositiveIntegerField(default=2880)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={'verbose_name': 'Workflow Task Rule', 'ordering': ['-created_at']},
        ),
        # ── WorkflowTaskExecution ─────────────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowTaskExecution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('workflow_id', models.UUIDField(db_index=True)),
                ('execution_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('rule', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='executions',
                    to='automation_tasks.workflowtaskrule',
                )),
                ('task_title', models.CharField(max_length=500)),
                ('task_description', models.TextField(blank=True)),
                ('assignee_user_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent'),
                    ],
                    db_index=True, default='medium', max_length=10,
                )),
                ('due_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'), ('in_progress', 'In Progress'),
                        ('completed', 'Completed'), ('overdue', 'Overdue'),
                        ('cancelled', 'Cancelled'), ('escalated', 'Escalated'),
                    ],
                    db_index=True, default='pending', max_length=20,
                )),
                ('escalated', models.BooleanField(db_index=True, default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('context_snapshot', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Workflow Task Execution', 'ordering': ['-created_at']},
        ),
        # ── WorkflowTaskEscalation ────────────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowTaskEscalation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('task_execution', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='escalations',
                    to='automation_tasks.workflowtaskexecution',
                )),
                ('escalation_level', models.PositiveSmallIntegerField(default=1)),
                ('escalated_to', models.UUIDField(blank=True, null=True)),
                ('escalated_to_role', models.CharField(blank=True, max_length=50)),
                ('reason', models.TextField(blank=True)),
                ('escalated_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={'verbose_name': 'Workflow Task Escalation', 'ordering': ['task_execution', 'escalation_level']},
        ),
        # ── WorkflowTaskDependency ────────────────────────────────────────────
        migrations.CreateModel(
            name='WorkflowTaskDependency',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('task_execution', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dependencies',
                    to='automation_tasks.workflowtaskexecution',
                )),
                ('depends_on_task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='unlocks',
                    to='automation_tasks.workflowtaskexecution',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Workflow Task Dependency'},
        ),
        # ── Indexes ───────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='workflowtaskrule',
            index=models.Index(fields=['tenant_id', 'workflow_id'], name='wf_task_rule_tenant_wf_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskrule',
            index=models.Index(fields=['tenant_id', 'is_active'], name='wf_task_rule_active_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskexecution',
            index=models.Index(fields=['tenant_id', 'status'], name='wf_task_exec_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskexecution',
            index=models.Index(fields=['tenant_id', 'assignee_user_id'], name='wf_task_exec_assignee_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskexecution',
            index=models.Index(fields=['tenant_id', 'priority', 'status'], name='wf_task_exec_pri_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskexecution',
            index=models.Index(fields=['tenant_id', 'due_at', 'status'], name='wf_task_exec_due_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskescalation',
            index=models.Index(fields=['tenant_id', 'escalated_at'], name='wf_task_esc_tenant_at_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowtaskdependency',
            index=models.Index(fields=['tenant_id'], name='wf_task_dep_tenant_idx'),
        ),
        migrations.AddConstraint(
            model_name='workflowtaskdependency',
            constraint=models.UniqueConstraint(
                fields=['task_execution', 'depends_on_task'],
                name='unique_task_dependency',
            ),
        ),
    ]
