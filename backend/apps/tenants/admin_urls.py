from django.urls import path

from apps.tenants import admin_views


urlpatterns = [
    path('tenants/', admin_views.MasterAdminTenantListView.as_view(), name='master-admin-tenant-list'),
    path('tenants/<uuid:tenant_id>/', admin_views.MasterAdminTenantDetailView.as_view(), name='master-admin-tenant-detail'),
    path('tenants/<uuid:tenant_id>/verify/', admin_views.MasterAdminTenantVerifyView.as_view(), name='master-admin-tenant-verify'),
    path('tenants/<uuid:tenant_id>/suspend/', admin_views.MasterAdminTenantSuspendView.as_view(), name='master-admin-tenant-suspend'),
    path('tenants/<uuid:tenant_id>/reactivate/', admin_views.MasterAdminTenantReactivateView.as_view(), name='master-admin-tenant-reactivate'),
    path('tenants/<uuid:tenant_id>/deactivate/', admin_views.MasterAdminTenantDeactivateView.as_view(), name='master-admin-tenant-deactivate'),
    path('tenants/<uuid:tenant_id>/feature-flags/', admin_views.MasterAdminTenantFeatureFlagsView.as_view(), name='master-admin-tenant-feature-flags'),
    path('tenants/<uuid:tenant_id>/limits/', admin_views.MasterAdminTenantLimitsView.as_view(), name='master-admin-tenant-limits'),
    path('settings/', admin_views.MasterAdminPlatformSettingsView.as_view(), name='master-admin-platform-settings'),
    path('audit/', admin_views.MasterAdminAuditLogView.as_view(), name='master-admin-audit'),
]
