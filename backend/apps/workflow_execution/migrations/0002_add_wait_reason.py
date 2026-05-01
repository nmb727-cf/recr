from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowinstance',
            name='wait_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('waiting_approval', 'Waiting Approval'),
                    ('waiting_candidate', 'Waiting Candidate'),
                    ('waiting_client', 'Waiting Client'),
                    ('waiting_recruiter', 'Waiting Recruiter'),
                    ('waiting_scheduler', 'Waiting Scheduler'),
                    ('waiting_signature', 'Waiting Signature'),
                    ('waiting_other', 'Waiting Other'),
                ],
                db_index=True,
                max_length=32,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='workflowstageexecution',
            name='wait_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('waiting_approval', 'Waiting Approval'),
                    ('waiting_candidate', 'Waiting Candidate'),
                    ('waiting_client', 'Waiting Client'),
                    ('waiting_recruiter', 'Waiting Recruiter'),
                    ('waiting_scheduler', 'Waiting Scheduler'),
                    ('waiting_signature', 'Waiting Signature'),
                    ('waiting_other', 'Waiting Other'),
                ],
                max_length=32,
                null=True,
            ),
        ),
    ]
