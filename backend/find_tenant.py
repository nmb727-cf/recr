import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from apps.organisations.models import Organisation
t = Organisation.objects.first()
if t:
    print(t.tenant_id)
