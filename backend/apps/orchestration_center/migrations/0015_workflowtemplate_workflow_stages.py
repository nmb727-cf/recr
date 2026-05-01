from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('orchestration_center', '0014_workflowfailureinsight_workflowactionmetric_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowtemplate',
            name='workflow_stages',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
