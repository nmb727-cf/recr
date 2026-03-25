from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.core.responses import success_response
from apps.core.responses import error_response
from apps.rbac.models import Permission, Role
from apps.rbac.utils import get_user_permissions


def _can_manage_roles(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return user.role in {
        'super_admin',
        'tenant_admin',
        'agency_owner',
        'agency_admin',
    }


def _tenant_type_from_user(user) -> str:
    role = getattr(user, 'role', '') or ''
    if role.startswith('agency_'):
        return 'agency'
    if role == 'candidate':
        return 'candidate'
    return 'company'


def _role_applicability(role_name: str) -> str:
    if role_name.startswith('agency_'):
        return 'agency'
    if role_name in {'tenant_admin', 'hr_manager', 'hiring_manager', 'recruiter', 'interviewer', 'viewer'}:
        return 'company'
    if role_name == 'candidate':
        return 'candidate'
    return 'shared'


def _permission_applicability(code: str) -> str:
    if code.startswith('agencies.'):
        return 'agency'
    if code.startswith('organisations.'):
        return 'company'
    return 'shared'


def _serialize_permission(qs):
    return list(
        qs.values(
            'id', 'code', 'label', 'description', 'module', 'module_label', 'resource', 'action', 'is_active'
        ).order_by('module', 'resource', 'action')
    )


def _serialize_role(role: Role):
    perms = role.permissions.filter(is_active=True)
    return {
        'id': str(role.id),
        'role_key': role.name,
        'role_name': role.display_name,
        'name': role.name,
        'display_name': role.display_name,
        'description': role.description,
        'is_system': role.is_system,
        'is_system_role': role.is_system,
        'is_assignable': role.name not in {'super_admin', 'candidate'},
        'tenant_type_applicability': _role_applicability(role.name),
        'tenant_id': str(role.tenant_id) if role.tenant_id else None,
        'based_on_role_id': str(role.based_on_role_id) if role.based_on_role_id else None,
        'permission_count': perms.count(),
        'permissions': _serialize_permission(perms),
    }


class RBACDebugView(APIView):
    """
    Returns all system roles + permissions + current user's effective permissions.
    Used by the frontend RBAC debug/admin page at /rbac-debug.
    Safe for any authenticated user — read-only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = (
            Role.objects
            .filter(tenant_id__isnull=True)
            .prefetch_related('permissions')
            .order_by('name')
        )
        roles_data = []
        for role in roles:
            perms = list(
                role.permissions
                .filter(is_active=True)
                .values('code', 'label', 'description', 'module', 'module_label', 'resource', 'action')
                .order_by('module', 'resource', 'action')
            )
            roles_data.append({
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'permission_count': len(perms),
                'permissions': perms,
            })

        all_permissions = list(
            Permission.objects
            .filter(is_active=True)
            .values('code', 'label', 'description', 'module', 'module_label', 'resource', 'action', 'is_active')
            .order_by('module', 'resource', 'action')
        )

        current_user_permissions = sorted(get_user_permissions(request.user))

        return success_response(data={
            'current_user': {
                'email': request.user.email,
                'role': request.user.role,
                'permission_count': len(current_user_permissions),
                'permissions': current_user_permissions,
            },
            'roles': roles_data,
            'all_permissions': all_permissions,
        })


class RBACRoleCatalogView(APIView):
    """
    Tenant-aware role catalog:
      - system_templates: platform-managed defaults
      - tenant_roles: editable roles for current tenant
      - all_permissions: active permissions with friendly metadata
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        system_templates = Role.objects.filter(
            tenant_id__isnull=True, is_system=True
        ).prefetch_related('permissions').order_by('display_name', 'name')
        tenant_roles = Role.objects.filter(
            tenant_id=tenant_id, is_system=False
        ).prefetch_related('permissions').order_by('display_name', 'name')

        permissions = _serialize_permission(Permission.objects.filter(is_active=True))
        for p in permissions:
            p['tenant_type_applicability'] = _permission_applicability(p['code'])

        return success_response(data={
            'can_manage_roles': _can_manage_roles(request.user),
            'system_templates': [_serialize_role(r) for r in system_templates],
            'tenant_roles': [_serialize_role(r) for r in tenant_roles],
            'all_permissions': permissions,
            'current_user': {
                'id': str(request.user.id),
                'email': request.user.email,
                'role': request.user.role,
                'tenant_id': str(request.user.tenant_id) if request.user.tenant_id else None,
                'permission_count': len(get_user_permissions(request.user)),
                'tenant_type': _tenant_type_from_user(request.user),
            },
        })

    @transaction.atomic
    def post(self, request):
        if not _can_manage_roles(request.user):
            return error_response(
                message='You are not allowed to create roles',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        tenant_id = request.user.tenant_id
        name = (request.data.get('name') or '').strip()
        display_name = (request.data.get('display_name') or '').strip() or name
        description = (request.data.get('description') or '').strip()
        permission_codes = request.data.get('permission_codes') or []
        based_on_role_id = request.data.get('based_on_role_id')

        if not name:
            return error_response(message='Role name is required')
        if not tenant_id:
            return error_response(message='Tenant context is required')

        exists = Role.objects.filter(name=name, tenant_id=tenant_id).exists()
        if exists:
            return error_response(message='A role with this name already exists in this tenant')

        based_on_role = None
        if based_on_role_id:
            based_on_role = Role.objects.filter(id=based_on_role_id).first()
            if based_on_role is None:
                return error_response(message='Template role not found')

        role = Role.objects.create(
            name=name,
            display_name=display_name,
            description=description,
            is_system=False,
            tenant_id=tenant_id,
            based_on_role=based_on_role,
        )

        if permission_codes:
            perms = list(Permission.objects.filter(code__in=permission_codes, is_active=True))
            role.permissions.set(perms)

        return success_response(
            data={'role': _serialize_role(role)},
            message='Role created',
            status_code=status.HTTP_201_CREATED,
        )


class RBACRoleCloneTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, template_role_id: str):
        if not _can_manage_roles(request.user):
            return error_response(
                message='You are not allowed to clone role templates',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        template_role = Role.objects.filter(
            id=template_role_id,
            tenant_id__isnull=True,
            is_system=True,
        ).prefetch_related('permissions').first()
        if template_role is None:
            return error_response(message='System role template not found')

        tenant_id = request.user.tenant_id
        if not tenant_id:
            return error_response(message='Tenant context is required')

        name = (request.data.get('name') or template_role.name).strip()
        display_name = (request.data.get('display_name') or template_role.display_name).strip()
        description = (request.data.get('description') or template_role.description).strip()

        if Role.objects.filter(name=name, tenant_id=tenant_id).exists():
            return error_response(message='A role with this name already exists in this tenant')

        role = Role.objects.create(
            name=name,
            display_name=display_name,
            description=description,
            is_system=False,
            tenant_id=tenant_id,
            based_on_role=template_role,
        )
        role.permissions.set(template_role.permissions.filter(is_active=True))

        return success_response(
            data={'role': _serialize_role(role)},
            message='Template cloned',
            status_code=status.HTTP_201_CREATED,
        )


class RBACRoleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_role(self, request, role_id: str):
        return Role.objects.filter(
            id=role_id,
            tenant_id=request.user.tenant_id,
            is_system=False,
        ).prefetch_related('permissions').first()

    @transaction.atomic
    def put(self, request, role_id: str):
        if not _can_manage_roles(request.user):
            return error_response(
                message='You are not allowed to edit roles',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        role = self._get_role(request, role_id)
        if role is None:
            return error_response(message='Tenant role not found', status_code=status.HTTP_404_NOT_FOUND)

        name = request.data.get('name')
        display_name = request.data.get('display_name')
        description = request.data.get('description')
        permission_codes = request.data.get('permission_codes')

        if name is not None:
            candidate = str(name).strip()
            if not candidate:
                return error_response(message='Role name cannot be empty')
            conflict = Role.objects.filter(
                name=candidate,
                tenant_id=request.user.tenant_id,
            ).exclude(id=role.id).exists()
            if conflict:
                return error_response(message='Another role with this name already exists')
            role.name = candidate
        if display_name is not None:
            role.display_name = str(display_name).strip() or role.name
        if description is not None:
            role.description = str(description).strip()
        role.save(update_fields=['name', 'display_name', 'description', 'updated_at'])

        if permission_codes is not None:
            perms = list(Permission.objects.filter(code__in=permission_codes, is_active=True))
            role.permissions.set(perms)

        return success_response(data={'role': _serialize_role(role)}, message='Role updated')

    @transaction.atomic
    def delete(self, request, role_id: str):
        if not _can_manage_roles(request.user):
            return error_response(
                message='You are not allowed to delete roles',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        role = self._get_role(request, role_id)
        if role is None:
            return error_response(message='Tenant role not found', status_code=status.HTTP_404_NOT_FOUND)

        # Preserve platform defaults and user role integrity: prevent deleting
        # the tenant role whose name matches the current user's active role.
        if role.name == request.user.role:
            return error_response(message='You cannot delete a role currently assigned to yourself')

        role.delete()
        return success_response(message='Role deleted')
