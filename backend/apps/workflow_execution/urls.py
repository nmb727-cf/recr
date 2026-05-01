from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.workflow_execution.api import views

router = DefaultRouter()

# Execution instances
router.register(r'instances', views.WorkflowInstanceViewSet, basename='workflow-instances')

# Stage transitions (typed routing rules)
router.register(r'stage-transitions', views.WorkflowStageTransitionViewSet, basename='workflow-stage-transitions')

# Wait states (global read + resume)
router.register(r'wait-states', views.WorkflowWaitStateViewSet, basename='workflow-wait-states')

# Transition logs (structured audit)
router.register(r'transition-logs', views.WorkflowTransitionLogViewSet, basename='workflow-transition-logs')
router.register(r'failure-logs', views.WorkflowFailureLogViewSet, basename='workflow-failure-logs')

# Trigger registry (read-only)
router.register(r'triggers/registry', views.WorkflowTriggerRegistryViewSet, basename='workflow-trigger-registry')

# Trigger mappings (CRUD)
router.register(r'triggers/mappings', views.WorkflowTriggerMappingViewSet, basename='workflow-trigger-mappings')

# Event logs (read-only)
router.register(r'events/logs', views.WorkflowEventLogViewSet, basename='workflow-event-logs')

# Event debug traces (read-only)
router.register(r'events/traces', views.WorkflowEventDebugTraceViewSet, basename='workflow-event-traces')

# Cross-entity routing
router.register(r'entity-routes', views.WorkflowEntityRouteViewSet, basename='workflow-entity-routes')
router.register(r'actor-assignments', views.WorkflowActorAssignmentViewSet, basename='workflow-actor-assignments')
router.register(r'handoff-checkpoints', views.WorkflowHandoffCheckpointViewSet, basename='workflow-handoff-checkpoints')
router.register(r'routing-rules', views.WorkflowRoutingRuleViewSet, basename='workflow-routing-rules')
router.register(r'route-timeline', views.WorkflowRouteTimelineLogViewSet, basename='workflow-route-timeline')

urlpatterns = [
    path('', include(router.urls)),
    path('events/test-emit/', views.WorkflowTestEmitView.as_view(), name='workflow-test-emit'),
]
