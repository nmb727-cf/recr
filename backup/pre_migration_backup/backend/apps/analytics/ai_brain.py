from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application
from apps.agencies.models import AgencyClientRelationship
from apps.analytics.intelligence_substrate import IntelligenceAggregator

class HiringAIBrainService:
    @staticmethod
    def generate_brain_intelligence(tenant_id):
        global_snapshot = IntelligenceAggregator.build_global_intelligence(tenant_id=tenant_id)
        pipeline_snapshot = IntelligenceAggregator.build_pipeline_intelligence(tenant_id=tenant_id)

        # 1. Job orchestrations
        active_jobs = JobRequisition.objects.filter(tenant_id=tenant_id, status='active', is_deleted=False)
        total_jobs = active_jobs.count()
        
        # 2. Risk Detection
        risks = []
        opportunities = []
        smart_actions = []
        job_recommendations = []

        stuck_candidates = Application.objects.filter(
            tenant_id=tenant_id, 
            status__in=['applied', 'screening', 'interview'],
            updated_at__lt=timezone.now() - timedelta(days=10),
            is_deleted=False
        ).count()
        substrate_stuck = pipeline_snapshot.get('signals', {}).get('stuck_stage')
        if substrate_stuck is not None:
            stuck_candidates = int(substrate_stuck)
        
        if stuck_candidates > 5:
            risks.append({
                'title': 'Candidate Bottleneck Detected',
                'impact': f'{stuck_candidates} candidates have not moved in over 10 days. Risk of high drop-off.'
            })
            smart_actions.append({
                'title': 'Clear Pipeline Bottleneck',
                'category': 'Pipeline',
                'priority': 'high',
                'description': 'Review stuck candidates and make immediate Go/No-Go decisions.'
            })
            
        # 3. Agency Analysis
        active_agencies = AgencyClientRelationship.objects.filter(
            company_tenant_id=tenant_id, status='active', is_deleted=False
        ).count()
        
        if active_agencies < 2 and total_jobs > 5:
            opportunities.append({
                'title': 'Expand Agency Network',
                'description': 'Current job volume indicates high load. Engaging more agencies could speed up hiring.',
                'metric': 'Reduce Time-to-Fill by ~15%'
            })
            
        # 4. Job specific logic
        for job in active_jobs:
            apps = Application.objects.filter(requisition_id=job.id, is_deleted=False)
            if apps.count() < 3 and (timezone.now() - job.created_at).days > 7:
                job_recommendations.append({
                    'job_title': job.title,
                    'suggestions': [
                        'Boost sourcing efforts or increase budget.',
                        'Assign to top performing agency.',
                        'Review job description for overly strict requirements.'
                    ]
                })
                
        # Fill in overview metrics
        overview = {
            'actionable_insights': len(smart_actions) + len(opportunities),
            'critical_risks': len(risks),
            'opportunities': len(opportunities),
            'health_score': max(0, 100 - (len(risks) * 10) + (len(opportunities) * 2))
        }

        # Add default smart actions if empty
        if not smart_actions:
            smart_actions.append({
                'title': 'Review Offer Acceptance Rates',
                'category': 'Strategy',
                'priority': 'medium',
                'description': 'Analyze recent offer declines to adjust compensation strategy.'
            })
            
        return {
            'overview': overview,
            'smart_actions': smart_actions,
            'risks': risks,
            'opportunities': opportunities,
            'job_recommendations': job_recommendations,
            'substrate': global_snapshot.get('signals', {}),
        }
