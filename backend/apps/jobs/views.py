from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.jobs.models import JobRequisition, JobPosting, JobStage
from apps.jobs.serializers import (
    JobRequisitionSerializer, JobPostingSerializer, JobStageSerializer
)
from apps.core.responses import success_response, error_response


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

        department_id = request.query_params.get('department_id')
        if department_id:
            qs = qs.filter(department_id=department_id)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(title__icontains=search)

        return success_response(
            data={'requisitions': JobRequisitionSerializer(qs, many=True).data},
            message="Requisitions retrieved."
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
            return None

    def get(self, request, pk):
        req = self.get_object(request, pk)
        if not req:
            return error_response("Requisition not found.", status_code=status.HTTP_404_NOT_FOUND)

        stages = JobStage.objects.filter(requisition_id=pk, is_active=True)
        return success_response(
            data={
                'requisition': JobRequisitionSerializer(req).data,
                'stages': JobStageSerializer(stages, many=True).data,
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

        if req.status != 'approved':
            return error_response("Only approved requisitions can be published.")

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
            posted_at=timezone.now(),
            is_active=True,
            created_by=request.user.id,
        )

        return success_response(
            data={
                'requisition': JobRequisitionSerializer(req).data,
                'posting': JobPostingSerializer(posting).data,
            },
            message="Requisition published successfully."
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

        # Check duplicate application
        if Application.objects.filter(
            candidate_id=request.user.id,
            requisition_id=posting.requisition_id,
            is_deleted=False
        ).exists():
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
            candidate_id=request.user.id,
            requisition_id=posting.requisition_id,
            current_stage_id=first_stage.id if first_stage else None,
            status='applied',
            source='direct',
            source_detail=request.data.get('cover_note', ''),
            submitted_by=request.user.id,
            submitted_by_tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )

        # Increment applications count
        posting.applications_count += 1
        posting.save(update_fields=['applications_count'])

        from apps.pipeline.serializers import ApplicationSerializer
        return success_response(
            data={'application': ApplicationSerializer(application).data},
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
        from apps.pipeline.serializers import ApplicationSerializer

        applications = Application.objects.filter(
            candidate_id=request.user.id,
            is_deleted=False
        ).order_by('-created_at')

        return success_response(
            data={'applications': ApplicationSerializer(applications, many=True).data},
            message="Your applications retrieved.",
            meta={'total': applications.count()}
        )


class CandidateApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from apps.pipeline.models import Application, ApplicationStageHistory
        from apps.pipeline.serializers import ApplicationSerializer, ApplicationStageHistorySerializer

        try:
            application = Application.objects.get(
                id=pk,
                candidate_id=request.user.id,
                is_deleted=False
            )
        except Application.DoesNotExist:
            return error_response("Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        history = ApplicationStageHistory.objects.filter(
            application_id=pk
        ).order_by('moved_at')

        return success_response(
            data={
                'application': ApplicationSerializer(application).data,
                'stage_history': ApplicationStageHistorySerializer(history, many=True).data,
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
