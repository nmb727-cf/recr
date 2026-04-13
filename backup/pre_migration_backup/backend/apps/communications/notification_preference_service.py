"""
User Notification Preference Service
=====================================

Handles resolution of notification delivery based on the hierarchy:

  System Rules → Tenant Overrides → User Preferences → Quiet Hours

Resolution Chain:
  1. System critical or CRITICAL priority?   → Always allow (bypass everything)
  2. Tenant-level channel disabled globally? → Deny
  3. User global channel disabled?           → Deny (e.g. "turn off ALL email")
  4. Within quiet hours?                     → Deny if priority < HIGH
  5. User category+channel disabled?         → Deny
  6. User min_priority filter?               → Deny if notification < user minimum
  7. Passes all checks                       → Allow

Key invariants:
  - CRITICAL notifications bypass all user and quiet-hours rules.
  - Tenant channel blocks override user enablement (tenant controls platform).
  - Category×channel defaults are auto-seeded on first read so the UI always
    shows the full matrix without needing explicit DB rows per user.

Named functions match the contract in COMMS-NOTIFICATION-PREFERENCES-01:
  resolve_user_notification_preference()
  is_notification_allowed_for_user()
  resolve_user_channels()
  is_quiet_hours()
"""
from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Dict, List, Optional

import pytz
from django.db import transaction
from django.utils import timezone

from apps.communications.models import (
    UserNotificationPreference,
    UserNotificationSetting,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — aligned with NotificationRuleCategory choices
# ---------------------------------------------------------------------------

NOTIFICATION_CATEGORIES = [
    'messaging',
    'candidate',
    'application',
    'interview',
    'offer',
    'approval',
    'agency',
    'deadline',
    'passport',
    'system',
]

NOTIFICATION_CHANNELS = ['in_app', 'email', 'whatsapp', 'sms', 'push']

# Channels that users can globally disable via UserNotificationSetting
_GLOBAL_CHANNEL_FLAGS: Dict[str, str] = {
    'email':    'all_email_enabled',
    'sms':      'all_sms_enabled',
    'whatsapp': 'all_whatsapp_enabled',
    'push':     'all_push_enabled',
    # in_app has no global toggle — always deliverable
}

_PRIORITY_RANK: Dict[str, int] = {'info': 0, 'medium': 1, 'high': 2, 'critical': 3}

# Category-level defaults when no explicit DB row exists for the user
_CATEGORY_CHANNEL_DEFAULTS: Dict[str, Dict[str, bool]] = {
    'messaging':   {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'candidate':   {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'application': {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'interview':   {'in_app': True, 'email': True,  'whatsapp': True,  'sms': False, 'push': False},
    'offer':       {'in_app': True, 'email': True,  'whatsapp': True,  'sms': False, 'push': False},
    'approval':    {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'agency':      {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'deadline':    {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'passport':    {'in_app': True, 'email': False, 'whatsapp': False, 'sms': False, 'push': False},
    'system':      {'in_app': True, 'email': True,  'whatsapp': False, 'sms': False, 'push': False},
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_timezone(tz_str: str) -> str:
    """Return tz_str if valid IANA timezone, else raise ValueError."""
    try:
        pytz.timezone(tz_str)
        return tz_str
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(
            f"Unknown timezone: '{tz_str}'. Use a valid IANA timezone string (e.g. 'Asia/Kolkata')."
        )


def _priority_rank(priority: str) -> int:
    return _PRIORITY_RANK.get((priority or 'info').lower(), 0)


def _effective_channel_enabled(
    category: str,
    channel: str,
    explicit_pref: Optional[UserNotificationPreference],
) -> bool:
    if explicit_pref is not None:
        return explicit_pref.is_enabled
    return _CATEGORY_CHANNEL_DEFAULTS.get(category, {}).get(channel, False)


def _effective_min_priority(
    explicit_pref: Optional[UserNotificationPreference],
) -> str:
    if explicit_pref is not None:
        return explicit_pref.min_priority or 'info'
    return 'info'


# ---------------------------------------------------------------------------
# Main Service
# ---------------------------------------------------------------------------

class UserNotificationPreferenceService:

    # ── Named resolution functions (per COMMS-NOTIFICATION-PREFERENCES-01) ────

    @staticmethod
    def resolve_user_notification_preference(
        *,
        user_id,
        category: str,
        channel: str,
    ) -> Dict:
        """
        Resolve the effective preference for a single category+channel pair.

        Returns:
          {
            is_enabled   : bool  — effective state (explicit row or system default)
            min_priority : str   — minimum priority threshold ('info'/'medium'/'high')
            source       : 'explicit' | 'default'
          }
        """
        pref = UserNotificationPreference.objects.filter(
            user_id=user_id,
            category=category,
            channel_type=channel,
        ).first()

        return {
            'is_enabled':   _effective_channel_enabled(category, channel, pref),
            'min_priority': _effective_min_priority(pref),
            'source':       'explicit' if pref else 'default',
        }

    @staticmethod
    def resolve_user_channels(
        *,
        tenant_id,
        user_id,
        category: str,
        priority: str = 'info',
        is_system_critical: bool = False,
    ) -> Dict[str, bool]:
        """
        Return which channels are active for this user/category/priority.

        Applies the full resolution chain:
          Tenant channel settings → User global settings → Quiet hours → User category prefs

        Returns:
          {'in_app': bool, 'email': bool, 'whatsapp': bool, 'sms': bool, 'push': bool}

        CRITICAL priority bypasses user and quiet-hours restrictions but still
        respects tenant-level channel disables (platform control).
        """
        user_settings = UserNotificationPreferenceService.get_user_settings(tenant_id, user_id)
        in_quiet = (
            not is_system_critical
            and priority != 'critical'
            and UserNotificationPreferenceService.is_quiet_hours(user_settings)
        )

        # Load all explicit prefs for this user+category in one query
        explicit_prefs: Dict[str, UserNotificationPreference] = {
            p.channel_type: p
            for p in UserNotificationPreference.objects.filter(
                user_id=user_id,
                category=category,
            )
        }

        try:
            from apps.communications.notification_control_service import NotificationControlService
            _tenant_channel_enabled = lambda ch: NotificationControlService.channel_enabled(
                tenant_id=tenant_id, channel=ch
            )
        except Exception:
            _tenant_channel_enabled = lambda ch: True

        result: Dict[str, bool] = {}
        for channel in NOTIFICATION_CHANNELS:

            # CRITICAL bypasses user prefs (but not tenant disables)
            if is_system_critical or priority == 'critical':
                if channel == 'in_app':
                    result[channel] = True
                else:
                    result[channel] = _tenant_channel_enabled(channel)
                continue

            # Tenant-level channel disable
            if channel != 'in_app' and not _tenant_channel_enabled(channel):
                result[channel] = False
                continue

            # User global channel toggle
            global_flag = _GLOBAL_CHANNEL_FLAGS.get(channel)
            if global_flag and not getattr(user_settings, global_flag, True):
                result[channel] = False
                continue

            # Quiet hours: suppress non-HIGH for non-in_app channels
            if in_quiet and channel != 'in_app' and _priority_rank(priority) < _priority_rank('high'):
                result[channel] = False
                continue

            # User category+channel preference
            pref = explicit_prefs.get(channel)
            if not _effective_channel_enabled(category, channel, pref):
                result[channel] = False
                continue

            # Priority threshold
            if _priority_rank(priority) < _priority_rank(_effective_min_priority(pref)):
                result[channel] = False
                continue

            result[channel] = True

        return result

    @staticmethod
    def is_notification_allowed_for_user(
        *,
        tenant_id,
        user_id,
        category: str,
        channel: str,
        priority: str = 'info',
        is_system_critical: bool = False,
    ) -> bool:
        """
        Single yes/no gate: should this notification be delivered to this user
        on this channel?

        Called by NotificationService before every delivery attempt.

        Resolution order:
          1. Critical → always allow
          2. Tenant channel disabled → deny
          3. User global channel off → deny
          4. Quiet hours (priority < HIGH) → deny non-in_app
          5. User category pref disabled → deny
          6. Priority below user minimum → deny
          7. → allow
        """
        # 1. CRITICAL always passes
        if is_system_critical or priority == 'critical':
            return True

        # 2. Tenant-level channel check (skip for in_app)
        if channel != 'in_app':
            try:
                from apps.communications.notification_control_service import NotificationControlService
                if not NotificationControlService.channel_enabled(
                    tenant_id=tenant_id, channel=channel
                ):
                    return False
            except Exception as exc:
                logger.warning("Tenant channel check failed: %s", exc)

        # 3. User global channel toggle
        user_settings = UserNotificationPreferenceService.get_user_settings(tenant_id, user_id)
        global_flag = _GLOBAL_CHANNEL_FLAGS.get(channel)
        if global_flag and not getattr(user_settings, global_flag, True):
            return False

        # 4. Quiet hours — suppress non-high for non-in_app channels
        if channel != 'in_app' and UserNotificationPreferenceService.is_quiet_hours(user_settings):
            if _priority_rank(priority) < _priority_rank('high'):
                return False

        # 5 & 6. Category+channel preference
        pref = UserNotificationPreference.objects.filter(
            user_id=user_id,
            category=category,
            channel_type=channel,
        ).first()

        if not _effective_channel_enabled(category, channel, pref):
            return False

        if _priority_rank(priority) < _priority_rank(_effective_min_priority(pref)):
            return False

        return True

    @staticmethod
    def is_quiet_hours(settings: UserNotificationSetting) -> bool:
        """
        Return True if the current time falls within the user's quiet window.
        Handles overnight spans (e.g. 22:00 → 08:00) correctly.
        """
        if (
            not settings.quiet_hours_enabled
            or not settings.quiet_hours_start
            or not settings.quiet_hours_end
        ):
            return False

        try:
            tz = pytz.timezone(settings.timezone or 'UTC')
            now: time = datetime.now(tz).time().replace(second=0, microsecond=0)
            start: time = settings.quiet_hours_start
            end: time = settings.quiet_hours_end

            if start <= end:
                # Same-day window: 08:00 – 22:00
                return start <= now <= end
            else:
                # Overnight window: 22:00 – 08:00
                return now >= start or now <= end
        except Exception as exc:
            logger.warning("is_quiet_hours check failed: %s", exc)
            return False

    # ── Preference Matrix ─────────────────────────────────────────────────────

    @staticmethod
    def get_preference_matrix(tenant_id, user_id) -> List[Dict]:
        """
        Return the full category × channel matrix for a user.

        Used by the Notification Preferences settings page.
        Returns system defaults for any category+channel without an explicit row.

        Shape:
          [
            {
              category: 'interview',
              label: 'Interviews',
              channels: [
                {channel: 'in_app', is_enabled: True, min_priority: 'info', source: 'default'},
                {channel: 'email',  is_enabled: True, min_priority: 'info', source: 'explicit'},
                ...
              ]
            },
            ...
          ]
        """
        all_prefs: Dict[tuple, UserNotificationPreference] = {
            (p.category, p.channel_type): p
            for p in UserNotificationPreference.objects.filter(user_id=user_id)
        }

        category_labels = {
            'messaging':   'Messaging',
            'candidate':   'Candidates',
            'application': 'Applications',
            'interview':   'Interviews',
            'offer':       'Offers',
            'approval':    'Approvals',
            'agency':      'Agency Collaboration',
            'deadline':    'Automation / Deadlines',
            'passport':    'Passport',
            'system':      'System Alerts',
        }

        matrix = []
        for category in NOTIFICATION_CATEGORIES:
            channels = []
            for channel in NOTIFICATION_CHANNELS:
                pref = all_prefs.get((category, channel))
                channels.append({
                    'channel':      channel,
                    'is_enabled':   _effective_channel_enabled(category, channel, pref),
                    'min_priority': _effective_min_priority(pref),
                    'source':       'explicit' if pref else 'default',
                })
            matrix.append({
                'category': category,
                'label':    category_labels.get(category, category.title()),
                'channels': channels,
            })

        return matrix

    # ── Settings CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def get_user_settings(tenant_id, user_id) -> UserNotificationSetting:
        """Return (or auto-create) the user's global notification settings."""
        obj, _ = UserNotificationSetting.objects.get_or_create(
            user_id=user_id,
            defaults={'tenant_id': tenant_id},
        )
        return obj

    @staticmethod
    def update_user_settings(tenant_id, user_id, **fields) -> UserNotificationSetting:
        """
        Update one or more fields on UserNotificationSetting.
        Validates timezone if provided.
        Ignores unknown field names silently.
        """
        updatable = {
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'timezone', 'digest_mode',
            'all_email_enabled', 'all_sms_enabled',
            'all_whatsapp_enabled', 'all_push_enabled',
        }

        if 'timezone' in fields and fields['timezone']:
            _validate_timezone(fields['timezone'])  # raises ValueError if invalid

        obj = UserNotificationPreferenceService.get_user_settings(tenant_id, user_id)
        changed = []
        for k, v in fields.items():
            if k in updatable:
                setattr(obj, k, v)
                changed.append(k)

        if changed:
            obj.save(update_fields=changed + ['updated_at'])

        return obj

    # ── Preferences CRUD ──────────────────────────────────────────────────────

    @staticmethod
    def get_user_preferences(tenant_id, user_id) -> List[UserNotificationPreference]:
        """Return all explicit preference rows for a user (may be empty)."""
        return list(UserNotificationPreference.objects.filter(user_id=user_id))

    @staticmethod
    @transaction.atomic
    def update_user_preference(
        tenant_id,
        user_id,
        category: str,
        channel_type: str,
        is_enabled: Optional[bool] = None,
        min_priority: Optional[str] = None,
    ) -> UserNotificationPreference:
        """Create or update a single category+channel preference row."""
        if category not in NOTIFICATION_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Valid: {', '.join(NOTIFICATION_CATEGORIES)}"
            )
        if channel_type not in NOTIFICATION_CHANNELS:
            raise ValueError(
                f"Invalid channel '{channel_type}'. Valid: {', '.join(NOTIFICATION_CHANNELS)}"
            )
        if min_priority is not None and min_priority not in _PRIORITY_RANK:
            raise ValueError(
                f"Invalid min_priority '{min_priority}'. Valid: {', '.join(_PRIORITY_RANK)}"
            )

        pref, _ = UserNotificationPreference.objects.get_or_create(
            user_id=user_id,
            category=category,
            channel_type=channel_type,
            defaults={'tenant_id': tenant_id, 'min_priority': min_priority or 'info'},
        )

        changed = []
        if is_enabled is not None:
            pref.is_enabled = is_enabled
            changed.append('is_enabled')
        if min_priority is not None:
            pref.min_priority = min_priority
            changed.append('min_priority')

        if changed:
            pref.save(update_fields=changed + ['updated_at'])

        return pref

    @staticmethod
    @transaction.atomic
    def bulk_update_preferences(
        tenant_id,
        user_id,
        updates: List[Dict],
    ) -> List[UserNotificationPreference]:
        """
        Atomically update multiple category+channel preferences.

        `updates`: list of dicts with keys:
          category     : str  (required)
          channel_type : str  (required)
          is_enabled   : bool (optional)
          min_priority : str  (optional)
        """
        results = []
        for item in updates:
            pref = UserNotificationPreferenceService.update_user_preference(
                tenant_id=tenant_id,
                user_id=user_id,
                category=item['category'],
                channel_type=item['channel_type'],
                is_enabled=item.get('is_enabled'),
                min_priority=item.get('min_priority'),
            )
            results.append(pref)
        return results

    @staticmethod
    def reset_preferences(tenant_id, user_id) -> bool:
        """
        Delete all explicit category+channel preference rows for the user,
        reverting them to system defaults.

        Global settings (quiet hours, digest mode, global channel toggles)
        are NOT deleted — only the per-category per-channel rows.
        """
        UserNotificationPreference.objects.filter(user_id=user_id).delete()
        return True
