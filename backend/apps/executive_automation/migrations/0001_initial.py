import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ------------------------------------------------------------------
        # ExecutiveAutomationSummary
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='ExecutiveAutomationSummary',
            fields=[
                ('id',                          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',                   models.UUIDField(db_index=True)),
                ('is_deleted',                  models.BooleanField(default=False)),
                ('deleted_at',                  models.DateTimeField(null=True, blank=True)),
                ('created_at',                  models.DateTimeField(auto_now_add=True)),
                ('updated_at',                  models.DateTimeField(auto_now=True)),
                ('metadata',                    models.JSONField(default=dict, blank=True)),
                ('snapshot_date',               models.DateField(db_index=True)),
                ('total_workflows',             models.PositiveIntegerField(default=0)),
                ('active_workflows',            models.PositiveIntegerField(default=0)),
                ('total_executions_today',      models.PositiveIntegerField(default=0)),
                ('successful_executions_today', models.PositiveIntegerField(default=0)),
                ('automation_coverage_percent', models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('automation_maturity_level',   models.CharField(max_length=20, default='manual')),
                ('time_saved_hours',            models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('tasks_automated',             models.PositiveIntegerField(default=0)),
                ('sla_improvement_percent',     models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('open_risks',                  models.PositiveIntegerField(default=0)),
                ('open_opportunities',          models.PositiveIntegerField(default=0)),
                ('business_impact_score',       models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ],
            options={'db_table': 'exec_automation_summary', 'ordering': ['-snapshot_date']},
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationSummary',
            index=models.Index(fields=['tenant_id', 'snapshot_date'], name='exec_sum_tenant_date_idx'),
        ),

        # ------------------------------------------------------------------
        # ExecutiveAutomationROI
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='ExecutiveAutomationROI',
            fields=[
                ('id',                          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',                   models.UUIDField(db_index=True)),
                ('is_deleted',                  models.BooleanField(default=False)),
                ('deleted_at',                  models.DateTimeField(null=True, blank=True)),
                ('created_at',                  models.DateTimeField(auto_now_add=True)),
                ('updated_at',                  models.DateTimeField(auto_now=True)),
                ('metadata',                    models.JSONField(default=dict, blank=True)),
                ('period',                      models.CharField(max_length=10, default='monthly')),
                ('period_start',                models.DateField(db_index=True)),
                ('period_end',                  models.DateField()),
                ('hours_saved',                 models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('manual_tasks_reduced',        models.PositiveIntegerField(default=0)),
                ('operational_cost_reduction',  models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('productivity_gain_percent',   models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('executions_count',            models.PositiveIntegerField(default=0)),
                ('success_rate',                models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ],
            options={'db_table': 'exec_automation_roi', 'ordering': ['-period_start']},
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationROI',
            index=models.Index(fields=['tenant_id', 'period', 'period_start'], name='exec_roi_tenant_period_idx'),
        ),

        # ------------------------------------------------------------------
        # ExecutiveAutomationRisk
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='ExecutiveAutomationRisk',
            fields=[
                ('id',              models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',       models.UUIDField(db_index=True)),
                ('is_deleted',      models.BooleanField(default=False)),
                ('deleted_at',      models.DateTimeField(null=True, blank=True)),
                ('created_at',      models.DateTimeField(auto_now_add=True)),
                ('updated_at',      models.DateTimeField(auto_now=True)),
                ('metadata',        models.JSONField(default=dict, blank=True)),
                ('risk_type',       models.CharField(max_length=30, db_index=True)),
                ('severity',        models.CharField(max_length=20, default='medium', db_index=True)),
                ('affected_module', models.CharField(max_length=100, blank=True)),
                ('title',           models.CharField(max_length=255)),
                ('description',     models.TextField()),
                ('status',          models.CharField(max_length=20, default='open', db_index=True)),
                ('metric_value',    models.JSONField(default=dict, blank=True)),
            ],
            options={'db_table': 'exec_automation_risks', 'ordering': ['-severity', '-created_at']},
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationRisk',
            index=models.Index(fields=['tenant_id', 'status'], name='exec_risk_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationRisk',
            index=models.Index(fields=['tenant_id', 'severity'], name='exec_risk_tenant_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationRisk',
            index=models.Index(fields=['tenant_id', 'risk_type'], name='exec_risk_tenant_type_idx'),
        ),

        # ------------------------------------------------------------------
        # ExecutiveAutomationDepartment
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='ExecutiveAutomationDepartment',
            fields=[
                ('id',                  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',           models.UUIDField(db_index=True)),
                ('is_deleted',          models.BooleanField(default=False)),
                ('deleted_at',          models.DateTimeField(null=True, blank=True)),
                ('created_at',          models.DateTimeField(auto_now_add=True)),
                ('updated_at',          models.DateTimeField(auto_now=True)),
                ('metadata',            models.JSONField(default=dict, blank=True)),
                ('snapshot_date',       models.DateField(db_index=True)),
                ('department_name',     models.CharField(max_length=200)),
                ('automation_coverage', models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('adoption_score',      models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('maturity_level',      models.CharField(max_length=20, default='manual')),
                ('manual_gap_percent',  models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('workflow_count',      models.PositiveIntegerField(default=0)),
                ('executions_30d',      models.PositiveIntegerField(default=0)),
            ],
            options={'db_table': 'exec_automation_departments', 'ordering': ['-automation_coverage']},
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationDepartment',
            index=models.Index(fields=['tenant_id', 'snapshot_date'], name='exec_dept_tenant_date_idx'),
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationDepartment',
            index=models.Index(fields=['tenant_id', 'department_name'], name='exec_dept_tenant_name_idx'),
        ),

        # ------------------------------------------------------------------
        # ExecutiveAutomationOpportunity
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='ExecutiveAutomationOpportunity',
            fields=[
                ('id',               models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',        models.UUIDField(db_index=True)),
                ('is_deleted',       models.BooleanField(default=False)),
                ('deleted_at',       models.DateTimeField(null=True, blank=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
                ('metadata',         models.JSONField(default=dict, blank=True)),
                ('opportunity_type', models.CharField(max_length=40)),
                ('module',           models.CharField(max_length=100)),
                ('title',            models.CharField(max_length=255)),
                ('description',      models.TextField()),
                ('expected_impact',  models.CharField(max_length=255)),
                ('priority',         models.CharField(max_length=20, default='medium', db_index=True)),
                ('status',           models.CharField(max_length=20, default='new', db_index=True)),
                ('assigned_to',      models.UUIDField(null=True, blank=True)),
                ('source_data',      models.JSONField(default=dict, blank=True)),
            ],
            options={'db_table': 'exec_automation_opportunities', 'ordering': ['-priority', '-created_at']},
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationOpportunity',
            index=models.Index(fields=['tenant_id', 'status'], name='exec_opp_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationOpportunity',
            index=models.Index(fields=['tenant_id', 'priority'], name='exec_opp_tenant_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='ExecutiveAutomationOpportunity',
            index=models.Index(fields=['tenant_id', 'opportunity_type'], name='exec_opp_tenant_type_idx'),
        ),
    ]
