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

class AgencyEvents:
    candidate_submitted = Signal()

class ApplicationEvents:
    created = Signal()
    stage_changed = Signal()
    interviewed = Signal()
    offer_made = Signal()
    hired = Signal()
    shortlisted = Signal()

# Instantiate for dot notation usage: events.application.created
company = CompanyEvents()
job = JobEvents()
agency = AgencyEvents()
application = ApplicationEvents()

# Legacy / Compatibility (if needed, but user said REPLACE)
# Keeping these commented for now or just removing them if I'm sure I'll update all refs
