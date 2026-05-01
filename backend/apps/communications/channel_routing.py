"""
Channel Routing Service
========================
Central brain for deciding WHICH channels to use, in WHAT ORDER, and WHEN.

Entry point:
    resolve_channel_plan(
        tenant_id=...,
        event_key=...,
        priority=...,   # 'low' | 'medium' | 'high' | 'critical'
        recipient_context=...,
        rule_config=...,  # NotificationRule instance or None
    ) -> ChannelPlan

ChannelPlan describes:
    immediate_channels  — sent synchronously at event time
    fallback_channels   — sent if notification is unread after fallback_delay_seconds
    escalation_channels — sent if still unresolved after escalation_delay_seconds
    suppressed_channels — channels disabled at tenant level (logged for observability)

Priority → Default policy (when no rule override):
    low:      in_app only (no fallback)
    medium:   in_app → email fallback (40 min)
    high:     in_app + email immediately → whatsapp fallback (10 min)
    critical: in_app + email immediately → whatsapp (1 min) → sms escalation (5 min)

Tenant rule overrides:
    NotificationRule.whatsapp_enabled / sms_enabled flags gate whether the
    channel is even allowed for that event.

    NotificationChannelSetting.is_enabled (per tenant, per channel) gates
    whether the channel is globally active for the tenant.

Separation of concerns:
    This module ONLY decides the plan.
    channel_services.py executes it.
    orchestration_tasks.py schedules the delayed steps.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ChannelStep:
    """A single channel in the delivery plan."""
    channel_type:    str                     # 'in_app' | 'email' | 'whatsapp' | 'sms' | 'push'
    delay_seconds:   int  = 0               # 0 = immediate
    is_fallback:     bool = False
    is_escalation:   bool = False
    suppressed:      bool = False
    suppress_reason: str  = ''


@dataclass
class ChannelPlan:
    """
    The full multi-channel delivery plan for one notification event.

    immediate_channels:  execute right now
    fallback_channels:   schedule after fallback_delay_seconds if unread
    escalation_channels: schedule after escalation_delay_seconds if still unread

    Each list contains ChannelStep objects in execution order.
    Use any() guards to check availability before scheduling.
    """
    event_key:   str
    priority:    str
    tenant_id:   str

    immediate_channels:  List[ChannelStep] = field(default_factory=list)
    fallback_channels:   List[ChannelStep] = field(default_factory=list)
    escalation_channels: List[ChannelStep] = field(default_factory=list)
    suppressed_channels: List[ChannelStep] = field(default_factory=list)

    fallback_delay_seconds:   int = 0
    escalation_delay_seconds: int = 0

    @property
    def has_fallback(self) -> bool:
        return bool(self.fallback_channels)

    @property
    def has_escalation(self) -> bool:
        return bool(self.escalation_channels)

    @property
    def all_active_channels(self) -> List[str]:
        """Return list of all enabled channel type strings in order."""
        result = []
        for step in self.immediate_channels + self.fallback_channels + self.escalation_channels:
            if not step.suppressed and step.channel_type not in result:
                result.append(step.channel_type)
        return result


# ---------------------------------------------------------------------------
# Default timing by priority (seconds)
# ---------------------------------------------------------------------------

_FALLBACK_DELAY = {
    'info':     None,    # No fallback
    'low':      None,    # No fallback
    'medium':   2400,    # 40 min
    'high':     600,     # 10 min
    'critical': 60,      # 1 min
}

_ESCALATION_DELAY = {
    'high':     3600,    # 1 hr after fallback
    'critical': 300,     # 5 min after fallback
}

# Default channels per priority when no rule is configured
_DEFAULT_IMMEDIATE = {
    'info':     ['in_app'],
    'low':      ['in_app'],
    'medium':   ['in_app', 'email'],
    'high':     ['in_app', 'email'],
    'critical': ['in_app', 'email'],
}

_DEFAULT_FALLBACK = {
    'medium':   ['email'],
    'high':     ['whatsapp'],
    'critical': ['whatsapp'],
}

_DEFAULT_ESCALATION = {
    'high':     [],
    'critical': ['sms'],
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def resolve_channel_plan(
    *,
    tenant_id,
    event_key: str,
    priority: str = 'medium',
    recipient_context: dict = None,
    rule_config=None,   # NotificationRule instance or None
) -> ChannelPlan:
    """
    Resolve the full channel delivery plan for this event + tenant + priority.

    Args:
        tenant_id:         Tenant UUID
        event_key:         Event key string (e.g. 'interview.scheduled')
        priority:          'low' | 'medium' | 'high' | 'critical'
        recipient_context: Dict with recipient info (phone, push_token, etc.)
        rule_config:       NotificationRule instance (loaded by orchestrator)

    Returns:
        ChannelPlan
    """
    ctx = recipient_context or {}
    priority = _normalise_priority(priority)

    # ── 1. Resolve which channels the rule allows ───────────────────────────
    rule_channels = _channels_from_rule(rule_config, priority)

    # ── 2. Check tenant-level global channel availability ──────────────────
    tenant_availability = _check_tenant_channel_availability(tenant_id)

    # ── 3. Resolve timing from rule or severity defaults ───────────────────
    fallback_delay    = _resolve_fallback_delay(rule_config, priority)
    escalation_delay  = _resolve_escalation_delay(rule_config, priority)

    # ── 4. Build immediate channels ─────────────────────────────────────────
    immediate = []
    suppressed = []

    for ch in rule_channels.get('immediate', _DEFAULT_IMMEDIATE.get(priority, ['in_app'])):
        step = _build_step(
            channel_type=ch,
            delay_seconds=0,
            is_fallback=False,
            is_escalation=False,
            tenant_availability=tenant_availability,
            rule_config=rule_config,
        )
        if step.suppressed:
            suppressed.append(step)
        else:
            immediate.append(step)

    # ── 5. Build fallback channels ──────────────────────────────────────────
    fallback = []
    if fallback_delay:
        for ch in rule_channels.get('fallback', _DEFAULT_FALLBACK.get(priority, [])):
            step = _build_step(
                channel_type=ch,
                delay_seconds=fallback_delay,
                is_fallback=True,
                is_escalation=False,
                tenant_availability=tenant_availability,
                rule_config=rule_config,
            )
            if step.suppressed:
                suppressed.append(step)
            else:
                fallback.append(step)

    # ── 6. Build escalation channels ────────────────────────────────────────
    escalation = []
    if escalation_delay:
        for ch in rule_channels.get('escalation', _DEFAULT_ESCALATION.get(priority, [])):
            step = _build_step(
                channel_type=ch,
                delay_seconds=escalation_delay,
                is_fallback=False,
                is_escalation=True,
                tenant_availability=tenant_availability,
                rule_config=rule_config,
            )
            if step.suppressed:
                suppressed.append(step)
            else:
                escalation.append(step)

    plan = ChannelPlan(
        event_key=event_key,
        priority=priority,
        tenant_id=str(tenant_id),
        immediate_channels=immediate,
        fallback_channels=fallback,
        escalation_channels=escalation,
        suppressed_channels=suppressed,
        fallback_delay_seconds=fallback_delay or 0,
        escalation_delay_seconds=escalation_delay or 0,
    )

    logger.debug(
        'ChannelPlan resolved: event=%s priority=%s '
        'immediate=%s fallback=%s escalation=%s suppressed=%s',
        event_key, priority,
        [s.channel_type for s in immediate],
        [s.channel_type for s in fallback],
        [s.channel_type for s in escalation],
        [s.channel_type for s in suppressed],
    )
    return plan


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise_priority(priority: str) -> str:
    known = ('info', 'low', 'medium', 'high', 'critical')
    p = (priority or 'medium').lower()
    return p if p in known else 'medium'


def _channels_from_rule(rule_config, priority: str) -> dict:
    """
    Extract allowed channel sets from a NotificationRule.

    Channel assignment logic:
      • in_app + email  → always immediate (if enabled)
      • whatsapp        → fallback channel (sent after fallback_delay if unread)
      • sms             → escalation channel (sent after escalation_delay)

    This reflects the intent of the rules: WhatsApp and SMS are follow-up
    channels, not initial delivery channels, unless explicitly placed in
    the immediate tier via priority defaults.

    Returns dict with keys 'immediate', 'fallback', 'escalation'.
    """
    if rule_config is None:
        return {
            'immediate':  list(_DEFAULT_IMMEDIATE.get(priority, ['in_app'])),
            'fallback':   list(_DEFAULT_FALLBACK.get(priority, [])),
            'escalation': list(_DEFAULT_ESCALATION.get(priority, [])),
        }

    # Immediate: in_app + email only
    immediate = []
    if getattr(rule_config, 'in_app_enabled', True):
        immediate.append('in_app')
    if getattr(rule_config, 'email_enabled', True):
        immediate.append('email')

    # Fallback: WhatsApp if enabled + fallback is on
    fallback = []
    if getattr(rule_config, 'fallback_enabled', False):
        if getattr(rule_config, 'whatsapp_enabled', False):
            fallback.append('whatsapp')
        elif priority == 'medium' and 'email' not in immediate:
            fallback.append('email')

    # Escalation: SMS only if rule allows escalation + sms enabled
    escalation = []
    if getattr(rule_config, 'escalation_enabled', False):
        if getattr(rule_config, 'sms_enabled', False):
            escalation.append('sms')

    return {'immediate': immediate, 'fallback': fallback, 'escalation': escalation}


def _check_tenant_channel_availability(tenant_id) -> dict:
    """
    Check which channels are globally enabled for the tenant.

    Returns dict: {channel_type: bool}
    Missing entries default to True (don't block if no config found).
    """
    availability = {
        'in_app':   True,
        'email':    True,
        'whatsapp': False,  # Disabled by default until configured
        'sms':      False,
        'push':     False,
    }
    try:
        from apps.communications.notification_control_models import NotificationChannelSetting
        settings = NotificationChannelSetting.objects.filter(
            tenant_id=tenant_id
        ).values('channel_type', 'is_enabled')
        for row in settings:
            availability[row['channel_type']] = row['is_enabled']
    except Exception as exc:
        logger.debug('Could not load channel settings for tenant %s: %s', tenant_id, exc)
    return availability


def _build_step(
    *,
    channel_type: str,
    delay_seconds: int,
    is_fallback: bool,
    is_escalation: bool,
    tenant_availability: dict,
    rule_config,
) -> ChannelStep:
    """
    Build a single ChannelStep, marking it suppressed if the channel is
    unavailable at the tenant level.
    """
    available = tenant_availability.get(channel_type, True)
    if not available:
        return ChannelStep(
            channel_type=channel_type,
            delay_seconds=delay_seconds,
            is_fallback=is_fallback,
            is_escalation=is_escalation,
            suppressed=True,
            suppress_reason='channel_disabled_for_tenant',
        )
    return ChannelStep(
        channel_type=channel_type,
        delay_seconds=delay_seconds,
        is_fallback=is_fallback,
        is_escalation=is_escalation,
    )


def _resolve_fallback_delay(rule_config, priority: str) -> Optional[int]:
    """Return fallback delay in seconds from rule or default."""
    if rule_config:
        if not getattr(rule_config, 'fallback_enabled', False):
            return None
        minutes = getattr(rule_config, 'fallback_delay_minutes', None)
        if minutes:
            return minutes * 60
    return _FALLBACK_DELAY.get(priority)


def _resolve_escalation_delay(rule_config, priority: str) -> Optional[int]:
    """Return escalation delay in seconds from rule or default."""
    if rule_config:
        if not getattr(rule_config, 'escalation_enabled', False):
            return None
        minutes = getattr(rule_config, 'escalation_delay_minutes', None)
        if minutes:
            return minutes * 60
    return _ESCALATION_DELAY.get(priority)
