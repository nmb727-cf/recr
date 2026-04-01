from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.orchestration_center.constants.execution_statuses import (
    AIExecutionStatus,
    ApplicationStatus,
    ApprovalMode,
    ApprovalStatus,
    ReviewStatus,
    ValidationStatus,
)
from apps.orchestration_center.models import (
    AIExecutionRequest,
    AIExecutionResult,
    AIExecutionReview,
    ApprovalQueueItem,
    ExecutionFailure,
)
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.prompt_registry_service import PromptRegistryService
from apps.orchestration_center.services.provider_router import ProviderExecutionError, ProviderRouter
from apps.orchestration_center.services.suggestion_service import SuggestionService


class AIExecutionService:
    @staticmethod
    def _extract_confidence_score(execution):
        candidate = execution.get('confidence_score')
        if candidate is None:
            candidate = execution.get('normalized_output_json', {}).get('confidence_score')
        if candidate in (None, ''):
            return None
        try:
            value = float(candidate)
        except (TypeError, ValueError):
            return None
        if value < 0 or value > 1:
            return None
        return value

    @staticmethod
    def _maybe_create_suggestion_from_completed_request(*, request):
        try:
            suggestion, created, outcome = SuggestionService.create_supported_suggestion_from_ai_execution(ai_request=request)
        except ValueError as exc:
            AuditService.log(
                tenant_id=request.tenant_id,
                actor_id=request.created_by,
                actor_type='system',
                action_type='ai_suggestion.skipped',
                target_type='ai_execution_request',
                target_id=request.id,
                metadata_json={'reason': str(exc), 'use_case_key': request.use_case_key},
            )
            return None, False, 'skipped'
        except Exception as exc:
            AuditService.log(
                tenant_id=request.tenant_id,
                actor_id=request.created_by,
                actor_type='system',
                action_type='ai_suggestion.generation_failed',
                target_type='ai_execution_request',
                target_id=request.id,
                metadata_json={'error': str(exc), 'use_case_key': request.use_case_key},
            )
            return None, False, 'failed'

        AuditService.log(
            tenant_id=request.tenant_id,
            actor_id=request.created_by,
            actor_type='system',
            action_type='ai_suggestion.created' if created else 'ai_suggestion.duplicate',
            target_type='ai_suggestion' if suggestion else 'ai_execution_request',
            target_id=suggestion.id if suggestion else request.id,
            metadata_json={
                'ai_execution_id': str(request.id),
                'use_case_key': request.use_case_key,
                'outcome': outcome,
            },
        )
        return suggestion, created, outcome

    @staticmethod
    @transaction.atomic
    def create_request(
        *,
        tenant_id,
        created_by,
        module_scope,
        use_case_key,
        source_module,
        source_entity_type,
        source_entity_id,
        source_event='',
        context_snapshot=None,
        mode='suggestion_only',
        requires_review=False,
        requires_approval=False,
        idempotency_key='',
    ):
        prompt_version = PromptRegistryService.resolve_prompt_version(
            tenant_id=tenant_id,
            module_scope=module_scope,
            use_case_key=use_case_key,
        )
        if not prompt_version:
            raise ValueError(f'No active prompt version is configured for {module_scope}:{use_case_key}.')

        if idempotency_key:
            existing_request = AIExecutionRequest.objects.filter(idempotency_key=idempotency_key).first()
            if existing_request:
                return existing_request, False

        try:
            with transaction.atomic():
                request = AIExecutionRequest.objects.create(
                    tenant_id=tenant_id,
                    created_by=created_by,
                    module_scope=module_scope,
                    use_case_key=use_case_key,
                    source_module=source_module,
                    source_entity_type=source_entity_type,
                    source_entity_id=str(source_entity_id),
                    source_event=source_event,
                    prompt_version=prompt_version,
                    context_snapshot_json=AIExecutionService._sanitize_json(context_snapshot or {}),
                    mode=mode,
                    requires_review=requires_review,
                    requires_approval=requires_approval,
                    status=AIExecutionStatus.QUEUED,
                    idempotency_key=idempotency_key or '',
                )
                created = True
        except IntegrityError:
            if not idempotency_key:
                raise
            request = AIExecutionRequest.objects.get(idempotency_key=idempotency_key)
            created = False

        if created and (requires_review or requires_approval or mode == ApprovalMode.APPROVAL_REQUIRED):
            AIExecutionReview.objects.get_or_create(
                request=request,
                defaults={
                    'tenant_id': tenant_id,
                    'created_by': created_by,
                    'review_status': ReviewStatus.PENDING,
                    'application_status': ApplicationStatus.PENDING,
                },
            )
        if created:
            AuditService.log(
                tenant_id=tenant_id,
                actor_id=created_by,
                actor_type='system' if created_by is None else 'user',
                action_type='ai_execution.created',
                target_type='ai_execution_request',
                target_id=request.id,
                after_state_json={'status': request.status, 'use_case_key': use_case_key, 'source_event': source_event},
            )
        return request, created

    @staticmethod
    def mark_running(request):
        request.status = AIExecutionStatus.RUNNING
        request.started_at = timezone.now()
        request.save(update_fields=['status', 'started_at', 'updated_at'])
        AuditService.log(
            tenant_id=request.tenant_id,
            actor_id=request.created_by,
            actor_type='system',
            action_type='ai_execution.running',
            target_type='ai_execution_request',
            target_id=request.id,
            after_state_json={'status': request.status},
        )
        return request

    @staticmethod
    def _sanitize_json(value):
        if isinstance(value, dict):
            return {str(key): AIExecutionService._sanitize_json(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [AIExecutionService._sanitize_json(item) for item in value]
        if hasattr(value, 'isoformat') and not isinstance(value, (str, bytes)):
            try:
                return value.isoformat()
            except TypeError:
                pass
        if hasattr(value, 'hex') and value.__class__.__name__ == 'UUID':
            return str(value)
        return value

    @staticmethod
    @transaction.atomic
    def execute_request_by_id(*, execution_request_id):
        request = AIExecutionRequest.objects.select_related('prompt_version').get(pk=execution_request_id)
        if request.status not in {AIExecutionStatus.QUEUED, AIExecutionStatus.FAILED, AIExecutionStatus.PARTIAL}:
            return request

        AIExecutionService.mark_running(request)
        started_at = timezone.now()
        prompt_version = PromptRegistryService.resolve_prompt_version(
            tenant_id=request.tenant_id,
            module_scope=request.module_scope,
            use_case_key=request.use_case_key,
            request_prompt_version=request.prompt_version,
        )
        if not prompt_version:
            raise ValueError('No prompt version is available for execution.')

        rendered_prompt = PromptRegistryService.render_prompt(
            prompt_version=prompt_version,
            context_snapshot=request.context_snapshot_json,
        )
        route = ProviderRouter.resolve(
            tenant_id=request.tenant_id,
            module_scope=request.module_scope,
            use_case_key=request.use_case_key,
        )
        request.provider = route.provider
        request.model = route.model
        request.mode = route.approval_mode or request.mode
        request.requires_approval = request.requires_approval or request.mode == ApprovalMode.APPROVAL_REQUIRED
        request.save(update_fields=['provider', 'model', 'mode', 'requires_approval', 'updated_at'])

        try:
            execution = ProviderRouter.execute_with_fallback(
                route=route,
                prompt_version=prompt_version,
                rendered_prompt=rendered_prompt,
                context_snapshot={
                    **(request.context_snapshot_json or {}),
                    'module_scope': request.module_scope,
                    'use_case_key': request.use_case_key,
                    'source_entity_type': request.source_entity_type,
                },
            )
        except ProviderExecutionError as exc:
            AIExecutionService.mark_failed(
                request=request,
                failure_category=exc.category,
                failure_reason=str(exc),
                retryable=exc.retryable,
            )
            raise

        if execution.get('provider_id') and execution.get('provider_id') != getattr(request.provider, 'id', None):
            request.provider_id = execution['provider_id']
        if execution.get('model_id') and execution.get('model_id') != getattr(request.model, 'id', None):
            request.model_id = execution['model_id']
        if request.provider_id or request.model_id:
            request.save(update_fields=['provider', 'model', 'updated_at'])

        result, _ = AIExecutionResult.objects.update_or_create(
            request=request,
            defaults={
                'tenant_id': request.tenant_id,
                'created_by': request.created_by,
                'raw_response_ref': execution.get('raw_response_ref', ''),
                'normalized_output_json': execution['normalized_output_json'],
                'validation_status': ValidationStatus.VALID if execution['validation_passed'] else ValidationStatus.INVALID,
                'confidence_score': AIExecutionService._extract_confidence_score(execution),
                'execution_ms': int((timezone.now() - started_at).total_seconds() * 1000),
                'schema_errors_json': execution.get('schema_errors_json', []),
            },
        )

        if request.requires_review or request.requires_approval or request.mode == ApprovalMode.APPROVAL_REQUIRED:
            review, _ = AIExecutionReview.objects.get_or_create(
                request=request,
                defaults={
                    'tenant_id': request.tenant_id,
                    'created_by': request.created_by,
                },
            )
            review.review_status = ReviewStatus.PENDING
            review.application_status = ApplicationStatus.PENDING
            review.save(update_fields=['review_status', 'application_status', 'updated_at'])

        if request.requires_approval or request.mode == ApprovalMode.APPROVAL_REQUIRED:
            ApprovalQueueItem.objects.get_or_create(
                tenant_id=request.tenant_id,
                origin_type='ai_execution',
                origin_id=request.id,
                requested_action='apply_ai_output',
                defaults={
                    'created_by': request.created_by,
                    'item_type': 'ai_output',
                    'summary_payload_json': execution['normalized_output_json'],
                    'recommended_decision': 'approve',
                    'approver_role': 'tenant_admin',
                    'status': ApprovalStatus.PENDING,
                },
            )
            request.status = AIExecutionStatus.REQUIRES_REVIEW
            request.final_disposition = 'awaiting_approval'
        elif not execution['validation_passed'] or request.requires_review:
            request.status = AIExecutionStatus.REQUIRES_REVIEW
            request.final_disposition = 'awaiting_review'
        else:
            request.status = AIExecutionStatus.COMPLETED
            request.final_disposition = 'completed'

        request.completed_at = timezone.now()
        request.failure_category = ''
        request.failure_reason = ''
        request.save(
            update_fields=[
                'status',
                'final_disposition',
                'completed_at',
                'failure_category',
                'failure_reason',
                'updated_at',
            ]
        )
        if result.validation_status == ValidationStatus.VALID:
            AIExecutionService._maybe_create_suggestion_from_completed_request(request=request)
        AuditService.log(
            tenant_id=request.tenant_id,
            actor_id=request.created_by,
            actor_type='system',
            action_type='ai_execution.completed',
            target_type='ai_execution_request',
            target_id=request.id,
            after_state_json={'status': request.status, 'final_disposition': request.final_disposition},
            metadata_json={'validation_status': result.validation_status},
        )
        return request

    @staticmethod
    def mark_failed(*, request, failure_category, failure_reason, retryable=True):
        request.status = AIExecutionStatus.FAILED
        request.completed_at = timezone.now()
        request.failure_category = failure_category
        request.failure_reason = failure_reason
        request.save(update_fields=['status', 'completed_at', 'failure_category', 'failure_reason', 'updated_at'])
        ExecutionFailure.objects.create(
            tenant_id=request.tenant_id,
            created_by=request.created_by,
            failure_type='ai_execution',
            related_request_id=request.id,
            category=failure_category,
            retryable=retryable,
            max_retries=request.max_retries,
            last_error_message=failure_reason,
        )
        AuditService.log(
            tenant_id=request.tenant_id,
            actor_id=request.created_by,
            actor_type='system',
            action_type='ai_execution.failed',
            target_type='ai_execution_request',
            target_id=request.id,
            after_state_json={'status': request.status, 'failure_category': failure_category},
        )
        return request

    @staticmethod
    def queue_for_retry(*, request):
        if request.status == AIExecutionStatus.CANCELLED:
            raise ValueError('Cancelled AI executions cannot be retried.')
        if request.retry_count >= request.max_retries:
            raise ValueError('AI execution has reached max retries.')
        request.retry_count += 1
        request.status = AIExecutionStatus.QUEUED
        request.completed_at = None
        request.failure_category = ''
        request.failure_reason = ''
        request.save(update_fields=['retry_count', 'status', 'completed_at', 'failure_category', 'failure_reason', 'updated_at'])
        AuditService.log(
            tenant_id=request.tenant_id,
            actor_id=request.created_by,
            actor_type='system',
            action_type='ai_execution.retry_scheduled',
            target_type='ai_execution_request',
            target_id=request.id,
            after_state_json={'status': request.status, 'retry_count': request.retry_count},
        )
        return request
