import uuid
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.communications.models import EmailTemplateDefinition, EmailTemplateScope, EmailTemplateType
from apps.orchestration_center.constants.execution_statuses import (
    ApprovalMode,
    ApprovalStatus,
    AutomationExecutionStatus,
    AutomationRuleStatus,
    DeadLetterStatus,
    FailureSeverity,
    FailureStatus,
    HealthStatus,
    PromptStatus,
    ProviderStatus,
    ValidationStatus,
)
from apps.orchestration_center.models import (
    AIExecutionRequest,
    AIExecutionResult,
    AIModel,
    AIProvider,
    ApprovalQueueItem,
    AutomationExecutionRun,
    AutomationRule,
    DeadLetterItem,
    ExecutionFailure,
    IntelligenceConnector,
    ModelRoutingRule,
    PromptScope,
    PromptTemplate,
    PromptTestRun,
    PromptVersion,
    ProviderConfig,
    TenantIntelligenceSettings,
)
from apps.orchestration_center.services.suggestion_service import SuggestionService


DEMO_TENANT_ID = uuid.UUID('00000000-0000-0000-0000-000000000901')
SYSTEM_USER_ID = uuid.UUID('00000000-0000-0000-0000-0000000009ff')


class Command(BaseCommand):
    help = 'Seed deterministic Intelligence Hub demo/runtime data for dev and staging environments.'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', dest='tenant_id', help='Optional tenant UUID override.')
        parser.add_argument('--user-email', dest='user_email', help='Resolve tenant UUID from a real user email.')
        parser.add_argument('--force', action='store_true', help='Allow running outside dev/staging safeguards.')

    def handle(self, *args, **options):
        self._guard_environment(force=options['force'])
        tenant_id = self._resolve_tenant_id(
            tenant_id=options.get('tenant_id'),
            user_email=options.get('user_email'),
        )
        providers = self._seed_providers(tenant_id)
        self._seed_communication_templates(tenant_id)
        prompts = self._seed_prompts(tenant_id)
        self._seed_settings(tenant_id, providers)
        self._seed_routing_rules(tenant_id, providers)
        self._seed_connectors(tenant_id)
        self._seed_automation_rules(tenant_id)
        self._seed_operational_examples(tenant_id, prompts, providers)
        self.stdout.write(self.style.SUCCESS(f'Intelligence Hub demo data seeded for tenant {tenant_id}.'))

    def _resolve_tenant_id(self, *, tenant_id, user_email):
        if tenant_id:
            return uuid.UUID(tenant_id)
        if user_email:
            User = get_user_model()
            user = User.objects.filter(email=user_email, is_active=True).exclude(tenant_id__isnull=True).first()
            if not user:
                raise CommandError(f'No active user with tenant found for email {user_email}.')
            return user.tenant_id
        return DEMO_TENANT_ID

    def _guard_environment(self, *, force):
        env = getattr(settings, 'ENVIRONMENT', None) or getattr(settings, 'TOS_ENV', None) or 'dev'
        env = str(env).lower()
        if force or settings.DEBUG or env in {'dev', 'development', 'staging', 'stage', 'local', 'test'}:
            return
        raise CommandError('Seed command is blocked outside dev/staging unless --force is provided.')

    def _seed_providers(self, tenant_id):
        providers = {}
        models = {}
        for spec in (
            ('demo', 'Demo Structured Provider', 10),
            ('local_echo', 'Local Echo Fallback', 20),
        ):
            provider, _ = AIProvider.objects.update_or_create(
                tenant_id=tenant_id,
                provider_key=spec[0],
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'provider_name': spec[1],
                    'provider_type': AIProvider.ProviderType.LOCAL,
                    'status': ProviderStatus.ACTIVE,
                    'api_version': 'demo-v1',
                    'timeout_seconds': 20,
                    'connect_timeout_seconds': 5,
                    'read_timeout_seconds': 15,
                    'max_retries': 2,
                    'priority_order': spec[2],
                    'supports_streaming': False,
                    'supports_structured_output': True,
                    'health_status': HealthStatus.HEALTHY,
                    'last_health_checked_at': timezone.now(),
                    'is_deleted': False,
                },
            )
            model, _ = AIModel.objects.update_or_create(
                tenant_id=tenant_id,
                provider=provider,
                model_key=f'{spec[0]}-core',
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'model_name': f'{spec[1]} Core',
                    'capability_type': 'structured_generation',
                    'status': ProviderStatus.ACTIVE,
                    'context_window': 32000,
                    'max_output_tokens': 2000,
                    'cost_class': 'dev',
                    'supports_json_schema': True,
                    'supports_tools': False,
                    'supports_multimodal': False,
                    'latency_tier': 'fast',
                    'quality_tier': 'standard',
                    'health_status': HealthStatus.HEALTHY,
                    'is_deleted': False,
                },
            )
            ProviderConfig.objects.update_or_create(
                tenant_id=tenant_id,
                provider=provider,
                environment=ProviderConfig.Environment.DEV,
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'credential_ref': 'OPENAI_API_KEY',
                    'allowed_use_cases_json': [],
                    'rate_limit_per_minute': 120,
                    'cost_limit_daily': Decimal('25.00'),
                    'is_active': True,
                    'is_deleted': False,
                },
            )
            providers[spec[0]] = provider
            models[spec[0]] = model
        return {'providers': providers, 'models': models}

    def _seed_communication_templates(self, tenant_id):
        templates = [
            (
                'pending_action_reminder',
                'Pending action reminder',
                EmailTemplateType.SYSTEM,
                EmailTemplateScope.SYSTEM_DEFAULT,
                'Pending action reminder',
                'A pending action requires attention for {{ source_entity_type }} {{ source_entity_id }}.',
            ),
            (
                'interview_feedback_reminder',
                'Interview feedback reminder',
                EmailTemplateType.BUSINESS,
                EmailTemplateScope.TENANT_CUSTOM,
                'Interview feedback reminder',
                'Please submit feedback for interview {{ source_entity_id }}.',
            ),
        ]
        for slug, name, template_type, scope, subject, body_text in templates:
            target_tenant = None if scope == EmailTemplateScope.SYSTEM_DEFAULT else tenant_id
            defaults = {
                'template_scope': scope,
                'template_type': template_type,
                'channel': 'email',
                'name': name,
                'category': 'automation',
                'subject_template': subject,
                'body_html': f'<p>{body_text}</p>',
                'body_text': body_text,
                'variables_schema_json': {
                    'variables': ['source_entity_type', 'source_entity_id']
                },
                'usage_context_json': {'seeded_for': 'intelligence_hub'},
                'is_active': True,
                'is_system_locked': scope == EmailTemplateScope.SYSTEM_DEFAULT,
                'created_by': SYSTEM_USER_ID,
            }
            existing = (
                EmailTemplateDefinition.objects.filter(
                    tenant_id=target_tenant,
                    slug=slug,
                    language_code='en',
                    version=1,
                )
                .order_by('created_at')
                .first()
            )
            if existing:
                for field, value in defaults.items():
                    setattr(existing, field, value)
                existing.save()
            else:
                EmailTemplateDefinition.objects.create(
                    tenant_id=target_tenant,
                    slug=slug,
                    language_code='en',
                    version=1,
                    **defaults,
                )

    def _seed_prompts(self, tenant_id):
        prompt_specs = [
            ('job_enrichment', 'jobs', 'job_enrichment', 'Job Enrichment', {'summary': {'type': 'string'}, 'recommended_skills': {'type': 'array'}, 'risk_flags': {'type': 'array'}}),
            ('candidate_matching', 'jobs', 'candidate_matching', 'Candidate Matching', {'match_score': {'type': 'number'}, 'top_reasons': {'type': 'array'}, 'gaps': {'type': 'array'}}),
            ('interview_summary', 'interviews', 'interview_summary', 'Interview Summary', {'summary': {'type': 'string'}, 'strengths': {'type': 'array'}, 'risks': {'type': 'array'}}),
            ('email_draft', 'communications', 'email_draft', 'Email Draft Generator', {'subject': {'type': 'string'}, 'body': {'type': 'string'}}),
            (
                'followup_recommendation',
                'communications',
                'followup_recommendation',
                'Follow-up Recommendation',
                {
                    'summary': {'type': 'string'},
                    'reason': {'type': 'string'},
                    'channel': {'type': 'string'},
                    'followup_type': {'type': 'string'},
                },
            ),
            ('decision_assist', 'hiring_decisions', 'decision_assist', 'Decision Assist', {'recommendation': {'type': 'string'}, 'confidence_band': {'type': 'string'}, 'notes': {'type': 'array'}}),
        ]
        prompt_versions = {}
        for index, spec in enumerate(prompt_specs, start=1):
            prompt_key, module_scope, use_case_key, title, properties = spec
            template, _ = PromptTemplate.objects.update_or_create(
                tenant_id=tenant_id,
                prompt_key=prompt_key,
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'prompt_title': title,
                    'module_scope': module_scope,
                    'use_case_key': use_case_key,
                    'description': f'Demo prompt for {title}.',
                    'status': PromptStatus.ACTIVE,
                    'approval_required': use_case_key == 'decision_assist',
                    'tenant_override_allowed': True,
                    'safety_notes': 'Demo-safe prompt managed through registry.',
                    'owner_role': 'tenant_admin',
                    'is_deleted': False,
                },
            )
            version, _ = PromptVersion.objects.update_or_create(
                tenant_id=tenant_id,
                prompt_template=template,
                version_number=1,
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'status': PromptStatus.ACTIVE,
                    'system_prompt': f'You are the {title} engine for Talent Operating System.',
                    'user_prompt_template': f'Use the provided context to produce a structured {use_case_key} response for {{source_entity_type}} {{source_entity_id}}. Context: {{context}}.',
                    'variables_schema_json': {
                        'type': 'object',
                        'properties': {
                            'source_entity_type': {'type': 'string'},
                            'source_entity_id': {'type': 'string'},
                            'context': {'type': 'object'},
                        },
                    },
                    'expected_output_schema_json': {'type': 'object', 'properties': properties},
                    'validation_rules_json': {'strict': False},
                    'approval_required': use_case_key == 'decision_assist',
                    'approved_by_id': SYSTEM_USER_ID,
                    'approved_at': timezone.now(),
                    'activation_notes': 'Seeded demo active version.',
                    'diff_notes': 'Initial demo version.',
                },
            )
            if template.active_version_id != version.id or template.status != PromptStatus.ACTIVE:
                template.active_version_id = version.id
                template.status = PromptStatus.ACTIVE
                template.save(update_fields=['active_version_id', 'status', 'updated_at'])
            PromptScope.objects.update_or_create(
                tenant_id=tenant_id,
                prompt_template=template,
                module_scope=module_scope,
                use_case_key=use_case_key,
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'entity_type': '',
                    'priority_order': index * 10,
                    'is_active': True,
                },
            )
            PromptTestRun.objects.update_or_create(
                tenant_id=tenant_id,
                prompt_version=version,
                notes='seed-smoke-test',
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'test_input_json': {'source_entity_type': 'candidate', 'source_entity_id': 'demo-candidate-001', 'context': {'sample': True, 'prompt_key': prompt_key}},
                    'normalized_output_json': {'seeded': True, 'prompt_key': prompt_key},
                    'validation_status': ValidationStatus.PASSED,
                    'run_status': ValidationStatus.PASSED,
                    'executed_by_id': SYSTEM_USER_ID,
                },
            )
            prompt_versions[prompt_key] = version
        return prompt_versions

    def _seed_settings(self, tenant_id, providers):
        TenantIntelligenceSettings.objects.update_or_create(
            tenant_id=tenant_id,
            defaults={
                'created_by': SYSTEM_USER_ID,
                'updated_by_id': SYSTEM_USER_ID,
                'ai_enabled': True,
                'automation_enabled': True,
                'default_approval_mode': ApprovalMode.SUGGESTION_ONLY,
                'allowed_provider_ids_json': [str(item.id) for item in providers['providers'].values()],
                'feature_flags_json': {'job_enrichment': True, 'candidate_matching': True, 'interview_summary': True, 'decision_assist': True},
                'notification_preferences_json': {'email_on_failure': True, 'slack_on_critical': False},
                'retry_policy_overrides_json': {'ai_default_max_retries': 2, 'automation_default_max_retries': 2},
                'connector_enablement_json': {'jobs': True, 'pipeline': True, 'interviews': True, 'communications': True, 'hiring_decisions': True},
                'visibility_permissions_json': {'recruiter_can_view_executions': True, 'tenant_admin_can_manage_prompts': True},
            },
        )

    def _seed_routing_rules(self, tenant_id, providers):
        for module_scope, use_case_key, approval_mode in (
            ('jobs', 'job_enrichment', ApprovalMode.SUGGESTION_ONLY),
            ('jobs', 'candidate_matching', ApprovalMode.SUGGESTION_ONLY),
            ('interviews', 'interview_summary', ApprovalMode.AUTO_APPLY),
            ('communications', 'email_draft', ApprovalMode.SUGGESTION_ONLY),
            ('communications', 'followup_recommendation', ApprovalMode.SUGGESTION_ONLY),
            ('hiring_decisions', 'decision_assist', ApprovalMode.APPROVAL_REQUIRED),
        ):
            ModelRoutingRule.objects.update_or_create(
                tenant_id=tenant_id,
                module_scope=module_scope,
                use_case_key=use_case_key,
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'primary_provider': providers['providers']['demo'],
                    'primary_model': providers['models']['demo'],
                    'fallback_chain_json': [{'provider_id': str(providers['providers']['local_echo'].id), 'model_id': str(providers['models']['local_echo'].id)}],
                    'timeout_override_seconds': 18,
                    'retry_override_count': 2,
                    'approval_mode': approval_mode,
                    'status': ProviderStatus.ACTIVE,
                    'is_deleted': False,
                },
            )

    def _seed_connectors(self, tenant_id):
        for module_code, events, ai_actions, automation_actions in (
            ('candidates', ['candidate.created', 'candidate.updated'], ['resume_parsing', 'profile_enrichment'], ['notify', 'mark_flag']),
            ('jobs', ['job.created', 'job.published'], ['job_enrichment', 'candidate_matching'], ['notify', 'create_deadline']),
            ('pipeline', ['application.created', 'application.stage_changed', 'application.shortlisted'], ['candidate_ranking'], ['create_deadline', 'schedule_followup', 'escalate', 'assign', 'mark_flag']),
            ('interviews', ['interview.scheduled', 'interview.completed', 'interview.feedback_submitted'], ['interview_summary'], ['schedule_followup', 'create_review_task']),
            ('communications', ['message.sent'], ['email_draft'], ['enqueue_communication']),
            ('hiring_decisions', ['interview.decision_recorded'], ['decision_assist'], ['create_review_task', 'escalate']),
        ):
            IntelligenceConnector.objects.update_or_create(
                tenant_id=tenant_id,
                module_code=module_code,
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'status': 'active',
                    'events_consumed_json': events,
                    'ai_actions_allowed_json': ai_actions,
                    'automation_actions_allowed_json': automation_actions,
                    'fallback_behavior': 'manual_continue',
                    'compatibility_notes': 'Seeded demo connector.',
                    'version_tag': 'demo-1',
                    'is_deleted': False,
                },
            )

    def _seed_automation_rules(self, tenant_id):
        specs = [
            ('jobs_publish_followup', 'Job Publish Follow-up', 'jobs', 'job.published', ApprovalMode.SUGGESTION_ONLY, [{'field_path': 'job.priority', 'operator': 'exists', 'expected_value_json': True, 'sequence_order': 1}], [{'action_type': 'notify', 'action_config_json': {'channel': 'both', 'notification_type': 'reminder_notification', 'title': 'Published job needs shortlist review', 'message': 'A published job is waiting for shortlist review.', 'template_key': 'pending_action_reminder'}, 'sequence_order': 1}, {'action_type': 'create_deadline', 'action_config_json': {'deadline_type': 'shortlist_review', 'action_required': 'Review published job shortlist', 'entity_type': 'requisition', 'due_in_hours': 24}, 'sequence_order': 2}]),
            ('agency_submission_feedback_followup', 'Agency Submission Feedback Follow-up', 'pipeline', 'application.created', ApprovalMode.SUGGESTION_ONLY, [{'field_path': 'application.is_agency_submission', 'operator': 'eq', 'expected_value_json': True, 'sequence_order': 1}], [{'action_type': 'create_deadline', 'action_config_json': {'deadline_type': 'agency_feedback', 'action_required': 'Review agency submission feedback', 'entity_type': 'application', 'due_in_hours': 24}, 'sequence_order': 1}, {'action_type': 'schedule_followup', 'action_config_json': {'delay_seconds': 86400, 'followup_type': 'agency_submission_followup', 'channel': 'email', 'template_key': 'followup', 'recipient_paths': ['submission.client_email'], 'message_purpose': 'agency_submission_update'}, 'sequence_order': 2}, {'action_type': 'escalate', 'action_config_json': {'severity': 'medium', 'reason': 'Agency submission feedback is still pending', 'deadline_entity_type': 'application', 'deadline_action_required': 'Review agency submission feedback', 'notify': True, 'default_to_actor': True, 'title': 'Agency submission feedback pending'}, 'delay_seconds': 172800, 'sequence_order': 3}]),
            ('pipeline_stalled_escalation', 'Pipeline Stalled Escalation', 'pipeline', 'application.stage_changed', ApprovalMode.SUGGESTION_ONLY, [{'field_path': 'application.stage', 'operator': 'eq', 'expected_value_json': 'interview_pending', 'sequence_order': 1}], [{'action_type': 'escalate', 'action_config_json': {'severity': 'medium', 'target_role': 'hr_manager', 'notify': True, 'notification_type': 'escalation_alert', 'title': 'Pipeline candidate is stalled', 'message': 'Candidate requires escalation due to stalled progression.'}, 'sequence_order': 1}, {'action_type': 'assign', 'action_config_json': {'assignee_role': 'recruiter_ops'}, 'sequence_order': 2}, {'action_type': 'mark_flag', 'action_config_json': {'flag_key': 'stalled_pipeline', 'flag_value': True}, 'sequence_order': 3}]),
            ('interview_completion_followup', 'Interview Completion Follow-up', 'interviews', 'interview.completed', ApprovalMode.APPROVAL_REQUIRED, [{'field_path': 'interview.feedback_missing', 'operator': 'eq', 'expected_value_json': True, 'sequence_order': 1}], [{'action_type': 'schedule_followup', 'action_config_json': {'delay_seconds': 7200, 'followup_type': 'feedback_reminder', 'channel': 'email', 'template_key': 'interview_feedback_reminder', 'message_purpose': 'interview_reminder'}, 'sequence_order': 1}, {'action_type': 'create_review_task', 'action_config_json': {'review_type': 'interview_feedback_review', 'owner_module': 'interviews', 'assigned_role': 'hr_manager'}, 'requires_approval': True, 'sequence_order': 2}]),
            ('decision_approval_mailer', 'Decision Approval Mailer', 'hiring_decisions', 'interview.decision_recorded', ApprovalMode.APPROVAL_REQUIRED, [{'field_path': 'decision.recommendation', 'operator': 'eq', 'expected_value_json': 'hire', 'sequence_order': 1}], [{'action_type': 'enqueue_communication', 'action_config_json': {'template_key': 'decision_review_requested'}, 'requires_approval': True, 'sequence_order': 1}, {'action_type': 'invoke_ai_execution', 'action_config_json': {'use_case_key': 'decision_assist'}, 'sequence_order': 2}]),
        ]
        for index, spec in enumerate(specs, start=1):
            rule, _ = AutomationRule.objects.update_or_create(
                tenant_id=tenant_id,
                rule_key=spec[0],
                defaults={
                    'created_by': SYSTEM_USER_ID,
                    'rule_title': spec[1],
                    'module_scope': spec[2],
                    'trigger_event': spec[3],
                    'mode': spec[4],
                    'status': AutomationRuleStatus.ACTIVE,
                    'is_builtin': True,
                    'dry_run_enabled': False,
                    'requires_high_risk_approval': spec[4] == ApprovalMode.APPROVAL_REQUIRED,
                    'max_executions_per_day': 200,
                    'duplicate_window_seconds': 300,
                    'priority_order': index * 10,
                    'notes': 'Seeded built-in demo rule.',
                    'is_deleted': False,
                },
            )
            rule.conditions.all().delete()
            rule.actions.all().delete()
            rule.scopes.all().delete()
            for condition in spec[5]:
                rule.conditions.create(tenant_id=tenant_id, created_by=SYSTEM_USER_ID, condition_group='default', field_path=condition['field_path'], operator=condition['operator'], expected_value_json=condition['expected_value_json'], sequence_order=condition['sequence_order'])
            for action in spec[6]:
                rule.actions.create(tenant_id=tenant_id, created_by=SYSTEM_USER_ID, action_type=action['action_type'], action_config_json=action.get('action_config_json', {}), delay_seconds=action.get('delay_seconds', 0), requires_approval=action.get('requires_approval', False), sequence_order=action['sequence_order'])
            rule.scopes.create(tenant_id=tenant_id, created_by=SYSTEM_USER_ID, entity_type='candidate', is_active=True)

    def _seed_operational_examples(self, tenant_id, prompts, providers):
        tenant_suffix = str(tenant_id)
        approval_item, _ = ApprovalQueueItem.objects.update_or_create(
            tenant_id=tenant_id,
            origin_type='prompt_version',
            origin_id=prompts['decision_assist'].id,
            requested_action='activate_prompt_version',
            defaults={
                'created_by': SYSTEM_USER_ID,
                'item_type': 'prompt_activation',
                'summary_payload_json': {'prompt_key': 'decision_assist', 'version': 1},
                'recommended_decision': 'approve',
                'approver_role': 'tenant_admin',
                'status': ApprovalStatus.PENDING,
            },
        )
        failure, _ = ExecutionFailure.objects.update_or_create(
            tenant_id=tenant_id,
            failure_type='provider_timeout',
            category='provider_timeout',
            defaults={
                'created_by': SYSTEM_USER_ID,
                'severity': FailureSeverity.MEDIUM,
                'status': FailureStatus.NEW,
                'retryable': True,
                'max_retries': 2,
                'next_retry_at': timezone.now(),
                'operator_notes': 'Seeded demo failure for UI visibility.',
                'last_error_message': 'Primary provider timed out during candidate matching demo run.',
            },
        )
        DeadLetterItem.objects.update_or_create(
            tenant_id=tenant_id,
            item_type='automation_run',
            related_object_id=approval_item.id,
            reason_code='retry_exhausted',
            defaults={
                'created_by': SYSTEM_USER_ID,
                'payload_snapshot_json': {'origin': 'seed_demo', 'approval_id': str(approval_item.id)},
                'status': DeadLetterStatus.OPEN,
                'requeue_count': 0,
                'notes': 'Seeded dead-letter example.',
            },
        )
        request, _ = AIExecutionRequest.objects.update_or_create(
            tenant_id=tenant_id,
            idempotency_key=f'seed-demo-ai-execution:{tenant_suffix}',
            defaults={
                'created_by': SYSTEM_USER_ID,
                'module_scope': 'jobs',
                'use_case_key': 'job_enrichment',
                'source_event': 'job.published',
                'source_entity_type': 'job',
                'source_entity_id': 'JOB-DEMO-001',
                'source_module': 'jobs',
                'prompt_version': prompts['job_enrichment'],
                'provider': providers['providers']['demo'],
                'model': providers['models']['demo'],
                'mode': ApprovalMode.SUGGESTION_ONLY,
                'status': 'completed',
                'context_snapshot_json': {'job': {'title': 'Senior Backend Engineer'}},
                'retry_count': 0,
                'max_retries': 2,
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
                'requires_review': False,
                'requires_approval': False,
                'final_disposition': 'suggested',
            },
        )
        AIExecutionResult.objects.update_or_create(
            tenant_id=tenant_id,
            request=request,
            defaults={
                'created_by': SYSTEM_USER_ID,
                'normalized_output_json': {'summary': 'Strong backend scope with reliability emphasis.', 'recommended_skills': ['Python', 'Django', 'PostgreSQL'], 'risk_flags': ['niche-domain-hiring']},
                'validation_status': ValidationStatus.VALID,
                'confidence_score': Decimal('0.91'),
                'token_input_count': 320,
                'token_output_count': 140,
                'estimated_cost': Decimal('0.0125'),
                'execution_ms': 420,
                'schema_errors_json': [],
                'warnings_json': [],
            },
        )
        AutomationExecutionRun.objects.update_or_create(
            tenant_id=tenant_id,
            dedupe_key=f'seed-demo-automation-run:{tenant_suffix}',
            defaults={
                'created_by': SYSTEM_USER_ID,
                'rule': AutomationRule.objects.get(tenant_id=tenant_id, rule_key='jobs_publish_followup'),
                'source_event': 'job.published',
                'source_module': 'jobs',
                'source_entity_type': 'job',
                'source_entity_id': 'JOB-DEMO-001',
                'status': AutomationExecutionStatus.PARTIAL,
                'mode': ApprovalMode.SUGGESTION_ONLY,
                'trigger_payload_json': {'job': {'priority': 'high', 'title': 'Senior Backend Engineer'}},
                'evaluated_conditions_json': [{'field_path': 'job.priority', 'matched': True}],
                'action_results_json': [{'action_type': 'notify', 'status': 'completed'}, {'action_type': 'create_deadline', 'status': 'completed'}],
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
                'retry_count': 1,
                'failure_category': failure.category,
                'failure_reason': failure.last_error_message,
            },
        )
        followup_request, _ = AIExecutionRequest.objects.update_or_create(
            tenant_id=tenant_id,
            idempotency_key=f'seed-demo-followup-recommendation-execution:{tenant_suffix}',
            defaults={
                'created_by': SYSTEM_USER_ID,
                'module_scope': 'communications',
                'use_case_key': 'followup_recommendation',
                'source_event': 'application.stage_changed',
                'source_entity_type': 'application',
                'source_entity_id': 'APP-DEMO-001',
                'source_module': 'communications',
                'prompt_version': prompts['followup_recommendation'],
                'provider': providers['providers']['demo'],
                'model': providers['models']['demo'],
                'mode': ApprovalMode.SUGGESTION_ONLY,
                'status': 'completed',
                'context_snapshot_json': {
                    'application': {
                        'id': 'APP-DEMO-001',
                        'stage': 'interview_pending',
                        'candidate_name': 'Demo Candidate',
                    }
                },
                'retry_count': 0,
                'max_retries': 2,
                'started_at': timezone.now(),
                'completed_at': timezone.now(),
                'requires_review': False,
                'requires_approval': False,
                'final_disposition': 'suggested',
            },
        )
        AIExecutionResult.objects.update_or_create(
            tenant_id=tenant_id,
            request=followup_request,
            defaults={
                'created_by': SYSTEM_USER_ID,
                'normalized_output_json': {
                    'summary': 'Send a follow-up to move the application forward.',
                    'reason': 'The application has been waiting in interview pending without outbound communication.',
                    'channel': 'email',
                    'followup_type': 'candidate_followup',
                    'template_key': 'pending_action_reminder',
                    'recipient_hint': 'candidate',
                    'recommended_window': 'within_24_hours',
                    'delay_hours': 24,
                    'urgency': 'medium',
                    'signals': ['interview_pending', 'no_recent_outreach'],
                },
                'validation_status': ValidationStatus.VALID,
                'confidence_score': Decimal('0.86'),
                'token_input_count': 190,
                'token_output_count': 110,
                'estimated_cost': Decimal('0.0085'),
                'execution_ms': 310,
                'schema_errors_json': [],
                'warnings_json': [],
            },
        )
        suggestion, _, _ = SuggestionService.create_supported_suggestion_from_ai_execution(ai_request=followup_request)
        if suggestion:
            failure.related_request_id = followup_request.id
            failure.save(update_fields=['related_request_id', 'updated_at'])
