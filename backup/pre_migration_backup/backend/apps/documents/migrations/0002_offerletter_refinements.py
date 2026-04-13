from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offerletter',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='offerletter',
            name='version',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='offerletter',
            name='parent_offer_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]
