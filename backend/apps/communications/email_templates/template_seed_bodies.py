"""
Canonical template bodies for the 5 core business email templates.

Tag syntax: Django template {{ variable }} — same syntax that
EmailTemplateService.render_template_string() processes.

Call apply_core_template_bodies() in a management command or post-migration
signal to upsert these bodies into existing EmailTemplateDefinition rows.
These are idempotent — safe to run multiple times.
"""

from django.db import transaction

# Each entry: (slug, subject_template, body_html, variables_schema_json)
CORE_TEMPLATE_BODIES = [
    (
        'interview_invite',
        'Interview Invitation for {{ job_title }} at {{ company_name }}',
        """Hello {{ candidate_first_name }},

We would like to invite you for an interview for the role of {{ job_title }} at {{ company_name }}.

Interview Details:
- Date: {{ interview_date }}
- Time: {{ interview_time }}
- Mode: {{ interview_mode }}
- Location / Link: {{ meeting_link }}

Please confirm your availability by replying to this email.

Regards,
{{ recruiter_name }}
{{ sender_email }}""",
        {
            'variables': [
                'candidate_first_name', 'job_title', 'company_name',
                'interview_date', 'interview_time', 'interview_mode',
                'meeting_link', 'recruiter_name', 'sender_email',
            ]
        },
    ),
    (
        'offer_letter_email',
        'Offer for {{ job_title }} at {{ company_name }}',
        """Hello {{ candidate_first_name }},

We are pleased to extend an offer for the position of {{ job_title }} at {{ company_name }}.

Offer Details:
- Title: {{ offer_title }}
- Compensation: {{ offer_salary }}
- Joining Date: {{ offer_joining_date }}
- Offer Valid Until: {{ offer_expiry_date }}

Please review and let us know your confirmation at the earliest.

Regards,
{{ recruiter_name }}
{{ sender_email }}""",
        {
            'variables': [
                'candidate_first_name', 'job_title', 'company_name',
                'offer_title', 'offer_salary', 'offer_joining_date',
                'offer_expiry_date', 'recruiter_name', 'sender_email',
            ]
        },
    ),
    (
        'rejection_polite',
        'Update on your application for {{ job_title }}',
        """Hello {{ candidate_first_name }},

Thank you for your interest in {{ company_name }} and for taking the time to engage with our team regarding the {{ job_title }} position.

After careful review, we will not be moving forward with your application for this role at this time.

We truly appreciate your effort and wish you every success in your search.

Regards,
{{ recruiter_name }}
{{ sender_email }}""",
        {
            'variables': [
                'candidate_first_name', 'job_title', 'company_name',
                'recruiter_name', 'sender_email',
            ]
        },
    ),
    (
        'candidate_followup',
        'Following up on your application for {{ job_title }}',
        """Hello {{ candidate_first_name }},

I wanted to follow up regarding your application for {{ job_title }} at {{ company_name }}.

Please let us know if you have any updates, questions, or changes to your availability.

Regards,
{{ recruiter_name }}
{{ sender_email }}""",
        {
            'variables': [
                'candidate_first_name', 'job_title', 'company_name',
                'recruiter_name', 'sender_email',
            ]
        },
    ),
    (
        'document_collection_request',
        'Document request for {{ job_title }} process',
        """Hello {{ candidate_first_name }},

To proceed further for the {{ job_title }} opportunity at {{ company_name }}, we would like to request the following documents from you.

Please reply to this email with the required documents at your earliest convenience.

Regards,
{{ recruiter_name }}
{{ sender_email }}""",
        {
            'variables': [
                'candidate_first_name', 'job_title', 'company_name',
                'recruiter_name', 'sender_email',
            ]
        },
    ),
]


@transaction.atomic
def apply_core_template_bodies():
    """
    Upsert body content into existing EmailTemplateDefinition rows.
    Matches by slug. Safe to run multiple times — only updates body fields.
    Does NOT create new rows; the seeder in services.py handles creation.
    """
    from apps.communications.models import EmailTemplateDefinition

    updated = []
    for slug, subject, body_text, variables_schema in CORE_TEMPLATE_BODIES:
        body_html = '<br>'.join(body_text.replace('\n\n', '\n<br>\n').splitlines())
        rows = EmailTemplateDefinition.objects.filter(slug=slug)
        if rows.exists():
            rows.update(
                subject_template=subject,
                body_text=body_text,
                body_html=body_html,
                variables_schema_json=variables_schema,
            )
            updated.append(slug)
    return updated
