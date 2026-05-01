from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0005_workflow_instance_tracker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflowwaitstate',
            name='wait_type',
            field=models.CharField(default='manual', max_length=32),
        ),
    ]
