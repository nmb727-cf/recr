"""
Email Template Renderer
=========================
Standalone rendering service for automation email templates.

Supports:
- Subject, HTML body, plain-text body from EmailTemplateDefinition
- Safe {variable} substitution — missing variables render as empty string
- HTML sanitization to prevent XSS in variable-injected content
- Fallback text-from-HTML strip when body_text is absent

Usage:
    renderer = EmailTemplateRenderer()
    result = renderer.render(template_slug='interview_scheduled', context={...})
    # result.subject, result.html_body, result.text_body

    # Or with a raw subject/body string
    result = renderer.render_raw(subject='Hello {name}', html='<p>Hi {name}</p>', context={'name': 'Alice'})
"""
from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe dict — missing keys render as empty string instead of raising KeyError
# ---------------------------------------------------------------------------

class _SafeDict(dict):
    def __missing__(self, key):
        return ''


# ---------------------------------------------------------------------------
# Rendered result
# ---------------------------------------------------------------------------

@dataclass
class RenderedEmail:
    subject: str
    html_body: str
    text_body: str
    template_used: str = ''


# ---------------------------------------------------------------------------
# Sanitization helpers
# ---------------------------------------------------------------------------

# HTML tags allowed in email bodies (very conservative allow-list)
_ALLOWED_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'span', 'div', 'table', 'tr', 'td', 'th',
    'thead', 'tbody', 'img', 'hr',
}

_TAG_RE = re.compile(r'<[^>]+>')


def _sanitize_context_value(value: str) -> str:
    """Escape HTML in user-supplied context values to prevent injection."""
    if not isinstance(value, str):
        return str(value) if value is not None else ''
    return html.escape(value)


def _strip_html(body_html: str) -> str:
    """Convert HTML to approximate plain text."""
    text = re.sub(r'<br\s*/?>', '\n', body_html, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = _TAG_RE.sub('', text)
    text = html.unescape(text)
    # Collapse excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class EmailTemplateRenderer:
    """
    Renders email templates with context variable substitution.

    Context values are HTML-escaped before injection into HTML bodies
    but are NOT escaped for subject lines (plain text context).
    """

    def render(
        self,
        template_slug: str,
        context: dict,
        tenant_id=None,
        language_code: str = 'en',
    ) -> RenderedEmail:
        """
        Look up EmailTemplateDefinition by slug and render with context.

        Falls back to a basic notification template if none found.
        """
        template = self._resolve_template(
            slug=template_slug,
            tenant_id=tenant_id,
            language_code=language_code,
        )
        if template:
            return self._render_template_obj(template, context)

        logger.debug(
            'EmailTemplateRenderer: no template found for slug=%r — using raw fallback',
            template_slug,
        )
        # Return minimal readable content when template is absent
        safe_ctx = _SafeDict({k: str(v) for k, v in (context or {}).items()})
        subject = safe_ctx.get('subject') or template_slug.replace('_', ' ').replace('.', ' ').title()
        body = safe_ctx.get('body') or ''
        return RenderedEmail(
            subject=subject,
            html_body=f'<p>{html.escape(body)}</p>' if body else '',
            text_body=body,
            template_used='',
        )

    def render_raw(
        self,
        *,
        subject: str,
        html: str = '',
        text: str = '',
        context: dict,
    ) -> RenderedEmail:
        """
        Render caller-supplied subject/body strings with context substitution.
        No DB lookup.
        """
        safe_ctx = self._build_safe_context(context, escape_html=False)
        safe_html_ctx = self._build_safe_context(context, escape_html=True)

        rendered_subject = self._sub(subject, safe_ctx)
        rendered_html = self._sub(html, safe_html_ctx)
        rendered_text = self._sub(text, safe_ctx) if text else _strip_html(rendered_html)

        return RenderedEmail(
            subject=rendered_subject,
            html_body=rendered_html,
            text_body=rendered_text,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_template(self, slug: str, tenant_id, language_code: str):
        """Look up EmailTemplateDefinition; tenant-custom overrides system default."""
        try:
            from apps.communications.models import EmailTemplateDefinition
            qs = EmailTemplateDefinition.objects.filter(
                slug=slug, is_active=True, language_code=language_code,
            )
            if tenant_id:
                tenant_tmpl = qs.filter(
                    tenant_scope__in=('TENANT_CUSTOM',),
                    tenant_id=tenant_id,
                ).first()
                if tenant_tmpl:
                    return tenant_tmpl
            return qs.filter(template_scope='SYSTEM_DEFAULT').first()
        except Exception as exc:
            logger.warning('EmailTemplateRenderer._resolve_template error: %s', exc)
            return None

    def _render_template_obj(self, template, context: dict) -> RenderedEmail:
        safe_ctx = self._build_safe_context(context, escape_html=False)
        safe_html_ctx = self._build_safe_context(context, escape_html=True)

        subject = self._sub(template.subject_template or '', safe_ctx)
        body_html = self._sub(template.body_html or '', safe_html_ctx)
        body_text = self._sub(template.body_text or '', safe_ctx) if template.body_text else _strip_html(body_html)

        return RenderedEmail(
            subject=subject,
            html_body=body_html,
            text_body=body_text,
            template_used=template.slug or str(template.id),
        )

    @staticmethod
    def _build_safe_context(context: dict, *, escape_html: bool) -> _SafeDict:
        result = {}
        for k, v in (context or {}).items():
            if v is None:
                result[k] = ''
            elif isinstance(v, str):
                result[k] = _sanitize_context_value(v) if escape_html else v
            else:
                result[k] = str(v)
        return _SafeDict(result)

    @staticmethod
    def _sub(template_str: str, safe_ctx: _SafeDict) -> str:
        """Safe {variable} substitution — never raises KeyError."""
        try:
            return template_str.format_map(safe_ctx)
        except Exception as exc:
            logger.debug('EmailTemplateRenderer._sub format error: %s', exc)
            return template_str
