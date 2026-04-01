from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.jobs.models import JobRequisition, JobPosting
from apps.candidates.models import Candidate
from apps.pipeline.models import Application
from apps.interviews.models import Interview, InterviewFeedback, InterviewDecision
from apps.agencies.models import AgencyJobAssignment
from apps.core.responses import success_response, error_response


from apps.jobs.services import GlobalHiringCommandCenterService


class HiringIntelligenceDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # RBAC: Leadership, Admins, Hiring Managers, and Recruiters can see this.
        # Hide from Candidate and Guest roles.
        allowed_roles = ['super_admin', 'tenant_admin', 'hr_manager', 'hiring_manager', 'recruiter']
        if request.user.role not in allowed_roles and not request.user.is_staff:
            return error_response(
                "You do not have permission to access the Hiring Intelligence Dashboard.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            intelligence = GlobalHiringCommandCenterService.get_global_intelligence(
                tenant_id=request.user.tenant_id
            )
            return success_response(
                data={'intelligence': intelligence},
                message="Hiring Intelligence Dashboard data retrieved."
            )
        except Exception as e:
            return error_response(str(e))


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # Jobs metrics
        total_jobs = JobRequisition.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).count()
        active_jobs = JobRequisition.objects.filter(
            tenant_id=tenant_id, status='active', is_deleted=False
        ).count()
        jobs_this_month = JobRequisition.objects.filter(
            tenant_id=tenant_id, created_at__gte=thirty_days_ago, is_deleted=False
        ).count()

        # Candidates metrics
        total_candidates = Candidate.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).count()
        new_candidates = Candidate.objects.filter(
            tenant_id=tenant_id, created_at__gte=thirty_days_ago, is_deleted=False
        ).count()

        # Applications metrics
        total_applications = Application.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).count()
        applications_by_status = Application.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values('status').annotate(count=Count('id'))

        # Interviews metrics
        scheduled_interviews = Interview.objects.filter(
            tenant_id=tenant_id, status='scheduled', is_deleted=False
        ).count()
        completed_interviews = Interview.objects.filter(
            tenant_id=tenant_id, status='completed', is_deleted=False
        ).count()

        return success_response(
            data={
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs,
                    'this_month': jobs_this_month,
                },
                'candidates': {
                    'total': total_candidates,
                    'new_this_month': new_candidates,
                },
                'applications': {
                    'total': total_applications,
                    'by_status': list(applications_by_status),
                },
                'interviews': {
                    'scheduled': scheduled_interviews,
                    'completed': completed_interviews,
                },
            },
            message="Dashboard metrics retrieved."
        )


class RecruitmentAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['super_admin', 'tenant_admin', 'hr_manager'] and not request.user.is_staff:
            return error_response("You do not have permission to view analytics.", status_code=status.HTTP_403_FORBIDDEN)

        tenant_id = request.user.tenant_id

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        department_id = request.query_params.get('department_id')

        apps_qs = Application.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        )

        if start_date:
            apps_qs = apps_qs.filter(created_at__gte=start_date)
        if end_date:
            apps_qs = apps_qs.filter(created_at__lte=end_date)
        
        if department_id:
            # Filter applications by jobs in that department
            req_ids = JobRequisition.objects.filter(
                tenant_id=tenant_id, 
                department_id=department_id
            ).values_list('id', flat=True)
            apps_qs = apps_qs.filter(requisition_id__in=req_ids)

        # Funnel
        total = apps_qs.count()
        shortlisted = apps_qs.filter(status='shortlisted').count()
        interviewed = apps_qs.filter(status='interview').count()
        offered = apps_qs.filter(status='offer').count()
        joined = apps_qs.filter(status='joined').count()
        rejected = apps_qs.filter(status='rejected').count()

        # Source breakdown
        by_source = apps_qs.values('source').annotate(count=Count('id'))

        return success_response(
            data={
                'funnel': {
                    'total_applications': total,
                    'shortlisted': shortlisted,
                    'interviewed': interviewed,
                    'offered': offered,
                    'joined': joined,
                    'rejected': rejected,
                    'shortlist_rate': round(shortlisted / total * 100, 1) if total else 0,
                    'offer_rate': round(offered / total * 100, 1) if total else 0,
                    'join_rate': round(joined / total * 100, 1) if total else 0,
                },
                'by_source': list(by_source),
            },
            message="Recruitment analytics retrieved."
        )


class PipelineAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id

        # Applications by stage across all jobs
        by_status = Application.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values('status').annotate(count=Count('id'))

        # Jobs with most applications
        top_jobs = Application.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values('requisition_id').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        # Overdue applications (in same stage for 7+ days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        stale = Application.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False,
            updated_at__lte=seven_days_ago,
            status__in=['applied', 'screening', 'shortlisted']
        ).count()

        return success_response(
            data={
                'by_status': list(by_status),
                'top_jobs_by_applications': list(top_jobs),
                'stale_applications': stale,
            },
            message="Pipeline analytics retrieved."
        )


class AgencyAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id

        # Agency submissions breakdown
        agency_submissions = Application.objects.filter(
            tenant_id=tenant_id,
            is_agency_submission=True,
            is_deleted=False
        ).values('agency_id').annotate(
            total=Count('id'),
            shortlisted=Count('id', filter=Q(status='shortlisted')),
            joined=Count('id', filter=Q(status='joined')),
        ).order_by('-total')

        return success_response(
            data={'agency_submissions': list(agency_submissions)},
            message="Agency analytics retrieved."
        )


class CandidateAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id

        # Candidates by source
        by_source = Candidate.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values('source').annotate(count=Count('id'))

        # Skills distribution
        # Note: skills is a JSONField array — basic count
        total_candidates = Candidate.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).count()

        actively_looking = Candidate.objects.filter(
            tenant_id=tenant_id,
            is_deleted=False,
            is_actively_looking=True
        ).count()

        return success_response(
            data={
                'total': total_candidates,
                'actively_looking': actively_looking,
                'by_source': list(by_source),
            },
            message="Candidate analytics retrieved."
        )


class InterviewAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id

        by_status = Interview.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values('status').annotate(count=Count('id'))

        by_type = Interview.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values('interview_type').annotate(count=Count('id'))

        avg_score = Interview.objects.filter(
            tenant_id=tenant_id,
            status='completed',
            overall_score__isnull=False,
            is_deleted=False
        ).aggregate(avg=Avg('overall_score'))

        return success_response(
            data={
                'by_status': list(by_status),
                'by_type': list(by_type),
                'average_score': avg_score['avg'],
            },
            message="Interview analytics retrieved."
        )


class InterviewIntelligenceAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        interview_type = request.query_params.get('interview_type')
        interviewer_id = request.query_params.get('interviewer_id')

        if start_date and not parse_date(start_date):
            return error_response("start_date must be in YYYY-MM-DD format.")
        if end_date and not parse_date(end_date):
            return error_response("end_date must be in YYYY-MM-DD format.")

        apps_qs = Application.objects.filter(tenant_id=tenant_id, is_deleted=False)
        interviews_qs = Interview.objects.filter(tenant_id=tenant_id, is_deleted=False)
        feedback_qs = InterviewFeedback.objects.filter(tenant_id=tenant_id, is_deleted=False)
        decisions_qs = InterviewDecision.objects.filter(tenant_id=tenant_id)

        if start_date:
            apps_qs = apps_qs.filter(created_at__date__gte=start_date)
            interviews_qs = interviews_qs.filter(created_at__date__gte=start_date)
            feedback_qs = feedback_qs.filter(created_at__date__gte=start_date)
            decisions_qs = decisions_qs.filter(created_at__date__gte=start_date)
        if end_date:
            apps_qs = apps_qs.filter(created_at__date__lte=end_date)
            interviews_qs = interviews_qs.filter(created_at__date__lte=end_date)
            feedback_qs = feedback_qs.filter(created_at__date__lte=end_date)
            decisions_qs = decisions_qs.filter(created_at__date__lte=end_date)
        if interview_type:
            interviews_qs = interviews_qs.filter(interview_type=interview_type)
            feedback_qs = feedback_qs.filter(interview_id__in=interviews_qs.values_list('id', flat=True))
            decisions_qs = decisions_qs.filter(interview_id__in=interviews_qs.values_list('id', flat=True))
        if interviewer_id:
            feedback_qs = feedback_qs.filter(panelist_id=interviewer_id)

        applied = apps_qs.filter(status='applied').count()
        prequalified = apps_qs.filter(status__in=['screening', 'shortlisted', 'interview', 'offer', 'joined']).count()
        interviewed = apps_qs.filter(status='interview').count()
        shortlisted = apps_qs.filter(status='shortlisted').count()
        offered = apps_qs.filter(status='offer').count()
        hired = apps_qs.filter(status='joined').count()
        rejected = apps_qs.filter(status='rejected').count()

        total_apps = apps_qs.count()
        interview_success_rate = round((offered / interviewed * 100), 1) if interviewed else 0
        rejection_rate = round((rejected / total_apps * 100), 1) if total_apps else 0
        conversion = {
            'applied_to_prequalified': round((prequalified / applied * 100), 1) if applied else 0,
            'prequalified_to_interviewed': round((interviewed / prequalified * 100), 1) if prequalified else 0,
            'interviewed_to_shortlisted': round((shortlisted / interviewed * 100), 1) if interviewed else 0,
            'shortlisted_to_offer': round((offered / shortlisted * 100), 1) if shortlisted else 0,
            'offer_to_hired': round((hired / offered * 100), 1) if offered else 0,
            'interview_success_rate': interview_success_rate,
            'rejection_rate': rejection_rate,
        }

        interviewer_stats = []
        grouped_feedback = feedback_qs.values('panelist_id').annotate(
            total=Count('id'),
            avg_score=Avg('score'),
            pass_count=Count('id', filter=Q(recommendation__in=['hire', 'next_round'])),
            reject_count=Count('id', filter=Q(recommendation='reject')),
        )
        for row in grouped_feedback:
            total = row['total'] or 0
            interviewer_stats.append({
                'interviewer_id': str(row['panelist_id']),
                'total_feedback': total,
                'average_score': row['avg_score'],
                'pass_rate': round((row['pass_count'] / total * 100), 1) if total else 0,
                'reject_rate': round((row['reject_count'] / total * 100), 1) if total else 0,
            })

        app_map = {str(a.id): a for a in apps_qs}
        time_to_interview_hours = []
        rounds_by_application = {}
        for iv in interviews_qs.exclude(scheduled_at__isnull=True):
            app = app_map.get(str(iv.application_id))
            if app:
                delta = iv.scheduled_at - app.created_at
                time_to_interview_hours.append(delta.total_seconds() / 3600)
            rounds_by_application.setdefault(str(iv.application_id), []).append(iv)

        time_between_rounds_hours = []
        for arr in rounds_by_application.values():
            sorted_arr = sorted(arr, key=lambda x: (x.interview_round, x.scheduled_at or timezone.now()))
            for idx in range(1, len(sorted_arr)):
                prev = sorted_arr[idx - 1].scheduled_at
                curr = sorted_arr[idx].scheduled_at
                if prev and curr:
                    time_between_rounds_hours.append((curr - prev).total_seconds() / 3600)

        time_to_hire_hours = []
        for app in apps_qs.filter(status='joined'):
            joined_at = app.joined_at or app.updated_at
            time_to_hire_hours.append((joined_at - app.created_at).total_seconds() / 3600)

        type_rows = interviews_qs.values('interview_type').annotate(total=Count('id'))
        decision_map = {}
        for row in decisions_qs.values('interview_id', 'decision'):
            decision_map[str(row['interview_id'])] = row['decision']
        type_analytics = []
        for row in type_rows:
            itype = row['interview_type']
            ids = list(interviews_qs.filter(interview_type=itype).values_list('id', flat=True))
            success = 0
            for iv_id in ids:
                if decision_map.get(str(iv_id)) in {'hire', 'next_round'}:
                    success += 1
            total = row['total'] or 0
            type_analytics.append({
                'interview_type': itype,
                'total': total,
                'success': success,
                'success_rate': round((success / total * 100), 1) if total else 0,
            })

        drop_off = {
            'no_show': interviews_qs.filter(status='no_show').count(),
            'incomplete_interview': interviews_qs.filter(status='in_progress').count(),
            'rejected_after_stage': apps_qs.filter(status='rejected').count(),
        }

        return success_response(
            data={
                'funnel': {
                    'applied': applied,
                    'prequalified': prequalified,
                    'interviewed': interviewed,
                    'shortlisted': shortlisted,
                    'offer': offered,
                    'hired': hired,
                },
                'conversion': conversion,
                'interviewer_analytics': interviewer_stats,
                'time_analytics': {
                    'time_to_interview_hours': round(sum(time_to_interview_hours) / len(time_to_interview_hours), 1) if time_to_interview_hours else 0,
                    'time_between_rounds_hours': round(sum(time_between_rounds_hours) / len(time_between_rounds_hours), 1) if time_between_rounds_hours else 0,
                    'time_to_hire_hours': round(sum(time_to_hire_hours) / len(time_to_hire_hours), 1) if time_to_hire_hours else 0,
                },
                'interview_type_analytics': type_analytics,
                'candidate_drop_off': drop_off,
                'integration': {
                    'flow_engine': True,
                    'scorecard_engine': True,
                    'decision_engine': True,
                    'scheduling_engine': True,
                },
            },
            message="Interview intelligence analytics retrieved.",
        )

from apps.accounts.services import RecruiterIntelligenceService

class RecruiterIntelligenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        allowed_roles = ['super_admin', 'tenant_admin', 'hr_manager', 'hiring_manager']
        if request.user.role not in allowed_roles and not request.user.is_staff:
            return error_response(
                "You do not have permission to access Recruiter Intelligence.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            tenant_id = request.user.tenant_id
            
            # Overview/Performance (the team list)
            team_intelligence = RecruiterIntelligenceService.get_team_intelligence(tenant_id)
            
            # We can calculate global workload balance here
            total_active = sum(r['workload']['active_candidates'] for r in team_intelligence)
            overloaded = sum(1 for r in team_intelligence if r['workload']['workload_status'] == 'overloaded')
            balanced = sum(1 for r in team_intelligence if r['workload']['workload_status'] == 'balanced')
            underutilized = sum(1 for r in team_intelligence if r['workload']['workload_status'] == 'underutilized')
            
            # Assignments/Recommendations (For jobs that are currently active and unassigned or assigned to overloaded)
            jobs = JobRequisition.objects.filter(tenant_id=tenant_id, status='active', is_deleted=False)
            job_recommendations = []
            for job in jobs[:10]: # Limit for performance
                is_unassigned = not job.recruiter_id
                is_overloaded = False
                if not is_unassigned:
                    for r in team_intelligence:
                        if r['user_id'] == str(job.recruiter_id) and r['workload']['workload_status'] == 'overloaded':
                            is_overloaded = True
                            break
                
                if is_unassigned or is_overloaded:
                    recs = RecruiterIntelligenceService.get_assignment_recommendations(job.id, tenant_id)
                    job_recommendations.append({
                        'job_id': str(job.id),
                        'job_title': job.title,
                        'current_recruiter_id': str(job.recruiter_id) if job.recruiter_id else None,
                        'reason': 'Unassigned' if is_unassigned else 'Current recruiter overloaded',
                        'recommendations': recs
                    })

            data = {
                'team_performance': team_intelligence,
                'workload_overview': {
                    'total_active_candidates': total_active,
                    'overloaded_count': overloaded,
                    'balanced_count': balanced,
                    'underutilized_count': underutilized,
                },
                'job_recommendations': job_recommendations
            }

            return success_response(data=data, message="Recruiter Intelligence retrieved.")
        except Exception as e:
            import traceback
            print(traceback.format_exc()) # Log to console for debugging
            return error_response(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

