from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0018_candidate_candidate_ref_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='user_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]
