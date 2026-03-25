from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.communications.constants import SYSTEM_EMAIL_PURPOSES
from apps.communications.email_accounts.providers import get_provider
from apps.communications.email_accounts.services import UserEmailAccountManager
from apps.communications.email_dispatch.types import EmailSendRequest, ResolvedRoute
from apps.communications.models import (
    EmailPreference,
    EmailProviderType,
    EmailRouteUsed,
    EmailSendingAccount,
)


class EmailRoutingService:
    @staticmethod
    def _is_system_email(request: EmailSendRequest) -> bool:
        if request.email_type == 'system':
            return True
        return request.message_purpose in SYSTEM_EMAIL_PURPOSES

    @staticmethod
    def _is_account_healthy(account: EmailSendingAccount) -> bool:
        if account.deleted_at:
            return False
        if not account.can_send:
            return False
        if account.status not in ('connected', 'pending'):
            return False

        # Refresh OAuth account if token has expired.
        if account.provider_type in (EmailProviderType.GMAIL_OAUTH, EmailProviderType.MICROSOFT_OAUTH):
            if account.token_expires_at and account.token_expires_at <= timezone.now():
                provider = get_provider(account.provider_type)
                refreshed = provider.refresh_credentials(account)
                if not refreshed:
                    account.status = 'error'
                    account.health_status = 'degraded'
                    account.last_failure_at = timezone.now()
                    account.failure_reason = 'OAuth token refresh failed'
                    account.save(update_fields=['status', 'health_status', 'last_failure_at', 'failure_reason', 'updated_at'])
                    return False
        return True

    @staticmethod
    def _resolve_system_route(request: EmailSendRequest) -> ResolvedRoute:
        system_account = UserEmailAccountManager.ensure_system_account(tenant_id=request.tenant_id)
        system_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@talentos.com')
        system_from_name = getattr(settings, 'SYSTEM_EMAIL_FROM_NAME', 'TalentOS Notifications')
        return ResolvedRoute(
            provider_key='system',
            route_used=EmailRouteUsed.SYSTEM_EMAIL_FALLBACK,
            account_id=str(system_account.id),
            from_email=system_account.email_address or system_from_email,
            from_name=system_account.from_name or system_from_name,
            reply_to_email=request.reply_to_email,
            fallback_applied=False,
        )

    @staticmethod
    def _pref(tenant_id, user_id):
        return EmailPreference.objects.filter(tenant_id=tenant_id, user_id=user_id).first()

    @classmethod
    def _pick_business_account(cls, request: EmailSendRequest) -> EmailSendingAccount | None:
        tenant_id = request.tenant_id
        user_id = request.actor_user_id

        if request.preferred_sender_account_id:
            account = EmailSendingAccount.objects.filter(
                id=request.preferred_sender_account_id,
                tenant_id=tenant_id,
                deleted_at__isnull=True,
            ).first()
            if account and cls._is_account_healthy(account):
                if account.account_scope == 'tenant_shared' and user_id:
                    if not UserEmailAccountManager.can_send_from_shared_account(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        account_id=str(account.id),
                    ):
                        return None
                return account

        if user_id:
            user_default = EmailSendingAccount.objects.filter(
                tenant_id=tenant_id,
                user_id=user_id,
                is_default_sender=True,
                deleted_at__isnull=True,
            ).first()
            if user_default and cls._is_account_healthy(user_default):
                return user_default

            pref = cls._pref(tenant_id, user_id)
            if pref and pref.default_sender_account_id:
                account = EmailSendingAccount.objects.filter(id=pref.default_sender_account_id, tenant_id=tenant_id, deleted_at__isnull=True).first()
                if account and cls._is_account_healthy(account):
                    return account

        tenant_default = EmailSendingAccount.objects.filter(
            tenant_id=tenant_id,
            user_id__isnull=True,
            account_scope='tenant_shared',
            is_default_sender=True,
            deleted_at__isnull=True,
        ).first()
        if tenant_default and cls._is_account_healthy(tenant_default):
            return tenant_default

        any_healthy = EmailSendingAccount.objects.filter(
            tenant_id=tenant_id,
            deleted_at__isnull=True,
            can_send=True,
            status='connected',
        ).filter(
            Q(user_id=user_id) | Q(account_scope='tenant_shared')
        ).exclude(provider_type='system').first()
        if any_healthy and cls._is_account_healthy(any_healthy):
            return any_healthy

        return None

    @classmethod
    def resolve_route(cls, request: EmailSendRequest) -> ResolvedRoute:
        if cls._is_system_email(request):
            return cls._resolve_system_route(request)

        account = cls._pick_business_account(request)
        if account:
            return ResolvedRoute(
                provider_key=account.provider_type,
                route_used=EmailRouteUsed.USER_EMAIL,
                account_id=str(account.id),
                from_email=account.email_address,
                from_name=account.from_name or account.display_name,
                reply_to_email=request.reply_to_email or account.email_address,
                fallback_applied=False,
            )

        fallback_allowed = request.allow_fallback
        if request.actor_user_id:
            pref = cls._pref(request.tenant_id, request.actor_user_id)
            if pref is not None:
                fallback_allowed = fallback_allowed and pref.allow_system_fallback

        if fallback_allowed:
            system_route = cls._resolve_system_route(request)
            system_route.fallback_applied = True
            intended_reply_to = request.reply_to_email
            if request.actor_user_id:
                actor_default = EmailSendingAccount.objects.filter(
                    tenant_id=request.tenant_id,
                    user_id=request.actor_user_id,
                    deleted_at__isnull=True,
                ).exclude(provider_type='system').first()
                if actor_default:
                    intended_reply_to = actor_default.email_address

            system_route.reply_to_email = intended_reply_to or system_route.reply_to_email
            if intended_reply_to:
                system_route.from_name = f'TalentOS via {intended_reply_to}'
            return system_route

        raise ValueError('No healthy sender account available and fallback is disabled. Connect or reconnect an email account.')
