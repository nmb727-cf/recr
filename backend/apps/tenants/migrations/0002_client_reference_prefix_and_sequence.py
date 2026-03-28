from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='reference_prefix_auto',
            field=models.CharField(blank=True, max_length=12, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='client',
            name='reference_prefix_custom',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.CreateModel(
            name='TenantReferenceSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('entity_type', models.CharField(choices=[('CC', 'Company Candidate'), ('AC', 'Agency Candidate'), ('DC', 'Direct Candidate'), ('CJ', 'Company Job'), ('AJ', 'Agency Job')], max_length=2)),
                ('year_suffix', models.CharField(db_index=True, max_length=2)),
                ('next_value', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'tenants_reference_sequence',
            },
        ),
        migrations.AddConstraint(
            model_name='tenantreferencesequence',
            constraint=models.UniqueConstraint(fields=('tenant_id', 'entity_type', 'year_suffix'), name='uniq_ref_seq_tenant_type_year'),
        ),
    ]
