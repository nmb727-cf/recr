import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0012_jobrequisition_agency_commission_fixed_fee_and_more'),
    ]

    operations = [
        # ── JobDescriptionTemplate ──────────────────────────────────────
        migrations.CreateModel(
            name='JobDescriptionTemplate',
            fields=[
                ('id',               models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',        models.UUIDField(db_index=True)),
                ('name',             models.CharField(max_length=255)),
                ('category',         models.CharField(max_length=50, default='other', db_index=True)),
                ('job_type',         models.CharField(max_length=50, blank=True)),
                ('description',      models.TextField(blank=True)),
                ('requirements',     models.TextField(blank=True)),
                ('responsibilities', models.TextField(blank=True)),
                ('skills_suggested', models.JSONField(default=list, blank=True)),
                ('usage_count',      models.PositiveIntegerField(default=0)),
                ('is_active',        models.BooleanField(default=True, db_index=True)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
                ('created_by',       models.UUIDField(null=True, blank=True)),
                ('is_deleted',       models.BooleanField(default=False, db_index=True)),
                ('deleted_at',       models.DateTimeField(null=True, blank=True)),
                ('metadata',         models.JSONField(default=dict, blank=True)),
            ],
            options={'db_table': 'jobs_jd_template', 'ordering': ['-usage_count', '-created_at']},
        ),
        migrations.AddIndex(
            model_name='JobDescriptionTemplate',
            index=models.Index(fields=['tenant_id', 'is_active'], name='jobs_jdt_tenant_active_idx'),
        ),
        migrations.AddIndex(
            model_name='JobDescriptionTemplate',
            index=models.Index(fields=['tenant_id', 'category'], name='jobs_jdt_tenant_category_idx'),
        ),

        # ── JobLocation ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='JobLocation',
            fields=[
                ('id',            models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('tenant_id',     models.UUIDField(db_index=True)),
                ('requisition',   models.ForeignKey(
                    to='jobs.JobRequisition',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='locations',
                )),
                ('location_id',   models.UUIDField(db_index=True)),
                ('location_name', models.CharField(max_length=200, blank=True)),
                ('is_primary',    models.BooleanField(default=False)),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'jobs_location'},
        ),
        migrations.AddIndex(
            model_name='JobLocation',
            index=models.Index(fields=['tenant_id', 'requisition_id'], name='jobs_loc_tenant_req_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='JobLocation',
            unique_together={('requisition', 'location_id')},
        ),
    ]
