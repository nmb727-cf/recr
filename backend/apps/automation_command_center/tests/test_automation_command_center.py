import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orchestration_center.models.workflow import Workflow, WorkflowExecution
from apps.orchestration_center.models.suggestion import AISuggestion
from apps.orchestration_center.constants.execution_statuses import SuggestionStatus


def _make_user(role='tenant_admin', tenant_id=None):
    """Return a simple mock user object."""

    class MockUser:
        is_authenticated = True
        id = uuid.uuid4()
        pass

    u = MockUser()
    u.role = role
    u.tenant_id = tenant_id or uuid.uuid4()
    return u


class OverviewViewTest(TestCase):
    """Test 1 — Active workflows exist → shown in command center overview."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.user = _make_user(tenant_id=self.tenant_id)
        self.client.force_authenticate(user=self.user)

    def test_active_workflows_shown_in_overview(self):
        Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Candidate Follow-up',
            trigger_event='candidate_applied',
            status='active',
            is_active=True,
        )
        Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Interview Reminder',
            trigger_event='interview_scheduled',
            status='active',
            is_active=True,
        )
        resp = self.client.get('/api/v1/automation-center/overview/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertEqual(data['active_workflows'], 2)

    def test_executions_today_and_success_rate(self):
        wf = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Offer Reminder',
            trigger_event='offer_sent',
            status='active',
            is_active=True,
        )
        today = timezone.now()
        for _ in range(8):
            WorkflowExecution.objects.create(
                tenant_id=self.tenant_id,
                workflow=wf,
                entity_type='candidate',
                entity_id=str(uuid.uuid4()),
                status='completed',
                started_at=today,
            )
        for _ in range(2):
            WorkflowExecution.objects.create(
                tenant_id=self.tenant_id,
                workflow=wf,
                entity_type='candidate',
                entity_id=str(uuid.uuid4()),
                status='failed',
                started_at=today,
            )

        resp = self.client.get('/api/v1/automation-center/overview/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertEqual(data['executions_today'], 10)
        self.assertEqual(data['success_rate'], 80.0)
        self.assertEqual(data['failures_today'], 2)


class HealthViewTest(TestCase):
    """Test 2 — Workflow fails → health alert shown."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.user = _make_user(tenant_id=self.tenant_id)
        self.client.force_authenticate(user=self.user)

    def test_failing_workflow_appears_in_health(self):
        wf = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='SLA Escalation',
            trigger_event='sla_breached',
            status='active',
            is_active=True,
        )
        WorkflowExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow=wf,
            entity_type='job',
            entity_id=str(uuid.uuid4()),
            status='failed',
            started_at=timezone.now(),
        )

        resp = self.client.get('/api/v1/automation-center/health/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertGreaterEqual(data['failing_workflows'], 1)

    def test_paused_workflow_in_health(self):
        Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Paused WF',
            trigger_event='candidate_applied',
            status='paused',
            is_active=False,
        )
        resp = self.client.get('/api/v1/automation-center/health/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertGreaterEqual(data['paused_workflows'], 1)


class AISuggestionsViewTest(TestCase):
    """Test 3 — AI suggestion generated → visible in suggestions."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.user = _make_user(tenant_id=self.tenant_id)
        self.client.force_authenticate(user=self.user)

    def test_pending_suggestion_visible(self):
        AISuggestion.objects.create(
            tenant_id=self.tenant_id,
            suggestion_key='stuck_in_screening',
            category='automation',
            status=SuggestionStatus.PENDING,
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(uuid.uuid4()),
            title='Candidates stuck in screening stage',
            summary='7 candidates have been in screening for more than 5 days without action.',
        )
        resp = self.client.get('/api/v1/automation-center/ai-suggestions/')
        self.assertEqual(resp.status_code, 200)
        results = resp.json()['data']
        self.assertGreaterEqual(len(results), 1)
        titles = [r['title'] for r in results]
        self.assertIn('Candidates stuck in screening stage', titles)


class PauseAllResumeAllTest(TestCase):
    """Test 4 — Pause all automation → all workflows paused."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.admin_user = _make_user(role='tenant_admin', tenant_id=self.tenant_id)
        self.recruiter_user = _make_user(role='recruiter', tenant_id=self.tenant_id)

    def _create_active_workflows(self, count=3):
        for i in range(count):
            Workflow.objects.create(
                tenant_id=self.tenant_id,
                name=f'Workflow {i}',
                trigger_event='candidate_applied',
                status='active',
                is_active=True,
            )

    def test_pause_all_sets_all_active_to_paused(self):
        self._create_active_workflows(3)
        self.client.force_authenticate(user=self.admin_user)

        resp = self.client.post('/api/v1/automation-center/pause-all/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertEqual(data['paused_count'], 3)

        still_active = Workflow.objects.filter(tenant_id=self.tenant_id, status='active').count()
        self.assertEqual(still_active, 0)

    def test_resume_all_sets_paused_to_active(self):
        self._create_active_workflows(3)
        Workflow.objects.filter(tenant_id=self.tenant_id).update(status='paused')
        self.client.force_authenticate(user=self.admin_user)

        resp = self.client.post('/api/v1/automation-center/resume-all/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertEqual(data['resumed_count'], 3)

        paused = Workflow.objects.filter(tenant_id=self.tenant_id, status='paused').count()
        self.assertEqual(paused, 0)

    def test_recruiter_cannot_pause_all(self):
        self._create_active_workflows(1)
        self.client.force_authenticate(user=self.recruiter_user)

        resp = self.client.post('/api/v1/automation-center/pause-all/')
        self.assertEqual(resp.status_code, 403)

    def test_recruiter_cannot_emergency_stop(self):
        self.client.force_authenticate(user=self.recruiter_user)
        resp = self.client.post('/api/v1/automation-center/emergency-stop/')
        self.assertEqual(resp.status_code, 403)


class EmergencyStopTest(TestCase):
    """Test 5 — Emergency stop deactivates all workflows and stops running executions."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.admin_user = _make_user(role='tenant_admin', tenant_id=self.tenant_id)
        self.client.force_authenticate(user=self.admin_user)

    def test_emergency_stop_deactivates_and_stops(self):
        wf = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Critical WF',
            trigger_event='offer_expired',
            status='active',
            is_active=True,
        )
        WorkflowExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow=wf,
            entity_type='offer',
            entity_id=str(uuid.uuid4()),
            status='running',
        )

        resp = self.client.post('/api/v1/automation-center/emergency-stop/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertGreaterEqual(data['deactivated_workflows'], 1)
        self.assertGreaterEqual(data['stopped_executions'], 1)

        wf.refresh_from_db()
        self.assertEqual(wf.status, 'archived')
        self.assertFalse(wf.is_active)


class WorkflowListViewTest(TestCase):
    """Test 6 — Workflow list with search and filter."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.user = _make_user(tenant_id=self.tenant_id)
        self.client.force_authenticate(user=self.user)

    def test_workflows_listed(self):
        Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Auto Assign Recruiter',
            trigger_event='job_posted',
            status='active',
            is_active=True,
        )
        resp = self.client.get('/api/v1/automation-center/workflows/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertGreaterEqual(len(data), 1)
        names = [w['name'] for w in data]
        self.assertIn('Auto Assign Recruiter', names)

    def test_search_filters_results(self):
        Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Offer Reminder Flow',
            trigger_event='offer_sent',
            status='active',
            is_active=True,
        )
        Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Interview Reminder Flow',
            trigger_event='interview_scheduled',
            status='active',
            is_active=True,
        )
        resp = self.client.get('/api/v1/automation-center/workflows/?search=Offer')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Offer Reminder Flow')


class ActivityFeedTest(TestCase):
    """Test 7 — Activity feed shows recent automation events."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_id = uuid.uuid4()
        self.user = _make_user(tenant_id=self.tenant_id)
        self.client.force_authenticate(user=self.user)

    def test_activity_feed_returns_events(self):
        wf = Workflow.objects.create(
            tenant_id=self.tenant_id,
            name='Candidate Auto Move',
            trigger_event='candidate_stage_changed',
            status='active',
            is_active=True,
        )
        WorkflowExecution.objects.create(
            tenant_id=self.tenant_id,
            workflow=wf,
            entity_type='candidate',
            entity_id=str(uuid.uuid4()),
            status='completed',
        )
        resp = self.client.get('/api/v1/automation-center/activity/')
        self.assertEqual(resp.status_code, 200)
        events = resp.json()['data']
        self.assertGreaterEqual(len(events), 1)
        self.assertIn('workflow_name', events[0])
        self.assertIn('time', events[0])
