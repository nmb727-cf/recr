from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Avg, Sum

from apps.jobs.models import JobRequisition
from apps.pipeline.models import Application, ActionDeadline
from apps.interviews.models import Interview
from apps.automation.models import AutomationLog
from apps.agencies.services import AgencyIntelligenceService
from apps.accounts.services import RecruiterIntelligenceService
from apps.jobs.services import GlobalHiringCommandCenterService

class UnifiedOperationsService:
    @staticmethod
    def get_unified_operations_data(tenant_id):
        now = timezone.now()
        
        # 1. Base Intelligence from other services
        hiring_intel = GlobalHiringCommandCenterService.get_global_intelligence(tenant_id)
        recruiter_intel = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
        agency_intel = AgencyIntelligenceService.get_global_agency_stats(tenant_id)
        
        # 2. Executive Summary
        summary = {
            'total_active_load': hiring_intel['overview']['active_jobs'],
            'total_in_pipeline': hiring_intel['overview']['candidates_in_pipeline'],
            'urgent_actions': ActionDeadline.objects.filter(
                tenant_id=tenant_id, 
                completed_at__isnull=True, 
                deadline_at__lt=now,
                status='pending'
            ).count(),
            'system_health_score': 88, # Heuristic for now
        }

        # 3. Operational Health (Module Statuses)
        health = {
            'jobs': 'healthy' if hiring_intel['job_health']['at_risk_count'] < 3 else 'warning',
            'pipeline': 'warning' if hiring_intel['pipeline_intelligence']['stalled_candidates'] > 10 else 'healthy',
            'team': 'healthy' if all(r['workload']['workload_status'] != 'overloaded' for r in recruiter_intel) else 'warning',
            'agencies': 'healthy' if len([a for a in agency_intel if a['score'] < 45]) == 0 else 'warning',
            'automation': 'healthy', # Default
        }

        # 4. Cross-Module Risks
        risks = []
        # Job + Recruiter Risk
        overloaded_recruiters = [r for r in recruiter_intel if r['workload']['workload_status'] == 'overloaded']
        for r in overloaded_recruiters:
            risks.append({
                'severity': 'high',
                'module': 'Team',
                'title': f"Recruiter {r['full_name']} Overloaded",
                'impact': f"Impacts {r['workload']['active_candidates']} active candidates across multiple jobs.",
                'owner': r['full_name'],
                'suggested_action': 'Reassign high-priority jobs to balanced recruiters.'
            })

        # Job + Agency Risk
        weak_agencies = [a for a in agency_intel if a['score'] < 45]
        for a in weak_agencies:
            risks.append({
                'severity': 'medium',
                'module': 'Agency',
                'title': f"Underperforming Agency: {a['agency_name']}",
                'impact': "Low conversion rate affecting sourcing top of funnel.",
                'owner': 'Talent Ops',
                'suggested_action': 'Review agency partnership or move to probation tier.'
            })

        # Pipeline + SLA Risk
        stalled_count = hiring_intel['pipeline_intelligence']['stalled_candidates']
        if stalled_count > 5:
            risks.append({
                'severity': 'high',
                'module': 'Pipeline',
                'title': f"{stalled_count} Stalled Candidates",
                'impact': "High risk of candidate withdrawal due to slow response.",
                'owner': 'Hiring Managers',
                'suggested_action': 'Batch review stuck candidates in screening stage.'
            })

        # 5. Team / Recruiter Load Overview
        workload = {
            'total_recruiters': len(recruiter_intel),
            'overloaded': len(overloaded_recruiters),
            'balanced': len([r for r in recruiter_intel if r['workload']['workload_status'] == 'balanced']),
            'underutilized': len([r for r in recruiter_intel if r['workload']['workload_status'] == 'underutilized']),
        }

        # 6. Interview / Decision Delays
        pending_feedback = Interview.objects.filter(
            tenant_id=tenant_id, 
            status='completed', 
            overall_score__isnull=True,
            is_deleted=False
        ).count()
        
        # 7. SLA / Automation Health
        auto_logs = AutomationLog.objects.filter(tenant_id=tenant_id, is_deleted=False)
        total_auto = auto_logs.count()
        failed_auto = auto_logs.filter(status='failed').count()
        
        automation_health = {
            'success_rate': round(((total_auto - failed_auto) / total_auto * 100) if total_auto else 100, 1),
            'failed_last_24h': auto_logs.filter(status='failed', executed_at__gte=now - timedelta(days=1)).count(),
        }

        # 8. Recommended Interventions
        interventions = []
        if workload['overloaded'] > 0:
            interventions.append({
                'type': 'reassignment',
                'title': 'Recruiter Workload Balancing',
                'description': f'Shift load from {workload["overloaded"]} overloaded recruiters to {workload["underutilized"]} underutilized team members.'
            })
        if stalled_count > 10:
            interventions.append({
                'type': 'workflow',
                'title': 'Pipeline Purge Required',
                'description': 'Automate rejection for candidates stalled for > 14 days to clean up pipeline noise.'
            })
        if hiring_intel['job_health']['at_risk_count'] > 0:
            interventions.append({
                'type': 'sourcing',
                'title': 'Emergency Sourcing Injection',
                'description': f'Trigger external agency distribution for {hiring_intel["job_health"]["at_risk_count"]} at-risk jobs.'
            })

        return {
            'summary': summary,
            'health': health,
            'risks': risks,
            'workload': workload,
            'interviews': {
                'pending_feedback': pending_feedback,
                'scheduled_today': Interview.objects.filter(tenant_id=tenant_id, scheduled_at__date=now.date(), is_deleted=False).count(),
            },
            'automation': automation_health,
            'interventions': interventions,
            'last_updated': now.isoformat()
        }
