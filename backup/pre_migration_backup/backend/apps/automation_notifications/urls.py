from django.urls import path

from apps.automation_notifications import views
from apps.workflow_execution.api.views import (
    WorkflowNotificationListView,
    WorkflowNotificationDetailView,
    WorkflowNotificationTestSendView,
    WorkflowNotificationRetryView,
)

urlpatterns = [
    path('', WorkflowNotificationListView.as_view(), name='workflow-notification-list'),
    path('test-send/', WorkflowNotificationTestSendView.as_view(), name='workflow-notification-test-send'),
    path('<uuid:pk>/', WorkflowNotificationDetailView.as_view(), name='workflow-notification-detail'),
    path('<uuid:pk>/retry/', WorkflowNotificationRetryView.as_view(), name='workflow-notification-retry'),

    # Notification rules
    path('rules/',           views.NotificationRuleListView.as_view(),   name='wf-notif-rule-list'),
    path('rules/<uuid:pk>/', views.NotificationRuleDetailView.as_view(), name='wf-notif-rule-detail'),

    # Delivery log
    path('deliveries/', views.DeliveryLogView.as_view(), name='wf-notif-deliveries'),

    # Retry a specific delivery
    path('retry/<uuid:delivery_id>/', views.RetryDeliveryView.as_view(), name='wf-notif-retry'),

    # Escalation log
    path('escalations/', views.EscalationLogView.as_view(), name='wf-notif-escalations'),

    # Channel health
    path('channel-health/', views.ChannelHealthView.as_view(), name='wf-notif-channel-health'),

    # User preferences
    path('preferences/', views.PreferencesView.as_view(), name='wf-notif-preferences'),

    # Insights
    path('insights/', views.InsightsView.as_view(), name='wf-notif-insights'),

    # Legacy test send
    path('legacy/test-send/', views.TestSendView.as_view(), name='wf-notif-test-send'),
]
