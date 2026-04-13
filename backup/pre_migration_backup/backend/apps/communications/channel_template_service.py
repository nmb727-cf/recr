"""
Channel Template Service
=========================
Renders notification content into channel-appropriate formats.

Each channel has different constraints:
  • in_app  — full HTML allowed, long body fine
  • email   — full HTML, handled by EmailDispatchService (not this service)
  • whatsapp — plain text, template-driven, Unicode safe, ~1024 chars
  • sms      — plain text, STRICT 160-char GSM7 or 153-char Unicode limit
               (concatenated SMS: 2 segments = 306 GSM7 chars max)
  • push     — title ≤ 65 chars, body ≤ 240 chars, action_url included

Entry point:
    render_channel_template(
        channel_type='whatsapp',
        template=...,      # dict or None — see ChannelTemplate below
        context=...,       # variable dict
        notification=...,  # optional Notification instance
    )

Returns RenderedMessage with: subject, body, template_name, template_params.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Hard limits per channel
_SMS_MAX_CHARS       = 306   # 2 concatenated GSM-7 segments (safe limit)
_WHATSAPP_MAX_CHARS  = 1024
_PUSH_TITLE_MAX      = 65
_PUSH_BODY_MAX       = 240

# Regex for {variable} placeholders
_VAR_PATTERN = re.compile(r'\{(\w+)\}')


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ChannelTemplate:
    """
    Channel-specific template definition.

    For WhatsApp:  template_name is mandatory (pre-approved template ID).
    For SMS:       body_template is the text with {variables}.
    For Push:      subject_template (title) + body_template.
    For in_app:    body_template only.
    """
    channel_type:      str
    body_template:     str = ''
    subject_template:  str = ''
    template_name:     str = ''   # Provider-side template ID (WhatsApp)
    template_params_keys: list = field(default_factory=list)  # ordered variable names


@dataclass
class RenderedMessage:
    """Output of render_channel_template()."""
    channel_type:    str
    subject:         str = ''
    body:            str = ''
    template_name:   str = ''    # provider template ID if applicable
    template_params: dict = field(default_factory=dict)  # for provider-side substitution
    truncated:       bool = False
    variables_used:  list = field(default_factory=list)
    missing_variables: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_channel_template(
    *,
    channel_type: str,
    template: Optional[ChannelTemplate] = None,
    context: dict = None,
    notification=None,
) -> RenderedMessage:
    """
    Render a notification into the appropriate format for channel_type.

    Args:
        channel_type: 'in_app' | 'whatsapp' | 'sms' | 'push'
        template:     ChannelTemplate or None (falls back to notification fields)
        context:      Variable substitution dict (merged with notification fields)
        notification: Notification model instance (used for fallback content)

    Returns:
        RenderedMessage

    Never raises — missing variables produce empty strings, truncation is silent.
    """
    ctx = _build_context(notification, context)

    dispatch = {
        'in_app':   _render_in_app,
        'whatsapp': _render_whatsapp,
        'sms':      _render_sms,
        'push':     _render_push,
    }
    renderer = dispatch.get(channel_type, _render_generic)

    try:
        return renderer(template=template, ctx=ctx, notification=notification)
    except Exception as exc:
        logger.error('render_channel_template failed for %s: %s', channel_type, exc)
        # Safe fallback: return whatever we can from the notification
        return _safe_fallback(channel_type, notification, ctx)


# ---------------------------------------------------------------------------
# Per-channel renderers
# ---------------------------------------------------------------------------

def _render_in_app(template, ctx, notification) -> RenderedMessage:
    """In-app: render subject + body with variable injection, no truncation."""
    subject, body, missing = _render_text(
        subject_tpl=_tpl_subject(template, notification),
        body_tpl=_tpl_body(template, notification),
        ctx=ctx,
    )
    return RenderedMessage(
        channel_type='in_app',
        subject=subject,
        body=body,
        missing_variables=missing,
    )


def _render_whatsapp(template, ctx, notification) -> RenderedMessage:
    """
    WhatsApp: template-driven.

    If template has template_name:
        Returns template_name + template_params (provider handles substitution).
    Else:
        Renders body text locally and checks length constraint.
    """
    if template and template.template_name:
        # Build ordered params dict for provider substitution
        params = {}
        missing = []
        for key in (template.template_params_keys or []):
            val = ctx.get(key, '')
            if not val:
                missing.append(key)
            params[key] = str(val) if val else ''

        body = _render_string(template.body_template, ctx) if template.body_template else ''
        body = _truncate(body, _WHATSAPP_MAX_CHARS) if body else ''

        return RenderedMessage(
            channel_type='whatsapp',
            body=body,
            template_name=template.template_name,
            template_params=params,
            missing_variables=missing,
        )

    # Fallback: render body locally
    _, body, missing = _render_text(
        subject_tpl='',
        body_tpl=_tpl_body(template, notification),
        ctx=ctx,
    )
    truncated = len(body) > _WHATSAPP_MAX_CHARS
    body = _truncate(body, _WHATSAPP_MAX_CHARS)
    return RenderedMessage(
        channel_type='whatsapp',
        body=body,
        truncated=truncated,
        missing_variables=missing,
    )


def _render_sms(template, ctx, notification) -> RenderedMessage:
    """
    SMS: plain text, strictly truncated to safe concat limit.

    Strips HTML tags, line breaks become spaces.
    """
    _, body, missing = _render_text(
        subject_tpl='',
        body_tpl=_tpl_body(template, notification),
        ctx=ctx,
    )
    body = _strip_html(body)
    body = ' '.join(body.split())  # collapse whitespace
    body = _append_action_url(body, ctx)
    truncated = len(body) > _SMS_MAX_CHARS
    body = _truncate(body, _SMS_MAX_CHARS)
    return RenderedMessage(
        channel_type='sms',
        body=body,
        truncated=truncated,
        missing_variables=missing,
    )


def _render_push(template, ctx, notification) -> RenderedMessage:
    """
    Push: title (subject) + short body. Strict character limits.
    """
    subject, body, missing = _render_text(
        subject_tpl=_tpl_subject(template, notification),
        body_tpl=_tpl_body(template, notification),
        ctx=ctx,
    )
    subject_truncated = len(subject) > _PUSH_TITLE_MAX
    body_truncated    = len(body) > _PUSH_BODY_MAX
    subject = _truncate(subject, _PUSH_TITLE_MAX)
    body    = _truncate(_strip_html(body), _PUSH_BODY_MAX)
    return RenderedMessage(
        channel_type='push',
        subject=subject,
        body=body,
        truncated=(subject_truncated or body_truncated),
        missing_variables=missing,
    )


def _render_generic(template, ctx, notification) -> RenderedMessage:
    subject, body, missing = _render_text(
        subject_tpl=_tpl_subject(template, notification),
        body_tpl=_tpl_body(template, notification),
        ctx=ctx,
    )
    return RenderedMessage(
        channel_type='unknown',
        subject=subject,
        body=body,
        missing_variables=missing,
    )


# ---------------------------------------------------------------------------
# Context and template helpers
# ---------------------------------------------------------------------------

def _build_context(notification, extra: dict) -> dict:
    """Merge notification fields into context dict."""
    ctx = {}
    if notification:
        ctx.update({
            'title':       notification.title or '',
            'body':        notification.body or '',
            'action_url':  notification.action_url or '',
            'severity':    notification.severity or 'info',
            'type':        notification.get_type() if hasattr(notification, 'get_type') else '',
        })
    if extra:
        ctx.update({k: str(v) if v is not None else '' for k, v in extra.items()})
    return ctx


def _tpl_subject(template, notification) -> str:
    if template and template.subject_template:
        return template.subject_template
    if notification:
        return notification.title or ''
    return ''


def _tpl_body(template, notification) -> str:
    if template and template.body_template:
        return template.body_template
    if notification:
        return notification.body or ''
    return ''


def _render_text(subject_tpl: str, body_tpl: str, ctx: dict):
    """
    Substitute {variables} in subject and body templates.
    Returns (subject, body, missing_variables).
    """
    missing = set()
    subject = _render_string(subject_tpl, ctx, missing_out=missing)
    body    = _render_string(body_tpl, ctx, missing_out=missing)
    return subject, body, sorted(missing)


def _render_string(template_str: str, ctx: dict, missing_out: set = None) -> str:
    """
    Substitute {var} placeholders.  Missing vars become '' and are logged in missing_out.
    Never raises.
    """
    if not template_str:
        return ''
    try:
        def replacer(match):
            key = match.group(1)
            val = ctx.get(key)
            if val is None or val == '':
                if missing_out is not None:
                    missing_out.add(key)
                return ''
            return str(val)
        return _VAR_PATTERN.sub(replacer, template_str)
    except Exception as exc:
        logger.debug('_render_string error: %s', exc)
        return template_str


def _safe_fallback(channel_type: str, notification, ctx: dict) -> RenderedMessage:
    title = ctx.get('title', '') or (notification.title if notification else '') or ''
    body  = ctx.get('body', '')  or (notification.body  if notification else '') or ''
    if channel_type == 'sms':
        body = _truncate(_strip_html(body), _SMS_MAX_CHARS)
    return RenderedMessage(channel_type=channel_type, subject=title, body=body)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + '…'


def _strip_html(text: str) -> str:
    """Remove HTML tags from text (safe, no external deps)."""
    return re.sub(r'<[^>]+>', '', text)


def _append_action_url(body: str, ctx: dict) -> str:
    """Append action URL to SMS body if available and there's room."""
    url = ctx.get('action_url', '')
    if not url:
        return body
    suffix = f' {url}'
    if len(body) + len(suffix) <= _SMS_MAX_CHARS:
        return body + suffix
    return body
