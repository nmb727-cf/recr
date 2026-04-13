from django.dispatch import Signal

class AuthEvents:
    company_created = Signal()  # application.company_created -> company.created?
    # Standardizing to prompt's dot notation via class attributes
    
class CompanyEvents:
    created = Signal()

class JobEvents:
    created = Signal()
    approved = Signal()
    published = Signal()
    guarantee_watch_started = Signal()
    fully_closed = Signal()

class AgencyEvents:
    candidate_submitted = Signal()
    recruiter_assigned = Signal()
    submission_governance_updated = Signal()
    relationship_reactivated = Signal()

class ApplicationEvents:
    created = Signal()
    stage_changed = Signal()
    interviewed = Signal()
    offer_made = Signal()
    hired = Signal()
    shortlisted = Signal()
    rejected = Signal()


class OfferEvents:
    created          = Signal()  # kwargs: offer
    approved         = Signal()  # kwargs: offer
    sent             = Signal()  # kwargs: application, candidate_user_id
    accepted         = Signal()  # kwargs: application, recruiter_user_id, hiring_manager_user_id
    rejected         = Signal()  # kwargs: application, recruiter_user_id
    expired          = Signal()  # kwargs: application, recruiter_user_id
    response_pending = Signal()  # kwargs: application, candidate_user_id, tenant_id


class PassportEvents:
    viewed = Signal()
    shared = Signal()


class DeadlineEvents:
    reminder_due = Signal()
    overdue = Signal()


class OnboardingEvents:
    started = Signal()  # kwargs: application
    completed = Signal()

class TalentPoolEvents:
    created = Signal()
    updated = Signal()
    archived = Signal()

class CandidateEvents:
    created = Signal()
    linked_to_user = Signal()
    associated_with_tenant = Signal()
    deduplicated = Signal()
    added_to_pool = Signal()
    removed_from_pool = Signal()
    protection_started = Signal()
    protection_expired = Signal()
    rights_changed = Signal()
    protected_action_blocked = Signal()


class PlacementEvents:
    guarantee_started = Signal()
    guarantee_expired = Signal()
    guarantee_breached = Signal()


class MessageEvents:
    created          = Signal()  # kwargs: message, thread, sender_user_id, recipient_user_ids
    external_created = Signal()  # kwargs: message, thread, sender_user_id, recipient_user_ids
    high_priority    = Signal()  # kwargs: message, thread, sender_user_id, recipient_user_ids
    thread_read      = Signal()  # kwargs: thread, user_id — cancels pending fallback for thread


class ApprovalEvents:
    requested = Signal()  # kwargs: entity_type, entity_id, approver_user_id, tenant_id
    overdue   = Signal()  # kwargs: entity_type, entity_id, approver_user_id, tenant_id


class InterviewEvents:
    scheduled          = Signal()  # kwargs: interview
    rescheduled        = Signal()  # kwargs: interview, candidate_user_id, interviewer_user_ids
    started            = Signal()  # kwargs: interview
    completed          = Signal()  # kwargs: interview
    cancelled          = Signal()  # kwargs: interview
    feedback_submitted = Signal()  # kwargs: interview, feedback
    decision_recorded  = Signal()  # kwargs: interview, decision, created
    feedback_pending   = Signal()  # kwargs: interview, panelist_user_ids, tenant_id


class IntelligenceEvents:
    snapshot_updated = Signal()  # kwargs: tenant_id, event_name, entity_type, entity_id


# Instantiate for dot notation usage: events.interview.scheduled
company = CompanyEvents()
job = JobEvents()
agency = AgencyEvents()
application = ApplicationEvents()
onboarding = OnboardingEvents()
talent_pool = TalentPoolEvents()
candidate = CandidateEvents()
placement = PlacementEvents()
interview = InterviewEvents()
offer = OfferEvents()
passport = PassportEvents()
deadline = DeadlineEvents()
message = MessageEvents()
approval = ApprovalEvents()
intelligence = IntelligenceEvents()
