from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.jobs.models import JobRequisition, JobPosting
from apps.candidates.models import Candidate
from apps.pipeline.models import Application
from apps.interviews.models import Interview
from apps.agencies.models import AgencyJobAssignment
from apps.core.responses import success_response, error_response


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