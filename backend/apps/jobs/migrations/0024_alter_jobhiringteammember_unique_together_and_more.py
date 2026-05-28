import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0023_add_shortlisted_stage_type'),
        ('organisations', '0005_organisation_primary_currency_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Handle Requisition fields
        migrations.RemoveField(model_name='jobrequisition', name='department_id'),
        migrations.RemoveField(model_name='jobrequisition', name='location_id'),
        migrations.RemoveField(model_name='jobrequisition', name='job_owner_id'),
        migrations.RemoveField(model_name='jobrequisition', name='hiring_manager_id'),
        migrations.RemoveField(model_name='jobrequisition', name='recruiter_id'),
        migrations.RemoveField(model_name='jobrequisition', name='backup_recruiter_id'),
        migrations.RemoveField(model_name='jobrequisition', name='coordinator_id'),

        migrations.AddField(
            model_name='jobrequisition',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requisitions', to='organisations.department'),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='primary_requisitions', to='organisations.location'),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='job_owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='owned_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='hiring_manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='recruiter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='backup_recruiter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='backup_assigned_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jobrequisition',
            name='coordinator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coordinated_jobs', to=settings.AUTH_USER_MODEL),
        ),

        # Handle HiringTeamMember
        migrations.RemoveField(model_name='jobhiringteammember', name='user_id'),
        migrations.AddField(
            model_name='jobhiringteammember',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_team_memberships', to=settings.AUTH_USER_MODEL),
        ),

        # Handle JobLocation
        migrations.RemoveField(model_name='joblocation', name='location_id'),
        migrations.AddField(
            model_name='joblocation',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_locations', to='organisations.location'),
        ),
    ]
