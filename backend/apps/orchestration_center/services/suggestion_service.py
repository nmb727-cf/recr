from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.candidates.models import Candidate
from apps.communications.email_dispatch.types import EmailSendRequest
from apps.communications.models import EmailTemplateDefinition
from apps.communications.services import CommunicationDispatchService
from apps.orchestration_center.constants.execution_statuses import (
    ApprovalStatus,
    ConfidenceBand,
    SuggestionCategory,
    SuggestionConversionStatus,
    SuggestionStatus,
)
from apps.orchestration_center.models import AIExecutionRequest, AISuggestion, AISuggestionConversion, ApprovalQueueItem
from apps.orchestration_center.services.approval_service import ApprovalService
from apps.orchestration_center.services.audit_service import AuditService
from apps.pipeline.models import Application
from apps.pipeline.services import PipelineDeadlineService
from shared.owner_contracts import OwnerActionContext, OwnerContractError


class SuggestionService:
    GOVERNABLE_PENDING_STATUSES = {SuggestionStatus.PENDING}
    TERMINAL_STATUSES = {
        SuggestionStatus.REJECTED,
        SuggestionStatus.DISMISSED,
        SuggestionStatus.APPLIED,
        SuggestionStatus.APPLY_FAILED,
        SuggestionStatus.CONVERTED,
        SuggestionStatus.EXPIRED,
        SuggestionStatus.SUPERSEDED,
        SuggestionStatus.FAILED,
    }
    LOW_CONFIDENCE_THRESHOLD = Decimal('0.40')
    SUPPORTED_AI_EXECUTION_MAPPERS = {
        ('communications', 'email_draft'): 'communication_draft',
        ('communications', 'followup_recommendation'): 'followup_recommendation',
    }

    @staticmethod
    def _schedule_automation_intelligence_evaluation(*, suggestion_id):
        def _dispatch():
            from apps.orchestration_center.tasks.automation_intelligence_tasks import evaluate_suggestion_policy_task

            try:
                evaluate_suggestion_policy_task.delay(str(suggestion_id))
            except Exception:
                evaluate_suggestion_policy_task(str(suggestion_id))

        transaction.on_commit(_dispatch)

    @staticmethod
    def _derive_confidence_band(confidence_score):
        if confidence_score is None:
            return ConfidenceBand.MEDIUM
        score = Decimal(str(confidence_score))
        if score < Decimal('0.40'):
            return ConfidenceBand.LOW
        if score < Decimal('0.75'):
            return ConfidenceBand.MEDIUM
        return ConfidenceBand.HIGH

    @staticmethod
    def _sanitize_json(value):
        if isinstance(value, dict):
            return {str(key): SuggestionService._sanitize_json(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [SuggestionService._sanitize_json(item) for item in value]
        if hasattr(value, 'isoformat') and not isinstance(value, (str, bytes)):
            try:
                return value.isoformat()
            except TypeError:
                pass
        if hasattr(value, 'hex') and value.__class__.__name__ == 'UUID':
            return str(value)
        return value

    @staticmethod
    def _first_non_empty_value(payload, *keys):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value
            elif value not in (None, '', [], {}, ()):
                return value
        return None

    @staticmethod
    def _base_requested_payload(*, suggestion, payload):
        return {
            'suggestion_id': str(suggestion.id),
            'category': suggestion.category,
            'status': suggestion.status,
            'owner_module': suggestion.owner_module,
            'proposed_action_family': suggestion.proposed_action_family,
            'source_entity_type': suggestion.source_entity_type,
            'source_entity_id': suggestion.source_entity_id,
            'title': suggestion.title,
            'summary': suggestion.summary,
            'payload': SuggestionService._sanitize_json(payload),
        }

    @staticmethod
    def _build_owner_context(*, suggestion, user_id, action_payload):
        return OwnerActionContext(
            tenant_id=suggestion.tenant_id,
            actor_id=user_id,
            external_reference=f'ai-suggestion:{suggestion.id}:apply',
            audit_metadata={
                'suggestion_id': str(suggestion.id),
                'source_module': suggestion.source_module,
                'source_entity_type': suggestion.source_entity_type,
                'source_entity_id': suggestion.source_entity_id,
                'owner_module': suggestion.owner_module,
                'proposed_action_family': suggestion.proposed_action_family,
                'applied_payload': SuggestionService._sanitize_json(action_payload),
            },
        )

    @staticmethod
    def _resolve_candidate_email(*, suggestion, payload):
        direct = []
        for key in ('recipient_email', 'email'):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                direct.append(value.strip())
        for key in ('recipient_emails', 'emails'):
            values = payload.get(key)
            if isinstance(values, list):
                direct.extend(str(item).strip() for item in values if str(item).strip())
        if direct:
            return sorted(set(direct))

        entity_type = str(suggestion.source_entity_type or '').lower()
        entity_id = suggestion.source_entity_id
        if entity_type == 'candidate':
            candidate = Candidate.objects.filter(id=entity_id, tenant_id=suggestion.tenant_id).only('email').first()
            if candidate and candidate.email:
                return [candidate.email]
        if entity_type == 'application':
            application = Application.objects.filter(id=entity_id, tenant_id=suggestion.tenant_id).only('candidate_id').first()
            if application:
                candidate = Candidate.objects.filter(id=application.candidate_id, tenant_id=suggestion.tenant_id).only('email').first()
                if candidate and candidate.email:
                    return [candidate.email]
        raise OwnerContractError.validation('Suggestion apply contract could not resolve a recipient email.')

    @staticmethod
    def _resolve_email_template(*, tenant_id, template_key):
        if not template_key:
            return None
        return (
            EmailTemplateDefinition.objects.filter(
                slug=template_key,
                tenant_id__in=[tenant_id, None],
                is_active=True,
            )
            .order_by('-tenant_id', '-version')
            .first()
        )

    @staticmethod
    def _apply_enqueue_communication(*, suggestion, user_id, payload):
        recipients = SuggestionService._resolve_candidate_email(suggestion=suggestion, payload=payload)
        template = SuggestionService._resolve_email_template(
            tenant_id=suggestion.tenant_id,
            template_key=payload.get('template_key') or payload.get('template_slug') or '',
        )
        subject = str(payload.get('subject') or '').strip()
        body = str(payload.get('body') or payload.get('body_text') or '').strip()
        body_html = str(payload.get('body_html') or '').strip()
        if not template and not (subject or body or body_html):
            raise OwnerContractError.validation('Suggestion apply contract requires a template or explicit email content.')

        request = EmailSendRequest(
            tenant_id=str(suggestion.tenant_id),
            actor_user_id=str(user_id) if user_id else None,
            email_type='business',
            message_purpose=str(payload.get('message_purpose') or 'suggestion_apply'),
            recipients=recipients,
            related_object_type=suggestion.source_entity_type,
            related_object_id=str(suggestion.source_entity_id),
            workflow_context_type='ai_suggestion',
            workflow_context_id=str(suggestion.id),
            subject=subject,
            body_html=body_html,
            body_text=body,
            template_id=str(template.id) if template else None,
            preferred_sender_account_id=payload.get('preferred_sender_account_id'),
            variables=SuggestionService._sanitize_json(payload.get('variables', {})),
            allow_fallback=True,
            track_delivery=True,
            cc_emails=[str(item) for item in payload.get('cc_emails', []) if str(item).strip()],
            bcc_emails=[str(item) for item in payload.get('bcc_emails', []) if str(item).strip()],
            reply_to_email=str(payload.get('reply_to_email') or ''),
            trigger_source='ai_suggestion',
            triggered_by_event_id=str(suggestion.source_event or ''),
            metadata={
                'suggestion_id': str(suggestion.id),
                'template_key': payload.get('template_key') or payload.get('template_slug') or '',
            },
        )
        context = SuggestionService._build_owner_context(suggestion=suggestion, user_id=user_id, action_payload=payload)
        return CommunicationDispatchService.enqueue_email_from_orchestration(
            context=context,
            request=request,
            dedupe_key=f'ai-suggestion:{suggestion.id}:apply:enqueue_communication',
        )

    @staticmethod
    def _apply_create_deadline(*, suggestion, user_id, payload):
        context = SuggestionService._build_owner_context(suggestion=suggestion, user_id=user_id, action_payload=payload)
        return PipelineDeadlineService.create_from_orchestration(
            context=context,
            entity_type=str(payload.get('entity_type') or suggestion.source_entity_type),
            entity_id=payload.get('entity_id') or suggestion.source_entity_id,
            action_required=str(payload.get('action_required') or payload.get('deadline_type') or suggestion.title or 'followup'),
            due_in_hours=int(payload.get('due_in_hours', 24)),
            assigned_to=payload.get('assigned_to'),
            escalate_to=payload.get('escalate_to'),
            deadline_type=str(payload.get('deadline_type') or 'followup'),
            owner_role=str(payload.get('owner_role') or 'recruiter'),
        )

    @staticmethod
    def _execute_apply(*, suggestion, user_id, payload):
        owner_module = str(suggestion.owner_module or '').lower()
        action_family = str(suggestion.proposed_action_family or '').lower()
        if owner_module == 'communications' and action_family == 'enqueue_communication':
            return SuggestionService._apply_enqueue_communication(suggestion=suggestion, user_id=user_id, payload=payload)
        if owner_module == 'pipeline' and action_family == 'create_deadline':
            return SuggestionService._apply_create_deadline(suggestion=suggestion, user_id=user_id, payload=payload)
        raise OwnerContractError.unsupported(
            f'No owner-module apply contract exists for {suggestion.owner_module or "unknown"}:{suggestion.proposed_action_family or "unknown"}.'
        )

    @staticmethod
    def _create_apply_conversion(*, suggestion, user_id, payload, idempotency_key=''):
        effective_idempotency_key = idempotency_key or f'ai-suggestion:{suggestion.id}:apply'
        existing = AISuggestionConversion.objects.filter(
            tenant_id=suggestion.tenant_id,
            idempotency_key=effective_idempotency_key,
        ).first()
        if existing:
            return existing, False
        conversion = AISuggestionConversion.objects.create(
            tenant_id=suggestion.tenant_id,
            created_by=user_id,
            suggestion=suggestion,
            conversion_type='apply',
            idempotency_key=effective_idempotency_key,
            requested_by_id=user_id,
            requested_action_payload_json=SuggestionService._base_requested_payload(
                suggestion=suggestion,
                payload=payload,
            ),
            retry_safe=True,
        )
        return conversion, True

    @staticmethod
    @transaction.atomic
    def create_suggestion(
        *,
        tenant_id,
        created_by,
        suggestion_data,
    ):
        suggestion_data = dict(suggestion_data)
        idempotency_key = suggestion_data.get('idempotency_key', '') or ''
        if idempotency_key:
            existing = AISuggestion.objects.filter(tenant_id=tenant_id, idempotency_key=idempotency_key).first()
            if existing:
                return existing, False

        ai_request = suggestion_data.pop('ai_request', None)
        if ai_request and ai_request.tenant_id != tenant_id:
            raise ValueError('AI execution request is outside this tenant.')

        confidence_score = suggestion_data.get('confidence_score')
        if confidence_score is not None:
            score = Decimal(str(confidence_score))
            if score < Decimal('0.00') or score > Decimal('1.00'):
                raise ValueError('confidence_score must be between 0.00 and 1.00.')
            suggestion_data['confidence_score'] = score
        elif ai_request and hasattr(ai_request, 'result') and ai_request.result.confidence_score is not None:
            suggestion_data['confidence_score'] = ai_request.result.confidence_score

        suggestion_data['confidence_band'] = suggestion_data.get(
            'confidence_band',
            SuggestionService._derive_confidence_band(suggestion_data.get('confidence_score')),
        )
        suggestion_data['status'] = suggestion_data.get('status', SuggestionStatus.PENDING)
        suggestion_data['payload_json'] = SuggestionService._sanitize_json(suggestion_data.get('payload_json', {}))
        suggestion_data['rationale_json'] = SuggestionService._sanitize_json(suggestion_data.get('rationale_json', {}))
        suggestion_data['audit_metadata_json'] = SuggestionService._sanitize_json(suggestion_data.get('audit_metadata_json', {}))

        try:
            suggestion = AISuggestion.objects.create(
                tenant_id=tenant_id,
                created_by=created_by,
                ai_request=ai_request,
                **suggestion_data,
            )
            created = True
        except IntegrityError:
            if not idempotency_key:
                raise
            suggestion = AISuggestion.objects.get(tenant_id=tenant_id, idempotency_key=idempotency_key)
            created = False

        if created and suggestion.requires_approval and not suggestion.approval_item_id:
            approval_item = ApprovalQueueItem.objects.create(
                tenant_id=tenant_id,
                created_by=created_by,
                item_type='ai_suggestion',
                origin_type='ai_suggestion',
                origin_id=suggestion.id,
                requested_action='approve_suggestion',
                summary_payload_json={
                    'suggestion_id': str(suggestion.id),
                    'category': suggestion.category,
                    'title': suggestion.title,
                    'owner_module': suggestion.owner_module,
                    'proposed_action_family': suggestion.proposed_action_family,
                    'source_entity_type': suggestion.source_entity_type,
                    'source_entity_id': suggestion.source_entity_id,
                },
                recommended_decision='approve',
                approver_role='tenant_admin',
                status=ApprovalStatus.PENDING,
            )
            suggestion.approval_item = approval_item
            suggestion.save(update_fields=['approval_item', 'updated_at'])

        if created:
            AuditService.log(
                tenant_id=tenant_id,
                actor_id=created_by,
                actor_type='system' if created_by is None else 'user',
                action_type='ai_suggestion.created',
                target_type='ai_suggestion',
                target_id=suggestion.id,
                after_state_json={
                    'status': suggestion.status,
                    'category': suggestion.category,
                    'requires_approval': suggestion.requires_approval,
                },
                metadata_json={'source_entity_type': suggestion.source_entity_type, 'source_entity_id': suggestion.source_entity_id},
            )
            SuggestionService._schedule_automation_intelligence_evaluation(suggestion_id=suggestion.id)
        return suggestion, created

    @staticmethod
    def create_from_ai_execution(
        *,
        tenant_id,
        created_by,
        ai_request,
        suggestion_data,
    ):
        if ai_request.tenant_id != tenant_id:
            raise ValueError('AI execution request is outside this tenant.')
        result = getattr(ai_request, 'result', None)
        merged = {
            **suggestion_data,
            'source_event': suggestion_data.get('source_event', ai_request.source_event),
            'source_module': suggestion_data.get('source_module', ai_request.source_module),
            'source_entity_type': suggestion_data.get('source_entity_type', ai_request.source_entity_type),
            'source_entity_id': suggestion_data.get('source_entity_id', ai_request.source_entity_id),
            'ai_request': ai_request,
        }
        if result and result.confidence_score is not None and 'confidence_score' not in merged:
            merged['confidence_score'] = result.confidence_score
        return SuggestionService.create_suggestion(tenant_id=tenant_id, created_by=created_by, suggestion_data=merged)

    @staticmethod
    def _build_communication_draft_suggestion_data(*, ai_request):
        result = getattr(ai_request, 'result', None)
        if not result:
            raise ValueError('AI execution result is required before suggestion creation.')

        output = result.normalized_output_json or {}
        subject = str(output.get('subject', '') or '').strip()
        body = str(output.get('body', '') or '').strip()
        if not subject or not body:
            raise ValueError('Communication draft output must contain non-empty subject and body.')

        confidence_score = result.confidence_score
        if confidence_score is not None and Decimal(str(confidence_score)) < SuggestionService.LOW_CONFIDENCE_THRESHOLD:
            raise ValueError('Communication draft output confidence is below the safe suggestion threshold.')

        return {
            'suggestion_key': 'communication_draft',
            'category': SuggestionCategory.COMMUNICATION_DRAFT,
            'source_event': ai_request.source_event,
            'source_module': ai_request.source_module,
            'source_entity_type': ai_request.source_entity_type,
            'source_entity_id': ai_request.source_entity_id,
            'owner_module': 'communications',
            'proposed_action_family': 'enqueue_communication',
            'title': f'Draft communication for {ai_request.source_entity_type}',
            'summary': subject,
            'confidence_score': confidence_score,
            'payload_json': {
                'suggestion_subtype': 'email_draft',
                'channel': 'email',
                'subject': subject,
                'body': body,
                'source_event': ai_request.source_event,
                'source_entity_type': ai_request.source_entity_type,
                'source_entity_id': ai_request.source_entity_id,
                'use_case_key': ai_request.use_case_key,
            },
            'rationale_json': {
                'ai_execution_id': str(ai_request.id),
                'module_scope': ai_request.module_scope,
                'use_case_key': ai_request.use_case_key,
            },
            'audit_metadata_json': {
                'source': 'ai_execution',
                'ai_execution_id': str(ai_request.id),
            },
            'manual_override_allowed': True,
            'requires_approval': False,
            'idempotency_key': f'ai-suggestion:{ai_request.id}:communication_draft',
        }

    @staticmethod
    def _build_followup_recommendation_suggestion_data(*, ai_request):
        result = getattr(ai_request, 'result', None)
        if not result:
            raise ValueError('AI execution result is required before suggestion creation.')

        output = result.normalized_output_json or {}
        summary = SuggestionService._first_non_empty_value(output, 'summary', 'recommendation_summary', 'headline')
        reason = SuggestionService._first_non_empty_value(output, 'reason', 'rationale', 'why')
        if not summary and not reason:
            raise ValueError('Follow-up recommendation output must include a non-empty summary or rationale.')

        confidence_score = result.confidence_score
        if confidence_score is not None and Decimal(str(confidence_score)) < SuggestionService.LOW_CONFIDENCE_THRESHOLD:
            raise ValueError('Follow-up recommendation output confidence is below the safe suggestion threshold.')

        channel = str(SuggestionService._first_non_empty_value(output, 'channel') or 'email').strip().lower()
        followup_type = str(
            SuggestionService._first_non_empty_value(output, 'followup_type', 'recommendation_type') or 'generic_followup'
        ).strip()
        template_key = SuggestionService._first_non_empty_value(output, 'template_key')
        recipient_hint = SuggestionService._first_non_empty_value(output, 'recipient_hint', 'recipient_role', 'recipient_type')
        urgency = SuggestionService._first_non_empty_value(output, 'urgency', 'priority')
        recommended_window = SuggestionService._first_non_empty_value(
            output,
            'recommended_window',
            'suggested_timing',
            'timing_hint',
        )
        delay_hours = SuggestionService._first_non_empty_value(output, 'delay_hours', 'followup_in_hours', 'recommended_delay_hours')

        payload = {
            'suggestion_subtype': 'followup_recommendation',
            'recommended_action': 'enqueue_communication',
            'channel': channel,
            'followup_type': followup_type,
            'template_key': template_key or 'followup',
            'recipient_hint': recipient_hint or '',
            'recommended_window': recommended_window or '',
            'delay_hours': delay_hours,
            'urgency': urgency or '',
            'summary': summary or reason,
            'reason': reason or '',
            'source_event': ai_request.source_event,
            'source_entity_type': ai_request.source_entity_type,
            'source_entity_id': ai_request.source_entity_id,
            'use_case_key': ai_request.use_case_key,
        }

        rationale_json = {
            'ai_execution_id': str(ai_request.id),
            'module_scope': ai_request.module_scope,
            'use_case_key': ai_request.use_case_key,
        }
        decision_factors = output.get('decision_factors')
        if decision_factors not in (None, ''):
            rationale_json['decision_factors'] = SuggestionService._sanitize_json(decision_factors)
        if reason:
            rationale_json['reason'] = reason
        signals = output.get('signals')
        if signals not in (None, ''):
            rationale_json['signals'] = SuggestionService._sanitize_json(signals)

        return {
            'suggestion_key': 'followup_recommendation',
            'category': SuggestionCategory.FOLLOWUP_RECOMMENDATION,
            'source_event': ai_request.source_event,
            'source_module': ai_request.source_module,
            'source_entity_type': ai_request.source_entity_type,
            'source_entity_id': ai_request.source_entity_id,
            'owner_module': 'communications',
            'proposed_action_family': 'enqueue_communication',
            'title': f'Recommend follow-up for {ai_request.source_entity_type}',
            'summary': str(summary or reason),
            'confidence_score': confidence_score,
            'payload_json': payload,
            'rationale_json': rationale_json,
            'audit_metadata_json': {
                'source': 'ai_execution',
                'ai_execution_id': str(ai_request.id),
                'bounded_use_case': 'followup_recommendation',
            },
            'manual_override_allowed': True,
            'requires_approval': False,
            'idempotency_key': f'ai-suggestion:{ai_request.id}:followup_recommendation',
        }

    @staticmethod
    def create_supported_suggestion_from_ai_execution(*, ai_request):
        mapper_key = (ai_request.module_scope, ai_request.use_case_key)
        mapper = SuggestionService.SUPPORTED_AI_EXECUTION_MAPPERS.get(mapper_key)
        if not mapper:
            return None, False, 'unsupported'

        if ai_request.tenant_id is None:
            raise ValueError('AI execution request must belong to a tenant.')

        if mapper == 'communication_draft':
            suggestion_data = SuggestionService._build_communication_draft_suggestion_data(ai_request=ai_request)
        elif mapper == 'followup_recommendation':
            suggestion_data = SuggestionService._build_followup_recommendation_suggestion_data(ai_request=ai_request)
        else:
            return None, False, 'unsupported'

        suggestion, created = SuggestionService.create_from_ai_execution(
            tenant_id=ai_request.tenant_id,
            created_by=ai_request.created_by,
            ai_request=ai_request,
            suggestion_data=suggestion_data,
        )
        return suggestion, created, 'created' if created else 'duplicate'

    @staticmethod
    def review_suggestion(*, suggestion, user_id, status_value, comment=''):
        if status_value == SuggestionStatus.REJECTED:
            return SuggestionService.reject_suggestion(suggestion=suggestion, user_id=user_id, comment=comment)
        if status_value not in {SuggestionStatus.PENDING, SuggestionStatus.PENDING_REVIEW}:
            raise ValueError('Unsupported review status.')
        if suggestion.status in SuggestionService.TERMINAL_STATUSES:
            raise ValueError('Terminal suggestions cannot be reviewed.')
        suggestion.status = SuggestionStatus.PENDING
        suggestion.review_comment = comment
        suggestion.reviewed_by_id = user_id
        suggestion.reviewed_at = timezone.now()
        suggestion.save(update_fields=['status', 'review_comment', 'reviewed_by_id', 'reviewed_at', 'updated_at'])
        AuditService.log(
            tenant_id=suggestion.tenant_id,
            actor_id=user_id,
            action_type='ai_suggestion.reviewed',
            target_type='ai_suggestion',
            target_id=suggestion.id,
            after_state_json={'status': suggestion.status},
            metadata_json={'comment': comment},
        )
        return suggestion

    @staticmethod
    def approve_suggestion(*, suggestion, user_id, comment=''):
        if suggestion.status not in SuggestionService.GOVERNABLE_PENDING_STATUSES:
            raise ValueError('Only pending suggestions can be approved.')
        if suggestion.approval_item_id and suggestion.approval_item.status == ApprovalStatus.PENDING:
            ApprovalService.approve(suggestion.approval_item, user_id, comment, apply_now=False)
        suggestion.status = SuggestionStatus.APPROVED
        suggestion.approval_comment = comment
        suggestion.approved_by_id = user_id
        suggestion.approved_at = timezone.now()
        suggestion.reviewed_by_id = user_id
        suggestion.reviewed_at = suggestion.approved_at
        suggestion.save(
            update_fields=[
                'status',
                'approval_comment',
                'approved_by_id',
                'approved_at',
                'reviewed_by_id',
                'reviewed_at',
                'updated_at',
            ]
        )
        AuditService.log(
            tenant_id=suggestion.tenant_id,
            actor_id=user_id,
            action_type='ai_suggestion.approved',
            target_type='ai_suggestion',
            target_id=suggestion.id,
            after_state_json={'status': suggestion.status},
            metadata_json={'comment': comment},
        )
        return suggestion

    @staticmethod
    def reject_suggestion(*, suggestion, user_id, comment=''):
        if suggestion.status not in SuggestionService.GOVERNABLE_PENDING_STATUSES:
            raise ValueError('Only pending suggestions can be rejected.')
        if suggestion.approval_item_id and suggestion.approval_item.status == ApprovalStatus.PENDING:
            ApprovalService.reject(suggestion.approval_item, user_id, comment)
        now = timezone.now()
        suggestion.status = SuggestionStatus.REJECTED
        suggestion.review_comment = comment
        suggestion.rejection_reason = comment
        suggestion.reviewed_by_id = user_id
        suggestion.reviewed_at = now
        suggestion.rejected_by_id = user_id
        suggestion.rejected_at = now
        suggestion.save(
            update_fields=[
                'status',
                'review_comment',
                'rejection_reason',
                'reviewed_by_id',
                'reviewed_at',
                'rejected_by_id',
                'rejected_at',
                'updated_at',
            ]
        )
        AuditService.log(
            tenant_id=suggestion.tenant_id,
            actor_id=user_id,
            action_type='ai_suggestion.rejected',
            target_type='ai_suggestion',
            target_id=suggestion.id,
            after_state_json={'status': suggestion.status},
            metadata_json={'comment': comment},
        )
        return suggestion

    @staticmethod
    def dismiss_suggestion(*, suggestion, user_id, comment=''):
        if suggestion.status not in SuggestionService.GOVERNABLE_PENDING_STATUSES:
            raise ValueError('Only pending suggestions can be dismissed.')
        now = timezone.now()
        suggestion.status = SuggestionStatus.DISMISSED
        suggestion.dismissal_comment = comment
        suggestion.dismissed_by_id = user_id
        suggestion.dismissed_at = now
        suggestion.save(
            update_fields=['status', 'dismissal_comment', 'dismissed_by_id', 'dismissed_at', 'updated_at']
        )
        AuditService.log(
            tenant_id=suggestion.tenant_id,
            actor_id=user_id,
            action_type='ai_suggestion.dismissed',
            target_type='ai_suggestion',
            target_id=suggestion.id,
            after_state_json={'status': suggestion.status},
            metadata_json={'comment': comment},
        )
        return suggestion

    @staticmethod
    @transaction.atomic
    def apply_suggestion(*, suggestion, user_id, comment='', override_payload_json=None, idempotency_key=''):
        if suggestion.status != SuggestionStatus.APPROVED:
            raise ValueError('Suggestion must be approved before apply.')
        if override_payload_json is not None and not suggestion.manual_override_allowed:
            raise ValueError('Manual override is not allowed for this suggestion.')

        payload = SuggestionService._sanitize_json(override_payload_json if override_payload_json is not None else suggestion.payload_json)
        conversion, created = SuggestionService._create_apply_conversion(
            suggestion=suggestion,
            user_id=user_id,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        if not created:
            return conversion, conversion.status == SuggestionConversionStatus.CONVERTED

        try:
            result = SuggestionService._execute_apply(suggestion=suggestion, user_id=user_id, payload=payload)
            now = timezone.now()
            contract_payload = result.as_contract_payload()
            conversion.status = SuggestionConversionStatus.CONVERTED
            conversion.retry_safe = result.retry_safe
            conversion.result_payload_json = contract_payload
            conversion.save(update_fields=['status', 'retry_safe', 'result_payload_json', 'updated_at'])

            suggestion.status = SuggestionStatus.APPLIED
            suggestion.apply_comment = comment
            suggestion.applied_by_id = user_id
            suggestion.applied_at = now
            suggestion.last_apply_status = result.execution_status()
            suggestion.last_apply_error_message = ''
            suggestion.last_apply_result_json = {
                'owner_module': suggestion.owner_module,
                'proposed_action_family': suggestion.proposed_action_family,
                'target_type': result.target_type,
                'target_id': str(result.target_id) if result.target_id else '',
                'retry_safe': result.retry_safe,
                'result': contract_payload,
            }
            suggestion.converted_artifact_type = result.target_type
            suggestion.converted_artifact_id = result.target_id or None
            suggestion.converted_by_id = user_id
            suggestion.converted_at = now
            suggestion.save(
                update_fields=[
                    'status',
                    'apply_comment',
                    'applied_by_id',
                    'applied_at',
                    'last_apply_status',
                    'last_apply_error_message',
                    'last_apply_result_json',
                    'converted_artifact_type',
                    'converted_artifact_id',
                    'converted_by_id',
                    'converted_at',
                    'updated_at',
                ]
            )
            AuditService.log(
                tenant_id=suggestion.tenant_id,
                actor_id=user_id,
                action_type='ai_suggestion.applied',
                target_type='ai_suggestion',
                target_id=suggestion.id,
                after_state_json={'status': suggestion.status, 'apply_status': suggestion.last_apply_status},
                metadata_json={'conversion_id': str(conversion.id), 'comment': comment},
            )
            return conversion, True
        except OwnerContractError as exc:
            conversion.status = SuggestionConversionStatus.FAILED
            conversion.error_category = exc.error_category
            conversion.error_message = str(exc)
            conversion.retry_safe = exc.retry_safe
            conversion.save(
                update_fields=['status', 'error_category', 'error_message', 'retry_safe', 'updated_at']
            )
            suggestion.apply_comment = comment
            suggestion.status = SuggestionStatus.APPLY_FAILED
            suggestion.last_apply_status = SuggestionStatus.APPLY_FAILED
            suggestion.last_apply_error_message = str(exc)
            suggestion.last_apply_result_json = {
                'owner_module': suggestion.owner_module,
                'proposed_action_family': suggestion.proposed_action_family,
                'error_category': exc.error_category,
                'retry_safe': exc.retry_safe,
            }
            suggestion.save(
                update_fields=[
                    'status',
                    'apply_comment',
                    'last_apply_status',
                    'last_apply_error_message',
                    'last_apply_result_json',
                    'updated_at',
                ]
            )
            AuditService.log(
                tenant_id=suggestion.tenant_id,
                actor_id=user_id,
                action_type='ai_suggestion.apply_failed',
                target_type='ai_suggestion',
                target_id=suggestion.id,
                after_state_json={'status': suggestion.status, 'apply_status': suggestion.last_apply_status},
                metadata_json={'conversion_id': str(conversion.id), 'error_category': exc.error_category},
            )
            return conversion, False
        except Exception as exc:
            conversion.status = SuggestionConversionStatus.FAILED
            conversion.error_category = 'owner_contract_unhandled'
            conversion.error_message = str(exc)
            conversion.retry_safe = True
            conversion.save(
                update_fields=['status', 'error_category', 'error_message', 'retry_safe', 'updated_at']
            )
            suggestion.status = SuggestionStatus.APPLY_FAILED
            suggestion.apply_comment = comment
            suggestion.last_apply_status = SuggestionStatus.APPLY_FAILED
            suggestion.last_apply_error_message = str(exc)
            suggestion.last_apply_result_json = {
                'owner_module': suggestion.owner_module,
                'proposed_action_family': suggestion.proposed_action_family,
                'error_category': 'owner_contract_unhandled',
                'retry_safe': True,
            }
            suggestion.save(
                update_fields=[
                    'status',
                    'apply_comment',
                    'last_apply_status',
                    'last_apply_error_message',
                    'last_apply_result_json',
                    'updated_at',
                ]
            )
            AuditService.log(
                tenant_id=suggestion.tenant_id,
                actor_id=user_id,
                action_type='ai_suggestion.apply_failed',
                target_type='ai_suggestion',
                target_id=suggestion.id,
                after_state_json={'status': suggestion.status, 'apply_status': suggestion.last_apply_status},
                metadata_json={'conversion_id': str(conversion.id), 'error_category': 'owner_contract_unhandled'},
            )
            return conversion, False

    @staticmethod
    @transaction.atomic
    def convert_suggestion(
        *,
        suggestion,
        user_id,
        conversion_type,
        override_payload_json=None,
        idempotency_key='',
    ):
        if conversion_type == 'apply':
            return SuggestionService.apply_suggestion(
                suggestion=suggestion,
                user_id=user_id,
                override_payload_json=override_payload_json,
                idempotency_key=idempotency_key,
            )

        if suggestion.status in {SuggestionStatus.REJECTED, SuggestionStatus.DISMISSED, SuggestionStatus.EXPIRED, SuggestionStatus.SUPERSEDED, SuggestionStatus.FAILED}:
            raise ValueError('Suggestion cannot be converted from its current status.')
        if suggestion.requires_approval and suggestion.status != SuggestionStatus.APPROVED:
            raise ValueError('Suggestion approval is required before conversion.')
        if override_payload_json is not None and not suggestion.manual_override_allowed:
            raise ValueError('Manual override is not allowed for this suggestion.')

        if suggestion.status == SuggestionStatus.CONVERTED:
            existing = suggestion.conversions.filter(conversion_type=conversion_type).order_by('-created_at').first()
            if existing:
                return existing, False
            raise ValueError('Suggestion is already converted.')

        effective_idempotency_key = idempotency_key or f'ai-suggestion:{suggestion.id}:{conversion_type}'
        existing = AISuggestionConversion.objects.filter(
            tenant_id=suggestion.tenant_id,
            idempotency_key=effective_idempotency_key,
        ).first()
        if existing:
            return existing, False

        requested_payload = SuggestionService._base_requested_payload(
            suggestion=suggestion,
            payload=override_payload_json if override_payload_json is not None else suggestion.payload_json,
        )
        conversion = AISuggestionConversion.objects.create(
            tenant_id=suggestion.tenant_id,
            created_by=user_id,
            suggestion=suggestion,
            conversion_type=conversion_type,
            idempotency_key=effective_idempotency_key,
            requested_by_id=user_id,
            requested_action_payload_json=requested_payload,
            retry_safe=True,
        )

        try:
            approval_item = ApprovalQueueItem.objects.create(
                tenant_id=suggestion.tenant_id,
                created_by=user_id,
                item_type='ai_suggestion_action',
                origin_type='ai_suggestion',
                origin_id=suggestion.id,
                requested_action=suggestion.proposed_action_family or conversion_type,
                summary_payload_json=requested_payload,
                recommended_decision='review',
                approver_role='tenant_admin',
                status=ApprovalStatus.PENDING,
            )
            conversion.status = SuggestionConversionStatus.CONVERTED
            conversion.approval_item = approval_item
            conversion.result_payload_json = {
                'artifact_type': 'approval_queue_item',
                'artifact_id': str(approval_item.id),
                'artifact_status': approval_item.status,
            }
            conversion.save(update_fields=['status', 'approval_item', 'result_payload_json', 'updated_at'])

            suggestion.status = SuggestionStatus.CONVERTED
            suggestion.converted_artifact_type = 'approval_queue_item'
            suggestion.converted_artifact_id = approval_item.id
            suggestion.converted_by_id = user_id
            suggestion.converted_at = timezone.now()
            suggestion.save(
                update_fields=[
                    'status',
                    'converted_artifact_type',
                    'converted_artifact_id',
                    'converted_by_id',
                    'converted_at',
                    'updated_at',
                ]
            )
        except Exception as exc:
            conversion.status = SuggestionConversionStatus.FAILED
            conversion.error_category = 'conversion'
            conversion.error_message = str(exc)
            conversion.retry_safe = True
            conversion.save(update_fields=['status', 'error_category', 'error_message', 'retry_safe', 'updated_at'])
            raise

        AuditService.log(
            tenant_id=suggestion.tenant_id,
            actor_id=user_id,
            action_type='ai_suggestion.converted',
            target_type='ai_suggestion',
            target_id=suggestion.id,
            after_state_json={'status': suggestion.status},
            metadata_json={'conversion_id': str(conversion.id), 'conversion_type': conversion_type},
        )
        return conversion, True
