from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.utils import timezone

from apps.core.responses import error_response, success_response

class SLAPolicyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        from apps.automation_sla.serializers import WorkflowSLAPolicySerializer
        return WorkflowSLAPolicySerializer

    def get_queryset(self):
        from apps.automation_sla.models import WorkflowSLAPolicy
        return WorkflowSLAPolicy.objects.filter(tenant_id=self.request.user.tenant_id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="SLA policies retrieved.")

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)


class SLAExecutionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        from apps.automation_sla.serializers import WorkflowSLAExecutionSerializer
        return WorkflowSLAExecutionSerializer

    def get_queryset(self):
        from apps.automation_sla.models import WorkflowSLAExecution
        return WorkflowSLAExecution.objects.filter(tenant_id=self.request.user.tenant_id).select_related('sla_policy')

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return success_response(data=serializer.data, message="SLA executions retrieved.")
        except Exception as e:
            return error_response(str(e), status_code=500)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        from apps.automation_sla.models import SLAExecutionStatus
        from apps.automation_sla.services.workflow_sla_engine import WorkflowSLAEngine
        
        execution = self.get_object()
        if execution.current_status in [SLAExecutionStatus.COMPLETED, SLAExecutionStatus.CANCELLED]:
            return error_response(f"Cannot complete SLA in {execution.current_status} status.")
        
        WorkflowSLAEngine.complete_sla(
            tenant_id=request.user.tenant_id,
            entity_type=execution.entity_type,
            entity_id=execution.entity_id,
            policy_name=execution.sla_policy.name
        )
        return success_response(message="SLA marked as completed.")

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        from apps.automation_sla.models import SLAExecutionStatus
        execution = self.get_object()
        execution.current_status = SLAExecutionStatus.CANCELLED
        execution.save(update_fields=['current_status', 'updated_at'])
        return success_response(message="SLA cancelled.")


class SLAReminderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.automation_sla.models import WorkflowSLAReminder
        from apps.automation_sla.serializers import WorkflowSLAReminderSerializer
        reminders = WorkflowSLAReminder.objects.filter(tenant_id=request.user.tenant_id).order_by('-scheduled_at')
        return success_response(data=WorkflowSLAReminderSerializer(reminders, many=True).data)


class SLAEscalationRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        from apps.automation_sla.serializers import WorkflowSLAEscalationRuleSerializer
        return WorkflowSLAEscalationRuleSerializer

    def get_queryset(self):
        from apps.automation_sla.models import WorkflowSLAEscalationRule
        return WorkflowSLAEscalationRule.objects.filter(tenant_id=self.request.user.tenant_id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Escalation rules retrieved.")

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)


class SLAAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from apps.automation_sla.models import WorkflowSLAExecution, SLAExecutionStatus
            
            tenant_id = request.user.tenant_id
            qs = WorkflowSLAExecution.objects.filter(tenant_id=tenant_id)
            
            total = qs.count()
            completed = qs.filter(current_status=SLAExecutionStatus.COMPLETED).count()
            breached = qs.filter(current_status__in=[SLAExecutionStatus.BREACHED, SLAExecutionStatus.ESCALATED]).count()
            
            # Completion Rate
            rate = (completed / total * 100) if total > 0 else 0
            
            # Avg Time to Completion
            completed_qs = qs.filter(current_status=SLAExecutionStatus.COMPLETED, completed_at__isnull=False)
            
            avg_duration = None
            if completed_qs.exists():
                duration_expr = ExpressionWrapper(F('completed_at') - F('started_at'), output_field=DurationField())
                avg_duration = completed_qs.annotate(duration=duration_expr).aggregate(Avg('duration'))['duration__avg']
            
            # Module Comparison
            module_stats = qs.values('sla_policy__module_scope').annotate(
                total=Count('id'),
                breached=Count('id', filter=Q(current_status__in=[SLAExecutionStatus.BREACHED, SLAExecutionStatus.ESCALATED]))
            )

            return success_response(data={
                'summary': {
                    'total_executions': total,
                    'completion_rate': round(rate, 2),
                    'breach_rate': round((breached / total * 100), 2) if total > 0 else 0,
                    'avg_completion_time_minutes': int(avg_duration.total_seconds() / 60) if avg_duration else 0
                },
                'module_comparison': list(module_stats)
            })
        except Exception as e:
            import traceback
            return error_response(str(e), errors={'traceback': traceback.format_exc()}, status_code=500)


class SLABreachInsightListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.automation_sla.models import WorkflowSLABreachInsight
        from apps.automation_sla.serializers import WorkflowSLABreachInsightSerializer
        insights = WorkflowSLABreachInsight.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')
        return success_response(data=WorkflowSLABreachInsightSerializer(insights, many=True).data)
    
    def post(self, request):
        from apps.automation_sla.services.workflow_sla_engine import WorkflowSLAEngine
        # Trigger insight generation manually
        count = WorkflowSLAEngine.generate_breach_insights(request.user.tenant_id)
        return success_response(message=f"Generated {count} new breach insights.")
