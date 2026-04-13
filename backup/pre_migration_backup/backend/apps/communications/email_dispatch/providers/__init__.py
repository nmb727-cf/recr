"""
Automation Email Provider Abstraction
======================================
Clean provider layer for system/automation-triggered emails.
Distinct from the business email providers in email_accounts/providers.py
which are tied to user-linked OAuth accounts and EmailSendingAccount.

These providers read from TenantEmailConfig and are used exclusively by
EmailDeliveryService for notification fallbacks, reminders, and escalations.

Usage:
    from apps.communications.email_dispatch.providers import get_provider
    provider = get_provider(tenant_config)
    result = provider.send(...)
"""
from apps.communications.email_dispatch.providers.base import (
    AutomationEmailProvider,
    AutomationSendResult,
    ProviderHealthStatus,
)
from apps.communications.email_dispatch.providers.smtp import SMTPAutomationProvider
from apps.communications.email_dispatch.providers.sendgrid import SendGridProvider
from apps.communications.email_dispatch.providers.ses import SESProvider


def get_provider(tenant_config) -> AutomationEmailProvider:
    """
    Return the correct provider instance for a TenantEmailConfig.
    Falls back to SMTPAutomationProvider using Django's EMAIL_* settings
    if no tenant config is given.
    """
    if tenant_config is None:
        return SMTPAutomationProvider(config=None)

    provider_key = getattr(tenant_config, 'provider', 'system')
    if provider_key == 'sendgrid':
        return SendGridProvider(config=tenant_config)
    if provider_key == 'ses':
        return SESProvider(config=tenant_config)
    # smtp and system both use SMTP path
    return SMTPAutomationProvider(config=tenant_config)


__all__ = [
    'AutomationEmailProvider',
    'AutomationSendResult',
    'ProviderHealthStatus',
    'SMTPAutomationProvider',
    'SendGridProvider',
    'SESProvider',
    'get_provider',
]
