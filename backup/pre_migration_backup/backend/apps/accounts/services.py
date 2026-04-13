import uuid
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import CustomUser
from apps.pipeline.models import Application, ApplicationStageHistory, ActionDeadline
from apps.jobs.models import JobRequisition

class RecruiterIntelligenceService:
    @staticmethod
    def calculate_recruiter_metrics(tenant_id, user_id):
        """
        Calculates performance metrics for a specific recruiter using real data.
        """
        now = timezone.now()
        
        # 1. Job Assignments
        jobs_assigned = JobRequisition.objects.filter(
            tenant_id=tenant_id,
            recruiter_id=user_id,
            is_deleted=False
        ).count()

        # 2. Handling metrics
        apps = Application.objects.filter(
            tenant_id=tenant_id,
            metadata__assigned_owner_id=str(user_id),
            is_deleted=False
        )
        
        total_handled = apps.count()
        
        # Outcomes
        stats = apps.aggregate(
            submissions=Count('id', filter=Q(status__in=['sourcing', 'screening', 'shortlisted', 'interview', 'offer', 'joined', 'rejected'])),
            shortlisted=Count('id', filter=Q(status__in=['shortlisted', 'interview', 'offer', 'joined'])),
            interviewed=Count('id', filter=Q(status__in=['interview', 'offer', 'joined'])),
            offered=Count('id', filter=Q(status__in=['offer', 'joined'])),
            joined=Count('id', filter=Q(status='joined')),
        )

        total = stats['submissions'] or 1
        
        # 3. Speed metrics (Average days to first move after application)
        # Using a heuristic approximation based on updated_at for active candidates
        recent_apps = apps.filter(created_at__gte=now - timedelta(days=30))
        speed_stats = recent_apps.exclude(status='applied').aggregate(
            avg_response=Avg(F('updated_at') - F('created_at'))
        )
        avg_response_delta = speed_stats.get('avg_response')
        avg_response_hours = 24.5
        if avg_response_delta is not None:
            # Handle both timedelta objects and potential numeric values depending on DB backend
            if hasattr(avg_response_delta, 'total_seconds'):
                avg_response_hours = avg_response_delta.total_seconds() / 3600
            else:
                # Some DBs return seconds or microseconds as float
                avg_response_hours = float(avg_response_delta) / 3600

        # 4. Action Deadlines
        overdue_actions = ActionDeadline.objects.filter(
            tenant_id=tenant_id,
            assigned_to=user_id,
            status__in=['pending', 'reminded', 'escalated'],
            deadline_at__lt=now
        ).count()

        metrics = {
            'jobs_assigned': jobs_assigned,
            'total_handled': total_handled,
            'submissions': stats['submissions'],
            'shortlisted_count': stats['shortlisted'],
            'interviewed_count': stats['interviewed'],
            'offered_count': stats['offered'],
            'joined_count': stats['joined'],
            'shortlist_rate': (stats['shortlisted'] / total) * 100,
            'interview_rate': (stats['interviewed'] / total) * 100,
            'offer_rate': (stats['offered'] / total) * 100,
            'hire_rate': (stats['joined'] / total) * 100,
            'avg_response_hours': round(avg_response_hours, 1),
            'overdue_actions': overdue_actions,
        }

        # 5. Overall Score (0-100)
        # Quality + Speed + Conversion
        score = (metrics['shortlist_rate'] * 0.1) + \
                (metrics['interview_rate'] * 0.2) + \
                (metrics['hire_rate'] * 0.4) + \
                (max(0, 100 - (avg_response_hours * 2)) * 0.2) + \
                (max(0, 100 - (overdue_actions * 10)) * 0.1)
                
        metrics['overall_score'] = round(min(score, 100), 1)

        return metrics

    @staticmethod
    def get_recruiter_workload(tenant_id, user_id):
        """
        Detects workload and risks for a specific recruiter.
        """
        now = timezone.now()
        active_apps = Application.objects.filter(
            tenant_id=tenant_id,
            metadata__assigned_owner_id=str(user_id),
            is_deleted=False
        ).exclude(status__in=['joined', 'rejected', 'withdrawn'])
        
        active_count = active_apps.count()
        stalled_candidates = active_apps.filter(updated_at__lt=now - timedelta(days=5)).count()
        
        overdue_actions = ActionDeadline.objects.filter(
            tenant_id=tenant_id,
            assigned_to=user_id,
            status__in=['pending', 'reminded', 'escalated'],
            deadline_at__lt=now
        ).count()

        # Load status
        status = 'balanced'
        if active_count > 60 or overdue_actions > 10: 
            status = 'overloaded'
        elif active_count < 15: 
            status = 'underutilized'
        
        risks = []
        if overdue_actions > 5:
            risks.append({'type': 'high_overdue', 'message': f'{overdue_actions} overdue actions require immediate attention.'})
        if stalled_candidates > (active_count * 0.3) and active_count > 10:
            risks.append({'type': 'stalled_pipeline', 'message': f'{stalled_candidates} active candidates have not moved in 5+ days.'})

        return {
            'active_candidates': active_count,
            'stalled_candidates': stalled_candidates,
            'overdue_actions': overdue_actions,
            'workload_status': status,
            'capacity_percentage': min((active_count / 60) * 100, 100),
            'risks': risks
        }

    @staticmethod
    def get_team_intelligence(tenant_id):
        """
        Lists all recruiters in the tenant with their intelligence.
        """
        recruiters = CustomUser.objects.filter(
            tenant_id=tenant_id,
            role__in=['recruiter', 'hr_manager', 'tenant_admin', 'super_admin'],
            is_active=True,
            is_deleted=False
        )
        
        result = []
        for r in recruiters:
            metrics = RecruiterIntelligenceService.calculate_recruiter_metrics(tenant_id, r.id)
            workload = RecruiterIntelligenceService.get_recruiter_workload(tenant_id, r.id)
            result.append({
                'user_id': str(r.id),
                'full_name': f"{r.first_name} {r.last_name}",
                'email': r.email,
                'role': r.role,
                'score': metrics['overall_score'],
                'metrics': metrics,
                'workload': workload
            })
            
        return sorted(result, key=lambda x: x['score'], reverse=True)

    @staticmethod
    def get_assignment_recommendations(requisition_id, tenant_id):
        """
        Recommends recruiters for a job based on performance, workload, and job specialization.
        """
        job = JobRequisition.objects.filter(id=requisition_id, tenant_id=tenant_id).first()
        team = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
        
        if not team:
            return {'recommended': None, 'avoid': [], 'fallbacks': []}

        # Smart Assignment Logic
        # Boost score if recruiter owns similar jobs
        for r in team:
            domain_bonus = 0
            if job and job.department_id:
                # Mock domain fit check: if they have assigned jobs in same department
                dept_jobs = JobRequisition.objects.filter(
                    tenant_id=tenant_id,
                    recruiter_id=uuid.UUID(r['user_id']),
                    department_id=job.department_id,
                    is_deleted=False
                ).count()
                if dept_jobs > 0:
                    domain_bonus = 15

            r['assignment_score'] = (r['score'] * 0.5) + ((100 - r['workload']['capacity_percentage']) * 0.3) + domain_bonus
        
        sorted_team = sorted(team, key=lambda x: x['assignment_score'], reverse=True)
        
        avoid = [r for r in sorted_team if r['workload']['workload_status'] == 'overloaded']
        available = [r for r in sorted_team if r['workload']['workload_status'] != 'overloaded']
        
        recommended = available[0] if available else (sorted_team[0] if sorted_team else None)
        fallbacks = available[1:4] if len(available) > 1 else []
        
        def format_recruiter(r, reason):
            return {
                'user_id': r['user_id'],
                'full_name': r['full_name'],
                'score': r['score'],
                'workload_status': r['workload']['workload_status'],
                'active_candidates': r['workload']['active_candidates'],
                'reason': reason
            }

        return {
            'recommended': format_recruiter(recommended, 'Optimal performance and capacity balance.') if recommended else None,
            'fallbacks': [format_recruiter(f, 'Good alternative with available capacity.') for f in fallbacks],
            'avoid': [format_recruiter(a, 'Currently overloaded with candidates or overdue actions.') for a in avoid]
        }
