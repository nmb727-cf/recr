from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0015_rename_jobs_jdt_tenant_active_idx_jobs_jd_tem_tenant__db8d0f_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobstage',
            name='responsible_user_id',
            field=models.UUIDField(blank=True, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='jobstage',
            name='trigger_type',
            field=models.CharField(
                choices=[
                    ('none', 'None'),
                    ('interview', 'Interview Round'),
                    ('prequal', 'Prequalification'),
                    ('assessment', 'External Assessment'),
                    ('approval', 'Stage Approval'),
                ],
                default='none',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='jobstage',
            name='trigger_config',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
