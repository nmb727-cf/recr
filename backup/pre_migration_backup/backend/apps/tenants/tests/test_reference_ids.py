from datetime import datetime, timezone as dt_timezone

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.candidates.models import Candidate
from apps.candidates.serializers import CandidateSerializer
from apps.jobs.models import JobRequisition
from apps.jobs.serializers import JobRequisitionSerializer
from apps.tenants.models import Client
from apps.tenants.reference_ids import build_reference, ensure_tenant_prefix


class ReferenceIdGenerationTests(TestCase):
    def setUp(self):
        self.public_tenant = Client.objects.create(
            schema_name='public',
            name='Public',
            slug='public',
            tenant_type='company',
            status='active',
        )
        self.company_tenant = Client.objects.create(
            schema_name='acme',
            name='Acme Corporation',
            slug='acme',
            tenant_type='company',
            status='active',
        )
        self.agency_tenant = Client.objects.create(
            schema_name='talentpartners',
            name='Talent Partners',
            slug='talentpartners',
            tenant_type='agency',
            status='active',
        )

    def test_prefix_fallback_and_custom_override(self):
        auto_prefix = ensure_tenant_prefix(self.company_tenant.id)
        self.assertTrue(auto_prefix)

        self.company_tenant.reference_prefix_custom = 'app'
        self.company_tenant.save(update_fields=['reference_prefix_custom'])
        effective_prefix = ensure_tenant_prefix(self.company_tenant.id)
        self.assertEqual(effective_prefix, 'APP')

    def test_sequence_isolated_by_tenant_type_and_year(self):
        ts_2025 = datetime(2025, 3, 1, tzinfo=dt_timezone.utc)

        cc_1 = build_reference(tenant_id=self.company_tenant.id, entity_type='CC', created_at=ts_2025)
        cc_2 = build_reference(tenant_id=self.company_tenant.id, entity_type='CC', created_at=ts_2025)
        ac_1 = build_reference(tenant_id=self.company_tenant.id, entity_type='AC', created_at=ts_2025)
        cj_1 = build_reference(tenant_id=self.company_tenant.id, entity_type='CJ', created_at=ts_2025)
        cc_agency = build_reference(tenant_id=self.agency_tenant.id, entity_type='CC', created_at=ts_2025)

        self.assertTrue(cc_1.endswith('/25'))
        self.assertIn('-CC-0001/', cc_1)
        self.assertIn('-CC-0002/', cc_2)
        self.assertIn('-AC-0001/', ac_1)
        self.assertIn('-CJ-0001/', cj_1)
        self.assertIn('-CC-0001/', cc_agency)

    def test_candidate_type_assignment_and_immutability(self):
        company_candidate = Candidate.objects.create(
            tenant_id=self.company_tenant.id,
            first_name='Company',
            last_name='Candidate',
            email='cc@example.com',
            source='company',
        )
        agency_candidate = Candidate.objects.create(
            tenant_id=self.agency_tenant.id,
            first_name='Agency',
            last_name='Candidate',
            email='ac@example.com',
            source='agency',
            initial_entry_type='agency_submit',
        )
        direct_candidate = Candidate.objects.create(
            tenant_id=None,
            first_name='Direct',
            last_name='Candidate',
            email='dc@example.com',
            source='self',
            initial_entry_type='self',
        )

        self.assertIn('-CC-', company_candidate.candidate_ref_id)
        self.assertIn('-AC-', agency_candidate.candidate_ref_id)
        self.assertIn('-DC-', direct_candidate.candidate_ref_id)

        original = company_candidate.candidate_ref_id
        company_candidate.candidate_ref_id = 'APP-CC-0001/25'
        with self.assertRaises(ValidationError):
            company_candidate.save()
        company_candidate.refresh_from_db()
        self.assertEqual(company_candidate.candidate_ref_id, original)

    def test_job_type_assignment_and_immutability(self):
        company_job = JobRequisition.objects.create(
            tenant_id=self.company_tenant.id,
            title='Backend Engineer',
            status='draft',
        )
        agency_job = JobRequisition.objects.create(
            tenant_id=self.agency_tenant.id,
            title='Agency Job',
            status='draft',
        )

        self.assertIn('-CJ-', company_job.job_ref_id)
        self.assertIn('-AJ-', agency_job.job_ref_id)

        original = company_job.job_ref_id
        company_job.job_ref_id = 'APP-CJ-0001/25'
        with self.assertRaises(ValidationError):
            company_job.save()
        company_job.refresh_from_db()
        self.assertEqual(company_job.job_ref_id, original)

    def test_serializer_exposes_reference_ids(self):
        candidate = Candidate.objects.create(
            tenant_id=self.company_tenant.id,
            first_name='Serial',
            last_name='Candidate',
            email='serial@example.com',
            source='company',
        )
        job = JobRequisition.objects.create(
            tenant_id=self.company_tenant.id,
            title='Serializer Job',
            status='draft',
        )

        candidate_data = CandidateSerializer(candidate).data
        job_data = JobRequisitionSerializer(job).data

        self.assertEqual(candidate_data['candidate_ref_id'], candidate.candidate_ref_id)
        self.assertEqual(job_data['job_ref_id'], job.job_ref_id)
