from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0004_rename_cr_company_pstatus_idx_pipeline_co_company_5e3ff6_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[
                    ('applied', 'Applied'),
                    ('sourcing', 'Sourcing'),
                    ('screening', 'Screening'),
                    ('shortlisted', 'Shortlisted'),
                    ('interview', 'Interview'),
                    ('assessment', 'Assessment'),
                    ('offer', 'Offer'),
                    ('joined', 'Joined'),
                    ('rejected', 'Rejected'),
                    ('withdrawn', 'Withdrawn'),
                    ('on_hold', 'On Hold'),
                ],
                default='applied',
                max_length=50,
            ),
        ),
    ]
