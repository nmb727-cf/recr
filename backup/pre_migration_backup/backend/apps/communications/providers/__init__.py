"""
Provider abstraction layer for multi-channel communication.

Usage:
    from apps.communications.providers import get_provider
    provider = get_provider(channel_type='whatsapp', provider_name='whatsapp_business_api', config=cfg)
    result = provider.send(recipient='+919876543210', body='Hello', template_name='interview_reminder')
"""
from apps.communications.providers.base import (
    BaseChannelProvider,
    SendResult,
    HealthCheckResult,
    ProviderUnavailableError,
    ProviderConfigError,
    ProviderSendError,
)

__all__ = [
    'BaseChannelProvider',
    'SendResult',
    'HealthCheckResult',
    'ProviderUnavailableError',
    'ProviderConfigError',
    'ProviderSendError',
    'get_provider',
    'get_whatsapp_provider',
    'get_sms_provider',
    'get_push_provider',
]


def get_whatsapp_provider(provider_name: str, config: dict) -> BaseChannelProvider:
    """Return an instantiated WhatsApp provider by name."""
    from apps.communications.providers.whatsapp.business_api import WhatsAppBusinessAPIProvider
    from apps.communications.providers.whatsapp.twilio import TwilioWhatsAppProvider
    from apps.communications.providers.whatsapp.mock import MockWhatsAppProvider

    providers = {
        'whatsapp_business_api': WhatsAppBusinessAPIProvider,
        'twilio_whatsapp': TwilioWhatsAppProvider,
        'mock': MockWhatsAppProvider,
    }
    klass = providers.get(provider_name)
    if klass is None:
        raise ProviderConfigError(f'Unknown WhatsApp provider: {provider_name!r}')
    return klass(config=config)


def get_sms_provider(provider_name: str, config: dict) -> BaseChannelProvider:
    """Return an instantiated SMS provider by name."""
    from apps.communications.providers.sms.twilio import TwilioSMSProvider
    from apps.communications.providers.sms.http import GenericHTTPSMSProvider
    from apps.communications.providers.sms.mock import MockSMSProvider

    providers = {
        'twilio': TwilioSMSProvider,
        'generic_http': GenericHTTPSMSProvider,
        'mock': MockSMSProvider,
    }
    klass = providers.get(provider_name)
    if klass is None:
        raise ProviderConfigError(f'Unknown SMS provider: {provider_name!r}')
    return klass(config=config)


def get_push_provider(provider_name: str, config: dict) -> BaseChannelProvider:
    """Return an instantiated Push provider by name."""
    from apps.communications.providers.push.placeholder import PlaceholderPushProvider

    providers = {
        'web_push':  PlaceholderPushProvider,
        'fcm':       PlaceholderPushProvider,
        'apns':      PlaceholderPushProvider,
        'mock':      PlaceholderPushProvider,
    }
    klass = providers.get(provider_name, PlaceholderPushProvider)
    return klass(config=config)


def get_provider(channel_type: str, provider_name: str, config: dict) -> BaseChannelProvider:
    """
    Factory: return the right provider instance for (channel_type, provider_name).

    Args:
        channel_type:  'whatsapp' | 'sms' | 'push'
        provider_name: provider identifier string
        config:        dict of provider config (usually from TenantChannelConfig)

    Raises:
        ProviderConfigError if channel_type or provider_name is unknown.
    """
    dispatch = {
        'whatsapp': get_whatsapp_provider,
        'sms':      get_sms_provider,
        'push':     get_push_provider,
    }
    factory = dispatch.get(channel_type)
    if factory is None:
        raise ProviderConfigError(f'No provider factory for channel: {channel_type!r}')
    return factory(provider_name, config)
