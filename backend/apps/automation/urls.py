from django.urls import path

from apps.automation import views

urlpatterns = [
    path('rules/', views.AutomationRuleListView.as_view(), name='automation-rule-list'),
    path('rules/<uuid:pk>/', views.AutomationRuleDetailView.as_view(), name='automation-rule-detail'),
    path('trigger/', views.AutomationTriggerView.as_view(), name='automation-trigger'),
    path('logs/', views.AutomationLogListView.as_view(), name='automation-log-list'),
]

