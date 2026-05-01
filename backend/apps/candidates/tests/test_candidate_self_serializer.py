import uuid
from unittest.mock import patch

from django.test import TestCase

from apps.candidates.models import Candidate
from apps.candidates.serializers import CandidateSelfSerializer


class CandidateSelfSerializerTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Self',
            last_name='Profile',
            email='self.profile@example.com',
            profile_completeness=70,
            is_actively_looking=False,
            skills=[],
        )

    @patch('apps.candidates.services.CandidateIntelligenceService.get_intelligence_profile')
    def test_engagement_intelligence_reads_nested_labels_schema(self, mock_get_intel):
        mock_get_intel.return_value = {
            'labels': {
                'availability': 'Engaged',
                'seniority': 'Senior',
            }
        }
        data = CandidateSelfSerializer(self.candidate).data
        intelligence = data['engagement_intelligence']
        self.assertEqual(intelligence['availability_label'], 'Engaged')
        self.assertEqual(intelligence['seniority_label'], 'Senior')

    @patch('apps.candidates.services.CandidateIntelligenceService.get_intelligence_profile')
    def test_engagement_intelligence_falls_back_to_legacy_shape(self, mock_get_intel):
        mock_get_intel.return_value = {
            'availability': 'Active',
            'seniority': 'Mid-Level',
        }
        data = CandidateSelfSerializer(self.candidate).data
        intelligence = data['engagement_intelligence']
        self.assertEqual(intelligence['availability_label'], 'Active')
        self.assertEqual(intelligence['seniority_label'], 'Mid-Level')
