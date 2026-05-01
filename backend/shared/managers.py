from django.db import models

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class AllObjectsManager(models.Manager):
    pass


class TenantScopedQuerySet(models.QuerySet):
    def for_tenant(self, tenant_id):
        if not tenant_id:
            return self.none()
        return self.filter(tenant_id=tenant_id)

    def for_user(self, user, *, allow_platform_admin=False):
        from shared.tenant_access import is_platform_admin
        if allow_platform_admin and is_platform_admin(user):
            return self
        return self.for_tenant(getattr(user, 'tenant_id', None))


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        return TenantScopedQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant_id):
        return self.get_queryset().for_tenant(tenant_id)

    def for_user(self, user, *, allow_platform_admin=False):
        return self.get_queryset().for_user(user, allow_platform_admin=allow_platform_admin)
