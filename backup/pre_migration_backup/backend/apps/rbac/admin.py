from django.contrib import admin
from apps.rbac.models import Permission, Role, RolePermission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'module', 'resource', 'action', 'is_active')
    list_filter = ('module', 'is_active')
    search_fields = ('code', 'description')
    ordering = ('module', 'resource', 'action')
    readonly_fields = ('id', 'created_at')


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    autocomplete_fields = ['permission']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_system', 'tenant_id', 'permission_count')
    list_filter = ('is_system',)
    search_fields = ('name', 'display_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [RolePermissionInline]

    def permission_count(self, obj):
        return obj.permissions.filter(is_active=True).count()
    permission_count.short_description = 'Permissions'


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'created_at')
    list_filter = ('role__name',)
    search_fields = ('role__name', 'permission__code')
    readonly_fields = ('id', 'created_at')
