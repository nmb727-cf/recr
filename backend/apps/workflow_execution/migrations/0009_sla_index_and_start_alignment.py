import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_execution', '0008_workflow_sla_engine'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='workflowslatracker',
            new_name='wf_exec_sla_workflo_fdaefe_idx',
            old_name='wf_exec_sla_workflo_5f0cf7_idx',
        ),
        migrations.RenameIndex(
            model_name='workflowslatracker',
            new_name='wf_exec_sla_stage_e_a83dc3_idx',
            old_name='wf_exec_sla_stage_e_4f808d_idx',
        ),
        migrations.RenameIndex(
            model_name='workflowstagesla',
            new_name='wf_exec_sta_workflo_ca347f_idx',
            old_name='wf_exec_sta_workflo_6a3147_idx',
        ),
        migrations.AlterField(
            model_name='workflowslatracker',
            name='sla_start',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
    ]
