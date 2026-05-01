import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='WorkflowPermissionPolicy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={
                'verbose_name': 'Workflow Permission Policy',
                'verbose_name_plural': 'Workflow Permission Policies',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowPermissionRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('policy', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rules',
                    to='automation_permissions.workflowpermissionpolicy',
                )),
                ('role_code', models.CharField(max_length=100)),
                ('module_scope', models.CharField(blank=True, max_length=100)),
                ('resource_type', models.CharField(
                    choices=[
                        ('workflow', 'Workflow'),
                        ('workflow_template', 'Workflow Template'),
                        ('workflow_execution', 'Workflow Execution'),
                        ('workflow_governance', 'Workflow Governance'),
                        ('workflow_analytics', 'Workflow Analytics'),
                        ('automation_center', 'Automation Center'),
                    ],
                    max_length=50,
                )),
                ('action_type', models.CharField(
                    choices=[
                        ('view', 'View'), ('create', 'Create'), ('edit', 'Edit'),
                        ('delete', 'Delete'), ('activate', 'Activate'), ('pause', 'Pause'),
                        ('archive', 'Archive'), ('duplicate', 'Duplicate'),
                        ('import_template', 'Import Template'), ('emergency_stop', 'Emergency Stop'),
                        ('rollback', 'Rollback'), ('approve', 'Approve'), ('dry_run', 'Dry Run'),
                        ('view_logs', 'View Logs'), ('view_analytics', 'View Analytics'),
                    ],
                    max_length=50,
                )),
                ('permission_level', models.CharField(
                    choices=[
                        ('allow', 'Allow'), ('deny', 'Deny'), ('require_approval', 'Require Approval'),
                    ],
                    default='deny',
                    max_length=30,
                )),
                ('conditions', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Workflow Permission Rule',
                'ordering': ['role_code', 'resource_type', 'action_type'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowRestrictedAction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('action_key', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('severity', models.CharField(
                    choices=[
                        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical'),
                    ],
                    default='medium',
                    max_length=20,
                )),
                ('requires_approval', models.BooleanField(default=True)),
                ('requires_admin', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Workflow Restricted Action',
                'ordering': ['-severity', 'action_key'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowAccessAudit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('user_id', models.UUIDField(db_index=True)),
                ('workflow_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('action_attempted', models.CharField(max_length=100)),
                ('decision', models.CharField(
                    choices=[
                        ('allowed', 'Allowed'),
                        ('denied', 'Denied'),
                        ('approval_required', 'Approval Required'),
                    ],
                    max_length=30,
                )),
                ('reason', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Workflow Access Audit',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='workflowpermissionpolicy',
            index=models.Index(fields=['tenant_id', 'is_active'], name='wf_perm_policy_tenant_active_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowpermissionrule',
            index=models.Index(fields=['policy', 'role_code'], name='wf_perm_rule_policy_role_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowpermissionrule',
            index=models.Index(fields=['role_code', 'resource_type', 'action_type'], name='wf_perm_rule_role_res_act_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowrestrictedaction',
            index=models.Index(fields=['tenant_id', 'severity'], name='wf_restricted_tenant_sev_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowaccessaudit',
            index=models.Index(fields=['tenant_id', 'created_at'], name='wf_audit_tenant_created_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowaccessaudit',
            index=models.Index(fields=['tenant_id', 'user_id'], name='wf_audit_tenant_user_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowaccessaudit',
            index=models.Index(fields=['tenant_id', 'decision'], name='wf_audit_tenant_decision_idx'),
        ),
    ]
