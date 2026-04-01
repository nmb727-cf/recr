import json
import os
from dataclasses import dataclass
from typing import Any

import requests
from django.db.models import Q
from django.utils import timezone
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate as validate_json_schema

from apps.orchestration_center.constants.execution_statuses import HealthStatus, ProviderStatus
from apps.orchestration_center.models import AIModel, AIProvider, ModelRoutingRule, PromptVersion, ProviderConfig
from apps.orchestration_center.services.tenant_settings_service import TenantSettingsService


class ProviderExecutionError(Exception):
    def __init__(self, message: str, *, retryable: bool = True, category: str = 'provider_error'):
        super().__init__(message)
        self.retryable = retryable
        self.category = category


@dataclass
class ResolvedRoute:
    provider: AIProvider
    model: AIModel
    config: ProviderConfig | None
    approval_mode: str
    fallback_chain: list[dict[str, Any]]
    routing_rule: ModelRoutingRule | None = None


class ProviderRouter:
    DEFAULT_OPENAI_BASE_URL = 'https://api.openai.com/v1'

    @staticmethod
    def resolve(tenant_id, module_scope, use_case_key) -> ResolvedRoute:
        settings, _ = TenantSettingsService.get_or_create(tenant_id, None)
        rule = (
            ModelRoutingRule.objects.filter(
                tenant_id__in=[tenant_id, None],
                module_scope=module_scope,
                use_case_key=use_case_key,
                is_deleted=False,
                status=ProviderStatus.ACTIVE,
            )
            .order_by('-tenant_id')
            .first()
        )
        if rule:
            provider = rule.primary_provider
            model = rule.primary_model
            ProviderRouter._validate_allowed_provider(settings=settings, provider=provider)
            config = ProviderRouter._get_provider_config(provider=provider, tenant_id=tenant_id, use_case_key=use_case_key)
            ProviderRouter._validate_route(provider=provider, model=model, config=config)
            return ResolvedRoute(
                provider=provider,
                model=model,
                config=config,
                approval_mode=rule.approval_mode,
                fallback_chain=rule.fallback_chain_json or [],
                routing_rule=rule,
            )

        provider = (
            AIProvider.objects.filter(
                tenant_id__in=[tenant_id, None],
                is_deleted=False,
                status=ProviderStatus.ACTIVE,
            )
            .order_by('-tenant_id', 'priority_order')
            .first()
        )
        if not provider:
            raise ProviderExecutionError('No active provider is configured for this tenant.', retryable=False, category='provider_unavailable')
        ProviderRouter._validate_allowed_provider(settings=settings, provider=provider)
        model = (
            AIModel.objects.filter(
                provider=provider,
                tenant_id__in=[tenant_id, None],
                is_deleted=False,
                status=ProviderStatus.ACTIVE,
            )
            .order_by('-tenant_id', 'id')
            .first()
        )
        if not model:
            raise ProviderExecutionError('No active model is configured for the selected provider.', retryable=False, category='model_unavailable')
        config = ProviderRouter._get_provider_config(provider=provider, tenant_id=tenant_id, use_case_key=use_case_key)
        ProviderRouter._validate_route(provider=provider, model=model, config=config)
        return ResolvedRoute(
            provider=provider,
            model=model,
            config=config,
            approval_mode='suggestion_only',
            fallback_chain=[],
            routing_rule=None,
        )

    @staticmethod
    def execute_with_fallback(*, route: ResolvedRoute, prompt_version: PromptVersion, rendered_prompt: dict[str, str], context_snapshot: dict[str, Any]):
        candidates = [
            {
                'provider': route.provider,
                'model': route.model,
                'config': route.config,
            },
            *ProviderRouter._resolve_fallback_chain(
                route.fallback_chain,
                tenant_id=route.provider.tenant_id,
                use_case_key=route.routing_rule.use_case_key if route.routing_rule else '',
            ),
        ]
        last_error = None
        for candidate in candidates:
            provider = candidate['provider']
            model = candidate['model']
            config = candidate['config']
            try:
                result = ProviderRouter._execute(
                    provider=provider,
                    model=model,
                    config=config,
                    prompt_version=prompt_version,
                    rendered_prompt=rendered_prompt,
                    context_snapshot=context_snapshot,
                )
                ProviderRouter.update_provider_health(provider=provider, health_status=HealthStatus.HEALTHY)
                return {
                    **result,
                    'provider_id': provider.id,
                    'model_id': model.id,
                }
            except ProviderExecutionError as exc:
                last_error = exc
                ProviderRouter.update_provider_health(
                    provider=provider,
                    health_status=HealthStatus.WARNING if exc.retryable else HealthStatus.UNHEALTHY,
                )
                continue
        if last_error:
            raise last_error
        raise ProviderExecutionError('Execution failed before any provider attempt was made.', retryable=False, category='execution_unavailable')

    @staticmethod
    def validate_structured_output(payload: dict[str, Any], expected_schema: dict[str, Any] | None):
        if not expected_schema:
            return True, []
        try:
            validate_json_schema(instance=payload, schema=expected_schema)
            return True, []
        except JsonSchemaValidationError as exc:
            return False, [exc.message]

    @staticmethod
    def update_provider_health(*, provider: AIProvider, health_status: str):
        provider.health_status = health_status
        provider.last_health_checked_at = timezone.now()
        provider.save(update_fields=['health_status', 'last_health_checked_at', 'updated_at'])

    @staticmethod
    def _execute(*, provider: AIProvider, model: AIModel, config: ProviderConfig | None, prompt_version: PromptVersion, rendered_prompt: dict[str, str], context_snapshot: dict[str, Any]):
        if provider.provider_type == AIProvider.ProviderType.LOCAL or provider.provider_key in {'mock', 'demo', 'local_echo'}:
            raw_text = ProviderRouter._execute_local_mock(prompt_version=prompt_version, rendered_prompt=rendered_prompt, context_snapshot=context_snapshot)
        else:
            raw_text = ProviderRouter._execute_external(
                provider=provider,
                model=model,
                config=config,
                prompt_version=prompt_version,
                rendered_prompt=rendered_prompt,
            )

        normalized_output = ProviderRouter._normalize_output(raw_text)
        is_valid, schema_errors = ProviderRouter.validate_structured_output(
            normalized_output,
            prompt_version.expected_output_schema_json or None,
        )
        return {
            'raw_response_ref': '',
            'raw_text': raw_text,
            'normalized_output_json': normalized_output,
            'validation_passed': is_valid,
            'schema_errors_json': schema_errors,
        }

    @staticmethod
    def _execute_local_mock(*, prompt_version: PromptVersion, rendered_prompt: dict[str, str], context_snapshot: dict[str, Any]):
        schema = prompt_version.expected_output_schema_json or {}
        properties = schema.get('properties') if isinstance(schema, dict) else None
        if properties:
            payload = {}
            for key, config in properties.items():
                config_type = config.get('type')
                if config_type == 'number':
                    payload[key] = 0
                elif config_type == 'boolean':
                    payload[key] = False
                elif config_type == 'array':
                    payload[key] = []
                elif config_type == 'object':
                    payload[key] = {}
                else:
                    payload[key] = f'Generated {key} for {context_snapshot.get("source_entity_type", "entity")}'
            return json.dumps(payload)
        return json.dumps(
            {
                'summary': rendered_prompt.get('user_prompt', '')[:400],
                'module_scope': context_snapshot.get('module_scope'),
                'use_case_key': context_snapshot.get('use_case_key'),
            }
        )

    @staticmethod
    def _execute_external(*, provider: AIProvider, model: AIModel, config: ProviderConfig | None, prompt_version: PromptVersion, rendered_prompt: dict[str, str]):
        if not config:
            raise ProviderExecutionError('Provider configuration is missing for this environment.', retryable=False, category='provider_config_missing')

        api_key = os.getenv(config.credential_ref)
        if not api_key:
            raise ProviderExecutionError(
                f'Credential env var {config.credential_ref} is not configured.',
                retryable=False,
                category='provider_credentials_missing',
            )

        base_url = provider.base_url or ProviderRouter.DEFAULT_OPENAI_BASE_URL
        endpoint = base_url.rstrip('/') + '/chat/completions'
        timeout_seconds = provider.timeout_seconds
        body = {
            'model': model.model_key,
            'messages': [
                {'role': 'system', 'content': rendered_prompt['system_prompt']},
                {'role': 'user', 'content': rendered_prompt['user_prompt']},
            ],
            'temperature': 0.2,
        }
        try:
            response = requests.post(
                endpoint,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json=body,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise ProviderExecutionError('Provider request timed out.', retryable=True, category='provider_timeout') from exc
        except requests.RequestException as exc:
            raise ProviderExecutionError(str(exc), retryable=True, category='provider_http_error') from exc

        payload = response.json()
        try:
            return payload['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderExecutionError('Provider returned an unexpected response shape.', retryable=False, category='provider_invalid_response') from exc

    @staticmethod
    def _normalize_output(raw_text: str):
        if not raw_text:
            return {}
        try:
            parsed = json.loads(raw_text)
            return parsed if isinstance(parsed, dict) else {'items': parsed}
        except json.JSONDecodeError:
            return {'text': raw_text}

    @staticmethod
    def _get_provider_config(*, provider: AIProvider, tenant_id, use_case_key: str):
        environment = os.getenv('TOS_ENV', 'dev').lower()
        configs = ProviderConfig.objects.filter(
            provider=provider,
            tenant_id__in=[tenant_id, None],
            is_deleted=False,
            is_active=True,
        ).filter(Q(environment=environment) | Q(environment=ProviderConfig.Environment.PROD)).order_by('-tenant_id')
        for config in configs:
            allowed = config.allowed_use_cases_json or []
            if not allowed or use_case_key in allowed:
                return config
        return None

    @staticmethod
    def _resolve_fallback_chain(fallback_chain: list[dict[str, Any]], tenant_id, use_case_key: str):
        resolved = []
        for item in fallback_chain or []:
            provider = None
            model = None
            if item.get('provider_id'):
                provider = AIProvider.objects.filter(id=item['provider_id'], tenant_id__in=[tenant_id, None], is_deleted=False).first()
            elif item.get('provider_key'):
                provider = AIProvider.objects.filter(provider_key=item['provider_key'], tenant_id__in=[tenant_id, None], is_deleted=False).order_by('-tenant_id').first()
            if not provider:
                continue
            if item.get('model_id'):
                model = AIModel.objects.filter(id=item['model_id'], provider=provider, tenant_id__in=[tenant_id, None], is_deleted=False).first()
            elif item.get('model_key'):
                model = AIModel.objects.filter(model_key=item['model_key'], provider=provider, tenant_id__in=[tenant_id, None], is_deleted=False).order_by('-tenant_id').first()
            else:
                model = AIModel.objects.filter(provider=provider, tenant_id__in=[tenant_id, None], is_deleted=False, status=ProviderStatus.ACTIVE).order_by('-tenant_id').first()
            if not model:
                continue
            config = ProviderRouter._get_provider_config(provider=provider, tenant_id=tenant_id, use_case_key=item.get('use_case_key', use_case_key))
            resolved.append({'provider': provider, 'model': model, 'config': config})
        return resolved

    @staticmethod
    def _validate_allowed_provider(*, settings, provider: AIProvider):
        allowed_ids = settings.allowed_provider_ids_json or []
        if allowed_ids and str(provider.id) not in {str(item) for item in allowed_ids}:
            raise ProviderExecutionError('Provider is not enabled for this tenant.', retryable=False, category='provider_not_allowed')

    @staticmethod
    def _validate_route(*, provider: AIProvider, model: AIModel, config: ProviderConfig | None):
        if provider.status != ProviderStatus.ACTIVE:
            raise ProviderExecutionError('Provider is not active.', retryable=False, category='provider_disabled')
        if model.status != ProviderStatus.ACTIVE:
            raise ProviderExecutionError('Model is not active.', retryable=False, category='model_disabled')
        if provider.provider_type != AIProvider.ProviderType.LOCAL and not config:
            raise ProviderExecutionError('Provider configuration is missing.', retryable=False, category='provider_config_missing')
