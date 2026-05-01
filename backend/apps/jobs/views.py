from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.jobs.models import JobRequisition, JobPosting, JobStage, JobDescriptionTemplate, JobLocation
from apps.jobs.serializers import (
    JobRequisitionSerializer, JobPostingSerializer, JobStageSerializer,
    JobDescriptionTemplateSerializer, JobLocationSerializer,
)
from apps.core.responses import success_response, error_response
from apps.core import events
from apps.candidates.protection import mark_direct_apply_during_protection
from apps.rbac.utils import user_has_permission
from drf_spectacular.utils import extend_schema, OpenApiResponse
from shared.tenant_access import TenantAccessMixin, scope_queryset_by_tenant_fields
from shared.actor_access import (
    require_candidate,
    require_non_candidate,
    is_tenant_or_platform_admin,
    is_company_operational_user,
)
from apps.analytics.intelligence_substrate import IntelligenceAggregator
from shared.search_utils import (
    apply_keyword_search,
    get_search_query,
    parse_limit_offset,
    resolve_sort_order,
)


from apps.jobs.services import HiringAIBrainService, GlobalHiringCommandCenterService


def _require_candidate_role(user):
    require_candidate(user, "This endpoint is available only for candidate users.")


def _require_internal_jobs_actor(user):
    require_non_candidate(user, "You do not have permission to access internal job operations.")
    if is_tenant_or_platform_admin(user) or is_company_operational_user(user):
        return
    raise PermissionDenied("You do not have permission to access internal job operations.")


def _require_jobs_permission(user, permission_code: str):
    if is_tenant_or_platform_admin(user):
        return
    if user_has_permission(user, permission_code):
        return
    raise PermissionDenied("You do not have permission to perform this job operation.")

class GlobalHiringCommandCenterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_internal_jobs_actor(request.user)
        try:
            intel = GlobalHiringCommandCenterService.get_global_intelligence(
                tenant_id=request.user.tenant_id
            )
            return success_response(
                data={'intelligence': intel},
                message="Global intelligence retrieved."
            )
        except Exception as e:
            return error_response(str(e))


class HiringAIBrainView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        try:
            intel = HiringAIBrainService.get_job_intelligence(
                tenant_id=request.user.tenant_id,
                requisition_id=pk
            )
            return success_response(
                data={'intelligence': intel},
                message="Job intelligence retrieved."
            )
        except Exception as e:
            return error_response(str(e))


class JobPipelineSnapshotView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        from apps.pipeline.models import Application
        from django.db.models import Count

        requisition = scope_queryset_by_tenant_fields(
            JobRequisition.objects.filter(id=pk, is_deleted=False),
            user=request.user,
            tenant_fields=('tenant_id',),
            allow_platform_admin=True,
        ).first()
        if not requisition:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        stages = JobStage.objects.filter(
            requisition_id=pk,
            tenant_id=requisition.tenant_id,
            is_active=True,
        ).order_by('stage_order')
        app_counts = Application.objects.filter(
            requisition_id=pk,
            tenant_id=requisition.tenant_id,
            is_deleted=False,
        ).values('current_stage_id').annotate(count=Count('id'))
        count_map = {str(c['current_stage_id']): c['count'] for c in app_counts}
        
        stage_data = []
        total_apps = sum(count_map.values())
        substrate_pipeline = IntelligenceAggregator.build_pipeline_intelligence(
            tenant_id=requisition.tenant_id,
            requisition_id=pk,
        )
        substrate_job = IntelligenceAggregator.build_job_intelligence(
            tenant_id=requisition.tenant_id,
            requisition_id=pk,
        )
        bottlenecks = substrate_job.get('signals', {}).get('stage_bottlenecks', [])
        sla_risks = []
        stale_stage_count = substrate_pipeline.get('signals', {}).get('stuck_stage', 0)

        for s in stages:
            sid = str(s.id)
            count = count_map.get(sid, 0)
            is_bottleneck = any(str(b.get('stage_id')) == sid for b in bottlenecks if b.get('stage_id'))
            at_risk_count = stale_stage_count if is_bottleneck else 0
            if at_risk_count:
                sla_risks.append({'stage_id': sid, 'stage_name': s.name, 'at_risk_count': at_risk_count})

            stage_data.append({
                'id': sid,
                'name': s.name,
                'candidate_count': count,
                'is_bottleneck': is_bottleneck,
                'sla_at_risk_count': at_risk_count
            })
            
        return success_response(data={
            'snapshot': {
                'stages': stage_data,
                'bottlenecks': bottlenecks,
                'sla_risks': sla_risks,
                'total_candidates': total_apps
            }
        })


class JobRequisitionListView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_internal_jobs_actor(request.user)
        denied = self.reject_scope_widening(request)
        if denied:
            return denied

        qs = JobRequisition.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )
        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        hiring_status = request.query_params.get('hiring_status')
        if hiring_status:
            qs = qs.filter(hiring_status=hiring_status)

        department_id = request.query_params.get('department_id')
        if department_id:
            qs = qs.filter(department_id=department_id)

        search = get_search_query(request.query_params)
        search_mode = 'none'
        if search:
            qs, search_mode = apply_keyword_search(
                qs,
                query=search,
                fields=(
                    'title',
                    'job_ref_id',
                    'description',
                    'requirements',
                    'responsibilities',
                    'skills_required',
                    'status',
                ),
                typo_tolerant=True,
            )

        limit, offset = parse_limit_offset(request.query_params, default_limit=50, max_limit=200)
        sort_order = resolve_sort_order(
            request.query_params,
            allowed_fields={
                'created_at', 'updated_at', 'title', 'status', 'priority',
                'target_date', 'job_ref_id',
            },
            default_field='created_at',
            default_dir='desc',
        )
        total = qs.count()
        qs = qs.order_by(sort_order)[offset:offset + limit]

        # Get counts from Application model
        from apps.pipeline.models import Application
        
        # Optimize by getting all applications for these requisitions in one go
        apps = Application.objects.filter(requisition_id__in=qs.values_list('id', flat=True), is_deleted=False)
        
        stats_map = {}
        for app in apps:
            rid = str(app.requisition_id)
            if rid not in stats_map:
                stats_map[rid] = {
                    'applications_count': 0,
                    'applied': 0,
                    'screening': 0,
                    'interview': 0,
                    'offer': 0,
                    'joined': 0
                }
            stats_map[rid]['applications_count'] += 1
            status_key = app.status if app.status in stats_map[rid] else None
            if status_key:
                stats_map[rid][status_key] += 1

        requisitions_data = JobRequisitionSerializer(qs, many=True, context={'request': request}).data
        for req in requisitions_data:
            rid = req['id']
            # Ensure metadata exists and inject counts
            if 'metadata' not in req or req['metadata'] is None:
                req['metadata'] = {}
            
            req['metadata'].update(stats_map.get(rid, {
                'applications_count': 0,
                'applied': 0,
                'screening': 0,
                'interview': 0,
                'offer': 0,
                'joined': 0
            }))

        return success_response(
            data={'requisitions': requisitions_data},
            message="Requisitions retrieved.",
            meta={
                'total': total,
                'limit': limit,
                'offset': offset,
                'sort': sort_order,
                'search_mode': search_mode,
            },
        )

    def post(self, request):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.create')
        serializer = JobRequisitionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        requisition = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            status='draft'
        )

        # Create default stages for this requisition
        default_stages = [
            {'name': 'Applied', 'stage_order': 1, 'stage_type': 'screening', 'action_deadline_hours': 24},
            {'name': 'Screening', 'stage_order': 2, 'stage_type': 'screening', 'action_deadline_hours': 48},
            {'name': 'Interview', 'stage_order': 3, 'stage_type': 'interview', 'action_deadline_hours': 48},
            {'name': 'Offer', 'stage_order': 4, 'stage_type': 'offer', 'action_deadline_hours': 48},
            {'name': 'Joined', 'stage_order': 5, 'stage_type': 'joined', 'action_deadline_hours': 72},
        ]
        for stage_data in default_stages:
            JobStage.objects.create(
                tenant_id=request.user.tenant_id,
                requisition_id=requisition.id,
                created_by=request.user.id,
                **stage_data
            )

        # Emit Event
        events.job.created.send(
            sender=self.__class__,
            requisition=requisition,
            user=request.user,
            request=request
        )

        from apps.jobs.workflow_service import JobWorkflowService
        JobWorkflowService.sync_job_pipeline(requisition)

        return success_response(
            data={'requisition': JobRequisitionSerializer(requisition).data},
            message="Requisition created.",
            status_code=status.HTTP_201_CREATED
        )


class JobRequisitionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return JobRequisition.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            # Candidates may belong to a different tenant than the hiring company.
            # Allow reading any active (published) requisition regardless of tenant.
            try:
                return JobRequisition.objects.get(
                    id=pk,
                    status='active',
                    is_deleted=False
                )
            except JobRequisition.DoesNotExist:
                return None

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        req = self.get_object(request, pk)
        if not req:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Get stats
        from apps.pipeline.models import Application
        apps = Application.objects.filter(requisition_id=pk, is_deleted=False)
        stats = {
            'applications_count': apps.count(),
            'applied': apps.filter(status='applied').count(),
            'screening': apps.filter(status='screening').count(),
            'interview': apps.filter(status='interview').count(),
            'offer': apps.filter(status='offer').count(),
            'joined': apps.filter(status='joined').count(),
        }

        req_data = JobRequisitionSerializer(req, context={'request': request}).data
        if 'metadata' not in req_data or req_data['metadata'] is None:
            req_data['metadata'] = {}
        req_data['metadata'].update(stats)

        stages = JobStage.objects.filter(requisition_id=pk, is_active=True)
        from apps.pipeline.models import PlacementGuarantee
        guarantees = PlacementGuarantee.objects.filter(requisition_id=pk).order_by('-created_at')[:10]
        return success_response(
            data={
                'requisition': req_data,
                'stages': JobStageSerializer(stages, many=True).data,
                'placement_guarantees': [
                    {
                        'id': str(g.id),
                        'candidate_id': str(g.candidate_id),
                        'application_id': str(g.application_id),
                        'status': g.status,
                        'guarantee_start_date': g.guarantee_start_date,
                        'guarantee_end_date': g.guarantee_end_date,
                        'guarantee_resolution_type': g.guarantee_resolution_type,
                        'refund_mode': g.refund_mode,
                        'refund_percentage': g.refund_percentage,
                    } for g in guarantees
                ],
            },
            message="Requisition retrieved."
        )

    def put(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        req = self.get_object(request, pk)
        if not req:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = JobRequisitionSerializer(req, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        requisition = serializer.save()
        
        from apps.jobs.workflow_service import JobWorkflowService
        JobWorkflowService.sync_job_pipeline(requisition)

        return success_response(
            data={'requisition': serializer.data},
            message="Requisition updated."
        )

    def delete(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.delete')
        req = self.get_object(request, pk)
        if not req:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        req.soft_delete()
        return success_response(
            message="Requisition deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class JobRequisitionReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        from apps.interviews.models import InterviewPackageBinding
        binding = InterviewPackageBinding.objects.filter(job_id=pk, is_deleted=False).first()
        stages = JobStage.objects.filter(requisition_id=pk).order_by('stage_order')

        # 1. Summarize configuration
        summary = JobRequisitionSerializer(req, context={'request': request}).data
        
        # 2. Completeness Check & Warnings
        errors = []
        warnings = []
        
        # Critical Checks
        if not req.hiring_manager_id:
            errors.append("Hiring Manager is not assigned.")
        if not req.recruiter_id:
            errors.append("Primary Recruiter is not assigned.")
        if not req.description:
            errors.append("Job description is missing.")
        if req.headcount < 1:
            errors.append("Headcount must be at least 1.")
        
        # Operational Warnings (Non-blocking)
        if not stages.exists():
            warnings.append("No custom pipeline stages configured. Default stages will be used.")
        if not binding:
            warnings.append("No interview package bound to this job.")
        if req.sourcing_mode == 'external_only' and not req.is_published_to_agencies:
            warnings.append("Sourcing is set to external but job is not yet published to agencies.")
        if not req.auto_assign_recruiter and not req.recruiter_id:
            warnings.append("Automation routing is disabled and no manual recruiter is assigned.")
        if req.salary_min == 0 and req.salary_max == 0:
            warnings.append("Salary range is set to zero.")

        # 3. Readiness Score
        if errors:
            readiness = "Incomplete"
            readiness_color = "red"
        elif warnings:
            readiness = "Needs Attention"
            readiness_color = "amber"
        else:
            readiness = "Ready"
            readiness_color = "green"

        return success_response(
            data={
                'summary': summary,
                'validation': {
                    'readiness': readiness,
                    'readiness_color': readiness_color,
                    'errors': errors,
                    'warnings': warnings,
                    'can_publish': len(errors) == 0,
                    'is_draft': req.status == 'draft'
                },
                'steps_status': {
                    'information': "complete" if req.title and req.department_id and req.location_id else "incomplete",
                    'ownership': "complete" if req.hiring_manager_id and req.recruiter_id else "incomplete",
                    'sourcing': "complete" if req.sourcing_mode else "incomplete",
                    'pipeline': "complete" if stages.exists() else "warning",
                    'interview': "complete" if binding else "warning",
                    'automation': "complete" if req.override_workflow_mode else "warning",
                    'offer_closure': "complete" if req.offer_salary_default else "warning"
                }
            },
            message="Requisition review data retrieved."
        )


class JobRequisitionSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        if req.status != 'draft':
            return error_response("Only draft requisitions can be submitted for approval.")

        req.status = 'pending_approval'

        # Set current approver from chain (first in order)
        chain = req.approval_chain if isinstance(req.approval_chain, list) else []
        if chain:
            first = sorted(chain, key=lambda x: x.get('order', 0))[0]
            first_approver_id = first.get('user_id')
            req.current_approver_id = first_approver_id if first_approver_id else None
        else:
            req.current_approver_id = None

        req.save(update_fields=['status', 'current_approver_id', 'updated_at'])
        return success_response(
            data={'requisition': JobRequisitionSerializer(req).data},
            message="Requisition submitted for approval."
        )


class JobRequisitionApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.approve')
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        if req.status != 'pending_approval':
            return error_response("Only pending requisitions can be approved.")

        req.status = 'approved'
        req.approved_at = timezone.now()
        req.approved_by = request.user.id
        req.save(update_fields=['status', 'approved_at', 'approved_by', 'updated_at'])

        # Emit Event
        events.job.approved.send(
            sender=self.__class__,
            requisition=req,
            user=request.user,
            request=request
        )

        return success_response(
            data={'requisition': JobRequisitionSerializer(req).data},
            message="Requisition approved."
        )


class JobRequisitionRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.approve')
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        req.status = 'draft'
        req.closed_reason = reason
        req.save(update_fields=['status', 'closed_reason', 'updated_at'])
        return success_response(
            data={'requisition': JobRequisitionSerializer(req).data},
            message="Requisition rejected."
        )


class JobRequisitionPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.approve')
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Critical validation
        if not req.hiring_manager_id or not req.recruiter_id or not req.description:
            return error_response("Requisition is incomplete. Ensure Hiring Manager, Recruiter, and Description are set.")

        if req.status == 'active':
            return error_response("Requisition is already active.")

        # Enforce approval when an approval chain is configured
        chain = req.approval_chain if isinstance(req.approval_chain, list) else []
        if chain and req.status == 'draft':
            return error_response(
                "This job requires approval before publishing. Submit it for approval first."
            )

        if req.status not in ['approved', 'draft']:
            return error_response(f"Cannot publish from status: {req.status}")

        req.status = 'active'
        req.save(update_fields=['status', 'updated_at'])

        # Create job posting
        slug = slugify(req.title)
        counter = 1
        base_slug = slug
        while JobPosting.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        posting = JobPosting.objects.create(
            tenant_id=request.user.tenant_id,
            requisition_id=req.id,
            title=req.title,
            slug=slug,
            description_html=req.description,
            requirements=req.requirements,
            responsibilities=req.responsibilities,
            skills_required=req.skills_required,
            posted_at=timezone.now(),
            is_active=True,
            created_by=request.user.id,
        )

        # Emit Event
        events.job.published.send(
            sender=self.__class__,
            requisition=req,
            posting=posting,
            user=request.user,
            request=request
        )

        return success_response(
            data={
                'requisition': JobRequisitionSerializer(req).data,
                'posting': JobPostingSerializer(posting).data,
            },
            message="Requisition published successfully."
        )


class JobRequisitionCandidatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        try:
            job = JobRequisition.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        from apps.pipeline.models import Application
        from apps.pipeline.serializers import ApplicationSerializer

        applications = Application.objects.filter(
            requisition_id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('-created_at')

        return success_response(
            data={'candidates': ApplicationSerializer(applications, many=True).data},
            message="Job candidates retrieved.",
            meta={'total': applications.count()}
        )


class JobRequisitionCloneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Clone the requisition
        req.pk = None
        req.id = None
        req.status = 'draft'
        req.approved_at = None
        req.approved_by = None
        req.closed_at = None
        req.closed_reason = ''
        req.approval_chain = []
        req.current_approver_id = None
        req.title = f"{req.title} (Copy)"
        req.created_by = request.user.id
        req.save()

        return success_response(
            data={'requisition': JobRequisitionSerializer(req).data},
            message="Requisition cloned.",
            status_code=status.HTTP_201_CREATED
        )


class JobPostingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_internal_jobs_actor(request.user)
        postings = JobPosting.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )
        return success_response(
            data={'postings': JobPostingSerializer(postings, many=True).data},
            message="Postings retrieved."
        )


class JobPostingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return JobPosting.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except JobPosting.DoesNotExist:
            # Candidates may belong to a different tenant — allow reading active postings.
            try:
                return JobPosting.objects.get(
                    id=pk,
                    is_active=True,
                    is_deleted=False
                )
            except JobPosting.DoesNotExist:
                return None

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        posting = self.get_object(request, pk)
        if not posting:
            return error_response("Posting not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'posting': JobPostingSerializer(posting).data},
            message="Posting retrieved."
        )

    def put(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        posting = self.get_object(request, pk)
        if not posting:
            return error_response("Posting not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = JobPostingSerializer(posting, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'posting': serializer.data},
            message="Posting updated."
        )


class JobPostingPauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        try:
            posting = JobPosting.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobPosting.DoesNotExist:
            return error_response("Posting not found.", status_code=status.HTTP_404_NOT_FOUND)

        posting.is_active = False
        posting.save(update_fields=['is_active', 'updated_at'])
        return success_response(
            data={'posting': JobPostingSerializer(posting).data},
            message="Posting paused."
        )


class JobPostingCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        try:
            posting = JobPosting.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobPosting.DoesNotExist:
            return error_response("Posting not found.", status_code=status.HTTP_404_NOT_FOUND)

        posting.is_active = False
        posting.save(update_fields=['is_active', 'updated_at'])

        # Also close the requisition
        JobRequisition.objects.filter(
            id=posting.requisition_id,
            tenant_id=request.user.tenant_id
        ).update(
            status='closed',
            closed_at=timezone.now()
        )

        return success_response(
            data={'posting': JobPostingSerializer(posting).data},
            message="Posting closed."
        )


class JobStageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, requisition_id):
        _require_internal_jobs_actor(request.user)
        stages = JobStage.objects.filter(
            requisition_id=requisition_id,
            tenant_id=request.user.tenant_id,
            is_active=True
        ).order_by('stage_order')
        return success_response(
            data={'stages': JobStageSerializer(stages, many=True).data},
            message="Stages retrieved."
        )

    def post(self, request, requisition_id):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        # Verify requisition belongs to tenant
        try:
            JobRequisition.objects.get(
                id=requisition_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = JobStageSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save(
            tenant_id=request.user.tenant_id,
            requisition_id=requisition_id,
            created_by=request.user.id
        )
        return success_response(
            data={'stage': serializer.data},
            message="Stage created.",
            status_code=status.HTTP_201_CREATED
        )


class JobStageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, requisition_id, stage_id):
        try:
            return JobStage.objects.get(
                id=stage_id,
                requisition_id=requisition_id,
                tenant_id=request.user.tenant_id,
            )
        except JobStage.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Stage updated"),
            404: OpenApiResponse(description="Stage not found"),
        }
    )
    def put(self, request, requisition_id, stage_id):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        stage = self.get_object(request, requisition_id, stage_id)
        if not stage:
            return error_response("Stage not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = JobStageSerializer(stage, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'stage': serializer.data},
            message="Stage updated."
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Stage deleted"),
            404: OpenApiResponse(description="Stage not found"),
        }
    )
    def delete(self, request, requisition_id, stage_id):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        stage = self.get_object(request, requisition_id, stage_id)
        if not stage:
            return error_response("Stage not found.", status_code=status.HTTP_404_NOT_FOUND)

        stage.is_active = False
        stage.save(update_fields=['is_active'])
        return success_response(
            message="Stage deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class JobStageReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, requisition_id):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        stage_ids = request.data.get('stage_ids', [])
        if not stage_ids:
            return error_response("stage_ids is required.")

        for order, stage_id in enumerate(stage_ids, start=1):
            JobStage.objects.filter(
                id=stage_id,
                requisition_id=requisition_id,
                tenant_id=request.user.tenant_id
            ).update(stage_order=order)

        stages = JobStage.objects.filter(
            requisition_id=requisition_id,
            tenant_id=request.user.tenant_id,
            is_active=True
        ).order_by('stage_order')

        return success_response(
            data={'stages': JobStageSerializer(stages, many=True).data},
            message="Stages reordered."
        )


# ─── JOB SEARCH (PUBLIC + CANDIDATE SIDE) ────────────────────────────────────

from rest_framework.permissions import AllowAny


class JobSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = JobPosting.objects.filter(
            is_active=True,
            is_deleted=False,
        )
        # Public search should only include postings tied to active requisitions.
        active_requisitions = JobRequisition.objects.filter(
            is_deleted=False,
            status='active',
        )
        qs = qs.filter(requisition_id__in=active_requisitions.values('id'))

        # Query aliases: search / q / query
        query = get_search_query(request.query_params)
        search_mode = 'none'
        if query:
            qs, search_mode = apply_keyword_search(
                qs,
                query=query,
                fields=(
                    'title',
                    'description_html',
                    'requirements',
                    'responsibilities',
                    'skills_required',
                    'metadata',
                ),
                typo_tolerant=True,
            )

        job_type = (request.query_params.get('job_type') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        work_mode = request.query_params.get('work_mode')
        experience = request.query_params.get('experience')
        location = (request.query_params.get('location') or '').strip()

        if job_type:
            active_requisitions = active_requisitions.filter(job_type=job_type)
        if work_mode:
            active_requisitions = active_requisitions.filter(work_mode=work_mode)
        if status_filter:
            active_requisitions = active_requisitions.filter(status=status_filter)
        if experience:
            active_requisitions = active_requisitions.filter(experience_min__lte=experience)
        if location:
            from apps.organisations.models import Location
            location_ids = Location.objects.filter(
                Q(name__icontains=location) | Q(city__icontains=location),
                is_deleted=False,
            ).values_list('id', flat=True)
            active_requisitions = active_requisitions.filter(location_id__in=location_ids)

        qs = qs.filter(requisition_id__in=active_requisitions.values('id'))

        # Stable ordering + pagination contract.
        limit, offset = parse_limit_offset(request.query_params, default_limit=50, max_limit=200)
        total = qs.count()
        qs = qs.order_by('-posted_at', '-created_at')[offset:offset + limit]

        return success_response(
            data={'jobs': JobPostingSerializer(qs, many=True).data},
            message="Jobs retrieved.",
            meta={
                'total': total,
                'limit': limit,
                'offset': offset,
                'search_mode': search_mode,
            },
        )

@extend_schema(
    responses={
        200: OpenApiResponse(description="Success"),
        404: OpenApiResponse(description="Job not found."),
    }
)
class JobPublicDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            posting = JobPosting.objects.get(
                id=pk,
                is_active=True,
                is_deleted=False
            )
        except JobPosting.DoesNotExist:
            return error_response("Job not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Increment view count
        posting.views_count += 1
        posting.save(update_fields=['views_count'])

        # Get requisition details
        try:
            req = JobRequisition.objects.get(id=posting.requisition_id)
            req_data = JobRequisitionSerializer(req).data
        except JobRequisition.DoesNotExist:
            req_data = None

        return success_response(
            data={
                'posting': JobPostingSerializer(posting).data,
                'requisition': req_data,
            },
            message="Job retrieved."
        )

@extend_schema(
    responses={
        200: OpenApiResponse(description="Success"),
        404: OpenApiResponse(description="Job not found."),
    }
)
def _get_or_create_candidate_for_user(user):
    """
    Return the Candidate record linked to this user account.

    Look-up order:
      1. Candidate.user_id == user.id  (fast path — already linked)
      2. Email / phone match via identity_service  (claim flow)
      3. Auto-create a minimal Candidate record  (fresh self-registered user)

    Always sets Candidate.user_id and marks account_status='active' if not
    already set, so subsequent calls hit the fast path.
    """
    from apps.candidates.identity_service import resolve_candidate_identity

    resolution = resolve_candidate_identity(
        email=user.email,
        phone=getattr(user, 'phone', '') or '',
        user=user,
        tenant_id=getattr(user, 'tenant_id', None),
        create_if_missing=True,
        allow_cross_tenant=True,
        actor_user_id=user.id,
        ensure_tenant_association_flag=bool(getattr(user, 'tenant_id', None)),
        ensure_visibility=False,
        source='job_apply',
        candidate_defaults={
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'source': 'self',
            'source_type': 'direct',
            'account_status': 'active',
            'profile_status': 'partial',
            'initial_entry_type': 'self',
            'owner_tenant_id': getattr(user, 'tenant_id', None),
            'owner_user_id': user.id,
        },
    )
    return resolution.candidate


class JobApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_candidate_role(request.user)
        from apps.pipeline.models import Application
        from apps.jobs.models import JobStage

        try:
            posting = JobPosting.objects.get(
                id=pk,
                is_active=True,
                is_deleted=False
            )
        except JobPosting.DoesNotExist:
            return error_response("Job not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Resolve the Candidate record for this user.
        # Application.candidate_id must always be Candidate.id (not User.id) so
        # the company-side pipeline sees the correct candidate record.
        candidate = _get_or_create_candidate_for_user(request.user)

        # Check duplicate application
        existing_app = Application.objects.filter(
            candidate_id=candidate.id,
            requisition_id=posting.requisition_id,
            is_deleted=False
        ).first()

        if existing_app:
            if 'duplicate_attempts' not in existing_app.metadata:
                existing_app.metadata['duplicate_attempts'] = []
            existing_app.metadata['duplicate_attempts'].append({
                'attempted_at': timezone.now().isoformat(),
                'attempted_by': str(request.user.id),
                'source': 'direct'
            })
            existing_app.save(update_fields=['metadata', 'updated_at'])

            return error_response(
                "You have already applied for this job.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Get first stage
        first_stage = JobStage.objects.filter(
            requisition_id=posting.requisition_id,
            is_active=True
        ).order_by('stage_order').first()

        application = Application.objects.create(
            tenant_id=posting.tenant_id,
            candidate_id=candidate.id,
            requisition_id=posting.requisition_id,
            current_stage_id=first_stage.id if first_stage else None,
            status='applied',
            source='direct',
            source_detail=request.data.get('cover_note', ''),
            submitted_by=request.user.id,
            submitted_by_tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        mark_direct_apply_during_protection(
            candidate_id=candidate.id,
            tenant_id=posting.tenant_id,
            actor_user_id=request.user.id,
        )

        # Emit Event
        events.application.created.send(
            sender=self.__class__,
            application=application,
            user=request.user,
            request=request
        )

        # Increment applications count
        posting.applications_count += 1
        posting.save(update_fields=['applications_count'])

        from apps.pipeline.serializers import CandidateApplicationSerializer
        return success_response(
            data={'application': CandidateApplicationSerializer(application).data},
            message="Application submitted successfully.",
            status_code=status.HTTP_201_CREATED
        )


class JobSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # TODO: Implement saved jobs with a SavedJob model
        return success_response(message="Job saved.")


class CandidateApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_candidate_role(request.user)
        from apps.pipeline.models import Application
        from apps.pipeline.serializers import CandidateApplicationSerializer

        candidate = _get_or_create_candidate_for_user(request.user)

        applications = Application.objects.filter(
            candidate_id=candidate.id,
            is_deleted=False
        ).order_by('-created_at')

        return success_response(
            data={'applications': CandidateApplicationSerializer(applications, many=True).data},
            message="Your applications retrieved.",
            meta={'total': applications.count()}
        )


class CandidateApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_candidate_role(request.user)
        from apps.pipeline.models import Application, ApplicationStageHistory
        from apps.pipeline.serializers import (
            CandidateApplicationSerializer,
            CandidateApplicationStageHistorySerializer,
        )

        candidate = _get_or_create_candidate_for_user(request.user)

        try:
            application = Application.objects.get(
                id=pk,
                candidate_id=candidate.id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        history = ApplicationStageHistory.objects.filter(
            application_id=pk
        ).order_by('moved_at')

        return success_response(
            data={
                'application': CandidateApplicationSerializer(application).data,
                'stage_history': CandidateApplicationStageHistorySerializer(history, many=True).data,
            },
            message="Application retrieved."
        )


class RecommendedJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_candidate_role(request.user)
        from apps.passport.models import TalentPassport
        from django.db.models import Q

        # Get candidate skills from passport
        skills = []
        try:
            passport = TalentPassport.objects.get(
                user_id=request.user.id,
                is_deleted=False
            )
            skills = passport.skills
        except TalentPassport.DoesNotExist:
            pass

        # Find active postings matching skills
        qs = JobPosting.objects.filter(
            is_active=True,
            is_deleted=False
        )

        if skills:
            # Filter requisitions with matching skills
            matching_reqs = JobRequisition.objects.filter(
                status='active',
                is_deleted=False
            )
            skill_filter = Q()
            for skill in skills[:5]:  # top 5 skills
                skill_filter |= Q(skills_required__contains=[skill])
            matching_reqs = matching_reqs.filter(skill_filter)
            qs = qs.filter(requisition_id__in=matching_reqs.values('id'))

        return success_response(
            data={'jobs': JobPostingSerializer(qs[:20], many=True).data},
            message="Recommended jobs retrieved.",
            meta={'total': qs.count()}
        )


# ─────────────────────────────────────────────────────────────────────────────
# JD Template Views
# ─────────────────────────────────────────────────────────────────────────────

class JDTemplateListView(APIView):
    """List and create job description templates."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_internal_jobs_actor(request.user)
        qs = JobDescriptionTemplate.objects.filter(
            tenant_id=request.user.tenant_id, is_deleted=False
        )
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        job_type = request.query_params.get('job_type')
        if job_type:
            qs = qs.filter(job_type=job_type)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        active_only = request.query_params.get('active_only', 'true').lower() == 'true'
        if active_only:
            qs = qs.filter(is_active=True)

        return success_response(
            data={'templates': JobDescriptionTemplateSerializer(qs, many=True).data},
            meta={'total': qs.count()}
        )

    def post(self, request):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.create')
        ser = JobDescriptionTemplateSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        tpl = ser.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'template': JobDescriptionTemplateSerializer(tpl).data},
            message='Template created.',
            status=status.HTTP_201_CREATED
        )


class JDTemplateDetailView(APIView):
    """Retrieve, update, or delete a single JD template."""
    permission_classes = [IsAuthenticated]

    def _get(self, request, pk):
        try:
            return JobDescriptionTemplate.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobDescriptionTemplate.DoesNotExist:
            return None

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        tpl = self._get(request, pk)
        if not tpl:
            return error_response('Template not found.', status=status.HTTP_404_NOT_FOUND)
        return success_response(data={'template': JobDescriptionTemplateSerializer(tpl).data})

    def put(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        tpl = self._get(request, pk)
        if not tpl:
            return error_response('Template not found.', status=status.HTTP_404_NOT_FOUND)
        ser = JobDescriptionTemplateSerializer(tpl, data=request.data, partial=True)
        if not ser.is_valid():
            return error_response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        tpl = ser.save()
        return success_response(data={'template': JobDescriptionTemplateSerializer(tpl).data}, message='Template updated.')

    def delete(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.delete')
        tpl = self._get(request, pk)
        if not tpl:
            return error_response('Template not found.', status=status.HTTP_404_NOT_FOUND)
        tpl.soft_delete()
        return success_response(message='Template deleted.')


class JDTemplateDuplicateView(APIView):
    """Duplicate a template as a new draft."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.create')
        try:
            tpl = JobDescriptionTemplate.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobDescriptionTemplate.DoesNotExist:
            return error_response('Template not found.', status=status.HTTP_404_NOT_FOUND)

        clone = JobDescriptionTemplate.objects.create(
            tenant_id=request.user.tenant_id,
            name=f"{tpl.name} (Copy)",
            category=tpl.category,
            job_type=tpl.job_type,
            description=tpl.description,
            requirements=tpl.requirements,
            responsibilities=tpl.responsibilities,
            skills_suggested=tpl.skills_suggested,
            created_by=request.user.id,
        )
        return success_response(
            data={'template': JobDescriptionTemplateSerializer(clone).data},
            message='Template duplicated.',
            status=status.HTTP_201_CREATED
        )


class JDTemplateApplyView(APIView):
    """Apply a template to a job requisition, prefilling description fields."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        try:
            tpl = JobDescriptionTemplate.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobDescriptionTemplate.DoesNotExist:
            return error_response('Template not found.', status=status.HTTP_404_NOT_FOUND)

        requisition_id = request.data.get('requisition_id')
        if not requisition_id:
            # Return template fields only (for pre-fill before creation)
            return success_response(data={
                'description': tpl.description,
                'requirements': tpl.requirements,
                'responsibilities': tpl.responsibilities,
                'skills_required': tpl.skills_suggested,
            })

        try:
            req = JobRequisition.objects.get(
                id=requisition_id, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response('Job requisition not found.', status=status.HTTP_404_NOT_FOUND)

        overwrite = request.data.get('overwrite', False)
        fields_updated = []

        if overwrite or not req.description:
            req.description = tpl.description
            fields_updated.append('description')
        if overwrite or not req.requirements:
            req.requirements = tpl.requirements
            fields_updated.append('requirements')
        if overwrite or not req.responsibilities:
            req.responsibilities = tpl.responsibilities
            fields_updated.append('responsibilities')
        if overwrite or not req.skills_required:
            req.skills_required = tpl.skills_suggested
            fields_updated.append('skills_required')

        if fields_updated:
            req.save(update_fields=fields_updated + ['updated_at'])

        # Increment usage count
        JobDescriptionTemplate.objects.filter(id=tpl.id).update(
            usage_count=tpl.usage_count + 1
        )

        return success_response(
            data={'fields_updated': fields_updated, 'requisition_id': str(req.id)},
            message='Template applied successfully.'
        )


# ─────────────────────────────────────────────────────────────────────────────
# Job Multiple Locations Views
# ─────────────────────────────────────────────────────────────────────────────

class JobLocationListView(APIView):
    """List and add locations for a job requisition."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response('Job not found.', status=status.HTTP_404_NOT_FOUND)

        locs = JobLocation.objects.filter(requisition=req)
        return success_response(data={'locations': JobLocationSerializer(locs, many=True).data})

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response('Job not found.', status=status.HTTP_404_NOT_FOUND)

        location_id = request.data.get('location_id')
        if not location_id:
            return error_response('location_id is required.', status=status.HTTP_400_BAD_REQUEST)

        location_name = request.data.get('location_name', '')
        is_primary = request.data.get('is_primary', False)

        # If setting as primary, clear existing primary
        if is_primary:
            JobLocation.objects.filter(requisition=req, is_primary=True).update(is_primary=False)

        loc, created = JobLocation.objects.get_or_create(
            requisition=req,
            location_id=location_id,
            defaults={
                'tenant_id': request.user.tenant_id,
                'location_name': location_name,
                'is_primary': is_primary,
            }
        )
        if not created:
            loc.location_name = location_name
            loc.is_primary = is_primary
            loc.save(update_fields=['location_name', 'is_primary'])

        return success_response(
            data={'location': JobLocationSerializer(loc).data},
            message='Location added.' if created else 'Location updated.',
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class JobLocationDeleteView(APIView):
    """Remove a location from a job requisition."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, location_id):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        try:
            loc = JobLocation.objects.get(
                id=location_id,
                requisition_id=pk,
                tenant_id=request.user.tenant_id,
            )
        except JobLocation.DoesNotExist:
            return error_response('Location not found.', status=status.HTTP_404_NOT_FOUND)
        loc.delete()
        return success_response(message='Location removed.')


# ─────────────────────────────────────────────────────────────────────────────
# Prequalification Binding Views
# ─────────────────────────────────────────────────────────────────────────────

class JobPrequalSnapshotView(APIView):
    """
    GET /jobs/requisitions/{pk}/prequal-snapshot/
    Returns prequal config + aggregate response stats for the Job Command Center.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_internal_jobs_actor(request.user)
        from apps.jobs.prequal_service import get_job_prequal_snapshot
        snapshot = get_job_prequal_snapshot(
            job_id=str(pk),
            tenant_id=str(request.user.tenant_id),
        )
        return success_response(data={'prequal': snapshot}, message='Prequal snapshot retrieved.')


class JobPrequalEvaluateView(APIView):
    """
    POST /jobs/requisitions/{pk}/prequal-evaluate/
    Evaluate a candidate's responses against the job's prequal config.
    Optionally updates the Application's metadata with the result.

    Body: { "candidate_id": "<uuid>", "application_id": "<uuid>" (optional) }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        _require_internal_jobs_actor(request.user)
        _require_jobs_permission(request.user, 'jobs.job.edit')
        from apps.jobs.prequal_service import evaluate_candidate_prequal

        candidate_id = request.data.get('candidate_id')
        if not candidate_id:
            return error_response('candidate_id is required.', status_code=status.HTTP_400_BAD_REQUEST)

        result = evaluate_candidate_prequal(
            job_id=str(pk),
            candidate_id=str(candidate_id),
            tenant_id=str(request.user.tenant_id),
        )

        if result['result'] == 'not_configured':
            return success_response(
                data={'result': result},
                message='Prequalification is not configured for this job.'
            )

        # Optionally persist result to Application.application_form_data
        application_id = request.data.get('application_id')
        if application_id:
            from apps.pipeline.models import Application
            try:
                app = Application.objects.get(
                    id=application_id,
                    requisition_id=pk,
                    tenant_id=request.user.tenant_id,
                    is_deleted=False,
                )
                if not isinstance(app.application_form_data, dict):
                    app.application_form_data = {}
                app.application_form_data['prequal_result'] = result['result']
                app.application_form_data['prequal_score'] = result['score']
                app.application_form_data['prequal_threshold'] = result.get('threshold')
                app.application_form_data['prequal_action'] = result['action']
                app.application_form_data['prequal_knockout'] = result.get('knockout_triggered', False)

                # Apply pass/fail action
                if result['result'] == 'pass' and result['action'] == 'advance':
                    # Don't auto-advance here — that's a pipeline operation.
                    # Just mark the prequal as passed; pipeline engine handles movement.
                    app.metadata = app.metadata or {}
                    app.metadata['prequal_passed_at'] = timezone.now().isoformat()
                elif result['result'] == 'fail' and result['action'] == 'reject':
                    app.status = 'rejected'
                    app.rejection_reason = 'Failed prequalification screening.'
                elif result['result'] == 'fail' and result['action'] == 'hold':
                    app.status = 'on_hold'
                elif result['action'] == 'manual_review':
                    app.metadata = app.metadata or {}
                    app.metadata['prequal_flagged_for_review'] = True

                app.save(update_fields=['application_form_data', 'status', 'rejection_reason', 'metadata', 'updated_at'])
            except Application.DoesNotExist:
                pass  # non-fatal: still return result

        return success_response(
            data={'result': result},
            message=f"Prequalification evaluated: {result['result'].upper()}"
        )
