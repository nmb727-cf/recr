from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0017_alter_candidate_availability_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='candidate_ref_id',
            field=models.CharField(blank=True, db_index=True, max_length=32, null=True, unique=True),
        ),
    ]
