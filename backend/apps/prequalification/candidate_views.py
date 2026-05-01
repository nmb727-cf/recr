from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.prequalification.models import PrequalForm, PrequalResponse, PrequalQuestion
from apps.prequalification.serializers import PrequalFormDetailSerializer, PrequalResponseSerializer
from apps.core.responses import success_response, error_response
from apps.automation.services import AutomationEngine
import uuid

def _get_candidate_id_for_user(user):
    from apps.candidates.models import Candidate
    candidate = Candidate.objects.filter(user_id=user.id).first()
    return candidate.id if candidate else None

class CandidatePrequalFormDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Allow candidates to see active forms. 
        form = PrequalForm.objects.filter(id=pk, is_active=True, is_deleted=False).first()
        if not form:
            return error_response("Prequalification form not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        return success_response(
            data={'form': PrequalFormDetailSerializer(form).data},
            message="Form retrieved."
        )

class CandidatePrequalSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        candidate_id = _get_candidate_id_for_user(request.user)
        if not candidate_id:
            return error_response("Candidate profile not found.", status_code=status.HTTP_404_NOT_FOUND)

        form = PrequalForm.objects.filter(id=pk, is_active=True, is_deleted=False).first()
        if not form:
            return error_response("Form not found.", status_code=status.HTTP_404_NOT_FOUND)

        responses_data = request.data.get('responses', [])
        saved_responses = []
        
        for resp_data in responses_data:
            question_id = resp_data.get('question_id')
            answer_text = resp_data.get('answer_text', '')
            answer_json = resp_data.get('answer_json', {})
            
            question = PrequalQuestion.objects.filter(id=question_id, section__form=form).first()
            if not question:
                continue
                
            response = PrequalResponse.objects.create(
                tenant_id=form.tenant_id,
                form=form,
                candidate_id=candidate_id,
                question=question,
                answer_text=answer_text,
                answer_json=answer_json,
                created_by=request.user.id
            )
            saved_responses.append(response)

        # Trigger automation
        AutomationEngine.execute_trigger(
            trigger_event='prequalification.completed',
            tenant_id=form.tenant_id,
            context={
                'form_id': str(form.id),
                'candidate_id': str(candidate_id),
                'response_count': len(saved_responses),
            },
            actor_user_id=request.user.id,
            entity_type='candidate',
            entity_id=candidate_id,
        )

        return success_response(
            message="Prequalification submitted successfully."
        )
