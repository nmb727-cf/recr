from django.urls import path
from apps.pipeline import views

urlpatterns = [
    # Applications
    path('applications/', views.ApplicationListView.as_view(), name='application-list'),
    path('applications/<uuid:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/<uuid:pk>/move-stage/', views.ApplicationMoveStageView.as_view(), name='application-move-stage'),
    path('applications/<uuid:pk>/shortlist/', views.ApplicationShortlistView.as_view(), name='application-shortlist'),
    path('applications/<uuid:pk>/reject/', views.ApplicationRejectView.as_view(), name='application-reject'),
    path('applications/<uuid:pk>/withdraw/', views.ApplicationWithdrawView.as_view(), name='application-withdraw'),
    path('applications/<uuid:pk>/make-offer/', views.ApplicationMakeOfferView.as_view(), name='application-make-offer'),

    # Pipeline view
    path('pipeline/<uuid:requisition_id>/', views.PipelineView.as_view(), name='pipeline-view'),
    path('pipeline/bulk-action/', views.BulkActionView.as_view(), name='pipeline-bulk-action'),

    # Deadlines
    path('deadlines/', views.DeadlineListView.as_view(), name='deadline-list'),
    path('deadlines/<uuid:pk>/complete/', views.DeadlineCompleteView.as_view(), name='deadline-complete'),
    path('deadlines/overdue/', views.OverdueDeadlineView.as_view(), name='deadline-overdue'),
]
