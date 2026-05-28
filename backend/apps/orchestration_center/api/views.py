from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Q, F, ExpressionWrapper, fields
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response
from apps.orchestration_center.api.permissions import require_hub_permission
from apps.orchestration_center.api.serializers import (
    AIExecutionRequestSerializer,
    AIModelSerializer,
    AIProviderSerializer,
    AISuggestionApproveSerializer,
    AISuggestionApplySerializer,
    AISuggestionConvertSerializer,
    AISuggestionCreateSerializer,
    AISuggestionDismissSerializer,
    AISuggestionRejectSerializer,
    AISuggestionReviewSerializer,
    AISuggestionSerializer,
    ApprovalDecisionSerializer,
    ApprovalQueueItemSerializer,
    AutomationExecutionRunSerializer,
    AutomationIntelligencePolicySerializer,
    AutomationTemplateSerializer,
    AutomationRuleSerializer,
    AutomationRuleActionSerializer,
    AutomationSimulationSerializer,
    AutomationToggleSerializer,
    DeadLetterItemSerializer,
    ExecutionFailureSerializer,
    FailureResolveRequestSerializer,
    IntelligenceAuditLogSerializer,
    IntelligenceConnectorSerializer,
    PromptApproveRequestSerializer,
    PromptTemplateCreateSerializer,
    PromptTemplateSerializer,
    PromptTemplateUpdateSerializer,
    PromptTestRequestSerializer,
    PromptTestRunSerializer,
    PromptVersionCreateSerializer,
    PromptVersionSerializer,
    TenantIntelligenceSettingsSerializer,
    WorkflowSerializer,
    WorkflowVersionSerializer,
    WorkflowApprovalSerializer,
    WorkflowSafetyRuleSerializer,
    WorkflowRollbackLogSerializer,
    WorkflowAuditLogSerializer,
    WorkflowExecutionSerializer,
    WorkflowTemplateSerializer,
    AIGovernanceApprovalSerializer,
    AutomationInsightSerializer,
    AutomationRecommendationSerializer,
    WorkflowEventDefinitionSerializer,
    WorkflowEventSubscriptionSerializer,
    WorkflowEventLogSerializer,
    WorkflowEventDebugTraceSerializer,
)
from apps.orchestration_center.constants.execution_statuses import (
    AIExecutionStatus,
    ApprovalStatus,
    AutomationExecutionStatus,
)
from apps.orchestration_center.models import (
    AIExecutionRequest,
    AIModel,
    AIProvider,
    AISuggestion,
    ApprovalQueueItem,
    AutomationExecutionRun,
    AutomationIntelligencePolicy,
    AutomationTemplate,
    AutomationRule,
    DeadLetterItem,
    ExecutionFailure,
    IntelligenceConnector,
    PromptTemplate,
    PromptVersion,
    TenantIntelligenceSettings,
    IntelligenceAuditLog,
    AutomationLearningSignal,
    AIGovernanceRule,
    AIGovernanceApproval,
    Workflow,
    WorkflowVersion,
    WorkflowApproval,
    WorkflowSafetyRule,
    WorkflowRollbackLog,
    WorkflowAuditLog,
    WorkflowExecution,
    WorkflowAnalyticsSnapshot,
    WorkflowActionMetric,
    WorkflowTriggerMetric,
    WorkflowImpactMetric,
    WorkflowFailureInsight,
    AutomationInsight,
    AutomationRecommendation,
)
from apps.orchestration_center.selectors.overview import get_overview_snapshot
from apps.orchestration_center.services.approval_service import ApprovalService
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.automation_rule_service import AutomationRuleService
from apps.orchestration_center.services.failure_service import FailureService
from apps.orchestration_center.services.prompt_registry_service import PromptRegistryService
from apps.orchestration_center.services.tenant_settings_service import TenantSettingsService
from apps.orchestration_center.services.suggestion_service import SuggestionService
from apps.orchestration_center.services.workflow_governance import WorkflowGovernanceService


def _tenant_queryset(queryset, tenant_id):
    if hasattr(queryset.model, 'tenant_id'):
        return queryset.filter(tenant_id=tenant_id)
    return queryset


def _platform_or_tenant_queryset(queryset, tenant_id):
    if hasattr(queryset.model, 'tenant_id'):
        return queryset.filter(tenant_id__in=[tenant_id, None])
    return queryset


def _effective_tenant_id(request):
    user = request.user
    if getattr(user, 'role', '') == 'super_admin':
        requested = request.query_params.get('tenant_id') or request.data.get('tenant_id')
        if requested:
            return requested
    return getattr(user, 'tenant_id', None)


def _bad_request(exc):
    return error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)


def _audit_mutation(*, request, action_type, target_type, target_id, before_state=None, after_state=None, metadata=None):
    AuditService.log(
        tenant_id=request.user.tenant_id,
        actor_id=request.user.id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        before_state_json=before_state or {},
        after_state_json=after_state or {},
        metadata_json=metadata or {},
    )


SUGGESTION_ACTION_ROLE_DEFAULTS = {
    'approve': {'super_admin', 'tenant_admin', 'hr_manager'},
    'reject': {'super_admin', 'tenant_admin', 'hr_manager'},
    'dismiss': {'super_admin', 'tenant_admin', 'hr_manager', 'hiring_manager', 'recruiter'},
    'apply': {'super_admin', 'tenant_admin', 'hr_manager', 'hiring_manager'},
}


def _has_suggestion_action_permission(*, request, action):
    settings_obj = TenantIntelligenceSettings.objects.filter(tenant_id=request.user.tenant_id).first()
    configured_roles = None
    if settings_obj and isinstance(settings_obj.visibility_permissions_json, dict):
        configured_roles = settings_obj.visibility_permissions_json.get(f'suggestion_{action}_roles')
    allowed_roles = {
        str(role)
        for role in (
            configured_roles
            if isinstance(configured_roles, list) and configured_roles
            else SUGGESTION_ACTION_ROLE_DEFAULTS[action]
        )
    }
    return getattr(request.user, 'role', None) in allowed_roles


class OverviewView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('overview.view')]

    def get(self, request):
        return success_response(
            data=get_overview_snapshot(request.user.tenant_id),
            message='Overview retrieved.',
        )


class ProviderListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('providers.view')]

    def get(self, request):
        data = AIProviderSerializer(
            _platform_or_tenant_queryset(AIProvider.objects.all(), request.user.tenant_id),
            many=True,
        ).data
        return success_response(data=data, message='Providers retrieved.')


class ModelListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('providers.view')]

    def get(self, request):
        data = AIModelSerializer(
            _platform_or_tenant_queryset(AIModel.objects.select_related('provider').all(), request.user.tenant_id),
            many=True,
        ).data
        return success_response(data=data, message='Models retrieved.')


class ProviderDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('providers.manage')]

    def put(self, request, pk):
        try:
            provider = _platform_or_tenant_queryset(AIProvider.objects.all(), request.user.tenant_id).get(pk=pk)
        except AIProvider.DoesNotExist:
            return error_response('Provider not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = AIProviderSerializer(provider).data
        serializer = AIProviderSerializer(provider, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        provider = serializer.save()
        _audit_mutation(
            request=request,
            action_type='provider.updated',
            target_type='provider',
            target_id=provider.id,
            before_state=before_state,
            after_state=AIProviderSerializer(provider).data,
        )
        return success_response(data=AIProviderSerializer(provider).data, message='Provider updated.')


class ModelDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('providers.manage')]

    def put(self, request, pk):
        try:
            model = _platform_or_tenant_queryset(AIModel.objects.all(), request.user.tenant_id).get(pk=pk)
        except AIModel.DoesNotExist:
            return error_response('Model not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = AIModelSerializer(model).data
        serializer = AIModelSerializer(model, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        model = serializer.save()
        _audit_mutation(
            request=request,
            action_type='model.updated',
            target_type='model',
            target_id=model.id,
            before_state=before_state,
            after_state=AIModelSerializer(model).data,
        )
        return success_response(data=AIModelSerializer(model).data, message='Model updated.')


class PromptListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('prompts.view')]

    def get(self, request):
        queryset = _platform_or_tenant_queryset(
            PromptTemplate.objects.prefetch_related('versions', 'scopes').all(),
            request.user.tenant_id,
        )
        return success_response(data=PromptTemplateSerializer(queryset, many=True).data, message='Prompts retrieved.')

    def post(self, request):
        self.check_permissions(request)
        if not require_hub_permission('prompts.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        serializer = PromptTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prompt = PromptRegistryService.create_template(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            template_data=serializer.validated_data,
        )
        _audit_mutation(
            request=request,
            action_type='prompt.created',
            target_type='prompt_template',
            target_id=prompt.id,
            after_state=PromptTemplateSerializer(prompt).data,
        )
        return success_response(
            data=PromptTemplateSerializer(prompt).data,
            message='Prompt created.',
            status_code=status.HTTP_201_CREATED,
        )


class PromptDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('prompts.view')]

    def get_object(self, request, pk):
        return _platform_or_tenant_queryset(
            PromptTemplate.objects.prefetch_related('versions', 'scopes').all(),
            request.user.tenant_id,
        ).get(pk=pk)

    def get(self, request, pk):
        try:
            prompt = self.get_object(request, pk)
        except PromptTemplate.DoesNotExist:
            return error_response('Prompt not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=PromptTemplateSerializer(prompt).data, message='Prompt retrieved.')

    def put(self, request, pk):
        if not require_hub_permission('prompts.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            prompt = self.get_object(request, pk)
        except PromptTemplate.DoesNotExist:
            return error_response('Prompt not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = PromptTemplateSerializer(prompt).data
        serializer = PromptTemplateUpdateSerializer(prompt, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        prompt = PromptRegistryService.update_template(template=prompt, template_data=serializer.validated_data)
        _audit_mutation(
            request=request,
            action_type='prompt.updated',
            target_type='prompt_template',
            target_id=prompt.id,
            before_state=before_state,
            after_state=PromptTemplateSerializer(prompt).data,
        )
        return success_response(data=PromptTemplateSerializer(prompt).data, message='Prompt updated.')


class PromptVersionCreateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('prompts.manage')]

    def post(self, request, pk):
        try:
            prompt = _platform_or_tenant_queryset(PromptTemplate.objects.all(), request.user.tenant_id).get(pk=pk)
        except PromptTemplate.DoesNotExist:
            return error_response('Prompt not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = PromptVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = PromptRegistryService.create_version(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt_template=prompt,
            version_data=serializer.validated_data,
        )
        _audit_mutation(
            request=request,
            action_type='prompt.version.created',
            target_type='prompt_version',
            target_id=version.id,
            after_state=PromptVersionSerializer(version).data,
            metadata={'prompt_template_id': str(prompt.id)},
        )
        return success_response(
            data=PromptVersionSerializer(version).data,
            message='Prompt version created.',
            status_code=status.HTTP_201_CREATED,
        )


class PromptApproveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('prompts.approve')]

    def post(self, request, pk):
        payload = PromptApproveRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            prompt = _platform_or_tenant_queryset(PromptTemplate.objects.all(), request.user.tenant_id).get(pk=pk)
            version = PromptVersion.objects.get(pk=payload.validated_data['version_id'], prompt_template=prompt)
        except (PromptTemplate.DoesNotExist, PromptVersion.DoesNotExist):
            return error_response('Prompt or version not found.', status_code=status.HTTP_404_NOT_FOUND)
        try:
            before_state = PromptVersionSerializer(version).data
            version = PromptRegistryService.approve_version(
                version=version,
                approver_id=request.user.id,
                activate=payload.validated_data['activate'],
            )
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='prompt.approved',
            target_type='prompt_version',
            target_id=version.id,
            before_state=before_state,
            after_state=PromptVersionSerializer(version).data,
            metadata={'activate': payload.validated_data['activate']},
        )
        return success_response(data=PromptVersionSerializer(version).data, message='Prompt version approved.')


class PromptArchiveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('prompts.manage')]

    def post(self, request, pk):
        try:
            prompt = _platform_or_tenant_queryset(PromptTemplate.objects.all(), request.user.tenant_id).get(pk=pk)
        except PromptTemplate.DoesNotExist:
            return error_response('Prompt not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = PromptTemplateSerializer(prompt).data
        try:
            prompt = PromptRegistryService.archive_template(template=prompt)
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='prompt.archived',
            target_type='prompt_template',
            target_id=prompt.id,
            before_state=before_state,
            after_state=PromptTemplateSerializer(prompt).data,
        )
        return success_response(data=PromptTemplateSerializer(prompt).data, message='Prompt archived.')


class PromptTestView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('prompts.view')]

    def post(self, request, pk):
        payload = PromptTestRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            prompt = _platform_or_tenant_queryset(PromptTemplate.objects.all(), request.user.tenant_id).get(pk=pk)
            version = PromptVersion.objects.get(pk=payload.validated_data['version_id'], prompt_template=prompt)
        except (PromptTemplate.DoesNotExist, PromptVersion.DoesNotExist):
            return error_response('Prompt or version not found.', status_code=status.HTTP_404_NOT_FOUND)
        test_run = PromptRegistryService.create_test_run(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            prompt_version=version,
            test_input_json=payload.validated_data.get('test_input_json', {}),
        )
        _audit_mutation(
            request=request,
            action_type='prompt.test.queued',
            target_type='prompt_test_run',
            target_id=test_run.id,
            after_state=PromptTestRunSerializer(test_run).data,
            metadata={'prompt_version_id': str(version.id)},
        )
        return success_response(
            data=PromptTestRunSerializer(test_run).data,
            message='Prompt test queued.',
            status_code=status.HTTP_201_CREATED,
        )


class AutomationListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automations.view')]

    def get(self, request):
        queryset = _platform_or_tenant_queryset(
            AutomationRule.objects.prefetch_related('conditions', 'actions', 'scopes').all(),
            request.user.tenant_id,
        )
        return success_response(data=AutomationRuleSerializer(queryset, many=True).data, message='Automation rules retrieved.')

    def post(self, request):
        if not require_hub_permission('automations.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        serializer = AutomationRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = AutomationRuleService.create_rule(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            rule_data=serializer.validated_data,
        )
        _audit_mutation(
            request=request,
            action_type='automation_rule.created',
            target_type='automation_rule',
            target_id=rule.id,
            after_state=AutomationRuleSerializer(rule).data,
        )
        return success_response(
            data=AutomationRuleSerializer(rule).data,
            message='Automation rule created.',
            status_code=status.HTTP_201_CREATED,
        )


class AutomationDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automations.view')]

    def get_object(self, request, pk):
        return _platform_or_tenant_queryset(
            AutomationRule.objects.prefetch_related('conditions', 'actions', 'scopes').all(),
            request.user.tenant_id,
        ).get(pk=pk)

    def get(self, request, pk):
        try:
            rule = self.get_object(request, pk)
        except AutomationRule.DoesNotExist:
            return error_response('Automation rule not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=AutomationRuleSerializer(rule).data, message='Automation rule retrieved.')

    def put(self, request, pk):
        if not require_hub_permission('automations.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            rule = self.get_object(request, pk)
        except AutomationRule.DoesNotExist:
            return error_response('Automation rule not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = AutomationRuleSerializer(rule).data
        serializer = AutomationRuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            rule = AutomationRuleService.update_rule(rule=rule, rule_data=serializer.validated_data)
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='automation_rule.updated',
            target_type='automation_rule',
            target_id=rule.id,
            before_state=before_state,
            after_state=AutomationRuleSerializer(rule).data,
        )
        return success_response(data=AutomationRuleSerializer(rule).data, message='Automation rule updated.')


class AutomationToggleView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automations.manage')]

    def post(self, request, pk):
        try:
            rule = _platform_or_tenant_queryset(
                AutomationRule.objects.prefetch_related('actions').all(),
                request.user.tenant_id,
            ).get(pk=pk)
        except AutomationRule.DoesNotExist:
            return error_response('Automation rule not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AutomationToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        before_state = AutomationRuleSerializer(rule).data
        try:
            rule = AutomationRuleService.toggle_rule(rule=rule, new_status=serializer.validated_data['status'])
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='automation_rule.toggled',
            target_type='automation_rule',
            target_id=rule.id,
            before_state=before_state,
            after_state=AutomationRuleSerializer(rule).data,
        )
        return success_response(data=AutomationRuleSerializer(rule).data, message='Automation rule updated.')


class AutomationSimulateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automations.manage')]

    def post(self, request, pk):
        try:
            rule = _platform_or_tenant_queryset(
                AutomationRule.objects.prefetch_related('conditions', 'actions', 'scopes').all(),
                request.user.tenant_id,
            ).get(pk=pk)
        except AutomationRule.DoesNotExist:
            return error_response('Automation rule not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AutomationSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AutomationRuleService.simulate_rule(
            rule=rule,
            event_payload_json=serializer.validated_data.get('event_payload_json', {}),
        )
        return success_response(data=result, message='Automation simulation completed.')


class AutomationRunsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automations.view')]

    def get(self, request, pk):
        runs = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id, rule_id=pk)
        return success_response(data=AutomationExecutionRunSerializer(runs, many=True).data, message='Automation runs retrieved.')


class AIExecutionListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('executions.view')]

    def get(self, request):
        queryset = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id)
        for field in ['status', 'module_scope', 'use_case_key', 'source_entity_type', 'source_entity_id']:
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        return success_response(data=AIExecutionRequestSerializer(queryset, many=True).data, message='AI executions retrieved.')


class SuggestionListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.view')]

    def get(self, request):
        queryset = AISuggestion.objects.filter(tenant_id=request.user.tenant_id)
        for field in ['category', 'status', 'source_module', 'source_entity_type', 'source_entity_id', 'owner_module', 'confidence_band']:
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        return success_response(data=AISuggestionSerializer(queryset, many=True).data, message='Suggestions retrieved.')

    def post(self, request):
        if not require_hub_permission('suggestions.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        serializer = AISuggestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        ai_request_id = payload.pop('ai_request_id', None)
        try:
            if ai_request_id:
                ai_request = AIExecutionRequest.objects.get(pk=ai_request_id, tenant_id=request.user.tenant_id)
                suggestion, created = SuggestionService.create_from_ai_execution(
                    tenant_id=request.user.tenant_id,
                    created_by=request.user.id,
                    ai_request=ai_request,
                    suggestion_data=payload,
                )
            else:
                suggestion, created = SuggestionService.create_suggestion(
                    tenant_id=request.user.tenant_id,
                    created_by=request.user.id,
                    suggestion_data=payload,
                )
        except AIExecutionRequest.DoesNotExist:
            return error_response('AI execution request not found.', status_code=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return _bad_request(exc)
        message = 'Suggestion created.' if created else 'Suggestion already exists.'
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return success_response(data=AISuggestionSerializer(suggestion).data, message=message, status_code=status_code)


class SuggestionDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.view')]

    def get(self, request, pk):
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=AISuggestionSerializer(item).data, message='Suggestion retrieved.')


class SuggestionReviewView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.manage')]

    def post(self, request, pk):
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AISuggestionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = SuggestionService.review_suggestion(
                suggestion=item,
                user_id=request.user.id,
                status_value=serializer.validated_data['status'],
                comment=serializer.validated_data.get('comment', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)
        return success_response(data=AISuggestionSerializer(item).data, message='Suggestion reviewed.')


class SuggestionApproveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.manage')]

    def post(self, request, pk):
        if not _has_suggestion_action_permission(request=request, action='approve'):
            return error_response('You do not have permission to approve suggestions.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AISuggestionApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = SuggestionService.approve_suggestion(
                suggestion=item,
                user_id=request.user.id,
                comment=serializer.validated_data.get('comment', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)
        
        # Record Learning Signal
        try:
            from apps.orchestration_center.services.automation_learning import AutomationLearningService
            AutomationLearningService.record_outcome(
                tenant_id=request.user.tenant_id,
                outcome_type='approved',
                suggestion_id=item.id,
                confidence_score=float(item.confidence_score),
                user_action='approve'
            )
        except Exception:
            pass # Learning signal should not block main flow

        return success_response(data=AISuggestionSerializer(item).data, message='Suggestion approved.')


class SuggestionRejectView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.manage')]

    def post(self, request, pk):
        if not _has_suggestion_action_permission(request=request, action='reject'):
            return error_response('You do not have permission to reject suggestions.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AISuggestionRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = SuggestionService.reject_suggestion(
                suggestion=item,
                user_id=request.user.id,
                comment=serializer.validated_data.get('comment', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)

        # Record Learning Signal
        try:
            from apps.orchestration_center.services.automation_learning import AutomationLearningService
            AutomationLearningService.record_outcome(
                tenant_id=request.user.tenant_id,
                outcome_type='rejected',
                suggestion_id=item.id,
                confidence_score=float(item.confidence_score),
                user_action='reject'
            )
        except Exception:
            pass # Learning signal should not block main flow

        return success_response(data=AISuggestionSerializer(item).data, message='Suggestion rejected.')


class SuggestionDismissView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.manage')]

    def post(self, request, pk):
        if not _has_suggestion_action_permission(request=request, action='dismiss'):
            return error_response('You do not have permission to dismiss suggestions.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AISuggestionDismissSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = SuggestionService.dismiss_suggestion(
                suggestion=item,
                user_id=request.user.id,
                comment=serializer.validated_data.get('comment', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)
        return success_response(data=AISuggestionSerializer(item).data, message='Suggestion dismissed.')


class SuggestionApplyView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.manage')]

    def post(self, request, pk):
        if not _has_suggestion_action_permission(request=request, action='apply'):
            return error_response('You do not have permission to apply suggestions.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AISuggestionApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            conversion, applied = SuggestionService.apply_suggestion(
                suggestion=item,
                user_id=request.user.id,
                comment=serializer.validated_data.get('comment', ''),
                override_payload_json=serializer.validated_data.get('override_payload_json'),
                idempotency_key=serializer.validated_data.get('idempotency_key', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)
        refreshed = AISuggestion.objects.get(pk=item.pk, tenant_id=request.user.tenant_id)
        return success_response(
            data={
                'suggestion': AISuggestionSerializer(refreshed).data,
                'conversion': {
                    'id': str(conversion.id),
                    'status': conversion.status,
                    'conversion_type': conversion.conversion_type,
                    'error_category': conversion.error_category,
                    'error_message': conversion.error_message,
                    'result_payload_json': conversion.result_payload_json,
                    'retry_safe': conversion.retry_safe,
                },
                'applied': applied,
            },
            message='Suggestion applied.' if applied else 'Suggestion apply failed and was logged.',
        )


class SuggestionConvertView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('suggestions.manage')]

    def post(self, request, pk):
        try:
            item = AISuggestion.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AISuggestion.DoesNotExist:
            return error_response('Suggestion not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = AISuggestionConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            conversion, created = SuggestionService.convert_suggestion(
                suggestion=item,
                user_id=request.user.id,
                conversion_type=serializer.validated_data['conversion_type'],
                override_payload_json=serializer.validated_data.get('override_payload_json'),
                idempotency_key=serializer.validated_data.get('idempotency_key', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)
        message = 'Suggestion converted.' if created else 'Suggestion conversion already exists.'
        return success_response(
            data={
                'suggestion': AISuggestionSerializer(item.__class__.objects.get(pk=item.pk)).data,
                'conversion': {
                    'id': str(conversion.id),
                    'status': conversion.status,
                    'conversion_type': conversion.conversion_type,
                    'result_payload_json': conversion.result_payload_json,
                    'approval_item_id': str(conversion.approval_item_id) if conversion.approval_item_id else None,
                },
                'deduplicated': not created,
            },
            message=message,
        )


class AutomationExecutionListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('executions.view')]

    def get(self, request):
        queryset = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id)
        for field in ['status', 'source_event', 'source_entity_type', 'source_entity_id']:
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        return success_response(data=AutomationExecutionRunSerializer(queryset, many=True).data, message='Automation executions retrieved.')


class AutomationIntelligencePolicyListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automation_intelligence.view')]

    def get(self, request):
        queryset = AutomationIntelligencePolicy.objects.filter(tenant_id=request.user.tenant_id)
        for field in ['suggestion_type', 'module_scope', 'is_enabled', 'auto_approve', 'auto_apply']:
            value = request.query_params.get(field)
            if value not in (None, ''):
                if field in {'is_enabled', 'auto_approve', 'auto_apply'}:
                    queryset = queryset.filter(**{field: str(value).lower() == 'true'})
                else:
                    queryset = queryset.filter(**{field: value})
        return success_response(
            data=AutomationIntelligencePolicySerializer(queryset, many=True).data,
            message='Automation intelligence policies retrieved.',
        )

    def post(self, request):
        if not require_hub_permission('automation_intelligence.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        serializer = AutomationIntelligencePolicySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        policy = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        _audit_mutation(
            request=request,
            action_type='automation_intelligence_policy.created',
            target_type='automation_intelligence_policy',
            target_id=policy.id,
            after_state=AutomationIntelligencePolicySerializer(policy).data,
        )
        return success_response(
            data=AutomationIntelligencePolicySerializer(policy).data,
            message='Automation intelligence policy created.',
            status_code=status.HTTP_201_CREATED,
        )


class AutomationIntelligencePolicyDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automation_intelligence.view')]

    def get_object(self, request, pk):
        return AutomationIntelligencePolicy.objects.get(pk=pk, tenant_id=request.user.tenant_id)

    def get(self, request, pk):
        try:
            policy = self.get_object(request, pk)
        except AutomationIntelligencePolicy.DoesNotExist:
            return error_response('Automation intelligence policy not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data=AutomationIntelligencePolicySerializer(policy).data,
            message='Automation intelligence policy retrieved.',
        )

    def put(self, request, pk):
        if not require_hub_permission('automation_intelligence.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            policy = self.get_object(request, pk)
        except AutomationIntelligencePolicy.DoesNotExist:
            return error_response('Automation intelligence policy not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = AutomationIntelligencePolicySerializer(policy).data
        serializer = AutomationIntelligencePolicySerializer(policy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        policy = serializer.save()
        _audit_mutation(
            request=request,
            action_type='automation_intelligence_policy.updated',
            target_type='automation_intelligence_policy',
            target_id=policy.id,
            before_state=before_state,
            after_state=AutomationIntelligencePolicySerializer(policy).data,
        )
        return success_response(
            data=AutomationIntelligencePolicySerializer(policy).data,
            message='Automation intelligence policy updated.',
        )

    def delete(self, request, pk):
        if not require_hub_permission('automation_intelligence.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        try:
            policy = self.get_object(request, pk)
        except AutomationIntelligencePolicy.DoesNotExist:
            return error_response('Automation intelligence policy not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = AutomationIntelligencePolicySerializer(policy).data
        policy.delete()
        _audit_mutation(
            request=request,
            action_type='automation_intelligence_policy.deleted',
            target_type='automation_intelligence_policy',
            target_id=pk,
            before_state=before_state,
            after_state={},
        )
        return success_response(data=None, message='Automation intelligence policy deleted.')


# ---------------------------------------------------------------------------
# Automation Template Library
# ---------------------------------------------------------------------------

class AutomationTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automation_templates.view')]

    def get(self, request):
        # Return builtin (platform-wide) templates plus this tenant's custom ones.
        from django.db.models import Q
        queryset = AutomationTemplate.objects.filter(
            Q(is_builtin=True, tenant_id__isnull=True) | Q(tenant_id=request.user.tenant_id)
        )
        suggestion_type = request.query_params.get('suggestion_type')
        if suggestion_type:
            queryset = queryset.filter(suggestion_type=suggestion_type)
        automation_level = request.query_params.get('automation_level')
        if automation_level:
            queryset = queryset.filter(automation_level=automation_level)
        return success_response(
            data=AutomationTemplateSerializer(queryset, many=True).data,
            message='Automation templates retrieved.',
        )

    def post(self, request):
        if not require_hub_permission('automation_templates.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        serializer = AutomationTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
            is_builtin=False,
        )
        return success_response(
            data=AutomationTemplateSerializer(template).data,
            message='Automation template created.',
            status_code=status.HTTP_201_CREATED,
        )


class AutomationTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('automation_templates.view')]

    def _get_object(self, request, pk):
        from django.db.models import Q
        return AutomationTemplate.objects.filter(
            Q(is_builtin=True, tenant_id__isnull=True) | Q(tenant_id=request.user.tenant_id),
            pk=pk,
        ).first()

    def get(self, request, pk):
        template = self._get_object(request, pk)
        if not template:
            return error_response('Automation template not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data=AutomationTemplateSerializer(template).data,
            message='Automation template retrieved.',
        )

    def put(self, request, pk):
        if not require_hub_permission('automation_templates.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        template = self._get_object(request, pk)
        if not template:
            return error_response('Automation template not found.', status_code=status.HTTP_404_NOT_FOUND)
        if template.is_builtin:
            return error_response('Built-in templates cannot be modified.', status_code=status.HTTP_403_FORBIDDEN)
        serializer = AutomationTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()
        return success_response(
            data=AutomationTemplateSerializer(template).data,
            message='Automation template updated.',
        )

    def delete(self, request, pk):
        if not require_hub_permission('automation_templates.manage')().has_permission(request, self):
            return error_response('Permission denied.', status_code=status.HTTP_403_FORBIDDEN)
        template = self._get_object(request, pk)
        if not template:
            return error_response('Automation template not found.', status_code=status.HTTP_404_NOT_FOUND)
        if template.is_builtin:
            return error_response('Built-in templates cannot be deleted.', status_code=status.HTTP_403_FORBIDDEN)
        template.soft_delete()
        return success_response(data=None, message='Automation template deleted.')


class AutomationTemplateApplyView(APIView):
    """Instantiate an AutomationIntelligencePolicy from a template."""
    permission_classes = [IsAuthenticated, require_hub_permission('automation_intelligence.manage')]

    def post(self, request, pk):
        from django.db.models import Q
        template = AutomationTemplate.objects.filter(
            Q(is_builtin=True, tenant_id__isnull=True) | Q(tenant_id=request.user.tenant_id),
            pk=pk,
        ).first()
        if not template:
            return error_response('Automation template not found.', status_code=status.HTTP_404_NOT_FOUND)

        level = template.automation_level
        auto_approve = level in ('auto_approve', 'auto_apply')
        auto_apply = level == 'auto_apply'
        approval_required = not auto_apply

        policy_data = {
            'suggestion_type': template.suggestion_type,
            'module_scope': template.module_scope,
            'confidence_threshold': template.confidence_threshold,
            'auto_approve': auto_approve,
            'auto_apply': auto_apply,
            'approval_required': approval_required,
            'is_enabled': True,
            'notes': f'Created from template: {template.name}',
        }
        serializer = AutomationIntelligencePolicySerializer(data=policy_data)
        serializer.is_valid(raise_exception=True)
        policy = serializer.save(
            tenant_id=request.user.tenant_id,
            created_by=request.user.id,
        )
        _audit_mutation(
            request=request,
            action_type='automation_intelligence_policy.created_from_template',
            target_type='automation_intelligence_policy',
            target_id=policy.id,
            after_state={**AutomationIntelligencePolicySerializer(policy).data, 'source_template_id': str(pk)},
        )
        return success_response(
            data=AutomationIntelligencePolicySerializer(policy).data,
            message='Policy created from template.',
            status_code=status.HTTP_201_CREATED,
        )


class UnifiedExecutionDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('executions.view')]

    def get(self, request, execution_id):
        ai_item = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, pk=execution_id).first()
        if ai_item:
            return success_response(
                data={'execution_type': 'ai', 'payload': AIExecutionRequestSerializer(ai_item).data},
                message='Execution retrieved.',
            )
        automation_item = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id, pk=execution_id).first()
        if automation_item:
            return success_response(
                data={'execution_type': 'automation', 'payload': AutomationExecutionRunSerializer(automation_item).data},
                message='Execution retrieved.',
            )
        return error_response('Execution not found.', status_code=status.HTTP_404_NOT_FOUND)


class ExecutionRetryView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('executions.manage')]

    def post(self, request, execution_id):
        ai_item = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, pk=execution_id).first()
        if ai_item:
            if ai_item.status == AIExecutionStatus.CANCELLED:
                return error_response('Cancelled executions cannot be retried.', status_code=status.HTTP_400_BAD_REQUEST)
            before_state = AIExecutionRequestSerializer(ai_item).data
            ai_item.retry_count += 1
            ai_item.status = AIExecutionStatus.QUEUED
            ai_item.failure_reason = ''
            ai_item.failure_category = ''
            ai_item.save(update_fields=['retry_count', 'status', 'failure_reason', 'failure_category', 'updated_at'])
            _audit_mutation(
                request=request,
                action_type='ai_execution.retried',
                target_type='ai_execution_request',
                target_id=ai_item.id,
                before_state=before_state,
                after_state=AIExecutionRequestSerializer(ai_item).data,
            )
            return success_response(data=AIExecutionRequestSerializer(ai_item).data, message='AI execution queued for retry.')

        automation_item = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id, pk=execution_id).first()
        if automation_item:
            if automation_item.status == AutomationExecutionStatus.CANCELLED:
                return error_response('Cancelled executions cannot be retried.', status_code=status.HTTP_400_BAD_REQUEST)
            before_state = AutomationExecutionRunSerializer(automation_item).data
            automation_item.retry_count += 1
            automation_item.status = AutomationExecutionStatus.QUEUED
            automation_item.failure_reason = ''
            automation_item.failure_category = ''
            automation_item.save(update_fields=['retry_count', 'status', 'failure_reason', 'failure_category', 'updated_at'])
            _audit_mutation(
                request=request,
                action_type='automation_execution.retried',
                target_type='automation_execution_run',
                target_id=automation_item.id,
                before_state=before_state,
                after_state=AutomationExecutionRunSerializer(automation_item).data,
            )
            return success_response(data=AutomationExecutionRunSerializer(automation_item).data, message='Automation execution queued for retry.')
        return error_response('Execution not found.', status_code=status.HTTP_404_NOT_FOUND)


class ExecutionCancelView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('executions.manage')]

    def post(self, request, execution_id):
        ai_item = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, pk=execution_id).first()
        if ai_item:
            if ai_item.status in {AIExecutionStatus.COMPLETED, AIExecutionStatus.FAILED, AIExecutionStatus.CANCELLED}:
                return error_response('Execution is already terminal.', status_code=status.HTTP_400_BAD_REQUEST)
            before_state = AIExecutionRequestSerializer(ai_item).data
            ai_item.status = AIExecutionStatus.CANCELLED
            ai_item.cancelled_at = timezone.now()
            ai_item.save(update_fields=['status', 'cancelled_at', 'updated_at'])
            _audit_mutation(
                request=request,
                action_type='ai_execution.cancelled',
                target_type='ai_execution_request',
                target_id=ai_item.id,
                before_state=before_state,
                after_state=AIExecutionRequestSerializer(ai_item).data,
            )
            return success_response(data=AIExecutionRequestSerializer(ai_item).data, message='AI execution cancelled.')

        automation_item = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id, pk=execution_id).first()
        if automation_item:
            if automation_item.status in {
                AutomationExecutionStatus.COMPLETED,
                AutomationExecutionStatus.FAILED,
                AutomationExecutionStatus.CANCELLED,
            }:
                return error_response('Execution is already terminal.', status_code=status.HTTP_400_BAD_REQUEST)
            before_state = AutomationExecutionRunSerializer(automation_item).data
            automation_item.status = AutomationExecutionStatus.CANCELLED
            automation_item.save(update_fields=['status', 'updated_at'])
            _audit_mutation(
                request=request,
                action_type='automation_execution.cancelled',
                target_type='automation_execution_run',
                target_id=automation_item.id,
                before_state=before_state,
                after_state=AutomationExecutionRunSerializer(automation_item).data,
            )
            return success_response(data=AutomationExecutionRunSerializer(automation_item).data, message='Automation execution cancelled.')
        return error_response('Execution not found.', status_code=status.HTTP_404_NOT_FOUND)


class ExecutionApproveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.manage')]

    def post(self, request, execution_id):
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = ApprovalQueueItem.objects.filter(
            tenant_id=request.user.tenant_id,
            origin_id=execution_id,
            status=ApprovalStatus.PENDING,
        ).first()
        if not item:
            return error_response('Approval item not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = ApprovalQueueItemSerializer(item).data
        try:
            item = ApprovalService.approve(
                item,
                request.user.id,
                serializer.validated_data.get('comment', ''),
                apply_now=serializer.validated_data['apply_now'],
            )
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='approval.approved',
            target_type='approval_queue_item',
            target_id=item.id,
            before_state=before_state,
            after_state=ApprovalQueueItemSerializer(item).data,
            metadata={'origin_execution_id': str(execution_id)},
        )
        return success_response(data=ApprovalQueueItemSerializer(item).data, message='Execution approved.')


class ExecutionRejectView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.manage')]

    def post(self, request, execution_id):
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = ApprovalQueueItem.objects.filter(
            tenant_id=request.user.tenant_id,
            origin_id=execution_id,
            status=ApprovalStatus.PENDING,
        ).first()
        if not item:
            return error_response('Approval item not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = ApprovalQueueItemSerializer(item).data
        try:
            item = ApprovalService.reject(item, request.user.id, serializer.validated_data.get('comment', ''))
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='approval.rejected',
            target_type='approval_queue_item',
            target_id=item.id,
            before_state=before_state,
            after_state=ApprovalQueueItemSerializer(item).data,
            metadata={'origin_execution_id': str(execution_id)},
        )
        return success_response(data=ApprovalQueueItemSerializer(item).data, message='Execution rejected.')


class FailureListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('failures.view')]

    def get(self, request):
        failures = ExecutionFailure.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data=ExecutionFailureSerializer(failures, many=True).data, message='Failures retrieved.')


class DeadLetterListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('failures.manage')]

    def get(self, request):
        items = DeadLetterItem.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data=DeadLetterItemSerializer(items, many=True).data, message='Dead-letter items retrieved.')


class FailureRetryView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('failures.manage')]

    def post(self, request, pk):
        try:
            failure = ExecutionFailure.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except ExecutionFailure.DoesNotExist:
            return error_response('Failure not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = ExecutionFailureSerializer(failure).data
        try:
            failure = FailureService.retry_failure(failure=failure)
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='failure.retry_requested',
            target_type='execution_failure',
            target_id=failure.id,
            before_state=before_state,
            after_state=ExecutionFailureSerializer(failure).data,
        )
        return success_response(data=ExecutionFailureSerializer(failure).data, message='Failure marked for retry.')


class FailureResolveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('failures.manage')]

    def post(self, request, pk):
        try:
            failure = ExecutionFailure.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except ExecutionFailure.DoesNotExist:
            return error_response('Failure not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = FailureResolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        before_state = ExecutionFailureSerializer(failure).data
        try:
            failure = FailureService.resolve_failure(
                failure=failure,
                user_id=request.user.id,
                resolution_note=serializer.validated_data.get('resolution_note', ''),
            )
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='failure.resolved',
            target_type='execution_failure',
            target_id=failure.id,
            before_state=before_state,
            after_state=ExecutionFailureSerializer(failure).data,
        )
        return success_response(data=ExecutionFailureSerializer(failure).data, message='Failure resolved.')


class DeadLetterRequeueView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('failures.manage')]

    def post(self, request, pk):
        try:
            item = DeadLetterItem.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except DeadLetterItem.DoesNotExist:
            return error_response('Dead-letter item not found.', status_code=status.HTTP_404_NOT_FOUND)
        before_state = DeadLetterItemSerializer(item).data
        try:
            item = FailureService.requeue_dead_letter(item=item)
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='dead_letter.requeued',
            target_type='dead_letter_item',
            target_id=item.id,
            before_state=before_state,
            after_state=DeadLetterItemSerializer(item).data,
        )
        return success_response(data=DeadLetterItemSerializer(item).data, message='Dead-letter item requeued.')


class SettingsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('settings.manage')]

    def get(self, request):
        settings_obj, _ = TenantSettingsService.get_or_create(request.user.tenant_id, request.user.id)
        return success_response(data=TenantIntelligenceSettingsSerializer(settings_obj).data, message='Settings retrieved.')

    def put(self, request):
        settings_obj, _ = TenantSettingsService.get_or_create(request.user.tenant_id, request.user.id)
        serializer = TenantIntelligenceSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        before_state = TenantIntelligenceSettingsSerializer(settings_obj).data
        try:
            settings_obj = TenantSettingsService.update_settings(
                settings_obj=settings_obj,
                data=serializer.validated_data,
                updated_by_id=request.user.id,
            )
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='tenant_settings.updated',
            target_type='tenant_intelligence_settings',
            target_id=settings_obj.id,
            before_state=before_state,
            after_state=TenantIntelligenceSettingsSerializer(settings_obj).data,
        )
        return success_response(data=TenantIntelligenceSettingsSerializer(settings_obj).data, message='Settings updated.')


class ConnectorListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('connectors.view')]

    def get(self, request):
        queryset = _platform_or_tenant_queryset(IntelligenceConnector.objects.all(), request.user.tenant_id)
        return success_response(
            data=IntelligenceConnectorSerializer(queryset, many=True).data,
            message='Connectors retrieved.',
        )


class ApprovalListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.view')]

    def get(self, request):
        items = ApprovalQueueItem.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data=ApprovalQueueItemSerializer(items, many=True).data, message='Approvals retrieved.')


class ApprovalDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.view')]

    def get(self, request, pk):
        try:
            item = ApprovalQueueItem.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except ApprovalQueueItem.DoesNotExist:
            return error_response('Approval item not found.', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=ApprovalQueueItemSerializer(item).data, message='Approval item retrieved.')


class ApprovalApproveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.manage')]

    def post(self, request, pk):
        try:
            item = ApprovalQueueItem.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except ApprovalQueueItem.DoesNotExist:
            return error_response('Approval item not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        before_state = ApprovalQueueItemSerializer(item).data
        try:
            item = ApprovalService.approve(
                item,
                request.user.id,
                serializer.validated_data.get('comment', ''),
                apply_now=serializer.validated_data['apply_now'],
            )
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='approval.approved',
            target_type='approval_queue_item',
            target_id=item.id,
            before_state=before_state,
            after_state=ApprovalQueueItemSerializer(item).data,
        )
        return success_response(data=ApprovalQueueItemSerializer(item).data, message='Approval granted.')


class ApprovalRejectView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('approvals.manage')]

    def post(self, request, pk):
        try:
            item = ApprovalQueueItem.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except ApprovalQueueItem.DoesNotExist:
            return error_response('Approval item not found.', status_code=status.HTTP_404_NOT_FOUND)
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        before_state = ApprovalQueueItemSerializer(item).data
        try:
            item = ApprovalService.reject(item, request.user.id, serializer.validated_data.get('comment', ''))
        except ValueError as exc:
            return _bad_request(exc)
        _audit_mutation(
            request=request,
            action_type='approval.rejected',
            target_type='approval_queue_item',
            target_id=item.id,
            before_state=before_state,
            after_state=ApprovalQueueItemSerializer(item).data,
        )
        return success_response(data=ApprovalQueueItemSerializer(item).data, message='Approval rejected.')


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('governance.view')]

    def get(self, request):
        queryset = IntelligenceAuditLog.objects.filter(tenant_id=request.user.tenant_id)
        action_type = request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        target_type = request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        return success_response(
            data=IntelligenceAuditLogSerializer(queryset[:100], many=True).data,
            message='Audit logs retrieved.',
        )


class DecisionTrackingView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('governance.view')]

    def get(self, request):
        # Decision tracking combines Audit logs for stage changes and Approval Queue decisions
        approvals = ApprovalQueueItem.objects.filter(
            tenant_id=request.user.tenant_id,
            status__in=[ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]
        )
        stage_changes = IntelligenceAuditLog.objects.filter(
            tenant_id=request.user.tenant_id,
            action_type__in=['candidate.move_stage', 'candidate.rejected', 'candidate.joined']
        )
        
        return success_response(
            data={
                'approvals': ApprovalQueueItemSerializer(approvals[:50], many=True).data,
                'audit_decisions': IntelligenceAuditLogSerializer(stage_changes[:50], many=True).data
            },
            message='Decision history retrieved.'
        )


class AutomationGovernanceView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('governance.view')]

    def get(self, request):
        # Automation health and override tracking
        runs = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id)
        overrides = IntelligenceAuditLog.objects.filter(
            tenant_id=request.user.tenant_id,
            action_type__in=['automation_execution.retried', 'automation_execution.cancelled']
        )
        
        return success_response(
            data={
                'runs_summary': {
                    'total': runs.count(),
                    'completed': runs.filter(status=AutomationExecutionStatus.COMPLETED).count(),
                    'failed': runs.filter(status=AutomationExecutionStatus.FAILED).count(),
                },
                'manual_overrides': IntelligenceAuditLogSerializer(overrides[:50], many=True).data
            },
            message='Automation governance data retrieved.'
        )


class AITransparencyView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('governance.view')]

    def get(self, request):
        # AI decision transparency and human override tracking
        ai_executions = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id)
        suggestions = AISuggestion.objects.filter(tenant_id=request.user.tenant_id)
        overrides = IntelligenceAuditLog.objects.filter(
            tenant_id=request.user.tenant_id,
            action_type__in=['suggestion.dismissed', 'suggestion.applied_with_override']
        )
        
        return success_response(
            data={
                'ai_summary': {
                    'total_executions': ai_executions.count(),
                    'total_suggestions': suggestions.count(),
                    'applied_suggestions': suggestions.filter(status='applied').count(),
                },
                'human_overrides': IntelligenceAuditLogSerializer(overrides[:50], many=True).data
            },
            message='AI transparency data retrieved.'
        )


class AutomationAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    def get(self, request):
        from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService
        days = int(request.query_params.get('days', 30))
        data = AutomationAnalyticsService.get_automation_analytics(request.user.tenant_id, days=days)
        return success_response(data=data, message='Automation analytics retrieved.')


class WorkflowAnalyticsBaseView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    def get_date_range(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            
        return start_date, end_date


class WorkflowAnalyticsOverviewView(WorkflowAnalyticsBaseView):
    def get(self, request):
        try:
            tenant_id = request.user.tenant_id
            start_date, end_date = self.get_date_range(request)
            
            executions = WorkflowExecution.objects.filter(
                tenant_id=tenant_id,
                started_at__gte=start_date,
                started_at__lte=end_date
            )
            
            total = executions.count()
            completed = executions.filter(status='completed').count()
            failed = executions.filter(status='failed').count()
            running = executions.filter(status='running').count()
            paused = executions.filter(status='paused').count()
            
            # Impact aggregation
            impacts = WorkflowImpactMetric.objects.filter(tenant_id=tenant_id).values('impact_type').annotate(total=Sum('metric_value'))
            impact_map = {item['impact_type']: item['total'] for item in impacts}
            
            # Trigger aggregation
            triggers = WorkflowTriggerMetric.objects.filter(tenant_id=tenant_id).values('trigger_event').annotate(total=Sum('trigger_count')).order_by('-total')[:5]
            
            data = {
                'execution_metrics': {
                    'total': total,
                    'completed': completed,
                    'failed': failed,
                    'running': running,
                    'paused': paused,
                    'success_rate': (completed / total * 100) if total > 0 else 100.0,
                },
                'impact_metrics': impact_map,
                'top_triggers': list(triggers),
                'active_workflows': Workflow.objects.filter(tenant_id=tenant_id, is_active=True).count(),
            }
            
            return success_response(data=data)
        except Exception as e:
            import traceback
            return error_response(str(e), errors={'traceback': traceback.format_exc()}, status_code=500)


class WorkflowAnalyticsListView(WorkflowAnalyticsBaseView):
    def get(self, request):
        try:
            tenant_id = request.user.tenant_id
            workflows = Workflow.objects.filter(tenant_id=tenant_id, is_deleted=False)
            
            data = []
            for wf in workflows:
                # Get latest snapshot or aggregate
                snapshot = WorkflowAnalyticsSnapshot.objects.filter(workflow=wf).order_by('-snapshot_date').first()
                impact = WorkflowImpactMetric.objects.filter(workflow=wf, impact_type='hours_saved').first()
                
                data.append({
                    'id': str(wf.id),
                    'name': wf.name,
                    'status': 'active' if wf.is_active else 'inactive',
                    'executions': snapshot.execution_count if snapshot else 0,
                    'success_rate': snapshot.completion_rate if snapshot else 0.0,
                    'avg_time_ms': snapshot.avg_execution_time_ms if snapshot else 0,
                    'impact_hours': impact.metric_value if impact else 0,
                })
                
            return success_response(data=data)
        except Exception as e:
            import traceback
            return error_response(str(e), errors={'traceback': traceback.format_exc()}, status_code=500)


class WorkflowAnalyticsDetailView(WorkflowAnalyticsBaseView):
    def get(self, request, pk):
        tenant_id = request.user.tenant_id
        workflow = Workflow.objects.get(id=pk, tenant_id=tenant_id)
        
        # 1. Snapshots (Trends)
        snapshots = WorkflowAnalyticsSnapshot.objects.filter(workflow=workflow).order_by('snapshot_date')[:30]
        
        # 2. Trigger stats
        triggers = WorkflowTriggerMetric.objects.filter(workflow=workflow)
        
        # 3. Action stats
        actions = WorkflowActionMetric.objects.filter(workflow=workflow)
        
        # 4. Impact stats
        impacts = WorkflowImpactMetric.objects.filter(workflow=workflow)
        
        # 5. Failure insights
        insights = WorkflowFailureInsight.objects.filter(workflow=workflow, status='new')
        
        data = {
            'workflow_id': workflow.id,
            'name': workflow.name,
            'trends': [{'date': s.snapshot_date, 'count': s.execution_count, 'success': s.success_count} for s in snapshots],
            'triggers': [{'event': t.trigger_event, 'count': t.trigger_count} for t in triggers],
            'actions': [{'type': a.action_type, 'count': a.action_count, 'success': a.success_count, 'avg_time': a.avg_action_time_ms} for a in actions],
            'impacts': [{'type': i.impact_type, 'value': i.metric_value, 'unit': i.metric_unit} for i in impacts],
            'failure_insights': [{'type': fi.failure_type, 'title': fi.title, 'count': fi.occurrence_count} for fi in insights]
        }
        
        return success_response(data=data)


class WorkflowAnalyticsTriggersView(WorkflowAnalyticsBaseView):
    def get(self, request):
        tenant_id = request.user.tenant_id
        triggers = WorkflowTriggerMetric.objects.filter(tenant_id=tenant_id).values('trigger_event').annotate(
            total_count=Sum('trigger_count'),
            execution_count=Sum('execution_started_count')
        ).order_by('-total_count')
        return success_response(data=list(triggers))


class WorkflowAnalyticsActionsView(WorkflowAnalyticsBaseView):
    def get(self, request):
        tenant_id = request.user.tenant_id
        actions = WorkflowActionMetric.objects.filter(tenant_id=tenant_id).values('action_type').annotate(
            total_count=Sum('action_count'),
            success_count=Sum('success_count'),
            failure_count=Sum('failure_count'),
            avg_time=Avg('avg_action_time_ms')
        ).order_by('-total_count')
        return success_response(data=list(actions))


class WorkflowAnalyticsFailuresView(WorkflowAnalyticsBaseView):
    def get(self, request):
        tenant_id = request.user.tenant_id
        insights = WorkflowFailureInsight.objects.filter(tenant_id=tenant_id).order_by('-occurrence_count')
        data = [{
            'id': i.id,
            'workflow_name': i.workflow.name,
            'failure_type': i.failure_type,
            'title': i.title,
            'description': i.description,
            'occurrence_count': i.occurrence_count,
            'last_seen_at': i.last_seen_at,
            'status': i.status
        } for i in insights]
        return success_response(data=data)


class WorkflowAnalyticsImpactView(WorkflowAnalyticsBaseView):
    def get(self, request):
        tenant_id = request.user.tenant_id
        impacts = WorkflowImpactMetric.objects.filter(tenant_id=tenant_id).values('impact_type').annotate(
            total_value=Sum('metric_value')
        )
        return success_response(data=list(impacts))


class WorkflowAnalyticsAdoptionView(WorkflowAnalyticsBaseView):
    def get(self, request):
        tenant_id = request.user.tenant_id
        total_workflows = Workflow.objects.filter(tenant_id=tenant_id, is_deleted=False).count()
        active_workflows = Workflow.objects.filter(tenant_id=tenant_id, is_active=True, is_deleted=False).count()
        
        # Workflows by category (module_scope)
        # Assuming Workflow has module_scope or similar. Checking Workflow model might be needed.
        # For now, aggregate by some field if it exists.
        
        data = {
            'total_workflows': total_workflows,
            'active_workflows': active_workflows,
            'inactive_workflows': total_workflows - active_workflows,
            'adoption_rate': (active_workflows / total_workflows * 100) if total_workflows > 0 else 0,
        }
        return success_response(data=data)


class PolicyAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    def get(self, request):
        from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService
        data = AutomationAnalyticsService.get_policy_analytics(request.user.tenant_id)
        return success_response(data=data, message='Policy analytics retrieved.')


class LearningSignalsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        signals = AutomationLearningSignal.objects.filter(tenant_id=request.user.tenant_id)[:100]
        return success_response(data=AutomationLearningSignalSerializer(signals, many=True).data, message='Learning signals retrieved.')


class LearningPoliciesView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_learning import AutomationLearningService
        data = AutomationLearningService.get_policy_learning_data(request.user.tenant_id)
        return success_response(data=data, message='Policy learning data retrieved.')


class LearningRecommendationsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_learning import AutomationLearningService
        data = AutomationLearningService.get_recommendations(request.user.tenant_id)
        return success_response(data=data, message='Learning recommendations retrieved.')


class GovernanceRulesView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        rules = AIGovernanceRule.objects.filter(tenant_id=request.user.tenant_id, is_deleted=False)
        return success_response(data=AIGovernanceRuleSerializer(rules, many=True).data)

    def post(self, request):
        serializer = AIGovernanceRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(tenant_id=request.user.tenant_id)
        return success_response(data=serializer.data, message='Governance rule created.')


class GovernanceApprovalsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        approval_status_val = request.query_params.get('status', 'pending')
        approvals = AIGovernanceApproval.objects.filter(tenant_id=request.user.tenant_id, approval_status=approval_status_val)
        return success_response(data=AIGovernanceApprovalSerializer(approvals, many=True).data)


class GovernanceApproveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request):
        from apps.orchestration_center.services.ai_governance import AIGovernanceService
        approval_id = request.data.get('approval_id')
        reason = request.data.get('reason', '')
        exists = AIGovernanceApproval.objects.filter(
            id=approval_id,
            tenant_id=request.user.tenant_id,
        ).exists()
        if not exists:
            return error_response('Approval request not found.', status_code=status.HTTP_404_NOT_FOUND)
        approval = AIGovernanceService.approve_request(request.user.tenant_id, approval_id, request.user.id, reason)
        return success_response(data=AIGovernanceApprovalSerializer(approval).data, message='Request approved.')


class GovernanceRejectView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request):
        from apps.orchestration_center.services.ai_governance import AIGovernanceService
        approval_id = request.data.get('approval_id')
        reason = request.data.get('reason', '')
        exists = AIGovernanceApproval.objects.filter(
            id=approval_id,
            tenant_id=request.user.tenant_id,
        ).exists()
        if not exists:
            return error_response('Approval request not found.', status_code=status.HTTP_404_NOT_FOUND)
        approval = AIGovernanceService.reject_request(request.user.tenant_id, approval_id, request.user.id, reason)
        return success_response(data=AIGovernanceApprovalSerializer(approval).data, message='Request rejected.')


class LibraryTemplateListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_library import AutomationLibraryService
        from apps.orchestration_center.api.serializers import AutomationLibraryTemplateSerializer
        category = request.query_params.get('category')
        templates = AutomationLibraryService.list_templates(tenant_id=request.user.tenant_id, category=category)
        return success_response(data=AutomationLibraryTemplateSerializer(templates, many=True).data)


class LibraryTemplateCloneView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.services.automation_library import AutomationLibraryService
        from apps.orchestration_center.api.serializers import AutomationLibraryTemplateSerializer
        from apps.orchestration_center.models import AutomationLibraryTemplate
        template_exists = AutomationLibraryTemplate.objects.filter(pk=pk, is_system_template=True, is_deleted=False).exists()
        if not template_exists:
            return error_response('Library template not found.', status_code=status.HTTP_404_NOT_FOUND)
        clone = AutomationLibraryService.clone_template_to_tenant(pk, request.user.tenant_id, request.user.id)
        return success_response(data=AutomationLibraryTemplateSerializer(clone).data, message='Template cloned to tenant.')


class LibraryTemplateActivateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.services.automation_library import AutomationLibraryService
        from apps.orchestration_center.models import AutomationLibraryTemplate
        template_exists = AutomationLibraryTemplate.objects.filter(pk=pk, is_system_template=True, is_deleted=False).exists()
        if not template_exists:
            return error_response('Library template not found.', status_code=status.HTTP_404_NOT_FOUND)
        policy = AutomationLibraryService.activate_template(pk, request.user.tenant_id, request.user.id)
        return success_response(message=f'Template activated as policy {policy.id}.')


class LibraryTenantTemplatesView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import AutomationLibraryTemplate
        from apps.orchestration_center.api.serializers import AutomationLibraryTemplateSerializer
        templates = AutomationLibraryTemplate.objects.filter(tenant_id=request.user.tenant_id, is_system_template=False, is_deleted=False)
        return success_response(data=AutomationLibraryTemplateSerializer(templates, many=True).data)


class WorkflowListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import Workflow
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        workflows = Workflow.objects.filter(tenant_id=request.user.tenant_id, is_deleted=False)
        return success_response(data=WorkflowSerializer(workflows, many=True).data)

    def post(self, request):
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        serializer = WorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(tenant_id=request.user.tenant_id, created_by=request.user.id)
        return success_response(data=serializer.data, message='Workflow created.')


class WorkflowDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request, pk):
        from apps.orchestration_center.models import Workflow
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        try:
            workflow = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
            return success_response(data=WorkflowSerializer(workflow).data)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        from apps.orchestration_center.models import Workflow
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        try:
            workflow = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = WorkflowSerializer(workflow, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message='Workflow updated.')


class WorkflowExecutionListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import WorkflowExecution
        from apps.orchestration_center.api.serializers import WorkflowExecutionSerializer
        executions = WorkflowExecution.objects.filter(tenant_id=request.user.tenant_id)
        
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            executions = executions.filter(workflow_id=workflow_id)
            
        return success_response(data=WorkflowExecutionSerializer(executions[:100], many=True).data)


class WorkflowBuilderView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request, pk):
        from apps.orchestration_center.models import Workflow
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        try:
            workflow = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
            return success_response(data=WorkflowSerializer(workflow).data)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)


class WorkflowBuilderSaveView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.models import Workflow, WorkflowNode, WorkflowEdge
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        try:
            workflow = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)

        nodes_data = request.data.get('nodes', [])
        edges_data = request.data.get('edges', [])
        metadata = request.data.get('metadata', {})

        # Update metadata
        if 'name' in metadata: workflow.name = metadata['name']
        if 'description' in metadata: workflow.description = metadata['description']
        if 'trigger_event' in metadata: workflow.trigger_event = metadata['trigger_event']
        workflow.save()

        # Simple approach: clear and rebuild nodes/edges
        # In a real production system, we might want to be more surgical to preserve IDs if possible
        workflow.nodes.all().delete()
        workflow.edges.all().delete()

        nodes_map = {}
        for n_data in nodes_data:
            node = WorkflowNode.objects.create(
                workflow=workflow,
                node_type=n_data['type'],
                config=n_data.get('config', {}),
                position_x=int(n_data.get('position', {}).get('x', 0)),
                position_y=int(n_data.get('position', {}).get('y', 0))
            )
            nodes_map[n_data['id']] = node

        for e_data in edges_data:
            source_id = e_data.get('source')
            target_id = e_data.get('target')
            if source_id in nodes_map and target_id in nodes_map:
                WorkflowEdge.objects.create(
                    workflow=workflow,
                    source_node=nodes_map[source_id],
                    target_node=nodes_map[target_id],
                    condition=e_data.get('condition', {})
                )

        return success_response(data=WorkflowSerializer(workflow).data, message='Workflow saved successfully.')


class WorkflowValidateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.models import Workflow
        try:
            workflow = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)

        errors = []
        nodes = workflow.nodes.all()
        
        if nodes.filter(node_type='start').count() != 1:
            errors.append('Workflow must have exactly one start node.')
        
        if nodes.filter(node_type='end').count() < 1:
            errors.append('Workflow must have at least one end node.')

        # Cycle detection and Reachability
        start_node = nodes.filter(node_type='start').first()
        if start_node:
            visited = set()
            stack = set()
            reachable = set()

            def has_cycle(node_id):
                visited.add(node_id)
                stack.add(node_id)
                reachable.add(node_id)
                
                from apps.orchestration_center.models import WorkflowEdge
                outgoing = WorkflowEdge.objects.filter(source_node_id=node_id)
                for edge in outgoing:
                    if edge.target_node_id in stack:
                        return True
                    if edge.target_node_id not in visited:
                        if has_cycle(edge.target_node_id):
                            return True
                stack.remove(node_id)
                return False

            if has_cycle(start_node.id):
                errors.append('Workflow contains circular dependencies (cycles).')
            
            # Orphan/Unreachable nodes check
            for node in nodes:
                if node.id not in reachable:
                    errors.append(f'Unreachable node detected: {node.node_type} ({str(node.id)[:8]})')
                
                # Check for node-specific config
                if node.node_type == 'action' and not node.config.get('type'):
                    errors.append(f'Action node missing type: {str(node.id)[:8]}')
                if node.node_type == 'condition' and not node.config.get('field'):
                    errors.append(f'Condition node missing field: {str(node.id)[:8]}')
                if node.node_type == 'approval' and not node.config.get('approver_role'):
                    errors.append(f'Approval node missing approver role: {str(node.id)[:8]}')

        return success_response(data={'valid': len(errors) == 0, 'errors': errors})


class WorkflowDuplicateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.models import Workflow, WorkflowNode, WorkflowEdge
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        try:
            original = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)

        new_workflow = Workflow.objects.create(
            tenant_id=request.user.tenant_id,
            name=f"{original.name} (Copy)",
            description=original.description,
            trigger_event=original.trigger_event,
            status='draft',
            created_by=request.user.id
        )

        nodes_map = {}
        for node in original.nodes.all():
            new_node = WorkflowNode.objects.create(
                workflow=new_workflow,
                node_type=node.node_type,
                config=node.config,
                position_x=node.position_x,
                position_y=node.position_y
            )
            nodes_map[node.id] = new_node

        for edge in original.edges.all():
            WorkflowEdge.objects.create(
                workflow=new_workflow,
                source_node=nodes_map[edge.source_node_id],
                target_node=nodes_map[edge.target_node_id],
                condition=edge.condition
            )

        return success_response(data=WorkflowSerializer(new_workflow).data, message='Workflow duplicated.')


class WorkflowStatusActionView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk, action):
        from apps.orchestration_center.models import Workflow
        try:
            workflow = Workflow.objects.get(pk=pk, tenant_id=request.user.tenant_id, is_deleted=False)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)

        if action == 'activate':
            workflow.status = 'active'
            workflow.is_active = True
        elif action == 'pause':
            workflow.status = 'paused'
            workflow.is_active = False
        elif action == 'archive':
            workflow.status = 'archived'
            workflow.is_active = False
        else:
            return error_response('Invalid action')

        workflow.save()
        return success_response(message=f'Workflow {action}d successfully.')


class WorkflowTemplateListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import WorkflowTemplate
        from apps.orchestration_center.api.serializers import WorkflowTemplateSerializer
        templates = WorkflowTemplate.objects.filter(is_active=True)
        return success_response(data=WorkflowTemplateSerializer(templates, many=True).data)


class WorkflowTemplateEnableView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.models import WorkflowTemplate, Workflow, WorkflowNode, WorkflowEdge
        from apps.orchestration_center.api.serializers import WorkflowSerializer
        try:
            template = WorkflowTemplate.objects.get(pk=pk, is_active=True)
        except WorkflowTemplate.DoesNotExist:
            return error_response('Template not found', status_code=status.HTTP_404_NOT_FOUND)
        
        # Clone template to tenant workflow
        workflow = Workflow.objects.create(
            tenant_id=request.user.tenant_id,
            name=template.name,
            description=template.description,
            trigger_event=template.trigger_event,
            is_active=True,
            created_by=request.user.id
        )
        
        # Create nodes
        nodes_map = {}
        for node_data in template.template_json.get('nodes', []):
            node = WorkflowNode.objects.create(
                workflow=workflow,
                node_type=node_data['type'],
                config=node_data.get('config', {}),
                position_x=node_data.get('position_x', 0),
                position_y=node_data.get('position_y', 0)
            )
            nodes_map[node_data['id']] = node
            
        # Create edges
        for edge_data in template.template_json.get('edges', []):
            WorkflowEdge.objects.create(
                workflow=workflow,
                source_node=nodes_map[edge_data['source']],
                target_node=nodes_map[edge_data['target']],
                condition=edge_data.get('condition')
            )
            
        return success_response(data=WorkflowSerializer(workflow).data, message=f'Workflow "{workflow.name}" enabled from template.')


# ─── Workflow Governance Views ──────────────────────────────────────────────────

class WorkflowVersionListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request, workflow_id):
        versions = WorkflowVersion.objects.filter(workflow_id=workflow_id, tenant_id=request.user.tenant_id)
        return success_response(data=WorkflowVersionSerializer(versions, many=True).data)

    def post(self, request, workflow_id):
        try:
            workflow = Workflow.objects.get(pk=workflow_id, tenant_id=request.user.tenant_id)
        except Workflow.DoesNotExist:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)
        
        version = WorkflowGovernanceService.create_version(
            workflow=workflow,
            config_snapshot=request.data.get('config_snapshot', {}),
            changed_by_id=request.user.id,
            change_summary=request.data.get('change_summary', '')
        )
        return success_response(data=WorkflowVersionSerializer(version).data, message='Workflow version created.')


class WorkflowApprovalListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        status_filter = request.query_params.get('status', 'pending')
        approvals = WorkflowApproval.objects.filter(tenant_id=request.user.tenant_id, status=status_filter)
        return success_response(data=WorkflowApprovalSerializer(approvals, many=True).data)


class WorkflowApprovalDecideView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        status_val = request.data.get('status')
        if status_val not in ['approved', 'rejected']:
            return error_response('Invalid status')
        tenant_id = _effective_tenant_id(request)
        exists = WorkflowApproval.objects.filter(id=pk, tenant_id=tenant_id).exists()
        if not exists:
            return error_response('Approval not found', status_code=status.HTTP_404_NOT_FOUND)
        
        approval = WorkflowGovernanceService.decide_approval(
            approval_id=pk,
            approved_by_id=request.user.id,
            status=status_val,
            comment=request.data.get('comment', '')
        )
        return success_response(data=WorkflowApprovalSerializer(approval).data, message=f'Workflow {status_val}.')


class WorkflowSafetyRuleView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request, workflow_id):
        tenant_id = _effective_tenant_id(request)
        rule = WorkflowSafetyRule.objects.filter(workflow_id=workflow_id, tenant_id=tenant_id).first()
        if not rule:
            return error_response('Safety rule not found', status_code=status.HTTP_404_NOT_FOUND)
        return success_response(data=WorkflowSafetyRuleSerializer(rule).data)

    def put(self, request, workflow_id):
        tenant_id = _effective_tenant_id(request)
        workflow_exists = Workflow.objects.filter(id=workflow_id, tenant_id=tenant_id).exists()
        if not workflow_exists:
            return error_response('Workflow not found', status_code=status.HTTP_404_NOT_FOUND)
        rule, _ = WorkflowSafetyRule.objects.get_or_create(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            defaults={'tenant_id': tenant_id}
        )
        serializer = WorkflowSafetyRuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message='Safety rule updated.')


class WorkflowRollbackView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, execution_id):
        tenant_id = _effective_tenant_id(request)
        execution_exists = WorkflowExecution.objects.filter(id=execution_id, tenant_id=tenant_id).exists()
        if not execution_exists:
            return error_response('Execution not found', status_code=status.HTTP_404_NOT_FOUND)
        rollback_log = WorkflowGovernanceService.rollback_execution(
            execution_id=execution_id,
            performed_by_id=request.user.id
        )
        return success_response(data=WorkflowRollbackLogSerializer(rollback_log).data, message='Workflow execution rolled back.')


class WorkflowAuditLogListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        logs = WorkflowAuditLog.objects.filter(tenant_id=request.user.tenant_id)
        workflow_id = request.query_params.get('workflow_id')
        if workflow_id:
            logs = logs.filter(workflow_id=workflow_id)
        return success_response(data=WorkflowAuditLogSerializer(logs[:100], many=True).data)


class WorkflowGovernanceHealthView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        # Health metrics for the entire tenant's workflow system
        from django.db.models import Count, Q
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(days=1)
        
        executions = WorkflowExecution.objects.filter(tenant_id=request.user.tenant_id, started_at__gte=last_24h)
        
        summary = {
            'total_24h': executions.count(),
            'failed_24h': executions.filter(status='failed').count(),
            'paused_workflows': Workflow.objects.filter(tenant_id=request.user.tenant_id, status='paused').count(),
            'pending_approvals': WorkflowApproval.objects.filter(tenant_id=request.user.tenant_id, status='pending').count(),
            'active_workflows': Workflow.objects.filter(tenant_id=request.user.tenant_id, is_active=True).count(),
        }
        
        return success_response(data=summary)


# ---------------------------------------------------------------------------
# Analytics endpoints (admin-only, tenant-scoped)
# ---------------------------------------------------------------------------

class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService
        days = int(request.query_params.get('days', 30))
        data = AutomationAnalyticsService.get_overview_analytics(request.user.tenant_id, days=days)
        return success_response(data=data, message='Analytics overview retrieved.')


class AnalyticsSuggestionsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService
        days = int(request.query_params.get('days', 30))
        data = AutomationAnalyticsService.get_suggestion_analytics(request.user.tenant_id, days=days)
        return success_response(data=data, message='Suggestion analytics retrieved.')


class AnalyticsPoliciesView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService
        data = AutomationAnalyticsService.get_policy_analytics(request.user.tenant_id)
        return success_response(data=data, message='Policy analytics retrieved.')


class AnalyticsExecutionsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('analytics.view')]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        from apps.orchestration_center.services.automation_analytics import AutomationAnalyticsService
        days = int(request.query_params.get('days', 30))
        data = AutomationAnalyticsService.get_execution_analytics(request.user.tenant_id, days=days)
        return success_response(data=data, message='Execution analytics retrieved.')

# ---------------------------------------------------------------------------
# Learning Engine endpoints (admin-only, tenant-scoped)
# ---------------------------------------------------------------------------

class LearningOverviewView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_learning import AutomationLearningService
        data = AutomationLearningService.get_learning_overview(request.user.tenant_id)
        return success_response(data=data, message='Learning overview retrieved.')


class LearningRecommendationsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_learning import AutomationLearningService
        # Refresh recommendations
        AutomationLearningService.generate_policy_recommendations(request.user.tenant_id)
        
        # Get latest recommendations
        signals = AutomationLearningSignal.objects.filter(
            tenant_id=request.user.tenant_id
        ).exclude(recommendation='').order_by('-created_at')[:20]
        
        from apps.orchestration_center.api.serializers import AutomationLearningSignalSerializer
        return success_response(data=AutomationLearningSignalSerializer(signals, many=True).data)


class LearningSignalsView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_learning import AutomationLearningService
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        signals = AutomationLearningSignal.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')
        total_count = signals.count()
        paged_signals = signals[offset:offset+limit]
        
        from apps.orchestration_center.api.serializers import AutomationLearningSignalSerializer
        return success_response(data={
            'items': AutomationLearningSignalSerializer(paged_signals, many=True).data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }, message='Learning signals retrieved.')


class PolicyLearningTableView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_learning import AutomationLearningService
        data = AutomationLearningService.get_policy_learning_table(request.user.tenant_id)
        return success_response(data=data)


# ---------------------------------------------------------------------------
# Governance & Safety endpoints (admin-only, tenant-scoped)
# ---------------------------------------------------------------------------

class GovernanceSummaryView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.ai_governance import AIGovernanceService
        data = AIGovernanceService.get_governance_summary(request.user.tenant_id)
        return success_response(data=data, message='Governance summary retrieved.')

    def post(self, request):
        from apps.orchestration_center.models import TenantIntelligenceSettings, AutomationUsageLimit
        from apps.orchestration_center.services.ai_governance import AIGovernanceService
        
        tenant_id = request.user.tenant_id
        settings_data = request.data.get('settings', {})
        limits_data = request.data.get('limits', {})

        # Update Settings (Kill Switches)
        settings, _ = TenantIntelligenceSettings.objects.get_or_create(tenant_id=tenant_id)
        if 'ai_enabled' in settings_data: settings.ai_enabled = settings_data['ai_enabled']
        if 'automation_enabled' in settings_data: settings.automation_enabled = settings_data['automation_enabled']
        if 'auto_apply_enabled' in settings_data: settings.auto_apply_enabled = settings_data['auto_apply_enabled']
        settings.save()

        # Update Limits
        limits, _ = AutomationUsageLimit.objects.get_or_create(tenant_id=tenant_id)
        if 'daily_limit' in limits_data: limits.daily_limit = limits_data['daily_limit']
        if 'hourly_limit' in limits_data: limits.hourly_limit = limits_data['hourly_limit']
        if 'max_auto_apply' in limits_data: limits.max_auto_apply = limits_data['max_auto_apply']
        if 'max_failures' in limits_data: limits.max_failures = limits_data['max_failures']
        limits.save()

        AIGovernanceService.log_audit(tenant_id, 'kill_switch_toggled' if 'ai_enabled' in settings_data else 'policy_change', performed_by=request.user.id)

        return success_response(message='Governance settings updated.')


class GovernanceAuditListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import AutomationGovernanceAudit
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        audits_qs = AutomationGovernanceAudit.objects.filter(tenant_id=request.user.tenant_id).order_by('-timestamp')
        total_count = audits_qs.count()
        audits = audits_qs[offset:offset+limit]
        
        data = []
        for audit in audits:
            data.append({
                'id': str(audit.id),
                'action': audit.action,
                'performed_by': str(audit.performed_by) if audit.performed_by else None,
                'target_id': str(audit.target_id) if audit.target_id else None,
                'details': audit.details,
                'timestamp': audit.timestamp.isoformat()
            })
        return success_response(data={
            'items': data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }, message='Governance audit logs retrieved.')

# ---------------------------------------------------------------------------
# Optimization Engine endpoints (admin-only, tenant-scoped)
# ---------------------------------------------------------------------------

class OptimizationOverviewView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_optimization import AutomationOptimizationService
        data = AutomationOptimizationService.get_optimization_overview(request.user.tenant_id)
        return success_response(data=data, message='Optimization overview retrieved.')


class OptimizationRecommendationListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_optimization import AutomationOptimizationService
        # Trigger recommendation generation
        AutomationOptimizationService.generate_recommendations(request.user.tenant_id)
        
        from apps.orchestration_center.models import AutomationOptimizationRecommendation
        from apps.orchestration_center.api.serializers import AutomationOptimizationRecommendationSerializer
        recommendations = AutomationOptimizationRecommendation.objects.filter(
            tenant_id=request.user.tenant_id,
            applied_at__isnull=True
        )
        return success_response(data=AutomationOptimizationRecommendationSerializer(recommendations, many=True).data)


class OptimizationApplyView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.services.automation_optimization import AutomationOptimizationService
        success, message = AutomationOptimizationService.apply_recommendation(
            pk, 
            request.user.tenant_id, 
            performed_by=request.user.id
        )
        if success:
            return success_response(message=message)
        return error_response(message, status_code=400)


# ---------------------------------------------------------------------------
# Automation Library endpoints (admin-only, tenant-scoped)
# ---------------------------------------------------------------------------

class TemplateListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import AutomationTemplate
        from apps.orchestration_center.api.serializers import AutomationTemplateSerializer
        
        # System templates only for global listing
        templates = AutomationTemplate.objects.filter(is_system_template=True, is_active=True)
        return success_response(data=AutomationTemplateSerializer(templates, many=True).data)


class TemplateCloneView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.services.automation_template import AutomationTemplateService
        from apps.orchestration_center.api.serializers import AutomationTemplateSerializer
        
        cloned = AutomationTemplateService.clone_template(pk, request.user.tenant_id, performed_by=request.user.id)
        return success_response(data=AutomationTemplateSerializer(cloned).data, message='Template cloned successfully.')


class TemplateActivateView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from apps.orchestration_center.services.automation_template import AutomationTemplateService
        from apps.orchestration_center.api.serializers import AutomationIntelligencePolicySerializer
        
        policy = AutomationTemplateService.activate_template(pk, request.user.tenant_id, performed_by=request.user.id)
        return success_response(data=AutomationIntelligencePolicySerializer(policy).data, message='Template activated successfully.')


class TenantTemplateListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import AutomationTemplate
        from apps.orchestration_center.api.serializers import AutomationTemplateSerializer
        
        templates = AutomationTemplate.objects.filter(tenant_id=request.user.tenant_id, is_active=True)
        return success_response(data=AutomationTemplateSerializer(templates, many=True).data)


class IntelligenceHealthView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models import AIExecutionRequest, AutomationExecutionRun, AISuggestion
        from django.db.models import Count, Q
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(days=1)
        
        # 1. Execution Queue Health
        pending_ai = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, status='pending').count()
        running_ai = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, status='running').count()
        
        # 2. Failure Rate (Last 24h)
        total_ai_24h = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, created_at__gte=last_24h).count()
        failed_ai_24h = AIExecutionRequest.objects.filter(tenant_id=request.user.tenant_id, created_at__gte=last_24h, status='failed').count()
        
        ai_failure_rate = (failed_ai_24h / total_ai_24h * 100) if total_ai_24h > 0 else 0
        
        # 3. Automation Run Health
        total_runs_24h = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id, started_at__gte=last_24h).count()
        failed_runs_24h = AutomationExecutionRun.objects.filter(tenant_id=request.user.tenant_id, started_at__gte=last_24h, status='failed').count()
        
        run_failure_rate = (failed_runs_24h / total_runs_24h * 100) if total_runs_24h > 0 else 0
        
        # 4. Suggestions back-log
        pending_suggestions = AISuggestion.objects.filter(tenant_id=request.user.tenant_id, status='pending').count()

        health_data = {
            'status': 'healthy' if ai_failure_rate < 15 and run_failure_rate < 15 else 'degraded',
            'execution_queue': {
                'pending': pending_ai,
                'running': running_ai,
            },
            'performance_24h': {
                'ai_requests': total_ai_24h,
                'ai_failure_rate': round(ai_failure_rate, 2),
                'automation_runs': total_runs_24h,
                'run_failure_rate': round(run_failure_rate, 2),
            },
            'backlog': {
                'pending_suggestions': pending_suggestions
            },
            'timestamp': now.isoformat()
        }
        
        return success_response(data=health_data)


# ---------------------------------------------------------------------------
# AI Automation Intelligence endpoints
# ---------------------------------------------------------------------------

class AutomationInsightListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_ai_engine import AutomationAIEngine
        # Force a refresh of insights just before fetching
        AutomationAIEngine.run_all_analysis(request.user.tenant_id)
        
        status_filter = request.query_params.get('status', 'new')
        insights = AutomationInsight.objects.filter(tenant_id=request.user.tenant_id, status=status_filter)
        return success_response(data=AutomationInsightSerializer(insights, many=True).data)


class AutomationInsightAcceptView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        from django.db import transaction
        from apps.orchestration_center.models import WorkflowNode, WorkflowEdge

        try:
            insight = AutomationInsight.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AutomationInsight.DoesNotExist:
            return error_response('Insight not found.', status_code=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            insight.status = 'accepted'
            insight.save()

            action = insight.suggested_action.get('action')
            workflow_data = None
            if action == 'create_workflow':
                trigger_event = insight.suggested_action.get('trigger_event', 'manual')

                workflow = Workflow.objects.create(
                    tenant_id=request.user.tenant_id,
                    name=f"AI Optimized: {insight.title}",
                    description=f"Auto-generated from AI Insight: {insight.description}",
                    trigger_event=trigger_event,
                    is_active=False,
                    status='draft',
                    created_by=request.user.id
                )

                # Populate nodes if provided in suggested_action
                nodes_data = insight.suggested_action.get('nodes', [])
                nodes_map = {}
                for i, n_data in enumerate(nodes_data):
                    node = WorkflowNode.objects.create(
                        workflow=workflow,
                        node_type=n_data['type'],
                        config=n_data.get('config', {}),
                        position_x=100 + (i * 250),
                        position_y=200
                    )
                    nodes_map[i] = node

                # Simple linear edge creation for mock
                if len(nodes_map) > 1:
                    for i in range(len(nodes_map) - 1):
                        WorkflowEdge.objects.create(
                            workflow=workflow,
                            source_node=nodes_map[i],
                            target_node=nodes_map[i+1]
                        )

                workflow_data = WorkflowSerializer(workflow).data

        return success_response(data={'insight': AutomationInsightSerializer(insight).data, 'workflow': workflow_data}, message='Insight accepted and workflow generated.')

class AutomationInsightDismissView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request, pk):
        try:
            insight = AutomationInsight.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except AutomationInsight.DoesNotExist:
            return error_response('Insight not found.', status_code=status.HTTP_404_NOT_FOUND)

        insight.status = 'dismissed'
        insight.save()

        return success_response(data=AutomationInsightSerializer(insight).data, message='Insight dismissed.')


class AutomationRecommendationListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.services.automation_ai_engine import AutomationAIEngine
        # Refresh recommendations
        AutomationAIEngine.generate_recommendations(request.user.tenant_id)
        
        recommendations = AutomationRecommendation.objects.filter(tenant_id=request.user.tenant_id)
        return success_response(data=AutomationRecommendationSerializer(recommendations, many=True).data)


# ---------------------------------------------------------------------------
# Workflow Event Trigger System endpoints
# ---------------------------------------------------------------------------

class WorkflowEventRegistryView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models.event_trigger import WorkflowEventDefinition
        from apps.orchestration_center.api.serializers import WorkflowEventDefinitionSerializer
        events = WorkflowEventDefinition.objects.filter(is_active=True)
        return success_response(data=WorkflowEventDefinitionSerializer(events, many=True).data)


class WorkflowEventSubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]
    serializer_class = WorkflowEventSubscriptionSerializer

    def get_queryset(self):
        from apps.orchestration_center.models.event_trigger import WorkflowEventSubscription
        return WorkflowEventSubscription.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, created_by=self.request.user.id)


class WorkflowEventLogListView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request):
        from apps.orchestration_center.models.event_trigger import WorkflowEventLog
        from apps.orchestration_center.api.serializers import WorkflowEventLogSerializer
        logs = WorkflowEventLog.objects.filter(tenant_id=request.user.tenant_id).order_by('-created_at')[:100]
        return success_response(data=WorkflowEventLogSerializer(logs, many=True).data)


class WorkflowEventLogDetailView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request, pk):
        from apps.orchestration_center.models.event_trigger import WorkflowEventLog
        from apps.orchestration_center.api.serializers import WorkflowEventLogSerializer
        try:
            log = WorkflowEventLog.objects.get(pk=pk, tenant_id=request.user.tenant_id)
            return success_response(data=WorkflowEventLogSerializer(log).data)
        except WorkflowEventLog.DoesNotExist:
            return error_response('Log entry not found.', status_code=status.HTTP_404_NOT_FOUND)


class WorkflowEventDebugTraceView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def get(self, request, log_pk):
        from apps.orchestration_center.models.event_trigger import WorkflowEventDebugTrace
        from apps.orchestration_center.api.serializers import WorkflowEventDebugTraceSerializer
        traces = WorkflowEventDebugTrace.objects.filter(event_log_id=log_pk, tenant_id=request.user.tenant_id)
        return success_response(data=WorkflowEventDebugTraceSerializer(traces, many=True).data)


class WorkflowEventTestEmitView(APIView):
    permission_classes = [IsAuthenticated, require_hub_permission('intelligence.admin')]

    def post(self, request):
        from apps.orchestration_center.services.workflow_event_engine import WorkflowEventEngine
        event_key = request.data.get('event_key')
        entity_type = request.data.get('entity_type', 'test')
        entity_id = request.data.get('entity_id', str(uuid.uuid4()))
        payload = request.data.get('payload', {})
        source_module = request.data.get('source_module', 'test_studio')

        if not event_key:
            return error_response('event_key is required.')

        WorkflowEventEngine.emit_event(
            tenant_id=request.user.tenant_id,
            event_key=event_key,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            source_module=source_module
        )

        return success_response(message=f"Event '{event_key}' emitted successfully.")
