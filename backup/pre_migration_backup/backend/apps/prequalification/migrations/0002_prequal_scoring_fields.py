from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prequalification', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='prequalquestion',
            name='score_weight',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='prequalquestion',
            name='is_knockout',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prequalrule',
            name='outcome_code',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
