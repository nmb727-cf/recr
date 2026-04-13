from django.urls import path

from apps.automation_permissions import views

urlpatterns = [
    # Policy CRUD
    path('policies/',      views.PolicyListView.as_view(),   name='workflow-permission-policy-list'),
    path('policies/<uuid:pk>/', views.PolicyDetailView.as_view(), name='workflow-permission-policy-detail'),

    # Restricted actions
    path('restricted-actions/',           views.RestrictedActionListView.as_view(),   name='workflow-restricted-action-list'),
    path('restricted-actions/<uuid:pk>/', views.RestrictedActionDetailView.as_view(), name='workflow-restricted-action-detail'),

    # Audit log
    path('audit/', views.AuditLogListView.as_view(), name='workflow-access-audit'),

    # Role matrix
    path('matrix/', views.RoleMatrixView.as_view(), name='workflow-permission-matrix'),

    # Permission check
    path('check/', views.PermissionCheckView.as_view(), name='workflow-permission-check'),
]
