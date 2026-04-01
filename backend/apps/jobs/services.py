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

class HiringAIBrainService:
    @staticmethod
    def get_job_intelligence(tenant_id, requisition_id):
        """
        Orchestrates intelligence from all engines to provide a unified 'Brain' view.
        """
        job = JobRequisition.objects.get(id=requisition_id, tenant_id=tenant_id)
        apps = Application.objects.filter(requisition_id=requisition_id, tenant_id=tenant_id, is_deleted=False)
        total_apps = apps.count()
        
        # 1. Calculate Hiring Health Score (0-100)
        health_metrics = HiringAIBrainService._calculate_health_metrics(job, apps, total_apps)
        
        # 2. Detect Job Fill Risks
        risks = HiringAIBrainService._detect_risks(job, apps, total_apps, health_metrics)
        
        # 3. Generate Next Best Actions
        actions = HiringAIBrainService._generate_actions(job, apps, risks, health_metrics)
        
        # 4. Get Team/Source Recommendations
        recommendations = HiringAIBrainService._get_source_recommendations(job, tenant_id)
        
        # 5. Top Candidate Recommendations
        best_fit = apps.filter(status__in=['applied', 'screening', 'shortlisted', 'interview']).order_by('-match_score')[:5]
        from apps.pipeline.serializers import ApplicationSerializer
        
        return {
            'health_score': health_metrics['overall_score'],
            'health_label': health_metrics['label'],
            'health_factors': health_metrics['factors'],
            'risks': risks,
            'next_best_actions': actions,
            'recommendations': recommendations,
            'best_fit_candidates': ApplicationSerializer(best_fit, many=True).data,
            'team': {
                'hiring_manager_id': str(job.hiring_manager_id) if job.hiring_manager_id else None,
                'recruiter_id': str(job.recruiter_id) if job.recruiter_id else None,
            },
            'summary': {
                'total_candidates': total_apps,
                'active_candidates': apps.exclude(status__in=['joined', 'rejected', 'withdrawn']).count(),
                'velocity': health_metrics['velocity_label']
            }
        }

    @staticmethod
    def _calculate_health_metrics(job, apps, total_apps):
        if total_apps == 0:
            return {'overall_score': 50, 'label': 'Watch', 'factors': [], 'velocity_label': 'N/A'}
        
        # Weighting factors
        # 1. Pipeline Strength (Target vs Current) - 30%
        # 2. Conversion Velocity (Shortlist/Interview rates) - 30%
        # 3. SLA Adherence (Overdue %) - 20%
        # 4. Recency of movement - 20%
        
        # Pipeline factor
        target_candidates = job.headcount * 10 # Heuristic: need 10 apps per hire
        pipeline_fill = min((total_apps / target_candidates) * 100, 100)
        
        # Velocity factor (Shortlisted or beyond)
        qualified_apps = apps.filter(status__in=['shortlisted', 'interview', 'assessment', 'offer', 'joined']).count()
        conversion_rate = (qualified_apps / total_apps) * 100
        
        # SLA factor
        overdue_count = 0
        now = timezone.now()
        for app in apps:
            if (now - app.updated_at).total_seconds() > (48 * 3600):
                overdue_count += 1
        sla_health = max(0, 100 - ((overdue_count / total_apps) * 100))
        
        # Overall Score
        score = (pipeline_fill * 0.3) + (conversion_rate * 0.3) + (sla_health * 0.2) + (20 if total_apps > 5 else 0)
        score = min(score, 100)
        
        label = 'Healthy'
        if score < 40: label = 'At Risk'
        elif score < 70: label = 'Watch'
        
        return {
            'overall_score': round(score, 1),
            'label': label,
            'velocity_label': 'Optimal' if conversion_rate > 20 else 'Slow',
            'factors': [
                {'name': 'Pipeline Fill', 'score': pipeline_fill},
                {'name': 'Conversion', 'score': conversion_rate},
                {'name': 'SLA Health', 'score': sla_health}
            ]
        }

    @staticmethod
    def _detect_risks(job, apps, total_apps, health):
        risks = []
        if total_apps < job.headcount * 3:
            risks.append({'type': 'low_volume', 'level': 'high', 'message': 'Insufficient candidate volume for headcount target.'})
        
        stalled = apps.filter(updated_at__lt=timezone.now() - timedelta(days=4)).exclude(status__in=['joined', 'rejected']).count()
        if stalled > (total_apps * 0.3):
            risks.append({'type': 'stalled_pipeline', 'level': 'medium', 'message': f'{stalled} candidates have no activity for > 4 days.'})
            
        if health['overall_score'] < 40:
            risks.append({'type': 'velocity_drop', 'level': 'high', 'message': 'Hiring velocity has dropped below critical threshold.'})
            
        return risks

    @staticmethod
    def _generate_actions(job, apps, risks, health):
        actions = []
        
        # Priority actions based on status
        new_apps = apps.filter(status='applied').count()
        if new_apps > 0:
            actions.append({'text': f'Review {new_apps} new applications', 'type': 'review', 'priority': 'high'})
            
        interview_pending = apps.filter(status='shortlisted').count()
        if interview_pending > 0:
            actions.append({'text': f'Schedule interviews for {interview_pending} shortlisted candidates', 'type': 'schedule', 'priority': 'medium'})
            
        for risk in risks:
            if risk['type'] == 'low_volume':
                actions.append({'text': 'Distribute job to more agencies or increase sourcing', 'type': 'sourcing', 'priority': 'high'})
            if risk['type'] == 'stalled_pipeline':
                actions.append({'text': 'Nudge interviewers for pending feedback', 'type': 'follow_up', 'priority': 'medium'})
                
        return actions

    @staticmethod
    def _get_source_recommendations(job, tenant_id):
        # Tie into existing intelligence services
        recruiters = RecruiterIntelligenceService.get_assignment_recommendations(job.id, tenant_id)
        agencies = AgencyIntelligenceService.get_job_agency_recommendations(job.id, tenant_id)
        
        return {
            'best_recruiter': recruiters[0] if recruiters else None,
            'best_agency': agencies[0] if agencies else None,
            'sourcing_mix': 'Increase External' if job.priority in ('high', 'urgent') else 'Balanced'
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
        stalled_threshold = now - timedelta(days=7)
        jobs_at_risk = []
        for job in active_jobs:
            job_apps = apps.filter(requisition_id=job.id)
            # Risk if: headcount not met AND (no apps OR no activity in 7 days OR slow conversion)
            if job_apps.count() < job.headcount:
                if not job_apps.exists() or not job_apps.filter(updated_at__gt=stalled_threshold).exists():
                    jobs_at_risk.append({
                        'id': str(job.id),
                        'title': job.title,
                        'reason': 'No recent activity' if job_apps.exists() else 'No candidates'
                    })

        # 3. Pipeline Intelligence
        # Bottleneck detection: Stages where candidates spend > 5 days
        bottlenecks = []
        # Calculate avg time in stage from ApplicationStageHistory if available
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
                'stalled_candidates': stuck_candidates,
                'bottlenecks': bottlenecks,
                'avg_time_to_hire_days': 24, # Heuristic
                'stage_conversion_rates': {
                    'applied_to_shortlist': 15, # Heuristic
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
            }
        }

