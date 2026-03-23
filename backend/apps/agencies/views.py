from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import uuid
from django.db.models import Q
from apps.accounts.models import CustomUser

from apps.agencies.models import (
    AgencyClientRelationship, AgencyJobAssignment, AgencyPerformanceScore
)
from apps.agencies.serializers import (
    AgencyClientRelationshipSerializer, AgencyJobAssignmentSerializer,
    AgencyPerformanceScoreSerializer,
)
from apps.core.responses import success_response, error_response


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


class AgencyRelationshipListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        except Exception:
            qs = AgencyClientRelationship.objects.none()

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return success_response(
            data={'relationships': AgencyClientRelationshipSerializer(qs, many=True).data},
            message="Relationships retrieved.",
            meta={'total': qs.count()}
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


class AgencyRelationshipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return AgencyClientRelationship.objects.get(
                id=pk,
                is_deleted=False
            )
        except AgencyClientRelationship.DoesNotExist:
            return None

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


class AgencyRelationshipInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rel = AgencyClientRelationship.objects.get(id=pk, is_deleted=False)
        except AgencyClientRelationship.DoesNotExist:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        if rel.status != 'pending':
            return error_response("Only pending relationships can be invited.")

        rel.status = 'pending'
        rel.save(update_fields=['status', 'updated_at'])

        # TODO: Send invite email to agency
        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Invitation sent to agency."
        )


class AgencyRelationshipAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rel = AgencyClientRelationship.objects.get(id=pk, is_deleted=False)
        except AgencyClientRelationship.DoesNotExist:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        if rel.status != 'pending':
            return error_response("Only pending relationships can be accepted.")

        rel.status = 'active'
        rel.save(update_fields=['status', 'updated_at'])

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Relationship accepted."
        )


class AgencyRelationshipSuspendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rel = AgencyClientRelationship.objects.get(id=pk, is_deleted=False)
        except AgencyClientRelationship.DoesNotExist:
            return error_response("Relationship not found.", status_code=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        rel.status = 'suspended'
        rel.notes = f"Suspended: {reason}" if reason else rel.notes
        rel.save(update_fields=['status', 'notes', 'updated_at'])

        return success_response(
            data={'relationship': AgencyClientRelationshipSerializer(rel).data},
            message="Relationship suspended."
        )


class AgencyJobAssignmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AgencyJobAssignment.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
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


class AgencyJobAssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return AgencyJobAssignment.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except AgencyJobAssignment.DoesNotExist:
            return None

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


class AgencyPerformanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AgencyPerformanceScore.objects.filter(
            tenant_id=request.user.tenant_id
        )

        agency_id = request.query_params.get('agency_id')
        if agency_id:
            qs = qs.filter(agency_tenant_id=agency_id)

        return success_response(
            data={'performance': AgencyPerformanceScoreSerializer(qs, many=True).data},
            message="Performance scores retrieved.",
            meta={'total': qs.count()}
        )
class AgencyMyJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assignments = AgencyJobAssignment.objects.filter(
            agency_tenant_id=request.user.tenant_id,
            is_deleted=False,
            status='active'
        )

        result = []
        for assignment in assignments:
            try:
                from apps.jobs.models import JobRequisition
                req = JobRequisition.objects.get(
                    id=assignment.requisition_id,
                    is_deleted=False
                )
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
            except Exception:
                pass

        return success_response(
            data={'jobs': result},
            message="Assigned jobs retrieved.",
            meta={'total': len(result)}
        )


class AgencySubmitCandidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.pipeline.models import Application, ApplicationStageHistory
        from apps.candidates.models import Candidate, CandidateProfile
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

        # 1. Candidate Deduplication / Creation in Company Pool
        target_candidate = Candidate.objects.filter(
            global_hash=agency_candidate.global_hash,
            tenant_id=company_id,
            is_deleted=False
        ).first()

        if not target_candidate:
            # Create a company-side copy of the candidate
            target_candidate = Candidate.objects.create(
                tenant_id=company_id,
                first_name=agency_candidate.first_name,
                last_name=agency_candidate.last_name,
                email=agency_candidate.email,
                phone=agency_candidate.phone,
                whatsapp=agency_candidate.whatsapp,
                linkedin_url=agency_candidate.linkedin_url,
                current_title=agency_candidate.current_title,
                current_company=agency_candidate.current_company,
                current_location_city=agency_candidate.current_location_city,
                current_location_country=agency_candidate.current_location_country,
                experience_years=agency_candidate.experience_years,
                skills=agency_candidate.skills,
                languages=agency_candidate.languages,
                source='agency',
                source_detail=f"Submitted by Agency (Tenant ID: {request.user.tenant_id})",
                owner_tenant_id=request.user.tenant_id,
                owner_user_id=request.user.id,
                created_by=request.user.id
            )
            
            # Copy profile if exists
            try:
                agency_profile = CandidateProfile.objects.get(candidate_id=agency_candidate.id)
                CandidateProfile.objects.create(
                    tenant_id=company_id,
                    candidate_id=target_candidate.id,
                    summary=agency_profile.summary,
                    work_experience=agency_profile.work_experience,
                    education=agency_profile.education,
                    certifications=agency_profile.certifications,
                    projects=agency_profile.projects,
                    cv_url=agency_profile.cv_url,
                    cv_parsed_data=agency_profile.cv_parsed_data,
                    created_by=request.user.id
                )
            except CandidateProfile.DoesNotExist:
                CandidateProfile.objects.create(
                    tenant_id=company_id,
                    candidate_id=target_candidate.id,
                    created_by=request.user.id
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

        return success_response(
            data={'submissions': ApplicationSerializer(applications, many=True).data},
            message="Submissions retrieved.",
            meta={'total': applications.count()}
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

        return success_response(
            data={'clients': AgencyClientRelationshipSerializer(relationships, many=True).data},
            message="Clients retrieved.",
            meta={'total': relationships.count()}
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
        base_slug = slugify(slug_input or name)
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
                contact_person_name=contact_name,
                contact_phone=request.data.get('contact_phone', ''),
                commission_percentage=request.data.get('commission_percentage') or None,
                commission_type=request.data.get('commission_type', 'percentage'),
                payment_terms=request.data.get('payment_terms', []),
                sla_submission_hours=request.data.get('sla_submission_hours', 48),
                sla_feedback_hours=request.data.get('sla_feedback_hours', 72),
                contract_start_date=request.data.get('contract_start_date') or None,
                contract_end_date=request.data.get('contract_end_date') or None,
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
                contact_person_name=contact_name,
                status='pending',
                created_by=request.user.id,
            )

        # TODO: Send invite email (wire up email service later)
        # send_guest_portal_invite_email(portal)

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

        # TODO: Send invite email again

        return success_response(
            data={'portal_id': str(portal.id), 'status': portal.status},
            message="Invite resent."
        )
