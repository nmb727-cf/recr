from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0014_candidateengagement_unique_active_general_engagement'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='candidate_state',
            field=models.CharField(
                choices=[
                    ('NEW_LEAD', 'New Lead'),
                    ('JOB_ASSOCIATED', 'Job Associated'),
                    ('REVIVED', 'Revived'),
                ],
                db_index=True,
                default='NEW_LEAD',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='candidate_pool',
            field=models.CharField(
                choices=[
                    ('GENERAL', 'General Pool'),
                    ('NONE', 'No Pool'),
                ],
                db_index=True,
                default='GENERAL',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='is_general_pool_used',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
