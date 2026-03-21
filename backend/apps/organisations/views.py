from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.organisations.models import Organisation, Department, Location, Team
from apps.organisations.serializers import (
    OrganisationSerializer, DepartmentSerializer,
    LocationSerializer, TeamSerializer,
)
from apps.core.responses import success_response, error_response


class OrganisationProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            org = Organisation.objects.get(
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
            return success_response(
                data={'organisation': OrganisationSerializer(org).data},
                message="Organisation profile retrieved."
            )
        except Organisation.DoesNotExist:
            return error_response(
                "Organisation profile not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        try:
            org = Organisation.objects.get(
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Organisation.DoesNotExist:
            # Create if not exists
            org = Organisation(tenant_id=request.user.tenant_id)

        serializer = OrganisationSerializer(org, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id
        )
        return success_response(
            data={'organisation': serializer.data},
            message="Organisation profile updated."
        )


class DepartmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = Department.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('name')
        return success_response(
            data={'departments': DepartmentSerializer(departments, many=True).data},
            message="Departments retrieved."
        )

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id
        )
        return success_response(
            data={'department': serializer.data},
            message="Department created.",
            status_code=status.HTTP_201_CREATED
        )


class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Department.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Department.DoesNotExist:
            return None

    def get(self, request, pk):
        dept = self.get_object(request, pk)
        if not dept:
            return error_response("Department not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'department': DepartmentSerializer(dept).data},
            message="Department retrieved."
        )

    def put(self, request, pk):
        dept = self.get_object(request, pk)
        if not dept:
            return error_response("Department not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = DepartmentSerializer(dept, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'department': serializer.data},
            message="Department updated."
        )

    def delete(self, request, pk):
        dept = self.get_object(request, pk)
        if not dept:
            return error_response("Department not found.", status_code=status.HTTP_404_NOT_FOUND)

        dept.soft_delete()
        return success_response(message="Department deleted.", status_code=status.HTTP_204_NO_CONTENT)


class LocationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        locations = Location.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('name')
        return success_response(
            data={'locations': LocationSerializer(locations, many=True).data},
            message="Locations retrieved."
        )

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id
        )
        return success_response(
            data={'location': serializer.data},
            message="Location created.",
            status_code=status.HTTP_201_CREATED
        )


class LocationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Location.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Location.DoesNotExist:
            return None

    def get(self, request, pk):
        loc = self.get_object(request, pk)
        if not loc:
            return error_response("Location not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'location': LocationSerializer(loc).data},
            message="Location retrieved."
        )

    def put(self, request, pk):
        loc = self.get_object(request, pk)
        if not loc:
            return error_response("Location not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = LocationSerializer(loc, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'location': serializer.data},
            message="Location updated."
        )

    def delete(self, request, pk):
        loc = self.get_object(request, pk)
        if not loc:
            return error_response("Location not found.", status_code=status.HTTP_404_NOT_FOUND)

        loc.soft_delete()
        return success_response(message="Location deleted.", status_code=status.HTTP_204_NO_CONTENT)


class TeamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teams = Team.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        ).order_by('name')
        return success_response(
            data={'teams': TeamSerializer(teams, many=True).data},
            message="Teams retrieved."
        )

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id
        )
        return success_response(
            data={'team': serializer.data},
            message="Team created.",
            status_code=status.HTTP_201_CREATED
        )


class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Team.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except Team.DoesNotExist:
            return None

    def get(self, request, pk):
        team = self.get_object(request, pk)
        if not team:
            return error_response("Team not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'team': TeamSerializer(team).data},
            message="Team retrieved."
        )

    def put(self, request, pk):
        team = self.get_object(request, pk)
        if not team:
            return error_response("Team not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = TeamSerializer(team, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            data={'team': serializer.data},
            message="Team updated."
        )

    def delete(self, request, pk):
        team = self.get_object(request, pk)
        if not team:
            return error_response("Team not found.", status_code=status.HTTP_404_NOT_FOUND)

        team.soft_delete()
        return success_response(message="Team deleted.", status_code=status.HTTP_204_NO_CONTENT)
   


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.accounts.models import CustomUser
        users = CustomUser.objects.filter(
            tenant_id=request.user.tenant_id,
            is_deleted=False
        )

        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)

        status_filter = request.query_params.get('status')
        if status_filter:
            users = users.filter(is_active=status_filter.lower() == 'true')

        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            users = users.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        from apps.accounts.serializers import UserSerializer
        return success_response(
            data={'users': UserSerializer(users, many=True).data},
            message="Users retrieved.",
            meta={'total': users.count()}
        )

    def post(self, request):
        from apps.accounts.models import CustomUser
        from apps.accounts.serializers import UserSerializer
        import secrets

        email = request.data.get('email')
        role = request.data.get('role', 'viewer')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email:
            return error_response("email is required.")

        if CustomUser.objects.filter(email=email.lower()).exists():
            return error_response(
                "A user with this email already exists.",
                status_code=status.HTTP_409_CONFLICT
            )

        # Create user with temp password
        temp_password = secrets.token_urlsafe(12)
        user = CustomUser.objects.create_user(
            email=email.lower(),
            password=temp_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            tenant_id=request.user.tenant_id,
        )

        # TODO: Send invite email with temp password

        return success_response(
            data={'user': UserSerializer(user).data},
            message="User invited successfully. They will receive an email to set their password.",
            status_code=status.HTTP_201_CREATED
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        from apps.accounts.models import CustomUser
        try:
            return CustomUser.objects.get(
                id=pk,
                tenant_id=request.user.tenant_id,
                is_deleted=False
            )
        except CustomUser.DoesNotExist:
            return None

    def get(self, request, pk):
        from apps.accounts.serializers import UserSerializer
        user = self.get_object(request, pk)
        if not user:
            return error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data={'user': UserSerializer(user).data},
            message="User retrieved."
        )

    def put(self, request, pk):
        from apps.accounts.serializers import UserSerializer
        user = self.get_object(request, pk)
        if not user:
            return error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)

        allowed_fields = ['role', 'is_active', 'first_name', 'last_name', 'phone']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        for field, value in data.items():
            setattr(user, field, value)
        user.save()

        return success_response(
            data={'user': UserSerializer(user).data},
            message="User updated."
        )

    def delete(self, request, pk):
        user = self.get_object(request, pk)
        if not user:
            return error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Cannot delete yourself
        if str(user.id) == str(request.user.id):
            return error_response("You cannot delete your own account.")

        user.is_deleted = True
        user.is_active = False
        user.save(update_fields=['is_deleted', 'is_active'])

        return success_response(
            message="User deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )
