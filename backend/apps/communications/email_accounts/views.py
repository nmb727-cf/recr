import logging
import urllib.parse

from django.conf import settings
from django.db import DatabaseError, ProgrammingError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.email_accounts.serializers import EmailPreferenceSerializer, EmailSendingAccountSerializer
from apps.communications.email_accounts.services import UserEmailAccountManager
from apps.communications.email_audit.services import EmailAuditService
from apps.communications.feature_readiness import (
    email_not_ready_response,
    get_email_feature_status,
    get_oauth_provider_status,
)
from apps.communications.models import EmailPreference, EmailSendingAccount
from apps.communications.permissions import can_manage_email_accounts, can_view_email_accounts
from apps.core.responses import error_response, success_response

logger = logging.getLogger(__name__)


def _frontend_settings_url(result: str, **extra_params: str) -> str:
    """Return the frontend settings page URL with OAuth result params appended."""
    base = str(getattr(settings, 'FRONTEND_BASE_URL', '') or '').strip().rstrip('/')
    if not base:
        raise ValueError('FRONTEND_BASE_URL is not configured on the server.')
    if not (base.startswith('http://') or base.startswith('https://')):
        raise ValueError('FRONTEND_BASE_URL must include http:// or https://')
    params: dict[str, str] = {'tab': 'communication', 'email_connect': result}
    params.update(extra_params)
    final_url = f'{base}/settings?{urllib.parse.urlencode(params)}'
    logger.info('OAuth frontend redirect target: FRONTEND_BASE_URL=%s final_url=%s', base, final_url)
    return final_url


def _frontend_redirect_or_server_error(result: str, **extra_params: str):
    try:
        final_url = _frontend_settings_url(result, **extra_params)
    except ValueError as exc:
        logger.error('OAuth redirect configuration error: %s', exc)
        return HttpResponse(str(exc), status=500)
    return HttpResponseRedirect(final_url)


class EmailFeatureStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_info = get_email_feature_status()
        return success_response(
            data={
                'feature_ready': status_info.feature_ready,
                'message': status_info.message,
                'missing_tables': status_info.missing_tables,
            },
        )


class EmailOAuthStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data=get_oauth_provider_status())


class EmailAccountListView(APIView):
    permission_classes = [IsAuthenticated, can_view_email_accounts]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_accounts': []})

        try:
            qs = UserEmailAccountManager.get_accessible_accounts(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
            ).order_by('-created_at')
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_accounts': []})
        return success_response(data={'email_accounts': EmailSendingAccountSerializer(qs, many=True).data})


# ─── Gmail OAuth ──────────────────────────────────────────────────────────────

class GmailConnectInitiateView(APIView):
    """
    Start the Gmail OAuth flow.
    Returns an authorization URL that the frontend should redirect the browser to.
    The redirect_uri embedded in the auth URL points to the backend callback endpoint
    registered in Google Cloud Console — never to the frontend.
    """
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response()

        client_id = str(getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or '').strip()
        client_secret = str(getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '') or '').strip()
        redirect_uri = str(getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '') or '').strip()
        if not client_id:
            return error_response('GOOGLE_OAUTH_CLIENT_ID is not configured on the server.')
        if not client_secret:
            return error_response('GOOGLE_OAUTH_CLIENT_SECRET is not configured on the server.')
        if not redirect_uri:
            return error_response('GOOGLE_OAUTH_REDIRECT_URI is not configured on the server.')

        payload = UserEmailAccountManager.initiate_oauth(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
            provider_type='gmail_oauth',
            redirect_uri=redirect_uri,
        )
        return success_response(data=payload)


class GmailCallbackView(APIView):
    """
    Backend OAuth callback for Gmail.
    Google redirects here with ?code=...&state=...
    No user authentication needed — security is guaranteed by the state token.
    Exchanges code for tokens, stores them encrypted, then redirects to frontend.
    """
    permission_classes = []  # Unauthenticated — validated via state token

    def get(self, request):
        logger.info('Gmail OAuth callback hit: path=%s query_keys=%s', request.path, list(request.query_params.keys()))
        # User denied or provider returned an error
        error = request.query_params.get('error', '')
        if error:
            desc = request.query_params.get('error_description', error)
            logger.warning('Gmail OAuth callback error: %s — %s', error, desc)
            return _frontend_redirect_or_server_error('failed', reason=desc[:200])

        code = request.query_params.get('code', '')
        state = request.query_params.get('state', '')

        if not code or not state:
            logger.warning('Gmail OAuth callback missing params: code_present=%s state_present=%s', bool(code), bool(state))
            return _frontend_redirect_or_server_error('failed', reason='missing_code_or_state')

        redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '')
        if not redirect_uri:
            logger.error('Gmail OAuth callback server misconfigured: GOOGLE_OAUTH_REDIRECT_URI missing')
            return _frontend_redirect_or_server_error('failed', reason='server_misconfigured')

        try:
            account = UserEmailAccountManager.complete_oauth(
                state=state,
                code=code,
                redirect_uri=redirect_uri,
            )
        except Exception as exc:
            logger.exception('Gmail OAuth callback failed during completion')
            return _frontend_redirect_or_server_error('failed', reason=str(exc)[:200])

        try:
            EmailAuditService.record_usage(
                tenant_id=account.tenant_id,
                actor_user_id=account.user_id,
                action='email_account.connected',
                target_type='email_account',
                target_id=account.id,
                details={'provider_type': account.provider_type, 'email_address': account.email_address},
            )
        except Exception:
            pass  # Audit failure must not break the connect flow

        logger.info('Gmail OAuth callback completed successfully: account_id=%s email=%s', account.id, account.email_address)
        return _frontend_redirect_or_server_error('success', email=account.email_address)


# ─── Microsoft OAuth ──────────────────────────────────────────────────────────

class MicrosoftConnectInitiateView(APIView):
    """
    Start the Microsoft OAuth flow.
    Returns an authorization URL that the frontend should redirect the browser to.
    The redirect_uri embedded in the auth URL points to the backend callback endpoint
    registered in Azure — never to the frontend.
    """
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response()

        client_id = str(getattr(settings, 'MICROSOFT_OAUTH_CLIENT_ID', '') or '').strip()
        client_secret = str(getattr(settings, 'MICROSOFT_OAUTH_CLIENT_SECRET', '') or '').strip()
        redirect_uri = str(getattr(settings, 'MICROSOFT_OAUTH_REDIRECT_URI', '') or '').strip()
        if not client_id:
            return error_response('MICROSOFT_OAUTH_CLIENT_ID is not configured on the server.')
        if not client_secret:
            return error_response('MICROSOFT_OAUTH_CLIENT_SECRET is not configured on the server.')
        if not redirect_uri:
            return error_response('MICROSOFT_OAUTH_REDIRECT_URI is not configured on the server.')

        payload = UserEmailAccountManager.initiate_oauth(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
            provider_type='microsoft_oauth',
            redirect_uri=redirect_uri,
        )
        return success_response(data=payload)


class MicrosoftCallbackView(APIView):
    """
    Backend OAuth callback for Microsoft / Outlook.
    Microsoft redirects here with ?code=...&state=...
    No user authentication needed — security is guaranteed by the state token.
    Exchanges code for tokens, stores them encrypted, then redirects to frontend.
    """
    permission_classes = []  # Unauthenticated — validated via state token

    def get(self, request):
        logger.info('Microsoft OAuth callback hit: path=%s query_keys=%s', request.path, list(request.query_params.keys()))
        error = request.query_params.get('error', '')
        if error:
            desc = request.query_params.get('error_description', error)
            logger.warning('Microsoft OAuth callback error: %s — %s', error, desc)
            return _frontend_redirect_or_server_error('failed', reason=desc[:200])

        code = request.query_params.get('code', '')
        state = request.query_params.get('state', '')

        if not code or not state:
            logger.warning('Microsoft OAuth callback missing params: code_present=%s state_present=%s', bool(code), bool(state))
            return _frontend_redirect_or_server_error('failed', reason='missing_code_or_state')

        redirect_uri = getattr(settings, 'MICROSOFT_OAUTH_REDIRECT_URI', '')
        if not redirect_uri:
            logger.error('Microsoft OAuth callback server misconfigured: MICROSOFT_OAUTH_REDIRECT_URI missing')
            return _frontend_redirect_or_server_error('failed', reason='server_misconfigured')

        try:
            account = UserEmailAccountManager.complete_oauth(
                state=state,
                code=code,
                redirect_uri=redirect_uri,
            )
        except Exception as exc:
            logger.exception('Microsoft OAuth callback failed during completion')
            return _frontend_redirect_or_server_error('failed', reason=str(exc)[:200])

        try:
            EmailAuditService.record_usage(
                tenant_id=account.tenant_id,
                actor_user_id=account.user_id,
                action='email_account.connected',
                target_type='email_account',
                target_id=account.id,
                details={'provider_type': account.provider_type, 'email_address': account.email_address},
            )
        except Exception:
            pass

        logger.info('Microsoft OAuth callback completed successfully: account_id=%s email=%s', account.id, account.email_address)
        return _frontend_redirect_or_server_error('success', email=account.email_address)


# ─── Account management ───────────────────────────────────────────────────────

class SetDefaultSenderView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response()
        try:
            account = get_object_or_404(EmailSendingAccount, id=pk, tenant_id=request.user.tenant_id, deleted_at__isnull=True)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response()
        if account.account_scope == 'system':
            return error_response('System account cannot be changed.')
        UserEmailAccountManager.set_default_account(
            tenant_id=request.user.tenant_id,
            user_id=request.user.id,
            account=account,
        )
        EmailAuditService.record_usage(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            action='email_account.default_set',
            target_type='email_account',
            target_id=account.id,
            details={'email_address': account.email_address},
        )
        return success_response(data={'email_account': EmailSendingAccountSerializer(account).data})


class EmailAccountTestView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'ok': False, 'reason': '', 'email_account': None})
        try:
            account = get_object_or_404(EmailSendingAccount, id=pk, tenant_id=request.user.tenant_id, deleted_at__isnull=True)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'ok': False, 'reason': '', 'email_account': None})
        if account.account_scope == 'system':
            return success_response(data={'ok': True, 'reason': '', 'email_account': EmailSendingAccountSerializer(account).data})
        ok, reason = UserEmailAccountManager.test_connection(account=account)
        return success_response(
            data={'ok': ok, 'reason': reason, 'email_account': EmailSendingAccountSerializer(account).data},
            message='Connection healthy.' if ok else 'Connection failed.',
            status_code=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST,
        )


class EmailAccountReconnectView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'ok': False, 'reason': '', 'email_account': None})
        try:
            account = get_object_or_404(EmailSendingAccount, id=pk, tenant_id=request.user.tenant_id, deleted_at__isnull=True)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'ok': False, 'reason': '', 'email_account': None})
        if account.account_scope == 'system':
            return error_response('System account cannot be reconnected.')
        ok, reason = UserEmailAccountManager.test_connection(account=account)
        action = 'email_account.reconnected' if ok else 'email_account.reconnect_failed'
        EmailAuditService.record_usage(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            action=action,
            target_type='email_account',
            target_id=account.id,
            details={'reason': reason},
        )
        return success_response(
            data={'ok': ok, 'reason': reason, 'email_account': EmailSendingAccountSerializer(account).data},
            message='Reconnect successful.' if ok else 'Reconnect failed.',
            status_code=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST,
        )


class EmailAccountDisconnectView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response()
        try:
            account = get_object_or_404(EmailSendingAccount, id=pk, tenant_id=request.user.tenant_id, deleted_at__isnull=True)
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response()
        if account.account_scope == 'system':
            return error_response('System account cannot be disconnected.')
        UserEmailAccountManager.disconnect_account(account=account)
        EmailAuditService.record_usage(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            action='email_account.disconnected',
            target_type='email_account',
            target_id=account.id,
            details={'email_address': account.email_address},
        )
        return success_response(message='Email account disconnected.')


class SMTPAccountCreateView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def post(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_account': None})
        try:
            account = UserEmailAccountManager.create_smtp_account(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
                data=request.data,
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_account': None})
        return success_response(data={'email_account': EmailSendingAccountSerializer(account).data}, status_code=status.HTTP_201_CREATED)


class SMTPAccountPatchView(APIView):
    permission_classes = [IsAuthenticated, can_manage_email_accounts]

    def patch(self, request, pk):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_account': None})
        try:
            account = get_object_or_404(
                EmailSendingAccount,
                id=pk,
                tenant_id=request.user.tenant_id,
                provider_type='smtp',
                deleted_at__isnull=True,
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_account': None})
        serializer = EmailSendingAccountSerializer(account, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)
        serializer.save()
        return success_response(data={'email_account': serializer.data})


class EmailPreferenceView(APIView):
    permission_classes = [IsAuthenticated, can_view_email_accounts]

    def get(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_preferences': None})
        try:
            pref, _ = EmailPreference.objects.get_or_create(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
                defaults={'allow_system_fallback': True},
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_preferences': None})
        return success_response(data={'email_preferences': EmailPreferenceSerializer(pref).data})

    def patch(self, request):
        status_info = get_email_feature_status()
        if not status_info.feature_ready:
            return email_not_ready_response(empty_data={'email_preferences': None})
        try:
            pref, _ = EmailPreference.objects.get_or_create(
                tenant_id=request.user.tenant_id,
                user_id=request.user.id,
                defaults={'allow_system_fallback': True},
            )
        except (ProgrammingError, DatabaseError):
            return email_not_ready_response(empty_data={'email_preferences': None})
        serializer = EmailPreferenceSerializer(pref, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response('Validation failed', serializer.errors)
        serializer.save()
        EmailAuditService.record_usage(
            tenant_id=request.user.tenant_id,
            actor_user_id=request.user.id,
            action='email_preferences.updated',
            target_type='email_preference',
            target_id=pref.id,
            details=serializer.validated_data,
        )
        return success_response(data={'email_preferences': serializer.data})
