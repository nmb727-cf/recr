from django.core.management.base import BaseCommand

from apps.module_registry.models import ModuleRegistry, ModuleStatus


BASE_MODULES = [
    ('auth', 'Authentication', 'core_platform', 1),
    ('rbac', 'RBAC', 'core_platform', 2),
    ('tenant_architecture', 'Tenant Architecture', 'core_platform', 3),
    ('organisation_architecture', 'Organisation / Company / Agency Architecture', 'core_platform', 4),
    ('candidate_global_architecture', 'Candidate Global Architecture', 'core_platform', 5),
    ('settings_controls', 'Settings / Controls', 'core_platform', 6),
    ('jobs', 'Jobs', 'ats_core', 10),
    ('job_pipeline', 'Job Pipeline', 'ats_core', 11),
    ('workflow_system', 'Workflow System', 'ats_core', 12),
    ('candidate_database', 'Candidate Database', 'ats_core', 13),
    ('active_lead_general_pool_logic', 'Active / Lead / General Pool Logic', 'ats_core', 14),
    ('agency_company_relation', 'Agency-Company Relation', 'ats_core', 15),
    ('submissions', 'Submissions', 'ats_core', 16),
    ('recruiter_operations', 'Recruiter Operations', 'ats_core', 17),
    ('email', 'Email', 'communication', 20),
    ('templates', 'Templates', 'communication', 21),
    ('notifications', 'Notifications', 'communication', 22),
    ('communication_history', 'Communication History', 'communication', 23),
    ('interview_command_center', 'Interview Command Center', 'interview_system', 30),
    ('execution_engines', 'Execution Engines', 'interview_system', 31),
    ('flow_engine', 'Flow Engine', 'interview_system', 32),
    ('scorecards', 'Scorecards', 'interview_system', 33),
    ('scheduling', 'Scheduling', 'interview_system', 34),
    ('interview_candidate_experience', 'Interview Candidate Experience', 'interview_system', 35),
    ('interview_recruiter_productivity', 'Interview Recruiter Productivity', 'interview_system', 36),
    ('decision_engine', 'Decision Engine', 'hiring_decision', 40),
    ('committee_engine', 'Committee Engine', 'hiring_decision', 41),
    ('comparison_engine', 'Comparison Engine', 'hiring_decision', 42),
    ('approval_engine', 'Approval Engine', 'hiring_decision', 43),
    ('offer_intelligence', 'Offer Intelligence', 'hiring_decision', 44),
    ('compensation', 'Compensation', 'hiring_decision', 45),
    ('negotiation', 'Negotiation', 'hiring_decision', 46),
    ('offer_release', 'Offer Release', 'hiring_decision', 47),
    ('offer_acceptance', 'Offer Acceptance', 'hiring_decision', 48),
    ('joining_tracking', 'Joining Tracking', 'hiring_decision', 49),
    ('automation', 'Automation', 'cross_system', 60),
    ('analytics', 'Analytics', 'cross_system', 61),
    ('governance', 'Governance', 'cross_system', 62),
    ('audit', 'Audit', 'cross_system', 63),
    ('integration', 'Integration', 'cross_system', 64),
]


class Command(BaseCommand):
    help = 'Seed baseline Talent Operating System modules into the core module registry.'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', dest='tenant_id', help='Optional tenant UUID for tenant-scoped registry rows.')

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        created_count = 0
        for module_key, module_name, module_domain, implementation_order in BASE_MODULES:
            module, created = ModuleRegistry.objects.get_or_create(
                module_key=module_key,
                defaults={
                    'tenant_id': tenant_id,
                    'module_name': module_name,
                    'module_domain': module_domain,
                    'implementation_order': implementation_order,
                    'created_by': None,
                },
            )
            if created:
                created_count += 1
            ModuleStatus.objects.get_or_create(
                module=module,
                defaults={
                    'tenant_id': tenant_id,
                    'created_by': None,
                    'status': module.status,
                    'architecture_status': module.architecture_status,
                    'backend_status': module.backend_status,
                    'frontend_status': module.frontend_status,
                    'integration_status': module.integration_status,
                    'qa_status': module.qa_status,
                    'dependency_status': module.dependency_status,
                    'blocker_status': module.blocker_status,
                },
            )

        self.stdout.write(self.style.SUCCESS(f'Seeded/verified {len(BASE_MODULES)} module registry entries. Created: {created_count}.'))

