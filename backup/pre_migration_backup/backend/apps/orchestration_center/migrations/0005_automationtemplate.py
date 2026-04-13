import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orchestration_center', '0004_automationintelligencepolicy_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('suggestion_type', models.CharField(
                    choices=[
                        ('followup_recommendation', 'Follow-up Recommendation'),
                        ('escalation_recommendation', 'Escalation Recommendation'),
                        ('review_recommendation', 'Review Recommendation'),
                        ('assignment_recommendation', 'Assignment Recommendation'),
                        ('communication_draft', 'Communication Draft'),
                        ('risk_flag_recommendation', 'Risk Flag Recommendation'),
                        ('deadline_recommendation', 'Deadline Recommendation'),
                        ('insight_summary', 'Insight Summary'),
                    ],
                    db_index=True,
                    max_length=64,
                )),
                ('module_scope', models.CharField(blank=True, max_length=64)),
                ('automation_level', models.CharField(
                    choices=[
                        ('suggest_only', 'Suggest Only'),
                        ('auto_approve', 'Auto Approve'),
                        ('auto_apply', 'Auto Apply'),
                    ],
                    default='suggest_only',
                    max_length=20,
                )),
                ('confidence_threshold', models.DecimalField(decimal_places=2, default=0.85, max_digits=5)),
                ('is_builtin', models.BooleanField(db_index=True, default=False)),
                ('tags', models.JSONField(blank=True, default=list)),
            ],
            options={
                'db_table': 'icc_automation_templates',
                'ordering': ['-is_builtin', 'name'],
            },
        ),
    ]
