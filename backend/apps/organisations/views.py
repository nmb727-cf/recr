from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.organisations.models import Organisation, Department, Location, Team, TeamMembership
from apps.organisations.serializers import (
    OrganisationSerializer, DepartmentSerializer,
    LocationSerializer, TeamSerializer, TeamMembershipSerializer,
)
from apps.core.responses import success_response, error_response
from apps.accounts.models import CustomUser
from apps.accounts.serializers import UserSerializer
from django.db.models import Count


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
        ).annotate(member_count=Count('memberships')).order_by('name')
        
        # Include member_count in the serialized data
        data = TeamSerializer(teams, many=True).data
        for i, team in enumerate(teams):
            data[i]['member_count'] = team.member_count
            
        return success_response(
            data={'teams': data},
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


class TeamMemberListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        memberships = TeamMembership.objects.filter(
            team_id=team_id,
            tenant_id=request.user.tenant_id
        )
        
        # Fetch user details for each membership
        user_ids = [m.user_id for m in memberships]
        users = CustomUser.objects.filter(id__in=user_ids)
        user_map = {str(u.id): UserSerializer(u).data for u in users}
        
        data = []
        for m in memberships:
            member_data = TeamMembershipSerializer(m).data
            member_data['user'] = user_map.get(str(m.user_id))
            data.append(member_data)
            
        return success_response(
            data={'members': data},
            message="Team members retrieved."
        )

    def post(self, request, team_id):
        user_id = request.data.get('user_id')
        role = request.data.get('role', '')
        
        if not user_id:
            return error_response("user_id is required.")
            
        # Verify team exists and belongs to tenant
        try:
            team = Team.objects.get(id=team_id, tenant_id=request.user.tenant_id)
        except Team.DoesNotExist:
            return error_response("Team not found.", status_code=status.HTTP_404_NOT_FOUND)
            
        # Verify user belongs to tenant
        try:
            user = CustomUser.objects.get(id=user_id, tenant_id=request.user.tenant_id)
        except CustomUser.DoesNotExist:
            return error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)
            
        membership, created = TeamMembership.objects.get_or_create(
            team=team,
            user_id=user_id,
            defaults={
                'tenant_id': request.user.tenant_id,
                'role': role,
                'created_by': request.user.id
            }
        )
        
        if not created:
            return error_response("User is already a member of this team.")
            
        return success_response(
            data={'membership': TeamMembershipSerializer(membership).data},
            message="Member added to team.",
            status_code=status.HTTP_201_CREATED
        )


class TeamMemberDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, team_id, user_id):
        try:
            membership = TeamMembership.objects.get(
                team_id=team_id,
                user_id=user_id,
                tenant_id=request.user.tenant_id
            )
            membership.delete()
            return success_response(message="Member removed from team.", status_code=status.HTTP_204_NO_CONTENT)
        except TeamMembership.DoesNotExist:
            return error_response("Membership not found.", status_code=status.HTTP_404_NOT_FOUND)


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
