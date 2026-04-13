from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.prequalification.models import (
    PrequalForm, PrequalSection, PrequalQuestion, PrequalRule, PrequalResponse,
)
from apps.prequalification.serializers import (
    PrequalFormSerializer, PrequalFormDetailSerializer,
    PrequalSectionSerializer, PrequalQuestionSerializer,
    PrequalRuleSerializer, PrequalResponseSerializer,
)
from apps.prequalification.services import (
    PrequalFormService, PrequalSectionService,
    PrequalQuestionService, PrequalRuleService,
)
from apps.prequalification.permissions import CanManagePrequalForms, CanViewPrequalForms
from apps.core.responses import success_response, error_response
from apps.automation.services import AutomationEngine


# ─── Forms ────────────────────────────────────────────────────────────────────

class PrequalFormListView(APIView):
    permission_classes = [IsAuthenticated, CanViewPrequalForms]

    def get(self, request):
        forms = PrequalFormService.list_for_tenant(request.user.tenant_id)
        return success_response(
            data={'forms': PrequalFormSerializer(forms, many=True).data},
            message="Forms retrieved.",
            meta={'total': forms.count()},
        )

    def post(self, request):
        self.permission_classes = [IsAuthenticated, CanManagePrequalForms]
        self.check_permissions(request)

        serializer = PrequalFormSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        form = PrequalFormService.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            metadata=serializer.validated_data.get('metadata', {}),
        )
        return success_response(
            data={'form': PrequalFormSerializer(form).data},
            message="Form created.",
            status_code=status.HTTP_201_CREATED,
        )


class PrequalFormDetailView(APIView):
    permission_classes = [IsAuthenticated, CanViewPrequalForms]

    def get_object(self, request, pk):
        return PrequalFormService.get(pk, request.user.tenant_id)

    def get(self, request, pk):
        form = self.get_object(request, pk)
        if not form:
            return error_response("Form not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'form': PrequalFormDetailSerializer(form).data},
            message="Form retrieved.",
        )

    def put(self, request, pk):
        self.permission_classes = [IsAuthenticated, CanManagePrequalForms]
        self.check_permissions(request)

        form = self.get_object(request, pk)
        if not form:
            return error_response("Form not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = PrequalFormSerializer(form, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'form': serializer.data},
            message="Form updated.",
        )

    def delete(self, request, pk):
        self.permission_classes = [IsAuthenticated, CanManagePrequalForms]
        self.check_permissions(request)

        form = self.get_object(request, pk)
        if not form:
            return error_response("Form not found.", status_code=status.HTTP_404_NOT_FOUND)

        form.soft_delete()
        return success_response(
            message="Form deleted.",
            status_code=status.HTTP_204_NO_CONTENT,
        )


# ─── Sections ─────────────────────────────────────────────────────────────────

class PrequalSectionListView(APIView):
    permission_classes = [IsAuthenticated, CanViewPrequalForms]

    def get(self, request):
        form_id = request.query_params.get('form_id')
        if not form_id:
            return error_response("form_id is required.")
        sections = PrequalSectionService.list_for_form(form_id)
        return success_response(
            data={'sections': PrequalSectionSerializer(sections, many=True).data},
            message="Sections retrieved.",
        )

    def post(self, request):
        self.permission_classes = [IsAuthenticated, CanManagePrequalForms]
        self.check_permissions(request)

        serializer = PrequalSectionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        d = serializer.validated_data
        section = PrequalSectionService.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            form_id=d['form'].id,
            title=d['title'],
            description=d.get('description', ''),
            order=d.get('order', 0),
            metadata=d.get('metadata', {}),
        )
        return success_response(
            data={'section': PrequalSectionSerializer(section).data},
            message="Section created.",
            status_code=status.HTTP_201_CREATED,
        )


# ─── Questions ────────────────────────────────────────────────────────────────

class PrequalQuestionListView(APIView):
    permission_classes = [IsAuthenticated, CanViewPrequalForms]

    def get(self, request):
        section_id = request.query_params.get('section_id')
        if not section_id:
            return error_response("section_id is required.")
        questions = PrequalQuestionService.list_for_section(section_id)
        return success_response(
            data={'questions': PrequalQuestionSerializer(questions, many=True).data},
            message="Questions retrieved.",
        )

    def post(self, request):
        self.permission_classes = [IsAuthenticated, CanManagePrequalForms]
        self.check_permissions(request)

        serializer = PrequalQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        d = serializer.validated_data
        question = PrequalQuestionService.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            section_id=d['section'].id,
            question_text=d['question_text'],
            question_type=d.get('question_type', 'yes_no'),
            required=d.get('required', True),
            order=d.get('order', 0),
            help_text=d.get('help_text', ''),
            options_json=d.get('options_json', []),
            score_weight=d.get('score_weight', 0),
            is_knockout=d.get('is_knockout', False),
            metadata=d.get('metadata', {}),
        )
        return success_response(
            data={'question': PrequalQuestionSerializer(question).data},
            message="Question created.",
            status_code=status.HTTP_201_CREATED,
        )


# ─── Rules ────────────────────────────────────────────────────────────────────

class PrequalRuleListView(APIView):
    permission_classes = [IsAuthenticated, CanViewPrequalForms]

    def get(self, request):
        question_id = request.query_params.get('question_id')
        if not question_id:
            return error_response("question_id is required.")
        rules = PrequalRuleService.list_for_question(question_id)
        return success_response(
            data={'rules': PrequalRuleSerializer(rules, many=True).data},
            message="Rules retrieved.",
        )

    def post(self, request):
        self.permission_classes = [IsAuthenticated, CanManagePrequalForms]
        self.check_permissions(request)

        serializer = PrequalRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        d = serializer.validated_data
        question_id = request.data.get('question_id')
        if not question_id:
            return error_response("question_id is required.")

        rule = PrequalRuleService.create(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            question_id=question_id,
            condition_type=d.get('condition_type', 'equals'),
            compare_value=d.get('compare_value', ''),
            action_type=d.get('action_type', 'next_question'),
            outcome_code=d.get('outcome_code', ''),
            target_question_id=d.get('target_question_id'),
            target_section_id=d.get('target_section_id'),
            metadata=d.get('metadata', {}),
        )
        return success_response(
            data={'rule': PrequalRuleSerializer(rule).data},
            message="Rule created.",
            status_code=status.HTTP_201_CREATED,
        )


# ─── Section Detail ───────────────────────────────────────────────────────────

class PrequalSectionDetailView(APIView):
    permission_classes = [IsAuthenticated, CanManagePrequalForms]

    def get_object(self, pk, tenant_id):
        try:
            return PrequalSection.objects.get(id=pk, tenant_id=tenant_id)
        except PrequalSection.DoesNotExist:
            return None

    def patch(self, request, pk):
        section = self.get_object(pk, request.user.tenant_id)
        if not section:
            return error_response("Section not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = PrequalSectionSerializer(section, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(data={'section': serializer.data}, message="Section updated.")

    def delete(self, request, pk):
        section = self.get_object(pk, request.user.tenant_id)
        if not section:
            return error_response("Section not found.", status_code=status.HTTP_404_NOT_FOUND)
        section.delete()
        return success_response(message="Section deleted.", status_code=status.HTTP_204_NO_CONTENT)


# ─── Question Detail ──────────────────────────────────────────────────────────

class PrequalQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated, CanManagePrequalForms]

    def get_object(self, pk, tenant_id):
        try:
            return PrequalQuestion.objects.get(id=pk, tenant_id=tenant_id)
        except PrequalQuestion.DoesNotExist:
            return None

    def patch(self, request, pk):
        question = self.get_object(pk, request.user.tenant_id)
        if not question:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = PrequalQuestionSerializer(question, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(data={'question': serializer.data}, message="Question updated.")

    def delete(self, request, pk):
        question = self.get_object(pk, request.user.tenant_id)
        if not question:
            return error_response("Question not found.", status_code=status.HTTP_404_NOT_FOUND)
        question.delete()
        return success_response(message="Question deleted.", status_code=status.HTTP_204_NO_CONTENT)


# ─── Rule Detail ──────────────────────────────────────────────────────────────

class PrequalRuleDetailView(APIView):
    permission_classes = [IsAuthenticated, CanManagePrequalForms]

    def get_object(self, pk, tenant_id):
        try:
            return PrequalRule.objects.get(id=pk, tenant_id=tenant_id)
        except PrequalRule.DoesNotExist:
            return None

    def delete(self, request, pk):
        rule = self.get_object(pk, request.user.tenant_id)
        if not rule:
            return error_response("Rule not found.", status_code=status.HTTP_404_NOT_FOUND)
        rule.delete()
        return success_response(message="Rule deleted.", status_code=status.HTTP_204_NO_CONTENT)


# ─── Responses ────────────────────────────────────────────────────────────────

class PrequalResponseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        form_id = request.query_params.get('form_id')
        candidate_id = request.query_params.get('candidate_id')

        qs = PrequalResponse.objects.filter(tenant_id=request.user.tenant_id)
        if form_id:
            qs = qs.filter(form_id=form_id)
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)

        return success_response(
            data={'responses': PrequalResponseSerializer(qs, many=True).data},
            message="Responses retrieved.",
            meta={'total': qs.count()},
        )

    def post(self, request):
        serializer = PrequalResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        response = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        AutomationEngine.execute_trigger(
            trigger_event='prequalification.completed',
            tenant_id=request.user.tenant_id,
            context={
                'response_id': str(response.id),
                'form_id': str(response.form_id),
                'question_id': str(response.question_id),
                'candidate_id': str(response.candidate_id),
                'answer_text': response.answer_text,
            },
            actor_user_id=request.user.id,
            entity_type='prequalification_response',
            entity_id=response.id,
        )
        return success_response(
            data={'response': PrequalResponseSerializer(response).data},
            message="Response saved.",
            status_code=status.HTTP_201_CREATED,
        )
