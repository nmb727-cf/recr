from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0004_interviewflow_seed_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterviewScorecardTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('interview_type', models.CharField(choices=[('ai_screening', 'AI Screening'), ('one_way_video', 'One-Way Video'), ('live_video', 'Live Video'), ('panel', 'Panel'), ('technical', 'Technical'), ('group_discussion', 'Group Discussion'), ('psychometric', 'Psychometric'), ('case_study', 'Case Study'), ('mock', 'Mock')], default='ai_screening', max_length=50)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'interviews_scorecard_template',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InterviewScorecardAttribute',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('attribute_name', models.CharField(max_length=255)),
                ('weight', models.DecimalField(decimal_places=2, default=1, max_digits=6)),
                ('rating_type', models.CharField(choices=[('scale_1_5', '1-5 Scale'), ('yes_no', 'Yes / No'), ('pass_fail', 'Pass / Fail'), ('custom_scale', 'Custom Scale')], default='scale_1_5', max_length=20)),
                ('required', models.BooleanField(default=True)),
                ('custom_scale', models.JSONField(blank=True, default=list)),
                ('order_index', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('scorecard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='interviews.interviewscorecardtemplate')),
            ],
            options={
                'db_table': 'interviews_scorecard_attribute',
                'ordering': ['order_index', 'created_at'],
            },
        ),
        migrations.AddField(
            model_name='interview',
            name='scorecard_template_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='interviewfeedback',
            name='scorecard_ratings',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddConstraint(
            model_name='interviewscorecardattribute',
            constraint=models.UniqueConstraint(fields=('scorecard', 'attribute_name'), name='uniq_scorecard_attribute_name'),
        ),
    ]
