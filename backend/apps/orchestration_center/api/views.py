from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import error_response, success_response
from apps.orchestration_center.api.permissions import require_hub_permission
from apps.orchestration_center.api.serializers import (
    AIExecutionRequestSerializer,
    AIModelSerializer,
    AIProviderSerializer,
    AISuggestionApproveSerializer,
    AISuggestionConvertSerializer,
    AISuggestionCreateSerializer,
    AISuggestionReviewSerializer,
    AISuggestionSerializer,
    ApprovalDecisionSerializer,
    ApprovalQueueItemSerializer,
    AutomationExecutionRunSerializer,
    AutomationRuleSerializer,
    AutomationSimulationSerializer,
    AutomationToggleSerializer,
    DeadLetterItemSerializer,
    ExecutionFailureSerializer,
    FailureResolveRequestSerializer,
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
    AutomationRule,
    DeadLetterItem,
    ExecutionFailure,
    IntelligenceConnector,
    PromptTemplate,
    PromptVersion,
)
from apps.orchestration_center.selectors.overview import get_overview_snapshot
from apps.orchestration_center.services.approval_service import ApprovalService
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.automation_rule_service import AutomationRuleService
from apps.orchestration_center.services.failure_service import FailureService
from apps.orchestration_center.services.prompt_registry_service import PromptRegistryService
from apps.orchestration_center.services.tenant_settings_service import TenantSettingsService
from apps.orchestration_center.services.suggestion_service import SuggestionService


def _tenant_queryset(queryset, tenant_id):
    if hasattr(queryset.model, 'tenant_id'):
        return queryset.filter(tenant_id=tenant_id)
    return queryset


def _platform_or_tenant_queryset(queryset, tenant_id):
    if hasattr(queryset.model, 'tenant_id'):
        return queryset.filter(tenant_id__in=[tenant_id, None])
    return queryset


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
        return success_response(data=AISuggestionSerializer(item).data, message='Suggestion approved.')


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
