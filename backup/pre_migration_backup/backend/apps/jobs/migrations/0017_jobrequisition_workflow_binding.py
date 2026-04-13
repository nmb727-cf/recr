from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0016_jobstage_binding_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrequisition',
            name='workflow_id',
            field=models.UUIDField(blank=True, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='workflow_template_id',
            field=models.UUIDField(blank=True, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='workflow_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
