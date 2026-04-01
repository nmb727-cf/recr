from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.jobs.models import JobRequisition, JobPosting, JobStage
from apps.jobs.serializers import (
    JobRequisitionSerializer, JobPostingSerializer, JobStageSerializer
)
from apps.core.responses import success_response, error_response
from apps.core import events
from apps.candidates.protection import mark_direct_apply_during_protection
from drf_spectacular.utils import extend_schema, OpenApiResponse


from apps.jobs.services import HiringAIBrainService, GlobalHiringCommandCenterService

class GlobalHiringCommandCenterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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


class JobRequisitionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(job_ref_id__icontains=search))

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
            meta={'total': qs.count()}
        )

    def post(self, request):
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
        req = self.get_object(request, pk)
        if not req:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = JobRequisitionSerializer(req, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'requisition': serializer.data},
            message="Requisition updated."
        )

    def delete(self, request, pk):
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
        try:
            req = JobRequisition.objects.get(
                id=pk, tenant_id=request.user.tenant_id, is_deleted=False
            )
        except JobRequisition.DoesNotExist:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        if req.status != 'draft':
            return error_response("Only draft requisitions can be submitted for approval.")

        req.status = 'pending_approval'
        req.save(update_fields=['status', 'updated_at'])
        return success_response(
            data={'requisition': JobRequisitionSerializer(req).data},
            message="Requisition submitted for approval."
        )


class JobRequisitionApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
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

        # If it's already approved or we're skipping approval (e.g., admin)
        # For now, allow publishing if approved or if it's a draft and user is admin
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
        posting = self.get_object(request, pk)
        if not posting:
            return error_response("Posting not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'posting': JobPostingSerializer(posting).data},
            message="Posting retrieved."
        )

    def put(self, request, pk):
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
        from django.db.models import Q
        qs = JobPosting.objects.filter(
            is_active=True,
            is_deleted=False,
        )

        # Search
        q = request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description_html__icontains=q)
            )

        # Filter by work mode - need to join with requisition
        work_mode = request.query_params.get('work_mode')
        location = request.query_params.get('location')
        experience = request.query_params.get('experience')

        if work_mode or location or experience:
            req_ids = JobRequisition.objects.filter(
                is_deleted=False,
                status='active'
            )
            if work_mode:
                req_ids = req_ids.filter(work_mode=work_mode)
            if experience:
                req_ids = req_ids.filter(experience_min__lte=experience)
            qs = qs.filter(requisition_id__in=req_ids.values('id'))

        return success_response(
            data={'jobs': JobPostingSerializer(qs, many=True).data},
            message="Jobs retrieved.",
            meta={'total': qs.count()}
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
    from apps.candidates.models import Candidate, CandidateProfile
    from apps.candidates.identity_service import match_candidate

    # Fast path
    candidate = Candidate.objects.filter(user_id=user.id, is_deleted=False).first()
    if candidate:
        return candidate

    # Match by email/phone (recruiter pre-added this person)
    candidate = match_candidate(email=user.email, phone=user.phone)
    if candidate:
        if not candidate.user_id:
            candidate.user_id = user.id
            candidate.account_status = 'active'
            candidate.save(update_fields=['user_id', 'account_status', 'updated_at'])
        return candidate

    # Auto-create for fresh direct signups that were never pre-added
    candidate = Candidate.objects.create(
        user_id=user.id,
        first_name=user.first_name or '',
        last_name=user.last_name or '',
        email=user.email,
        phone=getattr(user, 'phone', '') or '',
        source='self',
        source_type='direct',
        account_status='active',
        profile_status='partial',
        initial_entry_type='self',
    )
    CandidateProfile.objects.create(candidate_id=candidate.id)
    return candidate


class JobApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
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
