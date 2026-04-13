from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EmailSendRequest:
    tenant_id: str
    actor_user_id: str | None
    email_type: str
    message_purpose: str
    recipients: list[str]

    related_object_type: str = ''
    related_object_id: str | None = None
    workflow_context_type: str = ''
    workflow_context_id: str | None = None

    subject: str = ''
    body_html: str = ''
    body_text: str = ''

    template_id: str | None = None
    quick_reply_template_id: str | None = None

    preferred_sender_account_id: str | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    allow_fallback: bool = True
    track_delivery: bool = True
    schedule_at: datetime | None = None
    cc_emails: list[str] = field(default_factory=list)
    bcc_emails: list[str] = field(default_factory=list)
    reply_to_email: str = ''
    trigger_source: str = 'manual'
    triggered_by_event_id: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedRoute:
    provider_key: str
    route_used: str
    account_id: str | None
    from_email: str
    from_name: str
    reply_to_email: str
    fallback_applied: bool = False


@dataclass
class SendResult:
    ok: bool
    provider_message_id: str = ''
    provider_thread_id: str = ''
    status: str = 'sent'
    error: str = ''
    raw: dict[str, Any] = field(default_factory=dict)
