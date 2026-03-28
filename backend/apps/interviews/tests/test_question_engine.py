from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import CustomUser
from apps.interviews.models import (
    InterviewQuestionBank,
    InterviewQuestionAttachment,
    InterviewQuestionGroup,
    InterviewTemplate,
    InterviewQuestion,
)
from apps.interviews.views import (
    InterviewQuestionBankListView,
    InterviewQuestionAttachmentListView,
    InterviewQuestionGroupListView,
    InterviewManualSchedulingView,
)


class InterviewQuestionEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            email='question-admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id='00000000-0000-0000-0000-000000000001',
        )
        self.permission_patch = patch('apps.rbac.permissions.user_has_all_permissions', return_value=True)
        self.permission_patch.start()
        self.addCleanup(self.permission_patch.stop)
        self.template = InterviewTemplate.objects.create(
            tenant_id=self.user.tenant_id,
            name='Question Template',
            interview_type='technical_interview',
            created_by=self.user.id,
            questions=[],
        )

    def test_question_create_works(self):
        req = self.factory.post(
            '/api/v1/interviews/questions/bank/',
            {
                'scope': 'tenant',
                'question_title': 'Explain polymorphism',
                'description': 'Core OOP concept',
                'question_type': 'text',
                'difficulty': 'medium',
                'tags': ['oop'],
                'skills': ['python'],
                'scoring_weight': 2,
            },
            format='json',
        )
        force_authenticate(req, user=self.user)
        res = InterviewQuestionBankListView.as_view()(req)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(InterviewQuestionBank.objects.filter(tenant_id=self.user.tenant_id, is_deleted=False).count(), 1)

    def test_question_attach_works(self):
        q = InterviewQuestionBank.objects.create(
            tenant_id=self.user.tenant_id,
            scope='tenant',
            question_title='What is a transaction?',
            question_type='text',
            difficulty='easy',
            scoring_weight=1,
            created_by=self.user.id,
        )
        attach_req = self.factory.post(
            '/api/v1/interviews/questions/attachments/',
            {
                'question_id': str(q.id),
                'attach_type': 'template',
                'template_id': str(self.template.id),
                'order_index': 0,
            },
            format='json',
        )
        force_authenticate(attach_req, user=self.user)
        attach_res = InterviewQuestionAttachmentListView.as_view()(attach_req)
        self.assertEqual(attach_res.status_code, 201, attach_res.data)
        self.assertTrue(InterviewQuestionAttachment.objects.filter(tenant_id=self.user.tenant_id, question=q).exists())
        self.template.refresh_from_db()
        self.assertGreaterEqual(len(self.template.questions or []), 1)

    def test_grouping_works(self):
        q = InterviewQuestionBank.objects.create(
            tenant_id=self.user.tenant_id,
            scope='tenant',
            question_title='Rate communication',
            question_type='rating',
            difficulty='medium',
            scoring_weight=1,
            created_by=self.user.id,
        )
        req = self.factory.post(
            '/api/v1/interviews/questions/groups/',
            {
                'scope': 'tenant',
                'name': 'Behavioral Section',
                'section_name': 'Culture',
                'target_type': 'interview_type',
                'target_ref': 'behavioral',
                'order_index': 0,
                'items': [{'question_id': str(q.id), 'order_index': 0, 'required': True}],
            },
            format='json',
        )
        force_authenticate(req, user=self.user)
        res = InterviewQuestionGroupListView.as_view()(req)
        self.assertEqual(res.status_code, 201)
        grp = InterviewQuestionGroup.objects.filter(tenant_id=self.user.tenant_id, name='Behavioral Section').first()
        self.assertIsNotNone(grp)
        self.assertEqual(grp.items.count(), 1)

    def test_interview_type_attachment_seeds_runtime_questions(self):
        q = InterviewQuestionBank.objects.create(
            tenant_id=self.user.tenant_id,
            scope='tenant',
            question_title='Design an API for inventory',
            question_type='text',
            difficulty='hard',
            scoring_weight=3,
            created_by=self.user.id,
        )
        InterviewQuestionAttachment.objects.create(
            tenant_id=self.user.tenant_id,
            question=q,
            attach_type='interview_type',
            interview_type='system_design',
            order_index=0,
            created_by=self.user.id,
        )
        sched_req = self.factory.post(
            '/api/v1/interviews/scheduling/manual/',
            {
                'application_id': '00000000-0000-0000-0000-000000001111',
                'candidate_id': '00000000-0000-0000-0000-000000001222',
                'requisition_id': '00000000-0000-0000-0000-000000001333',
                'interview_type': 'system_design',
                'scheduled_at': '2026-04-02T10:00:00Z',
            },
            format='json',
        )
        force_authenticate(sched_req, user=self.user)
        sched_res = InterviewManualSchedulingView.as_view()(sched_req)
        self.assertEqual(sched_res.status_code, 201)
        interview_id = sched_res.data['data']['interview']['id']
        self.assertGreaterEqual(InterviewQuestion.objects.filter(interview_id=interview_id).count(), 1)
