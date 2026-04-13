from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import uuid
from django.db.models import Q
from django.conf import settings
from apps.accounts.models import CustomUser

from apps.agencies.models import (
    AgencyClientRelationship, AgencyJobAssignment, AgencyPerformanceScore, AgencyMembership
)
from apps.agencies.serializers import (
    AgencyClientRelationshipSerializer, AgencyJobAssignmentSerializer,
    AgencyPerformanceScoreSerializer,
)
from apps.agencies.permissions import AgencyPerformancePermission
from apps.agencies.emailing import send_agency_invite_email
from apps.candidates.protection import create_or_update_protection_on_submission
from apps.core.responses import success_response, error_response
from apps.orchestration_center.services.audit_service import AuditService
from shared.tenant_access import (
    TenantAccessMixin,
    is_platform_admin as shared_is_platform_admin,
    scope_queryset_by_tenant_fields,
    scope_agency_relationship_qs,
)
from shared.search_utils import (
    apply_keyword_search,
    get_search_query,
    parse_limit_offset,
)

AGENCY_INTELLIGENCE_DASHBOARD_ROLES = {'super_admin', 'tenant_admin', 'hr_manager', 'hiring_manager'}
AGENCY_INTELLIGENCE_OPERATIONAL_ROLES = AGENCY_INTELLIGENCE_DASHBOARD_ROLES | {'recruiter'}


def _to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _require_agency_intelligence_access(request, *, include_recruiter=False):
    allowed_roles = AGENCY_INTELLIGENCE_OPERATIONAL_ROLES if include_recruiter else AGENCY_INTELLIGENCE_DASHBOARD_ROLES
    if request.user.is_staff or request.user.role in allowed_roles:
        return None
    return error_response(
        "You do not have permission to access Agency Intelligence.",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def _is_platform_admin(user):
    return shared_is_platform_admin(user)


def _is_company_user(user):
    return getattr(user, 'role', '') in {'tenant_admin', 'hr_manager', 'hiring_manager', 'recruiter'}


def _is_agency_user(user):
    return getattr(user, 'role', '') in {'agency_owner', 'agency_admin', 'agency_recruiter'}


def _is_agency_member(*, agency_tenant_id, user_id):
    if AgencyMembership.objects.filter(
        agency_tenant_id=agency_tenant_id,
        user_id=user_id,
        is_active=True,
    ).exists():
        return True
    return CustomUser.objects.filter(
        id=user_id,
        tenant_id=agency_tenant_id,
        role__in=['agency_owner', 'agency_admin', 'agency_recruiter'],
        is_deleted=False,
    ).exists()


class AvailableAgencyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.tenants.models import Client
        from apps.organisations.models import Organisation

        def normalize_tenant_id(value):
            if value is None:
                return ''
            if isinstance(value, uuid.UUID):
                return str(value)
            if isinstance(value, int):
                return str(uuid.UUID(int=value))
            raw = str(value).strip()
            if not raw:
                return ''
            try:
                return str(uuid.UUID(raw))
            except Exception:
                if raw.isdigit():
                    return str(uuid.UUID(int=int(raw)))
                return ''

        agencies = Client.objects.filter(
            tenant_type='agency',
            is_deleted=False,
        ).order_by('name')

        by_id = {}
        for a in agencies:
            agency_tenant_id = normalize_tenant_id(a.id)
            if not agency_tenant_id:
                continue
            by_id[agency_tenant_id] = {
                'agency_tenant_id': agency_tenant_id,
                'name': a.name,
                'status': a.status,
                'country_code': a.country_code,
            }

        # Fallback/source-merge for Phase 1:
        # include agency org records in case tenant listing visibility is limited.
        agency_orgs = Organisation.objects.filter(
            org_type='agency',
            is_deleted=False
        ).values('tenant_id', 'name', 'country_code')

        for org in agency_orgs:
            tenant_id = normalize_tenant_id(org.get('tenant_id'))
            if not tenant_id:
                continue
            existing = by_id.get(tenant_id)
            if existing:
                if not existing.get('name') and org.get('name'):
                    existing['name'] = org['name']
                if not existing.get('country_code') and org.get('country_code'):
                    existing['country_code'] = org['country_code']
                continue
            by_id[tenant_id] = {
                'agency_tenant_id': tenant_id,
                'name': org.get('name') or f"Agency {tenant_id[:8]}",
                'status': 'active',
                'country_code': org.get('country_code') or '',
            }

        data = sorted(by_id.values(), key=lambda x: (x.get('name') or '').lower())

        return success_response(
            data={'agencies': data},
            message="Available agencies retrieved.",
            meta={'total': len(data)}
        )


class AgencyLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return error_response("Search query required.")

        from apps.accounts.models import CustomUser
        from apps.tenants.models import Client
        from django.db.models import Q

        user = CustomUser.objects.filter(
            Q(email__iexact=q) | Q(phone=q)
        ).first()

        if not user:
            return error_response(
                "No user found with that email or phone.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        from apps.organisations.models import Organisation
        org = Organisation.objects.filter(tenant_id=user.tenant_id).first()
        if not org:
            return error_response("Account found but no organisation details linked.")

        return success_response(
            data={
                'tenant_id': str(user.tenant_id),
                'name': org.name,
                'tenant_type': org.org_type,
                'industry': org.industry or '',
                'email': user.email,
            },
            message="Found."
        )


class AgencyRelationshipListView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.reject_scope_widening(request)
        if denied:
            return denied

        # Company sees relationships where they are the company
        # Agency sees relationships where they are the agency
        from apps.organisations.models import Organisation
        try:
            org = Organisation.objects.filter(tenant_id=request.user.tenant_id).first()
            if org and org.org_type == 'agency':
                qs = AgencyClientRelationship.objects.filter(
                    agency_tenant_id=request.user.tenant_id,
                    is_deleted=False
                )
            else:
                qs = AgencyClientRelationship.objects.filter(
                    company_tenant_id=request.user.tenant_id,
                    is_deleted=False
                )
            qs = scope_agency_relationship_qs(
                relationship_qs=qs,
                user=request.user,
                allow_platform_admin=True,
            )
        except Exception:
            qs = AgencyClientRelationship.objects.none()

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        search = get_search_query(request.query_params)
        if search:
            qs, _ = apply_keyword_search(
                qs,
                query=search,
                fields=(
                    'contact_person_name',
                    'contact_email',
                    'contact_phone',
                    'industry',
                    'invited_via',
                    'notes',
                ),
                typo_tolerant=True,
            )

        total = qs.count()
        limit, offset = parse_limit_offset(request.query_params, default_limit=50, max_limit=200)
        qs = qs.order_by('-updated_at')[offset:offset + limit]

        return success_response(
            data={'relationships': AgencyClientRelationshipSerializer(qs, many=True).data},
            message="Relationships retrieved.",
            meta={'total': total, 'limit': limit, 'offset': offset}
        )

    def post(self, request):
        serializer = AgencyClientRelationshipSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        data = serializer.validated_data
        agency_tenant_id = data.get('agency_tenant_id')
        company_tenant_id = data.get('company_tenant_id')
        invited_via = data.get('invited_via')

        # Determine if company is inviting agency or vice-versa
        if request.user.role in ['tenant_admin', 'hr_manager', 'recruiter']:
            invited_by = 'company'
            company_tenant_id = request.user.tenant_id
            
            # Look up agency if not provided
            if not agency_tenant_id and invited_via:
                try:
                    user = CustomUser.objects.filter(
                        Q(email=invited_via) | Q(phone=invited_via)
                    ).first()
                    if user:
                        agency_tenant_id = user.tenant_id
                    else:
                        return error_response("No agency found with that email or phone number.")
                except Exception:
                    return error_response("Could not find agency.")
        else:
            invited_by = 'agency'
            agency_tenant_id = request.user.tenant_id

            # Look up company if not provided
            if not company_tenant_id and invited_via:
                try:
                    user = CustomUser.objects.filter(
                        Q(email=invited_via) | Q(phone=invited_via)
                    ).first()
                    if user:
                        company_tenant_id = user.tenant_id
                    else:
                        return error_response("No company found with that email or phone number.")
                except Exception:
                    return error_response("Could not find company.")

        if not agency_tenant_id or not company_tenant_id:
            return error_response("Both agency and company tenant IDs are required.")

        # Check duplicate
        if AgencyClientRelationship.objects.filter(
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=company_tenant_id,
            is_deleted=False
        ).exists():
            return error_response(
                "Relationship already exists.",
                status_code=status.HTTP_409_CONFLICT
            )

        relationship = serializer.save(
            tenant_id=request.user.tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=company_tenant_id,
            invited_by=invited_by,
            created_by=request.user.id,
            status='pending'
        )

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(relationship).data},
            message="Relationship created.",
            status_code=status.HTTP_201_CREATED
        )


class AgencyRelationshipDetailView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        qs = AgencyClientRelationship.objects.filter(
            id=pk,
            is_deleted=False,
        )
        qs = self.relationship_scope(qs, request=request, allow_platform_admin=True)
        return qs.first()

    def get(self, request, pk):
        rel = self.get_object(request, pk)
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Relationship retrieved."
        )

    def put(self, request, pk):
        rel = self.get_object(request, pk)
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = AgencyClientRelationshipSerializer(rel, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'relationship': serializer.data},
            message="Relationship updated."
        )

    def delete(self, request, pk):
        rel = self.get_object(request, pk)
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        rel.soft_delete()
        return success_response(
            message="Relationship deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class AgencyRelationshipInviteView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        rel = self.relationship_scope(
            AgencyClientRelationship.objects.filter(id=pk, is_deleted=False),
            request=request,
            allow_platform_admin=True,
        ).first()
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        if rel.status != 'pending':
            return error_response("Only pending relationships can be invited.")

        rel.status = 'pending'
        rel.save(update_fields=['status', 'updated_at'])

        # Send invite email to agency
        from apps.communications.services import EmailRoutingService
        EmailRoutingService.send_email(
            subject=f"Invitation to collaborate with {rel.client_name}",
            body_text=(
                f"Hi,\n\n"
                f"{request.user.first_name or 'Someone'} from {rel.client_name} has invited you to collaborate on TalentOS.\n\n"
                f"Log in to your dashboard to accept the invitation."
            ),
            body_html=None,
            recipient_list=[rel.contact_email],
            user_id=request.user.id,
            tenant_id=request.user.tenant_id
        )

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Invitation sent to agency."
        )


class AgencyRelationshipAcceptView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        rel = self.relationship_scope(
            AgencyClientRelationship.objects.filter(id=pk, is_deleted=False),
            request=request,
            allow_platform_admin=True,
        ).first()
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        if rel.status != 'pending':
            return error_response("Only pending relationships can be accepted.")

        rel.status = 'active'
        rel.save(update_fields=['status', 'updated_at'])

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Relationship accepted."
        )


class AgencyRelationshipSuspendView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        rel = self.relationship_scope(
            AgencyClientRelationship.objects.filter(id=pk, is_deleted=False),
            request=request,
            allow_platform_admin=True,
        ).first()
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        rel.status = 'suspended'
        rel.notes = f"Suspended: {reason}" if reason else rel.notes
        rel.save(update_fields=['status', 'notes', 'updated_at'])

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Relationship suspended."
        )


class AgencyRelationshipReactivateView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        rel = self.relationship_scope(
            AgencyClientRelationship.objects.filter(id=pk, is_deleted=False),
            request=request,
            allow_platform_admin=True,
        ).first()
        if not rel:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        allowed = _is_platform_admin(request.user) or request.user.tenant_id in {rel.company_tenant_id, rel.agency_tenant_id}
        if not allowed:
            return error_response("You do not have permission to reactivate this relationship.", status_code=status.HTTP_403_FORBIDDEN)

        before_state = {'status': rel.status}
        rel.status = 'active'
        rel.save(update_fields=['status', 'updated_at'])

        AuditService.log(
            tenant_id=request.user.tenant_id,
            actor_id=request.user.id,
            action_type='agency_relationship_reactivated',
            target_type='agency_relationship',
            target_id=rel.id,
            before_state_json=before_state,
            after_state_json={'status': rel.status},
            metadata_json={'company_tenant_id': str(rel.company_tenant_id), 'agency_tenant_id': str(rel.agency_tenant_id)},
        )

        from apps.core import events
        events.agency.relationship_reactivated.send(
            sender=self.__class__,
            relationship_id=rel.id,
            company_tenant_id=rel.company_tenant_id,
            agency_tenant_id=rel.agency_tenant_id,
            actor_id=request.user.id,
        )

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Relationship reactivated."
        )


class AgencyJobAssignmentListView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = self.reject_scope_widening(request)
        if denied:
            return denied

        qs = scope_queryset_by_tenant_fields(
            AgencyJobAssignment.objects.filter(is_deleted=False),
            user=request.user,
            tenant_fields=('tenant_id', 'agency_tenant_id'),
            allow_platform_admin=True,
        )

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        agency_id = request.query_params.get('agency_id')
        if agency_id:
            qs = qs.filter(agency_tenant_id=agency_id)

        requisition_id = request.query_params.get('requisition_id')
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)

        return success_response(
            data={'assignments': AgencyJobAssignmentSerializer(qs, many=True).data},
            message="Assignments retrieved.",
            meta={'total': qs.count()}
        )

    def post(self, request):
        serializer = AgencyJobAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        data = serializer.validated_data

        # Check duplicate
        if AgencyJobAssignment.objects.filter(
            tenant_id=request.user.tenant_id,
            requisition_id=data['requisition_id'],
            agency_tenant_id=data['agency_tenant_id'],
            is_deleted=False
        ).exists():
            return error_response(
                "Agency already assigned to this job.",
                status_code=status.HTTP_409_CONFLICT
            )

        assignment = serializer.save(
            tenant_id=request.user.tenant_id,
            assigned_by=request.user.id,
            created_by=request.user.id,
        )

        return success_response(
            data={'assignment': AgencyJobAssignmentSerializer(assignment).data},
            message="Agency assigned to job.",
            status_code=status.HTTP_201_CREATED
        )


class AgencyJobAssignmentDetailView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        qs = scope_queryset_by_tenant_fields(
            AgencyJobAssignment.objects.filter(
                id=pk,
                is_deleted=False,
            ),
            user=request.user,
            tenant_fields=('tenant_id', 'agency_tenant_id'),
            allow_platform_admin=True,
        )
        return qs.first()

    def get(self, request, pk):
        assignment = self.get_object(request, pk)
        if not assignment:
            return error_response("Assignment not found.", status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            data={'assignment': AgencyJobAssignmentSerializer(assignment).data},
            message="Assignment retrieved."
        )

    def put(self, request, pk):
        assignment = self.get_object(request, pk)
        if not assignment:
            return error_response("Assignment not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = AgencyJobAssignmentSerializer(assignment, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'assignment': serializer.data},
            message="Assignment updated."
        )

    def delete(self, request, pk):
        assignment = self.get_object(request, pk)
        if not assignment:
            return error_response("Assignment not found.", status_code=status.HTTP_404_NOT_FOUND)

        assignment.soft_delete()
        return success_response(
            message="Assignment deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class AgencyJobAssignRecruiterView(TenantAccessMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        recruiter_id = request.data.get('recruiter_id')
        if not recruiter_id:
            return error_response("recruiter_id is required.", status_code=status.HTTP_400_BAD_REQUEST)

        assignment = scope_queryset_by_tenant_fields(
            AgencyJobAssignment.objects.filter(id=pk, is_deleted=False),
            user=request.user,
            tenant_fields=('tenant_id', 'agency_tenant_id'),
            allow_platform_admin=True,
        ).first()
        if not assignment:
            return error_response("Assignment not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Allow platform admin or tenant users tied to this assignment's agency/company
        allowed = _is_platform_admin(request.user) or request.user.tenant_id in {assignment.tenant_id, assignment.agency_tenant_id}
        if not allowed:
            return error_response("You do not have permission to assign recruiter for this job.", status_code=status.HTTP_403_FORBIDDEN)

        try:
            recruiter_uuid = uuid.UUID(str(recruiter_id))
        except (ValueError, TypeError):
            return error_response("recruiter_id must be a valid UUID.", status_code=status.HTTP_400_BAD_REQUEST)

        if not _is_agency_member(agency_tenant_id=assignment.agency_tenant_id, user_id=recruiter_uuid):
            return error_response("Recruiter does not belong to the assigned agency.", status_code=status.HTTP_403_FORBIDDEN)

        before_state = {'internal_recruiter_id': str(assignment.internal_recruiter_id) if assignment.internal_recruiter_id else None}
        assignment.internal_recruiter_id = recruiter_uuid
        assignment.save(update_fields=['internal_recruiter_id', 'updated_at'])

        AuditService.log(
            tenant_id=request.user.tenant_id,
            actor_id=request.user.id,
            action_type='agency_assignment_recruiter_assigned',
            target_type='agency_job_assignment',
            target_id=assignment.id,
            before_state_json=before_state,
            after_state_json={'internal_recruiter_id': str(recruiter_uuid)},
            metadata_json={'agency_tenant_id': str(assignment.agency_tenant_id), 'requisition_id': str(assignment.requisition_id)},
        )

        from apps.core import events
        events.agency.recruiter_assigned.send(
            sender=self.__class__,
            assignment_id=assignment.id,
            requisition_id=assignment.requisition_id,
            agency_tenant_id=assignment.agency_tenant_id,
            recruiter_id=recruiter_uuid,
            actor_id=request.user.id,
        )

        return success_response(
            data={'assignment': AgencyJobAssignmentSerializer(assignment).data},
            message="Internal recruiter assigned."
        )


class AgencyJobSubmissionGovernanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        policy = request.data.get('policy')
        if not policy:
            return error_response("policy is required.", status_code=status.HTTP_400_BAD_REQUEST)

        from apps.jobs.models import JobRequisition
        valid_policies = {'direct', 'approval_required', 'draft_only'}
        if policy not in valid_policies:
            return error_response(f"policy must be one of: {', '.join(sorted(valid_policies))}.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            requisition = JobRequisition.objects.get(id=pk, is_deleted=False)
        except JobRequisition.DoesNotExist:
            return error_response("Job not found.", status_code=status.HTTP_404_NOT_FOUND)

        allowed = _is_platform_admin(request.user) or (_is_company_user(request.user) and request.user.tenant_id == requisition.tenant_id)
        if not allowed:
            return error_response("You do not have permission to update submission governance for this job.", status_code=status.HTTP_403_FORBIDDEN)

        before_state = {'agency_submission_governance': requisition.agency_submission_governance}
        requisition.agency_submission_governance = policy
        requisition.save(update_fields=['agency_submission_governance', 'updated_at'])

        AuditService.log(
            tenant_id=request.user.tenant_id,
            actor_id=request.user.id,
            action_type='agency_submission_governance_updated',
            target_type='job_requisition',
            target_id=requisition.id,
            before_state_json=before_state,
            after_state_json={'agency_submission_governance': policy},
            metadata_json={'requisition_id': str(requisition.id)},
        )

        from apps.core import events
        events.agency.submission_governance_updated.send(
            sender=self.__class__,
            requisition_id=requisition.id,
            tenant_id=requisition.tenant_id,
            policy=policy,
            actor_id=request.user.id,
        )

        return success_response(
            data={'requisition_id': str(requisition.id), 'submission_policy': policy},
            message="Submission governance updated."
        )


from apps.agencies.services import AgencyIntelligenceService

class AgencyIntelligenceDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _require_agency_intelligence_access(request)
        if denied:
            return denied

        return success_response(
            data={'intelligence': AgencyIntelligenceService.build_dashboard(request.user.tenant_id)},
            message="Agency intelligence dashboard retrieved.",
        )


class AgencyPerformanceListView(APIView):
    permission_classes = [IsAuthenticated, AgencyPerformancePermission]

    def get(self, request):
        # Query parameter-based filtering is intentionally ignored to avoid
        # unauthorized data access across agencies.
        user = request.user
        result = []

        if _is_platform_admin(user):
            perf_rows = AgencyPerformanceScore.objects.filter().order_by('-updated_at')[:200]
            for row in perf_rows:
                metrics = AgencyIntelligenceService.calculate_agency_metrics(
                    tenant_id=row.tenant_id,
                    agency_tenant_id=row.agency_tenant_id,
                )
                result.append({
                    'agency_tenant_id': str(row.agency_tenant_id) if row.agency_tenant_id else None,
                    'company_tenant_id': str(row.company_tenant_id) if row.company_tenant_id else None,
                    'tier': row.metadata.get('tier', 'standard') if isinstance(row.metadata, dict) else 'standard',
                    'score': metrics['overall_score'],
                    'metrics': metrics,
                })
        elif _is_company_user(user):
            relationships = AgencyClientRelationship.objects.filter(
                company_tenant_id=user.tenant_id,
                is_deleted=False
            )
            for rel in relationships:
                metrics = AgencyIntelligenceService.calculate_agency_metrics(
                    tenant_id=user.tenant_id,
                    agency_tenant_id=rel.agency_tenant_id
                )
                result.append({
                    'agency_tenant_id': str(rel.agency_tenant_id),
                    'agency_name': rel.metadata.get('agency_name', 'Unknown Agency'),
                    'tier': rel.tier,
                    'score': metrics['overall_score'],
                    'metrics': metrics
                })
        elif _is_agency_user(user):
            # Agency can only view its own agency performance across linked companies.
            relationships = AgencyClientRelationship.objects.filter(
                agency_tenant_id=user.tenant_id,
                is_deleted=False
            )
            company_ids = list({rel.company_tenant_id for rel in relationships if rel.company_tenant_id})
            for company_tenant_id in company_ids:
                metrics = AgencyIntelligenceService.calculate_agency_metrics(
                    tenant_id=company_tenant_id,
                    agency_tenant_id=user.tenant_id
                )
                result.append({
                    'agency_tenant_id': str(user.tenant_id),
                    'company_tenant_id': str(company_tenant_id),
                    'score': metrics['overall_score'],
                    'metrics': metrics,
                })
        else:
            return error_response("You do not have permission to view agency performance.", status_code=status.HTTP_403_FORBIDDEN)

        return success_response(
            data={'performance': result},
            message="Agency performance list retrieved.",
            meta={'total': len(result)}
        )


class JobAgencyIntelligenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, requisition_id):
        denied = _require_agency_intelligence_access(request, include_recruiter=True)
        if denied:
            return denied

        intelligence = AgencyIntelligenceService.build_job_agency_intelligence(
            tenant_id=request.user.tenant_id,
            requisition_id=requisition_id,
        )

        return success_response(
            data=intelligence,
            message="Job agency intelligence retrieved."
        )
class AgencyMyJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.jobs.models import JobRequisition

        assignments = AgencyJobAssignment.objects.filter(
            agency_tenant_id=request.user.tenant_id,
            is_deleted=False,
            status='active'
        )
        search = get_search_query(request.query_params)
        requisitions_qs = JobRequisition.objects.filter(
            id__in=assignments.values('requisition_id'),
            is_deleted=False,
        )
        if search:
            requisitions_qs, _ = apply_keyword_search(
                requisitions_qs,
                query=search,
                fields=('title', 'job_ref_id', 'description', 'requirements', 'skills_required', 'status'),
                typo_tolerant=True,
            )
        assignments = assignments.filter(requisition_id__in=requisitions_qs.values('id'))
        total = assignments.count()
        limit, offset = parse_limit_offset(request.query_params, default_limit=50, max_limit=200)
        assignments = assignments.order_by('-updated_at')[offset:offset + limit]

        requisition_map = {
            str(req.id): req for req in JobRequisition.objects.filter(
                id__in=assignments.values('requisition_id'),
                is_deleted=False,
            )
        }
        result = []
        for assignment in assignments:
            req = requisition_map.get(str(assignment.requisition_id))
            if not req:
                continue
            result.append({
                'assignment': AgencyJobAssignmentSerializer(assignment).data,
                'requisition': {
                    'id': str(req.id),
                    'title': req.title,
                    'job_type': req.job_type,
                    'work_mode': req.work_mode,
                    'experience_min': req.experience_min,
                    'experience_max': req.experience_max,
                    'skills_required': req.skills_required,
                    'status': req.status,
                }
            })

        return success_response(
            data={'jobs': result},
            message="Assigned jobs retrieved.",
            meta={'total': total, 'limit': limit, 'offset': offset}
        )


class AgencySubmitCandidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.pipeline.models import Application, ApplicationStageHistory
        from apps.candidates.models import Candidate, CandidateProfile
        from apps.candidates.identity_service import resolve_candidate_identity, merge_candidate_payload
        from apps.core import events

        candidate_id = request.data.get('candidate_id')
        requisition_id = request.data.get('requisition_id')
        cover_note = request.data.get('cover_note', '')

        if not candidate_id or not requisition_id:
            return error_response("candidate_id and requisition_id are required.")

        # Get agency's candidate record
        try:
            agency_candidate = Candidate.objects.get(
                id=candidate_id,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Candidate.DoesNotExist:
            return error_response("Candidate not found in your pool.", status_code=status.HTTP_404_NOT_FOUND)

        # Verify assignment exists and is active
        assignment = AgencyJobAssignment.objects.filter(
            agency_tenant_id=request.user.tenant_id,
            requisition_id=requisition_id,
            status='active',
            is_deleted=False
        ).first()

        if not assignment:
            return error_response(
                "You are not assigned to this job.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Check max submissions
        if assignment.max_submissions:
            if assignment.submission_count >= assignment.max_submissions:
                return error_response(
                    "Maximum submission limit reached for this job.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        company_id = assignment.tenant_id

        # 1. Candidate canonical identity resolution in company context.
        resolution = resolve_candidate_identity(
            email=agency_candidate.email,
            phone=agency_candidate.phone or agency_candidate.phone_number,
            passport_id=agency_candidate.passport_id,
            tenant_id=company_id,
            create_if_missing=True,
            allow_cross_tenant=True,
            actor_user_id=request.user.id,
            ensure_tenant_association_flag=True,
            ensure_visibility=True,
            source='agency_submission',
            candidate_defaults={
                'tenant_id': company_id,
                'first_name': agency_candidate.first_name,
                'last_name': agency_candidate.last_name,
                'email': agency_candidate.email,
                'phone': agency_candidate.phone,
                'whatsapp': agency_candidate.whatsapp,
                'linkedin_url': agency_candidate.linkedin_url,
                'current_title': agency_candidate.current_title,
                'current_company': agency_candidate.current_company,
                'current_location_city': agency_candidate.current_location_city,
                'current_location_country': agency_candidate.current_location_country,
                'experience_years': agency_candidate.experience_years,
                'skills': agency_candidate.skills,
                'languages': agency_candidate.languages,
                'source': 'agency',
                'source_type': 'agency',
                'source_detail': f"Submitted by Agency (Tenant ID: {request.user.tenant_id})",
                'owner_tenant_id': request.user.tenant_id,
                'owner_user_id': request.user.id,
                'created_by': request.user.id,
                'candidate_state': 'NEW_LEAD',
                'candidate_pool': 'GENERAL',
                'is_general_pool_used': False,
            },
        )
        target_candidate = resolution.candidate
        merge_candidate_payload(
            target_candidate,
            {
                'first_name': agency_candidate.first_name,
                'last_name': agency_candidate.last_name,
                'email': agency_candidate.email,
                'phone': agency_candidate.phone,
                'whatsapp': agency_candidate.whatsapp,
                'linkedin_url': agency_candidate.linkedin_url,
                'current_title': agency_candidate.current_title,
                'current_company': agency_candidate.current_company,
                'current_location_city': agency_candidate.current_location_city,
                'current_location_country': agency_candidate.current_location_country,
                'experience_years': agency_candidate.experience_years,
                'skills': agency_candidate.skills,
                'languages': agency_candidate.languages,
                'source': 'agency',
                'source_type': 'agency',
            },
            overwrite=False,
        )
        try:
            agency_profile = CandidateProfile.objects.get(candidate_id=agency_candidate.id)
            target_profile, target_profile_created = CandidateProfile.objects.get_or_create(
                candidate_id=target_candidate.id,
                defaults={
                    'tenant_id': company_id,
                    'summary': agency_profile.summary,
                    'work_experience': agency_profile.work_experience,
                    'education': agency_profile.education,
                    'certifications': agency_profile.certifications,
                    'projects': agency_profile.projects,
                    'cv_url': agency_profile.cv_url,
                    'cv_parsed_data': agency_profile.cv_parsed_data,
                    'created_by': request.user.id,
                },
            )
            if not target_profile_created:
                changed = False
                if agency_profile.summary and not target_profile.summary:
                    target_profile.summary = agency_profile.summary
                    changed = True
                if agency_profile.work_experience and not target_profile.work_experience:
                    target_profile.work_experience = agency_profile.work_experience
                    changed = True
                if agency_profile.education and not target_profile.education:
                    target_profile.education = agency_profile.education
                    changed = True
                if agency_profile.certifications and not target_profile.certifications:
                    target_profile.certifications = agency_profile.certifications
                    changed = True
                if agency_profile.projects and not target_profile.projects:
                    target_profile.projects = agency_profile.projects
                    changed = True
                if agency_profile.cv_url and not target_profile.cv_url:
                    target_profile.cv_url = agency_profile.cv_url
                    changed = True
                if agency_profile.cv_parsed_data and not target_profile.cv_parsed_data:
                    target_profile.cv_parsed_data = agency_profile.cv_parsed_data
                    changed = True
                if changed:
                    target_profile.save(update_fields=[
                        'summary', 'work_experience', 'education', 'certifications',
                        'projects', 'cv_url', 'cv_parsed_data', 'updated_at',
                    ])
        except CandidateProfile.DoesNotExist:
            CandidateProfile.objects.get_or_create(
                candidate_id=target_candidate.id,
                defaults={
                    'tenant_id': company_id,
                    'created_by': request.user.id,
                },
            )

        # Check if candidate already has an application for this job in company pool
        existing_app = Application.objects.filter(
            candidate_id=target_candidate.id,
            requisition_id=requisition_id,
            tenant_id=company_id,
            is_deleted=False
        ).first()

        if existing_app:
            # Mark as duplicate attempt in metadata
            if 'duplicate_attempts' not in existing_app.metadata:
                existing_app.metadata['duplicate_attempts'] = []
            
            existing_app.metadata['duplicate_attempts'].append({
                'attempted_at': timezone.now().isoformat(),
                'attempted_by': str(request.user.id),
                'attempted_by_tenant': str(request.user.tenant_id),
                'source': 'agency',
                'cover_note': cover_note
            })
            existing_app.save(update_fields=['metadata', 'updated_at'])

            return error_response(
                "This candidate has already been submitted/applied for this job.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Get first stage of requisition
        from apps.jobs.models import JobStage
        first_stage = JobStage.objects.filter(
            requisition_id=requisition_id,
            is_active=True
        ).order_by('stage_order').first()

        # 2. Create application
        application = Application.objects.create(
            tenant_id=company_id,
            candidate_id=target_candidate.id,
            requisition_id=requisition_id,
            agency_id=request.user.tenant_id,
            is_agency_submission=True,
            submitted_by=request.user.id,
            submitted_by_tenant_id=request.user.tenant_id,
            current_stage_id=first_stage.id if first_stage else None,
            status='applied',
            source='agency',
            source_detail=cover_note,
            created_by=request.user.id,
        )

        # 3. Always create ApplicationStageHistory
        ApplicationStageHistory.objects.create(
            tenant_id=company_id,
            application_id=application.id,
            to_stage_id=first_stage.id if first_stage else None,
            to_status='applied',
            moved_by=request.user.id,
            notes='Candidate submitted by agency'
        )

        # Increment submission count
        assignment.submission_count += 1
        assignment.save(update_fields=['submission_count'])

        # 4. Emit events
        events.agency.candidate_submitted.send(
            sender=self.__class__,
            application=application,
            agency_user=request.user,
            request=request
        )
        create_or_update_protection_on_submission(
            candidate_id=target_candidate.id,
            source_tenant_id=request.user.tenant_id,
            target_tenant_id=company_id,
            context_job_id=requisition_id,
            actor_user_id=request.user.id,
        )
        events.application.created.send(
            sender=self.__class__,
            application=application,
            user=request.user,
            request=request
        )

        from apps.pipeline.serializers import ApplicationSerializer
        return success_response(
            data={'application': ApplicationSerializer(application).data},
            message="Candidate submitted successfully.",
            status_code=status.HTTP_201_CREATED
        )


class AgencyMySubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.pipeline.models import Application
        from apps.pipeline.serializers import ApplicationSerializer

        applications = Application.objects.filter(
            agency_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)

        requisition_id = request.query_params.get('requisition_id')
        if requisition_id:
            applications = applications.filter(requisition_id=requisition_id)

        search = get_search_query(request.query_params)
        if search:
            from apps.candidates.models import Candidate
            from apps.jobs.models import JobRequisition

            candidate_ids = Candidate.objects.filter(
                tenant_id=request.user.tenant_id,
                is_deleted=False,
            )
            candidate_ids, _ = apply_keyword_search(
                candidate_ids,
                query=search,
                fields=('first_name', 'last_name', 'email', 'current_title', 'candidate_ref_id', 'skills'),
                typo_tolerant=True,
            )
            requisition_ids = JobRequisition.objects.filter(
                id__in=applications.values('requisition_id'),
                is_deleted=False,
            )
            requisition_ids, _ = apply_keyword_search(
                requisition_ids,
                query=search,
                fields=('title', 'job_ref_id', 'description', 'requirements', 'skills_required'),
                typo_tolerant=True,
            )
            applications = applications.filter(
                Q(candidate_id__in=candidate_ids.values('id')) |
                Q(requisition_id__in=requisition_ids.values('id'))
            )

        total = applications.count()
        limit, offset = parse_limit_offset(request.query_params, default_limit=50, max_limit=200)
        applications = applications[offset:offset + limit]

        return success_response(
            data={'submissions': ApplicationSerializer(applications, many=True).data},
            message="Submissions retrieved.",
            meta={'total': total, 'limit': limit, 'offset': offset}
        )


class AgencyMyClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        relationships = AgencyClientRelationship.objects.filter(
            agency_tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        status_filter = request.query_params.get('status')
        if status_filter:
            relationships = relationships.filter(status=status_filter)

        search = get_search_query(request.query_params)
        if search:
            relationships, _ = apply_keyword_search(
                relationships,
                query=search,
                fields=(
                    'contact_person_name',
                    'contact_email',
                    'contact_phone',
                    'industry',
                    'invited_via',
                    'notes',
                ),
                typo_tolerant=True,
            )
        total = relationships.count()
        limit, offset = parse_limit_offset(request.query_params, default_limit=50, max_limit=200)
        relationships = relationships.order_by('-updated_at')[offset:offset + limit]

        return success_response(
            data={'clients': AgencyClientRelationshipSerializer(relationships, many=True).data},
            message="Clients retrieved.",
            meta={'total': total, 'limit': limit, 'offset': offset}
        )


import re
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta


class TenantLookupView(APIView):
    """
    Enhanced lookup: search by email, return tenant status.
    Returns whether found as full tenant, guest portal, or not found.
    Used by both company and agency sides in Add Agency / Add Client forms.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return error_response("Search query required.")

        from apps.accounts.models import CustomUser
        from apps.tenants.models import Client
        from apps.organisations.models import Organisation
        from apps.agencies.models import GuestPortal
        from django.db.models import Q

        # Step 1: Check full tenant users
        user = CustomUser.objects.filter(
            Q(email__iexact=q) | Q(phone=q)
        ).first()

        if user and user.tenant_id:
            org = Organisation.objects.filter(tenant_id=user.tenant_id).first()
            if org:
                return success_response(
                    data={
                        'found': True,
                        'source': 'full_tenant',
                        'tenant_id': str(user.tenant_id),
                        'name': org.name,
                        'tenant_type': org.org_type,
                        'industry': org.industry or '',
                        'email': user.email,
                        'slug': None,
                    },
                    message="Found as full tenant."
                )

        # Step 2: Check guest portals
        portal = GuestPortal.objects.filter(
            contact_email__iexact=q,
            is_deleted=False
        ).first()

        if portal:
            return success_response(
                data={
                    'found': True,
                    'source': 'guest_portal',
                    'portal_id': str(portal.id),
                    'name': portal.name,
                    'tenant_type': portal.portal_type,
                    'email': portal.contact_email,
                    'slug': portal.slug,
                    'portal_status': portal.status,
                },
                message="Found as guest portal."
            )

        # Step 3: Not found — return empty so frontend shows manual entry
        return success_response(
            data={
                'found': False,
                'email': q,
                # Auto-generate a slug preview from the email domain
                'suggested_slug': slugify(q.split('@')[-1].split('.')[0]) if '@' in q else '',
            },
            message="Not found in system."
        )


class GuestPortalCreateView(APIView):
    """
    Creates a guest portal and sends invite email.
    Used when:
    - Company invites agency not in system (portal_type=agency_guest)
    - Agency invites company not in system (portal_type=client_guest)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.agencies.models import GuestPortal, AgencyClientRelationship
        from django.utils.text import slugify

        portal_type = request.data.get('portal_type')  # agency_guest | client_guest
        name = request.data.get('name', '').strip()
        contact_email = request.data.get('contact_email', '').strip()
        contact_name = request.data.get('contact_name', '').strip()
        contact_phone = request.data.get('contact_phone', '').strip()
        invite_message = request.data.get('invite_message', '').strip()
        slug_input = request.data.get('slug', '').strip()

        if not portal_type or not name or not contact_email:
            return error_response("portal_type, name, and contact_email are required.")

        if portal_type not in ['agency_guest', 'client_guest']:
            return error_response("portal_type must be agency_guest or client_guest.")

        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while GuestPortal.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Create portal
        portal = GuestPortal(
            portal_type=portal_type,
            name=name,
            slug=slug,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            invite_message=invite_message,
            created_by_tenant_id=request.user.tenant_id,
            created_by_user_id=request.user.id,
            status='pending',
        )
        portal.generate_invite_token()
        portal.invite_sent_at = timezone.now()
        portal.invite_expires_at = timezone.now() + timedelta(days=7)
        portal.save()

        # Create relationship record
        if portal_type == 'agency_guest':
            # Company created portal for agency
            AgencyClientRelationship.objects.create(
                tenant_id=request.user.tenant_id,
                company_tenant_id=request.user.tenant_id,
                agency_tenant_id=None,
                guest_portal_id=portal.id,
                connection_type='agency_guest',
                invited_by='company',
                contact_email=contact_email,
                contact_person_name=request.data.get('contact_name', '').strip(),
                contact_phone=request.data.get('contact_phone', '').strip(),
                industry=request.data.get('industry', '').strip(),
                commission_percentage=request.data.get('commission_percentage') or None,
                commission_type=request.data.get('commission_type', 'percentage'),
                payment_terms=request.data.get('payment_terms', []),
                payment_schedule=request.data.get('payment_schedule', []),
                sla_submission_hours=request.data.get('sla_submission_hours', 48),
                sla_feedback_hours=request.data.get('sla_feedback_hours', 72),
                contract_start_date=request.data.get('contract_start_date') or None,
                contract_end_date=request.data.get('contract_end_date') or None,
                retention_enabled=_to_bool(request.data.get('retention_enabled', False)),
                retention_days=request.data.get('retention_days') or 90,
                retention_start_type=request.data.get('retention_start_type') or 'submission_date',
                retention_scope=request.data.get('retention_scope') or 'job_only',
                retention_post_expiry=request.data.get('retention_post_expiry') or 'shared',
                replacement_guarantee_enabled=_to_bool(request.data.get('replacement_guarantee_enabled', False)),
                guarantee_period_days=request.data.get('guarantee_period_days') or 30,
                guarantee_start_type=request.data.get('guarantee_start_type') or 'joining_date',
                guarantee_resolution_type=request.data.get('guarantee_resolution_type') or 'replacement_only',
                refund_mode=request.data.get('refund_mode', ''),
                refund_percentage=request.data.get('refund_percentage') or None,
                replacement_attempt_limit=str(request.data.get('replacement_attempt_limit') or '1'),
                guarantee_notes=request.data.get('guarantee_notes', ''),
                notes=request.data.get('notes', ''),
                status='pending',
                created_by=request.user.id,
                metadata={'agency_name': name},
            )
        else:
            # Agency created portal for client
            AgencyClientRelationship.objects.create(
                tenant_id=request.user.tenant_id,
                agency_tenant_id=request.user.tenant_id,
                company_tenant_id=None,
                guest_portal_id=portal.id,
                connection_type='client_guest',
                invited_by='agency',
                contact_email=contact_email,
                contact_person_name=request.data.get('contact_name', '').strip(),
                contact_phone=request.data.get('contact_phone', '').strip(),
                industry=request.data.get('industry', '').strip(),
                commission_percentage=request.data.get('commission_percentage') or None,
                commission_type=request.data.get('commission_type', 'percentage'),
                payment_terms=request.data.get('payment_terms', []),
                payment_schedule=request.data.get('payment_schedule', []),
                sla_submission_hours=request.data.get('sla_submission_hours', 48),
                sla_feedback_hours=request.data.get('sla_feedback_hours', 72),
                contract_start_date=request.data.get('contract_start_date') or None,
                contract_end_date=request.data.get('contract_end_date') or None,
                retention_enabled=_to_bool(request.data.get('retention_enabled', False)),
                retention_days=request.data.get('retention_days') or 90,
                retention_start_type=request.data.get('retention_start_type') or 'submission_date',
                retention_scope=request.data.get('retention_scope') or 'job_only',
                retention_post_expiry=request.data.get('retention_post_expiry') or 'shared',
                replacement_guarantee_enabled=_to_bool(request.data.get('replacement_guarantee_enabled', False)),
                guarantee_period_days=request.data.get('guarantee_period_days') or 30,
                guarantee_start_type=request.data.get('guarantee_start_type') or 'joining_date',
                guarantee_resolution_type=request.data.get('guarantee_resolution_type') or 'replacement_only',
                refund_mode=request.data.get('refund_mode', ''),
                refund_percentage=request.data.get('refund_percentage') or None,
                replacement_attempt_limit=str(request.data.get('replacement_attempt_limit') or '1'),
                guarantee_notes=request.data.get('guarantee_notes', ''),
                notes=request.data.get('notes', ''),
                status='pending',
                created_by=request.user.id,
                metadata={'client_name': name},
            )

        # Send invite email to guest
        from apps.communications.services import EmailRoutingService
        EmailRoutingService.send_email(
            subject=f"Access your {portal.portal_type} Portal - {portal.name}",
            body_text=(
                f"Hi,\n\n"
                f"{request.user.first_name or 'Someone'} has invited you to access the {portal.portal_type} portal for {portal.name}.\n\n"
                f"You can access it here: {settings.FRONTEND_URL}/portal/{portal.slug}"
            ),
            body_html=None,
            recipient_list=[portal.contact_email],
            user_id=request.user.id,
            tenant_id=request.user.tenant_id
        )

        return success_response(
            data={
                'portal': {
                    'id': str(portal.id),
                    'name': portal.name,
                    'slug': portal.slug,
                    'portal_url': f"https://{portal.slug}.recruitos.com",
                    'status': portal.status,
                    'invite_expires_at': portal.invite_expires_at.isoformat(),
                }
            },
            message="Guest portal created and invite sent.",
            status_code=status.HTTP_201_CREATED
        )


class EmailTrackingCreateView(APIView):
    """
    Agency adds client as email tracking only.
    No portal, no invite. System monitors email domain.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.agencies.models import EmailTrackingConfig, AgencyClientRelationship

        client_name = request.data.get('client_name', '').strip()
        contact_email = request.data.get('contact_email', '').strip()
        contact_name = request.data.get('contact_name', '').strip()
        notes = request.data.get('notes', '').strip()

        if not client_name or not contact_email:
            return error_response("client_name and contact_email are required.")

        # Extract domain
        email_domain = contact_email.split('@')[-1] if '@' in contact_email else contact_email

        config = EmailTrackingConfig.objects.create(
            agency_tenant_id=request.user.tenant_id,
            client_name=client_name,
            email_domain=f"@{email_domain}",
            contact_email=contact_email,
            contact_name=contact_name,
            notes=notes,
            created_by=request.user.id,
        )

        # Create relationship record as email_tracking type
        AgencyClientRelationship.objects.create(
            tenant_id=request.user.tenant_id,
            agency_tenant_id=request.user.tenant_id,
            company_tenant_id=None,
            email_tracking_id=config.id,
            connection_type='email_tracking',
            invited_by='agency',
            contact_email=contact_email,
            contact_person_name=contact_name,
            contact_phone=request.data.get('contact_phone', '').strip(),
            industry=request.data.get('industry', '').strip(),
            commission_percentage=request.data.get('commission_percentage') or None,
            commission_type=request.data.get('commission_type', 'percentage'),
            payment_terms=request.data.get('payment_terms', []),
            payment_schedule=request.data.get('payment_schedule', []),
            sla_submission_hours=request.data.get('sla_submission_hours', 48),
            sla_feedback_hours=request.data.get('sla_feedback_hours', 72),
            contract_start_date=request.data.get('contract_start_date') or None,
            contract_end_date=request.data.get('contract_end_date') or None,
            retention_enabled=_to_bool(request.data.get('retention_enabled', False)),
            retention_days=request.data.get('retention_days') or 90,
            retention_start_type=request.data.get('retention_start_type') or 'submission_date',
            retention_scope=request.data.get('retention_scope') or 'job_only',
            retention_post_expiry=request.data.get('retention_post_expiry') or 'shared',
            replacement_guarantee_enabled=_to_bool(request.data.get('replacement_guarantee_enabled', False)),
            guarantee_period_days=request.data.get('guarantee_period_days') or 30,
            guarantee_start_type=request.data.get('guarantee_start_type') or 'joining_date',
            guarantee_resolution_type=request.data.get('guarantee_resolution_type') or 'replacement_only',
            refund_mode=request.data.get('refund_mode', ''),
            refund_percentage=request.data.get('refund_percentage') or None,
            replacement_attempt_limit=str(request.data.get('replacement_attempt_limit') or '1'),
            guarantee_notes=request.data.get('guarantee_notes', ''),
            notes=request.data.get('notes', ''),
            status='active',
            created_by=request.user.id,
        )

        return success_response(
            data={
                'config': {
                    'id': str(config.id),
                    'client_name': config.client_name,
                    'email_domain': config.email_domain,
                    'status': config.status,
                }
            },
            message="Email tracking set up successfully.",
            status_code=status.HTTP_201_CREATED
        )


class OfflineClientCreateView(APIView):
    """
    Agency adds client as offline (no portal, no email tracking).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.agencies.models import AgencyClientRelationship

        client_name = request.data.get('client_name', '').strip()
        contact_email = request.data.get('contact_email', '').strip()
        contact_name = request.data.get('contact_name', '').strip()
        contact_phone = request.data.get('contact_phone', '').strip()
        their_ats_url = request.data.get('their_ats_url', '').strip()
        notes = request.data.get('notes', '').strip()
        receive_via_email = request.data.get('receive_via_email', True)

        if not client_name:
            return error_response("client_name is required.")

        rel = AgencyClientRelationship.objects.create(
            tenant_id=request.user.tenant_id,
            agency_tenant_id=request.user.tenant_id,
            company_tenant_id=None,
            connection_type='offline',
            invited_by='agency',
            contact_email=contact_email,
            contact_person_name=contact_name,
            contact_phone=contact_phone,
            their_ats_url=their_ats_url,
            industry=request.data.get('industry', '').strip(),
            commission_percentage=request.data.get('commission_percentage') or None,
            commission_type=request.data.get('commission_type', 'percentage'),
            payment_terms=request.data.get('payment_terms', []),
            payment_schedule=request.data.get('payment_schedule', []),
            sla_submission_hours=request.data.get('sla_submission_hours', 48),
            sla_feedback_hours=request.data.get('sla_feedback_hours', 72),
            contract_start_date=request.data.get('contract_start_date') or None,
            contract_end_date=request.data.get('contract_end_date') or None,
            retention_enabled=_to_bool(request.data.get('retention_enabled', False)),
            retention_days=request.data.get('retention_days') or 90,
            retention_start_type=request.data.get('retention_start_type') or 'submission_date',
            retention_scope=request.data.get('retention_scope') or 'job_only',
            retention_post_expiry=request.data.get('retention_post_expiry') or 'shared',
            replacement_guarantee_enabled=_to_bool(request.data.get('replacement_guarantee_enabled', False)),
            guarantee_period_days=request.data.get('guarantee_period_days') or 30,
            guarantee_start_type=request.data.get('guarantee_start_type') or 'joining_date',
            guarantee_resolution_type=request.data.get('guarantee_resolution_type') or 'replacement_only',
            refund_mode=request.data.get('refund_mode', ''),
            refund_percentage=request.data.get('refund_percentage') or None,
            replacement_attempt_limit=str(request.data.get('replacement_attempt_limit') or '1'),
            guarantee_notes=request.data.get('guarantee_notes', ''),
            notes=notes,
            status='active',
            created_by=request.user.id,
            metadata={
                'client_name': client_name,
                'receive_via_email': receive_via_email,
            }
        )

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Offline client added.",
            status_code=status.HTTP_201_CREATED
        )


class GuestPortalResendInviteView(APIView):
    """
    Resend invite for a pending/expired guest portal.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from apps.agencies.models import GuestPortal

        try:
            portal = GuestPortal.objects.get(
                id=pk,
                created_by_tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except GuestPortal.DoesNotExist:
            return error_response("Portal not found.", status_code=status.HTTP_404_NOT_FOUND)

        portal.generate_invite_token()
        portal.invite_sent_at = timezone.now()
        portal.invite_expires_at = timezone.now() + timedelta(days=7)
        portal.status = 'pending'
        portal.save()

        if not portal.contact_email:
            return error_response("Portal contact email is missing.", status_code=status.HTTP_400_BAD_REQUEST)

        invite_link = f"{settings.FRONTEND_URL}/portal/accept/{portal.invite_token}"
        send_agency_invite_email(
            recipient_email=portal.contact_email,
            sender_name=request.user.first_name or 'Someone',
            portal_name=portal.name,
            portal_type=portal.portal_type,
            invite_link=invite_link,
            user_id=request.user.id,
            tenant_id=request.user.tenant_id,
        )

        AuditService.log(
            tenant_id=request.user.tenant_id,
            actor_id=request.user.id,
            action_type='agency_guest_portal_invite_resent',
            target_type='agency_guest_portal',
            target_id=portal.id,
            metadata_json={'portal_type': portal.portal_type, 'contact_email': portal.contact_email},
        )

        return success_response(
            data={'portal_id': str(portal.id), 'status': portal.status},
            message="Invite resent."
        )
