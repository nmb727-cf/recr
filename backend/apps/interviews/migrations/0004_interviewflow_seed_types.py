import uuid
from django.db import migrations, models


# ─── 40 interview type seed records ───────────────────────────────────────────

INTERVIEW_TYPE_SEED = [
    # Screening
    ('Recruiter Screening',        'recruiter_screening',     'Initial recruiter-led qualification call to assess baseline fit.'),
    ('AI Screening',               'ai_screening',            'Automated AI-driven candidate screening with dynamic questioning.'),
    ('Phone Interview',            'phone_interview',          'Structured phone-based interview for early-stage candidates.'),

    # Video
    ('One-Way Video',              'one_way_video',            'Candidate records async video responses to pre-set questions.'),
    ('Pre-Recorded Video',         'prerecorded_video',        'Recruiter sends a pre-recorded video with embedded questions.'),
    ('Live Video Interview',       'live_video',               'Real-time synchronous video interview via integrated conferencing.'),

    # Async
    ('Async Text Interview',       'async_text_interview',     'Text-based asynchronous Q&A delivered via chat interface.'),

    # Technical
    ('Technical Interview',        'technical_interview',      'Deep technical skills and domain knowledge probe.'),
    ('Coding Interview',           'coding_interview',         'Live or recorded coding challenge with real-time evaluation.'),
    ('System Design',              'system_design',            'Architecture and system design evaluation round.'),
    ('Take-Home Assignment',       'take_home_assignment',     'Offline project or assignment submission for async evaluation.'),
    ('Debugging Interview',        'debugging_interview',      'Candidate finds and fixes bugs in provided codebase.'),
    ('Whiteboard Interview',       'whiteboard_interview',     'Problem-solving on a shared whiteboard (virtual or physical).'),
    ('Technical Panel',            'technical_panel',          'Multiple technical interviewers evaluating in a single session.'),

    # Behavioral
    ('Behavioral Interview',       'behavioral_interview',     'STAR-based past behavior and competency assessment.'),
    ('Cultural Fit Interview',     'cultural_fit',             'Values alignment and organizational culture assessment.'),

    # HR / People
    ('HR Interview',               'hr_interview',             'HR-led competency check, compensation discussion, and culture alignment.'),
    ('Leadership Interview',       'leadership_interview',     'Leadership capability, style, and decision-making evaluation.'),
    ('Executive Interview',        'executive_interview',      'C-suite or VP-level strategic and vision discussion.'),
    ('Hiring Manager Interview',   'hiring_manager_interview', 'Direct hiring manager qualification and role-fit round.'),

    # Panel / Group
    ('Panel Interview',            'panel_interview',          'Multiple interviewers evaluating a candidate simultaneously.'),
    ('Sequential Round',           'sequential_round',         'Series of back-to-back one-on-one interviews in sequence.'),
    ('Stakeholder Interview',      'stakeholder_interview',    'Interview with cross-functional stakeholders and business partners.'),
    ('Bar Raiser',                 'bar_raiser',               'Amazon-style independent raising-the-bar evaluation interview.'),
    ('Final Round',                'final_round',              'Final decision-making round with senior stakeholders.'),
    ('Group Discussion',           'group_discussion',         'Group candidate interaction, debate, and assessment exercise.'),

    # Assessment
    ('MCQ Assessment',             'mcq_assessment',           'Timed multiple-choice knowledge and aptitude assessment.'),
    ('Aptitude Test',              'aptitude_test',            'Numerical, verbal, and abstract reasoning evaluation.'),
    ('Psychometric Test',          'psychometric_test',        'Personality, motivation, and cognitive trait evaluation.'),
    ('Cognitive Test',             'cognitive_test',           'Cognitive ability, mental agility, and problem-solving test.'),
    ('Language Assessment',        'language_assessment',      'Language proficiency, communication, and writing skills test.'),

    # Simulation
    ('Case Study',                 'case_study',               'Structured problem-solving exercise using real business data.'),
    ('Role Play',                  'role_play',                'Simulated real-world scenario to assess practical skills.'),
    ('Work Sample Test',           'work_sample_test',         'Candidate performs an actual job task as a performance sample.'),
    ('Presentation Interview',     'presentation_interview',   'Candidate delivers a prepared topic or project presentation.'),
    ('Portfolio Review',           'portfolio_review',         'Structured review and discussion of candidate portfolio work.'),

    # Special Formats
    ('Assessment Center',          'assessment_center',        'Full-day multi-exercise assessment event with multiple evaluators.'),
    ('Mock Interview',             'mock_interview',           'Practice or preparation interview simulation round.'),
    ('Campus Hiring',              'campus_hiring',            'University campus recruitment drive interview.'),
    ('Walk-In Drive',              'walkin_drive',             'Open walk-in interview event for high-volume hiring.'),
    ('Interview Café Live',        'interview_cafe_live',      'TOS Café live AI-powered immersive interview session.'),
]


def seed_interview_types(apps, schema_editor):
    InterviewType = apps.get_model('interviews', 'InterviewType')
    for name, code, description in INTERVIEW_TYPE_SEED:
        InterviewType.objects.get_or_create(
            code=code,
            defaults={
                'id': uuid.uuid4(),
                'name': name,
                'description': description,
                'is_active': True,
                'is_deleted': False,
                'metadata': {},
            },
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0003_interviewdecision_created_at_and_more'),
    ]

    operations = [
        # ── InterviewFlow table ───────────────────────────────────────────────
        migrations.CreateModel(
            name='InterviewFlow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('stages', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'interviews_flow',
                'ordering': ['-created_at'],
            },
        ),

        # ── Seed 40 interview types ───────────────────────────────────────────
        migrations.RunPython(seed_interview_types, reverse_code=noop),
    ]
