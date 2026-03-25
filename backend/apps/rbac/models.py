"""
RBAC models: Permission, Role, RolePermission.

Design:
  - Permission.code uses the format  module.resource.action
    e.g.  candidates.candidate.view
  - Role names mirror CustomUser.role choices so lookups are a simple
    Role.objects.get(name=user.role) — no extra join.
  - tenant_id on Role is NULL for built-in system roles; when custom per-tenant
    roles are added later, set tenant_id to scope them to that tenant.
  - The ManyToManyField through RolePermission leaves room to attach extra
    metadata to the mapping (e.g. scope, conditions) without a schema change.
"""
import uuid
from django.db import models


class Permission(models.Model):
    """
    A single, indivisible action on a resource in a module.

    code format:  <module>.<resource>.<action>
    example:      candidates.candidate.view
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=200, unique=True, db_index=True)
    label = models.CharField(max_length=200, blank=True)
    module = models.CharField(max_length=100, db_index=True)
    module_label = models.CharField(max_length=120, blank=True)
    resource = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    # Reserved for future use: scope hints, UI metadata, etc.
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rbac_permission'
        ordering = ['module', 'resource', 'action']

    def __str__(self):
        return self.code


class Role(models.Model):
    """
    A named bundle of permissions.

    name must match a CustomUser.role value for built-in roles so
    get_user_permissions() can look up by user.role without a join.

    is_system=True means this role was created by seed_rbac and should not be
    deleted — only its permission assignments can change.

    tenant_id=None means platform-wide.  Set it for future per-tenant custom
    roles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True)
    display_name = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    is_system = models.BooleanField(default=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    based_on_role = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='derived_roles',
    )
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rbac_role'
        # A given role name is unique per tenant (NULL = platform-wide).
        # Using a partial unique constraint would be ideal but requires
        # database support; this handles the common cases safely.
        unique_together = [('name', 'tenant_id')]

    def __str__(self):
        return self.display_name or self.name


class RolePermission(models.Model):
    """
    Explicit join table so scope / extra conditions can be added later.
    For now it is a simple role → permission mapping.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name='role_permissions'
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name='role_permissions'
    )
    # Placeholder for future scope expansion:
    #   scope = models.CharField(max_length=20, default='all',
    #               choices=[('own','own'),('team','team'),('all','all')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rbac_role_permission'
        unique_together = [('role', 'permission')]

    def __str__(self):
        return f'{self.role.name} → {self.permission.code}'
