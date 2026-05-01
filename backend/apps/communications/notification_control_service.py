"""
Notification Control Service
==============================
Admin-side service for managing notification rules, channel settings,
and default preferences.  Also exposes the runtime helper used by
NotificationService to apply per-tenant rule overrides.
"""
import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.communications.notification_control_models import (
    NotificationRule,
    NotificationChannelSetting,
    TenantNotificationPreferenceDefaults,
    NotificationRuleCategory,
)
from apps.communications.notification_control_defaults import DEFAULT_NOTIFICATION_RULES

logger = logging.getLogger(__name__)

# Severity → minutes (used when no rule exists for the tenant)
_SEVERITY_TO_FALLBACK_MINUTES = {
    'info':     None,
    'medium':   40,
    'high':     10,
    'critical': 1,
}
_SEVERITY_TO_ESCALATION_MINUTES = {
    'high':     60,
    'critical': 5,
}


# ---------------------------------------------------------------------------
# NotificationControlService
# ---------------------------------------------------------------------------

class NotificationControlService:

    # ── Runtime integration (called by NotificationService) ─────────────────

    @staticmethod
    def get_rule(*, tenant_id, event_key) -> Optional[NotificationRule]:
        """
        Return the best matching rule for (tenant_id, event_key).

        Lookup order:
          1. Tenant-specific rule
          2. System default (tenant_id=None)
          3. None — caller uses hardcoded defaults
        """
        if tenant_id:
            rule = NotificationRule.objects.filter(
                tenant_id=tenant_id,
                event_key=event_key,
                is_deleted=False,
            ).first()
            if rule:
                return rule
        # Fall through to system default
        return NotificationRule.objects.filter(
            tenant_id=None,
            event_key=event_key,
            is_deleted=False,
            is_system=True,
        ).first()

    @staticmethod
    def channel_enabled(*, tenant_id, channel: str) -> bool:
        """
        Return False only if admin has explicitly disabled a channel.
        Defaults to True when no setting exists.
        """
        setting = NotificationChannelSetting.objects.filter(
            tenant_id=tenant_id,
            channel_type=channel,
        ).first()
        return setting.is_enabled if setting else True

    # ── Rule CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def list_rules(*, tenant_id) -> list:
        """
        Return merged rule list: system defaults + tenant overrides.
        Tenant-specific rows override system defaults for the same event_key.
        """
        # Ensure defaults exist for this tenant
        NotificationControlService._ensure_defaults_seeded(tenant_id=tenant_id)

        # Fetch all tenant rules
        tenant_rules = {
            r.event_key: r
            for r in NotificationRule.objects.filter(
                tenant_id=tenant_id,
                is_deleted=False,
            )
        }
        # Fetch system defaults for any keys not yet overridden
        system_rules = NotificationRule.objects.filter(
            tenant_id=None,
            is_system=True,
            is_deleted=False,
        )

        result = {}
        for sr in system_rules:
            if sr.event_key in tenant_rules:
                result[sr.event_key] = tenant_rules[sr.event_key]
            else:
                result[sr.event_key] = sr

        # Include any tenant-only rules (no system default)
        for key, rule in tenant_rules.items():
            if key not in result:
                result[key] = rule

        return sorted(result.values(), key=lambda r: (r.category, r.business_label))

    @staticmethod
    @transaction.atomic
    def upsert_rule(*, tenant_id, event_key: str, updated_by=None, **fields) -> NotificationRule:
        """Create or update a tenant-specific rule for the given event_key."""
        rule, created = NotificationRule.objects.get_or_create(
            tenant_id=tenant_id,
            event_key=event_key,
            defaults={
                'business_label': fields.get('business_label', event_key),
                'category': fields.get('category', NotificationRuleCategory.SYSTEM),
                'is_system': False,
            },
        )
        allowed_fields = {
            'business_label', 'category', 'priority', 'is_active',
            'in_app_enabled', 'email_enabled', 'whatsapp_enabled', 'sms_enabled',
            'send_immediately',
            'fallback_enabled', 'fallback_delay_minutes',
            'escalation_enabled', 'escalation_delay_minutes', 'escalation_target_type',
            'template_id', 'template_name',
            'allow_user_override', 'admin_notes',
        }
        for k, v in fields.items():
            if k in allowed_fields:
                setattr(rule, k, v)

        rule.updated_by = updated_by
        rule.save()
        return rule

    @staticmethod
    def delete_rule(*, tenant_id, rule_id, deleted_by=None):
        """Soft-delete a tenant rule. System rules cannot be deleted."""
        rule = NotificationRule.objects.filter(
            id=rule_id,
            tenant_id=tenant_id,  # tenants can only delete their own rules
            is_deleted=False,
        ).first()
        if not rule:
            raise ValueError('Rule not found or already deleted.')
        if rule.is_system:
            raise ValueError('System rules cannot be deleted.')
        rule.soft_delete()

    # ── Channel settings CRUD ────────────────────────────────────────────────

    @staticmethod
    def get_channel_settings(*, tenant_id) -> list:
        """Return channel settings, creating defaults if absent."""
        NotificationControlService._ensure_channel_settings_exist(tenant_id)
        return list(
            NotificationChannelSetting.objects.filter(tenant_id=tenant_id)
            .order_by('channel_type')
        )

    @staticmethod
    @transaction.atomic
    def update_channel_settings(*, tenant_id, settings: list, updated_by=None) -> list:
        """
        Bulk-update channel settings.
        `settings` is a list of dicts with at least {'channel_type': ..., 'is_enabled': ...}.
        """
        results = []
        for s in settings:
            channel_type = s.get('channel_type')
            if not channel_type:
                continue
            obj, _ = NotificationChannelSetting.objects.get_or_create(
                tenant_id=tenant_id,
                channel_type=channel_type,
            )
            updatable = {
                'is_enabled', 'provider', 'quiet_hours_enabled',
                'quiet_hours_start', 'quiet_hours_end',
                'sender_name', 'sender_email', 'config_json',
            }
            for k, v in s.items():
                if k in updatable:
                    setattr(obj, k, v)
            obj.save()
            results.append(obj)
        return results

    # ── Preference defaults CRUD ─────────────────────────────────────────────

    @staticmethod
    def get_preference_defaults(*, tenant_id) -> TenantNotificationPreferenceDefaults:
        obj, _ = TenantNotificationPreferenceDefaults.objects.get_or_create(
            tenant_id=tenant_id,
        )
        return obj

    @staticmethod
    @transaction.atomic
    def update_preference_defaults(*, tenant_id, **fields) -> TenantNotificationPreferenceDefaults:
        obj, _ = TenantNotificationPreferenceDefaults.objects.get_or_create(
            tenant_id=tenant_id,
        )
        allowed = {
            'default_in_app_enabled', 'default_email_enabled',
            'default_reminder_enabled', 'allow_user_override', 'digest_frequency',
        }
        for k, v in fields.items():
            if k in allowed:
                setattr(obj, k, v)
        obj.save()
        return obj

    # ── Summary stats ────────────────────────────────────────────────────────

    @staticmethod
    def get_summary(*, tenant_id) -> dict:
        rules = NotificationControlService.list_rules(tenant_id=tenant_id)
        active = [r for r in rules if r.is_active]
        return {
            'total_rules':               len(rules),
            'active_rules':              len(active),
            'fallback_enabled_count':    sum(1 for r in active if r.fallback_enabled),
            'escalation_enabled_count':  sum(1 for r in active if r.escalation_enabled),
            'high_priority_count':       sum(1 for r in active if r.priority in ('high', 'critical')),
            'email_channel_enabled':     NotificationControlService.channel_enabled(
                tenant_id=tenant_id, channel='email',
            ),
            'in_app_channel_enabled':    NotificationControlService.channel_enabled(
                tenant_id=tenant_id, channel='in_app',
            ),
        }

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _ensure_defaults_seeded(*, tenant_id):
        """
        Seed system-level default rules if they don't exist yet.
        Safe to call multiple times (idempotent).
        """
        for defaults in DEFAULT_NOTIFICATION_RULES:
            # We use filter().first() instead of get_or_create to be robust
            # against database-level duplicate NULLs if they somehow occur.
            exists = NotificationRule.objects.filter(
                tenant_id__isnull=True,
                event_key=defaults['event_key'],
                is_system=True,
            ).exists()

            if not exists:
                try:
                    NotificationRule.objects.create(
                        tenant_id=None,
                        event_key=defaults['event_key'],
                        is_system=True,
                        is_locked=False,
                        **{k: v for k, v in defaults.items() if k != 'event_key'},
                    )
                except Exception as e:
                    # In case of race condition during concurrent seeding
                    logger.warning(f"Failed to seed default rule {defaults['event_key']}: {e}")

    @staticmethod
    def _ensure_channel_settings_exist(tenant_id):
        """Create default channel settings rows if absent."""
        defaults = [
            {'channel_type': 'in_app',   'is_enabled': True},
            {'channel_type': 'email',    'is_enabled': True},
            {'channel_type': 'whatsapp', 'is_enabled': False},
            {'channel_type': 'sms',      'is_enabled': False},
        ]
        for d in defaults:
            NotificationChannelSetting.objects.get_or_create(
                tenant_id=tenant_id,
                channel_type=d['channel_type'],
                defaults={'is_enabled': d['is_enabled']},
            )
