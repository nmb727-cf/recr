from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application
from apps.interviews.models import Interview
from apps.agencies.models import AgencyPerformanceScore
from apps.analytics.models import SystemIntelligenceMemory
from apps.accounts.services import RecruiterIntelligenceService

class SystemIntelligenceMemoryService:
    @staticmethod
    def get_intelligence_memory(tenant_id):
        # Retrieve all learned memories
        memories = SystemIntelligenceMemory.objects.filter(tenant_id=tenant_id)
        
        # If no memories, perform initial "learning"
        if not memories.exists():
            SystemIntelligenceMemoryService.trigger_learning(tenant_id)
            memories = SystemIntelligenceMemory.objects.filter(tenant_id=tenant_id)
            
        return list(memories.values())

    @staticmethod
    def trigger_learning(tenant_id):
        now = timezone.now()
        
        # 1. Pipeline Success Learning
        hires = Application.objects.filter(tenant_id=tenant_id, status='joined').count()
        rejections = Application.objects.filter(tenant_id=tenant_id, status='rejected').count()
        total_apps = Application.objects.filter(tenant_id=tenant_id).count()
        
        if total_apps > 0:
            SystemIntelligenceMemory.objects.update_or_create(
                tenant_id=tenant_id, category='pipeline', attribute_key='success_rate',
                defaults={
                    'entity_name': 'Global Pipeline',
                    'attribute_value': {
                        'rate': round(hires/total_apps*100, 1), 
                        'hires': hires, 
                        'rejections': rejections,
                        'total': total_apps
                    },
                    'confidence_score': 0.9 if total_apps > 50 else 0.5
                }
            )

        # 2. Recruiter Learning
        recruiter_intel = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
        for r in recruiter_intel:
            # Learn speed
            avg_response = r['metrics'].get('avg_response_hours', 24)
            SystemIntelligenceMemory.objects.update_or_create(
                tenant_id=tenant_id, category='recruiter', entity_id=r['user_id'],
                attribute_key='response_velocity',
                defaults={
                    'entity_name': r['full_name'],
                    'attribute_value': {'avg_hours': avg_response, 'status': 'fast' if avg_response < 12 else 'normal'},
                    'confidence_score': 0.8
                }
            )
            # Learn overall performance
            SystemIntelligenceMemory.objects.update_or_create(
                tenant_id=tenant_id, category='recruiter', entity_id=r['user_id'],
                attribute_key='performance_score',
                defaults={
                    'entity_name': r['full_name'],
                    'attribute_value': {'score': r['score'], 'hire_rate': r['metrics'].get('hire_rate', 0)},
                    'confidence_score': 0.85
                }
            )

        # 3. Agency Learning
        agency_scores = AgencyPerformanceScore.objects.filter(tenant_id=tenant_id)
        for s in agency_scores:
            SystemIntelligenceMemory.objects.update_or_create(
                tenant_id=tenant_id, category='agency', entity_id=s.agency_tenant_id,
                attribute_key='sourcing_quality',
                defaults={
                    'entity_name': f"Agency {str(s.agency_tenant_id)[:8]}",
                    'attribute_value': {
                        'score': float(s.overall_score), 
                        'hires': s.joined_count,
                        'shortlist_rate': float(s.shortlist_rate)
                    },
                    'confidence_score': 0.85
                }
            )

        # 4. Interview Learning
        interviews = Interview.objects.filter(tenant_id=tenant_id, status='completed')
        avg_score = interviews.aggregate(avg=Avg('overall_score'))['avg'] or 0
        if avg_score > 0:
            SystemIntelligenceMemory.objects.update_or_create(
                tenant_id=tenant_id, category='interview', attribute_key='success_threshold',
                defaults={
                    'entity_name': 'Global Interview Standard',
                    'attribute_value': {'ideal_score': round(float(avg_score) + 0.5, 2)},
                    'confidence_score': 0.7
                }
            )
            
        return True
