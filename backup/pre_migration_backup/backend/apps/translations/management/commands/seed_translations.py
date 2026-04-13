"""
Management command: seed_translations

Seeds baseline TranslationOverride records for global defaults.
These records demonstrate the DB-backed override pattern.
Safe to re-run — uses update_or_create throughout.

Usage:
    python manage.py seed_translations
"""
from django.core.management.base import BaseCommand
from apps.translations.models import TranslationOverride

# ---------------------------------------------------------------------------
# Baseline overrides — these mirror the static JSON files but live in the DB
# so they can be edited at runtime without a frontend deploy.
# ---------------------------------------------------------------------------

SEED_DATA = [
    # ── Sidebar — English ────────────────────────────────────────────────────
    {'key': 'sidebar.dashboard',        'language_code': 'en', 'module': 'sidebar', 'value': 'Dashboard'},
    {'key': 'sidebar.jobs',             'language_code': 'en', 'module': 'sidebar', 'value': 'Jobs'},
    {'key': 'sidebar.pipeline',         'language_code': 'en', 'module': 'sidebar', 'value': 'Pipeline'},
    {'key': 'sidebar.candidates',       'language_code': 'en', 'module': 'sidebar', 'value': 'Candidates'},
    {'key': 'sidebar.agencies',         'language_code': 'en', 'module': 'sidebar', 'value': 'Agencies'},
    {'key': 'sidebar.interviews',       'language_code': 'en', 'module': 'sidebar', 'value': 'Interviews'},
    {'key': 'sidebar.offers',           'language_code': 'en', 'module': 'sidebar', 'value': 'Offers'},
    {'key': 'sidebar.reports',          'language_code': 'en', 'module': 'sidebar', 'value': 'Reports'},
    {'key': 'sidebar.settings',         'language_code': 'en', 'module': 'sidebar', 'value': 'Settings'},
    {'key': 'sidebar.performance',      'language_code': 'en', 'module': 'sidebar', 'value': 'Performance'},
    {'key': 'sidebar.submissions',      'language_code': 'en', 'module': 'sidebar', 'value': 'Submissions'},
    {'key': 'sidebar.clients',          'language_code': 'en', 'module': 'sidebar', 'value': 'Clients'},

    # ── Sidebar — Hindi ──────────────────────────────────────────────────────
    {'key': 'sidebar.dashboard',        'language_code': 'hi', 'module': 'sidebar', 'value': 'डैशबोर्ड'},
    {'key': 'sidebar.jobs',             'language_code': 'hi', 'module': 'sidebar', 'value': 'नौकरियाँ'},
    {'key': 'sidebar.pipeline',         'language_code': 'hi', 'module': 'sidebar', 'value': 'पाइपलाइन'},
    {'key': 'sidebar.candidates',       'language_code': 'hi', 'module': 'sidebar', 'value': 'उम्मीदवार'},
    {'key': 'sidebar.agencies',         'language_code': 'hi', 'module': 'sidebar', 'value': 'एजेंसियाँ'},
    {'key': 'sidebar.interviews',       'language_code': 'hi', 'module': 'sidebar', 'value': 'साक्षात्कार'},
    {'key': 'sidebar.offers',           'language_code': 'hi', 'module': 'sidebar', 'value': 'ऑफर'},
    {'key': 'sidebar.reports',          'language_code': 'hi', 'module': 'sidebar', 'value': 'रिपोर्ट'},
    {'key': 'sidebar.settings',         'language_code': 'hi', 'module': 'sidebar', 'value': 'सेटिंग्स'},
    {'key': 'sidebar.performance',      'language_code': 'hi', 'module': 'sidebar', 'value': 'प्रदर्शन'},
    {'key': 'sidebar.submissions',      'language_code': 'hi', 'module': 'sidebar', 'value': 'सबमिशन'},
    {'key': 'sidebar.clients',          'language_code': 'hi', 'module': 'sidebar', 'value': 'क्लाइंट'},

    # ── Candidates module — English ──────────────────────────────────────────
    {'key': 'candidates.add_candidate', 'language_code': 'en', 'module': 'candidates', 'value': 'Add Candidate'},
    {'key': 'candidates.database',      'language_code': 'en', 'module': 'candidates', 'value': 'Database'},
    {'key': 'candidates.active',        'language_code': 'en', 'module': 'candidates', 'value': 'Active'},

    # ── Candidates module — Hindi ────────────────────────────────────────────
    {'key': 'candidates.add_candidate', 'language_code': 'hi', 'module': 'candidates', 'value': 'उम्मीदवार जोड़ें'},
    {'key': 'candidates.database',      'language_code': 'hi', 'module': 'candidates', 'value': 'डेटाबेस'},
    {'key': 'candidates.active',        'language_code': 'hi', 'module': 'candidates', 'value': 'सक्रिय'},

    # ── Common actions — English ─────────────────────────────────────────────
    {'key': 'actions.save',    'language_code': 'en', 'module': 'common', 'value': 'Save'},
    {'key': 'actions.cancel',  'language_code': 'en', 'module': 'common', 'value': 'Cancel'},
    {'key': 'actions.delete',  'language_code': 'en', 'module': 'common', 'value': 'Delete'},
    {'key': 'actions.edit',    'language_code': 'en', 'module': 'common', 'value': 'Edit'},
    {'key': 'actions.search',  'language_code': 'en', 'module': 'common', 'value': 'Search'},

    # ── Common actions — Hindi ───────────────────────────────────────────────
    {'key': 'actions.save',    'language_code': 'hi', 'module': 'common', 'value': 'सहेजें'},
    {'key': 'actions.cancel',  'language_code': 'hi', 'module': 'common', 'value': 'रद्द करें'},
    {'key': 'actions.delete',  'language_code': 'hi', 'module': 'common', 'value': 'हटाएं'},
    {'key': 'actions.edit',    'language_code': 'hi', 'module': 'common', 'value': 'संपादित करें'},
    {'key': 'actions.search',  'language_code': 'hi', 'module': 'common', 'value': 'खोजें'},
]


class Command(BaseCommand):
    help = 'Seed baseline TranslationOverride records for global defaults'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n─── Translation Seed ───\n'))

        created = updated = 0
        for entry in SEED_DATA:
            _, was_created = TranslationOverride.objects.update_or_create(
                key=entry['key'],
                language_code=entry['language_code'],
                tenant_id=None,  # global
                defaults={
                    'value': entry['value'],
                    'module': entry['module'],
                    'is_active': True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Done. {created} created, {updated} updated ({len(SEED_DATA)} total)\n'
        ))
