from django.core.management.base import BaseCommand
from apps.orchestration_center.models.event_trigger import WorkflowEventDefinition

class Command(BaseCommand):
    help = 'Seeds the Workflow Event Registry with standard system events.'

    def handle(self, *args, **options):
        events = [
            # Candidate Events
            {'key': 'candidate_created', 'name': 'Candidate Created', 'module': 'candidates'},
            {'key': 'candidate_updated', 'name': 'Candidate Updated', 'module': 'candidates'},
            {'key': 'candidate_tag_added', 'name': 'Candidate Tag Added', 'module': 'candidates'},
            {'key': 'candidate_score_updated', 'name': 'Candidate Score Updated', 'module': 'candidates'},
            {'key': 'candidate_source_changed', 'name': 'Candidate Source Changed', 'module': 'candidates'},
            {'key': 'candidate_idle', 'name': 'Candidate Idle', 'module': 'candidates'},
            
            # Job Events
            {'key': 'job_created', 'name': 'Job Created', 'module': 'jobs'},
            {'key': 'job_updated', 'name': 'Job Updated', 'module': 'jobs'},
            {'key': 'job_published', 'name': 'Job Published', 'module': 'jobs'},
            {'key': 'job_closed', 'name': 'Job Closed', 'module': 'jobs'},
            {'key': 'job_approved', 'name': 'Job Approved', 'module': 'jobs'},
            
            # Pipeline Events
            {'key': 'application_created', 'name': 'Application Created', 'module': 'pipeline'},
            {'key': 'candidate_added', 'name': 'Candidate Added', 'module': 'pipeline'},
            {'key': 'stage_entered', 'name': 'Stage Entered', 'module': 'pipeline'},
            {'key': 'stage_changed', 'name': 'Stage Changed', 'module': 'pipeline'},
            {'key': 'stage_idle', 'name': 'Stage Idle', 'module': 'pipeline'},
            {'key': 'candidate_shortlisted', 'name': 'Candidate Shortlisted', 'module': 'pipeline'},
            {'key': 'candidate_rejected', 'name': 'Candidate Rejected', 'module': 'pipeline'},
            
            # Agency Events
            {'key': 'agency_submission_received', 'name': 'Agency Submission Received', 'module': 'agencies'},
            {'key': 'agency_submission_reviewed', 'name': 'Agency Submission Reviewed', 'module': 'agencies'},
            {'key': 'agency_no_response', 'name': 'Agency No Response', 'module': 'agencies'},
            {'key': 'agency_sla_breached', 'name': 'Agency SLA Breached', 'module': 'agencies'},
            
            # Interview Events
            {'key': 'interview_created', 'name': 'Interview Created', 'module': 'interviews'},
            {'key': 'interview_scheduled', 'name': 'Interview Scheduled', 'module': 'interviews'},
            {'key': 'interview_rescheduled', 'name': 'Interview Rescheduled', 'module': 'interviews'},
            {'key': 'interview_completed', 'name': 'Interview Completed', 'module': 'interviews'},
            {'key': 'interview_feedback_submitted', 'name': 'Interview Feedback Submitted', 'module': 'interviews'},
            {'key': 'interview_no_show', 'name': 'Interview No Show', 'module': 'interviews'},
            
            # Offer Events
            {'key': 'offer_created', 'name': 'Offer Created', 'module': 'offers'},
            {'key': 'offer_approved', 'name': 'Offer Approved', 'module': 'offers'},
            {'key': 'offer_sent', 'name': 'Offer Sent', 'module': 'offers'},
            {'key': 'offer_viewed', 'name': 'Offer Viewed', 'module': 'offers'},
            {'key': 'offer_negotiation_started', 'name': 'Offer Negotiation Started', 'module': 'offers'},
            {'key': 'offer_countered', 'name': 'Offer Countered', 'module': 'offers'},
            {'key': 'offer_accepted', 'name': 'Offer Accepted', 'module': 'offers'},
            {'key': 'offer_rejected', 'name': 'Offer Rejected', 'module': 'offers'},
            
            # Task Events
            {'key': 'task_created', 'name': 'Task Created', 'module': 'tasks'},
            {'key': 'task_completed', 'name': 'Task Completed', 'module': 'tasks'},
            {'key': 'task_overdue', 'name': 'Task Overdue', 'module': 'tasks'},
            
            # SLA Events
            {'key': 'sla_created', 'name': 'SLA Created', 'module': 'SLA'},
            {'key': 'sla_warning_due', 'name': 'SLA Warning Due', 'module': 'SLA'},
            {'key': 'sla_breached', 'name': 'SLA Breached', 'module': 'SLA'},
            {'key': 'sla_completed', 'name': 'SLA Completed', 'module': 'SLA'},
            
            # Communication Events
            {'key': 'email_sent', 'name': 'Email Sent', 'module': 'communications'},
            {'key': 'whatsapp_sent', 'name': 'WhatsApp Sent', 'module': 'communications'},
            {'key': 'notification_failed', 'name': 'Notification Failed', 'module': 'communications'},
            {'key': 'candidate_replied', 'name': 'Candidate Replied', 'module': 'communications'},
            
            # Document Events
            {'key': 'document_generated', 'name': 'Document Generated', 'module': 'documents'},
            {'key': 'offer_letter_generated', 'name': 'Offer Letter Generated', 'module': 'documents'},
            {'key': 'document_signed', 'name': 'Document Signed', 'module': 'documents'},
            
            # Onboarding Events
            {'key': 'onboarding_started', 'name': 'Onboarding Started', 'module': 'onboarding'},
            {'key': 'onboarding_completed', 'name': 'Onboarding Completed', 'module': 'onboarding'},
            {'key': 'hrms_handoff_ready', 'name': 'HRMS Handoff Ready', 'module': 'onboarding'},
            
            # Integration Events
            {'key': 'webhook_received', 'name': 'Webhook Received', 'module': 'integrations'},
            {'key': 'integration_sync_completed', 'name': 'Integration Sync Completed', 'module': 'integrations'},
        ]

        count = 0
        for e in events:
            obj, created = WorkflowEventDefinition.objects.get_or_create(
                event_key=e['key'],
                defaults={
                    'event_name': e['name'],
                    'module_scope': e['module']
                }
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} new event definitions.'))
