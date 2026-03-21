from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.agencies.models import (
    AgencyClientRelationship, AgencyJobAssignment, AgencyPerformanceScore
)
from apps.agencies.serializers import (
    AgencyClientRelationshipSerializer, AgencyJobAssignmentSerializer,
    AgencyPerformanceScoreSerializer,
)
from apps.core.responses import success_response, error_response


class AgencyRelationshipListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Company sees relationships where they are the company
        # Agency sees relationships where they are the agency
        from apps.tenants.models import Client
        try:
            tenant = Client.objects.get(id=request.user.tenant_id)
            if tenant.tenant_type == 'agency':
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

        # Check duplicate
        if AgencyClientRelationship.objects.filter(
            agency_tenant_id=data['agency_tenant_id'],
            company_tenant_id=data['company_tenant_id'],
            is_deleted=False
        ).exists():
            return error_response(
                "Relationship already exists.",
                status_code=status.HTTP_409_CONFLICT
            )

        relationship = serializer.save(
            tenant_id=request.user.tenant_id,
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