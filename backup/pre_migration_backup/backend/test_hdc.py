import os
import django
import sys

# Set up Django environment
sys.path.append('/home/nirav/projects/SaaS_Project/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.hdc.models import HiringCommittee
from apps.tenants.models import Client
from django_tenants.utils import schema_context

def test_hdc_query():
    print("Testing HDC query...")
    try:
        # Check in public schema first (since it's in SHARED_APPS)
        with schema_context('public'):
            count = HiringCommittee.objects.count()
            print(f"HiringCommittee count in public: {count}")
    except Exception as e:
        print(f"Error querying HiringCommittee in public: {e}")

    try:
        # Check in a tenant schema
        client = Client.objects.first()
        if client:
            print(f"Testing with client: {client.schema_name}")
            with schema_context(client.schema_name):
                count = HiringCommittee.objects.count()
                print(f"HiringCommittee count in {client.schema_name}: {count}")
        else:
            print("No clients found.")
    except Exception as e:
        print(f"Error querying HiringCommittee in tenant schema: {e}")

if __name__ == "__main__":
    test_hdc_query()
