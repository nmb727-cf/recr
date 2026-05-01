import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.accounts.models import CustomUser
from apps.agencies.views import AgencyMyJobsView
from apps.analytics.views import DashboardView
from apps.core.tests.access_matrix import AccessCase, AccessMatrixMixin
from apps.jobs.views import CandidateApplicationListView, JobRequisitionListView


class UiApiAccessContractTests(AccessMatrixMixin, TestCase):
    """
    UI <-> API access contract (soft):
    - Enforce cross-role deny boundaries to prevent menu/API drift.
    - Keep allow assertions only where stable.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        self.users = {
            "candidate": self._mk_user("contract-candidate@example.com", "candidate"),
            "recruiter": self._mk_user("contract-recruiter@example.com", "recruiter"),
            "tenant_admin": self._mk_user("contract-tenant-admin@example.com", "tenant_admin"),
            "agency_recruiter": self._mk_user("contract-agency@example.com", "agency_recruiter"),
        }

    def _mk_user(self, email: str, role: str) -> CustomUser:
        return CustomUser.objects.create_user(
            email=email,
            password="testpass123",
            role=role,
            tenant_id=self.tenant_id,
        )

    def test_role_journeys_match_backend_contract(self):
        cases = [
            AccessCase(
                name="company_jobs_menu_to_api",
                method="get",
                path="/api/v1/jobs/requisitions/",
                view=JobRequisitionListView.as_view(),
                deny_roles={"candidate", "agency_recruiter"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="company_dashboard_menu_to_api",
                method="get",
                path="/api/v1/analytics/dashboard/",
                view=DashboardView.as_view(),
                deny_roles={"candidate", "agency_recruiter"},
                allow_roles={"recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="agency_jobs_menu_to_api",
                method="get",
                path="/api/v1/agencies/my-jobs/",
                view=AgencyMyJobsView.as_view(),
                deny_roles={"candidate", "recruiter"},
                allow_roles={"agency_recruiter", "tenant_admin"},
            ),
            AccessCase(
                name="candidate_applications_menu_to_api",
                method="get",
                path="/api/v1/candidate/applications/",
                view=CandidateApplicationListView.as_view(),
                deny_roles={"recruiter", "tenant_admin", "agency_recruiter"},
                allow_roles={"candidate"},
            ),
        ]

        self.assert_matrix(cases)

