import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PrequalForm',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'prequalification_form',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PrequalSection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('form', models.ForeignKey(
                    db_column='form_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sections',
                    to='prequalification.prequalform',
                )),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('order', models.IntegerField(db_index=True, default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'prequalification_section',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='PrequalQuestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('section', models.ForeignKey(
                    db_column='section_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='questions',
                    to='prequalification.prequalsection',
                )),
                ('question_text', models.TextField()),
                ('question_type', models.CharField(
                    choices=[
                        ('yes_no', 'Yes / No'),
                        ('multiple_choice', 'Multiple Choice'),
                        ('text', 'Text'),
                        ('number', 'Number'),
                        ('dropdown', 'Dropdown'),
                        ('file_upload', 'File Upload'),
                    ],
                    default='yes_no',
                    max_length=50,
                )),
                ('required', models.BooleanField(default=True)),
                ('order', models.IntegerField(db_index=True, default=0)),
                ('help_text', models.TextField(blank=True)),
                ('options_json', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'prequalification_question',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='PrequalRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('question', models.ForeignKey(
                    db_column='question_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rules',
                    to='prequalification.prequalquestion',
                )),
                ('condition_type', models.CharField(
                    choices=[
                        ('equals', 'Equals'),
                        ('not_equals', 'Not Equals'),
                        ('greater_than', 'Greater Than'),
                        ('less_than', 'Less Than'),
                        ('contains', 'Contains'),
                        ('is_empty', 'Is Empty'),
                        ('is_not_empty', 'Is Not Empty'),
                    ],
                    default='equals',
                    max_length=50,
                )),
                ('compare_value', models.CharField(blank=True, max_length=500)),
                ('action_type', models.CharField(
                    choices=[
                        ('reject', 'Reject'),
                        ('next_question', 'Next Question'),
                        ('skip_section', 'Skip Section'),
                        ('manual_review', 'Manual Review'),
                        ('show_question', 'Show Question'),
                        ('hide_question', 'Hide Question'),
                    ],
                    default='next_question',
                    max_length=50,
                )),
                ('target_question_id', models.UUIDField(blank=True, null=True)),
                ('target_section_id', models.UUIDField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'prequalification_rule',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='PrequalResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('form', models.ForeignKey(
                    db_column='form_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='prequalification.prequalform',
                )),
                ('candidate_id', models.UUIDField(db_index=True)),
                ('question', models.ForeignKey(
                    db_column='question_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='prequalification.prequalquestion',
                )),
                ('answer_text', models.TextField(blank=True)),
                ('answer_json', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'prequalification_response',
                'ordering': ['-created_at'],
            },
        ),
    ]
