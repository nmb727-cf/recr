from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.candidates.crm_models import CandidatePipelineStatus, CandidateInteraction
from apps.candidates.models import Candidate
from apps.core.responses import success_response, error_response
from django.utils import timezone
from django.db import models


class CRMPipelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statuses = ['new_lead','nurturing','in_process','offer_stage','placed','lost']
        pipeline = {}
        
        for s in statuses:
            entries = CandidatePipelineStatus.objects.filter(
                tenant_id=request.user.tenant_id,
                status=s,
                is_deleted=False
            )
            
            candidates_data = []
            for entry in entries:
                try:
                    candidate = Candidate.objects.get(id=entry.candidate_id)
                    days_in_stage = (timezone.now() - entry.updated_at).days
                    candidates_data.append({
                        'pipeline_id': str(entry.id),
                        'candidate_id': str(candidate.id),
                        'name': candidate.full_name,
                        'current_title': candidate.current_title,
                        'current_company': candidate.current_company,
                        'days_in_stage': days_in_stage,
                        'next_action': entry.next_action,
                        'next_action_date': entry.next_action_date,
                        'sentiment': entry.sentiment,
                        'assigned_to': str(entry.assigned_to) if entry.assigned_to else None,
                        'last_contacted_at': entry.last_contacted_at,
                    })
                except Candidate.DoesNotExist:
                    pass
            
            pipeline[s] = candidates_data

        return success_response(data={'pipeline': pipeline}, message="CRM pipeline retrieved.")


class CRMAddToPipelineView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        candidate_id = request.data.get('candidate_id')
        if not candidate_id:
            return error_response("candidate_id is required.")

        pipeline, created = CandidatePipelineStatus.objects.get_or_create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id,
            defaults={
                'status': request.data.get('status', 'new_lead'),
                'assigned_to': request.user.id,
                'next_action': request.data.get('next_action', ''),
                'next_action_date': request.data.get('next_action_date'),
                'source_job_id': request.data.get('source_job_id'),
                'created_by': request.user.id,
            }
        )

        if not created:
            return error_response(
                "Candidate already in pipeline.",
                status_code=409
            )

        return success_response(
            data={'pipeline_id': str(pipeline.id)},
            message="Candidate added to pipeline.",
            status_code=201
        )


class CRMMovePipelineView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            entry = CandidatePipelineStatus.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id
            )
        except CandidatePipelineStatus.DoesNotExist:
            return error_response("Pipeline entry not found.", status_code=404)

        target_status = request.data.get('status', entry.status)
        note = (
            request.data.get('note')
            or request.data.get('notes')
            or request.data.get('reason')
            or ''
        ).strip()
        if target_status != entry.status and not note:
            return error_response(
                "A mandatory note/reason is required for every stage change.",
                errors={'note': ['This field is required.']}
            )
        previous_status = entry.status
        entry.status = target_status
        entry.next_action = request.data.get('next_action', entry.next_action)
        entry.next_action_date = request.data.get('next_action_date', entry.next_action_date)
        entry.save()
        if target_status != previous_status:
            CandidateInteraction.objects.create(
                tenant_id=request.user.tenant_id,
                candidate_id=entry.candidate_id,
                interaction_type='note',
                direction='internal',
                subject='CRM stage changed',
                content=note,
                outcome=f"{previous_status} -> {target_status}",
                created_by=request.user.id,
            )

        return success_response(message=f"Candidate moved to {entry.status}.")


class CRMInteractionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        interactions = CandidateInteraction.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id
        ).order_by('-created_at')

        data = [{
            'id': str(i.id),
            'interaction_type': i.interaction_type,
            'direction': i.direction,
            'subject': i.subject,
            'content': i.content,
            'outcome': i.outcome,
            'next_followup_date': i.next_followup_date,
            'created_by': str(i.created_by) if i.created_by else None,
            'created_at': i.created_at,
        } for i in interactions]

        return success_response(
            data={'interactions': data},
            message="Interactions retrieved."
        )

    def post(self, request, candidate_id):
        interaction = CandidateInteraction.objects.create(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id,
            interaction_type=request.data.get('interaction_type', 'note'),
            direction=request.data.get('direction', 'outbound'),
            subject=request.data.get('subject', ''),
            content=request.data.get('content', ''),
            outcome=request.data.get('outcome', ''),
            next_followup_date=request.data.get('next_followup_date'),
            created_by=request.user.id,
        )

        # Update last contacted
        CandidatePipelineStatus.objects.filter(
            tenant_id=request.user.tenant_id,
            candidate_id=candidate_id
        ).update(
            last_contacted_at=timezone.now(),
            contact_count=models.F('contact_count') + 1
        )

        return success_response(
            data={'interaction_id': str(interaction.id)},
            message="Interaction logged.",
            status_code=201
        )


class CRMRemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import date
        today = date.today()

        overdue = CandidatePipelineStatus.objects.filter(
            tenant_id=request.user.tenant_id,
            assigned_to=request.user.id,
            next_action_date__lte=today,
            is_deleted=False,
            status__in=['new_lead', 'nurturing', 'in_process', 'offer_stage']
        ).exclude(status__in=['placed', 'lost'])

        data = []
        for entry in overdue:
            try:
                candidate = Candidate.objects.get(id=entry.candidate_id)
                days_overdue = (today - entry.next_action_date).days if entry.next_action_date else 0
                data.append({
                    'pipeline_id': str(entry.id),
                    'candidate_id': str(candidate.id),
                    'name': candidate.full_name,
                    'next_action': entry.next_action,
                    'next_action_date': entry.next_action_date,
                    'days_overdue': days_overdue,
                })
            except Candidate.DoesNotExist:
                pass

        return success_response(
            data={'reminders': data},
            message="Reminders retrieved.",
            meta={'total': len(data)}
        )


class CRMSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        from apps.jobs.models import JobRequisition
        try:
            job = JobRequisition.objects.get(
                id=job_id,
                tenant_id=request.user.tenant_id
            )
        except JobRequisition.DoesNotExist:
            return error_response("Job not found.", status_code=404)

        required_skills = job.skills_required or []
        candidates = Candidate.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        suggestions = []
        for candidate in candidates:
            candidate_skills = candidate.skills or []
            if not candidate_skills:
                continue

            required_lower = [s.lower() for s in required_skills]
            candidate_lower = [s.lower() for s in candidate_skills]

            matched = [s for s in required_lower if s in candidate_lower]
            missing = [s for s in required_lower if s not in candidate_lower]

            if not matched:
                continue

            skill_score = (len(matched) / max(len(required_lower), 1)) * 60

            exp_score = 0
            if candidate.experience_years:
                exp_min = job.experience_min or 0
                exp_max = job.experience_max or 99
                if exp_min <= float(candidate.experience_years) <= exp_max:
                    exp_score = 25

            mode_score = 0
            if hasattr(candidate, 'preferred_work_mode'):
                if candidate.preferred_work_mode == job.work_mode:
                    mode_score = 15

            total_score = skill_score + exp_score + mode_score

            if total_score > 20:
                suggestions.append({
                    'candidate': {
                        'id': str(candidate.id),
                        'name': candidate.full_name,
                        'current_title': candidate.current_title,
                        'current_company': candidate.current_company,
                        'experience_years': str(candidate.experience_years) if candidate.experience_years else None,
                        'skills': candidate_skills,
                    },
                    'match_score': round(total_score),
                    'matched_skills': matched,
                    'missing_skills': missing,
                })

        suggestions.sort(key=lambda x: x['match_score'], reverse=True)

        return success_response(
            data={'suggestions': suggestions[:10]},
            message="Suggestions retrieved.",
            meta={'total': len(suggestions)}
        )
