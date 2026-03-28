from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from uuid import uuid4

from apps.interviews.models import (
    Interview, InterviewType, InterviewTemplate, InterviewFlow,
    InterviewPanelist, InterviewFeedback, InterviewDecision, InterviewQuestion,
    InterviewScorecardTemplate,
    InterviewAvailabilityProfile, InterviewAvailabilityBlock,
    InterviewSchedulingLink, InterviewCalendarConnection,
    InterviewIntegrationProvider, InterviewTenantProviderConnection,
    InterviewExecutionMapping,
    InterviewQuestionBank, InterviewQuestionAttachment,
    InterviewQuestionGroup,
)
from apps.interviews.serializers import (
    InterviewSerializer, InterviewDetailSerializer,
    InterviewTypeSerializer, InterviewTemplateSerializer,
    InterviewFlowSerializer,
    InterviewPanelistSerializer,
    InterviewFeedbackSerializer, InterviewDecisionSerializer,
    InterviewDecisionHistorySerializer,
    InterviewQuestionSerializer,
    InterviewScorecardTemplateSerializer,
    InterviewAvailabilityProfileSerializer, InterviewAvailabilityBlockSerializer,
    InterviewSchedulingLinkSerializer, InterviewCalendarConnectionSerializer,
    InterviewIntegrationProviderSerializer,
    InterviewTenantProviderConnectionSerializer,
    InterviewExecutionMappingSerializer,
    InterviewQuestionBankSerializer,
    InterviewQuestionAttachmentSerializer,
    InterviewQuestionGroupSerializer,
)
from apps.interviews.services import (
    InterviewTypeService, InterviewService,
    InterviewFeedbackService, InterviewDecisionService,
)
from apps.interviews.permissions import (
    can_view_interview_types, can_manage_interview_types,
    can_view_templates, can_create_templates, can_edit_templates, can_delete_templates,
    can_view_interviews, can_create_interviews, can_edit_interviews,
    can_start_interview, can_complete_interview, can_cancel_interview,
    can_submit_feedback, can_view_feedback,
    can_record_decision, can_view_decision,
)
from apps.pipeline.models import Application
from apps.candidates.models import Candidate, CandidateProfile
from apps.jobs.models import JobRequisition
from apps.core.responses import success_response, error_response
from apps.core import events
from apps.interviews.scheduling import compute_common_slots


INTEGRATION_PROVIDER_DEFAULTS = [
    {'name': 'Google Meet', 'code': 'google_meet', 'provider_type': 'meeting'},
    {'name': 'Zoom', 'code': 'zoom', 'provider_type': 'meeting'},
    {'name': 'Microsoft Teams', 'code': 'microsoft_teams', 'provider_type': 'meeting'},
    {'name': 'Google Calendar', 'code': 'google_calendar', 'provider_type': 'calendar'},
    {'name': 'Outlook Calendar', 'code': 'outlook_calendar', 'provider_type': 'calendar'},
    {'name': 'Apple Calendar', 'code': 'apple_calendar', 'provider_type': 'calendar'},
    {'name': 'ICS External', 'code': 'ics_external', 'provider_type': 'external'},
]


def _ensure_integration_provider_registry():
    for row in INTEGRATION_PROVIDER_DEFAULTS:
        InterviewIntegrationProvider.objects.update_or_create(
            code=row['code'],
            defaults={
                'name': row['name'],
                'provider_type': row['provider_type'],
                'is_active': True,
                'tenant_configurable': True,
            },
        )


def _resolve_execution_mapping(*, tenant_id, interview_type, stage_code=''):
    qs = InterviewExecutionMapping.objects.filter(
        tenant_id=tenant_id,
        interview_type=interview_type,
        is_active=True,
        is_deleted=False,
    )
    if stage_code:
        obj = qs.filter(stage_code=stage_code).first()
        if obj:
            return obj
    return qs.filter(stage_code='').first()


def _apply_execution_mode_and_links(*, interview, payload, tenant_id):
    requested_mode = payload.get('execution_mode')
    requested_provider = payload.get('execution_provider_code') or payload.get('provider_code') or ''
    stage_code = payload.get('stage_code') or ''
    mapping = _resolve_execution_mapping(
        tenant_id=tenant_id,
        interview_type=interview.interview_type,
        stage_code=stage_code,
    )

    execution_mode = requested_mode or (mapping.execution_mode if mapping else 'native')
    provider_code = requested_provider or (mapping.provider_code if mapping else '')

    manual_link = payload.get('meeting_link') or ''
    external_link = payload.get('external_interview_link') or payload.get('external_link') or ''

    interview.execution_mode = execution_mode
    interview.execution_provider_code = provider_code

    if execution_mode == 'external_manual':
        if external_link:
            interview.external_interview_link = external_link
            interview.meeting_link = external_link
            interview.interview_link = external_link
        interview.meeting_provider_code = provider_code or 'external_manual'
    elif execution_mode == 'third_party':
        interview.meeting_provider_code = provider_code
        if manual_link:
            interview.meeting_link = manual_link
            interview.interview_link = manual_link
        elif provider_code:
            generated = f"https://{provider_code}.integration.local/interview/{interview.id}"
            interview.meeting_link = generated
            interview.interview_link = generated
    else:
        if manual_link:
            interview.meeting_link = manual_link
            interview.interview_link = manual_link

    md = interview.metadata or {}
    md['execution'] = {
        'mode': execution_mode,
        'provider_code': provider_code,
        'stage_code': stage_code or '',
    }
    interview.metadata = md


def _question_bank_to_template_question(q):
    qtype_map = {
        'text': 'text',
        'multiple_choice': 'multiple_choice',
        'multi_select': 'multiple_choice',
        'coding': 'code',
        'file_upload': 'text',
        'video': 'video',
        'rating': 'rating_scale',
        'yes_no': 'multiple_choice',
    }
    options = q.options_json or []
    if q.question_type == 'yes_no' and not options:
        options = ['Yes', 'No']
    return {
        'text': q.question_title,
        'type': qtype_map.get(q.question_type, 'text'),
        'options': options,
        'duration': 120,
        'description': q.description,
        'difficulty': q.difficulty,
        'tags': q.tags or [],
        'skills': q.skills or [],
        'expected_answer': q.expected_answer or '',
        'scoring_weight': float(q.scoring_weight or 1),
    }


def _sync_template_questions_from_attachment(*, attachment):
    if attachment.attach_type != 'template' or not attachment.template_id:
        return
    template = InterviewTemplate.objects.filter(id=attachment.template_id, is_deleted=False).first()
    if not template:
        return
    q = attachment.question
    if not q:
        return
    existing = template.questions or []
    payload = _question_bank_to_template_question(q)
    # Avoid duplicate insert by title
    if any(str(row.get('text', '')).strip().lower() == payload['text'].strip().lower() for row in existing):
        return
    existing.append(payload)
    template.questions = existing
    template.save(update_fields=['questions', 'updated_at'])


def _seed_interview_questions_from_type_attachments(*, interview, tenant_id):
    if InterviewQuestion.objects.filter(interview_id=interview.id).exists():
        return
    attachments = InterviewQuestionAttachment.objects.filter(
        tenant_id=tenant_id,
        attach_type='interview_type',
        interview_type=interview.interview_type,
        is_active=True,
        is_deleted=False,
        question__is_deleted=False,
    ).select_related('question').order_by('order_index', 'created_at')
    for idx, att in enumerate(attachments):
        q = att.question
        payload = _question_bank_to_template_question(q)
        InterviewQuestion.objects.create(
            tenant_id=tenant_id,
            interview_id=interview.id,
            question_text=payload['text'],
            question_type=payload['type'],
            options=payload.get('options') or [],
            expected_duration_seconds=payload.get('duration'),
            order_index=idx,
            metadata={
                'question_bank_id': str(q.id),
                'difficulty': q.difficulty,
                'tags': q.tags or [],
                'skills': q.skills or [],
                'scoring_weight': float(q.scoring_weight or 1),
            },
        )


def _panel_decision_payload(interview_id):
    feedback_qs = InterviewFeedback.objects.filter(
        interview_id=interview_id,
        is_deleted=False,
    )
    total = feedback_qs.count()
    recommendation_counts = {}
    for row in feedback_qs.values('recommendation'):
        key = row.get('recommendation') or ''
        if not key:
            continue
        recommendation_counts[key] = recommendation_counts.get(key, 0) + 1

    combined_recommendation = None
    if recommendation_counts:
        combined_recommendation = sorted(
            recommendation_counts.items(),
            key=lambda x: (-x[1], x[0]),
        )[0][0]

    avg_score = feedback_qs.exclude(score__isnull=True).aggregate(avg=models.Avg('score')).get('avg')
    payload = {
        'total_feedback': total,
        'recommendation_counts': recommendation_counts,
        'combined_recommendation': combined_recommendation,
        'average_score': avg_score,
    }
    interview = Interview.objects.filter(id=interview_id, is_deleted=False).first()
    if interview:
        payload.update(InterviewDecisionService.multi_interviewer_recommendation(interview=interview))
    return payload


class InterviewTemplateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = InterviewTemplate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
            is_active=True
        )
        return success_response(
            data={'templates': InterviewTemplateSerializer(templates, many=True).data},
            message="Templates retrieved."
        )

    def post(self, request):
        serializer = InterviewTemplateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        template = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'template': InterviewTemplateSerializer(template).data},
            message="Template created.",
            status_code=status.HTTP_201_CREATED
        )


class InterviewTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return InterviewTemplate.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except InterviewTemplate.DoesNotExist:
            return None

    def get(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return error_response("Template not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'template': InterviewTemplateSerializer(template).data},
            message="Template retrieved."
        )

    def put(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return error_response("Template not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = InterviewTemplateSerializer(template, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'template': serializer.data},
            message="Template updated."
        )

    def delete(self, request, pk):
        template = self.get_object(request, pk)
        if not template:
            return error_response("Template not found.", status_code=status.HTTP_404_NOT_FOUND)

        template.soft_delete()
        return success_response(
            message="Template deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class InterviewScorecardTemplateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InterviewScorecardTemplate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).prefetch_related('attributes')
        interview_type = request.query_params.get('interview_type')
        if interview_type:
            qs = qs.filter(interview_type=interview_type)
        return success_response(
            data={'scorecards': InterviewScorecardTemplateSerializer(qs, many=True).data},
            message="Scorecard templates retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = InterviewScorecardTemplateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        template = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'scorecard': InterviewScorecardTemplateSerializer(template).data},
            message="Scorecard template created.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewScorecardTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return InterviewScorecardTemplate.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).prefetch_related('attributes').first()

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            return error_response("Scorecard template not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'scorecard': InterviewScorecardTemplateSerializer(obj).data},
            message="Scorecard template retrieved.",
        )

    def put(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            return error_response("Scorecard template not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = InterviewScorecardTemplateSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'scorecard': serializer.data},
            message="Scorecard template updated.",
        )

    def delete(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            return error_response("Scorecard template not found.", status_code=status.HTTP_404_NOT_FOUND)
        obj.soft_delete()
        return success_response(
            message="Scorecard template deleted.",
            status_code=status.HTTP_204_NO_CONTENT,
        )


class InterviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Interview.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        application_id = request.query_params.get('application_id')
        if application_id:
            qs = qs.filter(application_id=application_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        interview_type = request.query_params.get('type')
        if interview_type:
            qs = qs.filter(interview_type=interview_type)

        candidate_id = request.query_params.get('candidate_id')
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)

        return success_response(
            data={'interviews': InterviewSerializer(qs, many=True).data},
            message="Interviews retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = InterviewSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        data = serializer.validated_data
        scorecard_template_id = request.data.get('scorecard_template_id')
        if not scorecard_template_id:
            default_scorecard = InterviewScorecardTemplate.objects.filter(
                tenant_id=request.user.tenant_id,
                interview_type=data.get('interview_type'),
                is_active=True,
                is_deleted=False,
            ).order_by('-updated_at').first()
            if default_scorecard:
                scorecard_template_id = str(default_scorecard.id)

        # If template provided, copy questions from template
        questions_to_create = []
        if data.get('template_id'):
            try:
                template = InterviewTemplate.objects.get(
                    id=data['template_id'],
                    tenant_id=request.user.tenant_id,
                    is_deleted=False
                )
                for i, q in enumerate(template.questions):
                    questions_to_create.append({
                        'question_text': q.get('text', ''),
                        'question_type': q.get('type', 'text'),
                        'options': q.get('options', []),
                        'expected_duration_seconds': q.get('duration', None),
                        'order_index': i,
                    })
            except InterviewTemplate.DoesNotExist:
                pass

        interview = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            status='scheduled',
            scorecard_template_id=scorecard_template_id,
        )
        _apply_execution_mode_and_links(
            interview=interview,
            payload=request.data,
            tenant_id=request.user.tenant_id,
        )
        interview.save(update_fields=[
            'execution_mode', 'execution_provider_code',
            'meeting_provider_code', 'external_interview_link',
            'meeting_link', 'interview_link', 'metadata', 'updated_at',
        ])

        # Create questions from template
        for q_data in questions_to_create:
            InterviewQuestion.objects.create(
                tenant_id=request.user.tenant_id,
                interview_id=interview.id,
                **q_data
            )
        if not questions_to_create:
            _seed_interview_questions_from_type_attachments(
                interview=interview,
                tenant_id=request.user.tenant_id,
            )

        # Create panelists if provided
        panelist_ids = request.data.get('panelist_ids', [])
        for panelist_id in panelist_ids:
            InterviewPanelist.objects.create(
                tenant_id=request.user.tenant_id,
                interview_id=interview.id,
                interviewer_id=panelist_id,
                role='interviewer',
                deadline_at=data.get('scheduled_at') + timedelta(hours=24) if data.get('scheduled_at') else None,
            )

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview scheduled.",
            status_code=status.HTTP_201_CREATED
        )


class InterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return None

    def get(self, request, pk):
        interview = self.get_object(request, pk)
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        panelists = InterviewPanelist.objects.filter(interview_id=pk)
        questions = InterviewQuestion.objects.filter(interview_id=pk).order_by('order_index')

        return success_response(
            data={
                'interview': InterviewSerializer(interview).data,
                'panelists': InterviewPanelistSerializer(panelists, many=True).data,
                'questions': InterviewQuestionSerializer(questions, many=True).data,
            },
            message="Interview retrieved."
        )

    def put(self, request, pk):
        interview = self.get_object(request, pk)
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        previous_status = interview.status
        serializer = InterviewSerializer(interview, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        refreshed = Interview.objects.filter(id=interview.id).first()
        if refreshed and refreshed.status == 'no_show' and previous_status != 'no_show':
            events.interview.cancelled.send(sender=self.__class__, interview=refreshed)
        return success_response(
            data={'interview': serializer.data},
            message="Interview updated."
        )


class InterviewStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        if interview.status != 'scheduled':
            return error_response("Only scheduled interviews can be started.")

        interview.status = 'in_progress'
        interview.started_at = timezone.now()
        interview.save(update_fields=['status', 'started_at', 'updated_at'])

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview started."
        )


class InterviewCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        if interview.status != 'in_progress':
            return error_response("Only in-progress interviews can be completed.")

        overall_score = request.data.get('overall_score')
        recommendation = request.data.get('recommendation', '')
        feedback_summary = request.data.get('feedback_summary', '')

        interview.status = 'completed'
        interview.completed_at = timezone.now()
        interview.overall_score = overall_score
        interview.recommendation = recommendation
        interview.feedback_summary = feedback_summary
        interview.save(update_fields=[
            'status', 'completed_at', 'overall_score',
            'recommendation', 'feedback_summary', 'updated_at'
        ])

        # Emit Event
        try:
            application = Application.objects.get(id=interview.application_id)
            events.application.interviewed.send(
                sender=self.__class__,
                application=application,
                user=request.user,
                request=request
            )
        except Application.DoesNotExist:
            pass

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview completed."
        )


class InterviewCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        if interview.status in ['completed', 'cancelled']:
            return error_response("Cannot cancel a completed or already cancelled interview.")

        reason = request.data.get('reason', '')
        interview.status = 'cancelled'
        interview.feedback_summary = f"Cancelled: {reason}"
        interview.save(update_fields=['status', 'feedback_summary', 'updated_at'])

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview cancelled."
        )


class InterviewRescheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        scheduled_at = request.data.get('scheduled_at')
        if not scheduled_at:
            return error_response("scheduled_at is required.")

        interview.scheduled_at = scheduled_at
        interview.status = 'rescheduled'
        interview.save(update_fields=['scheduled_at', 'status', 'updated_at'])

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview rescheduled."
        )


def _parse_schedule_dt(raw_value, field_name='datetime'):
    if not raw_value:
        return None, error_response(f"{field_name} is required.")
    dt = parse_datetime(str(raw_value))
    if dt is None:
        return None, error_response(f"{field_name} must be a valid ISO datetime.")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt, None


class InterviewAvailabilityProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviewer_id = request.query_params.get('interviewer_id') or str(request.user.id)
        profile, _ = InterviewAvailabilityProfile.objects.get_or_create(
            tenant_id=request.user.tenant_id,
            interviewer_id=interviewer_id,
            defaults={'mode': 'system', 'timezone': 'UTC'},
        )
        return success_response(
            data={'profile': InterviewAvailabilityProfileSerializer(profile).data},
            message="Availability profile retrieved.",
        )

    def put(self, request):
        interviewer_id = request.data.get('interviewer_id') or str(request.user.id)
        profile, _ = InterviewAvailabilityProfile.objects.get_or_create(
            tenant_id=request.user.tenant_id,
            interviewer_id=interviewer_id,
            defaults={'mode': 'system', 'timezone': 'UTC'},
        )
        serializer = InterviewAvailabilityProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'profile': serializer.data},
            message="Availability profile updated.",
        )


class InterviewAvailabilityBlockListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviewer_id = request.query_params.get('interviewer_id') or str(request.user.id)
        qs = InterviewAvailabilityBlock.objects.filter(
            tenant_id=request.user.tenant_id,
            interviewer_id=interviewer_id,
        ).order_by('starts_at')
        return success_response(
            data={'blocks': InterviewAvailabilityBlockSerializer(qs, many=True).data},
            meta={'total': qs.count()},
            message="Availability blocks retrieved.",
        )

    def post(self, request):
        interviewer_id = request.data.get('interviewer_id') or str(request.user.id)
        serializer = InterviewAvailabilityBlockSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        starts_at = serializer.validated_data.get('starts_at')
        ends_at = serializer.validated_data.get('ends_at')
        if starts_at >= ends_at:
            return error_response("starts_at must be before ends_at.")

        block = serializer.save(
            tenant_id=request.user.tenant_id,
            interviewer_id=interviewer_id,
            created_by=request.user.id,
            source='manual',
        )
        return success_response(
            data={'block': InterviewAvailabilityBlockSerializer(block).data},
            status_code=status.HTTP_201_CREATED,
            message="Availability block created.",
        )


class InterviewPanelSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        panelist_ids = request.data.get('panelist_ids') or []
        if not panelist_ids:
            return error_response("panelist_ids is required.")

        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        if not from_date or not to_date:
            return error_response("from_date and to_date are required (YYYY-MM-DD).")
        try:
            start_date = timezone.datetime.fromisoformat(str(from_date)).date()
            end_date = timezone.datetime.fromisoformat(str(to_date)).date()
        except Exception:
            return error_response("Invalid from_date/to_date format.")

        if end_date < start_date:
            return error_response("to_date cannot be earlier than from_date.")

        timezone_name = request.data.get('timezone') or 'UTC'
        duration_minutes = int(request.data.get('duration_minutes') or 60)
        limit = int(request.data.get('limit') or 20)

        slots = compute_common_slots(
            tenant_id=request.user.tenant_id,
            interviewer_ids=panelist_ids,
            timezone_name=timezone_name,
            from_date=start_date,
            to_date=end_date,
            duration_minutes=duration_minutes,
            limit=limit,
        )
        suggestions = slots[:3]
        return success_response(
            data={'slots': slots, 'fallback_suggestions': suggestions},
            meta={'total': len(slots)},
            message="Panel slots computed.",
        )


class InterviewManualSchedulingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        interview_id = request.data.get('interview_id')
        scheduled_at, err = _parse_schedule_dt(request.data.get('scheduled_at'), 'scheduled_at')
        if err:
            return err

        duration_minutes = int(request.data.get('duration_minutes') or 60)
        panelist_ids = request.data.get('panelist_ids') or []
        tz_name = request.data.get('timezone') or 'UTC'

        if interview_id:
            interview = Interview.objects.filter(
                id=interview_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False,
            ).first()
            if not interview:
                return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)
            interview.scheduled_at = scheduled_at
            interview.duration_minutes = duration_minutes
            interview.status = 'rescheduled' if interview.status in ('scheduled', 'rescheduled') else 'scheduled'
            interview.metadata = {**(interview.metadata or {}), 'schedule_mode': 'manual', 'schedule_timezone': tz_name}
            _apply_execution_mode_and_links(
                interview=interview,
                payload=request.data,
                tenant_id=request.user.tenant_id,
            )
            interview.save(update_fields=[
                'scheduled_at', 'duration_minutes', 'status', 'metadata',
                'execution_mode', 'execution_provider_code', 'meeting_provider_code',
                'external_interview_link', 'meeting_link', 'interview_link', 'updated_at',
            ])
            InterviewPanelist.objects.filter(interview_id=interview.id).exclude(interviewer_id__in=panelist_ids).delete()
        else:
            required = ['application_id', 'candidate_id', 'requisition_id', 'interview_type']
            missing = [f for f in required if not request.data.get(f)]
            if missing:
                return error_response(f"Missing required fields: {', '.join(missing)}.")

            selected_type = request.data.get('interview_type')
            default_scorecard = InterviewScorecardTemplate.objects.filter(
                tenant_id=request.user.tenant_id,
                interview_type=selected_type,
                is_active=True,
                is_deleted=False,
            ).order_by('-updated_at').first()

            interview = Interview.objects.create(
                tenant_id=request.user.tenant_id,
                application_id=request.data.get('application_id'),
                candidate_id=request.data.get('candidate_id'),
                requisition_id=request.data.get('requisition_id'),
                interview_type=selected_type,
                title=request.data.get('title', ''),
                interview_round=int(request.data.get('interview_round') or 1),
                scheduled_at=scheduled_at,
                duration_minutes=duration_minutes,
                status='scheduled',
                scorecard_template_id=(default_scorecard.id if default_scorecard else None),
                created_by=request.user.id,
                metadata={'schedule_mode': 'manual', 'schedule_timezone': tz_name},
            )
            _apply_execution_mode_and_links(
                interview=interview,
                payload=request.data,
                tenant_id=request.user.tenant_id,
            )
            _seed_interview_questions_from_type_attachments(
                interview=interview,
                tenant_id=request.user.tenant_id,
            )
            interview.save(update_fields=[
                'execution_mode', 'execution_provider_code',
                'meeting_provider_code', 'external_interview_link',
                'meeting_link', 'interview_link', 'metadata', 'updated_at',
            ])

        for panelist_id in panelist_ids:
            InterviewPanelist.objects.get_or_create(
                interview_id=interview.id,
                interviewer_id=panelist_id,
                defaults={
                    'tenant_id': request.user.tenant_id,
                    'role': 'panelist',
                    'deadline_at': scheduled_at,
                }
            )

        events.interview.scheduled.send(sender=self.__class__, interview=interview)
        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview manually scheduled.",
            status_code=status.HTTP_201_CREATED if not interview_id else status.HTTP_200_OK,
        )


class InterviewScheduleActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        scheduled_at, err = _parse_schedule_dt(request.data.get('scheduled_at'), 'scheduled_at')
        if err:
            return err

        interview.scheduled_at = scheduled_at
        interview.status = 'rescheduled' if interview.status in ('scheduled', 'rescheduled') else 'scheduled'
        interview.metadata = {**(interview.metadata or {}), 'schedule_mode': request.data.get('mode', 'manual')}
        _apply_execution_mode_and_links(
            interview=interview,
            payload=request.data,
            tenant_id=request.user.tenant_id,
        )
        interview.save(update_fields=[
            'scheduled_at', 'status', 'metadata',
            'execution_mode', 'execution_provider_code',
            'meeting_provider_code', 'external_interview_link',
            'meeting_link', 'interview_link', 'updated_at',
        ])
        events.interview.scheduled.send(sender=self.__class__, interview=interview)

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview schedule updated.",
        )


class InterviewCancelActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)
        if interview.status in ('completed', 'cancelled'):
            return error_response("Cannot cancel a completed or already cancelled interview.")

        reason = request.data.get('reason', '')
        interview.status = 'cancelled'
        interview.feedback_summary = f"Cancelled: {reason}".strip()
        interview.metadata = {**(interview.metadata or {}), 'cancelled_by': str(request.user.id)}
        interview.save(update_fields=['status', 'feedback_summary', 'metadata', 'updated_at'])
        events.interview.cancelled.send(sender=self.__class__, interview=interview)
        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview cancelled.",
        )


class InterviewCalendarConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviewer_id = request.query_params.get('interviewer_id') or str(request.user.id)
        qs = InterviewCalendarConnection.objects.filter(
            tenant_id=request.user.tenant_id,
            interviewer_id=interviewer_id,
            is_active=True,
        )
        return success_response(
            data={'connections': InterviewCalendarConnectionSerializer(qs, many=True).data},
            meta={'providers_supported': ['google_calendar', 'outlook_calendar', 'apple_calendar', 'ics_external']},
            message="Calendar integration readiness retrieved.",
        )

    def post(self, request):
        serializer = InterviewCalendarConnectionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        connection = serializer.save(
            tenant_id=request.user.tenant_id,
            interviewer_id=request.data.get('interviewer_id') or str(request.user.id),
        )
        return success_response(
            data={'connection': InterviewCalendarConnectionSerializer(connection).data},
            status_code=status.HTTP_201_CREATED,
            message="Calendar connection configuration saved.",
        )


class InterviewIntegrationProviderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _ensure_integration_provider_registry()
        qs = InterviewIntegrationProvider.objects.filter(
            is_deleted=False,
        ).order_by('provider_type', 'name')
        provider_type = request.query_params.get('provider_type')
        if provider_type:
            qs = qs.filter(provider_type=provider_type)
        return success_response(
            data={'providers': InterviewIntegrationProviderSerializer(qs, many=True).data},
            message="Integration provider registry retrieved.",
            meta={'total': qs.count()},
        )


class InterviewIntegrationProviderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        _ensure_integration_provider_registry()
        obj = InterviewIntegrationProvider.objects.filter(id=pk, is_deleted=False).first()
        if not obj:
            return error_response("Provider not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewIntegrationProviderSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'provider': serializer.data},
            message="Provider updated.",
        )


class InterviewTenantProviderConnectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InterviewTenantProviderConnection.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).select_related('provider').order_by('-created_at')
        return success_response(
            data={'connections': InterviewTenantProviderConnectionSerializer(qs, many=True).data},
            message="Tenant provider connections retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = InterviewTenantProviderConnectionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        provider = InterviewIntegrationProvider.objects.filter(
            id=serializer.validated_data['provider_id'],
            is_deleted=False,
            is_active=True,
        ).first()
        if not provider:
            return error_response("Provider not found or inactive.", status_code=status.HTTP_404_NOT_FOUND)

        obj, _ = InterviewTenantProviderConnection.objects.update_or_create(
            tenant_id=request.user.tenant_id,
            provider=provider,
            defaults={
                'auth_data': serializer.validated_data.get('auth_data', {}),
                'config_data': serializer.validated_data.get('config_data', {}),
                'is_enabled': serializer.validated_data.get('is_enabled', True),
                'connection_status': serializer.validated_data.get('connection_status', 'configured'),
                'metadata': serializer.validated_data.get('metadata', {}),
                'created_by': request.user.id,
                'is_deleted': False,
                'deleted_at': None,
            },
        )
        return success_response(
            data={'connection': InterviewTenantProviderConnectionSerializer(obj).data},
            status_code=status.HTTP_201_CREATED,
            message="Tenant provider connection saved.",
        )


class InterviewTenantProviderConnectionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        obj = InterviewTenantProviderConnection.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not obj:
            return error_response("Connection not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewTenantProviderConnectionSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        update = serializer.validated_data
        if 'provider_id' in update:
            provider = InterviewIntegrationProvider.objects.filter(
                id=update['provider_id'], is_deleted=False, is_active=True,
            ).first()
            if not provider:
                return error_response("Provider not found or inactive.", status_code=status.HTTP_404_NOT_FOUND)
            obj.provider = provider
        for key in ['auth_data', 'config_data', 'is_enabled', 'connection_status', 'metadata']:
            if key in update:
                setattr(obj, key, update[key])
        obj.save()
        return success_response(
            data={'connection': InterviewTenantProviderConnectionSerializer(obj).data},
            message="Tenant provider connection updated.",
        )


class InterviewExecutionMappingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InterviewExecutionMapping.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).order_by('interview_type', 'stage_code')
        interview_type = request.query_params.get('interview_type')
        if interview_type:
            qs = qs.filter(interview_type=interview_type)
        return success_response(
            data={'mappings': InterviewExecutionMappingSerializer(qs, many=True).data},
            message="Interview execution mappings retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = InterviewExecutionMappingSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        obj = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'mapping': InterviewExecutionMappingSerializer(obj).data},
            message="Interview execution mapping saved.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewExecutionMappingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        obj = InterviewExecutionMapping.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not obj:
            return error_response("Execution mapping not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewExecutionMappingSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'mapping': serializer.data},
            message="Interview execution mapping updated.",
        )


class InterviewQuestionBankListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scope = request.query_params.get('scope')
        qs = InterviewQuestionBank.objects.filter(is_deleted=False, is_active=True)
        if scope:
            qs = qs.filter(scope=scope)
        # Global + tenant-local visibility
        qs = qs.filter(models.Q(scope='global') | models.Q(tenant_id=request.user.tenant_id))
        qtype = request.query_params.get('question_type')
        if qtype:
            qs = qs.filter(question_type=qtype)
        return success_response(
            data={'questions': InterviewQuestionBankSerializer(qs.order_by('-created_at'), many=True).data},
            message="Question bank retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = InterviewQuestionBankSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        scope = serializer.validated_data.get('scope', 'tenant')
        tenant_id = None if scope == 'global' else request.user.tenant_id
        obj = serializer.save(
            tenant_id=tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'question': InterviewQuestionBankSerializer(obj).data},
            message="Question created.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewQuestionBankDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, pk):
        return InterviewQuestionBank.objects.filter(
            id=pk,
            is_deleted=False,
        ).filter(
            models.Q(scope='global') | models.Q(tenant_id=request.user.tenant_id)
        ).first()

    def get(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'question': InterviewQuestionBankSerializer(obj).data},
            message="Question retrieved.",
        )

    def put(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewQuestionBankSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'question': serializer.data},
            message="Question updated.",
        )

    def delete(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return success_response(message="Question deleted.", status_code=status.HTTP_204_NO_CONTENT)


class InterviewQuestionAttachmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InterviewQuestionAttachment.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).select_related('question').order_by('order_index', 'created_at')
        attach_type = request.query_params.get('attach_type')
        if attach_type:
            qs = qs.filter(attach_type=attach_type)
        template_id = request.query_params.get('template_id')
        if template_id:
            qs = qs.filter(template_id=template_id)
        interview_type = request.query_params.get('interview_type')
        if interview_type:
            qs = qs.filter(interview_type=interview_type)
        return success_response(
            data={'attachments': InterviewQuestionAttachmentSerializer(qs, many=True).data},
            message="Question attachments retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = InterviewQuestionAttachmentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        q = InterviewQuestionBank.objects.filter(
            id=serializer.validated_data['question_id'],
            is_deleted=False,
        ).filter(models.Q(scope='global') | models.Q(tenant_id=request.user.tenant_id)).first()
        if not q:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)
        obj, _ = InterviewQuestionAttachment.objects.update_or_create(
            tenant_id=request.user.tenant_id,
            question=q,
            attach_type=serializer.validated_data['attach_type'],
            template_id=serializer.validated_data.get('template_id'),
            interview_type=serializer.validated_data.get('interview_type', ''),
            assessment_ref=serializer.validated_data.get('assessment_ref', ''),
            defaults={
                'is_active': serializer.validated_data.get('is_active', True),
                'order_index': serializer.validated_data.get('order_index', 0),
                'metadata': serializer.validated_data.get('metadata', {}),
                'created_by': request.user.id,
                'is_deleted': False,
                'deleted_at': None,
            }
        )
        _sync_template_questions_from_attachment(attachment=obj)
        return success_response(
            data={'attachment': InterviewQuestionAttachmentSerializer(obj).data},
            message="Question attached.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewQuestionAttachmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        obj = InterviewQuestionAttachment.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).select_related('question').first()
        if not obj:
            return error_response("Attachment not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewQuestionAttachmentSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        _sync_template_questions_from_attachment(attachment=obj)
        return success_response(
            data={'attachment': serializer.data},
            message="Question attachment updated.",
        )

    def delete(self, request, pk):
        obj = InterviewQuestionAttachment.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not obj:
            return error_response("Attachment not found.", status_code=status.HTTP_404_NOT_FOUND)
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return success_response(message="Question attachment deleted.", status_code=status.HTTP_204_NO_CONTENT)


class InterviewQuestionGroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InterviewQuestionGroup.objects.filter(
            is_deleted=False,
            is_active=True,
        ).filter(models.Q(scope='global') | models.Q(tenant_id=request.user.tenant_id)).prefetch_related('items__question')
        target_type = request.query_params.get('target_type')
        if target_type:
            qs = qs.filter(target_type=target_type)
        target_ref = request.query_params.get('target_ref')
        if target_ref:
            qs = qs.filter(target_ref=target_ref)
        return success_response(
            data={'groups': InterviewQuestionGroupSerializer(qs, many=True).data},
            message="Question groups retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = InterviewQuestionGroupSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        scope = serializer.validated_data.get('scope', 'tenant')
        tenant_id = None if scope == 'global' else request.user.tenant_id
        obj = serializer.save(
            tenant_id=tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'group': InterviewQuestionGroupSerializer(obj).data},
            message="Question group created.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewQuestionGroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, pk):
        return InterviewQuestionGroup.objects.filter(
            id=pk,
            is_deleted=False,
        ).filter(
            models.Q(scope='global') | models.Q(tenant_id=request.user.tenant_id)
        ).prefetch_related('items__question').first()

    def put(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return error_response("Question group not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewQuestionGroupSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            data={'group': serializer.data},
            message="Question group updated.",
        )

    def delete(self, request, pk):
        obj = self._get(request, pk)
        if not obj:
            return error_response("Question group not found.", status_code=status.HTTP_404_NOT_FOUND)
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return success_response(message="Question group deleted.", status_code=status.HTTP_204_NO_CONTENT)


class InterviewSchedulingLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        expires_in_days = int(request.data.get('expires_in_days') or 7)
        link = InterviewSchedulingLink.objects.create(
            tenant_id=request.user.tenant_id,
            interview_id=interview.id,
            token=uuid4().hex,
            timezone=request.data.get('timezone') or 'UTC',
            expires_at=timezone.now() + timedelta(days=expires_in_days),
            max_bookings=int(request.data.get('max_bookings') or 1),
            metadata={'mode': 'candidate_self'},
            created_by=request.user.id,
        )
        return success_response(
            data={
                'link': InterviewSchedulingLinkSerializer(link).data,
                'scheduling_url': f"/interviews/scheduling/self/{link.token}",
            },
            status_code=status.HTTP_201_CREATED,
            message="Candidate scheduling link created.",
        )


class InterviewSchedulingLinkPublicView(APIView):
    authentication_classes = []
    permission_classes = []

    def _get_link(self, token):
        return InterviewSchedulingLink.objects.filter(token=token, is_active=True).first()

    def get(self, request, token):
        link = self._get_link(token)
        if not link:
            return error_response("Scheduling link not found.", status_code=status.HTTP_404_NOT_FOUND)
        if link.expires_at and link.expires_at < timezone.now():
            return error_response("Scheduling link expired.", status_code=status.HTTP_410_GONE)

        interview = Interview.objects.filter(id=link.interview_id, is_deleted=False).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)
        panelist_ids = list(InterviewPanelist.objects.filter(interview_id=interview.id).values_list('interviewer_id', flat=True))
        if not panelist_ids:
            panelist_ids = [interview.created_by] if interview.created_by else []

        today = timezone.now().date()
        slots = compute_common_slots(
            tenant_id=link.tenant_id,
            interviewer_ids=panelist_ids,
            timezone_name=link.timezone or 'UTC',
            from_date=today,
            to_date=today + timedelta(days=7),
            duration_minutes=interview.duration_minutes or 60,
            limit=20,
        )
        return success_response(
            data={
                'link': InterviewSchedulingLinkSerializer(link).data,
                'interview': InterviewSerializer(interview).data,
                'slots': slots,
            },
            message="Candidate scheduling options retrieved.",
        )

    def post(self, request, token):
        link = self._get_link(token)
        if not link:
            return error_response("Scheduling link not found.", status_code=status.HTTP_404_NOT_FOUND)
        if link.expires_at and link.expires_at < timezone.now():
            return error_response("Scheduling link expired.", status_code=status.HTTP_410_GONE)
        if link.booking_count >= max(link.max_bookings, 1):
            return error_response("Scheduling link booking limit reached.", status_code=status.HTTP_409_CONFLICT)

        interview = Interview.objects.filter(id=link.interview_id, is_deleted=False).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        slot_start, err = _parse_schedule_dt(request.data.get('slot_start'), 'slot_start')
        if err:
            return err
        interview.scheduled_at = slot_start
        interview.status = 'scheduled' if interview.status not in ('scheduled', 'rescheduled') else 'rescheduled'
        interview.metadata = {
            **(interview.metadata or {}),
            'schedule_mode': 'candidate_self',
            'candidate_timezone': request.data.get('timezone') or link.timezone or 'UTC',
        }
        interview.save(update_fields=['scheduled_at', 'status', 'metadata', 'updated_at'])

        link.booking_count += 1
        link.last_selected_slot = slot_start
        if link.booking_count >= max(link.max_bookings, 1):
            link.is_active = False
        link.save(update_fields=['booking_count', 'last_selected_slot', 'is_active', 'updated_at'])

        events.interview.scheduled.send(sender=self.__class__, interview=interview)
        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview slot confirmed.",
        )


class InterviewFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        feedbacks = InterviewPanelist.objects.filter(interview_id=pk)
        return success_response(
            data={'feedbacks': InterviewPanelistSerializer(feedbacks, many=True).data},
            message="Feedback retrieved."
        )

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Get or create panelist record for this interviewer
        panelist, created = InterviewPanelist.objects.get_or_create(
            interview_id=pk,
            interviewer_id=request.user.id,
            defaults={'tenant_id': request.user.tenant_id}
        )

        score = request.data.get('score')
        recommendation = request.data.get('recommendation', '')
        feedback = request.data.get('feedback', '')
        question_scores = request.data.get('question_scores', [])

        panelist.score = score
        panelist.recommendation = recommendation
        panelist.feedback = feedback
        panelist.question_scores = question_scores
        panelist.submitted_at = timezone.now()
        panelist.save()

        # Calculate average human score from all panelists
        all_panelists = InterviewPanelist.objects.filter(
            interview_id=pk,
            score__isnull=False
        )
        if all_panelists.exists():
            avg_score = sum(p.score for p in all_panelists) / all_panelists.count()
            Interview.objects.filter(id=pk).update(human_score=avg_score)

        events.interview.feedback_submitted.send(
            sender=self.__class__,
            interview=interview,
            feedback=panelist,
        )
        return success_response(
            data={'feedback': InterviewPanelistSerializer(panelist).data},
            message="Feedback submitted."
        )


class CandidateInterviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def _ensure_runtime_shell(self, interview):
        runtime = dict((interview.metadata or {}).get('candidate_runtime_access') or {})
        changed = False
        if not runtime.get('token'):
            runtime['token'] = uuid4().hex
            changed = True
        if not runtime.get('token_expires_at') and interview.scheduled_at:
            runtime['token_expires_at'] = (interview.scheduled_at + timedelta(days=2)).isoformat()
            changed = True
        if 'single_attempt' not in runtime:
            runtime['single_attempt'] = True
            changed = True
        if 'attempts_used' not in runtime:
            runtime['attempts_used'] = 0
            changed = True
        if not runtime.get('attempt_status'):
            runtime['attempt_status'] = 'pending'
            changed = True
        if 'active_session_id' not in runtime:
            runtime['active_session_id'] = ''
            changed = True
        if 'rejoin_count' not in runtime:
            runtime['rejoin_count'] = 0
            changed = True
        if not isinstance(runtime.get('attempt_history'), list):
            runtime['attempt_history'] = []
            changed = True
        if not isinstance(runtime.get('security_events'), dict):
            runtime['security_events'] = {
                'tab_switch_count': 0,
                'copy_paste_count': 0,
                'multiple_window_count': 0,
                'last_event_at': None,
            }
            changed = True
        if not runtime.get('not_before') and interview.scheduled_at:
            runtime['not_before'] = (interview.scheduled_at - timedelta(minutes=30)).isoformat()
            changed = True
        if not runtime.get('expires_at') and interview.scheduled_at:
            runtime['expires_at'] = (interview.scheduled_at + timedelta(hours=8)).isoformat()
            changed = True
        if changed:
            md = interview.metadata or {}
            md['candidate_runtime_access'] = runtime
            interview.metadata = md
            interview.save(update_fields=['metadata', 'updated_at'])
        return runtime

    def _runtime_error(self, message, code, status_code):
        return error_response(message, errors={'code': code}, status_code=status_code)

    def _validate_runtime_access(self, interview, request, *, allow_rejoin=False):
        runtime = self._ensure_runtime_shell(interview)
        access_token = (
            request.query_params.get('access_token')
            or request.headers.get('X-Interview-Token')
            or request.data.get('access_token')
        )
        if not access_token or access_token != runtime.get('token'):
            return None, None, self._runtime_error("Invalid interview access token.", "token_invalid", status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        not_before = parse_datetime(runtime.get('not_before')) if runtime.get('not_before') else None
        expires_at = parse_datetime(runtime.get('expires_at')) if runtime.get('expires_at') else None
        token_expires_at = parse_datetime(runtime.get('token_expires_at')) if runtime.get('token_expires_at') else None
        if not_before and now < not_before:
            return None, None, self._runtime_error("Interview runtime not open yet.", "time_window_early", status.HTTP_403_FORBIDDEN)
        if (expires_at and now > expires_at) or (token_expires_at and now > token_expires_at):
            return None, None, self._runtime_error("Interview runtime access expired.", "token_expired", status.HTTP_410_GONE)

        session_id = (
            request.query_params.get('session_id')
            or request.headers.get('X-Interview-Session')
            or request.data.get('session_id')
            or ''
        ).strip()
        active_session_id = (runtime.get('active_session_id') or '').strip()
        if active_session_id and session_id and active_session_id != session_id:
            return None, None, self._runtime_error("Session locked on another active session.", "session_locked", status.HTTP_409_CONFLICT)
        if active_session_id and not session_id and not allow_rejoin:
            return None, None, self._runtime_error("Active session detected. Rejoin with the same session.", "session_locked", status.HTTP_409_CONFLICT)

        return runtime, (session_id or active_session_id or uuid4().hex), None

    def get(self, request):
        interviews = Interview.objects.filter(
            candidate_id=request.user.id,
            is_deleted=False
        ).order_by('scheduled_at')

        now = timezone.now()
        buckets = {
            'upcoming': [],
            'pending': [],
            'completed': [],
            'missed': [],
        }
        rows = []
        for interview in interviews:
            runtime = self._ensure_runtime_shell(interview)
            row = InterviewSerializer(interview).data
            row['candidate_runtime'] = runtime
            row['secure_runtime_url'] = f"/candidate/interviews/{interview.id}/runtime?access_token={runtime.get('token')}"
            row['candidate_status'] = 'missed' if interview.status == 'no_show' else interview.status
            rows.append(row)
            if interview.status == 'completed':
                buckets['completed'].append(row)
            elif interview.status == 'no_show':
                buckets['missed'].append(row)
            elif interview.status in {'scheduled', 'rescheduled'}:
                if interview.scheduled_at and interview.scheduled_at >= now:
                    buckets['upcoming'].append(row)
                else:
                    buckets['pending'].append(row)
            elif interview.status == 'in_progress':
                buckets['pending'].append(row)

        return success_response(
            data={
                'interviews': rows,
                'upcoming_interviews': buckets['upcoming'],
                'pending_interviews': buckets['pending'],
                'completed_interviews': buckets['completed'],
                'missed_interviews': buckets['missed'],
            },
            message="Your interviews retrieved."
        )


class CandidateInterviewInstructionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        runtime = CandidateInterviewListView()._ensure_runtime_shell(interview)
        template = InterviewTemplate.objects.filter(id=interview.template_id, is_deleted=False).first() if interview.template_id else None
        instructions = template.instructions if template else ''
        return success_response(
            data={
                'interview': InterviewSerializer(interview).data,
                'instructions': instructions or "Please review the interview details and join on time.",
                'runtime': runtime,
                'secure_runtime_url': f"/candidate/interviews/{interview.id}/runtime?access_token={runtime.get('token')}",
                'security_shell': {
                    'token_based_access': True,
                    'time_based_access': True,
                    'single_attempt_shell': bool(runtime.get('single_attempt', True)),
                    'session_lock': True,
                },
            },
            message="Candidate interview instructions retrieved.",
        )


class CandidateInterviewRuntimeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        shell = CandidateInterviewListView()
        runtime, session_id, err = shell._validate_runtime_access(interview, request, allow_rejoin=True)
        if err:
            return err
        if runtime.get('single_attempt', True) and int(runtime.get('attempts_used') or 0) >= 1 and interview.status != 'in_progress':
            return shell._runtime_error("Single attempt already used for this interview.", "attempt_blocked", status.HTTP_409_CONFLICT)

        questions = InterviewQuestion.objects.filter(interview_id=interview.id).order_by('order_index')
        return success_response(
            data={
                'interview': InterviewSerializer(interview).data,
                'questions': InterviewQuestionSerializer(questions, many=True).data,
                'runtime': runtime,
                'session': {'session_id': session_id, 'active_session_id': runtime.get('active_session_id')},
                'runtime_shell': {
                    'timer_enabled': True,
                    'video_recording_future': True,
                    'assignment_upload_supported': True,
                },
            },
            message="Candidate interview runtime loaded.",
        )


class CandidateInterviewStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)
        candidate_status = 'missed' if interview.status == 'no_show' else interview.status
        return success_response(
            data={
                'interview_id': str(interview.id),
                'status': candidate_status,
                'attempt_tracking': (interview.metadata or {}).get('candidate_runtime_access', {}),
                'decision': InterviewDecisionSerializer(InterviewDecision.objects.filter(interview_id=interview.id).first()).data if InterviewDecision.objects.filter(interview_id=interview.id).exists() else None,
                'scores': {
                    'overall_score': interview.overall_score,
                    'human_score': interview.human_score,
                    'ai_score': interview.ai_score,
                },
            },
            message="Candidate interview status retrieved.",
        )


class CandidateInterviewStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                candidate_id=request.user.id,
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        if interview.status not in {'scheduled', 'in_progress', 'rescheduled'}:
            return error_response("Interview is not available to start.")

        shell = CandidateInterviewListView()
        runtime, session_id, err = shell._validate_runtime_access(interview, request, allow_rejoin=True)
        if err:
            return err
        attempts_used = int(runtime.get('attempts_used') or 0)
        if runtime.get('single_attempt', True) and attempts_used >= 1 and interview.status != 'in_progress':
            return shell._runtime_error("Single attempt already used for this interview.", "attempt_blocked", status.HTTP_409_CONFLICT)

        if interview.status == 'in_progress':
            active_session_id = runtime.get('active_session_id') or ''
            if active_session_id and active_session_id == session_id:
                runtime['rejoin_count'] = int(runtime.get('rejoin_count') or 0) + 1
                runtime['attempt_status'] = 'in_progress'
                md = interview.metadata or {}
                md['candidate_runtime_access'] = runtime
                interview.metadata = md
                interview.save(update_fields=['metadata', 'updated_at'])
                questions = InterviewQuestion.objects.filter(interview_id=pk).order_by('order_index')
                return success_response(
                    data={
                        'interview': InterviewSerializer(interview).data,
                        'questions': InterviewQuestionSerializer(questions, many=True).data,
                        'rejoined': True,
                    },
                    message="Interview session rejoined.",
                )
            return shell._runtime_error("Session locked on another active session.", "session_locked", status.HTTP_409_CONFLICT)

        interview.status = 'in_progress'
        interview.started_at = timezone.now()
        runtime['attempts_used'] = attempts_used + 1
        runtime['attempt_status'] = 'in_progress'
        runtime['active_session_id'] = session_id
        runtime['attempt_started_at'] = interview.started_at.isoformat()
        runtime['attempt_history'] = runtime.get('attempt_history') or []
        runtime['attempt_history'].append({
            'attempt_no': runtime['attempts_used'],
            'session_id': session_id,
            'start_time': interview.started_at.isoformat(),
            'end_time': None,
            'duration_seconds': 0,
            'status': 'in_progress',
        })
        md = interview.metadata or {}
        md['candidate_runtime_access'] = runtime
        interview.metadata = md
        interview.save(update_fields=['status', 'started_at', 'metadata', 'updated_at'])

        questions = InterviewQuestion.objects.filter(
            interview_id=pk
        ).order_by('order_index')

        return success_response(
            data={
                'interview': InterviewSerializer(interview).data,
                'questions': InterviewQuestionSerializer(questions, many=True).data,
                'session_id': session_id,
            },
            message="Interview started. Good luck!"
        )


class CandidateSubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                candidate_id=request.user.id,
                status='in_progress',
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found or not in progress.", status_code=status.HTTP_404_NOT_FOUND)

        question_id = request.data.get('question_id')
        if not question_id:
            return error_response("question_id is required.")

        try:
            question = InterviewQuestion.objects.get(
                id=question_id,
                interview_id=pk
            )
        except InterviewQuestion.DoesNotExist:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)

        question.candidate_answer = request.data.get('answer_text', '')
        question.candidate_video_url = request.data.get('video_url', '')
        if request.data.get('assignment_url'):
            md = question.metadata or {}
            md['assignment_url'] = request.data.get('assignment_url')
            question.metadata = md
        question.answered_at = timezone.now()
        question.save(update_fields=['candidate_answer', 'candidate_video_url', 'metadata', 'answered_at', 'updated_at'])

        return success_response(
            data={'question': InterviewQuestionSerializer(question).data},
            message="Answer submitted."
        )


class CandidateCompleteInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            interview = Interview.objects.get(
                id=pk,
                candidate_id=request.user.id,
                status='in_progress',
                is_deleted=False
            )
        except Interview.DoesNotExist:
            return error_response("Interview not found or not in progress.", status_code=status.HTTP_404_NOT_FOUND)

        interview.status = 'completed'
        interview.completed_at = timezone.now()
        runtime = CandidateInterviewListView()._ensure_runtime_shell(interview)
        runtime['attempt_status'] = 'completed'
        runtime['active_session_id'] = ''
        runtime['attempt_ended_at'] = interview.completed_at.isoformat()
        start_dt = parse_datetime(runtime.get('attempt_started_at')) if runtime.get('attempt_started_at') else interview.started_at
        if start_dt and interview.completed_at:
            runtime['attempt_duration_seconds'] = int((interview.completed_at - start_dt).total_seconds())
        history = runtime.get('attempt_history') or []
        if history:
            last = history[-1]
            if last.get('status') == 'in_progress':
                last['status'] = 'completed'
                last['end_time'] = interview.completed_at.isoformat()
                last['duration_seconds'] = int(runtime.get('attempt_duration_seconds') or 0)
                history[-1] = last
        runtime['attempt_history'] = history
        md = interview.metadata or {}
        md['candidate_runtime_access'] = runtime
        interview.metadata = md
        interview.save(update_fields=['status', 'completed_at', 'metadata', 'updated_at'])

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview completed. Thank you!"
        )


class CandidateInterviewSecurityEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            candidate_id=request.user.id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        runtime = CandidateInterviewListView()._ensure_runtime_shell(interview)
        event_type = str(request.data.get('event_type') or '').strip().lower()
        security = dict(runtime.get('security_events') or {})
        security.setdefault('tab_switch_count', 0)
        security.setdefault('copy_paste_count', 0)
        security.setdefault('multiple_window_count', 0)
        security['last_event_at'] = timezone.now().isoformat()
        if event_type == 'tab_switch':
            security['tab_switch_count'] += 1
        elif event_type == 'copy_paste':
            security['copy_paste_count'] += 1
        elif event_type == 'multiple_window':
            security['multiple_window_count'] += 1

        runtime['security_events'] = security
        md = interview.metadata or {}
        md['candidate_runtime_access'] = runtime
        interview.metadata = md
        interview.save(update_fields=['metadata', 'updated_at'])
        return success_response(
            data={'security_events': security},
            message="Security event tracked.",
        )


# ─── Interview Types ───────────────────────────────────────────────────────────

class InterviewTypeListView(APIView):
    """GET /interviews/types/ — list active types (all authenticated users)."""
    permission_classes = [IsAuthenticated, can_view_interview_types]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Interview types retrieved."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
        }
    )
    def get(self, request):
        active_only = str(request.query_params.get('active_only', '')).lower() in {'1', 'true', 'yes'}
        types = InterviewTypeService.list_registry(active_only=active_only)
        return success_response(
            data={'types': InterviewTypeSerializer(types, many=True).data},
            message="Interview types retrieved.",
            meta={'total': types.count()},
        )

    @extend_schema(
        request=InterviewTypeSerializer,
        responses={
            201: OpenApiResponse(description="Interview type created."),
            400: OpenApiResponse(description="Validation failed."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
        }
    )
    def post(self, request):
        self.permission_classes = [IsAuthenticated, can_manage_interview_types]
        self.check_permissions(request)

        serializer = InterviewTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        itype = InterviewTypeService.create(
            name=serializer.validated_data['name'],
            code=serializer.validated_data['code'],
            description=serializer.validated_data.get('description', ''),
            execution_mode=serializer.validated_data.get('execution_mode', 'native'),
            configurable=serializer.validated_data.get('configurable', True),
            type_configuration=serializer.validated_data.get('type_configuration', {}),
        )
        return success_response(
            data={'type': InterviewTypeSerializer(itype).data},
            message="Interview type created.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewTypeDetailView(APIView):
    """GET/PUT /interviews/types/<uuid:pk>/"""
    permission_classes = [IsAuthenticated, can_view_interview_types]

    def _get(self, pk):
        return InterviewType.objects.filter(id=pk, is_deleted=False).first()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Interview type retrieved."),
            404: OpenApiResponse(description="Not found."),
        }
    )
    def get(self, request, pk):
        itype = self._get(pk)
        if not itype:
            return error_response("Interview type not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'type': InterviewTypeSerializer(itype).data},
            message="Interview type retrieved.",
        )

    @extend_schema(
        request=InterviewTypeSerializer,
        responses={
            200: OpenApiResponse(description="Interview type updated."),
            400: OpenApiResponse(description="Validation failed."),
            404: OpenApiResponse(description="Not found."),
        }
    )
    def put(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_manage_interview_types]
        self.check_permissions(request)

        itype = self._get(pk)
        if not itype:
            return error_response("Interview type not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = InterviewTypeSerializer(itype, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'type': serializer.data},
            message="Interview type updated.",
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Interview type deleted."),
            404: OpenApiResponse(description="Not found."),
        }
    )
    def delete(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_manage_interview_types]
        self.check_permissions(request)

        itype = self._get(pk)
        if not itype:
            return error_response("Interview type not found.", status_code=status.HTTP_404_NOT_FOUND)

        itype.soft_delete()
        return success_response(message="Interview type deleted.", status_code=status.HTTP_204_NO_CONTENT)


class InterviewTypeConfigView(APIView):
    permission_classes = [IsAuthenticated, can_view_interview_types]

    def _get(self, pk):
        return InterviewType.objects.filter(id=pk, is_deleted=False).first()

    def get(self, request, pk):
        itype = self._get(pk)
        if not itype:
            return error_response("Interview type not found.", status_code=status.HTTP_404_NOT_FOUND)
        payload = {
            'template': bool((itype.type_configuration or {}).get('template', True)),
            'scorecard': bool((itype.type_configuration or {}).get('scorecard', True)),
            'scheduling': bool((itype.type_configuration or {}).get('scheduling', True)),
            'automation': bool((itype.type_configuration or {}).get('automation', True)),
            'prequalification': bool((itype.type_configuration or {}).get('prequalification', False)),
        }
        return success_response(
            data={'type': InterviewTypeSerializer(itype).data, 'configuration': payload},
            message="Interview type configuration retrieved.",
        )

    def put(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_manage_interview_types]
        self.check_permissions(request)

        itype = self._get(pk)
        if not itype:
            return error_response("Interview type not found.", status_code=status.HTTP_404_NOT_FOUND)

        cfg = {
            'template': bool(request.data.get('template', True)),
            'scorecard': bool(request.data.get('scorecard', True)),
            'scheduling': bool(request.data.get('scheduling', True)),
            'automation': bool(request.data.get('automation', True)),
            'prequalification': bool(request.data.get('prequalification', False)),
        }
        itype.type_configuration = cfg
        itype.configurable = bool(request.data.get('configurable', itype.configurable))
        if request.data.get('execution_mode'):
            itype.execution_mode = request.data.get('execution_mode')
        if 'is_active' in request.data:
            itype.is_active = bool(request.data.get('is_active'))
        itype.save(update_fields=['type_configuration', 'configurable', 'execution_mode', 'is_active', 'updated_at'])

        return success_response(
            data={'type': InterviewTypeSerializer(itype).data, 'configuration': cfg},
            message="Interview type configuration updated.",
        )


# ─── Structured Feedback ───────────────────────────────────────────────────────

class InterviewStructuredFeedbackView(APIView):
    """
    GET  /interviews/<uuid:pk>/structured-feedback/  — list all feedback for an interview
    POST /interviews/<uuid:pk>/structured-feedback/  — submit / update feedback (current user)
    """

    def _get_interview(self, request, pk):
        return Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Feedback list retrieved."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Interview not found."),
        }
    )
    def get(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_view_feedback]
        self.check_permissions(request)

        if not self._get_interview(request, pk):
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        qs = InterviewFeedbackService.list_for_interview(
            interview_id=pk,
            tenant_id=request.user.tenant_id,
        )
        return success_response(
            data={'feedback': InterviewFeedbackSerializer(qs, many=True).data},
            message="Feedback retrieved.",
            meta={'total': qs.count()},
        )

    @extend_schema(
        request=InterviewFeedbackSerializer,
        responses={
            200: OpenApiResponse(description="Feedback submitted."),
            400: OpenApiResponse(description="Validation failed."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Interview not found."),
        }
    )
    def post(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_submit_feedback]
        self.check_permissions(request)

        interview = self._get_interview(request, pk)
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = InterviewFeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        d = serializer.validated_data
        scorecard_ratings = request.data.get('scorecard_ratings', {}) or {}
        score_for_save = d.get('score')
        if score_for_save is None and isinstance(scorecard_ratings, dict) and scorecard_ratings:
            # Best-effort numeric aggregation for 1-5 style ratings.
            numeric_values = []
            for value in scorecard_ratings.values():
                if isinstance(value, (int, float)):
                    numeric_values.append(float(value))
            if numeric_values:
                score_for_save = sum(numeric_values) / len(numeric_values)
        feedback = InterviewFeedbackService.submit(
            tenant_id=request.user.tenant_id,
            interview_id=pk,
            panelist_id=request.user.id,
            score=score_for_save,
            notes=d.get('notes', ''),
            recommendation=d.get('recommendation', ''),
            criteria_scores=d.get('criteria_scores', {}),
            scorecard_ratings=scorecard_ratings,
        )
        events.interview.feedback_submitted.send(
            sender=self.__class__,
            interview=interview,
            feedback=feedback,
        )
        return success_response(
            data={
                'feedback': InterviewFeedbackSerializer(feedback).data,
                'panel_decision': _panel_decision_payload(pk),
            },
            message="Feedback submitted.",
        )


class InterviewKitView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        candidate = Candidate.objects.filter(id=interview.candidate_id, is_deleted=False).first()
        candidate_profile = CandidateProfile.objects.filter(candidate_id=interview.candidate_id, is_deleted=False).first()
        job = JobRequisition.objects.filter(id=interview.requisition_id, is_deleted=False).first()
        template = InterviewTemplate.objects.filter(
            id=interview.template_id,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first() if interview.template_id else None
        questions = InterviewQuestion.objects.filter(interview_id=interview.id).order_by('order_index')
        scorecard = None
        if interview.scorecard_template_id:
            scorecard = InterviewScorecardTemplate.objects.filter(
                id=interview.scorecard_template_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False,
            ).prefetch_related('attributes').first()
        if not scorecard:
            scorecard = InterviewScorecardTemplate.objects.filter(
                tenant_id=request.user.tenant_id,
                interview_type=interview.interview_type,
                is_active=True,
                is_deleted=False,
            ).prefetch_related('attributes').order_by('-updated_at').first()

        panelists = InterviewPanelist.objects.filter(interview_id=interview.id)
        feedbacks = InterviewFeedback.objects.filter(interview_id=interview.id, is_deleted=False)

        return success_response(
            data={
                'interview': InterviewSerializer(interview).data,
                'candidate': {
                    'id': str(candidate.id) if candidate else str(interview.candidate_id),
                    'full_name': candidate.full_name if candidate else '',
                    'email': candidate.email if candidate else '',
                    'phone': candidate.phone if candidate else '',
                    'current_title': candidate.current_title if candidate else '',
                    'resume_url': (candidate.resume_url if candidate else '') or (candidate_profile.cv_url if candidate_profile else ''),
                },
                'job': {
                    'id': str(job.id) if job else str(interview.requisition_id),
                    'title': job.title if job else '',
                    'job_ref_id': job.job_ref_id if job else '',
                    'description': job.description if job else '',
                },
                'resume_url': ((candidate.resume_url if candidate else '') or (candidate_profile.cv_url if candidate_profile else '')),
                'instructions': (template.instructions if template else ''),
                'questions': InterviewQuestionSerializer(questions, many=True).data,
                'scorecard': InterviewScorecardTemplateSerializer(scorecard).data if scorecard else None,
                'panelists': InterviewPanelistSerializer(panelists, many=True).data,
                'feedback': InterviewFeedbackSerializer(feedbacks, many=True).data,
                'panel_decision': _panel_decision_payload(interview.id),
            },
            message="Interview kit retrieved.",
        )


class InterviewPanelDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        payload = _panel_decision_payload(pk)
        return success_response(
            data={'panel_decision': payload},
            message="Panel decision computed.",
        )


# ─── Interview Decision ────────────────────────────────────────────────────────

class InterviewDecisionView(APIView):
    """
    GET  /interviews/<uuid:pk>/decision/  — retrieve the final decision
    POST /interviews/<uuid:pk>/decision/  — record / update the final decision
    """

    def _get_interview(self, request, pk):
        return Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Decision retrieved."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Interview or decision not found."),
        }
    )
    def get(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_view_decision]
        self.check_permissions(request)

        if not self._get_interview(request, pk):
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        decision = InterviewDecisionService.get_for_interview(interview_id=pk)
        if not decision:
            return error_response("No decision recorded yet.", status_code=status.HTTP_404_NOT_FOUND)

        history = InterviewDecisionService.history_for_interview(
            interview_id=pk,
            tenant_id=request.user.tenant_id,
        )
        return success_response(
            data={
                'decision': InterviewDecisionSerializer(decision).data,
                'history': InterviewDecisionHistorySerializer(history, many=True).data,
            },
            message="Decision retrieved.",
        )

    @extend_schema(
        request=InterviewDecisionSerializer,
        responses={
            200: OpenApiResponse(description="Decision recorded."),
            400: OpenApiResponse(description="Validation failed."),
            401: OpenApiResponse(description="Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Interview not found."),
        }
    )
    def post(self, request, pk):
        self.permission_classes = [IsAuthenticated, can_record_decision]
        self.check_permissions(request)

        interview = self._get_interview(request, pk)
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = InterviewDecisionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        d = serializer.validated_data
        decision = InterviewDecisionService.record(
            tenant_id=request.user.tenant_id,
            interview=interview,
            decision=d['decision'],
            notes=d.get('notes', ''),
            decided_by=request.user.id,
            decision_source=d.get('decision_source', 'manual'),
            decision_mode=d.get('decision_mode', 'manual'),
            is_override=bool(request.data.get('is_override', False)),
            override_reason=request.data.get('override_reason', ''),
            metadata={
                'module': 'ICC-DECISION-ENGINE-01',
                'interview_type': interview.interview_type,
            },
        )
        return success_response(
            data={'decision': InterviewDecisionSerializer(decision).data},
            message="Decision recorded.",
        )


class InterviewDecisionHistoryView(APIView):
    permission_classes = [IsAuthenticated, can_view_decision]

    def get(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)
        history = InterviewDecisionService.history_for_interview(
            interview_id=pk,
            tenant_id=request.user.tenant_id,
        )
        return success_response(
            data={'history': InterviewDecisionHistorySerializer(history, many=True).data},
            message="Decision history retrieved.",
            meta={'total': history.count()},
        )


class InterviewDecisionEvaluateView(APIView):
    permission_classes = [IsAuthenticated, can_record_decision]

    def post(self, request, pk):
        interview = Interview.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not interview:
            return error_response("Interview not found.", status_code=status.HTTP_404_NOT_FOUND)

        evaluation = InterviewDecisionService.evaluate(
            interview=interview,
            source_inputs=request.data.get('source_inputs', {}),
            thresholds=request.data.get('thresholds', {}),
        )

        if bool(request.data.get('persist', False)):
            decision = InterviewDecisionService.record(
                tenant_id=request.user.tenant_id,
                interview=interview,
                decision=evaluation['decision'],
                notes=request.data.get('notes') or evaluation.get('rationale', ''),
                decided_by=request.user.id,
                decision_source=evaluation.get('decision_source', 'automation_rules'),
                decision_mode=evaluation.get('decision_mode', 'auto'),
                is_override=bool(request.data.get('is_override', False)),
                override_reason=request.data.get('override_reason', ''),
                metadata={
                    'source_inputs': request.data.get('source_inputs', {}),
                    'thresholds': request.data.get('thresholds', {}),
                    'panel': evaluation.get('panel', {}),
                    'module': 'ICC-DECISION-ENGINE-01',
                },
            )
            return success_response(
                data={
                    'evaluation': evaluation,
                    'decision': InterviewDecisionSerializer(decision).data,
                },
                message="Decision evaluated and persisted.",
            )

        return success_response(
            data={'evaluation': evaluation},
            message="Decision evaluated.",
        )


# ─── Interview Flows ───────────────────────────────────────────────────────────

class InterviewFlowListView(APIView):
    """
    GET  /interviews/flows/  — list all active flows for the tenant
    POST /interviews/flows/  — create a new flow
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        flows = InterviewFlow.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        )
        return success_response(
            data={'flows': InterviewFlowSerializer(flows, many=True).data},
            message="Flows retrieved.",
            meta={'total': flows.count()},
        )

    def post(self, request):
        serializer = InterviewFlowSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        flow = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        return success_response(
            data={'flow': InterviewFlowSerializer(flow).data},
            message="Flow created.",
            status_code=status.HTTP_201_CREATED,
        )


class InterviewFlowDetailView(APIView):
    """
    GET    /interviews/flows/<uuid:pk>/  — retrieve flow
    PUT    /interviews/flows/<uuid:pk>/  — update flow
    DELETE /interviews/flows/<uuid:pk>/  — soft-delete flow
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return InterviewFlow.objects.filter(
            id=pk,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()

    def get(self, request, pk):
        flow = self.get_object(request, pk)
        if not flow:
            return error_response("Flow not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'flow': InterviewFlowSerializer(flow).data},
            message="Flow retrieved.",
        )

    def put(self, request, pk):
        flow = self.get_object(request, pk)
        if not flow:
            return error_response("Flow not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = InterviewFlowSerializer(flow, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'flow': serializer.data},
            message="Flow updated.",
        )

    def delete(self, request, pk):
        flow = self.get_object(request, pk)
        if not flow:
            return error_response("Flow not found.", status_code=status.HTTP_404_NOT_FOUND)

        flow.soft_delete()
        return success_response(
            message="Flow deleted.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
