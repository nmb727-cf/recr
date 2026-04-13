from django.urls import path
from apps.automation_observability import views

urlpatterns = [
    path('live/', views.LiveWorkflowMonitorView.as_view(), name='wf-obs-live'),
    path('failures/', views.FailureMonitorView.as_view(), name='wf-obs-failures'),
    path('latency/', views.LatencyMonitorView.as_view(), name='wf-obs-latency'),
    path('dependencies/', views.DependencyHealthView.as_view(), name='wf-obs-dependencies'),
    path('anomalies/', views.AnomalyListView.as_view(), name='wf-obs-anomalies'),
    path('alerts/', views.AlertListView.as_view(), name='wf-obs-alerts'),
]
