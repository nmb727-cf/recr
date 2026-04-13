# User Notification Preferences & Delivery Controls

**Prompt ID:** COMMS-NOTIFICATION-PREFERENCES-01  
**Module:** Communications Engine — User Preference Layer  
**Status:** Complete (Phase 1)

---

## Overview

The User Notification Preference system gives every user granular control over when and how they receive notifications. It operates as a per-user policy layer that sits between the platform's notification emission events and the actual delivery of those notifications.

Any user can:
- Silence entire notification categories (e.g. turn off all `messaging` email alerts)
- Raise the minimum priority threshold before a channel fires (e.g. only send SMS for `high` or above)
- Configure quiet hours — a window during which non-critical notifications are suppressed
- Toggle entire delivery channels globally (e.g. disable all WhatsApp)
- Reset to system defaults at any time without losing global settings

CRITICAL notifications always bypass all user preferences. Tenant-level channel rules (from `NotificationControlService`) take precedence before user rules are evaluated.

---

## Architecture

### Resolution Chain

Notification delivery is evaluated through a 7-step gate, in order:

```
1. CRITICAL bypass       — severity == CRITICAL → always deliver, skip remaining gates
2. Tenant channel check  — NotificationControlService.channel_enabled(tenant, channel)
3. Global channel toggle — UserNotificationSetting.all_email_enabled / all_sms_enabled / etc.
4. Quiet hours           — is_quiet_hours(settings) → suppress if active
5. Category preference   — UserNotificationPreference.is_enabled for (category, channel)
6. Priority threshold    — notification priority >= pref.min_priority
7. Allow                 — all gates passed, deliver
```

`is_notification_allowed_for_user()` implements this chain. It returns `True` or `False` synchronously and is called inside `NotificationService.create_notification()` before the notification row is written.

### Category × Channel Matrix

The system supports **10 notification categories** × **5 delivery channels** = 50 configurable preference slots per user.

Any slot without an explicit DB row falls back to `_CATEGORY_CHANNEL_DEFAULTS`, a hardcoded dict that represents sensible platform defaults (e.g. `interview` category has email+WhatsApp on by default; `passport` category is in-app only).

New users with zero DB rows see a full 50-slot matrix computed entirely from defaults — no DB writes required until the user changes a preference.

### Tenant Policy Precedence

Tenant-level rules from `NotificationControlService` are checked before user preferences. If the tenant has disabled the `email` channel entirely, no user-level email preference can re-enable it.

---

## Key Components

### Models

**`UserNotificationPreference`** (existing, one row per user × category × channel)
```
tenant_id       UUIDField
user_id         UUIDField
category        CharField    — one of NOTIFICATION_CATEGORIES
channel_type    CharField    — one of NOTIFICATION_CHANNELS
is_enabled      BooleanField — whether this channel fires for this category
min_priority    CharField    — minimum severity ('info'|'medium'|'high'|'critical')
```
Unique constraint: `(user_id, category, channel_type)`.  
Missing rows → system default via `_CATEGORY_CHANNEL_DEFAULTS`.

**`UserNotificationSetting`** (existing, one row per user — global settings)
```
tenant_id              UUIDField
user_id                UUIDField  unique
quiet_hours_enabled    BooleanField    default=False
quiet_hours_start      TimeField       nullable
quiet_hours_end        TimeField       nullable
timezone               CharField       default='UTC'
digest_mode            BooleanField    default=False  (future)
all_email_enabled      BooleanField    default=True
all_sms_enabled        BooleanField    default=False
all_whatsapp_enabled   BooleanField    default=False
all_push_enabled       BooleanField    default=False
```
Created on first access (`get_or_create`). Safe to call for new users.

---

### Service: `UserNotificationPreferenceService`

Located at `apps/communications/notification_preference_service.py`.

All methods are `@staticmethod` — no instantiation required.

#### Module-level constants

```python
NOTIFICATION_CATEGORIES = [
    'messaging', 'candidate', 'application', 'interview',
    'offer', 'approval', 'agency', 'deadline', 'passport', 'system'
]

NOTIFICATION_CHANNELS = ['in_app', 'email', 'whatsapp', 'sms', 'push']

_PRIORITY_RANK = {'info': 0, 'medium': 1, 'high': 2, 'critical': 3}

_CATEGORY_CHANNEL_DEFAULTS = {
    'messaging':    {'in_app': True,  'email': True,  'whatsapp': True,  'sms': False, 'push': False},
    'candidate':    {'in_app': True,  'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'application':  {'in_app': True,  'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'interview':    {'in_app': True,  'email': True,  'whatsapp': True,  'sms': False, 'push': False},
    'offer':        {'in_app': True,  'email': True,  'whatsapp': True,  'sms': False, 'push': False},
    'approval':     {'in_app': True,  'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'agency':       {'in_app': True,  'email': True,  'whatsapp': False, 'sms': False, 'push': False},
    'deadline':     {'in_app': True,  'email': True,  'whatsapp': True,  'sms': True,  'push': False},
    'passport':     {'in_app': True,  'email': False, 'whatsapp': False, 'sms': False, 'push': False},
    'system':       {'in_app': True,  'email': True,  'whatsapp': False, 'sms': False, 'push': False},
}
```

#### `resolve_user_notification_preference(...)`
Returns the effective preference for a single (category, channel) pair.

```python
resolve_user_notification_preference(
    *,
    user_id,
    category: str,
    channel: str,
) -> Dict
```

Returns:
```json
{
  "is_enabled": true,
  "min_priority": "info",
  "source": "explicit"   // or "default"
}
```
`source` tells the caller whether this came from a DB row (`explicit`) or the system default (`default`).

#### `is_notification_allowed_for_user(...)`
Main gate. Implements the full 7-step resolution chain.

```python
is_notification_allowed_for_user(
    *,
    tenant_id,
    user_id,
    category: str,
    channel: str,
    priority: str = 'info',
    is_system_critical: bool = False,
) -> bool
```

Returns `True` if the notification should be delivered through the specified channel, `False` if it should be suppressed.

CRITICAL notifications (`is_system_critical=True` or `priority='critical'`) skip steps 3–6 and return `True` immediately after the tenant channel check.

#### `resolve_user_channels(...)`
Returns the delivery verdict for all 5 channels at once for a given (category, priority) combination.

```python
resolve_user_channels(
    *,
    tenant_id,
    user_id,
    category: str,
    priority: str = 'info',
    is_system_critical: bool = False,
) -> Dict[str, bool]
```

Returns:
```json
{
  "in_app": true,
  "email": true,
  "whatsapp": false,
  "sms": false,
  "push": false
}
```

Useful when a caller needs to fan out a notification across all channels simultaneously (e.g. multi-channel orchestration).

#### `is_quiet_hours(settings: UserNotificationSetting) -> bool`
Returns `True` if the current time (in the user's configured timezone) falls within their quiet hours window.

Handles overnight windows correctly:
- `start=08:00, end=22:00` → quiet when `08:00 ≤ now ≤ 22:00`
- `start=22:00, end=08:00` → quiet when `now ≥ 22:00 OR now ≤ 08:00`

Returns `False` if `quiet_hours_enabled=False` or `start`/`end` are null.

#### `get_preference_matrix(...)`
Returns the full 10 × 5 matrix for display in a preferences UI.

```python
get_preference_matrix(tenant_id, user_id) -> List[Dict]
```

Each item:
```json
{
  "category": "interview",
  "channel": "email",
  "is_enabled": true,
  "min_priority": "info",
  "source": "explicit"
}
```

New users with zero preference rows receive a complete 50-item list computed entirely from `_CATEGORY_CHANNEL_DEFAULTS`.

#### `get_user_preferences(...)`
Returns all explicit `UserNotificationPreference` DB rows for the user.

```python
get_user_preferences(tenant_id, user_id) -> QuerySet
```

#### `update_user_preference(...)`
Create or update a single preference row atomically.

```python
update_user_preference(
    *,
    tenant_id,
    user_id,
    category: str,
    channel_type: str,
    is_enabled: bool = None,
    min_priority: str = None,
) -> UserNotificationPreference
```

Raises `ValueError` for invalid category, channel, or priority values. Wrapped in `@transaction.atomic`.

#### `bulk_update_preferences(...)`
Apply a list of preference updates atomically in a single transaction.

```python
bulk_update_preferences(
    *,
    tenant_id,
    user_id,
    updates: List[Dict],  # [{category, channel_type, is_enabled?, min_priority?}, ...]
) -> List[UserNotificationPreference]
```

Accepts 1–50 items. All-or-nothing: any validation error rolls back all updates.

#### `reset_preferences(...)`
Delete all explicit `UserNotificationPreference` rows for the user, restoring system defaults.

```python
reset_preferences(tenant_id, user_id) -> bool
```

`UserNotificationSetting` (quiet hours, digest mode, global channel toggles) is **preserved**. Only the per-category per-channel rows are deleted. Returns `True` on success.

#### `get_user_settings(...)`
Return the user's global settings, creating defaults on first access.

```python
get_user_settings(tenant_id, user_id) -> UserNotificationSetting
```

#### `update_user_settings(...)`
Partial update of global settings. Any subset of fields may be provided.

```python
update_user_settings(
    *,
    tenant_id,
    user_id,
    quiet_hours_enabled=None,
    quiet_hours_start=None,
    quiet_hours_end=None,
    timezone=None,
    digest_mode=None,
    all_email_enabled=None,
    all_sms_enabled=None,
    all_whatsapp_enabled=None,
    all_push_enabled=None,
) -> UserNotificationSetting
```

---

### Serializers

Located at `apps/communications/notification_preference_serializers.py`.

| Serializer | Purpose |
|-----------|---------|
| `UserNotificationPreferenceSerializer` | Read-only output for a single preference row |
| `UserNotificationPreferenceUpdateSerializer` | Validates single-row PUT body; enforces category/channel/priority choices |
| `UserNotificationPreferenceBulkUpdateSerializer` | Wraps 1–50 updates in `{"updates": [...]}` |
| `UserNotificationSettingSerializer` | Read-only output for global settings |
| `UserNotificationSettingUpdateSerializer` | Validates PUT body; enforces quiet-hours coherence |

**Quiet-hours coherence check** in `UserNotificationSettingUpdateSerializer.validate()`:
If `quiet_hours_enabled=True` is being set, `quiet_hours_start` and `quiet_hours_end` must both be present — either in the incoming data or already set on the instance.

---

## API Endpoints

All endpoints require authentication. Responses follow the project envelope: `{success, data, message}`.

### Preference Matrix
```
GET /api/v1/notifications/preferences/
```
Returns `{matrix: [...50 items...], preferences: [...explicit rows...]}`.

### Single Preference Update
```
PUT /api/v1/notifications/preferences/
```
Body:
```json
{
  "category": "interview",
  "channel_type": "whatsapp",
  "is_enabled": false,
  "min_priority": "medium"
}
```
`is_enabled` and `min_priority` are both optional — provide one or both.

### Bulk Preference Update
```
POST /api/v1/notifications/preferences/bulk/
```
Body:
```json
{
  "updates": [
    {"category": "messaging", "channel_type": "email", "is_enabled": false},
    {"category": "interview", "channel_type": "sms", "min_priority": "high"}
  ]
}
```
All updates applied atomically. Maximum 50 items per request.

### Reset to Defaults
```
POST /api/v1/notifications/preferences/reset/
```
No body required. Deletes all explicit preference rows; global settings preserved.

### Global Settings — Read
```
GET /api/v1/notifications/settings/
```
Returns the user's `UserNotificationSetting` record.

### Global Settings — Update
```
PUT /api/v1/notifications/settings/
```
Partial update (PATCH semantics). Example body to enable quiet hours:
```json
{
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00",
  "timezone": "Europe/London"
}
```

---

## Business Rules

| Rule | Behaviour |
|------|-----------|
| CRITICAL bypass | Notifications with `severity=critical` or `is_system_critical=True` skip user preferences entirely and are always delivered. |
| Tenant channel precedence | If the tenant has disabled a channel via `NotificationControlService`, user preferences cannot override it. |
| Quiet hours suppression | During quiet hours, non-critical notifications are suppressed for all channels except `in_app`. |
| Default-first population | Missing preference rows fall back to `_CATEGORY_CHANNEL_DEFAULTS`. No DB write required until user changes a setting. |
| Priority threshold | A notification at `info` level will not fire on a channel where `min_priority=medium`. Rank order: `info < medium < high < critical`. |
| Reset scope | `reset_preferences` only deletes per-category per-channel rows. Global settings (`UserNotificationSetting`) are preserved. |
| Atomic bulk updates | Bulk preference updates are wrapped in `@transaction.atomic`. Any validation error rolls back all updates in the batch. |
| Tenant isolation | All queries include `tenant_id`. A user in Tenant A cannot read or write preferences for Tenant B. |
| `get_user_settings` is safe | Calling `get_user_settings` for a new user creates a default settings row. Never raises on missing data. |

---

## Integration with NotificationService

`NotificationService.create_notification()` calls `is_notification_allowed_for_user()` after applying tenant-level rule overrides:

```python
# Inside NotificationService.create_notification():
allowed = UserNotificationPreferenceService.is_notification_allowed_for_user(
    tenant_id=tenant_id,
    user_id=user_id,
    category=pref_category,   # resolved from NotificationRule.category
    channel='in_app',
    priority=severity,
    is_system_critical=(severity == NotificationSeverity.CRITICAL)
)
if not allowed:
    return None  # Notification suppressed; no DB row created
```

The `category` passed to the preference check is resolved from the matching `NotificationRule.category`. If no rule exists, `'system'` is used as the default category.

---

## Test Coverage

Test file: `apps/communications/tests/test_notification_preferences.py`  
**72 tests** across 10 test classes.

| Class | Coverage |
|-------|---------|
| `TestResolveUserNotificationPreference` | Explicit row returned, default fallback, `source` field value, unknown category handling |
| `TestIsNotificationAllowedForUser` | Allow path, category disabled, channel disabled globally, quiet hours suppression, priority threshold, CRITICAL bypass, tenant channel blocked |
| `TestQuietHours` | Enabled/disabled flag, inside window, outside window, overnight window (22→08), boundary conditions, null times, timezone conversion |
| `TestResolveUserChannels` | Full channel map, some channels disabled, all blocked, CRITICAL bypasses, global toggle interaction |
| `TestPreferenceMatrix` | Full 50-item matrix, new-user defaults, explicit row present, source field, category ordering |
| `TestPreferenceCRUD` | Create row, update row, invalid category, invalid channel, invalid priority, idempotent update |
| `TestSettingsCRUD` | Create on first access, partial update, timezone saved, quiet hours coherence enforcement, reset preserves settings |
| `TestNotificationServiceIntegration` | Suppressed returns None, allowed creates notification, CRITICAL always fires |
| `TestTenantIsolation` | Tenant A cannot read Tenant B prefs, cross-tenant write blocked |
| `TestPreferenceAPIEndpoints` | All 9 views — GET matrix, PUT single, POST bulk, POST reset, GET settings, PUT settings, auth enforcement, 400 on bad input, response envelope shape |

---

## Files Modified / Created

| File | Action |
|------|--------|
| `apps/communications/notification_preference_service.py` | Rewritten — complete service with all named methods |
| `apps/communications/notification_preference_serializers.py` | Rewritten — 5 serializers with validation |
| `apps/communications/notification_preference_views.py` | Rewritten — 4 views including new bulk update endpoint |
| `apps/communications/urls.py` | Added `notifications/preferences/bulk/` route |
| `apps/communications/notification_service.py` | Two targeted fixes: `import uuid` added; suppressed-rule path now returns `None` |
| `apps/communications/tests/test_notification_preferences.py` | Created — 72 tests |
