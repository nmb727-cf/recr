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
