from django.urls import path
from apps.pipeline import views

urlpatterns = [
    # Applications
    path('pipeline/applications/', views.ApplicationListView.as_view(), name='application-list'),
    path('pipeline/applications/<uuid:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('pipeline/applications/<uuid:pk>/move-stage/', views.ApplicationMoveStageView.as_view(), name='application-move-stage'),
    path('pipeline/applications/<uuid:pk>/shortlist/', views.ApplicationShortlistView.as_view(), name='application-shortlist'),
    path('pipeline/applications/<uuid:pk>/reject/', views.ApplicationRejectView.as_view(), name='application-reject'),
    path('pipeline/applications/<uuid:pk>/withdraw/', views.ApplicationWithdrawView.as_view(), name='application-withdraw'),
    path('pipeline/applications/<uuid:pk>/make-offer/', views.ApplicationMakeOfferView.as_view(), name='application-make-offer'),

    # Pipeline view
    path('pipeline/<uuid:requisition_id>/', views.PipelineView.as_view(), name='pipeline-view'),
    path('pipeline/<uuid:requisition_id>/activity/', views.RequisitionActivityView.as_view(), name='requisition-activity'),
    path('pipeline/bulk-action/', views.BulkActionView.as_view(), name='pipeline-bulk-action'),

    # Deadlines
    path('pipeline/deadlines/', views.DeadlineListView.as_view(), name='deadline-list'),
    path('pipeline/deadlines/<uuid:pk>/complete/', views.DeadlineCompleteView.as_view(), name='deadline-complete'),
    path('pipeline/deadlines/overdue/', views.OverdueDeadlineView.as_view(), name='deadline-overdue'),
]
