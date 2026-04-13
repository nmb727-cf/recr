from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Sum

from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application, ActionDeadline
from apps.interviews.models import Interview
from apps.agencies.services import AgencyIntelligenceService
from apps.accounts.services import RecruiterIntelligenceService
from apps.jobs.services import GlobalHiringCommandCenterService

class ExecutiveDecisionService:
    @staticmethod
    def get_executive_decision_data(tenant_id):
        now = timezone.now()
        
        # 1. Base Intelligence
        hiring_intel = GlobalHiringCommandCenterService.get_global_intelligence(tenant_id)
        recruiter_intel = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
        agency_intel = AgencyIntelligenceService.get_global_agency_stats(tenant_id)
        
        # Determine Critical & At-Risk Jobs
        active_jobs = JobRequisition.objects.filter(tenant_id=tenant_id, status='active', is_deleted=False)
        critical_jobs_qs = active_jobs.filter(priority__in=['high', 'urgent'])
        
        critical_hiring = []
        open_headcount_sum = 0
        
        for job in active_jobs:
            open_headcount_sum += job.headcount
            if job.priority in ['high', 'urgent']:
                job_apps = Application.objects.filter(requisition_id=job.id, tenant_id=tenant_id, is_deleted=False)
                filled = job_apps.filter(status='joined').count()
                days_open = (now - job.created_at).days
                
                # Risk logic: open > 30 days and filled < headcount
                risk_state = 'At Risk' if days_open > 30 and filled < job.headcount else 'On Track'
                if not job_apps.exists():
                    risk_state = 'Critical'
                    
                critical_hiring.append({
                    'id': str(job.id),
                    'title': job.title,
                    'priority': job.priority,
                    'headcount': job.headcount,
                    'filled': filled,
                    'days_open': days_open,
                    'risk_state': risk_state,
                    'owner': 'Talent Team', # Should be hiring manager if available
                })

        # 2. Executive Summary
        summary = {
            'critical_roles_open': critical_jobs_qs.count(),
            'total_open_headcount': open_headcount_sum,
            'bottlenecked_decisions': ActionDeadline.objects.filter(
                tenant_id=tenant_id, 
                completed_at__isnull=True, 
                deadline_at__lt=now,
                status='pending'
            ).count(),
            'hiring_velocity': hiring_intel['pipeline_intelligence'].get('avg_time_to_hire_days', 0)
        }

        # 3. Decision Bottlenecks
        bottlenecks = []
        # Pending action deadlines
        overdue_actions = ActionDeadline.objects.filter(
            tenant_id=tenant_id, 
            completed_at__isnull=True, 
            deadline_at__lt=now, 
            status='pending'
        ).order_by('deadline_at')[:5]
        for action in overdue_actions:
            bottlenecks.append({
                'item': action.action_required,
                'blocker': 'SLA Overdue',
                'owner': str(action.assigned_to) if action.assigned_to else 'Unassigned',
                'age_days': (now - action.deadline_at).days,
                'suggested_step': 'Escalate to Department Head'
            })
            
        # Stalled candidates
        stalled = hiring_intel['pipeline_intelligence']['stalled_candidates']
        if stalled > 0:
            bottlenecks.append({
                'item': f'{stalled} Candidates Stalled in Pipeline',
                'blocker': 'Pending Review or Interview Feedback',
                'owner': 'Hiring Managers',
                'age_days': 5, # Threshold
                'suggested_step': 'Batch Review / Reject'
            })

        # 4. Team Capacity / Performance
        team_capacity = {
            'overloaded_recruiters': len([r for r in recruiter_intel if r['workload']['workload_status'] == 'overloaded']),
            'underutilized_recruiters': len([r for r in recruiter_intel if r['workload']['workload_status'] == 'underutilized']),
            'top_performers': sorted(recruiter_intel, key=lambda x: x['workload']['active_candidates'], reverse=True)[:3]
        }

        # 5. Agency / Source Effectiveness
        weak_agencies = [a for a in agency_intel if a['score'] < 45]
        top_agencies = sorted(agency_intel, key=lambda x: x['score'], reverse=True)[:3]
        
        agency_effectiveness = {
            'top_agencies': top_agencies,
            'weak_agencies': weak_agencies,
            'source_mix': 'Needs Diversification' if len(agency_intel) < 2 else 'Healthy'
        }

        # 6. Intervention Recommendations
        interventions = []
        if team_capacity['overloaded_recruiters'] > 0:
            interventions.append({
                'title': 'Rebalance recruiter workload',
                'description': 'Some recruiters are overloaded while others have capacity.',
                'action_type': 'rebalance'
            })
        if critical_jobs_qs.filter(created_at__lt=now - timedelta(days=45)).exists():
            interventions.append({
                'title': 'Widen agency distribution',
                'description': 'Critical roles (>45 days open) are aging without sufficient pipeline.',
                'action_type': 'sourcing'
            })
        if len(weak_agencies) > 0:
            interventions.append({
                'title': f'Review partnership with {len(weak_agencies)} underperforming agencies',
                'description': 'Low conversion rates impacting top-of-funnel quality.',
                'action_type': 'partnership'
            })
        if stalled > 10:
            interventions.append({
                'title': 'Enforce SLAs on Hiring Managers',
                'description': 'High volume of stalled candidates pending review.',
                'action_type': 'workflow'
            })

        return {
            'summary': summary,
            'critical_hiring': critical_hiring,
            'bottlenecks': bottlenecks,
            'team_capacity': team_capacity,
            'agency_effectiveness': agency_effectiveness,
            'interventions': interventions,
            'last_updated': now.isoformat()
        }
