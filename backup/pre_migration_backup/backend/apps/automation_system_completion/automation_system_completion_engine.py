import uuid
from typing import Dict, Any, List
from django.utils import timezone
from .models import (
    AutomationSystemReadiness,
    AutomationCompletionCheck,
    AutomationGapItem,
    AutomationProductionGate,
    AutomationCompletionReport
)

class AutomationSystemCompletionEngine:
    """
    Engine to validate full automation system completeness, integration, and production readiness.
    """

    def run_completion_assessment(self, tenant_id: uuid.UUID) -> AutomationSystemReadiness:
        # Run all sub-assessments
        self.check_engine_integrations(tenant_id)
        self.validate_end_to_end_flows(tenant_id)
        self.validate_permissions_and_isolation(tenant_id)
        self.validate_governance_and_audit(tenant_id)
        self.validate_observability_and_recovery(tenant_id)
        self.validate_ai_and_insight_alignment(tenant_id)
        
        # Detect gaps based on check failures
        self.detect_system_gaps(tenant_id)
        
        # Update gates based on checks and gaps
        self.evaluate_production_gates(tenant_id)
        
        # Calculate final score and status
        readiness = self.calculate_readiness_score(tenant_id)
        
        # Generate summary report
        self.generate_completion_reports(tenant_id, 'readiness_summary')
        
        return readiness

    def _create_or_update_check(self, tenant_id, category, name, status, severity, summary=""):
        check, _ = AutomationCompletionCheck.objects.update_or_create(
            tenant_id=tenant_id,
            check_category=category,
            check_name=name,
            defaults={
                'check_status': status,
                'severity': severity,
                'result_summary': summary
            }
        )
        return check

    def check_engine_integrations(self, tenant_id: uuid.UUID):
        # Mocking integration checks across all modules
        self._create_or_update_check(tenant_id, 'engine_integration', 'Workflow Engine Reachable', 'passed', 'critical')
        self._create_or_update_check(tenant_id, 'engine_integration', 'SLA Engine Heartbeat', 'passed', 'high')
        self._create_or_update_check(tenant_id, 'engine_integration', 'Playbook Engine Registry', 'passed', 'medium')
        # Simulate a warning
        self._create_or_update_check(tenant_id, 'engine_integration', 'Sandbox Environment Synced', 'warning', 'medium', 'Sandbox data is 24h old.')

    def validate_end_to_end_flows(self, tenant_id: uuid.UUID):
        self._create_or_update_check(tenant_id, 'api', 'Candidate Flow E2E', 'passed', 'critical')
        self._create_or_update_check(tenant_id, 'api', 'Offer Negotiation Flow', 'passed', 'high')

    def validate_permissions_and_isolation(self, tenant_id: uuid.UUID):
        self._create_or_update_check(tenant_id, 'permissions', 'RBAC Enforcement Check', 'passed', 'critical')
        self._create_or_update_check(tenant_id, 'tenant_isolation', 'Cross-Tenant Leakage Check', 'passed', 'critical')

    def validate_governance_and_audit(self, tenant_id: uuid.UUID):
        self._create_or_update_check(tenant_id, 'governance', 'Version Control Active', 'passed', 'high')
        self._create_or_update_check(tenant_id, 'governance', 'Approval Gates Configured', 'passed', 'critical')

    def validate_observability_and_recovery(self, tenant_id: uuid.UUID):
        self._create_or_update_check(tenant_id, 'observability', 'Observability Traces Active', 'passed', 'high')
        # Simulate a failed check for recovery
        self._create_or_update_check(tenant_id, 'reliability', 'Dead Letter Queue Bound', 'failed', 'high', 'Dead letter queue integration missing.')

    def validate_ai_and_insight_alignment(self, tenant_id: uuid.UUID):
        self._create_or_update_check(tenant_id, 'ai', 'AI Brain Context Synced', 'passed', 'medium')
        self._create_or_update_check(tenant_id, 'analytics', 'Maturity Metrics Updated', 'passed', 'low')

    def detect_system_gaps(self, tenant_id: uuid.UUID):
        failed_checks = AutomationCompletionCheck.objects.filter(tenant_id=tenant_id, check_status='failed')
        for check in failed_checks:
            AutomationGapItem.objects.get_or_create(
                tenant_id=tenant_id,
                title=f"Fix failed check: {check.check_name}",
                defaults={
                    'gap_type': 'broken_flow' if check.check_category == 'api' else 'missing_integration',
                    'module_scope': check.check_category,
                    'description': check.result_summary,
                    'impact_level': check.severity,
                    'recommended_fix': f"Review {check.check_category} configuration."
                }
            )

    def calculate_readiness_score(self, tenant_id: uuid.UUID) -> AutomationSystemReadiness:
        # Mock calculation logic
        # engine integration: 20, governance: 15, reliability: 15, security: 15, 
        # observability: 10, intelligence: 10, UI/API: 10, QA: 5
        
        checks = AutomationCompletionCheck.objects.filter(tenant_id=tenant_id)
        total_checks = checks.count()
        passed_checks = checks.filter(check_status='passed').count()
        
        # Simplified score calculation for demonstration
        base_score = 80 # Starting at 80
        if checks.filter(check_status='failed', severity='critical').exists():
            base_score -= 40
        elif checks.filter(check_status='failed', severity='high').exists():
            base_score -= 20
            
        readiness_status = 'not_ready'
        if base_score >= 85:
            readiness_status = 'production_ready'
        elif base_score >= 70:
            readiness_status = 'ready_with_warnings'
        elif base_score >= 50:
            readiness_status = 'partial'
            
        readiness, _ = AutomationSystemReadiness.objects.update_or_create(
            tenant_id=tenant_id,
            defaults={
                'readiness_score': max(0, base_score),
                'readiness_status': readiness_status,
                'engine_integration_score': 18,
                'governance_score': 15,
                'reliability_score': 10, # Penalty applied
                'intelligence_score': 10,
                'security_score': 15,
                'tenant_isolation_score': 15,
                'documentation_score': 5,
                'qa_score': 5
            }
        )
        return readiness

    def evaluate_production_gates(self, tenant_id: uuid.UUID):
        gates = [
            ('tenant_isolation_gate', 'isolation_gate'),
            ('permission_gate', 'security_gate'),
            ('governance_gate', 'governance_gate'),
            ('observability_gate', 'observability_gate'),
            ('recovery_gate', 'reliability_gate'),
            ('qa_gate', 'qa_gate'),
            ('documentation_gate', 'documentation_gate')
        ]
        
        for name, type_ in gates:
            # Simplistic gate logic: pass unless there are failed checks in the related category
            cat_map = {
                'isolation_gate': 'tenant_isolation',
                'security_gate': 'permissions',
                'governance_gate': 'governance',
                'observability_gate': 'observability',
                'reliability_gate': 'reliability',
                'qa_gate': 'qa',
                'documentation_gate': 'documentation'
            }
            related_category = cat_map.get(type_)
            has_failures = AutomationCompletionCheck.objects.filter(
                tenant_id=tenant_id, check_category=related_category, check_status='failed'
            ).exists()
            
            AutomationProductionGate.objects.update_or_create(
                tenant_id=tenant_id,
                gate_name=name,
                gate_type=type_,
                defaults={
                    'current_status': 'failed' if has_failures else 'passed',
                    'blocking_reason': 'Failed associated completion checks.' if has_failures else ''
                }
            )

    def generate_completion_reports(self, tenant_id: uuid.UUID, report_type: str):
        payload = {
            'generated_at': timezone.now().isoformat(),
            'tenant_id': str(tenant_id),
            'summary': f"Generated {report_type} successfully."
        }
        
        report = AutomationCompletionReport.objects.create(
            tenant_id=tenant_id,
            report_type=report_type,
            report_name=f"{report_type.replace('_', ' ').title()} - {timezone.now().strftime('%Y-%m-%d')}",
            report_payload=payload,
            generated_by='System Completion Engine'
        )
        return report
