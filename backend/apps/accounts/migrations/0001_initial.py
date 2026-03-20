from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('phone_verified', models.BooleanField(default=False)),
                ('avatar_url', models.TextField(blank=True)),
                ('role', models.CharField(choices=[('super_admin', 'Super Admin'), ('tenant_admin', 'Tenant Admin'), ('hr_manager', 'HR Manager'), ('hiring_manager', 'Hiring Manager'), ('recruiter', 'Recruiter'), ('interviewer', 'Interviewer'), ('agency_owner', 'Agency Owner'), ('agency_recruiter', 'Agency Recruiter'), ('candidate', 'Candidate'), ('viewer', 'Viewer')], default='viewer', max_length=50)),
                ('last_login_ip', models.CharField(blank=True, max_length=45)),
                ('mfa_enabled', models.BooleanField(default=False)),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('language', models.CharField(default='en', max_length=10)),
                ('ui_preferences', models.JSONField(blank=True, default=dict)),
                ('notification_preferences', models.JSONField(blank=True, default=dict)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('groups', models.ManyToManyField(blank=True, related_name='customuser_set', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='customuser_set', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'accounts_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
