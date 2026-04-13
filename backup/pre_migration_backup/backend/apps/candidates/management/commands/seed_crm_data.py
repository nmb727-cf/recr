from django.core.management.base import BaseCommand
from apps.candidates.models import Candidate
from apps.candidates.crm_models import CandidatePipelineStatus, CandidateInteraction
from apps.tenants.models import Client
from apps.accounts.models import CustomUser
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Seed Candidate Relations (CRM) sample data for specific tenants'

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
            owner = CustomUser.objects.filter(tenant_id=tenant_id).first()
            
            if not owner:
                self.stdout.write(self.style.WARNING(f"Skipping tenant {client.schema_name} (ID: {tenant_id}) - No user found."))
                continue

            candidates_to_create = [
                {"first_name": "Sarah", "last_name": "Conner", "email": f"sarah.{tenant_id}@example.com", "title": "Senior Project Manager", "status": "new_lead", "intent": "future_jobs"},
                {"first_name": "James", "last_name": "Bond", "email": f"007.{tenant_id}@mi6.gov.uk", "title": "Security Specialist", "status": "contacted", "intent": "specific_job"},
                {"first_name": "Ellen", "last_name": "Ripley", "email": f"ripley.{tenant_id}@weyland.corp", "title": "Operations Manager", "status": "interested", "intent": "looking_for_job"},
                {"first_name": "Tony", "last_name": "Stark", "email": f"tony.{tenant_id}@stark.com", "title": "CTO", "status": "qualified", "intent": "just_lead"},
            ]

            self.stdout.write(f"Seeding CRM data for {client.schema_name} (ID: {tenant_id})...")

            for data in candidates_to_create:
                candidate, _ = Candidate.objects.get_or_create(
                    tenant_id=tenant_id,
                    email=data['email'],
                    defaults={
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'current_title': data['title'],
                        'current_company': "Sample Global Inc.",
                        'experience_years': random.randint(5, 15),
                    }
                )

                next_date = timezone.now().date() + timedelta(days=random.randint(1, 7))
                CandidatePipelineStatus.objects.update_or_create(
                    tenant_id=tenant_id,
                    candidate_id=candidate.id,
                    defaults={
                        'status': data['status'],
                        'intent': data['intent'],
                        'assigned_to': owner.id,
                        'next_action': f"Review {data['title']} fitment",
                        'next_action_date': next_date,
                        'last_contacted_at': timezone.now() - timedelta(days=random.randint(0, 5)),
                        'contact_count': 1,
                        'sentiment': 'positive',
                    }
                )

                CandidateInteraction.objects.create(
                    tenant_id=tenant_id,
                    candidate_id=candidate.id,
                    interaction_type='call',
                    content='Initial screening completed. High matching confidence.',
                    created_by=owner.id
                )

        self.stdout.write(self.style.SUCCESS("CRM seeding complete for all active tenants."))
