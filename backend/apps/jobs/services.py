import uuid
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from apps.pipeline.models import Application, ApplicationStageHistory
from apps.jobs.models import JobRequisition, JobStage
from apps.agencies.services import AgencyIntelligenceService
from apps.accounts.services import RecruiterIntelligenceService
from apps.candidates.models import Candidate
from apps.candidates.services import CandidateIntelligenceService

from apps.jobs.intelligence_engine import JobIntelligenceEngine
from apps.analytics.intelligence_substrate import IntelligenceAggregator

class HiringAIBrainService:
    @staticmethod
    def get_job_intelligence(tenant_id, requisition_id):
        """
        Orchestrates intelligence from all engines to provide a unified 'Brain' view.
        Uses JobIntelligenceEngine for core logic.
        """
        job = JobRequisition.objects.get(id=requisition_id, tenant_id=tenant_id)
        apps = Application.objects.filter(requisition_id=requisition_id, tenant_id=tenant_id, is_deleted=False)
        substrate_snapshot = IntelligenceAggregator.build_job_intelligence(
            tenant_id=tenant_id,
            requisition_id=requisition_id,
        )
        intel = substrate_snapshot.get('engine') or JobIntelligenceEngine.get_job_intelligence(tenant_id, requisition_id)
        signal_intel = substrate_snapshot.get('signals') or {}
        
        # 5. Interview Snapshot (Keep as it is specific to the 'Brain' view)
        from apps.interviews.models import Interview
        interviews = Interview.objects.filter(requisition_id=requisition_id, tenant_id=tenant_id, is_deleted=False)
        interview_stats = {
            'total_conducted': interviews.filter(status='completed').count(),
            'pending_scheduled': interviews.filter(status='scheduled').count(),
            'in_progress': interviews.filter(status='in_progress').count(),
            'candidates_in_interview_stage': apps.filter(status='interview').count(),
            'upcoming_today': interviews.filter(
                status='scheduled',
                scheduled_at__date=timezone.now().date()
            ).count()
        }
        
        # 6. Top Candidate Recommendations
        best_fit = apps.filter(status__in=['applied', 'screening', 'shortlisted', 'interview']).order_by('-match_score')[:5]
        from apps.pipeline.serializers import ApplicationSerializer
        
        # Merge new engine intel with existing UI-specific structure
        return {
            'health_score': intel['health']['score'],
            'health_label': intel['health']['label'],
            'health_factors': intel['health']['factors'],
            'velocity': intel['velocity'],
            'bottlenecks': intel['bottlenecks'],
            'source_intelligence': intel['source_intelligence'],
            'team_impact': intel['team_impact'],
            'fill_risk': intel['fill_risk'],
            'next_best_actions': intel['recommended_actions'],
            'signal_intelligence': signal_intel,
            'substrate_insights': substrate_snapshot.get('insights', []),
            'interview_stats': interview_stats,
            'best_fit_candidates': ApplicationSerializer(best_fit, many=True).data,
            'team': {
                'hiring_manager_id': str(job.hiring_manager_id) if job.hiring_manager_id else None,
                'recruiter_id': str(job.recruiter_id) if job.recruiter_id else None,
            },
            'summary': intel['summary']
        }

class GlobalHiringCommandCenterService:
    @staticmethod
    def get_global_intelligence(tenant_id):
        """
        Global mission control intelligence (HID v1) aggregating all hiring signals.
        """
        now = timezone.now()
        jobs = JobRequisition.objects.filter(tenant_id=tenant_id, is_deleted=False)
        active_jobs = jobs.filter(status='active')
        apps = Application.objects.filter(tenant_id=tenant_id, is_deleted=False)
        global_snapshot = IntelligenceAggregator.build_global_intelligence(tenant_id=tenant_id)
        pipeline_snapshot = IntelligenceAggregator.build_pipeline_intelligence(tenant_id=tenant_id)
        
        # 1. Hiring Overview
        total_active_jobs = active_jobs.count()
        open_positions = active_jobs.aggregate(Sum('headcount'))['headcount__sum'] or 0
        total_in_pipeline = apps.exclude(status__in=['joined', 'rejected', 'withdrawn']).count()
        
        from apps.interviews.models import Interview
        interviews_scheduled = Interview.objects.filter(tenant_id=tenant_id, status='scheduled').count()
        offers_pending = apps.filter(status='offered').count()
        
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        hires_this_month = apps.filter(status='joined', joined_at__gte=start_of_month).count()

        # 2. Job Health Intelligence
        jobs_at_risk = []
        for job in active_jobs:
            # Quick check before deep intelligence to keep it performant
            job_apps_count = Application.objects.filter(requisition_id=job.id, is_deleted=False).count()
            if job_apps_count < job.headcount * 2: # Thin pipeline
                intel = JobIntelligenceEngine.get_job_intelligence(tenant_id, job.id)
                if intel['health']['label'] in ('Critical', 'At Risk'):
                    jobs_at_risk.append({
                        'id': str(job.id),
                        'title': job.title,
                        'reason': intel['health']['factors'][0]['name'] if intel['health']['factors'] else 'Low Health Score',
                        'health_score': intel['health']['score'],
                        'risk_level': intel['fill_risk']['risk_level']
                    })

        # 3. Pipeline Intelligence
        # Aggregate global bottlenecks
        bottlenecks = []
        for job in active_jobs[:10]: # Limit to top 10 for performance
            intel = JobIntelligenceEngine.get_job_intelligence(tenant_id, job.id)
            if intel['bottlenecks']:
                for b in intel['bottlenecks']:
                    bottlenecks.append({
                        'job_title': job.title,
                        **b
                    })
        
        # Simple count of stuck candidates for now
        stuck_candidates = apps.filter(status__in=['applied', 'screening', 'shortlisted'], updated_at__lt=now - timedelta(days=5)).count()

        # 4. Performance Intelligence
        recruiters = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
        agencies = AgencyIntelligenceService.get_global_agency_stats(tenant_id)

        # 5. Candidate Intelligence (Global Summary)
        candidates = Candidate.objects.filter(tenant_id=tenant_id, is_deleted=False)
        strong_candidates = candidates.filter(fit_score__gt=80).count()
        fast_hire_candidates = apps.filter(status='active', updated_at__gt=now - timedelta(days=3)).count()

        return {
            'overview': {
                'active_jobs': total_active_jobs,
                'open_positions': open_positions,
                'candidates_in_pipeline': total_in_pipeline,
                'interviews_scheduled': interviews_scheduled,
                'offers_pending': offers_pending,
                'hires_this_month': hires_this_month
            },
            'job_health': {
                'at_risk_count': len(jobs_at_risk),
                'at_risk_details': jobs_at_risk[:5],
                'stuck_jobs': active_jobs.filter(created_at__lt=now - timedelta(days=60)).count(),
                'slow_moving_jobs': active_jobs.filter(updated_at__lt=now - timedelta(days=14)).count()
            },
            'pipeline_intelligence': {
                'stalled_candidates': pipeline_snapshot.get('signals', {}).get('stuck_stage', stuck_candidates),
                'bottlenecks': bottlenecks,
                'avg_time_to_hire_days': 24, # Keep existing contract for phase compatibility
                'stage_conversion_rates': {
                    'applied_to_shortlist': 15, # Keep existing contract for phase compatibility
                    'shortlist_to_interview': 40,
                    'interview_to_offer': 20
                }
            },
            'performance': {
                'recruiters': recruiters[:5],
                'agencies': agencies[:5]
            },
            'candidate_intelligence': {
                'strong_candidates': strong_candidates,
                'fast_hire_potential': fast_hire_candidates,
                'stalled_candidates': stuck_candidates,
                'high_potential': candidates.filter(readiness_score__gt=80).count()
            },
            'substrate': global_snapshot.get('signals', {}),
        }
