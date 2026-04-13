import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    # ── shared base fields reused in each model ──────────────────────────────
    _BASE = [
        ('id',         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ('tenant_id',  models.UUIDField(blank=True, db_index=True, null=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('updated_at', models.DateTimeField(auto_now=True)),
        ('created_by', models.UUIDField(blank=True, null=True)),
        ('is_deleted', models.BooleanField(db_index=True, default=False)),
        ('deleted_at', models.DateTimeField(blank=True, null=True)),
        ('metadata',   models.JSONField(blank=True, default=dict)),
    ]

    _MATURITY_LEVEL_CHOICES = [
        ('manual', 'Manual'), ('assisted', 'Assisted'), ('structured', 'Structured'),
        ('optimized', 'Optimized'), ('autonomous', 'Autonomous'),
    ]

    operations = [
        # ── AutomationMaturityAssessment ────────────────────────────────────
        migrations.CreateModel(
            name='AutomationMaturityAssessment',
            fields=[
                *_BASE,
                ('assessment_date',       models.DateField(db_index=True)),
                ('overall_maturity_score',models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('maturity_level',        models.CharField(
                    choices=_MATURITY_LEVEL_CHOICES, db_index=True, default='manual', max_length=20
                )),
                ('coverage_score',        models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('adoption_score',        models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('governance_score',      models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('reliability_score',     models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('intelligence_score',    models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('operating_score',       models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('business_impact_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('score_breakdown',       models.JSONField(blank=True, default=dict)),
            ],
            options={'db_table': 'wf_maturity_assessments', 'ordering': ['-assessment_date']},
        ),
        migrations.AddIndex(
            model_name='automationmaturityassessment',
            index=models.Index(fields=['tenant_id', 'assessment_date'], name='am_assess_tenant_date_idx'),
        ),
        migrations.AddIndex(
            model_name='automationmaturityassessment',
            index=models.Index(fields=['tenant_id', 'maturity_level'], name='am_assess_tenant_level_idx'),
        ),

        # ── AutomationModuleMaturity ─────────────────────────────────────────
        migrations.CreateModel(
            name='AutomationModuleMaturity',
            fields=[
                *_BASE,
                ('assessment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='module_scores',
                    to='automation_maturity.automationmaturityassessment',
                )),
                ('module_scope', models.CharField(
                    choices=[
                        ('candidates', 'Candidates'), ('jobs', 'Jobs'), ('pipeline', 'Pipeline'),
                        ('interviews', 'Interviews'), ('offers', 'Offers'), ('agencies', 'Agencies'),
                        ('tasks', 'Tasks'), ('sla', 'SLA'), ('notifications', 'Notifications'),
                        ('cross_module', 'Cross Module'),
                    ],
                    db_index=True, max_length=30,
                )),
                ('maturity_score',              models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('maturity_level',              models.CharField(
                    choices=_MATURITY_LEVEL_CHOICES, default='manual', max_length=20
                )),
                ('automation_coverage_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('workflow_count',              models.PositiveIntegerField(default=0)),
                ('playbook_count',              models.PositiveIntegerField(default=0)),
                ('reliability_score',           models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('governance_score',            models.DecimalField(decimal_places=2, default=0, max_digits=5)),
            ],
            options={'db_table': 'wf_maturity_module_scores', 'ordering': ['-maturity_score']},
        ),
        migrations.AddIndex(
            model_name='automationmodulematurity',
            index=models.Index(fields=['tenant_id', 'module_scope'], name='am_mod_tenant_scope_idx'),
        ),
        migrations.AddIndex(
            model_name='automationmodulematurity',
            index=models.Index(fields=['tenant_id', 'assessment_id'], name='am_mod_tenant_assess_idx'),
        ),

        # ── AutomationTeamAdoption ───────────────────────────────────────────
        migrations.CreateModel(
            name='AutomationTeamAdoption',
            fields=[
                *_BASE,
                ('assessment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='team_scores',
                    to='automation_maturity.automationmaturityassessment',
                )),
                ('team_name',            models.CharField(max_length=200)),
                ('department_id',        models.UUIDField(blank=True, null=True)),
                ('adoption_score',       models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('active_user_count',    models.PositiveIntegerField(default=0)),
                ('workflow_usage_count', models.PositiveIntegerField(default=0)),
                ('playbook_usage_count', models.PositiveIntegerField(default=0)),
                ('manual_override_count',models.PositiveIntegerField(default=0)),
            ],
            options={'db_table': 'wf_maturity_team_adoption', 'ordering': ['-adoption_score']},
        ),
        migrations.AddIndex(
            model_name='automationteamadoption',
            index=models.Index(fields=['tenant_id', 'assessment_id'], name='am_team_tenant_assess_idx'),
        ),

        # ── AutomationMaturityRecommendation ─────────────────────────────────
        migrations.CreateModel(
            name='AutomationMaturityRecommendation',
            fields=[
                *_BASE,
                ('recommendation_type', models.CharField(
                    choices=[
                        ('increase_coverage', 'Increase Coverage'),
                        ('improve_governance', 'Improve Governance'),
                        ('improve_reliability', 'Improve Reliability'),
                        ('enable_playbooks', 'Enable Playbooks'),
                        ('expand_cross_module', 'Expand Cross Module'),
                        ('improve_sla_usage', 'Improve SLA Usage'),
                        ('increase_ai_adoption', 'Increase AI Adoption'),
                        ('strengthen_sandbox_usage', 'Strengthen Sandbox Usage'),
                    ],
                    max_length=40,
                )),
                ('title',                  models.CharField(max_length=255)),
                ('description',            models.TextField()),
                ('target_area',            models.CharField(max_length=100)),
                ('expected_maturity_gain', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('priority', models.CharField(
                    choices=[('low','Low'), ('medium','Medium'), ('high','High'), ('critical','Critical')],
                    db_index=True, default='medium', max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('new','New'), ('acknowledged','Acknowledged'),
                        ('in_progress','In Progress'), ('completed','Completed'), ('ignored','Ignored'),
                    ],
                    db_index=True, default='new', max_length=20,
                )),
            ],
            options={'db_table': 'wf_maturity_recommendations', 'ordering': ['-priority', '-created_at']},
        ),
        migrations.AddIndex(
            model_name='automationmaturityrecommendation',
            index=models.Index(fields=['tenant_id', 'status'], name='am_rec_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='automationmaturityrecommendation',
            index=models.Index(fields=['tenant_id', 'priority'], name='am_rec_tenant_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='automationmaturityrecommendation',
            index=models.Index(fields=['tenant_id', 'recommendation_type'], name='am_rec_tenant_type_idx'),
        ),

        # ── AutomationMaturityRoadmap ────────────────────────────────────────
        migrations.CreateModel(
            name='AutomationMaturityRoadmap',
            fields=[
                *_BASE,
                ('roadmap_name',           models.CharField(max_length=255)),
                ('current_level',          models.CharField(choices=_MATURITY_LEVEL_CHOICES, max_length=20)),
                ('target_level',           models.CharField(choices=_MATURITY_LEVEL_CHOICES, max_length=20)),
                ('roadmap_steps',          models.JSONField(default=list)),
                ('expected_timeline_days', models.PositiveIntegerField(default=90)),
                ('is_active',              models.BooleanField(default=True)),
            ],
            options={'db_table': 'wf_maturity_roadmaps', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='automationmaturityroadmap',
            index=models.Index(fields=['tenant_id', 'is_active'], name='am_roadmap_tenant_active_idx'),
        ),

        # ── AutomationBusinessTransformationMetric ───────────────────────────
        migrations.CreateModel(
            name='AutomationBusinessTransformationMetric',
            fields=[
                *_BASE,
                ('metric_date',                       models.DateField(db_index=True)),
                ('process_name',                      models.CharField(max_length=200)),
                ('manual_effort_reduction_percent',   models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('response_time_improvement_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('sla_improvement_percent',           models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('automation_usage_percent',          models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('executions_this_period',            models.PositiveIntegerField(default=0)),
                ('baseline_executions',               models.PositiveIntegerField(default=0)),
            ],
            options={'db_table': 'wf_maturity_transformation_metrics', 'ordering': ['-metric_date']},
        ),
        migrations.AddIndex(
            model_name='automationbusinesstransformationmetric',
            index=models.Index(fields=['tenant_id', 'metric_date'], name='am_biz_tenant_date_idx'),
        ),
        migrations.AddIndex(
            model_name='automationbusinesstransformationmetric',
            index=models.Index(fields=['tenant_id', 'process_name'], name='am_biz_tenant_process_idx'),
        ),
    ]
