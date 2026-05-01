from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0017_jobrequisition_workflow_binding'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrequisition',
            name='is_workflow_controlled',
            field=models.BooleanField(default=False),
        ),
    ]
