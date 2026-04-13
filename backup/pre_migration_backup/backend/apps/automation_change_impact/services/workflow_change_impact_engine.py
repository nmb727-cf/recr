import logging
from django.db import transaction
from django.utils import timezone
from apps.automation_change_impact.models import (
    WorkflowChangeSet,
    WorkflowImpactAnalysis,
    WorkflowDependencyMap,
    WorkflowDeploymentPlan,
    WorkflowRollbackPreview,
    ImpactLevel,
    DeploymentStrategy,
    DependencyType
)

logger = logging.getLogger(__name__)

class WorkflowChangeImpactEngine:
    @staticmethod
    @transaction.atomic
    def analyze_workflow_change(tenant_id, workflow_id, from_version, to_version, change_summary, created_by):
        # Create Change Set
        change_set = WorkflowChangeSet.objects.create(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            from_version=from_version,
            to_version=to_version,
            change_summary=change_summary,
            created_by=created_by
        )
        
        # 1. Detect Dependencies
        affected_workflows = WorkflowChangeImpactEngine.detect_dependencies(tenant_id, workflow_id)
        
        # 2. Identify Affected Modules
        affected_modules = WorkflowChangeImpactEngine.identify_affected_modules(change_summary)
        
        # 3. Identify Affected Users
        affected_users_count = WorkflowChangeImpactEngine.identify_affected_users(tenant_id, change_summary)
        
        # Determine affected SLAs, Notifications, Tasks
        affected_slas = change_summary.get('changed_slas', [])
        affected_notifications = change_summary.get('changed_notifications', [])
        affected_tasks = change_summary.get('changed_tasks', [])
        
        # 4. Calculate Risk Score
        risk_score, impact_level, risk_reason = WorkflowChangeImpactEngine.calculate_risk_score(
            affected_workflows=len(affected_workflows),
            affected_users=affected_users_count,
            affected_slas=len(affected_slas),
            affected_modules=len(affected_modules)
        )
        
        change_set.risk_score = risk_score
        change_set.impact_level = impact_level
        change_set.save()

        # Create Impact Analysis
        impact_analysis = WorkflowImpactAnalysis.objects.create(
            tenant_id=tenant_id,
            change_set=change_set,
            affected_module=affected_modules,
            affected_workflows=affected_workflows,
            affected_slas=affected_slas,
            affected_notifications=affected_notifications,
            affected_tasks=affected_tasks,
            affected_users_count=affected_users_count,
            risk_reason=risk_reason
        )
        
        # Generate Deployment Plan
        WorkflowChangeImpactEngine.generate_deployment_plan(tenant_id, change_set, created_by)
        
        # Generate Rollback Preview
        WorkflowChangeImpactEngine.generate_rollback_preview(tenant_id, change_set)
        
        return change_set

    @staticmethod
    def detect_dependencies(tenant_id, workflow_id):
        # Mock dependency detection logic
        # In a real scenario, this queries WorkflowDependencyMap or parses workflow edges
        dependencies = WorkflowDependencyMap.objects.filter(tenant_id=tenant_id, workflow_id=workflow_id)
        return [str(d.dependent_workflow_id) for d in dependencies if d.dependent_workflow_id]

    @staticmethod
    def identify_affected_modules(change_summary):
        # Parses change_summary for module context
        modules = set()
        if 'candidates' in str(change_summary): modules.add('candidates')
        if 'interviews' in str(change_summary): modules.add('interviews')
        if 'offers' in str(change_summary): modules.add('offers')
        return list(modules)

    @staticmethod
    def identify_affected_users(tenant_id, change_summary):
        # Calculate affected user count heuristically or by analyzing roles
        return 15 # Mock number

    @staticmethod
    def calculate_risk_score(affected_workflows, affected_users, affected_slas, affected_modules):
        score = 0
        reason = []
        
        if affected_workflows > 0:
            score += 15 * affected_workflows
            reason.append(f"Affects {affected_workflows} other workflows.")
            
        if affected_users > 50:
            score += 30
            reason.append("High number of affected users.")
        elif affected_users > 10:
            score += 10
            reason.append("Moderate number of affected users.")
            
        if affected_slas > 0:
            score += 20 * affected_slas
            reason.append(f"Modifies {affected_slas} SLA policies.")
            
        if affected_modules > 1:
            score += 25
            reason.append("Cross-module impact detected.")
            
        score = min(score, 100)
        
        if score <= 25:
            impact_level = ImpactLevel.LOW
        elif score <= 50:
            impact_level = ImpactLevel.MEDIUM
        elif score <= 75:
            impact_level = ImpactLevel.HIGH
        else:
            impact_level = ImpactLevel.CRITICAL
            
        if not reason:
            reason.append("Low risk changes detected.")
            
        return score, impact_level, " ".join(reason)

    @staticmethod
    def generate_deployment_plan(tenant_id, change_set, created_by):
        strategy = DeploymentStrategy.IMMEDIATE
        rollout_steps = []
        
        if change_set.impact_level == ImpactLevel.CRITICAL:
            strategy = DeploymentStrategy.MANUAL_APPROVAL
        elif change_set.impact_level == ImpactLevel.HIGH:
            strategy = DeploymentStrategy.STAGED
            rollout_steps = [10, 25, 50, 100]
        elif change_set.impact_level == ImpactLevel.MEDIUM:
            strategy = DeploymentStrategy.CANARY
            rollout_steps = [25, 100]
            
        return WorkflowDeploymentPlan.objects.create(
            tenant_id=tenant_id,
            change_set=change_set,
            deployment_strategy=strategy,
            rollout_steps=rollout_steps,
            created_by=created_by
        )

    @staticmethod
    def generate_rollback_preview(tenant_id, change_set):
        rollback_possible = True
        impact = "Safe to rollback"
        
        if change_set.impact_level == ImpactLevel.CRITICAL:
            impact = "Rollback may leave cross-module data in an inconsistent state. Manual reconciliation recommended."
            
        return WorkflowRollbackPreview.objects.create(
            tenant_id=tenant_id,
            change_set=change_set,
            rollback_possible=rollback_possible,
            rollback_impact=impact
        )
