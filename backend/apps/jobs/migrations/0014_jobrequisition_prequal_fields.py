from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0013_jobdescriptiontemplate_joblocation'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrequisition',
            name='prequal_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='prequal_form_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='prequal_threshold_override',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Override the form default pass threshold (0-100). Null = use form default.',
            ),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='prequal_pass_action',
            field=models.CharField(
                choices=[
                    ('advance', 'Advance to Next Stage'),
                    ('manual_review', 'Flag for Manual Review'),
                ],
                default='advance',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='prequal_fail_action',
            field=models.CharField(
                choices=[
                    ('reject', 'Auto-Reject'),
                    ('hold', 'Hold — Awaiting Review'),
                    ('manual_review', 'Flag for Manual Review'),
                ],
                default='reject',
                max_length=50,
            ),
        ),
    ]
