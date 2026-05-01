import logging
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Avg, Q
from apps.automation_os.models import (
    AutomationRuntimeState,
    AutomationEngineRegistry,
    AutomationExecutionPolicy,
    AutomationWorkloadBucket,
    AutomationBusinessCoverage,
    AutomationOperatingEvent,
    AutomationOperatingInsight,
    RuntimeStatus,
    OrchestrationMode,
    EngineStatus,
    BucketStatus,
    EventSeverity
)

logger = logging.getLogger(__name__)

class AutomationOperatingSystem:
    @staticmethod
    def initialize_runtime(tenant_id):
        """
        Sets up the initial runtime state and engine registry for a tenant.
        """
        with transaction.atomic():
            state, _ = AutomationRuntimeState.objects.get_or_create(
                tenant_id=tenant_id,
                defaults={
                    'runtime_status': RuntimeStatus.HEALTHY,
                    'orchestration_mode': OrchestrationMode.NORMAL
                }
            )
            
            AutomationOperatingSystem.register_engines(tenant_id)
            return state

    @staticmethod
    def register_engines(tenant_id):
        """
        Registers all standard automation engines.
        """
        engines = [
            ('workflow', 'Workflow Engine', 10),
            ('notification', 'Notification Orchestrator', 20),
            ('task', 'Task Engine', 30),
            ('sla', 'SLA Engine', 15),
            ('governance', 'Governance Engine', 5),
            ('observability', 'Observability Center', 40),
            ('recovery', 'Recovery Engine', 8),
            ('playbook', 'Playbook Engine', 50),
            ('permission', 'Permission Layer', 2),
            ('sandbox', 'Sandbox Lab', 60),
            ('change_impact', 'Change Impact Center', 70),
        ]
        
        for key, name, priority in engines:
            AutomationEngineRegistry.objects.get_or_create(
                tenant_id=tenant_id,
                engine_key=key,
                defaults={
                    'engine_name': name,
                    'engine_type': key,
                    'priority': priority,
                    'status': EngineStatus.ACTIVE
                }
            )

    @staticmethod
    def evaluate_runtime_health(tenant_id):
        """
        Aggregates statuses from registry and workload to update runtime state.
        """
        engines = AutomationEngineRegistry.objects.filter(tenant_id=tenant_id)
        degraded = engines.filter(status=EngineStatus.DEGRADED).count()
        failed = engines.filter(status=EngineStatus.FAILED).count()
        paused = engines.filter(status=EngineStatus.PAUSED).count()
        
        state = AutomationRuntimeState.objects.get(tenant_id=tenant_id)
        state.degraded_engine_count = degraded
        state.failed_engine_count = failed
        state.paused_engine_count = paused
        
        if failed > 0:
            state.runtime_status = RuntimeStatus.FAILED
        elif degraded > 0:
            state.runtime_status = RuntimeStatus.DEGRADED
        elif paused == engines.count():
            state.runtime_status = RuntimeStatus.PAUSED
        else:
            state.runtime_status = RuntimeStatus.HEALTHY
            
        state.save()
        return state

    @staticmethod
    def log_operating_event(tenant_id, event_type, message, severity=EventSeverity.INFO, source='OS', payload=None):
        return AutomationOperatingEvent.objects.create(
            tenant_id=tenant_id,
            event_type=event_type,
            severity=severity,
            source_engine=source,
            message=message,
            event_payload=payload or {}
        )

    @staticmethod
    def switch_orchestration_mode(tenant_id, mode, performed_by=None):
        state = AutomationRuntimeState.objects.get(tenant_id=tenant_id)
        old_mode = state.orchestration_mode
        state.orchestration_mode = mode
        state.save()
        
        AutomationOperatingSystem.log_operating_event(
            tenant_id, 
            'mode_change', 
            f"Orchestration mode switched from {old_mode} to {mode}.",
            severity=EventSeverity.WARNING if mode != OrchestrationMode.NORMAL else EventSeverity.INFO,
            payload={'old_mode': old_mode, 'new_mode': mode, 'user_id': str(performed_by)}
        )
        return state

    @staticmethod
    def recalculate_business_coverage(tenant_id):
        """
        Heuristic calculation of how much business logic is covered by automation.
        """
        # This would normally query all other modules
        # Mocking for implementation
        modules = ['candidates', 'jobs', 'interviews', 'offers', 'agencies']
        for mod in modules:
            AutomationBusinessCoverage.objects.update_or_create(
                tenant_id=tenant_id,
                module_scope=mod,
                defaults={
                    'process_name': f"{mod.capitalize()} Lifecycle",
                    'automation_coverage_percent': 65.0, # Mock
                    'manual_gap_percent': 35.0, # Mock
                    'active_workflow_count': 5
                }
            )

    @staticmethod
    def generate_operating_insights(tenant_id):
        """
        AI or heuristic-driven insights about the global automation state.
        """
        # 1. Check for under-automated modules
        # 2. Check for bottleneck workload buckets
        # Mocking
        AutomationOperatingInsight.objects.update_or_create(
            tenant_id=tenant_id,
            insight_type='under_automated',
            defaults={
                'title': "Low Automation Coverage: Agency Channel",
                'description': "Agency submissions are currently 80% manual. High risk of SLA breach detected.",
                'recommendation': "Install the 'Agency SLA Control' Playbook.",
                'impact_level': 'high'
            }
        )
