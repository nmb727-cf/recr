import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0024_alter_jobhiringteammember_unique_together_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobstage',
            name='responsible_user_id',
        ),
        migrations.AddField(
            model_name='jobstage',
            name='responsible_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='responsible_stages', to=settings.AUTH_USER_MODEL),
        ),
    ]
