from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Sum
from django.contrib.auth import get_user_model

from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application, ActionDeadline
from apps.interviews.models import Interview
from apps.agencies.models import AgencyPerformanceScore, AgencyJobAssignment
from apps.accounts.services import RecruiterIntelligenceService
from apps.automation.models import AutomationLog
from apps.analytics.ai_brain import HiringAIBrainService
from apps.orchestration_center.models.audit import IntelligenceAuditLog

User = get_user_model()

class ControlTowerService:
    @staticmethod
    def get_control_tower_data(tenant_id, filters=None):
        now = timezone.now()
        filters = filters or {}
        
        # ─── 0. Base Querysets for Filtering ───
        jobs_qs = JobRequisition.objects.filter(tenant_id=tenant_id, is_deleted=False)
        apps_qs = Application.objects.filter(tenant_id=tenant_id, is_deleted=False)
        interviews_qs = Interview.objects.filter(tenant_id=tenant_id, is_deleted=False)
        
        # Apply Global Filters
        if filters.get('department_id'):
            jobs_qs = jobs_qs.filter(department_id=filters['department_id'])
            apps_qs = apps_qs.filter(requisition_id__in=jobs_qs.values_list('id', flat=True))
            interviews_qs = interviews_qs.filter(application_id__in=apps_qs.values_list('id', flat=True))
            
        if filters.get('location'):
            jobs_qs = jobs_qs.filter(location=filters['location'])
            apps_qs = apps_qs.filter(requisition_id__in=jobs_qs.values_list('id', flat=True))
            interviews_qs = interviews_qs.filter(application_id__in=apps_qs.values_list('id', flat=True))
            
        if filters.get('recruiter_id'):
            jobs_qs = jobs_qs.filter(recruiter_id=filters['recruiter_id'])
            apps_qs = apps_qs.filter(requisition_id__in=jobs_qs.values_list('id', flat=True))
            interviews_qs = interviews_qs.filter(application_id__in=apps_qs.values_list('id', flat=True))
            
        if filters.get('agency_id'):
            # Agency filters typically focus on their submissions
            apps_qs = apps_qs.filter(agency_id=filters['agency_id'])
            interviews_qs = interviews_qs.filter(application_id__in=apps_qs.values_list('id', flat=True))
            jobs_qs = jobs_qs.filter(id__in=apps_qs.values_list('requisition_id', flat=True).distinct())

        if filters.get('job_priority'):
            jobs_qs = jobs_qs.filter(priority=filters['job_priority'])
            apps_qs = apps_qs.filter(requisition_id__in=jobs_qs.values_list('id', flat=True))
            interviews_qs = interviews_qs.filter(application_id__in=apps_qs.values_list('id', flat=True))

        if filters.get('job_status'):
            jobs_qs = jobs_qs.filter(status=filters['job_status'])
            apps_qs = apps_qs.filter(requisition_id__in=jobs_qs.values_list('id', flat=True))
            interviews_qs = interviews_qs.filter(application_id__in=apps_qs.values_list('id', flat=True))

        # Time-based Filter
        time_range = filters.get('time_range', 'this_month')
        since_date = None
        if time_range == 'today':
            since_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'this_week':
            since_date = now - timedelta(days=now.weekday())
        elif time_range == 'this_month':
            since_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'custom' and filters.get('start_date'):
            from django.utils.dateparse import parse_datetime
            since_date = parse_datetime(filters['start_date'])

        # 1. Global System Health (Overview)
        active_jobs = jobs_qs.filter(status='active')
        total_active_jobs = active_jobs.count()
        open_headcount = active_jobs.aggregate(Sum('headcount'))['headcount__sum'] or 0
        
        candidates_in_pipeline = apps_qs.filter(
            status__in=['applied', 'screening', 'shortlisted', 'interview', 'assessment', 'offer'],
        ).count()
        
        interviews_scheduled = interviews_qs.filter(
            status='scheduled', 
            scheduled_at__gte=now,
        ).count()
        
        offers_pending = apps_qs.filter(status='offer').count()
        
        hires_count = apps_qs.filter(status='joined')
        if since_date:
            hires_count = hires_count.filter(joined_at__gte=since_date)
        hires_this_month = hires_count.count()

        # 2. Talent Pipeline Health
        pipeline_stages = apps_qs.values('status').annotate(count=Count('id'))
        
        # Risk detection for pipeline
        high_risk_jobs = []
        for job in active_jobs:
            job_apps = apps_qs.filter(requisition_id=job.id)
            if job_apps.count() < job.headcount * 2 and (now - job.created_at).days > 14:
                high_risk_jobs.append({
                    'id': str(job.id),
                    'title': job.title,
                    'risk_reason': 'Low candidate volume',
                    'severity': 'high'
                })

        # 3. Team Capacity
        recruiter_intel = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
        # Simplify recruiter load for control tower
        team_load = {
            'total_recruiters': len(recruiter_intel),
            'overloaded': len([r for r in recruiter_intel if r['workload']['workload_status'] == 'overloaded']),
            'avg_candidates_per_recruiter': round(sum([r['workload']['active_candidates'] for r in recruiter_intel]) / len(recruiter_intel), 1) if recruiter_intel else 0
        }
        
        # HM Bottlenecks (Pending reviews in screening/applied)
        hm_bottlenecks = ActionDeadline.objects.filter(
            tenant_id=tenant_id, 
            status='pending', 
            completed_at__isnull=True,
            deadline_at__lt=now
        ).count()

        # 4. Source Health
        agency_scores = AgencyPerformanceScore.objects.filter(tenant_id=tenant_id).order_by('-overall_score')
        top_agencies = []
        for s in agency_scores[:3]:
            # In a real system, we'd join with the Agency model to get the name
            top_agencies.append({
                'agency_id': str(s.agency_tenant_id),
                'score': float(s.overall_score),
                'hires': s.joined_count
            })
            
        # 5. Automation Health
        auto_logs = AutomationLog.objects.filter(tenant_id=tenant_id, is_deleted=False)
        total_runs = auto_logs.count()
        failed_runs = auto_logs.filter(status='failed').count()
        automation_health = {
            'success_rate': round(((total_runs - failed_runs) / total_runs * 100) if total_runs else 100, 1),
            'failed_count': failed_runs,
            'blocked_actions': ActionDeadline.objects.filter(tenant_id=tenant_id, status='escalated').count()
        }

        # 6. AI Recommendations (Leverage existing brain service)
        ai_brain = HiringAIBrainService.generate_brain_intelligence(tenant_id)

        # 7. Real-Time Activity Feed
        recent_activity = IntelligenceAuditLog.objects.filter(
            tenant_id=tenant_id
        ).order_by('-created_at')[:20]
        activity_feed = []
        for log in recent_activity:
            activity_feed.append({
                'id': log.id,
                'action_type': log.action_type,
                'target_type': log.target_type,
                'target_id': str(log.target_id),
                'metadata': log.metadata_json,
                'created_at': log.created_at.isoformat(),
                'actor_id': str(log.actor_id) if log.actor_id else None
            })

        # 8. Alert & Risk Engine
        alerts = []
        # Critical
        for job in active_jobs.filter(created_at__lt=now - timedelta(days=30)):
            if not apps_qs.filter(requisition_id=job.id).exists():
                alerts.append({
                    'type': 'no_candidates',
                    'severity': 'critical',
                    'title': 'No Candidates',
                    'description': f'Job "{job.title}" has zero candidates after 30 days.',
                    'job_id': str(job.id)
                })
        
        sla_breaches = ActionDeadline.objects.filter(
            tenant_id=tenant_id, status='pending', deadline_at__lt=now
        ).count()
        if sla_breaches > 5:
            alerts.append({
                'type': 'sla_breach',
                'severity': 'critical',
                'title': 'High SLA Breaches',
                'description': f'{sla_breaches} actions are currently past their deadline.',
                'count': sla_breaches
            })

        # High
        if team_load['overloaded'] > 0:
            alerts.append({
                'type': 'recruiter_overloaded',
                'severity': 'high',
                'title': 'Recruiters Overloaded',
                'description': f'{team_load["overloaded"]} recruiters are exceeding their optimal capacity.',
                'count': team_load['overloaded']
            })

        # Medium
        if source_health_gap_count(tenant_id, active_jobs, apps_qs) > 3:
            alerts.append({
                'type': 'sourcing_gap',
                'severity': 'medium',
                'title': 'Weak Pipeline',
                'description': 'Several active jobs have weak candidate pipelines.',
                'count': source_health_gap_count(tenant_id, active_jobs, apps_qs)
            })

        return {
            'system_health': {
                'active_jobs': total_active_jobs,
                'open_headcount': open_headcount,
                'candidates_in_pipeline': candidates_in_pipeline,
                'interviews_scheduled': interviews_scheduled,
                'offers_pending': offers_pending,
                'hires_this_month': hires_this_month
            },
            'pipeline_health': {
                'stages': list(pipeline_stages),
                'high_risk_jobs': high_risk_jobs,
                'alerts': len(high_risk_jobs)
            },
            'team_capacity': {
                'load_summary': team_load,
                'hm_bottlenecks': hm_bottlenecks,
                'panel_availability': 'Normal'
            },
            'source_health': {
                'top_agencies': top_agencies,
                'active_partners': len(agency_scores),
                'sourcing_gap_jobs': source_health_gap_count(tenant_id, active_jobs, apps_qs)
            },
            'automation_health': automation_health,
            'ai_recommendations': ai_brain,
            'activity_feed': activity_feed,
            'alerts': alerts,
            'last_updated': now.isoformat()
        }

def source_health_gap_count(tenant_id, active_jobs, apps_qs):
    count = 0
    for job in active_jobs:
        if not apps_qs.filter(requisition_id=job.id).exists():
            count += 1
    return count
