from django.utils import timezone

from apps.orchestration_center.constants.execution_statuses import ApprovalMode, ApprovalStatus, ScheduledActionStatus
from apps.orchestration_center.models import AutomationScheduledAction
from apps.orchestration_center.services.ai_execution_service import AIExecutionService
from apps.orchestration_center.services.audit_service import AuditService
from apps.orchestration_center.services.communication_binding_service import CommunicationBindingService
from apps.agencies.services import AgencyAssignmentService, AgencyOperationalFlagService
from apps.candidates.services import CandidateAssignmentService, CandidateOperationalFlagService
from apps.pipeline.services import PipelineDeadlineService
from apps.interviews.services import InterviewReviewTaskService
from shared.owner_contracts import OwnerActionContext


class AutomationActionExecutor:
    EXECUTOR_MAP = {
        'invoke_ai_execution': '_execute_invoke_ai_execution',
        'notify': '_execute_notify',
        'create_deadline': '_execute_create_deadline',
        'escalate': '_execute_escalate',
        'assign': '_execute_assign',
        'schedule_followup': '_execute_schedule_followup',
        'create_review_task': '_execute_create_review_task',
        'enqueue_communication': '_execute_enqueue_communication',
        'mark_flag': '_execute_mark_flag',
        # ── Notification Orchestration actions ────────────────────────────────
        'send_email':       '_execute_send_orchestrated_notification',
        'send_whatsapp':    '_execute_send_orchestrated_notification',
        'notify_user':      '_execute_send_orchestrated_notification',
        'send_notification':'_execute_send_orchestrated_notification',
        # ── Task Orchestration actions ─────────────────────────────────────────
        'create_task':      '_execute_create_orchestrated_task',
    }

    @staticmethod
    def execute(*, run, action):
        handler_name = AutomationActionExecutor.EXECUTOR_MAP.get(action.action_type)
        if not handler_name:
            return {
                'action_type': action.action_type,
                'status': 'recorded',
                'payload': action.action_config_json,
            }
        result = getattr(AutomationActionExecutor, handler_name)(run=run, action=action)
        AuditService.log(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            actor_type='system',
            action_type=f'automation_action.{action.action_type}',
            target_type='automation_execution_run',
            target_id=run.id,
            after_state_json=result,
            metadata_json={'action_type': action.action_type, 'result_status': result.get('status')},
        )
        return result

    @staticmethod
    def _build_owner_context(*, run, action, config: dict, suffix: str, extra_audit_metadata: dict | None = None):
        external_reference = config.get('external_reference', f'{run.id}:{getattr(action, "id", "scheduled")}:{suffix}')
        return OwnerActionContext(
            tenant_id=run.tenant_id,
            actor_id=run.created_by,
            external_reference=external_reference,
            audit_metadata={
                'automation_run_id': str(run.id),
                'rule_id': str(run.rule_id),
                'source_event': run.source_event,
                'source_entity_type': run.source_entity_type,
                'source_entity_id': run.source_entity_id,
                **(extra_audit_metadata or {}),
            },
        )

    @staticmethod
    def _execute_invoke_ai_execution(*, run, action):
        use_case_key = action.action_config_json.get('use_case_key', 'automation_assist')
        try:
            request, _ = AIExecutionService.create_request(
                tenant_id=run.tenant_id,
                created_by=run.created_by,
                module_scope=run.rule.module_scope,
                use_case_key=use_case_key,
                source_module=run.source_module,
                source_entity_type=run.source_entity_type,
                source_entity_id=run.source_entity_id,
                source_event=run.source_event,
                context_snapshot=run.trigger_payload_json,
                mode=run.mode,
                requires_review=run.mode == ApprovalMode.APPROVAL_REQUIRED,
                requires_approval=run.mode == ApprovalMode.APPROVAL_REQUIRED,
                idempotency_key=f'{run.id}:{getattr(action, "id", "scheduled")}:{use_case_key}',
            )
        except ValueError:
            return {
                'action_type': action.action_type,
                'status': 'skipped',
                'reason': f'prompt_missing:{use_case_key}',
            }
        from apps.orchestration_center.tasks.ai_tasks import execute_ai_request

        execute_ai_request.delay(str(request.id))
        return {
            'action_type': action.action_type,
            'status': 'queued',
            'linked_ai_execution_id': str(request.id),
            'use_case_key': use_case_key,
        }

    @staticmethod
    def _execute_notify(*, run, action):
        config = action.action_config_json or {}
        channel = config.get('channel', 'in_app')
        notification_style = config.get('notification_style')
        if not notification_style:
            if config.get('notification_type') == 'escalation_alert' or action.action_type == 'escalate_notification':
                notification_style = 'escalation'
            else:
                notification_style = 'reminder'
        config = {**config, 'notification_style': notification_style}
        results = []
        if channel in {'in_app', 'both'}:
            results.append(
                CommunicationBindingService.dispatch_in_app_notification_from_automation(
                    run=run,
                    action_type=action.action_type,
                    config=config,
                )
            )
        if channel in {'email', 'both'}:
            results.append(
                CommunicationBindingService.queue_email_from_automation(
                    run=run,
                    action_type=action.action_type,
                    config=config,
                )
            )
        if not results:
            return {
                'action_type': action.action_type,
                'status': 'skipped',
                'reason': 'unsupported_notification_channel',
                'channel': channel,
            }
        statuses = {item.get('status') for item in results}
        if 'failed' in statuses:
            status_value = 'failed'
        elif 'completed' in statuses or 'queued' in statuses:
            status_value = 'completed' if statuses <= {'completed'} else 'partial'
        else:
            status_value = 'skipped'
        return {
            'action_type': action.action_type,
            'status': status_value,
            'channel': channel,
            'results': results,
        }

    @staticmethod
    def _execute_create_deadline(*, run, action):
        config = action.action_config_json or {}
        context = AutomationActionExecutor._build_owner_context(
            run=run,
            action=action,
            config=config,
            suffix='create_deadline',
            extra_audit_metadata={
                'deadline_type': config.get('deadline_type', 'followup'),
                'owner_role': config.get('owner_role', 'recruiter'),
                'created_via': 'automation_action',
            },
        )
        result = PipelineDeadlineService.create_from_orchestration(
            context=context,
            entity_type=config.get('entity_type', run.source_entity_type),
            entity_id=config.get('entity_id', run.source_entity_id),
            action_required=config.get('action_required', config.get('deadline_type', 'followup')),
            due_in_hours=int(config.get('due_in_hours', 24)),
            assigned_to=config.get('assigned_to') or run.created_by,
            escalate_to=config.get('escalate_to'),
            deadline_type=config.get('deadline_type', 'followup'),
            owner_role=config.get('owner_role', 'recruiter'),
        )
        return result.as_execution_payload(action_type=action.action_type)

    @staticmethod
    def _execute_escalate(*, run, action):
        config = action.action_config_json or {}
        if not (config.get('deadline_entity_type') or config.get('deadline_action_required') or run.source_entity_type in {'application', 'deadline'}):
            return {
                'action_type': action.action_type,
                'status': 'stubbed_unbound',
                'reason': 'escalation_owner_contract_not_available',
                'source_entity_type': run.source_entity_type,
                'source_entity_id': run.source_entity_id,
            }

        context = AutomationActionExecutor._build_owner_context(
            run=run,
            action=action,
            config={
                'external_reference': config.get('deadline_external_reference', '') if config.get('use_external_reference', False) else '',
            },
            suffix='escalate_deadline',
            extra_audit_metadata={
                'severity': config.get('severity', 'medium'),
                'escalation_reason': config.get('reason', run.source_event),
            },
        )
        deadline_result = PipelineDeadlineService.escalate_from_orchestration(
            context=context,
            entity_type=config.get('deadline_entity_type', run.source_entity_type),
            entity_id=config.get('deadline_entity_id', run.source_entity_id),
            action_required=config.get('deadline_action_required', ''),
            escalate_to=config.get('escalate_to'),
            severity=config.get('severity', 'medium'),
        )

        component_results = [
            {
                'binding': 'pipeline_deadline',
                **deadline_result.as_execution_payload(action_type=action.action_type),
            }
        ]

        if config.get('notify', True):
            try:
                notify_result = CommunicationBindingService.dispatch_in_app_notification_from_automation(
                    run=run,
                    action_type='escalate_notification',
                    config={
                        'notification_type': 'escalation_alert',
                        'notification_style': 'escalation',
                        'title': config.get('title', 'Escalation alert'),
                        'body': config.get('message') or config.get('reason', run.source_event),
                        'recipient_user_ids': config.get('recipient_user_ids', []),
                        'recipient_user_paths': config.get('recipient_user_paths', []),
                        'default_to_actor': config.get('default_to_actor', True),
                        'action_url': config.get('action_url', ''),
                        'dedupe_key': config.get('dedupe_key', ''),
                        'external_reference': config.get(
                            'notification_external_reference',
                            f'{run.id}:{getattr(action, "id", "scheduled")}:escalate_notification',
                        ),
                    },
                )
            except Exception as exc:
                notify_result = {
                    'action_type': 'escalate_notification',
                    'status': 'failed',
                    'error': str(exc),
                    'error_category': getattr(exc, 'error_category', 'unhandled_runtime_error'),
                    'retry_safe': getattr(exc, 'retry_safe', True),
                    'channel': 'in_app',
                }
            component_results.append(
                {
                    'binding': 'communications',
                    **notify_result,
                }
            )

        component_statuses = {item.get('status') for item in component_results}
        has_component_failure = 'failed' in component_statuses
        is_duplicate = deadline_result.duplicate and all(
            item.get('status') in {'deduplicated', 'skipped'} for item in component_results[1:]
        )
        aggregate_status = 'partial' if has_component_failure else deadline_result.execution_status()

        return {
            'action_type': action.action_type,
            'status': aggregate_status,
            'owner_module': deadline_result.owner_module,
            'action_family': deadline_result.action_family,
            'target_type': deadline_result.target_type,
            'target_id': deadline_result.target_id,
            'duplicate': is_duplicate,
            'retry_safe': all(item.get('retry_safe', True) for item in component_results),
            'audit_metadata': deadline_result.audit_metadata,
            'payload': {
                **deadline_result.payload,
                'severity': config.get('severity', 'medium'),
                'target_role': config.get('target_role', 'tenant_admin'),
                'escalation_reason': config.get('reason', run.source_event),
                'results': component_results,
            },
            **deadline_result.payload,
            'severity': config.get('severity', 'medium'),
            'target_role': config.get('target_role', 'tenant_admin'),
            'escalation_reason': config.get('reason', run.source_event),
            'results': component_results,
        }

    @staticmethod
    def _execute_assign(*, run, action):
        config = action.action_config_json or {}
        owner_module = config.get('owner_module')
        if owner_module == 'pipeline' or (run.source_entity_type in {'application', 'requisition'} and config.get('assignment_target') == 'deadline'):
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config={'external_reference': config.get('deadline_external_reference', '')},
                suffix='deadline_assign',
                extra_audit_metadata={'assignment_reason': config.get('assignment_reason', 'automation_rule')},
            )
            result = PipelineDeadlineService.assign_from_orchestration(
                context=context,
                entity_type=config.get('deadline_entity_type', config.get('entity_type', run.source_entity_type)),
                entity_id=config.get('deadline_entity_id', config.get('entity_id', run.source_entity_id)),
                assigned_to=config.get('assigned_to'),
                action_required=config.get('deadline_action_required', config.get('action_required', '')),
            )
            return result.as_execution_payload(action_type=action.action_type)
        if owner_module == 'interviews' or (run.source_entity_type == 'interview' and config.get('assignment_target') == 'review_task'):
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config={'external_reference': config.get('external_reference', '')},
                suffix='interview_assign',
                extra_audit_metadata={'assignment_reason': config.get('assignment_reason', 'automation_rule')},
            )
            result = InterviewReviewTaskService.assign_from_orchestration(
                context=context,
                interview_id=config.get('interview_id', run.source_entity_id),
                review_type=config.get('review_type', 'interview_review'),
                assigned_reviewer_id=config.get('assigned_reviewer_id'),
                assigned_role=config.get('assigned_role', ''),
            )
            return result.as_execution_payload(action_type=action.action_type)
        if owner_module == 'candidates' or (run.source_entity_type == 'candidate' and config.get('assignment_target') in {'candidate_owner', 'candidate'}):
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config=config,
                suffix='candidate_assign',
                extra_audit_metadata={'assignment_reason': config.get('assignment_reason', 'automation_rule')},
            )
            result = CandidateAssignmentService.assign_from_orchestration(
                context=context,
                candidate_id=config.get('candidate_id', config.get('entity_id', run.source_entity_id)),
                owner_user_id=config.get('owner_user_id', config.get('assigned_to')),
                sync_active_engagement=config.get('sync_active_engagement', True),
                assignment_reason=config.get('assignment_reason', 'automation_rule'),
            )
            return result.as_execution_payload(action_type=action.action_type)
        if owner_module == 'agencies' and config.get('assignment_target') in {'job_agency', 'agency_job_assignment'}:
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config=config,
                suffix='agency_assign',
                extra_audit_metadata={'assignment_reason': config.get('assignment_reason', 'automation_rule')},
            )
            result = AgencyAssignmentService.assign_from_orchestration(
                context=context,
                requisition_id=config.get('requisition_id', config.get('entity_id', run.source_entity_id)),
                agency_tenant_id=config.get('agency_tenant_id', config.get('assigned_to')),
                deadline=config.get('deadline'),
                max_submissions=config.get('max_submissions'),
                notes=config.get('notes', ''),
                assignment_reason=config.get('assignment_reason', 'automation_rule'),
            )
            return result.as_execution_payload(action_type=action.action_type)
        return {
            'action_type': action.action_type,
            'status': 'stubbed_unbound',
            'reason': 'assignment_owner_contract_not_available',
            'source_entity_type': run.source_entity_type,
            'source_entity_id': run.source_entity_id,
        }

    @staticmethod
    def _execute_schedule_followup(*, run, action):
        config = action.action_config_json or {}
        delay_seconds = int(config.get('delay_seconds', 3600))
        downstream_action_type = 'enqueue_communication' if config.get('channel', 'email') == 'email' else 'notify'
        dedupe_key = config.get(
            'dedupe_key',
            f'{run.id}:{getattr(action, "id", "scheduled")}:schedule_followup:{config.get("channel", "email")}:{config.get("followup_type", "generic_followup")}',
        )
        existing = AutomationScheduledAction.objects.filter(
            run=run,
            action_type=downstream_action_type,
            payload_json__schedule_followup_dedupe_key=dedupe_key,
            status__in=[ScheduledActionStatus.PENDING, ScheduledActionStatus.COMPLETED],
        ).order_by('-created_at').first()
        if existing:
            return {
                'action_type': action.action_type,
                'status': 'deduplicated',
                'scheduled_action_id': str(existing.id),
                'execute_at': existing.execute_at.isoformat(),
                'followup_type': config.get('followup_type', 'generic_followup'),
                'downstream_action_type': downstream_action_type,
            }

        scheduled = AutomationScheduledAction.objects.create(
            tenant_id=run.tenant_id,
            created_by=run.created_by,
            run=run,
            action_type=downstream_action_type,
            status=ScheduledActionStatus.PENDING,
            execute_at=timezone.now() + timezone.timedelta(seconds=delay_seconds),
            payload_json={
                'channel': config.get('channel', 'email'),
                'template_key': config.get('template_key', config.get('followup_type', 'followup')),
                'recipient_scope': config.get('recipient_scope', 'recruiter'),
                'recipient_paths': config.get('recipient_paths', []),
                'recipient_emails': config.get('recipient_emails', []),
                'message_purpose': config.get('message_purpose', 'followup'),
                'message': config.get('message', ''),
                'scheduled_from_action': 'schedule_followup',
                'followup_type': config.get('followup_type', 'generic_followup'),
                'schedule_followup_dedupe_key': dedupe_key,
                'external_reference': '',
            },
        )
        scheduled.payload_json['external_reference'] = f'{run.id}:{scheduled.id}:scheduled_followup'
        scheduled.save(update_fields=['payload_json', 'updated_at'])
        return {
            'action_type': action.action_type,
            'status': 'scheduled',
            'scheduled_action_id': str(scheduled.id),
            'execute_at': scheduled.execute_at.isoformat(),
            'followup_type': config.get('followup_type', 'generic_followup'),
            'downstream_action_type': downstream_action_type,
        }

    @staticmethod
    def _execute_create_review_task(*, run, action):
        config = action.action_config_json or {}
        due_at = None
        if config.get('due_in_hours'):
            due_at = timezone.now() + timezone.timedelta(hours=int(config.get('due_in_hours')))
        context = AutomationActionExecutor._build_owner_context(
            run=run,
            action=action,
            config=config,
            suffix=config.get('review_type', 'interview_review'),
            extra_audit_metadata={
                'requested_via': 'automation_action',
                'owner_module': config.get('owner_module', run.source_module),
            },
        )
        result = InterviewReviewTaskService.create_from_orchestration(
            context=context,
            owner_module=config.get('owner_module', run.source_module),
            entity_type=config.get('entity_type', run.source_entity_type),
            entity_id=config.get('entity_id', config.get('interview_id', run.source_entity_id)),
            review_type=config.get('review_type', 'interview_review'),
            assigned_role=config.get('assigned_role', 'hr_manager'),
            assigned_reviewer_id=config.get('assigned_reviewer_id'),
            due_at=due_at,
            notes=config.get('notes', ''),
            approval_required=run.mode == ApprovalMode.APPROVAL_REQUIRED or getattr(action, 'requires_approval', False),
            approver_role=config.get('approver_role', 'tenant_admin'),
        )
        return result.as_execution_payload(action_type=action.action_type)

    @staticmethod
    def _execute_enqueue_communication(*, run, action):
        config = action.action_config_json or {}
        if run.mode == ApprovalMode.APPROVAL_REQUIRED or getattr(action, 'requires_approval', False):
            return {
                'action_type': action.action_type,
                'status': 'pending_approval',
                'template_key': config.get('template_key', ''),
                'channel': config.get('channel', 'email'),
                'recipient_scope': config.get('recipient_scope', 'candidate'),
                'source_entity_type': run.source_entity_type,
                'source_entity_id': run.source_entity_id,
            }
        channel = config.get('channel', 'email')
        if channel in {'in_app', 'internal_notification'}:
            return CommunicationBindingService.dispatch_in_app_notification_from_automation(
                run=run,
                action_type=action.action_type,
                config={
                    **config,
                    'notification_type': config.get('notification_type', 'platform_notification'),
                    'notification_style': config.get('notification_style', 'communication'),
                },
            )
        if channel != 'email':
            return {
                'action_type': action.action_type,
                'status': 'stubbed_unbound',
                'reason': 'communication_channel_contract_not_available',
                'channel': channel,
            }
        return CommunicationBindingService.queue_email_from_automation(
            run=run,
            action_type=action.action_type,
            config=config,
        )

    @staticmethod
    def _execute_mark_flag(*, run, action):
        config = action.action_config_json or {}
        owner_module = config.get('owner_module')
        flag_key = config.get('flag_key', 'attention_needed')
        if owner_module == 'pipeline' or run.source_entity_type == 'application':
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config=config,
                suffix='pipeline_flag',
                extra_audit_metadata={'flag_reason': config.get('flag_reason', run.source_event)},
            )
            result = PipelineDeadlineService.mark_flag_from_orchestration(
                context=context,
                entity_type=config.get('entity_type', 'application' if run.source_entity_type == 'application' else 'deadline'),
                entity_id=config.get('entity_id', run.source_entity_id),
                flag_key=flag_key,
                flag_value=config.get('flag_value', True),
            )
            return result.as_execution_payload(action_type=action.action_type)
        if owner_module == 'interviews' or run.source_entity_type == 'interview':
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config=config,
                suffix='interview_flag',
                extra_audit_metadata={'flag_reason': config.get('flag_reason', run.source_event)},
            )
            result = InterviewReviewTaskService.mark_flag_from_orchestration(
                context=context,
                entity_type=config.get('entity_type', 'interview'),
                entity_id=config.get('entity_id', run.source_entity_id),
                flag_key=flag_key,
                flag_value=config.get('flag_value', True),
            )
            return result.as_execution_payload(action_type=action.action_type)
        if owner_module == 'candidates' or run.source_entity_type == 'candidate':
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config=config,
                suffix='candidate_flag',
                extra_audit_metadata={'flag_reason': config.get('flag_reason', run.source_event)},
            )
            result = CandidateOperationalFlagService.mark_flag_from_orchestration(
                context=context,
                entity_type=config.get('entity_type', 'candidate'),
                entity_id=config.get('entity_id', config.get('candidate_id', run.source_entity_id)),
                flag_key=flag_key,
                flag_value=config.get('flag_value', True),
                sync_active_engagement=config.get('sync_active_engagement', True),
            )
            return result.as_execution_payload(action_type=action.action_type)
        if owner_module == 'agencies':
            context = AutomationActionExecutor._build_owner_context(
                run=run,
                action=action,
                config=config,
                suffix='agency_flag',
                extra_audit_metadata={'flag_reason': config.get('flag_reason', run.source_event)},
            )
            result = AgencyOperationalFlagService.mark_flag_from_orchestration(
                context=context,
                entity_type=config.get('entity_type', 'job_assignment'),
                entity_id=config.get('entity_id', run.source_entity_id),
                flag_key=flag_key,
                flag_value=config.get('flag_value', True),
            )
            return result.as_execution_payload(action_type=action.action_type)
        return {
            'action_type': action.action_type,
            'status': 'stubbed_unbound',
            'reason': 'flag_owner_contract_not_available',
            'flag_key': flag_key,
        }

    # ── Notification Orchestration handler ────────────────────────────────────

    @staticmethod
    def _execute_send_orchestrated_notification(*, run, action):
        """
        Routes send_email / send_whatsapp / notify_user / send_notification
        through the WorkflowNotificationOrchestrator.

        Config keys (all optional):
          notification_rule_id  — UUID of a WorkflowNotificationRule to use
          channel               — override channel (email | whatsapp | in_app)
          recipient_type        — override recipient type
          notification_event    — event key for ad-hoc rules
          recipient_email       — direct recipient email
          recipient_phone       — direct recipient phone
          recipient_user_id     — direct recipient user_id
        """
        from apps.automation_notifications.models import (
            NotificationChannel,
            WorkflowNotificationRule,
        )
        from apps.automation_notifications.services.workflow_notification_orchestrator import (
            WorkflowNotificationOrchestrator,
        )

        config = action.action_config_json or {}

        # Derive channel from action type if not explicitly set
        channel_map = {
            'send_email':       NotificationChannel.EMAIL,
            'send_whatsapp':    NotificationChannel.WHATSAPP,
            'notify_user':      NotificationChannel.IN_APP,
            'send_notification':NotificationChannel.IN_APP,
        }
        channel = config.get('channel') or channel_map.get(action.action_type, NotificationChannel.IN_APP)

        # Try to load an explicit rule
        rule = None
        rule_id = config.get('notification_rule_id')
        if rule_id:
            rule = WorkflowNotificationRule.objects.filter(
                id=rule_id, tenant_id=run.tenant_id, is_deleted=False, is_active=True,
            ).first()

        # Synthesise an ad-hoc rule from config if none found
        if rule is None:
            rule = WorkflowNotificationRule(
                tenant_id=run.tenant_id,
                workflow_id=run.rule_id,
                notification_event=config.get('notification_event', run.source_event),
                recipient_type=config.get('recipient_type', 'workflow_owner'),
                channel=channel,
                fallback_channels=config.get('fallback_channels', [NotificationChannel.IN_APP]),
                throttle_window_minutes=int(config.get('throttle_window_minutes', 0)),
                dedupe_key_template=config.get('dedupe_key_template', ''),
            )

        # Build recipient override from explicit addresses in config
        recipient_override = None
        if config.get('recipient_email') or config.get('recipient_user_id'):
            recipient_override = {
                'user_id': config.get('recipient_user_id'),
                'email':   config.get('recipient_email', ''),
                'phone':   config.get('recipient_phone', ''),
            }

        result = WorkflowNotificationOrchestrator.dispatch(
            tenant_id=run.tenant_id,
            execution_id=run.id,
            workflow_id=run.rule_id,
            rule=rule,
            context=run.trigger_payload_json or {},
            recipient_override=recipient_override,
        )
        return {
            'action_type': action.action_type,
            'status': result.get('status', 'dispatched'),
            'orchestrator_result': result,
        }

    # ── Task Orchestration handler ─────────────────────────────────────────────

    @staticmethod
    def _execute_create_orchestrated_task(*, run, action):
        """
        Routes create_task action through the WorkflowTaskOrchestrator.

        Config keys:
          task_rule_id          — UUID of an existing WorkflowTaskRule (optional)
          task_title_template   — inline title if no rule_id given
          task_description_template — inline description
          assignee_type         — assigned_recruiter | hiring_manager | ...
          assignee_field        — dot-path for dynamic_field assignee type
          priority              — low | medium | high | urgent
          due_in_minutes        — SLA in minutes (default 1440)
          escalate_after_minutes— escalation threshold (default 2880)
          depends_on_task_id    — UUID of task this one depends on
        """
        from apps.automation_tasks.models import WorkflowTaskRule
        from apps.automation_tasks.services.workflow_task_orchestrator import (
            WorkflowTaskOrchestrator,
        )

        config = action.action_config_json or {}

        # Try to load an explicit rule
        rule = None
        rule_id = config.get('task_rule_id')
        if rule_id:
            rule = WorkflowTaskRule.objects.filter(
                id=rule_id, tenant_id=run.tenant_id, is_deleted=False, is_active=True,
            ).first()

        # Synthesise an ad-hoc rule from config if none found
        if rule is None:
            rule = WorkflowTaskRule(
                tenant_id=run.tenant_id,
                workflow_id=run.rule_id,
                task_title_template=config.get('task_title_template', 'Workflow task'),
                task_description_template=config.get('task_description_template', ''),
                assignee_type=config.get('assignee_type', 'workflow_owner'),
                assignee_field=config.get('assignee_field', ''),
                priority=config.get('priority', 'medium'),
                due_in_minutes=int(config.get('due_in_minutes', 1440)),
                escalate_after_minutes=int(config.get('escalate_after_minutes', 2880)),
            )

        task = WorkflowTaskOrchestrator.create_task_from_workflow(
            tenant_id=run.tenant_id,
            workflow_id=run.rule_id,
            execution_id=run.id,
            rule=rule,
            context=run.trigger_payload_json or {},
            depends_on_task_id=config.get('depends_on_task_id'),
        )

        return {
            'action_type': action.action_type,
            'status': 'task_created',
            'task_id': str(task.id),
            'task_title': task.task_title,
            'assignee_user_id': str(task.assignee_user_id) if task.assignee_user_id else None,
            'due_at': task.due_at.isoformat() if task.due_at else None,
        }
