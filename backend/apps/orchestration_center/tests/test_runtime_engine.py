import uuid
from types import SimpleNamespace
from unittest.mock import patch

from celery.exceptions import Retry
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core import events
from apps.communications.models import Notification
from apps.agencies.models import AgencyClientRelationship, AgencyJobAssignment
from apps.agencies.services import AgencyAssignmentService
from apps.candidates.models import Candidate, CandidateEngagement, CandidateTimelineEvent
from apps.pipeline.models import ActionDeadline, Application
from apps.pipeline.services import PipelineDeadlineService
from apps.orchestration_center.constants.execution_statuses import (
    AIExecutionStatus,
    ApprovalMode,
    ApprovalStatus,
    AutomationExecutionStatus,
    AutomationRuleStatus,
    FailureStatus,
    PromptStatus,
    ProviderStatus,
)
from apps.orchestration_center.models import (
    AIExecutionRequest,
    AIExecutionResult,
    AIModel,
    AIProvider,
    AISuggestion,
    ApprovalQueueItem,
    AutomationExecutionRun,
    AutomationRule,
    DeadLetterItem,
    ExecutionFailure,
    IntelligenceAuditLog,
    ModelRoutingRule,
    PromptTemplate,
    PromptVersion,
    ProviderConfig,
    TenantIntelligenceSettings,
)
from apps.interviews.models import InterviewReviewTask
from apps.orchestration_center.services.ai_execution_service import AIExecutionService
from apps.orchestration_center.services.provider_router import ProviderExecutionError, ProviderRouter
from apps.orchestration_center.services.runtime_event_service import IntelligenceRuntimeEventService
from apps.orchestration_center.services.automation_rule_service import AutomationRuleService
from apps.orchestration_center.tasks.ai_tasks import execute_ai_request
from apps.communications.models import EmailTemplateDefinition


class OrchestrationCenterRuntimeTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        self.other_tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000002')
        self.user_id = uuid.UUID('00000000-0000-0000-0000-000000000010')
        self._setup_tenant_runtime(self.tenant_id)
        self._setup_tenant_runtime(self.other_tenant_id, enable_ai=False, enable_automation=False)

    def _setup_tenant_runtime(self, tenant_id, *, enable_ai=True, enable_automation=True, approval_mode=ApprovalMode.SUGGESTION_ONLY):
        provider = AIProvider.objects.create(
            tenant_id=tenant_id,
            created_by=self.user_id,
            provider_key=f'mock-{tenant_id}',
            provider_name=f'Mock {tenant_id}',
            provider_type=AIProvider.ProviderType.LOCAL,
            status=ProviderStatus.ACTIVE,
            priority_order=1,
            supports_structured_output=True,
        )
        model = AIModel.objects.create(
            tenant_id=tenant_id,
            created_by=self.user_id,
            provider=provider,
            model_key='mock-model',
            model_name='Mock Model',
            capability_type='text_generation',
            status=ProviderStatus.ACTIVE,
            supports_json_schema=True,
        )
        ProviderConfig.objects.create(
            tenant_id=tenant_id,
            created_by=self.user_id,
            provider=provider,
            environment=ProviderConfig.Environment.DEV,
            credential_ref='MOCK_API_KEY',
            allowed_use_cases_json=[],
            is_active=True,
        )
        settings = TenantIntelligenceSettings.objects.create(
            tenant_id=tenant_id,
            created_by=self.user_id,
            updated_by_id=self.user_id,
            ai_enabled=enable_ai,
            automation_enabled=enable_automation,
            default_approval_mode=approval_mode,
            connector_enablement_json={'jobs': True, 'pipeline': True, 'interviews': True, 'agencies': True},
        )
        EmailTemplateDefinition.objects.create(
            tenant_id=tenant_id,
            template_scope='tenant_custom',
            template_type='business',
            channel='email',
            name='Automation Followup',
            slug='followup',
            category='automation',
            subject_template='Follow up for {{ source_entity_type }}',
            body_html='<p>Follow up for {{ source_entity_id }}</p>',
            body_text='Follow up for {{ source_entity_id }}',
            variables_schema_json={},
            usage_context_json={},
            is_active=True,
            is_system_locked=False,
            language_code='en',
            version=1,
            created_by=self.user_id,
        )
        use_cases = {
            'jobs': ['job_enrichment', 'candidate_matching'],
            'pipeline': ['candidate_ranking', 'stage_recommendation', 'shortlist_summary'],
            'interviews': ['interview_summary', 'decision_assist', 'decision_quality_check'],
            'communications': ['email_draft', 'followup_recommendation'],
            'agencies': ['submission_intake_summary'],
        }
        for module_scope, module_use_cases in use_cases.items():
            for use_case_key in module_use_cases:
                template = PromptTemplate.objects.create(
                    tenant_id=tenant_id,
                    created_by=self.user_id,
                    prompt_key=f'{module_scope}-{use_case_key}',
                    prompt_title=f'{module_scope} {use_case_key}',
                    module_scope=module_scope,
                    use_case_key=use_case_key,
                    status=PromptStatus.ACTIVE,
                    approval_required=approval_mode == ApprovalMode.APPROVAL_REQUIRED,
                )
                version = PromptVersion.objects.create(
                    tenant_id=tenant_id,
                    created_by=self.user_id,
                    prompt_template=template,
                    version_number=1,
                    status=PromptStatus.ACTIVE,
                    system_prompt='You are a structured assistant for {job.title}{application.id}{interview.id}.',
                    user_prompt_template='Handle {module_scope} {use_case_key} for {source_entity_id}.',
                    variables_schema_json={},
                    expected_output_schema_json={'type': 'object', 'properties': {'summary': {'type': 'string'}}},
                    approval_required=approval_mode == ApprovalMode.APPROVAL_REQUIRED,
                )
                template.active_version_id = version.id
                template.save(update_fields=['active_version_id', 'updated_at'])
                ModelRoutingRule.objects.create(
                    tenant_id=tenant_id,
                    created_by=self.user_id,
                    module_scope=module_scope,
                    use_case_key=use_case_key,
                    primary_provider=provider,
                    primary_model=model,
                    approval_mode=approval_mode,
                    status=ProviderStatus.ACTIVE,
                )
        return settings, provider, model

    def _create_rule(self, *, tenant_id=None, trigger_event='job.created', module_scope='jobs', rule_key='rule-job-created'):
        return AutomationRule.objects.create(
            tenant_id=tenant_id or self.tenant_id,
            created_by=self.user_id,
            rule_key=rule_key,
            rule_title='Create notification',
            module_scope=module_scope,
            trigger_event=trigger_event,
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )

    def test_event_dispatch_creates_ai_and_automation_runs(self):
        rule = self._create_rule()
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={'channel': 'in_app', 'message': 'Job created'},
        )

        with patch('apps.orchestration_center.services.runtime_event_service.execute_ai_request.delay') as ai_delay, patch(
            'apps.orchestration_center.services.runtime_event_service.execute_automation_rule.delay'
        ) as automation_delay:
            result = IntelligenceRuntimeEventService.dispatch(
                event_name='job.created',
                actor_id=self.user_id,
                payload={'tenant_id': self.tenant_id, 'source_entity_id': 'job-1', 'job': {'id': 'job-1', 'title': 'Demo Job'}},
            )

        self.assertEqual(len(result['ai_requests']), 1)
        self.assertEqual(len(result['automation_runs']), 1)
        self.assertEqual(AIExecutionRequest.objects.filter(tenant_id=self.tenant_id, source_event='job.created').count(), 1)
        self.assertEqual(AutomationExecutionRun.objects.filter(tenant_id=self.tenant_id, source_event='job.created').count(), 1)
        ai_delay.assert_called_once()
        automation_delay.assert_called_once()

    def test_duplicate_event_dispatch_reuses_existing_runs(self):
        rule = self._create_rule(rule_key='rule-job-duplicate')
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={'channel': 'email', 'message': 'Duplicate safe'},
        )

        payload = {'tenant_id': self.tenant_id, 'source_entity_id': 'job-dup', 'job': {'id': 'job-dup', 'title': 'Duplicate'}}
        with patch('apps.orchestration_center.services.runtime_event_service.execute_ai_request.delay'), patch(
            'apps.orchestration_center.services.runtime_event_service.execute_automation_rule.delay'
        ):
            first = IntelligenceRuntimeEventService.dispatch(event_name='job.created', actor_id=self.user_id, payload=payload)
            second = IntelligenceRuntimeEventService.dispatch(event_name='job.created', actor_id=self.user_id, payload=payload)

        self.assertEqual(AIExecutionRequest.objects.filter(tenant_id=self.tenant_id, source_event='job.created').count(), 1)
        self.assertEqual(AutomationExecutionRun.objects.filter(tenant_id=self.tenant_id, source_event='job.created').count(), 1)
        self.assertTrue(first['ai_requests'][0]['created'])
        self.assertFalse(second['ai_requests'][0]['created'])
        self.assertTrue(first['automation_runs'][0]['created'])
        self.assertFalse(second['automation_runs'][0]['created'])

    def test_retry_flow_respects_limits_and_moves_to_dead_letter(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='jobs',
            use_case_key='job_enrichment',
            source_module='jobs',
            source_entity_type='job_requisition',
            source_entity_id='job-retry',
            source_event='job.created',
            context_snapshot={'job': {'title': 'Retry Job'}},
            idempotency_key='retry-test-request',
        )
        request.max_retries = 0
        request.save(update_fields=['max_retries', 'updated_at'])

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            side_effect=ProviderExecutionError('Hard failure', retryable=False, category='provider_unavailable'),
        ):
            result = execute_ai_request.run(str(request.id))
        request.refresh_from_db()

        self.assertEqual(DeadLetterItem.objects.filter(related_object_id=request.id, item_type='ai_execution').count(), 1)
        self.assertIn('dead_letter_id', result)

    def test_retry_flow_raises_retry_when_retryable_and_below_limit(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='jobs',
            use_case_key='job_enrichment',
            source_module='jobs',
            source_entity_type='job_requisition',
            source_entity_id='job-retry-limit',
            source_event='job.created',
            context_snapshot={'job': {'title': 'Retry Limit Job'}},
            idempotency_key='retry-limit-request',
        )
        request.max_retries = 2
        request.save(update_fields=['max_retries', 'updated_at'])

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            side_effect=ProviderExecutionError('Primary timeout', retryable=True, category='provider_timeout'),
        ), patch.object(execute_ai_request, 'retry', side_effect=Retry()):
            with self.assertRaises(Retry):
                execute_ai_request.run(str(request.id))

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.QUEUED)
        self.assertEqual(request.retry_count, 1)

    def test_provider_fallback_executes_when_primary_fails(self):
        primary_provider = AIProvider.objects.get(tenant_id=self.tenant_id, priority_order=1)
        primary_model = AIModel.objects.get(tenant_id=self.tenant_id, provider=primary_provider)
        fallback_provider = AIProvider.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            provider_key='demo',
            provider_name='Demo Fallback',
            provider_type=AIProvider.ProviderType.LOCAL,
            status=ProviderStatus.ACTIVE,
            priority_order=2,
        )
        fallback_model = AIModel.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            provider=fallback_provider,
            model_key='demo-model',
            model_name='Demo Model',
            capability_type='text_generation',
            status=ProviderStatus.ACTIVE,
            supports_json_schema=True,
        )
        ProviderConfig.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            provider=fallback_provider,
            environment=ProviderConfig.Environment.DEV,
            credential_ref='MOCK_FALLBACK_KEY',
            is_active=True,
        )
        routing_rule = ModelRoutingRule.objects.get(tenant_id=self.tenant_id, module_scope='jobs', use_case_key='job_enrichment')
        routing_rule.fallback_chain_json = [{'provider_id': str(fallback_provider.id), 'model_id': str(fallback_model.id)}]
        routing_rule.save(update_fields=['fallback_chain_json', 'updated_at'])

        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='jobs',
            use_case_key='job_enrichment',
            source_module='jobs',
            source_entity_type='job_requisition',
            source_entity_id='job-fallback',
            source_event='job.created',
            context_snapshot={'job': {'title': 'Fallback Job'}},
            idempotency_key='fallback-request',
        )

        original_execute = ProviderRouter._execute

        def fail_primary_then_fallback(*, provider, model, config, prompt_version, rendered_prompt, context_snapshot):
            if provider.id == primary_provider.id:
                raise ProviderExecutionError('Primary failed', retryable=True, category='provider_timeout')
            return original_execute(
                provider=provider,
                model=model,
                config=config,
                prompt_version=prompt_version,
                rendered_prompt=rendered_prompt,
                context_snapshot=context_snapshot,
            )

        with patch('apps.orchestration_center.services.provider_router.ProviderRouter._execute', side_effect=fail_primary_then_fallback):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertEqual(request.provider_id, fallback_provider.id)
        self.assertEqual(request.model_id, fallback_model.id)
        self.assertTrue(AIExecutionResult.objects.filter(request=request).exists())

    def test_tenant_isolation_is_preserved(self):
        self._create_rule(tenant_id=self.other_tenant_id, rule_key='other-tenant-rule')
        with patch('apps.orchestration_center.services.runtime_event_service.execute_ai_request.delay'), patch(
            'apps.orchestration_center.services.runtime_event_service.execute_automation_rule.delay'
        ):
            result = IntelligenceRuntimeEventService.dispatch(
                event_name='job.created',
                actor_id=self.user_id,
                payload={'tenant_id': self.tenant_id, 'source_entity_id': 'job-tenant', 'job': {'id': 'job-tenant', 'title': 'Tenant Job'}},
            )

        self.assertEqual(AIExecutionRequest.objects.filter(tenant_id=self.tenant_id).count(), 1)
        self.assertEqual(AIExecutionRequest.objects.filter(tenant_id=self.other_tenant_id).count(), 0)
        self.assertEqual(AutomationExecutionRun.objects.filter(tenant_id=self.other_tenant_id).count(), 0)
        self.assertEqual(result['tenant_id'], str(self.tenant_id))

    def test_originating_business_event_is_not_blocked_when_orchestration_fails(self):
        requisition = SimpleNamespace(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            title='Failure Safe Job',
            status='draft',
            employment_type='full_time',
            work_mode='remote',
            department='Engineering',
        )
        with patch(
            'apps.orchestration_center.services.runtime_event_service.IntelligenceRuntimeEventService.dispatch',
            side_effect=RuntimeError('dispatch failed'),
        ):
            events.job.created.send(sender=self.__class__, requisition=requisition, user=None, request=None)

        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                action_type='runtime_event.consumer_failed',
            ).exists()
        )

    def test_approval_required_flows_stay_gated(self):
        TenantIntelligenceSettings.objects.filter(tenant_id=self.tenant_id).update(default_approval_mode=ApprovalMode.APPROVAL_REQUIRED)
        ModelRoutingRule.objects.filter(tenant_id=self.tenant_id, module_scope='jobs', use_case_key='job_enrichment').update(
            approval_mode=ApprovalMode.APPROVAL_REQUIRED
        )
        PromptTemplate.objects.filter(tenant_id=self.tenant_id, module_scope='jobs', use_case_key='job_enrichment').update(
            approval_required=True
        )

        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='jobs',
            use_case_key='job_enrichment',
            source_module='jobs',
            source_entity_type='job_requisition',
            source_entity_id='job-approval',
            source_event='job.created',
            context_snapshot={'job': {'title': 'Approval Job'}},
            mode=ApprovalMode.APPROVAL_REQUIRED,
            requires_review=True,
            requires_approval=True,
            idempotency_key='approval-required-request',
        )

        AIExecutionService.execute_request_by_id(execution_request_id=request.id)
        request.refresh_from_db()

        self.assertEqual(request.status, AIExecutionStatus.REQUIRES_REVIEW)
        self.assertEqual(request.final_disposition, 'awaiting_approval')
        self.assertTrue(
            ApprovalQueueItem.objects.filter(
                tenant_id=self.tenant_id,
                origin_type='ai_execution',
                origin_id=request.id,
                status=ApprovalStatus.PENDING,
            ).exists()
        )

    def test_email_draft_execution_creates_communication_draft_suggestion(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='email_draft',
            source_module='communications',
            source_entity_type='message_thread',
            source_entity_id='thread-1',
            source_event='message.sent',
            context_snapshot={'message': {'subject': 'Need follow up'}},
            idempotency_key='email-draft-suggestion-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'subject': 'Follow-up on your request',
                    'body': 'Thanks for your message. Here is a draft reply.',
                    'confidence_score': 0.91,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        suggestion = AISuggestion.objects.get(ai_request=request)
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertEqual(suggestion.category, 'communication_draft')
        self.assertEqual(suggestion.owner_module, 'communications')
        self.assertEqual(suggestion.proposed_action_family, 'enqueue_communication')
        self.assertEqual(suggestion.payload_json['suggestion_subtype'], 'email_draft')
        self.assertEqual(suggestion.payload_json['subject'], 'Follow-up on your request')
        self.assertEqual(str(suggestion.confidence_score), '0.91')

    def test_email_draft_suggestion_creation_is_duplicate_safe(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='email_draft',
            source_module='communications',
            source_entity_type='message_thread',
            source_entity_id='thread-dup',
            source_event='message.sent',
            context_snapshot={},
            idempotency_key='email-draft-duplicate-request',
        )
        AIExecutionResult.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            request=request,
            normalized_output_json={'subject': 'Hello', 'body': 'Draft body'},
            validation_status='valid',
            confidence_score='0.88',
        )

        first = AIExecutionService._maybe_create_suggestion_from_completed_request(request=request)
        second = AIExecutionService._maybe_create_suggestion_from_completed_request(request=request)

        self.assertEqual(first[2], 'created')
        self.assertEqual(second[2], 'duplicate')
        self.assertEqual(AISuggestion.objects.filter(ai_request=request).count(), 1)

    def test_email_draft_invalid_output_is_skipped_non_blockingly(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='email_draft',
            source_module='communications',
            source_entity_type='message_thread',
            source_entity_id='thread-invalid',
            source_event='message.sent',
            context_snapshot={},
            idempotency_key='email-draft-invalid-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'subject': '',
                    'body': 'Body exists but subject is blank',
                    'confidence_score': 0.77,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertFalse(AISuggestion.objects.filter(ai_request=request).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_execution_request',
                target_id=request.id,
                action_type='ai_suggestion.skipped',
            ).exists()
        )

    def test_email_draft_suggestion_creation_preserves_tenant_isolation(self):
        other_request, _ = AIExecutionService.create_request(
            tenant_id=self.other_tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='email_draft',
            source_module='communications',
            source_entity_type='message_thread',
            source_entity_id='thread-other-tenant',
            source_event='message.sent',
            context_snapshot={},
            idempotency_key='email-draft-other-tenant',
        )
        AIExecutionResult.objects.create(
            tenant_id=self.other_tenant_id,
            created_by=self.user_id,
            request=other_request,
            normalized_output_json={'subject': 'Other tenant', 'body': 'Draft'},
            validation_status='valid',
            confidence_score='0.83',
        )

        suggestion, created, outcome = AIExecutionService._maybe_create_suggestion_from_completed_request(request=other_request)

        self.assertTrue(created)
        self.assertEqual(outcome, 'created')
        self.assertEqual(suggestion.tenant_id, self.other_tenant_id)
        self.assertEqual(AISuggestion.objects.filter(tenant_id=self.tenant_id, ai_request=other_request).count(), 0)

    def test_email_draft_suggestion_failure_is_non_blocking(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='email_draft',
            source_module='communications',
            source_entity_type='message_thread',
            source_entity_id='thread-failure',
            source_event='message.sent',
            context_snapshot={},
            idempotency_key='email-draft-failure-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'subject': 'Failure-safe draft',
                    'body': 'Body',
                    'confidence_score': 0.79,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ), patch(
            'apps.orchestration_center.services.ai_execution_service.SuggestionService.create_supported_suggestion_from_ai_execution',
            side_effect=RuntimeError('suggestion mapping blew up'),
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertFalse(AISuggestion.objects.filter(ai_request=request).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_execution_request',
                target_id=request.id,
                action_type='ai_suggestion.generation_failed',
            ).exists()
        )

    def test_followup_recommendation_execution_creates_suggestion(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='followup_recommendation',
            source_module='communications',
            source_entity_type='candidate',
            source_entity_id='candidate-1',
            source_event='candidate.updated',
            context_snapshot={'candidate': {'last_activity_hours': 72}},
            idempotency_key='followup-recommendation-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'summary': 'Candidate has been idle for 72 hours; send a follow-up email.',
                    'reason': 'Recent engagement dropped after initial outreach.',
                    'channel': 'email',
                    'followup_type': 'candidate_followup',
                    'template_key': 'followup',
                    'delay_hours': 24,
                    'recipient_hint': 'candidate',
                    'signals': ['inactive_72h', 'awaiting_reply'],
                    'decision_factors': ['no_recent_response', 'pipeline_stall_risk'],
                    'confidence_score': 0.86,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        suggestion = AISuggestion.objects.get(ai_request=request)
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertEqual(suggestion.category, 'followup_recommendation')
        self.assertEqual(suggestion.owner_module, 'communications')
        self.assertEqual(suggestion.proposed_action_family, 'enqueue_communication')
        self.assertEqual(suggestion.payload_json['suggestion_subtype'], 'followup_recommendation')
        self.assertEqual(suggestion.payload_json['followup_type'], 'candidate_followup')
        self.assertEqual(suggestion.payload_json['delay_hours'], 24)
        self.assertEqual(suggestion.payload_json['recipient_hint'], 'candidate')
        self.assertEqual(suggestion.rationale_json['reason'], 'Recent engagement dropped after initial outreach.')
        self.assertEqual(str(suggestion.confidence_score), '0.86')

    def test_followup_recommendation_suggestion_creation_is_duplicate_safe(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='followup_recommendation',
            source_module='communications',
            source_entity_type='candidate',
            source_entity_id='candidate-dup',
            source_event='candidate.updated',
            context_snapshot={},
            idempotency_key='followup-recommendation-duplicate-request',
        )
        AIExecutionResult.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            request=request,
            normalized_output_json={
                'summary': 'Send a follow-up email to candidate.',
                'reason': 'No response in 48 hours.',
                'followup_type': 'candidate_followup',
            },
            validation_status='valid',
            confidence_score='0.74',
        )

        first = AIExecutionService._maybe_create_suggestion_from_completed_request(request=request)
        second = AIExecutionService._maybe_create_suggestion_from_completed_request(request=request)

        self.assertEqual(first[2], 'created')
        self.assertEqual(second[2], 'duplicate')
        self.assertEqual(AISuggestion.objects.filter(ai_request=request).count(), 1)

    def test_followup_recommendation_invalid_output_is_skipped_non_blockingly(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='followup_recommendation',
            source_module='communications',
            source_entity_type='candidate',
            source_entity_id='candidate-invalid',
            source_event='candidate.updated',
            context_snapshot={},
            idempotency_key='followup-recommendation-invalid-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'summary': '   ',
                    'reason': '',
                    'followup_type': 'candidate_followup',
                    'confidence_score': 0.72,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertFalse(AISuggestion.objects.filter(ai_request=request).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_execution_request',
                target_id=request.id,
                action_type='ai_suggestion.skipped',
            ).exists()
        )

    def test_followup_recommendation_low_confidence_output_is_skipped_non_blockingly(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='followup_recommendation',
            source_module='communications',
            source_entity_type='candidate',
            source_entity_id='candidate-low-confidence',
            source_event='candidate.updated',
            context_snapshot={},
            idempotency_key='followup-recommendation-low-confidence-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'summary': 'Send a follow-up reminder.',
                    'reason': 'Candidate may be drifting.',
                    'followup_type': 'candidate_followup',
                    'confidence_score': 0.21,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertFalse(AISuggestion.objects.filter(ai_request=request).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_execution_request',
                target_id=request.id,
                action_type='ai_suggestion.skipped',
            ).exists()
        )

    def test_followup_recommendation_suggestion_creation_preserves_tenant_isolation(self):
        other_request, _ = AIExecutionService.create_request(
            tenant_id=self.other_tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='followup_recommendation',
            source_module='communications',
            source_entity_type='candidate',
            source_entity_id='candidate-other-tenant',
            source_event='candidate.updated',
            context_snapshot={},
            idempotency_key='followup-recommendation-other-tenant',
        )
        AIExecutionResult.objects.create(
            tenant_id=self.other_tenant_id,
            created_by=self.user_id,
            request=other_request,
            normalized_output_json={
                'summary': 'Other tenant candidate needs a follow-up.',
                'reason': 'Reply SLA exceeded.',
                'followup_type': 'candidate_followup',
            },
            validation_status='valid',
            confidence_score='0.81',
        )

        suggestion, created, outcome = AIExecutionService._maybe_create_suggestion_from_completed_request(request=other_request)

        self.assertTrue(created)
        self.assertEqual(outcome, 'created')
        self.assertEqual(suggestion.tenant_id, self.other_tenant_id)
        self.assertEqual(AISuggestion.objects.filter(tenant_id=self.tenant_id, ai_request=other_request).count(), 0)

    def test_followup_recommendation_suggestion_failure_is_non_blocking(self):
        request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='communications',
            use_case_key='followup_recommendation',
            source_module='communications',
            source_entity_type='candidate',
            source_entity_id='candidate-failure',
            source_event='candidate.updated',
            context_snapshot={},
            idempotency_key='followup-recommendation-failure-request',
        )

        with patch(
            'apps.orchestration_center.services.ai_execution_service.ProviderRouter.execute_with_fallback',
            return_value={
                'raw_response_ref': '',
                'normalized_output_json': {
                    'summary': 'Follow up with candidate.',
                    'reason': 'Response window elapsed.',
                    'followup_type': 'candidate_followup',
                    'confidence_score': 0.79,
                },
                'validation_passed': True,
                'schema_errors_json': [],
            },
        ), patch(
            'apps.orchestration_center.services.ai_execution_service.SuggestionService.create_supported_suggestion_from_ai_execution',
            side_effect=RuntimeError('followup suggestion mapping blew up'),
        ):
            AIExecutionService.execute_request_by_id(execution_request_id=request.id)

        request.refresh_from_db()
        self.assertEqual(request.status, AIExecutionStatus.COMPLETED)
        self.assertFalse(AISuggestion.objects.filter(ai_request=request).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_type='ai_execution_request',
                target_id=request.id,
                action_type='ai_suggestion.generation_failed',
            ).exists()
        )

    def test_richer_automation_actions_record_structured_results(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-extended-actions',
            rule_title='Runtime Extended Actions',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={'channel': 'in_app', 'notification_type': 'reminder_notification', 'title': 'Interview reminder'},
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={'delay_seconds': 60, 'followup_type': 'stage_followup', 'channel': 'email', 'recipient_emails': ['panel@example.com']},
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={'review_type': 'interview_feedback_review', 'owner_module': 'interviews'},
            sequence_order=3,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={'flag_key': 'needs_attention', 'flag_value': True},
            sequence_order=4,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(uuid.uuid4()),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='extended-actions-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertIn(executed_run.status, {AutomationExecutionStatus.SCHEDULED, AutomationExecutionStatus.COMPLETED})
        self.assertSetEqual(
            {item['action_type'] for item in executed_run.action_results_json},
            {'notify', 'schedule_followup', 'create_review_task', 'mark_flag'},
        )
        self.assertTrue(InterviewReviewTask.objects.filter(tenant_id=self.tenant_id).exists())
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id).exists())
        self.assertTrue(executed_run.scheduled_actions.exists())

    def test_schedule_followup_is_duplicate_safe_for_same_run(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-schedule-followup-dedupe',
            rule_title='Runtime Schedule Followup Dedupe',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'feedback_reminder',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_emails': ['panel@example.com'],
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(uuid.uuid4()),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='schedule-followup-dedupe-test',
        )

        first = AutomationRuleService._apply_action(run=run, action=action)
        second = AutomationRuleService._apply_action(run=run, action=action)

        self.assertEqual(first['status'], 'scheduled')
        self.assertEqual(second['status'], 'deduplicated')
        self.assertEqual(first['scheduled_action_id'], second['scheduled_action_id'])
        self.assertEqual(run.scheduled_actions.count(), 1)

    def test_composed_followup_escalation_workflow_executes_end_to_end(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-composed-followup-escalation',
            rule_title='Runtime Composed Followup Escalation',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'feedback_due',
                'action_required': 'Collect interview feedback',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'feedback_reminder',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_emails': ['panel@example.com'],
                'message_purpose': 'candidate_followup',
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'high',
                'reason': 'Feedback still missing after follow-up',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Collect interview feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(uuid.uuid4()),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='composed-followup-escalation-test',
        )

        with patch('apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email') as queue_email:
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            self.assertEqual(executed_run.status, AutomationExecutionStatus.SCHEDULED)
            self.assertEqual(executed_run.scheduled_actions.count(), 2)

            executed_run.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            completed_ids = AutomationRuleService.process_due_scheduled_actions()

        executed_run.refresh_from_db()
        self.assertEqual(len(completed_ids), 2)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        self.assertTrue(queue_email.called)
        scheduled_email_action = executed_run.scheduled_actions.get(action_type='enqueue_communication')
        self.assertTrue(
            any(
                item.get('scheduled_action_id') == str(scheduled_email_action.id)
                and item['action_type'] == 'enqueue_communication'
                and item['status'] in {'queued', 'completed'}
                for item in executed_run.action_results_json
            )
        )
        self.assertTrue(
            any(item['action_type'] == 'escalate' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        deadline = ActionDeadline.objects.get(tenant_id=self.tenant_id, entity_id=entity_id)
        self.assertEqual(deadline.status, 'escalated')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_composed_followup_escalation_workflow_keeps_scheduled_failure_non_blocking(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-composed-followup-escalation-failure',
            rule_title='Runtime Composed Followup Escalation Failure',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'feedback_due',
                'action_required': 'Collect interview feedback',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'feedback_reminder',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_emails': ['panel@example.com'],
                'message_purpose': 'candidate_followup',
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'high',
                'reason': 'Feedback still missing after follow-up',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Collect interview feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(uuid.uuid4()),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='composed-followup-escalation-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.SCHEDULED)
        executed_run.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))

        with patch(
            'apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email',
            side_effect=RuntimeError('scheduled followup delivery unavailable'),
        ):
            completed_ids = AutomationRuleService.process_due_scheduled_actions()

        executed_run.refresh_from_db()
        self.assertEqual(len(completed_ids), 1)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        failed_action = executed_run.scheduled_actions.get(action_type='enqueue_communication')
        self.assertTrue(
            any(
                item.get('scheduled_action_id') == str(failed_action.id)
                and item['action_type'] == 'enqueue_communication'
                and item['status'] == 'failed'
                and item['error_category'] == 'unhandled_runtime_error'
                for item in executed_run.action_results_json
            )
        )
        self.assertTrue(
            any(item['action_type'] == 'escalate' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        self.assertEqual(failed_action.attempt_count, 1)
        self.assertIn('scheduled followup delivery unavailable', failed_action.last_error)
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_candidate_followup_workflow_executes_end_to_end(self):
        candidate_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-candidate-followup-workflow',
            rule_title='Runtime Candidate Followup Workflow',
            module_scope='candidates',
            trigger_event='candidate.updated',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Follow up with candidate',
                'entity_type': 'candidate',
                'entity_id': str(candidate_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'candidate_followup',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['candidate.email'],
                'message_purpose': 'candidate_followup',
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'medium',
                'reason': 'Candidate follow-up still pending',
                'deadline_entity_type': 'candidate',
                'deadline_entity_id': str(candidate_id),
                'deadline_action_required': 'Follow up with candidate',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.updated',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate_id),
            payload={'candidate': {'id': str(candidate_id), 'email': 'candidate@example.com'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='candidate-followup-workflow-test',
        )

        with patch('apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email') as queue_email:
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            self.assertEqual(executed_run.status, AutomationExecutionStatus.SCHEDULED)
            self.assertEqual(executed_run.scheduled_actions.count(), 2)

            executed_run.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            completed_ids = AutomationRuleService.process_due_scheduled_actions()

        executed_run.refresh_from_db()
        self.assertEqual(len(completed_ids), 2)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        self.assertTrue(queue_email.called)
        self.assertTrue(
            any(item['action_type'] == 'create_deadline' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        self.assertTrue(
            any(item['action_type'] == 'enqueue_communication' and item['status'] == 'queued' for item in executed_run.action_results_json)
        )
        self.assertTrue(
            any(item['action_type'] == 'escalate' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        deadline = ActionDeadline.objects.get(tenant_id=self.tenant_id, entity_type='candidate', entity_id=candidate_id)
        self.assertEqual(deadline.status, 'escalated')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_candidate_followup_workflow_retry_and_tenant_isolation_are_duplicate_safe(self):
        candidate_id = uuid.uuid4()
        shared_dedupe = 'candidate-followup-reminder-dedupe'
        Notification.objects.create(
            tenant_id=self.other_tenant_id,
            user_id=self.user_id,
            title='Other tenant escalation',
            body='Ignore',
            notification_type='escalation_alert',
            metadata={
                'external_source': 'orchestration_center',
                'orchestration_dedupe_key': shared_dedupe,
            },
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-candidate-followup-retry',
            rule_title='Runtime Candidate Followup Retry',
            module_scope='candidates',
            trigger_event='candidate.updated',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Follow up with candidate',
                'entity_type': 'candidate',
                'entity_id': str(candidate_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'candidate_followup',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['candidate.email'],
                'message_purpose': 'candidate_followup',
                'dedupe_key': shared_dedupe,
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'medium',
                'reason': 'Candidate follow-up still pending',
                'deadline_entity_type': 'candidate',
                'deadline_entity_id': str(candidate_id),
                'deadline_action_required': 'Follow up with candidate',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
                'dedupe_key': shared_dedupe,
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.updated',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate_id),
            payload={'candidate': {'id': str(candidate_id), 'email': 'candidate@example.com'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='candidate-followup-retry-test',
        )

        with patch('apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email') as queue_email:
            first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            first_initial_status = first.status
            first.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            first_completed = AutomationRuleService.process_due_scheduled_actions()
            first.refresh_from_db()
            first_final_status = first.status
            AutomationRuleService.queue_for_retry(run=first)
            second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            second.scheduled_actions.filter(status='pending').update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            second_completed = AutomationRuleService.process_due_scheduled_actions()

        second.refresh_from_db()
        self.assertEqual(first_initial_status, AutomationExecutionStatus.SCHEDULED)
        self.assertEqual(first_final_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertTrue(queue_email.called)
        self.assertGreaterEqual(len(first_completed), 2)
        self.assertGreaterEqual(len(second_completed), 0)
        self.assertEqual(
            ActionDeadline.objects.filter(
                tenant_id=self.tenant_id,
                entity_type='candidate',
                entity_id=candidate_id,
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.other_tenant_id,
                notification_type='escalation_alert',
                metadata__orchestration_dedupe_key=shared_dedupe,
            ).count(),
            1,
        )

    def test_candidate_followup_workflow_keeps_scheduled_email_failure_non_blocking(self):
        candidate_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-candidate-followup-failure',
            rule_title='Runtime Candidate Followup Failure',
            module_scope='candidates',
            trigger_event='candidate.updated',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Follow up with candidate',
                'entity_type': 'candidate',
                'entity_id': str(candidate_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'candidate_followup',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['candidate.email'],
                'message_purpose': 'candidate_followup',
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'medium',
                'reason': 'Candidate follow-up still pending',
                'deadline_entity_type': 'candidate',
                'deadline_entity_id': str(candidate_id),
                'deadline_action_required': 'Follow up with candidate',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.updated',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate_id),
            payload={'candidate': {'id': str(candidate_id), 'email': 'candidate@example.com'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='candidate-followup-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.SCHEDULED)
        executed_run.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))

        with patch(
            'apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email',
            side_effect=RuntimeError('candidate followup email unavailable'),
        ):
            completed_ids = AutomationRuleService.process_due_scheduled_actions()

        executed_run.refresh_from_db()
        self.assertEqual(len(completed_ids), 1)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertTrue(
            any(
                item['action_type'] == 'enqueue_communication'
                and item['status'] == 'failed'
                and item['error_category'] == 'unhandled_runtime_error'
                for item in executed_run.action_results_json
            )
        )
        self.assertTrue(
            any(item['action_type'] == 'escalate' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_agency_submission_followup_workflow_executes_end_to_end(self):
        application_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-agency-submission-followup-workflow',
            rule_title='Runtime Agency Submission Followup Workflow',
            module_scope='pipeline',
            trigger_event='application.created',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'agency_feedback',
                'action_required': 'Review agency submission feedback',
                'entity_type': 'application',
                'entity_id': str(application_id),
                'due_in_hours': 48,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'agency_submission_followup',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['submission.client_email'],
                'message_purpose': 'agency_submission_update',
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'medium',
                'reason': 'Agency submission feedback still pending',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(application_id),
                'deadline_action_required': 'Review agency submission feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
                'title': 'Agency submission feedback pending',
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.created',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(application_id),
            payload={
                'application': {'id': str(application_id), 'is_agency_submission': True},
                'submission': {'client_email': 'client-feedback@example.com'},
            },
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='agency-submission-followup-workflow-test',
        )

        with patch('apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email') as queue_email:
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            self.assertEqual(executed_run.status, AutomationExecutionStatus.SCHEDULED)
            self.assertEqual(executed_run.scheduled_actions.count(), 2)

            executed_run.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            completed_ids = AutomationRuleService.process_due_scheduled_actions()

        executed_run.refresh_from_db()
        self.assertEqual(len(completed_ids), 2)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        self.assertTrue(queue_email.called)
        self.assertTrue(
            any(item['action_type'] == 'create_deadline' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        self.assertTrue(
            any(item['action_type'] == 'enqueue_communication' and item['status'] == 'queued' for item in executed_run.action_results_json)
        )
        self.assertTrue(
            any(item['action_type'] == 'escalate' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        deadline = ActionDeadline.objects.get(tenant_id=self.tenant_id, entity_type='application', entity_id=application_id)
        self.assertEqual(deadline.status, 'escalated')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_agency_submission_followup_workflow_retry_and_tenant_isolation_are_duplicate_safe(self):
        application_id = uuid.uuid4()
        shared_dedupe = 'agency-submission-followup-dedupe'
        Notification.objects.create(
            tenant_id=self.other_tenant_id,
            user_id=self.user_id,
            title='Other tenant escalation',
            body='Ignore',
            notification_type='escalation_alert',
            metadata={
                'external_source': 'orchestration_center',
                'orchestration_dedupe_key': shared_dedupe,
            },
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-agency-submission-followup-retry',
            rule_title='Runtime Agency Submission Followup Retry',
            module_scope='pipeline',
            trigger_event='application.created',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'agency_feedback',
                'action_required': 'Review agency submission feedback',
                'entity_type': 'application',
                'entity_id': str(application_id),
                'due_in_hours': 48,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'agency_submission_followup',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['submission.client_email'],
                'message_purpose': 'agency_submission_update',
                'dedupe_key': shared_dedupe,
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'medium',
                'reason': 'Agency submission feedback still pending',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(application_id),
                'deadline_action_required': 'Review agency submission feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
                'dedupe_key': shared_dedupe,
                'title': 'Agency submission feedback pending',
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.created',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(application_id),
            payload={
                'application': {'id': str(application_id), 'is_agency_submission': True},
                'submission': {'client_email': 'client-feedback@example.com'},
            },
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='agency-submission-followup-retry-test',
        )

        with patch('apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email') as queue_email:
            first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            first_initial_status = first.status
            first.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            first_completed = AutomationRuleService.process_due_scheduled_actions()
            first.refresh_from_db()
            first_final_status = first.status
            AutomationRuleService.queue_for_retry(run=first)
            second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
            second.scheduled_actions.filter(status='pending').update(execute_at=timezone.now() - timezone.timedelta(seconds=1))
            second_completed = AutomationRuleService.process_due_scheduled_actions()

        second.refresh_from_db()
        self.assertEqual(first_initial_status, AutomationExecutionStatus.SCHEDULED)
        self.assertEqual(first_final_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertTrue(queue_email.called)
        self.assertGreaterEqual(len(first_completed), 2)
        self.assertGreaterEqual(len(second_completed), 0)
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.other_tenant_id,
                notification_type='escalation_alert',
                metadata__orchestration_dedupe_key=shared_dedupe,
            ).count(),
            1,
        )

    def test_agency_submission_followup_workflow_keeps_scheduled_email_failure_non_blocking(self):
        application_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-agency-submission-followup-failure',
            rule_title='Runtime Agency Submission Followup Failure',
            module_scope='pipeline',
            trigger_event='application.created',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'agency_feedback',
                'action_required': 'Review agency submission feedback',
                'entity_type': 'application',
                'entity_id': str(application_id),
                'due_in_hours': 48,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='schedule_followup',
            action_config_json={
                'delay_seconds': 60,
                'followup_type': 'agency_submission_followup',
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['submission.client_email'],
                'message_purpose': 'agency_submission_update',
            },
            sequence_order=2,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'medium',
                'reason': 'Agency submission feedback still pending',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(application_id),
                'deadline_action_required': 'Review agency submission feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
                'title': 'Agency submission feedback pending',
            },
            delay_seconds=120,
            sequence_order=3,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.created',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(application_id),
            payload={
                'application': {'id': str(application_id), 'is_agency_submission': True},
                'submission': {'client_email': 'client-feedback@example.com'},
            },
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='agency-submission-followup-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.SCHEDULED)
        executed_run.scheduled_actions.update(execute_at=timezone.now() - timezone.timedelta(seconds=1))

        with patch(
            'apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email',
            side_effect=RuntimeError('agency followup email unavailable'),
        ):
            completed_ids = AutomationRuleService.process_due_scheduled_actions()

        executed_run.refresh_from_db()
        self.assertEqual(len(completed_ids), 1)
        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertTrue(
            any(
                item['action_type'] == 'enqueue_communication'
                and item['status'] == 'failed'
                and item['error_category'] == 'unhandled_runtime_error'
                for item in executed_run.action_results_json
            )
        )
        self.assertTrue(
            any(item['action_type'] == 'escalate' and item['status'] == 'completed' for item in executed_run.action_results_json)
        )
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_enqueue_communication_uses_stable_email_queue_service(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-enqueue-communication',
            rule_title='Runtime Enqueue Communication',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='enqueue_communication',
            action_config_json={
                'channel': 'email',
                'template_key': 'followup',
                'recipient_paths': ['candidate.email'],
                'message_purpose': 'candidate_followup',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id='APP-1001',
            payload={'candidate': {'email': 'candidate@example.com'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='enqueue-communication-test',
        )

        with patch('apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.queue_email') as queue_email:
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'queued')
        queue_email.assert_called_once()

    def test_enqueue_communication_uses_stable_in_app_notification_contract(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-enqueue-communication-in-app',
            rule_title='Runtime Enqueue Communication In App',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='enqueue_communication',
            action_config_json={
                'channel': 'in_app',
                'title': 'Review candidate',
                'body': 'Please review this application.',
                'notification_type': 'platform_notification',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(uuid.uuid4()),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='enqueue-communication-in-app-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        notification = Notification.objects.get(tenant_id=self.tenant_id, notification_type='platform_notification')
        self.assertEqual(notification.metadata['external_source'], 'orchestration_center')
        self.assertEqual(notification.metadata['notification_style'], 'communication')

    def test_enqueue_communication_in_app_retry_is_duplicate_safe_and_tenant_isolated(self):
        shared_dedupe_key = 'enqueue-in-app-dedupe'
        Notification.objects.create(
            tenant_id=self.other_tenant_id,
            user_id=self.user_id,
            title='Other tenant',
            body='Ignore',
            notification_type='platform_notification',
            metadata={
                'external_source': 'orchestration_center',
                'orchestration_dedupe_key': shared_dedupe_key,
            },
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-enqueue-communication-in-app-retry',
            rule_title='Runtime Enqueue Communication In App Retry',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='enqueue_communication',
            action_config_json={
                'channel': 'in_app',
                'title': 'Review candidate',
                'body': 'Please review this application.',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'dedupe_key': shared_dedupe_key,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(uuid.uuid4()),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='enqueue-communication-in-app-retry-test',
        )

        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.tenant_id,
                notification_type='platform_notification',
                metadata__orchestration_dedupe_key=shared_dedupe_key,
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.other_tenant_id,
                notification_type='platform_notification',
                metadata__orchestration_dedupe_key=shared_dedupe_key,
            ).count(),
            1,
        )

    def test_enqueue_communication_unsupported_channel_remains_stubbed(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-enqueue-communication-sms',
            rule_title='Runtime Enqueue Communication Sms',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='enqueue_communication',
            action_config_json={
                'channel': 'sms',
                'recipient_paths': ['candidate.phone'],
                'message': 'Review needed',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(uuid.uuid4()),
            payload={'candidate': {'phone': '+15555555555'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='enqueue-communication-sms-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=action)

        self.assertEqual(result['status'], 'stubbed_unbound')
        self.assertEqual(result['reason'], 'communication_channel_contract_not_available')
        self.assertEqual(result['channel'], 'sms')

    def test_execute_run_enqueue_communication_in_app_failure_is_non_blocking_and_audited(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-enqueue-communication-in-app-failure',
            rule_title='Runtime Enqueue Communication In App Failure',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='enqueue_communication',
            action_config_json={
                'channel': 'in_app',
                'title': 'Review candidate',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Review application',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='enqueue-communication-in-app-failure-test',
        )

        with patch(
            'apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.dispatch_automation_notification',
            side_effect=RuntimeError('notification downstream unavailable'),
        ):
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(executed_run.action_results_json[1]['status'], 'completed')
        self.assertTrue(ActionDeadline.objects.filter(tenant_id=self.tenant_id, entity_id=entity_id).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_create_deadline_uses_pipeline_owned_contract(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-create-deadline-contract',
            rule_title='Runtime Create Deadline Contract',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Review application',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
                'owner_role': 'recruiter',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='create-deadline-contract-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=action)

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['owner_module'], 'pipeline')
        self.assertEqual(result['action_family'], 'create_deadline')
        self.assertEqual(result['target_type'], 'deadline')
        self.assertFalse(result['duplicate'])
        deadline = ActionDeadline.objects.get(id=result['deadline_id'])
        self.assertEqual(result['target_id'], str(deadline.id))

    def test_create_deadline_retry_is_duplicate_safe(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-create-deadline-retry',
            rule_title='Runtime Create Deadline Retry',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Review application',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='create-deadline-retry-contract-test',
        )

        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.action_results_json[0]['status'], 'deduplicated')
        self.assertTrue(second.action_results_json[0]['duplicate'])
        self.assertEqual(
            ActionDeadline.objects.filter(
                tenant_id=self.tenant_id,
                entity_type='application',
                entity_id=entity_id,
            ).count(),
            1,
        )

    def test_create_deadline_invalid_entity_uses_structured_owner_error(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-create-deadline-invalid',
            rule_title='Runtime Create Deadline Invalid',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Review application',
                'entity_type': 'application',
                'entity_id': 'not-a-uuid',
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(uuid.uuid4()),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='create-deadline-invalid-contract-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(
            executed_run.action_results_json[0]['error_category'],
            'owner_contract_validation',
        )
        self.assertFalse(executed_run.action_results_json[0]['retry_safe'])

    def test_notify_uses_communication_owned_notification_contract(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-notify-contract',
            rule_title='Runtime Notify Contract',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'title': 'Pending review',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(uuid.uuid4()),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='notify-contract-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        notification = Notification.objects.get(tenant_id=self.tenant_id, notification_type='reminder_notification')
        self.assertEqual(notification.metadata['external_source'], 'orchestration_center')
        self.assertEqual(notification.metadata['notification_style'], 'reminder')

    def test_notify_retry_is_duplicate_safe_and_tenant_isolated(self):
        shared_dedupe_key = 'tenant-shared-notify-key'
        Notification.objects.create(
            tenant_id=self.other_tenant_id,
            user_id=self.user_id,
            title='Other tenant reminder',
            body='Ignore',
            notification_type='reminder_notification',
            metadata={
                'external_source': 'orchestration_center',
                'orchestration_dedupe_key': shared_dedupe_key,
            },
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-notify-retry',
            rule_title='Runtime Notify Retry',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'title': 'Pending review',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'dedupe_key': shared_dedupe_key,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(uuid.uuid4()),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='notify-retry-contract-test',
        )

        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.tenant_id,
                notification_type='reminder_notification',
                metadata__orchestration_dedupe_key=shared_dedupe_key,
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.other_tenant_id,
                notification_type='reminder_notification',
                metadata__orchestration_dedupe_key=shared_dedupe_key,
            ).count(),
            1,
        )

    def test_create_review_task_uses_interview_owned_contract(self):
        interview_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-review-contract',
            rule_title='Runtime Review Contract',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={
                'review_type': 'interview_feedback_review',
                'owner_module': 'interviews',
                'assigned_role': 'hr_manager',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(interview_id),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='review-contract-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        result = executed_run.action_results_json[0]
        self.assertEqual(result['owner_module'], 'interviews')
        self.assertEqual(result['action_family'], 'create_review_task')
        self.assertEqual(result['target_type'], 'review_task')
        self.assertFalse(result['duplicate'])
        self.assertTrue(
            InterviewReviewTask.objects.filter(
                tenant_id=self.tenant_id,
                interview_id=interview_id,
                review_type='interview_feedback_review',
            ).exists()
        )

    def test_create_review_task_supports_ai_output_review_through_downstream_owner(self):
        execution_request, _ = AIExecutionService.create_request(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            module_scope='interviews',
            use_case_key='interview_summary',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(uuid.uuid4()),
            source_event='interview.completed',
            context_snapshot={'interview': {'id': 'demo'}},
            requires_review=True,
            idempotency_key='ai-output-review-request',
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-ai-output-review-contract',
            rule_title='Runtime AI Output Review Contract',
            module_scope='interviews',
            trigger_event='ai.execution.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={
                'owner_module': 'ai_execution',
                'entity_type': 'ai_execution',
                'entity_id': str(execution_request.id),
                'review_type': 'ai_output_review',
                'assigned_role': 'hr_manager',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='ai.execution.completed',
            source_module='orchestration_center',
            source_entity_type='ai_execution',
            source_entity_id=str(execution_request.id),
            payload={'ai_execution': {'id': str(execution_request.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='ai-output-review-contract-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        task = InterviewReviewTask.objects.get(
            tenant_id=self.tenant_id,
            interview_id=execution_request.id,
            review_type='ai_output_review',
        )
        self.assertEqual(task.metadata['owner_module'], 'ai_execution')
        self.assertEqual(task.metadata['entity_type'], 'ai_execution')
        self.assertEqual(task.metadata['entity_id'], str(execution_request.id))

    def test_create_review_task_retry_is_duplicate_safe(self):
        interview_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-review-retry',
            rule_title='Runtime Review Retry',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={
                'review_type': 'manual_check_review',
                'owner_module': 'interviews',
                'entity_type': 'interview',
                'entity_id': str(interview_id),
                'assigned_role': 'reviewer',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(interview_id),
            payload={'interview': {'id': str(interview_id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='review-retry-contract-test',
        )

        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.action_results_json[0]['status'], 'deduplicated')
        self.assertTrue(second.action_results_json[0]['duplicate'])
        self.assertEqual(
            InterviewReviewTask.objects.filter(
                tenant_id=self.tenant_id,
                interview_id=interview_id,
                review_type='manual_check_review',
            ).count(),
            1,
        )

    def test_execute_run_notify_failure_is_non_blocking_and_audited(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-notify-failure',
            rule_title='Runtime Notify Failure',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Review application',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'review'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='notify-failure-contract-test',
        )

        with patch(
            'apps.orchestration_center.services.communication_binding_service.CommunicationDispatchService.dispatch_automation_notification',
            side_effect=RuntimeError('notification downstream unavailable'),
        ):
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(executed_run.action_results_json[1]['status'], 'completed')
        self.assertTrue(ActionDeadline.objects.filter(tenant_id=self.tenant_id, entity_id=entity_id).exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_execute_run_create_review_task_failure_is_non_blocking_and_audited(self):
        interview_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-review-failure',
            rule_title='Runtime Review Failure',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={
                'owner_module': 'interviews',
                'entity_type': 'interview',
                'entity_id': str(interview_id),
                'review_type': 'interview_review',
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(interview_id),
            payload={'interview': {'id': str(interview_id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='review-failure-contract-test',
        )

        with patch(
            'apps.orchestration_center.services.automation_action_executor.InterviewReviewTaskService.create_automation_review_task',
            side_effect=RuntimeError('review downstream unavailable'),
        ):
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(
            executed_run.action_results_json[0]['error_category'],
            'unhandled_runtime_error',
        )
        self.assertTrue(executed_run.action_results_json[0]['retry_safe'])
        self.assertEqual(executed_run.action_results_json[1]['status'], 'completed')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='reminder_notification').exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_create_review_task_invalid_review_type_uses_structured_owner_error(self):
        interview_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-review-invalid-type',
            rule_title='Runtime Review Invalid Type',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={
                'owner_module': 'interviews',
                'entity_type': 'interview',
                'entity_id': str(interview_id),
                'review_type': 'unsupported_review_type',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(interview_id),
            payload={'interview': {'id': str(interview_id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='review-invalid-type-contract-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(
            executed_run.action_results_json[0]['error_category'],
            'owner_contract_unsupported',
        )
        self.assertFalse(executed_run.action_results_json[0]['retry_safe'])

    def test_escalate_updates_pipeline_deadline_and_creates_notification(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-escalate-contract',
            rule_title='Runtime Escalate Contract',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        create_deadline_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'feedback_due',
                'action_required': 'Collect interview feedback',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'high',
                'reason': 'Feedback overdue',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Collect interview feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'interview'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='escalate-contract-test',
        )

        first = AutomationRuleService._apply_action(run=run, action=create_deadline_action)
        self.assertEqual(first['status'], 'completed')
        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        deadline = ActionDeadline.objects.get(id=first['deadline_id'])
        deadline.refresh_from_db()
        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        escalate_result = executed_run.action_results_json[1]
        self.assertEqual(escalate_result['status'], 'completed')
        self.assertEqual(escalate_result['owner_module'], 'pipeline')
        self.assertEqual(escalate_result['action_family'], 'escalate')
        self.assertEqual(escalate_result['target_type'], 'deadline')
        self.assertEqual(escalate_result['target_id'], str(deadline.id))
        self.assertEqual(len(escalate_result['results']), 2)
        self.assertEqual(escalate_result['results'][0]['binding'], 'pipeline_deadline')
        self.assertEqual(escalate_result['results'][1]['binding'], 'communications')
        self.assertEqual(deadline.status, 'escalated')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='escalation_alert').exists())

    def test_escalate_retry_is_duplicate_safe_and_tenant_isolated(self):
        entity_id = uuid.uuid4()
        shared_notification_dedupe = 'escalate-notify-dedupe'
        PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.other_tenant_id,
            entity_type='application',
            entity_id=entity_id,
            action_required='Collect interview feedback',
            due_in_hours=24,
            metadata={},
            external_reference='other-tenant-escalate',
        )
        Notification.objects.create(
            tenant_id=self.other_tenant_id,
            user_id=self.user_id,
            title='Other tenant escalation',
            body='Ignore',
            notification_type='escalation_alert',
            metadata={
                'external_source': 'orchestration_center',
                'orchestration_dedupe_key': shared_notification_dedupe,
            },
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-escalate-retry',
            rule_title='Runtime Escalate Retry',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        create_deadline_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'feedback_due',
                'action_required': 'Collect interview feedback',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'high',
                'reason': 'Feedback overdue',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Collect interview feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
                'dedupe_key': shared_notification_dedupe,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'interview'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='escalate-retry-contract-test',
        )

        create_result = AutomationRuleService._apply_action(run=run, action=create_deadline_action)
        self.assertEqual(create_result['status'], 'completed')
        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.action_results_json[1]['status'], 'deduplicated')
        self.assertEqual(
            ActionDeadline.objects.filter(
                tenant_id=self.tenant_id,
                entity_type='application',
                entity_id=entity_id,
                status='escalated',
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.tenant_id,
                notification_type='escalation_alert',
                metadata__orchestration_dedupe_key=shared_notification_dedupe,
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                tenant_id=self.other_tenant_id,
                notification_type='escalation_alert',
                metadata__orchestration_dedupe_key=shared_notification_dedupe,
            ).count(),
            1,
        )

    def test_execute_run_escalate_notification_failure_is_non_blocking(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-escalate-notify-failure',
            rule_title='Runtime Escalate Notify Failure',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        create_deadline_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'feedback_due',
                'action_required': 'Collect interview feedback',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'high',
                'reason': 'Feedback overdue',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Collect interview feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'interview'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='escalate-notify-failure-test',
        )

        AutomationRuleService._apply_action(run=run, action=create_deadline_action)
        with patch(
            'apps.orchestration_center.services.automation_action_executor.CommunicationBindingService.dispatch_in_app_notification_from_automation',
            side_effect=RuntimeError('escalation notification unavailable'),
        ):
            executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        escalate_result = executed_run.action_results_json[1]
        self.assertEqual(escalate_result['status'], 'partial')
        self.assertEqual(escalate_result['results'][1]['status'], 'failed')
        deadline = ActionDeadline.objects.get(id=escalate_result['deadline_id'])
        self.assertEqual(deadline.status, 'escalated')

    def test_execute_run_escalate_tenant_isolation_failure_is_non_blocking_and_audited(self):
        entity_id = uuid.uuid4()
        PipelineDeadlineService.create_automation_deadline(
            tenant_id=self.other_tenant_id,
            entity_type='application',
            entity_id=entity_id,
            action_required='Collect interview feedback',
            due_in_hours=24,
            metadata={},
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-escalate-tenant-isolation',
            rule_title='Runtime Escalate Tenant Isolation',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='escalate',
            action_config_json={
                'severity': 'high',
                'reason': 'Feedback overdue',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Collect interview feedback',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
                'notify': True,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'interview'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='escalate-tenant-isolation-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(
            executed_run.action_results_json[0]['error_category'],
            'owner_contract_not_found',
        )
        self.assertFalse(executed_run.action_results_json[0]['retry_safe'])
        self.assertEqual(executed_run.action_results_json[1]['status'], 'completed')
        self.assertTrue(
            Notification.objects.filter(
                tenant_id=self.tenant_id,
                notification_type='reminder_notification',
            ).exists()
        )

    def test_assign_uses_pipeline_owned_deadline_contract(self):
        entity_id = uuid.uuid4()
        assignee_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-contract',
            rule_title='Runtime Assign Contract',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        create_deadline_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'followup',
                'action_required': 'Follow up with candidate',
                'entity_type': 'application',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        assign_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'pipeline',
                'assignment_target': 'deadline',
                'deadline_entity_type': 'application',
                'deadline_entity_id': str(entity_id),
                'deadline_action_required': 'Follow up with candidate',
                'assigned_to': str(assignee_id),
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(entity_id),
            payload={'application': {'stage': 'interview'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-contract-test',
        )
        first = AutomationRuleService._apply_action(run=run, action=create_deadline_action)
        assigned = AutomationRuleService._apply_action(run=run, action=assign_action)

        deadline = ActionDeadline.objects.get(id=first['deadline_id'])
        self.assertEqual(assigned['status'], 'completed')
        self.assertEqual(deadline.id, uuid.UUID(assigned['deadline_id']))
        deadline.refresh_from_db()
        self.assertEqual(deadline.assigned_to, assignee_id)

    def test_assign_uses_interview_owned_review_contract(self):
        interview_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-review',
            rule_title='Runtime Assign Review',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        create_review_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_review_task',
            action_config_json={
                'review_type': 'interview_feedback_review',
                'owner_module': 'interviews',
            },
            sequence_order=1,
        )
        assign_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'interviews',
                'assignment_target': 'review_task',
                'review_type': 'interview_feedback_review',
                'assigned_reviewer_id': str(self.user_id),
                'assigned_role': 'reviewer',
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(interview_id),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-review-contract-test',
        )
        create_result = AutomationRuleService._apply_action(run=run, action=create_review_action)
        assign_result = AutomationRuleService._apply_action(run=run, action=assign_action)

        self.assertEqual(create_result['status'], 'completed')
        self.assertEqual(assign_result['status'], 'completed')
        task = InterviewReviewTask.objects.get(id=assign_result['review_task_id'])
        self.assertEqual(task.assigned_reviewer_id, self.user_id)

    def test_mark_flag_uses_pipeline_owned_contract(self):
        application = Application.objects.create(
            tenant_id=self.tenant_id,
            candidate_id=uuid.uuid4(),
            requisition_id=uuid.uuid4(),
            status='applied',
            created_by=self.user_id,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-pipeline',
            rule_title='Runtime Mark Flag Pipeline',
            module_scope='pipeline',
            trigger_event='application.stage_changed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        mark_flag_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'pipeline',
                'entity_type': 'application',
                'entity_id': str(application.id),
                'flag_key': 'attention_needed',
                'flag_value': True,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='application.stage_changed',
            source_module='pipeline',
            source_entity_type='application',
            source_entity_id=str(application.id),
            payload={'application': {'stage': 'screening'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-pipeline-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=mark_flag_action)
        application.refresh_from_db()

        self.assertEqual(result['status'], 'completed')
        self.assertTrue(application.metadata['operational_flags']['attention_needed']['value'])

    def test_mark_flag_uses_interview_owned_contract(self):
        interview_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-interview',
            rule_title='Runtime Mark Flag Interview',
            module_scope='interviews',
            trigger_event='interview.completed',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        mark_flag_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'interviews',
                'entity_type': 'interview',
                'entity_id': str(interview_id),
                'flag_key': 'manual_check_required',
                'flag_value': True,
            },
            sequence_order=1,
        )
        from apps.interviews.models import Interview
        Interview.objects.create(
            id=interview_id,
            tenant_id=self.tenant_id,
            application_id=uuid.uuid4(),
            candidate_id=uuid.uuid4(),
            requisition_id=uuid.uuid4(),
            created_by=self.user_id,
            interview_type='technical',
            status='completed',
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='interview.completed',
            source_module='interviews',
            source_entity_type='interview',
            source_entity_id=str(interview_id),
            payload={'interview': {'feedback_missing': True}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-interview-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=mark_flag_action)
        interview = Interview.objects.get(id=interview_id)

        self.assertEqual(result['status'], 'completed')
        self.assertTrue(interview.metadata['operational_flags']['manual_check_required']['value'])

    def test_assign_uses_candidate_owned_assignment_contract(self):
        assignee = get_user_model().objects.create_user(
            email='runtime-candidate-assignee@example.com',
            password='testpass123',
            tenant_id=self.tenant_id,
            role='recruiter',
        )
        candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Neha',
            last_name='Rao',
            email='neha@example.com',
            phone='+911234567890',
            created_by=self.user_id,
        )
        engagement = CandidateEngagement.objects.create(
            tenant_id=self.tenant_id,
            candidate=candidate,
            engagement_type='lead',
            stage='new_lead',
            priority='warm',
            is_active=True,
        )
        assignee_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-candidate',
            rule_title='Runtime Assign Candidate',
            module_scope='candidates',
            trigger_event='candidate.created',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        assign_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'candidates',
                'assignment_target': 'candidate_owner',
                'candidate_id': str(candidate.id),
                'owner_user_id': str(assignee.id),
                'sync_active_engagement': True,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.created',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate.id),
            payload={'candidate': {'id': str(candidate.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-candidate-contract-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=assign_action)
        candidate.refresh_from_db()
        engagement.refresh_from_db()

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(candidate.owner_user_id, assignee.id)
        self.assertEqual(engagement.owner_user_id, assignee.id)
        self.assertTrue(
            CandidateTimelineEvent.objects.filter(
                tenant_id=self.tenant_id,
                candidate=candidate,
                event_type='candidate.assigned',
            ).exists()
        )

    def test_assign_uses_agencies_owned_assignment_contract(self):
        requisition_id = uuid.uuid4()
        agency_tenant_id = uuid.uuid4()
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=self.tenant_id,
            status='active',
            created_by=self.user_id,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-agency',
            rule_title='Runtime Assign Agency',
            module_scope='agencies',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        assign_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'agencies',
                'assignment_target': 'job_agency',
                'requisition_id': str(requisition_id),
                'agency_tenant_id': str(agency_tenant_id),
                'notes': 'Preferred partner for this role',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='jobs',
            source_entity_type='requisition',
            source_entity_id=str(requisition_id),
            payload={'job': {'id': str(requisition_id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-agency-contract-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=assign_action)
        assignment = AgencyJobAssignment.objects.get(id=result['assignment_id'])

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(assignment.requisition_id, requisition_id)
        self.assertEqual(assignment.agency_tenant_id, agency_tenant_id)
        self.assertEqual(assignment.metadata['external_source'], 'orchestration_center')

    def test_assign_agencies_retry_is_duplicate_safe_and_tenant_isolated(self):
        requisition_id = uuid.uuid4()
        agency_tenant_id = uuid.uuid4()
        shared_external_reference = 'shared-agency-assignment-ref'
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=self.tenant_id,
            status='active',
            created_by=self.user_id,
        )
        AgencyClientRelationship.objects.create(
            tenant_id=self.other_tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=self.other_tenant_id,
            status='active',
            created_by=self.user_id,
        )
        AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.other_tenant_id,
            requisition_id=requisition_id,
            agency_tenant_id=agency_tenant_id,
            assigned_by=self.user_id,
            external_reference=shared_external_reference,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-agency-retry',
            rule_title='Runtime Assign Agency Retry',
            module_scope='agencies',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'agencies',
                'assignment_target': 'job_agency',
                'requisition_id': str(requisition_id),
                'agency_tenant_id': str(agency_tenant_id),
                'external_reference': shared_external_reference,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='jobs',
            source_entity_type='requisition',
            source_entity_id=str(requisition_id),
            payload={'job': {'id': str(requisition_id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-agency-retry-contract-test',
        )

        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(
            AgencyJobAssignment.objects.filter(
                tenant_id=self.tenant_id,
                requisition_id=requisition_id,
                agency_tenant_id=agency_tenant_id,
                is_deleted=False,
            ).count(),
            1,
        )
        self.assertEqual(
            AgencyJobAssignment.objects.filter(
                tenant_id=self.other_tenant_id,
                requisition_id=requisition_id,
                agency_tenant_id=agency_tenant_id,
                is_deleted=False,
            ).count(),
            1,
        )

    def test_mark_flag_uses_candidate_owned_contract(self):
        candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Rhea',
            last_name='Kapoor',
            email='rhea@example.com',
            phone='+919123456789',
            created_by=self.user_id,
        )
        engagement = CandidateEngagement.objects.create(
            tenant_id=self.tenant_id,
            candidate=candidate,
            engagement_type='lead',
            stage='new_lead',
            priority='warm',
            is_active=True,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-candidate',
            rule_title='Runtime Mark Flag Candidate',
            module_scope='candidates',
            trigger_event='candidate.updated',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        mark_flag_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'candidates',
                'entity_type': 'candidate',
                'candidate_id': str(candidate.id),
                'flag_key': 'review_required',
                'flag_value': True,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.updated',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate.id),
            payload={'candidate': {'id': str(candidate.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-candidate-contract-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=mark_flag_action)
        candidate.refresh_from_db()
        engagement.refresh_from_db()

        self.assertEqual(result['status'], 'completed')
        self.assertTrue(candidate.metadata['operational_flags']['review_required']['value'])
        self.assertTrue(engagement.metadata['operational_flags']['review_required']['value'])
        self.assertTrue(
            CandidateTimelineEvent.objects.filter(
                tenant_id=self.tenant_id,
                candidate=candidate,
                event_type='candidate.flagged',
            ).exists()
        )

    def test_mark_flag_uses_agencies_owned_contract(self):
        requisition_id = uuid.uuid4()
        agency_tenant_id = uuid.uuid4()
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=self.tenant_id,
            status='active',
            created_by=self.user_id,
        )
        assignment = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.tenant_id,
            requisition_id=requisition_id,
            agency_tenant_id=agency_tenant_id,
            assigned_by=self.user_id,
            external_reference='agency-assignment-for-runtime-flag',
        )[0]
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-agencies',
            rule_title='Runtime Mark Flag Agencies',
            module_scope='agencies',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        mark_flag_action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'agencies',
                'entity_type': 'job_assignment',
                'entity_id': str(assignment.id),
                'flag_key': 'manual_check_required',
                'flag_value': True,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='agencies',
            source_entity_type='job_assignment',
            source_entity_id=str(assignment.id),
            payload={'assignment': {'id': str(assignment.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-agencies-test',
        )

        result = AutomationRuleService._apply_action(run=run, action=mark_flag_action)
        assignment.refresh_from_db()

        self.assertEqual(result['status'], 'completed')
        self.assertTrue(assignment.metadata['operational_flags']['manual_check_required']['value'])

    def test_mark_flag_agencies_retry_is_duplicate_safe_and_tenant_isolated(self):
        requisition_id = uuid.uuid4()
        agency_tenant_id = uuid.uuid4()
        shared_external_reference = 'shared-agency-flag-ref'
        AgencyClientRelationship.objects.create(
            tenant_id=self.tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=self.tenant_id,
            status='active',
            created_by=self.user_id,
        )
        AgencyClientRelationship.objects.create(
            tenant_id=self.other_tenant_id,
            agency_tenant_id=agency_tenant_id,
            company_tenant_id=self.other_tenant_id,
            status='active',
            created_by=self.user_id,
        )
        assignment = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.tenant_id,
            requisition_id=requisition_id,
            agency_tenant_id=agency_tenant_id,
            assigned_by=self.user_id,
            external_reference='agency-assignment-primary-flag',
        )[0]
        other_assignment = AgencyAssignmentService.assign_job_to_agency(
            tenant_id=self.other_tenant_id,
            requisition_id=requisition_id,
            agency_tenant_id=agency_tenant_id,
            assigned_by=self.user_id,
            external_reference='agency-assignment-secondary-flag',
        )[0]
        from apps.agencies.services import AgencyOperationalFlagService
        AgencyOperationalFlagService.mark_operational_flag(
            tenant_id=self.other_tenant_id,
            entity_type='job_assignment',
            entity_id=other_assignment.id,
            flag_key='review_required',
            flag_value=True,
            external_reference=shared_external_reference,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-agencies-retry',
            rule_title='Runtime Mark Flag Agencies Retry',
            module_scope='agencies',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'agencies',
                'entity_type': 'job_assignment',
                'entity_id': str(assignment.id),
                'flag_key': 'review_required',
                'flag_value': True,
                'external_reference': shared_external_reference,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='agencies',
            source_entity_type='job_assignment',
            source_entity_id=str(assignment.id),
            payload={'assignment': {'id': str(assignment.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-agencies-retry-test',
        )

        first = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)
        first_status = first.status
        AutomationRuleService.queue_for_retry(run=first)
        second = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        assignment.refresh_from_db()
        other_assignment.refresh_from_db()
        self.assertEqual(first_status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(second.status, AutomationExecutionStatus.COMPLETED)
        self.assertTrue(assignment.metadata['operational_flags']['review_required']['value'])
        self.assertTrue(other_assignment.metadata['operational_flags']['review_required']['value'])
        self.assertEqual(
            assignment.metadata['operational_flags']['review_required']['external_reference'],
            shared_external_reference,
        )
        self.assertEqual(
            other_assignment.metadata['operational_flags']['review_required']['external_reference'],
            shared_external_reference,
        )

    def test_execute_run_assignment_failure_is_non_blocking_and_audited(self):
        candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Ira',
            last_name='Shah',
            email='ira@example.com',
            phone='+918888888888',
            created_by=self.user_id,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-failure',
            rule_title='Runtime Assign Failure',
            module_scope='candidates',
            trigger_event='candidate.created',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'candidates',
                'assignment_target': 'candidate_owner',
                'candidate_id': str(candidate.id),
                'owner_user_id': 'not-a-uuid',
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.created',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate.id),
            payload={'candidate': {'id': str(candidate.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-candidate-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(
            executed_run.action_results_json[0]['error_category'],
            'owner_contract_validation',
        )
        self.assertFalse(executed_run.action_results_json[0]['retry_safe'])
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_execute_run_agency_assignment_failure_is_non_blocking_and_audited(self):
        requisition_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-assign-agency-failure',
            rule_title='Runtime Assign Agency Failure',
            module_scope='agencies',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='assign',
            action_config_json={
                'owner_module': 'agencies',
                'assignment_target': 'job_agency',
                'requisition_id': str(requisition_id),
                'agency_tenant_id': str(uuid.uuid4()),
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='jobs',
            source_entity_type='requisition',
            source_entity_id=str(requisition_id),
            payload={'job': {'id': str(requisition_id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='assign-agency-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(
            executed_run.action_results_json[0]['error_category'],
            'owner_contract_ownership',
        )
        self.assertFalse(executed_run.action_results_json[0]['retry_safe'])
        self.assertEqual(executed_run.action_results_json[1]['status'], 'completed')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='reminder_notification').exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_execute_run_mark_flag_failure_is_non_blocking_and_audited(self):
        candidate = Candidate.objects.create(
            tenant_id=self.tenant_id,
            first_name='Sara',
            last_name='Nair',
            email='sara@example.com',
            phone='+917777777777',
            created_by=self.user_id,
        )
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-failure',
            rule_title='Runtime Mark Flag Failure',
            module_scope='candidates',
            trigger_event='candidate.updated',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'candidates',
                'entity_type': 'candidate',
                'candidate_id': str(candidate.id),
                'flag_key': 'unsupported_flag',
                'flag_value': True,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='candidate.updated',
            source_module='candidates',
            source_entity_type='candidate',
            source_entity_id=str(candidate.id),
            payload={'candidate': {'id': str(candidate.id)}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-candidate-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_execute_run_agencies_mark_flag_failure_is_non_blocking_and_audited(self):
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-mark-flag-agencies-failure',
            rule_title='Runtime Mark Flag Agencies Failure',
            module_scope='agencies',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='mark_flag',
            action_config_json={
                'owner_module': 'agencies',
                'entity_type': 'job_assignment',
                'entity_id': str(uuid.uuid4()),
                'flag_key': 'review_required',
                'flag_value': True,
            },
            sequence_order=1,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='notify',
            action_config_json={
                'channel': 'in_app',
                'notification_type': 'reminder_notification',
                'recipient_user_ids': [str(self.user_id)],
                'default_to_actor': False,
            },
            sequence_order=2,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='agencies',
            source_entity_type='job_assignment',
            source_entity_id=str(uuid.uuid4()),
            payload={'assignment': {'id': 'missing'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='mark-flag-agencies-failure-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.PARTIAL)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'failed')
        self.assertEqual(executed_run.action_results_json[1]['status'], 'completed')
        self.assertTrue(Notification.objects.filter(tenant_id=self.tenant_id, notification_type='reminder_notification').exists())
        self.assertTrue(
            IntelligenceAuditLog.objects.filter(
                tenant_id=self.tenant_id,
                target_id=run.id,
                action_type='automation_run.completed',
            ).exists()
        )

    def test_create_deadline_uses_pipeline_owned_contract(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-create-deadline',
            rule_title='Runtime Create Deadline',
            module_scope='jobs',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'review',
                'action_required': 'Review published job',
                'entity_type': 'requisition',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='jobs',
            source_entity_type='job',
            source_entity_id=str(entity_id),
            payload={'job': {'priority': 'high'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='create-deadline-test',
        )

        executed_run = AutomationRuleService.execute_run_by_id(automation_run_id=run.id)

        self.assertEqual(executed_run.status, AutomationExecutionStatus.COMPLETED)
        self.assertEqual(executed_run.action_results_json[0]['status'], 'completed')
        deadline = ActionDeadline.objects.get(id=executed_run.action_results_json[0]['deadline_id'])
        self.assertEqual(deadline.tenant_id, self.tenant_id)
        self.assertEqual(deadline.entity_id, entity_id)
        self.assertEqual(deadline.metadata['external_source'], 'orchestration_center')

    def test_create_deadline_binding_is_idempotent(self):
        entity_id = uuid.uuid4()
        rule = AutomationRule.objects.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule_key='runtime-create-deadline-dedupe',
            rule_title='Runtime Create Deadline Dedupe',
            module_scope='jobs',
            trigger_event='job.published',
            mode=ApprovalMode.SUGGESTION_ONLY,
            status=AutomationRuleStatus.ACTIVE,
        )
        action = rule.actions.create(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            action_type='create_deadline',
            action_config_json={
                'deadline_type': 'review',
                'action_required': 'Review published job',
                'entity_type': 'requisition',
                'entity_id': str(entity_id),
                'due_in_hours': 24,
            },
            sequence_order=1,
        )
        run, _ = AutomationRuleService.create_run(
            tenant_id=self.tenant_id,
            created_by=self.user_id,
            rule=rule,
            source_event='job.published',
            source_module='jobs',
            source_entity_type='job',
            source_entity_id=str(entity_id),
            payload={'job': {'priority': 'high'}},
            mode=ApprovalMode.SUGGESTION_ONLY,
            dedupe_key='create-deadline-dedupe-run',
        )

        first = AutomationRuleService._apply_action(run=run, action=action)
        second = AutomationRuleService._apply_action(run=run, action=action)

        self.assertEqual(first['status'], 'completed')
        self.assertEqual(second['status'], 'deduplicated')
        self.assertEqual(
            ActionDeadline.objects.filter(
                tenant_id=self.tenant_id,
                entity_type='requisition',
                entity_id=entity_id,
                metadata__external_source='orchestration_center',
            ).count(),
            1,
        )
