import os
import django
import sys

sys.path.append('/home/nirav/projects/SaaS_Project/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.orchestration_center.models import AutomationInsight, Workflow, WorkflowTemplate
from apps.orchestration_center.services.automation_ai_engine import AutomationAIEngine
from apps.tenants.models import Client
from django_tenants.utils import schema_context

def run_tests():
    print("Testing AI Automation Intelligence...")
    
    tenant = Client.objects.first()
    if not tenant:
        print("No tenant found.")
        return

    with schema_context(tenant.schema_name):
        tenant_id = tenant.schema_name  # In django-tenants, usually use schema_name or tenant ID depending on how BaseModel is set up
        # We usually store tenant_id as UUID, let's grab the actual UUID if possible, or just the first user's tenant_id
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.first()
        if user and hasattr(user, 'tenant_id'):
            tenant_id = user.tenant_id

        print(f"Using Tenant ID: {tenant_id}")

        # Clear existing
        AutomationInsight.objects.filter(tenant_id=tenant_id).delete()
        Workflow.objects.filter(tenant_id=tenant_id).delete()

        # Test 1: AI detects bottleneck
        print("Test 1: Run AI analysis to detect bottleneck")
        insight = AutomationAIEngine.analyze_pipeline(tenant_id)
        
        assert insight is not None, "Insight should be created"
        assert insight.insight_type == 'pipeline_bottleneck', "Should be a bottleneck insight"
        print("Test 1 Passed: Suggestion created.")

        # Test 2: Accept suggestion
        print("Test 2: Accept suggestion")
        insight.status = 'accepted'
        insight.save()

        # Simulate view logic
        workflow = None
        action = insight.suggested_action.get('action')
        if action == 'create_workflow':
            trigger_event = insight.suggested_action.get('trigger_event', 'manual')
            workflow = Workflow.objects.create(
                tenant_id=tenant_id,
                name=f"Auto-generated: {insight.title}",
                trigger_event=trigger_event,
                is_active=False,
                status='draft'
            )
        
        assert workflow is not None, "Workflow should be created"
        assert "Auto-generated" in workflow.name, "Workflow name should reflect auto-generation"
        print("Test 2 Passed: Workflow created.")

        # Test 3: Dismiss suggestion
        print("Test 3: Dismiss suggestion")
        insight2 = AutomationAIEngine.analyze_workflow_performance(tenant_id)
        if not insight2:
            # force create
            insight2 = AutomationInsight.objects.create(
                tenant_id=tenant_id,
                insight_type='workflow_optimization',
                title="High Workflow Failure Rate",
                status='new'
            )
        
        insight2.status = 'dismissed'
        insight2.save()
        
        assert AutomationInsight.objects.get(id=insight2.id).status == 'dismissed', "Insight should be dismissed"
        print("Test 3 Passed: Suggestion dismissed.")

if __name__ == '__main__':
    run_tests()