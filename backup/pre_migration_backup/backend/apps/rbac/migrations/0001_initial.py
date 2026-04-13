import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=200, unique=True)),
                ('module', models.CharField(db_index=True, max_length=100)),
                ('resource', models.CharField(max_length=100)),
                ('action', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'rbac_permission',
                'ordering': ['module', 'resource', 'action'],
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('display_name', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('is_system', models.BooleanField(default=True)),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'rbac_role',
                'unique_together': {('name', 'tenant_id')},
            },
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('permission', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='role_permissions',
                    to='rbac.permission',
                )),
                ('role', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='role_permissions',
                    to='rbac.role',
                )),
            ],
            options={
                'db_table': 'rbac_role_permission',
                'unique_together': {('role', 'permission')},
            },
        ),
        migrations.AddField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(
                blank=True,
                related_name='roles',
                through='rbac.RolePermission',
                to='rbac.permission',
            ),
        ),
    ]
