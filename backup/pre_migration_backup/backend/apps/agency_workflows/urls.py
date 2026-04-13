from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import AgencyWorkflowViewSet
from .api import event_views
from .api import orchestration_views

router = DefaultRouter()
router.register(r'agency-workflow', AgencyWorkflowViewSet, basename='agency-workflow')
router.register(r'agency-workflow-events/registry', event_views.AgencyWorkflowEventRegistryViewSet, basename='agency-event-registry')
router.register(r'agency-workflow-events/subscriptions', event_views.AgencyWorkflowEventSubscriptionViewSet, basename='agency-event-subscriptions')
router.register(r'agency-workflow-events/logs', event_views.AgencyWorkflowEventLogViewSet, basename='agency-event-logs')
router.register(r'agency-workflow-events/test', event_views.AgencyWorkflowEventTestViewSet, basename='agency-event-test')

router.register(r'agency-workflow-orchestration/processes', orchestration_views.AgencyWorkflowOrchestrationViewSet, basename='agency-orchestration-processes')
router.register(r'agency-workflow-orchestration/approvals', orchestration_views.AgencyWorkflowApprovalViewSet, basename='agency-orchestration-approvals')
router.register(r'agency-workflow-orchestration/client-responses', orchestration_views.AgencyClientResponseViewSet, basename='agency-orchestration-client-responses')
router.register(r'agency-workflow-orchestration/offers', orchestration_views.AgencyOfferViewSet, basename='agency-orchestration-offers')
router.register(r'agency-workflow-orchestration/placements', orchestration_views.AgencyPlacementViewSet, basename='agency-orchestration-placements')
router.register(r'agency-workflow-orchestration/guarantees', orchestration_views.AgencyGuaranteeViewSet, basename='agency-orchestration-guarantees')

urlpatterns = [
    path('', include(router.urls)),
]
