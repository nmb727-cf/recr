import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.accounts.models import CustomUser
from apps.agencies.views import AgencyLookupView
from apps.analytics.views import DashboardView
from apps.automation.views import AutonomousHiringView, GlobalOrchestratorDashboardView
from apps.candidates.views import CandidateListView
from apps.communications.notification_orchestration_views import NotificationAutomationJobListView
from apps.interviews.views import InterviewListView
from apps.jobs.views import JobRequisitionListView
from apps.pipeline.views import ApplicationListView
from apps.core.tests.access_matrix import AccessCase, AccessMatrixMixin


class ActorAccessMatrixTests(AccessMatrixMixin, TestCase):
    """
    Soft matrix coverage:
    - Deny checks are strict (security invariants).
    - Allow checks are opt-in per endpoint to avoid rigid coupling while modules evolve.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.users = {
            "candidate": self._mk_user("matrix-candidate@example.com", "candidate"),
            "recruiter": self._mk_user("matrix-recruiter@example.com", "recruiter"),
            "hr_manager": self._mk_user("matrix-hr@example.com", "hr_manager"),
            "tenant_admin": self._mk_user("matrix-tenant-admin@example.com", "tenant_admin"),
        }
        # Platform admin role exists in policy helpers; keep as non-staff user to test role checks.
        self.users["super_admin"] = self._mk_user("matrix-super-admin@example.com", "super_admin")

    def _mk_user(self, email: str, role: str) -> CustomUser:
        return CustomUser.objects.create_user(
            email=email,
            password="testpass123",
            role=role,
            tenant_id=self.tenant_id,
        )

    def test_actor_access_matrix_soft_guards(self):
        cases = [
            AccessCase(
                name="jobs_requisition_list",
                method="get",
                path="/api/v1/jobs/requisitions/",
                view=JobRequisitionListView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="pipeline_applications_list",
                method="get",
                path="/api/v1/pipeline/applications/",
                view=ApplicationListView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="candidates_list",
                method="get",
                path="/api/v1/candidates/",
                view=CandidateListView.as_view(),
                deny_roles={"candidate"},
            ),
            AccessCase(
                name="interviews_list",
                method="get",
                path="/api/v1/interviews/",
                view=InterviewListView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="analytics_dashboard",
                method="get",
                path="/api/v1/analytics/dashboard/",
                view=DashboardView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="notification_orchestration_admin_jobs",
                method="get",
                path="/api/v1/communications/notification-control/jobs/",
                view=NotificationAutomationJobListView.as_view(),
                deny_roles={"candidate", "recruiter", "hr_manager"},
                allow_roles={"tenant_admin", "super_admin"},
            ),
            AccessCase(
                name="automation_autonomous_dashboard",
                method="get",
                path="/api/v1/automation/autonomous/",
                view=AutonomousHiringView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="automation_orchestrator_dashboard",
                method="get",
                path="/api/v1/automation/orchestrator/",
                view=GlobalOrchestratorDashboardView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="agency_lookup",
                method="get",
                path="/api/v1/agencies/lookup/?q=nomatch@example.com",
                view=AgencyLookupView.as_view(),
                deny_roles={"candidate"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
        ]

        self.assert_matrix(cases)
