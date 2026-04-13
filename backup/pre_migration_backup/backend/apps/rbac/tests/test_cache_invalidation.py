import uuid
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.models import CustomUser
from apps.rbac.models import Role, Permission
from apps.rbac.utils import user_has_permission
from apps.rbac.views import RBACRoleDetailView
from django.core.cache import cache

class RBACCacheInvalidationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tenant_id = uuid.uuid4()
        
        # 1. Create an admin to perform the role updates
        self.admin = CustomUser.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant_id=self.tenant_id
        )
        
        # 2. Create a custom role for a recruiter
        self.role = Role.objects.create(
            name='custom_recruiter',
            display_name='Custom Recruiter',
            tenant_id=self.tenant_id,
            is_system=False
        )
        
        # 3. Create permissions
        self.perm1 = Permission.objects.create(
            code='test.perm1', 
            label='Perm 1', 
            module='test',
            resource='perm',
            action='1',
            is_active=True
        )
        self.perm2 = Permission.objects.create(
            code='test.perm2', 
            label='Perm 2', 
            module='test',
            resource='perm',
            action='2',
            is_active=True
        )
        
        # 4. Assign only perm1 initially
        self.role.permissions.add(self.perm1)
        
        # 5. Create a recruiter user with this role
        self.recruiter = CustomUser.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            role='custom_recruiter',
            tenant_id=self.tenant_id
        )
        
        # Clear cache before starting
        cache.clear()

    def test_role_update_invalidates_cache_repro(self):
        # 1. Populate cache for recruiter
        self.assertTrue(user_has_permission(self.recruiter, 'test.perm1'))
        self.assertFalse(user_has_permission(self.recruiter, 'test.perm2'))
        
        # 2. Update role permissions via view (Swap perm1 for perm2)
        view = RBACRoleDetailView.as_view()
        payload = {
            'permission_codes': ['test.perm2'] 
        }
        request = self.factory.put(f'/api/v1/rbac/roles/{self.role.id}/', payload, format='json')
        force_authenticate(request, user=self.admin)
        
        response = view(request, role_id=str(self.role.id))
        self.assertEqual(response.status_code, 200)
        
        # 3. Check recruiter permissions again
        # This SHOULD reflect the change immediately.
        # WITHOUT fix, this will fail because it's still using the old cached frozenset.
        self.assertFalse(user_has_permission(self.recruiter, 'test.perm1'), "Perm 1 should be gone after role update")
        self.assertTrue(user_has_permission(self.recruiter, 'test.perm2'), "Perm 2 should be present after role update")

    def test_role_deletion_invalidates_cache_repro(self):
        # 1. Populate cache for recruiter
        self.assertTrue(user_has_permission(self.recruiter, 'test.perm1'))
        
        # 2. Delete the role via view
        view = RBACRoleDetailView.as_view()
        request = self.factory.delete(f'/api/v1/rbac/roles/{self.role.id}/')
        force_authenticate(request, user=self.admin)
        
        response = view(request, role_id=str(self.role.id))
        self.assertEqual(response.status_code, 200)
        
        # 3. Check recruiter permissions again
        # Recruiter should now have NO permissions (because role is gone)
        # WITHOUT fix, this will fail because of stale cache.
        self.assertFalse(user_has_permission(self.recruiter, 'test.perm1'), "Perm 1 should be gone after role deletion")
