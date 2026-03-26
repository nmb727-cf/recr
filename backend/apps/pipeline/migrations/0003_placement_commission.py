import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0002_placementguarantee'),
    ]

    operations = [
        migrations.CreateModel(
            name='Placement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('application_id', models.UUIDField(db_index=True, unique=True)),
                ('candidate_id', models.UUIDField(db_index=True)),
                ('requisition_id', models.UUIDField(db_index=True)),
                ('agency_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('agency_relationship_id', models.UUIDField(blank=True, null=True)),
                ('placement_status', models.CharField(
                    choices=[
                        ('pending_offer', 'Pending Offer Response'),
                        ('offer_accepted', 'Offer Accepted'),
                        ('pending_join', 'Pending Join'),
                        ('joined', 'Joined'),
                        ('placement_confirmed', 'Placement Confirmed'),
                        ('cancelled', 'Cancelled'),
                        ('guarantee_active', 'Guarantee Active'),
                    ],
                    db_index=True,
                    default='pending_offer',
                    max_length=30,
                )),
                ('offer_accepted_at', models.DateTimeField(blank=True, null=True)),
                ('joining_date', models.DateField(blank=True, null=True)),
                ('joined_at', models.DateTimeField(blank=True, null=True)),
                ('placement_confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('credited_recruiter_id', models.UUIDField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'pipeline_placement',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CommissionRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('placement_id', models.UUIDField(db_index=True, unique=True)),
                ('application_id', models.UUIDField(db_index=True)),
                ('requisition_id', models.UUIDField(db_index=True)),
                ('company_tenant_id', models.UUIDField(db_index=True)),
                ('agency_tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('agency_relationship_id', models.UUIDField(blank=True, null=True)),
                ('commission_applicable', models.BooleanField(default=True)),
                ('commission_model', models.CharField(
                    choices=[
                        ('percentage', 'Percentage of Salary'),
                        ('fixed', 'Fixed Fee'),
                        ('milestone', 'Milestone Based'),
                        ('custom', 'Custom'),
                    ],
                    default='percentage',
                    max_length=20,
                )),
                ('basis_source', models.CharField(
                    choices=[
                        ('inherited', 'Inherited from Agency Relationship'),
                        ('custom_per_job', 'Custom per Job'),
                        ('manual', 'Manually Set'),
                    ],
                    default='manual',
                    max_length=30,
                )),
                ('commission_rate', models.DecimalField(blank=True, decimal_places=2, help_text='Percentage rate (e.g. 15.00 = 15%)', max_digits=5, null=True)),
                ('commission_fixed_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('expected_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('currency', models.CharField(default='INR', max_length=10)),
                ('payment_status', models.CharField(
                    choices=[
                        ('not_started', 'Not Started'),
                        ('pending_invoice', 'Pending Invoice'),
                        ('invoice_expected', 'Invoice Expected'),
                        ('payment_due', 'Payment Due'),
                        ('reminder_sent', 'Reminder Sent'),
                        ('overdue', 'Overdue'),
                        ('paid', 'Paid'),
                        ('disputed', 'Disputed'),
                        ('waived', 'Waived'),
                    ],
                    db_index=True,
                    default='not_started',
                    max_length=30,
                )),
                ('due_date', models.DateField(blank=True, null=True)),
                ('paid_date', models.DateField(blank=True, null=True)),
                ('paid_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('payment_notes', models.TextField(blank=True)),
                ('reminder_count', models.PositiveIntegerField(default=0)),
                ('last_reminder_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'pipeline_commission_record',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CommissionReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('commission_record_id', models.UUIDField(db_index=True)),
                ('reminder_type', models.CharField(
                    choices=[
                        ('initial_notice', 'Initial Notice'),
                        ('follow_up', 'Follow Up'),
                        ('final_notice', 'Final Notice'),
                        ('manual', 'Manual'),
                    ],
                    default='manual',
                    max_length=20,
                )),
                ('channel', models.CharField(
                    choices=[
                        ('email', 'Email'),
                        ('phone', 'Phone'),
                        ('whatsapp', 'WhatsApp'),
                        ('manual', 'Manual'),
                    ],
                    default='manual',
                    max_length=20,
                )),
                ('sent_by', models.UUIDField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.TextField(blank=True)),
                ('outcome', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'pipeline_commission_reminder',
                'ordering': ['-sent_at'],
            },
        ),
        migrations.AddIndex(
            model_name='placement',
            index=models.Index(fields=['tenant_id', 'placement_status'], name='pl_tenant_status_idx'),
        ),
        migrations.AddIndex(
            model_name='placement',
            index=models.Index(fields=['requisition_id', 'placement_status'], name='pl_req_status_idx'),
        ),
        migrations.AddIndex(
            model_name='commissionrecord',
            index=models.Index(fields=['company_tenant_id', 'payment_status'], name='cr_company_pstatus_idx'),
        ),
        migrations.AddIndex(
            model_name='commissionrecord',
            index=models.Index(fields=['requisition_id', 'payment_status'], name='cr_req_pstatus_idx'),
        ),
    ]
