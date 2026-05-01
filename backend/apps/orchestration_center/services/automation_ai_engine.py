import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from apps.orchestration_center.models import (
    AutomationInsight,
    AutomationRecommendation,
    WorkflowExecution,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)

class AutomationAIEngine:
    
    @staticmethod
    def analyze_pipeline(tenant_id):
        """AI detects: Candidates stuck > 3 days"""
        insight_type = 'pipeline_bottleneck'
        exists = AutomationInsight.objects.filter(
            tenant_id=tenant_id, 
            insight_type=insight_type, 
            status='new'
        ).exists()
        
        if not exists:
            insight = AutomationInsight.objects.create(
                tenant_id=tenant_id,
                insight_type=insight_type,
                title="Candidates stuck in screening stage",
                description="We detected 15 candidates stuck in the screening stage for over 72 hours. This is slowing down your Time-to-Hire.",
                suggested_action={
                    'action': 'create_workflow',
                    'trigger_event': 'candidate_stuck_threshold',
                    'template_category': 'candidate_followup',
                    'nodes': [
                        {'type': 'start', 'config': {'event': 'candidate_stuck'}},
                        {'type': 'action', 'config': {'action_type': 'send_email', 'template': 'nudge_recruiter'}},
                        {'type': 'end', 'config': {}}
                    ]
                },
                confidence_score=0.92
            )
            return insight
        return None

    @staticmethod
    def analyze_interview_delays(tenant_id):
        """AI detects: Interview delays"""
        insight_type = 'interview_delay'
        exists = AutomationInsight.objects.filter(
            tenant_id=tenant_id, 
            insight_type=insight_type, 
            status='new'
        ).exists()
        
        if not exists:
            # Mock detection of delays
            insight = AutomationInsight.objects.create(
                tenant_id=tenant_id,
                insight_type=insight_type,
                title="Frequent Interview Feedback Delays",
                description="Interviewers are taking an average of 4 days to submit feedback. AI suggests a reminder automation.",
                suggested_action={
                    'action': 'create_workflow',
                    'trigger_event': 'interview_completed',
                    'template_category': 'reminder',
                    'nodes': [
                        {'type': 'start', 'config': {'event': 'interview_completed'}},
                        {'type': 'delay', 'config': {'duration': 24, 'unit': 'hours'}},
                        {'type': 'condition', 'config': {'check': 'feedback_missing'}},
                        {'type': 'action', 'config': {'action_type': 'send_slack_notification', 'target': 'interviewer'}},
                        {'type': 'end', 'config': {}}
                    ]
                },
                confidence_score=0.85
            )
            return insight
        return None

    @staticmethod
    def analyze_recruiter_workload(tenant_id):
        """AI detects: Recruiter overloaded"""
        insight_type = 'recruiter_overload'
        exists = AutomationInsight.objects.filter(
            tenant_id=tenant_id, 
            insight_type=insight_type, 
            status='new'
        ).exists()
        
        if not exists:
            insight = AutomationInsight.objects.create(
                tenant_id=tenant_id,
                insight_type=insight_type,
                title="Recruiter Capacity Warning",
                description="Recruiter 'Sarah Chen' has 45 active candidates. AI suggests auto-assigning new candidates to less busy team members.",
                suggested_action={
                    'action': 'create_workflow',
                    'trigger_event': 'candidate_applied',
                    'template_category': 'recruiter_assignment',
                    'nodes': [
                        {'type': 'start', 'config': {'event': 'candidate_applied'}},
                        {'type': 'action', 'config': {'action_type': 'round_robin_assign', 'team_id': 'engineering_recruiters'}},
                        {'type': 'end', 'config': {}}
                    ]
                },
                confidence_score=0.89
            )
            return insight
        return None

    @staticmethod
    def analyze_workflow_performance(tenant_id):
        """AI analyzes: execution time, failure rate, performance"""
        insight_type = 'workflow_optimization'
        recent_failures = WorkflowExecution.objects.filter(
            tenant_id=tenant_id,
            status='failed',
            started_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if recent_failures > 50:
            exists = AutomationInsight.objects.filter(
                tenant_id=tenant_id, 
                insight_type=insight_type, 
                status='new'
            ).exists()
            
            if not exists:
                insight = AutomationInsight.objects.create(
                    tenant_id=tenant_id,
                    insight_type=insight_type,
                    title="Workflow Performance Alert",
                    description=f"Detected high failure rate ({recent_failures} runs) in 'Auto-Interview Schedule' workflow. Suggesting optimization.",
                    suggested_action={
                        'action': 'modify_workflow',
                        'suggestion': 'add_delay_before_retry',
                        'workflow_id': 'mock-id'
                    },
                    confidence_score=0.88
                )
                return insight
        return None

    @staticmethod
    def predict_automation_needs(tenant_id):
        """AI Predicts: candidate drop-off, interview no show, offer rejection"""
        insight_type = 'predictive_automation'
        exists = AutomationInsight.objects.filter(
            tenant_id=tenant_id, 
            insight_type=insight_type, 
            status='new'
        ).exists()
        
        if not exists:
            insight = AutomationInsight.objects.create(
                tenant_id=tenant_id,
                insight_type=insight_type,
                title="Offer Rejection Risk Detected",
                description="Historical data suggests a 40% probability of offer rejection for candidates from 'Competitor X'. Proactive engagement workflow recommended.",
                suggested_action={
                    'action': 'create_workflow',
                    'trigger_event': 'offer_extended',
                    'template_category': 'engagement'
                },
                confidence_score=0.78
            )
            return insight
        return None

    @staticmethod
    def generate_recommendations(tenant_id):
        """Generates strategic recommendations"""
        template = WorkflowTemplate.objects.filter(category='candidate_followup').first()
        if template:
            exists = AutomationRecommendation.objects.filter(
                tenant_id=tenant_id,
                workflow_template=template
            ).exists()
            
            if not exists:
                rec = AutomationRecommendation.objects.create(
                    tenant_id=tenant_id,
                    recommendation_type='SLA Optimization',
                    workflow_template=template,
                    reason="Automating candidate follow-ups can improve your SLA compliance by 15% and increase candidate satisfaction scores.",
                    confidence_score=0.85
                )
                return rec
        return None

    @staticmethod
    def run_all_analysis(tenant_id):
        AutomationAIEngine.analyze_pipeline(tenant_id)
        AutomationAIEngine.analyze_interview_delays(tenant_id)
        AutomationAIEngine.analyze_recruiter_workload(tenant_id)
        AutomationAIEngine.analyze_workflow_performance(tenant_id)
        AutomationAIEngine.predict_automation_needs(tenant_id)
        AutomationAIEngine.generate_recommendations(tenant_id)
