from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.interviews.models import Interview, InterviewTemplate, InterviewPanelist, InterviewQuestion
from apps.interviews.serializers import (
    InterviewSerializer, InterviewTemplateSerializer,
    InterviewPanelistSerializer, InterviewQuestionSerializer,
)
from apps.pipeline.models import Application
from apps.core.responses import success_response, error_response
from apps.core import events


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
        )

        # Create questions from template
        for q_data in questions_to_create:
            InterviewQuestion.objects.create(
                tenant_id=request.user.tenant_id,
                interview_id=interview.id,
                **q_data
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

        serializer = InterviewSerializer(interview, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
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
            Interview.objects.get(
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

        return success_response(
            data={'feedback': InterviewPanelistSerializer(panelist).data},
            message="Feedback submitted."
        )


class CandidateInterviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interviews = Interview.objects.filter(
            candidate_id=request.user.id,
            is_deleted=False
        ).order_by('scheduled_at')

        return success_response(
            data={'interviews': InterviewSerializer(interviews, many=True).data},
            message="Your interviews retrieved."
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

        if interview.status != 'scheduled':
            return error_response("Interview is not available to start.")

        interview.status = 'in_progress'
        interview.started_at = timezone.now()
        interview.save(update_fields=['status', 'started_at', 'updated_at'])

        questions = InterviewQuestion.objects.filter(
            interview_id=pk
        ).order_by('order_index')

        return success_response(
            data={
                'interview': InterviewSerializer(interview).data,
                'questions': InterviewQuestionSerializer(questions, many=True).data,
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
        question.answered_at = timezone.now()
        question.save(update_fields=['candidate_answer', 'candidate_video_url', 'answered_at', 'updated_at'])

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
        interview.save(update_fields=['status', 'completed_at', 'updated_at'])

        return success_response(
            data={'interview': InterviewSerializer(interview).data},
            message="Interview completed. Thank you!"
        )
