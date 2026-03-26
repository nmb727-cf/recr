from django.urls import path

from apps.communications import views as legacy_views
from apps.communications.email_accounts import views as account_views
from apps.communications.email_audit import views as audit_views
from apps.communications.email_dispatch import views as dispatch_views
from apps.communications.email_templates import views as template_views
from apps.communications.email_webhooks import views as webhook_views

urlpatterns = [
    # Legacy messages/notifications
    path('messages/threads/', legacy_views.MessageThreadListView.as_view(), name='thread-list'),
    path('messages/threads/<uuid:pk>/', legacy_views.MessageThreadDetailView.as_view(), name='thread-detail'),
    path('messages/threads/<uuid:pk>/reply/', legacy_views.MessageReplyView.as_view(), name='thread-reply'),
    path('notifications/', legacy_views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/read/', legacy_views.NotificationReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', legacy_views.NotificationReadAllView.as_view(), name='notification-read-all'),

    # Legacy template/account endpoints kept for compatibility
    path('communication/templates/', legacy_views.EmailTemplateListView.as_view(), name='legacy-email-template-list'),
    path('communication/templates/<uuid:pk>/', legacy_views.EmailTemplateDetailView.as_view(), name='legacy-email-template-detail'),
    path('communication/email-accounts/', legacy_views.EmailAccountViewSet.as_view({'get': 'list', 'post': 'create'}), name='legacy-email-account-list'),
    path('communication/email-accounts/<uuid:pk>/', legacy_views.EmailAccountViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update', 'delete': 'destroy'}), name='legacy-email-account-detail'),

    # Phase-1 enterprise email architecture
    path('communications/email/feature-status', account_views.EmailFeatureStatusView.as_view(), name='email-feature-status'),
    path('communications/email/oauth-status', account_views.EmailOAuthStatusView.as_view(), name='email-oauth-status'),
    path('communications/email-accounts/', account_views.EmailAccountListView.as_view(), name='email-account-list'),
    path('communications/email-accounts/gmail/connect/initiate', account_views.GmailConnectInitiateView.as_view(), name='email-gmail-initiate'),
    path('communications/email-accounts/gmail/callback', account_views.GmailCallbackView.as_view(), name='email-gmail-callback'),
    path('communications/email-accounts/microsoft/connect/initiate', account_views.MicrosoftConnectInitiateView.as_view(), name='email-microsoft-initiate'),
    path('communications/email-accounts/microsoft/callback', account_views.MicrosoftCallbackView.as_view(), name='email-microsoft-callback'),
    path('communications/email-accounts/<uuid:pk>/set-default', account_views.SetDefaultSenderView.as_view(), name='email-set-default'),
    path('communications/email-accounts/<uuid:pk>/test', account_views.EmailAccountTestView.as_view(), name='email-account-test'),
    path('communications/email-accounts/<uuid:pk>/reconnect', account_views.EmailAccountReconnectView.as_view(), name='email-account-reconnect'),
    path('communications/email-accounts/<uuid:pk>/disconnect', account_views.EmailAccountDisconnectView.as_view(), name='email-account-disconnect'),

    # SMTP Phase-2 ready
    path('communications/email-accounts/smtp', account_views.SMTPAccountCreateView.as_view(), name='email-smtp-create'),
    path('communications/email-accounts/smtp/<uuid:pk>', account_views.SMTPAccountPatchView.as_view(), name='email-smtp-patch'),

    # Preferences
    path('communications/email-preferences/', account_views.EmailPreferenceView.as_view(), name='email-preferences'),

    # Templates and quick replies
    path('communications/email-templates/', template_views.EmailTemplateListCreateView.as_view(), name='email-template-list'),
    path('communications/email-templates/<uuid:pk>', template_views.EmailTemplateUpdateView.as_view(), name='email-template-patch'),
    path('communications/email-templates/<uuid:pk>/duplicate', template_views.EmailTemplateDuplicateView.as_view(), name='email-template-duplicate'),
    path('communications/email-templates/<uuid:pk>/preview', template_views.EmailTemplatePreviewView.as_view(), name='email-template-preview'),

    path('communications/quick-replies/', template_views.QuickReplyListCreateView.as_view(), name='quick-reply-list'),
    path('communications/quick-replies/<uuid:pk>', template_views.QuickReplyUpdateView.as_view(), name='quick-reply-patch'),

    # Send / preview
    path('communications/email/send', dispatch_views.EmailSendView.as_view(), name='email-send'),
    path('communications/email/send-test', dispatch_views.EmailSendTestView.as_view(), name='email-send-test'),
    path('communications/email/render-preview', dispatch_views.EmailRenderPreviewView.as_view(), name='email-render-preview'),
    path('communications/email/render-template', dispatch_views.EmailRenderTemplateView.as_view(), name='email-render-template'),

    # History / audit / webhooks
    path('communications/email-messages/', dispatch_views.EmailMessageListView.as_view(), name='email-message-list'),
    path('communications/email-messages/<uuid:pk>', dispatch_views.EmailMessageDetailView.as_view(), name='email-message-detail'),
    path('communications/email-audit/', audit_views.EmailAuditListView.as_view(), name='email-audit-list'),
    path('communications/email-webhooks/<str:provider>', webhook_views.EmailWebhookView.as_view(), name='email-webhook'),
]
