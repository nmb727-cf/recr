from django.core.management.base import BaseCommand
from apps.hdc.models import (
    HiringCommittee, CommitteeMember, ComparisonSet, ComparisonCandidate,
    DecisionApproval, OfferRecommendation, OfferScenario,
    NegotiationCase, NegotiationRound, OfferReleasePacket, JoiningCase
)
from apps.jobs.models import JobRequisition
from apps.candidates.models import Candidate
from apps.pipeline.models import Application
from apps.tenants.models import Client
from apps.accounts.models import CustomUser
from django.utils import timezone
from datetime import timedelta
import random
import uuid

class Command(BaseCommand):
    help = 'Seed Hiring Decision Command Center (HDC) sample data'

    def add_arguments(self, parser):
        parser.add_argument('--tenant_id', type=str, help='Target tenant ID')

    def handle(self, *args, **options):
        target_tenant = options.get('tenant_id')
        
        if target_tenant:
            clients = Client.objects.filter(id=target_tenant)
        else:
            clients = Client.objects.exclude(schema_name='public')

        if not clients.exists():
            self.stdout.write(self.style.ERROR("No valid tenants found to seed."))
            return

        for client in clients:
            tenant_id = client.id
            user = CustomUser.objects.filter(tenant_id=tenant_id).first()
            
            if not user:
                continue

            self.stdout.write(f"Seeding HDC data for {client.schema_name}...")

            # 1. Create or get Jobs
            job, _ = JobRequisition.objects.get_or_create(
                tenant_id=tenant_id,
                title="Senior Staff Engineer",
                defaults={'status': 'active', 'hiring_manager_id': user.id}
            )

            # 2. Scenarios
            self.seed_committee_scenario(tenant_id, job, user)
            self.seed_approval_scenario(tenant_id, job, user)
            self.seed_modeling_scenario(tenant_id, job, user)
            self.seed_negotiation_scenario(tenant_id, job, user)
            self.seed_joining_scenario(tenant_id, job, user)
            self.seed_comparison_scenario(tenant_id, job, user)

        self.stdout.write(self.style.SUCCESS("HDC seeding complete."))

    def seed_committee_scenario(self, tid, job, user):
        c = self.get_candidate(tid, "John", "Doe", "john.doe@seed.com")
        app, _ = Application.objects.get_or_create(
            tenant_id=tid, candidate_id=c.id, requisition_id=job.id,
            defaults={'status': 'interview'}
        )
        comm, _ = HiringCommittee.objects.get_or_create(
            tenant_id=tid, application_id=app.id,
            defaults={'name': f"Review: {c.first_name}", 'requisition_id': job.id, 'candidate_id': c.id, 'status': 'voting'}
        )
        CommitteeMember.objects.get_or_create(committee=comm, user_id=user.id, defaults={'role': 'Chair'})

    def seed_approval_scenario(self, tid, job, user):
        c = self.get_candidate(tid, "Jane", "Smith", "jane.smith@seed.com")
        app, _ = Application.objects.get_or_create(
            tenant_id=tid, candidate_id=c.id, requisition_id=job.id,
            defaults={'status': 'interview'}
        )
        DecisionApproval.objects.get_or_create(
            tenant_id=tid, application_id=app.id,
            defaults={'requisition_id': job.id, 'status': 'pending', 'approver_id': user.id}
        )

    def seed_modeling_scenario(self, tid, job, user):
        c = self.get_candidate(tid, "Alice", "Wonder", "alice@seed.com")
        app, _ = Application.objects.get_or_create(
            tenant_id=tid, candidate_id=c.id, requisition_id=job.id,
            defaults={'status': 'offer'}
        )
        rec, _ = OfferRecommendation.objects.get_or_create(
            tenant_id=tid, application_id=app.id,
            defaults={'status': 'scenario_modeling'}
        )
        OfferScenario.objects.get_or_create(
            recommendation=rec, name="Aggressive Package",
            defaults={'ctc_amount': 4500000, 'market_position': 'Top 10%', 'risk_level': 'Medium'}
        )

    def seed_negotiation_scenario(self, tid, job, user):
        c = self.get_candidate(tid, "Bob", "Builder", "bob@seed.com")
        app, _ = Application.objects.get_or_create(
            tenant_id=tid, candidate_id=c.id, requisition_id=job.id,
            defaults={'status': 'offer'}
        )
        neg, _ = NegotiationCase.objects.get_or_create(
            tenant_id=tid, application_id=app.id,
            defaults={'status': 'active', 'current_round': 1, 'candidate_ask': 'Needs 10% more base'}
        )
        NegotiationRound.objects.get_or_create(
            negotiation_case=neg, round_number=1,
            defaults={'status': 'open', 'notes': 'Candidate requested higher fixed component.'}
        )

    def seed_joining_scenario(self, tid, job, user):
        c = self.get_candidate(tid, "Charlie", "Brown", "charlie@seed.com")
        app, _ = Application.objects.get_or_create(
            tenant_id=tid, candidate_id=c.id, requisition_id=job.id,
            defaults={'status': 'offer'}
        )
        JoiningCase.objects.get_or_create(
            tenant_id=tid, application_id=app.id,
            defaults={'status': 'pending', 'joining_date': timezone.now().date() + timedelta(days=30)}
        )

    def seed_comparison_scenario(self, tid, job, user):
        c1 = self.get_candidate(tid, "Finalist", "One", "f1@seed.com")
        c2 = self.get_candidate(tid, "Finalist", "Two", "f2@seed.com")
        app1, _ = Application.objects.get_or_create(tenant_id=tid, candidate_id=c1.id, requisition_id=job.id, defaults={'status': 'interview'})
        app2, _ = Application.objects.get_or_create(tenant_id=tid, candidate_id=c2.id, requisition_id=job.id, defaults={'status': 'interview'})
        
        comp, _ = ComparisonSet.objects.get_or_create(
            tenant_id=tid, name="Senior Engineer Finalists", requisition_id=job.id,
            defaults={'status': 'active'}
        )
        ComparisonCandidate.objects.get_or_create(comparison_set=comp, candidate_id=c1.id, application_id=app1.id, defaults={'score': 8.5})
        ComparisonCandidate.objects.get_or_create(comparison_set=comp, candidate_id=c2.id, application_id=app2.id, defaults={'score': 7.9})

    def get_candidate(self, tid, fname, lname, email):
        cand, _ = Candidate.objects.get_or_create(
            tenant_id=tid, email=email,
            defaults={'first_name': fname, 'last_name': lname}
        )
        return cand
