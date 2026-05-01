from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0019_jobrequisition_automation_binding_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE jobs_stage ADD COLUMN IF NOT EXISTS responsible_role varchar(50) NOT NULL DEFAULT 'recruiter';",
            reverse_sql="ALTER TABLE jobs_stage DROP COLUMN IF EXISTS responsible_role;",
            state_operations=[
                migrations.AddField(
                    model_name='jobstage',
                    name='responsible_role',
                    field=models.CharField(
                        choices=[
                            ('hiring_manager', 'Hiring Manager'),
                            ('recruiter', 'Recruiter'),
                            ('coordinator', 'Coordinator'),
                            ('interviewer', 'Interviewer/Panel'),
                            ('agency', 'Agency'),
                            ('external', 'External Provider'),
                        ],
                        default='recruiter',
                        max_length=50,
                    ),
                ),
            ],
        ),
    ]
