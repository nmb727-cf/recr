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

class ApplicationEvents:
    created = Signal()
    stage_changed = Signal()
    interviewed = Signal()
    offer_made = Signal()
    hired = Signal()
    shortlisted = Signal()


class OnboardingEvents:
    completed = Signal()

class TalentPoolEvents:
    created = Signal()
    updated = Signal()
    archived = Signal()

class CandidateEvents:
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


class InterviewEvents:
    scheduled          = Signal()  # kwargs: interview
    started            = Signal()  # kwargs: interview
    completed          = Signal()  # kwargs: interview
    cancelled          = Signal()  # kwargs: interview
    feedback_submitted = Signal()  # kwargs: interview, feedback
    decision_recorded  = Signal()  # kwargs: interview, decision, created


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
