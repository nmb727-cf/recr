from django.urls import path
from apps.rbac.views import (
    RBACDebugView,
    RBACRoleCatalogView,
    RBACRoleCloneTemplateView,
    RBACRoleDetailView,
)

urlpatterns = [
    path('debug/', RBACDebugView.as_view(), name='rbac-debug'),
    path('roles/', RBACRoleCatalogView.as_view(), name='rbac-role-catalog'),
    path('roles/<uuid:template_role_id>/clone-template/', RBACRoleCloneTemplateView.as_view(), name='rbac-role-clone-template'),
    path('roles/<uuid:role_id>/', RBACRoleDetailView.as_view(), name='rbac-role-detail'),
]
