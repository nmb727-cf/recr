from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.db import DatabaseError, connection

from apps.core.responses import success_response

SAFE_NOT_READY_MESSAGE = 'Email module not configured'

# Keep aliases so older/newer schema names are both accepted.
REQUIRED_TABLE_ALIASES = {
    'communications_email_accounts': {'communications_email_accounts'},
    'communications_email_templates': {'communications_email_templates'},
    'communications_quick_replies': {'communications_quick_replies', 'communications_quick_reply_templates'},
    'communications_email_messages': {'communications_email_messages'},
    'communications_email_preferences': {'communications_email_preferences'},
}


@dataclass
class EmailFeatureStatus:
    feature_ready: bool
    message: str
    missing_tables: list[str]



def _has_table(existing_tables: set[str], aliases: set[str]) -> bool:
    return any(alias in existing_tables for alias in aliases)



def get_email_feature_status() -> EmailFeatureStatus:
    module_enabled = bool(getattr(settings, 'COMM_EMAIL_MODULE_ENABLED', True))
    if not module_enabled:
        return EmailFeatureStatus(
            feature_ready=False,
            message=SAFE_NOT_READY_MESSAGE,
            missing_tables=list(REQUIRED_TABLE_ALIASES.keys()),
        )

    try:
        existing_tables = set(connection.introspection.table_names())
    except DatabaseError:
        # Database/schema not ready: fail safe.
        return EmailFeatureStatus(
            feature_ready=False,
            message=SAFE_NOT_READY_MESSAGE,
            missing_tables=list(REQUIRED_TABLE_ALIASES.keys()),
        )

    missing_tables = [
        table_name
        for table_name, aliases in REQUIRED_TABLE_ALIASES.items()
        if not _has_table(existing_tables, aliases)
    ]

    return EmailFeatureStatus(
        feature_ready=not missing_tables,
        message='Email module ready' if not missing_tables else SAFE_NOT_READY_MESSAGE,
        missing_tables=missing_tables,
    )



def _check(setting_name: str) -> str:
    """Return setting_name if its value is empty, else ''."""
    return setting_name if not str(getattr(settings, setting_name, '') or '').strip() else ''


def get_oauth_provider_status() -> dict:
    gmail_missing = [k for k in ['GOOGLE_OAUTH_CLIENT_ID', 'GOOGLE_OAUTH_CLIENT_SECRET', 'GOOGLE_OAUTH_REDIRECT_URI'] if _check(k)]
    microsoft_missing = [k for k in ['MICROSOFT_OAUTH_CLIENT_ID', 'MICROSOFT_OAUTH_CLIENT_SECRET', 'MICROSOFT_OAUTH_REDIRECT_URI'] if _check(k)]

    gmail_ready = len(gmail_missing) == 0
    microsoft_ready = len(microsoft_missing) == 0

    return {
        'gmail_ready': gmail_ready,
        'gmail_missing': gmail_missing,
        'microsoft_ready': microsoft_ready,
        'microsoft_missing': microsoft_missing,
        'outlook_ready': microsoft_ready,   # backward-compat alias
        'smtp_ready': True,                 # always available — credentials supplied per-account
        'missing': gmail_missing + microsoft_missing,
    }



def email_not_ready_response(*, empty_data: dict | None = None):
    data = {
        'feature_ready': False,
        'message': SAFE_NOT_READY_MESSAGE,
    }
    if empty_data:
        data.update(empty_data)
    return success_response(data=data, message=SAFE_NOT_READY_MESSAGE)
