import uuid

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.utils import timezone

from apps.core.responses import success_response, error_response
from apps.hdc.models import (
    HiringCommittee, CommitteeMember,
    ComparisonSet, ComparisonCandidate,
    DecisionApproval,
    OfferRecommendation, OfferScenario,
    NegotiationCase, NegotiationRound,
    OfferReleasePacket, JoiningCase,
    HDCAuditLog
)
from apps.hdc.serializers import (
    HiringCommitteeSerializer,
    ComparisonSetSerializer,
    DecisionApprovalSerializer,
    OfferRecommendationSerializer,
    NegotiationCaseSerializer,
    OfferReleasePacketSerializer, JoiningCaseSerializer,
    HDCAuditLogSerializer, ApplicationHDCStatusSerializer
)
from apps.hdc.services import HDCOperationalService
from apps.pipeline.models import Application
from apps.core import events

class HiringCommitteeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = HiringCommitteeSerializer
    allowed_roles = {'super_admin', 'tenant_admin', 'recruiter', 'hiring_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Hiring Committee operations.')

    def get_queryset(self):
        return HiringCommittee.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).prefetch_related('members').order_by('-created_at')

    def perform_create(self, serializer):
        # Prevent duplicate committees for the same application/requisition if one is already active
        existing = HiringCommittee.objects.filter(
            tenant_id=self.request.user.tenant_id,
            application_id=serializer.validated_data.get('application_id'),
            status__in=['draft', 'active', 'voting']
        ).exists()
        if existing:
            raise ValueError('An active hiring committee already exists for this application.')
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Committees retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Committee retrieved successfully.")

    @action(detail=True, methods=['post'])
    def submit_vote(self, request, pk=None):
        committee = self.get_object()
        user_id = request.user.id
        vote = request.data.get('vote')
        notes = request.data.get('notes', '')

        if vote not in {'hire', 'reject', 'hold'}:
            return error_response('Invalid vote. Choose one of: hire, reject, hold.', status_code=status.HTTP_400_BAD_REQUEST)

        member = CommitteeMember.objects.filter(committee=committee, user_id=user_id).first()
        if not member and not request.user.is_staff and request.user.role not in {'super_admin', 'tenant_admin'}:
            return error_response('Only assigned committee members can submit votes.', status_code=status.HTTP_403_FORBIDDEN)
        if not member:
            member = CommitteeMember.objects.create(
                tenant_id=request.user.tenant_id,
                committee=committee,
                user_id=user_id,
            )

        member.has_voted = True
        member.vote = vote
        member.review_notes = notes
        member.voted_at = timezone.now()
        member.save()

        voted_count = committee.members.filter(has_voted=True).count()
        quorum_required = max(committee.quorum_required or 0, 1)
        
        if voted_count >= quorum_required:
            vote_counts = {'hire': 0, 'reject': 0, 'hold': 0}
            for row in committee.members.filter(has_voted=True):
                if row.vote in vote_counts:
                    vote_counts[row.vote] += 1
            
            # Determine the majority result safely
            sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
            top_vote, top_count = sorted_votes[0]
            second_vote, second_count = sorted_votes[1]
            
            if top_count > second_count:
                committee.result = top_vote
                committee.status = 'completed'
            elif top_count > 0:
                # Tie detected
                committee.result = 'tie'
                committee.status = 'split'
            else:
                committee.result = 'none'
                committee.status = 'active'
                
            committee.save(update_fields=['result', 'status', 'updated_at'])
            
            if committee.status == 'completed':
                HDCOperationalService.handle_committee_completion(committee)

        return success_response(
            data={
                'committee_id': str(committee.id),
                'status': committee.status,
                'result': committee.result,
                'voted_count': voted_count,
                'quorum_required': quorum_required,
            },
            message='Vote submitted successfully.'
        )

class ComparisonSetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ComparisonSetSerializer
    allowed_roles = {'super_admin', 'tenant_admin', 'recruiter', 'hiring_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Candidate Comparison operations.')

    def get_queryset(self):
        return ComparisonSet.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Comparison sets retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Comparison set retrieved successfully.")

    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        comp_set = self.get_object()
        if comp_set.status == 'frozen':
            return success_response(
                data={'comparison_id': str(comp_set.id), 'status': comp_set.status},
                message='Comparison set already frozen.'
            )
        comp_set.status = 'frozen'
        comp_set.save(update_fields=['status', 'updated_at'])
        return success_response(
            data={'comparison_id': str(comp_set.id), 'status': comp_set.status},
            message='Comparison set frozen.'
        )

class OfferRecommendationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OfferRecommendationSerializer
    allowed_roles = {'super_admin', 'tenant_admin', 'recruiter', 'hiring_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Offer Intelligence operations.')

    def get_queryset(self):
        return OfferRecommendation.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).prefetch_related('scenarios').order_by('-created_at')

    def perform_create(self, serializer):
        application_id = serializer.validated_data.get('application_id')
        if OfferRecommendation.objects.filter(application_id=application_id, tenant_id=self.request.user.tenant_id).exists():
            return
        serializer.save(
            tenant_id=self.request.user.tenant_id, 
            created_by=self.request.user.id
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Offer recommendations retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Offer recommendation retrieved successfully.")

    @action(detail=True, methods=['post'])
    def select_scenario(self, request, pk=None):
        recommendation = self.get_object()
        scenario_id = request.data.get('scenario_id')
        if not scenario_id:
            return error_response('scenario_id is required.', status_code=status.HTTP_400_BAD_REQUEST)
        scenario = OfferScenario.objects.filter(
            id=scenario_id,
            recommendation=recommendation,
            tenant_id=request.user.tenant_id
        ).first()
        if not scenario:
            return error_response('Scenario not found for this recommendation.', status_code=status.HTTP_404_NOT_FOUND)

        recommendation.selected_scenario_id = scenario_id
        recommendation.status = 'recommended'
        recommendation.save(update_fields=['selected_scenario_id', 'status', 'updated_at'])
        
        HDCOperationalService.handle_offer_selection(recommendation)

        return success_response(
            data={
                'recommendation_id': str(recommendation.id),
                'selected_scenario_id': str(scenario.id),
                'status': recommendation.status,
            },
            message='Scenario selected.'
        )

class NegotiationCaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NegotiationCaseSerializer
    allowed_roles = {'super_admin', 'tenant_admin', 'recruiter', 'hiring_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Negotiation operations.')

    def get_queryset(self):
        return NegotiationCase.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).prefetch_related('rounds').order_by('-created_at')

    def perform_create(self, serializer):
        application_id = serializer.validated_data.get('application_id')
        if NegotiationCase.objects.filter(application_id=application_id, tenant_id=self.request.user.tenant_id).exists():
            return
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Negotiation cases retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Negotiation case retrieved successfully.")

    @action(detail=True, methods=['post'])
    def add_round(self, request, pk=None):
        case = self.get_object()
        round_number = case.current_round + 1
        candidate_ask = request.data.get('candidate_ask')
        company_counter = request.data.get('company_counter')
        outcome = request.data.get('outcome', 'active')
        notes = request.data.get('notes', '')

        case.current_round = round_number
        if candidate_ask is not None:
            case.candidate_ask = candidate_ask
        if company_counter is not None:
            case.company_counter = company_counter
            
        if outcome in {'active', 'agreed', 'failed', 'paused', 'handed_off', 'closed'}:
            case.status = outcome
        case.save(update_fields=['current_round', 'candidate_ask', 'company_counter', 'status', 'updated_at'])

        if case.status == 'agreed':
            HDCOperationalService.finalize_negotiation(case)

        NegotiationRound.objects.create(
            tenant_id=request.user.tenant_id,
            negotiation_case=case,
            round_number=round_number,
            candidate_ask_payload={'text': candidate_ask} if isinstance(candidate_ask, str) else (candidate_ask or {}),
            company_counter_payload={'text': company_counter} if isinstance(company_counter, str) else (company_counter or {}),
            status='closed' if outcome in {'agreed', 'failed', 'closed'} else 'open',
            notes=notes or '',
        )
        return success_response(
            data={
                'negotiation_id': str(case.id),
                'current_round': case.current_round,
                'status': case.status,
            },
            message=f'Round {round_number} added.'
        )

class OfferReleasePacketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OfferReleasePacketSerializer
    allowed_roles = {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Offer Release operations.')

    def get_queryset(self):
        return OfferReleasePacket.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).order_by('-created_at')

    def perform_create(self, serializer):
        application_id = serializer.validated_data.get('application_id')
        if OfferReleasePacket.objects.filter(application_id=application_id, tenant_id=self.request.user.tenant_id).exists():
            return
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Offer release packets retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Offer release packet retrieved successfully.")

    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        packet = self.get_object()
        if packet.status in {'released', 'accepted', 'declined'}:
            return error_response('Released offers cannot be frozen.', status_code=status.HTTP_400_BAD_REQUEST)
        packet.status = 'frozen'
        packet.save(update_fields=['status', 'updated_at'])
        return success_response(
            data={'offer_release_id': str(packet.id), 'status': packet.status},
            message='Offer packet frozen.'
        )

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        packet = self.get_object()
        old_status = packet.status
        if packet.status not in {'frozen', 'scheduled', 'assembled', 'query'}:
            return error_response(
                'Offer must be frozen/assembled/scheduled before release.',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        packet.status = 'released'
        packet.released_at = timezone.now()
        packet.released_by = request.user.id
        packet.save(update_fields=['status', 'released_at', 'released_by', 'updated_at'])

        HDCOperationalService.log_action(
            tenant_id=request.user.tenant_id,
            application_id=packet.application_id,
            requisition_id=packet.requisition_id,
            action_type='release_offer',
            user_id=request.user.id,
            previous_status=old_status,
            new_status='released'
        )

        return success_response(
            data={
                'offer_release_id': str(packet.id),
                'status': packet.status,
                'released_at': packet.released_at.isoformat() if packet.released_at else None,
                'released_by': str(packet.released_by) if packet.released_by else None,
            },
            message='Offer released.'
        )

    @action(detail=True, methods=['post'])
    def record_response(self, request, pk=None):
        packet = self.get_object()
        old_status = packet.status
        response_value = request.data.get('response')
        
        if response_value not in {'accepted', 'declined', 'query'}:
            return error_response('response must be one of: accepted, declined, query.', status_code=status.HTTP_400_BAD_REQUEST)
        
        # Governance: Only Admins or HR Managers can manually override response to 'accepted'
        if response_value == 'accepted' and request.user.role not in {'super_admin', 'tenant_admin', 'hr_manager'}:
            raise PermissionDenied('Only HR Managers or Admins can manually record offer acceptance.')

        if packet.status not in {'released', 'query'} and not packet.candidate_response:
            return error_response('Candidate response can be recorded only after release.', status_code=status.HTTP_400_BAD_REQUEST)

        packet.candidate_response = response_value
        packet.responded_at = timezone.now()
        packet.status = response_value
        packet.save(update_fields=['candidate_response', 'responded_at', 'status', 'updated_at'])

        HDCOperationalService.log_action(
            tenant_id=request.user.tenant_id,
            application_id=packet.application_id,
            requisition_id=packet.requisition_id,
            action_type=f'record_{response_value}',
            user_id=request.user.id,
            previous_status=old_status,
            new_status=response_value,
            comments=request.data.get('reason', '')
        )

        if response_value == 'accepted':
            HDCOperationalService.handle_offer_acceptance(packet, request.user.id)
        elif response_value == 'declined':
            # Sync with pipeline
            HDCOperationalService.update_application_status(
                tenant_id=packet.tenant_id,
                application_id=packet.application_id,
                new_status='rejected',
                moved_by=request.user.id,
                reason='Offer Declined by Candidate',
                notes=request.data.get('reason', '')
            )

        return success_response(
            data={
                'offer_release_id': str(packet.id),
                'status': packet.status,
                'candidate_response': packet.candidate_response,
                'responded_at': packet.responded_at.isoformat() if packet.responded_at else None,
            },
            message='Candidate response recorded.'
        )

class JoiningCaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = JoiningCaseSerializer
    # Restricted joining confirmation to HR/Admin
    allowed_roles = {'super_admin', 'tenant_admin', 'hr_manager', 'recruiter', 'hiring_manager'}
    governance_roles = {'super_admin', 'tenant_admin', 'hr_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Joining Tracking operations.')

    def get_queryset(self):
        return JoiningCase.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).order_by('-created_at')

    def perform_create(self, serializer):
        application_id = serializer.validated_data.get('application_id')
        if JoiningCase.objects.filter(application_id=application_id, tenant_id=self.request.user.tenant_id).exists():
            return
        metadata = dict(serializer.validated_data.get('metadata') or {})
        metadata.setdefault('checklist', HDCOperationalService.build_default_onboarding_checklist())
        metadata.setdefault('documents', {})
        metadata.setdefault('hrms_handoff', {'status': 'pending'})
        serializer.save(
            tenant_id=self.request.user.tenant_id,
            created_by=self.request.user.id,
            metadata=metadata,
        )

    def perform_update(self, serializer):
        status_value = serializer.validated_data.get('status')
        if status_value == 'joined' and self.request.user.role not in self.governance_roles:
            raise PermissionDenied('Only HR Managers or Admins can finalize joining status.')
            
        actual_joining_date = serializer.validated_data.get('actual_joining_date')
        if status_value == 'joined' and not actual_joining_date:
            instance = serializer.save(actual_joining_date=timezone.now().date())
            HDCOperationalService.record_joining(instance, self.request.user.id)
            return
        instance = serializer.save()
        if status_value == 'joined':
            HDCOperationalService.record_joining(instance, self.request.user.id)

    @action(detail=True, methods=['get'])
    def checklist(self, request, pk=None):
        case = self.get_object()
        checklist = (case.metadata or {}).get('checklist') or []
        return success_response(
            data={'joining_case_id': str(case.id), 'checklist': checklist},
            message='Checklist retrieved.',
        )

    @action(detail=True, methods=['post'])
    def upsert_checklist_item(self, request, pk=None):
        case = self.get_object()
        payload = request.data or {}
        task_name = str(payload.get('task_name') or '').strip()
        if not task_name:
            return error_response('task_name is required.', status_code=status.HTTP_400_BAD_REQUEST)

        item_status = str(payload.get('status') or 'pending').strip().lower()
        if item_status not in {'pending', 'in_progress', 'completed'}:
            return error_response('status must be pending, in_progress, or completed.', status_code=status.HTTP_400_BAD_REQUEST)

        metadata = dict(case.metadata or {})
        checklist = list(metadata.get('checklist') or [])
        task_id = str(payload.get('task_id') or '').strip()
        updated = False
        for item in checklist:
            if task_id and str(item.get('task_id') or '') == task_id:
                item['task_name'] = task_name
                item['assigned_to'] = str(payload.get('assigned_to') or '')
                item['due_date'] = payload.get('due_date')
                item['status'] = item_status
                updated = True
                break

        if not updated:
            checklist.append(
                {
                    'task_id': str(uuid.uuid4()),
                    'task_name': task_name,
                    'assigned_to': str(payload.get('assigned_to') or ''),
                    'due_date': payload.get('due_date'),
                    'status': item_status,
                }
            )

        metadata['checklist'] = checklist
        if checklist and all(str(i.get('status') or '') == 'completed' for i in checklist):
            if case.status not in {'handed_off', 'joined'}:
                case.status = 'completed'

        case.metadata = metadata
        case.save(update_fields=['status', 'metadata', 'updated_at'])
        return success_response(
            data={'joining_case_id': str(case.id), 'checklist': checklist, 'status': case.status},
            message='Checklist updated.',
        )

    @action(detail=True, methods=['post'])
    def prepare_handoff(self, request, pk=None):
        case = self.get_object()
        app = Application.objects.filter(
            id=case.application_id,
            tenant_id=request.user.tenant_id,
            is_deleted=False,
        ).first()
        if not app:
            return error_response('Application not found for joining case.', status_code=status.HTTP_404_NOT_FOUND)

        metadata = dict(case.metadata or {})
        documents = dict(metadata.get('documents') or {})
        payload = {
            'onboarding_id': str(case.id),
            'candidate_info': {
                'candidate_id': str(case.candidate_id or app.candidate_id or ''),
            },
            'job_info': {
                'job_id': str(case.job_id or app.requisition_id or ''),
                'application_id': str(case.application_id),
            },
            'joining_date': case.joining_date.isoformat() if case.joining_date else None,
            'documents_status': documents,
            'hr_notes': case.handoff_notes or '',
        }
        metadata['hrms_handoff'] = {
            'status': 'ready',
            'payload': payload,
            'prepared_at': timezone.now().isoformat(),
            'prepared_by': str(request.user.id),
        }
        if case.status not in {'handed_off', 'joined'}:
            case.status = 'completed'
        case.metadata = metadata
        case.save(update_fields=['status', 'metadata', 'updated_at'])
        events.onboarding.completed.send(sender=self.__class__, application=app)
        return success_response(
            data={'joining_case_id': str(case.id), 'status': case.status, 'handoff_payload': payload},
            message='Handoff payload prepared.',
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Joining cases retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Joining case retrieved successfully.")

    @action(detail=True, methods=['post'])
    def confirm_joining(self, request, pk=None):
        if request.user.role not in self.governance_roles:
            raise PermissionDenied('Only HR Managers or Admins can confirm joining.')
            
        case = self.get_object()
        case.status = 'joined'
        case.actual_joining_date = timezone.now().date()
        case.save()
        HDCOperationalService.record_joining(case, request.user.id)
        return success_response(message='Joining confirmed.')

class DecisionApprovalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DecisionApprovalSerializer
    allowed_roles = {'super_admin', 'tenant_admin', 'hiring_manager'}

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_staff:
            return
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have access to Decision Approval operations.')

    def get_queryset(self):
        return DecisionApproval.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)

    @action(detail=True, methods=['post'])
    def approve_for_offer(self, request, pk=None):
        approval = self.get_object()
        old_status = approval.status
        approval.status = 'approved'
        approval.approved_at = timezone.now()
        approval.approver_id = request.user.id
        approval.comments = request.data.get('comments', '')
        approval.save()
        
        HDCOperationalService.log_action(
            tenant_id=request.user.tenant_id,
            application_id=approval.application_id,
            requisition_id=approval.requisition_id,
            action_type='approve_for_offer',
            user_id=request.user.id,
            previous_status=old_status,
            new_status='approved',
            comments=approval.comments
        )
        
        HDCOperationalService.handle_approval_completion(approval)
        return success_response(data=self.get_serializer(approval).data, message='Approved for offer.')

    @action(detail=True, methods=['post'])
    def reject_candidate(self, request, pk=None):
        approval = self.get_object()
        old_status = approval.status
        approval.status = 'rejected'
        approval.approved_at = timezone.now()
        approval.approver_id = request.user.id
        approval.comments = request.data.get('comments', '')
        approval.save()

        HDCOperationalService.log_action(
            tenant_id=request.user.tenant_id,
            application_id=approval.application_id,
            requisition_id=approval.requisition_id,
            action_type='reject_candidate',
            user_id=request.user.id,
            previous_status=old_status,
            new_status='rejected',
            comments=approval.comments
        )
        return success_response(data=self.get_serializer(approval).data, message='Candidate rejected.')

    @action(detail=True, methods=['post'])
    def send_back_to_review(self, request, pk=None):
        approval = self.get_object()
        old_status = approval.status
        approval.status = 'pending'
        approval.comments = request.data.get('comments', '')
        approval.save()

        HDCOperationalService.log_action(
            tenant_id=request.user.tenant_id,
            application_id=approval.application_id,
            requisition_id=approval.requisition_id,
            action_type='send_back_to_review',
            user_id=request.user.id,
            previous_status=old_status,
            new_status='pending',
            comments=approval.comments
        )
        return success_response(message='Sent back to review.')

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tid = request.user.tenant_id
        
        stats = {
            'pending_committee': HiringCommittee.objects.filter(tenant_id=tid, status__in=['active', 'voting']).count(),
            'pending_approvals': DecisionApproval.objects.filter(tenant_id=tid, status='pending').count(),
            'scenario_modeling': OfferRecommendation.objects.filter(tenant_id=tid, status='scenario_modeling').count(),
            'active_negotiations': NegotiationCase.objects.filter(tenant_id=tid, status='active').count(),
            'ready_for_release': OfferReleasePacket.objects.filter(tenant_id=tid, status__in=['draft', 'assembled', 'frozen']).count(),
            'awaiting_joining': JoiningCase.objects.filter(tenant_id=tid, status='pending').count(),
        }
        
        recent_tasks = []
        
        # 1. Committee Tasks (Voting)
        committees = HiringCommittee.objects.filter(tenant_id=tid, status__in=['active', 'voting']).order_by('-created_at')[:5]
        for c in committees:
            recent_tasks.append({
                'id': str(c.id),
                'application_id': str(c.application_id),
                'type': 'committee',
                'title': f'Vote: {c.name}',
                'status': c.status,
                'created_at': c.created_at
            })

        # 2. Approval Tasks
        approvals = DecisionApproval.objects.filter(tenant_id=tid, status='pending').order_by('-created_at')[:5]
        for a in approvals:
            recent_tasks.append({
                'id': str(a.id),
                'application_id': str(a.application_id),
                'type': 'approval',
                'title': f'Offer Approval Needed',
                'status': a.status,
                'created_at': a.created_at
            })

        # 3. Release Tasks
        releases = OfferReleasePacket.objects.filter(tenant_id=tid, status='frozen').order_by('-updated_at')[:5]
        for r in releases:
            recent_tasks.append({
                'id': str(r.id),
                'application_id': str(r.application_id),
                'type': 'release',
                'title': f'Offer Ready for Release',
                'status': r.status,
                'created_at': r.updated_at
            })

        # Sort combined tasks by date
        recent_tasks.sort(key=lambda x: x['created_at'], reverse=True)
            
        return success_response(data={'stats': stats, 'recent_tasks': recent_tasks[:10]})

from apps.pipeline.models import Application
from apps.jobs.models import JobRequisition
from apps.candidates.models import Candidate
from apps.interviews.models import Interview, InterviewDecision, InterviewFeedback

class ApplicationHDCStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        tid = request.user.tenant_id
        
        # 1. Fetch Core Records
        try:
            app = Application.objects.get(id=application_id, tenant_id=tid)
            job = JobRequisition.objects.get(id=app.requisition_id, tenant_id=tid)
            candidate = Candidate.objects.get(id=app.candidate_id, tenant_id=tid)
        except (Application.DoesNotExist, JobRequisition.DoesNotExist, Candidate.DoesNotExist):
            return error_response('Application context not found.', status_code=status.HTTP_404_NOT_FOUND)

        # 2. Gather all HDC components for this application
        committee = HiringCommittee.objects.filter(tenant_id=tid, application_id=application_id).first()
        approval = DecisionApproval.objects.filter(tenant_id=tid, application_id=application_id).first()
        offer_rec = OfferRecommendation.objects.filter(tenant_id=tid, application_id=application_id).first()
        negotiation = NegotiationCase.objects.filter(tenant_id=tid, application_id=application_id).first()
        release = OfferReleasePacket.objects.filter(tenant_id=tid, application_id=application_id).first()
        joining = JoiningCase.objects.filter(tenant_id=tid, application_id=application_id).first()
        
        # 3. Gather ICC Data (Interview Summaries)
        interviews = Interview.objects.filter(application_id=application_id, tenant_id=tid).order_by('interview_round')
        interview_summary = []
        for i in interviews:
            decision = InterviewDecision.objects.filter(interview_id=i.id).first()
            feedbacks = InterviewFeedback.objects.filter(interview_id=i.id)
            interview_summary.append({
                'id': str(i.id),
                'round': i.interview_round,
                'type': i.interview_type,
                'status': i.status,
                'overall_score': float(i.overall_score) if i.overall_score else None,
                'recommendation': i.recommendation,
                'decision': decision.decision if decision else None,
                'feedback_count': feedbacks.count(),
            })

        # 4. Determine Stage and Progress
        stage = "Committee"
        progress = 10
        
        if joining:
            stage = "Joining"
            progress = 100 if joining.status == 'joined' else 90
        elif release:
            stage = "Offer"
            progress = 80 if release.status == 'accepted' else 70
        elif negotiation:
            stage = "Negotiation"
            progress = 60
        elif offer_rec:
            stage = "Compensation"
            progress = 40
        elif approval:
            stage = "Approval"
            progress = 30 if approval.status == 'approved' else 20
            
        # 5. Timeline
        timeline = HDCAuditLog.objects.filter(tenant_id=tid, application_id=application_id).order_by('-created_at')
        
        data = {
            'application_id': application_id,
            'job': {
                'id': str(job.id),
                'title': job.title,
                'status': job.status,
                'hiring_manager_id': str(job.hiring_manager_id) if job.hiring_manager_id else None,
            },
            'candidate': {
                'id': str(candidate.id),
                'name': f"{candidate.first_name} {candidate.last_name}",
                'email': candidate.email,
            },
            'current_stage': stage,
            'progress_percentage': progress,
            'interview_summary': interview_summary,
            'timeline': HDCAuditLogSerializer(timeline, many=True).data,
            'can_approve': committee and committee.status == 'completed' and not (approval and approval.status == 'approved'),
            'can_release_offer': approval and approval.status == 'approved' and not (release and release.status == 'released'),
            'can_negotiate': offer_rec and offer_rec.status == 'recommended',
            'can_confirm_joining': release and release.status == 'accepted' and not (joining and joining.status == 'joined')
        }
        
        return success_response(data=data)
