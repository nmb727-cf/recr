from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0018_jobrequisition_is_workflow_controlled'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE jobs_requisition ADD COLUMN IF NOT EXISTS auto_assign_recruiter boolean NOT NULL DEFAULT false;
                ALTER TABLE jobs_requisition ADD COLUMN IF NOT EXISTS auto_assign_agencies boolean NOT NULL DEFAULT false;
                ALTER TABLE jobs_requisition ADD COLUMN IF NOT EXISTS auto_publish_enabled boolean NOT NULL DEFAULT false;
                ALTER TABLE jobs_requisition ADD COLUMN IF NOT EXISTS onboarding_automation_enabled boolean NOT NULL DEFAULT false;
            """,
            reverse_sql="""
                ALTER TABLE jobs_requisition DROP COLUMN IF EXISTS auto_assign_recruiter;
                ALTER TABLE jobs_requisition DROP COLUMN IF EXISTS auto_assign_agencies;
                ALTER TABLE jobs_requisition DROP COLUMN IF EXISTS auto_publish_enabled;
                ALTER TABLE jobs_requisition DROP COLUMN IF EXISTS onboarding_automation_enabled;
            """,
            state_operations=[
                migrations.AddField(
                    model_name='jobrequisition',
                    name='auto_assign_recruiter',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='jobrequisition',
                    name='auto_assign_agencies',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='jobrequisition',
                    name='auto_publish_enabled',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='jobrequisition',
                    name='onboarding_automation_enabled',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
