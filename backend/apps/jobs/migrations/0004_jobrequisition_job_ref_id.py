from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_jobrequisition_guarantee_watch_until_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrequisition',
            name='job_ref_id',
            field=models.CharField(blank=True, db_index=True, max_length=32, null=True, unique=True),
        ),
    ]
