from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0020_jobstage_responsible_role'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE jobs_stage ADD COLUMN IF NOT EXISTS decision_authority varchar(50) NOT NULL DEFAULT 'any';",
            reverse_sql="ALTER TABLE jobs_stage DROP COLUMN IF EXISTS decision_authority;",
            state_operations=[
                migrations.AddField(
                    model_name='jobstage',
                    name='decision_authority',
                    field=models.CharField(
                        choices=[
                            ('hiring_manager', 'Hiring Manager'),
                            ('recruiter', 'Recruiter'),
                            ('coordinator', 'Coordinator'),
                            ('approver', 'Specific Approver'),
                            ('admin', 'Admin/Owner'),
                            ('any', 'Anyone in Team'),
                        ],
                        default='any',
                        max_length=50,
                    ),
                ),
            ],
        ),
    ]
