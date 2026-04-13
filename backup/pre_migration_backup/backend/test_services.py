import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.analytics.ai_brain import HiringAIBrainService
from apps.analytics.operations import UnifiedOperationsService
from apps.automation.orchestrator import GlobalAutomationOrchestratorService

tenant_id = None # Mock tenant ID or use a real one if available

print("Testing HiringAIBrainService...")
try:
    res = HiringAIBrainService.generate_brain_intelligence(tenant_id)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

print("\nTesting UnifiedOperationsService...")
try:
    res = UnifiedOperationsService.get_unified_operations_data(tenant_id)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

print("\nTesting GlobalAutomationOrchestratorService...")
try:
    res = GlobalAutomationOrchestratorService.get_orchestrator_dashboard(tenant_id)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
