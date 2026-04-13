from django.urls import path

from apps.communications import views as legacy_views
from apps.communications import notification_control_views as ctrl_views
from apps.communications import notification_orchestration_views as orch_views
from apps.communications.email_accounts import views as account_views
from apps.communications.email_audit import views as audit_views
from apps.communications.email_dispatch import views as dispatch_views
from apps.communications.email_templates import views as template_views
from apps.communications.email_webhooks import views as webhook_views
from apps.communications import channel_views
from apps.communications import messaging_views
from apps.communications import presence_views
from apps.communications import search_views
from apps.communications import notification_preference_views
from apps.communications import analytics_views

urlpatterns = [
    # ── Communication Analytics API ────────────────────────────────────────
    path('communication-analytics/dashboard/', analytics_views.CommunicationDashboardView.as_view(), name='comms-analytics-dashboard'),
    path('communication-analytics/channels/', analytics_views.ChannelPerformanceView.as_view(), name='comms-analytics-channels'),
    path('communication-analytics/notifications/', analytics_views.NotificationEffectivenessView.as_view(), name='comms-analytics-notifications'),
    path('communication-analytics/response-times/', analytics_views.ResponseTimeView.as_view(), name='comms-analytics-response-times'),
    path('communication-analytics/workload/', analytics_views.WorkloadView.as_view(), name='comms-analytics-workload'),
    path('communication-analytics/fallbacks/', analytics_views.FallbackEscalationView.as_view(), name='comms-analytics-fallbacks'),
    path('communication-analytics/entities/', analytics_views.EntityCommunicationView.as_view(), name='comms-analytics-entities'),


    # ── User Notification Preferences API ──────────────────────────────────
    path('notifications/preferences/', notification_preference_views.UserNotificationPreferenceView.as_view(), name='user-notification-preferences'),
    path('notifications/preferences/bulk/', notification_preference_views.UserNotificationPreferenceBulkUpdateView.as_view(), name='user-notification-preferences-bulk'),
    path('notifications/preferences/reset/', notification_preference_views.UserNotificationPreferenceResetView.as_view(), name='user-notification-preferences-reset'),
    path('notifications/settings/', notification_preference_views.UserNotificationSettingView.as_view(), name='user-notification-settings'),

    # ── Real-time Presence API ──────────────────────────────────────────────
    path('communications/presence/', presence_views.UserPresenceView.as_view(), name='user-presence'),

    # ── Search & History API ──────────────────────────────────────────────
    path('communications/search/', search_views.GlobalCommunicationSearchView.as_view(), name='communication-search'),
    path('communications/history/<str:entity_type>/<uuid:entity_id>/', search_views.EntityCommunicationHistoryView.as_view(), name='entity-communication-history'),
    path('communications/recent/', search_views.RecentCommunicationsView.as_view(), name='communication-recent'),
    path('notifications/history/', search_views.NotificationHistoryView.as_view(), name='notification-history'),

    # ── Thread / Messaging API ──────────────────────────────────────────────
    path('messages/threads/', legacy_views.MessageThreadListView.as_view(), name='thread-list'),
    path('messages/threads/<uuid:pk>/', legacy_views.MessageThreadDetailView.as_view(), name='thread-detail'),
    path('messages/threads/<uuid:pk>/messages/', legacy_views.ThreadMessagesView.as_view(), name='thread-messages'),
    path('messages/threads/<uuid:pk>/search/', search_views.ThreadMessageSearchView.as_view(), name='thread-message-search'),
    path('messages/threads/<uuid:pk>/mark-read/', legacy_views.ThreadMarkReadView.as_view(), name='thread-mark-read'),
    path('messages/threads/<uuid:pk>/archive/', search_views.ArchiveThreadView.as_view(), name='thread-archive'),
    path('messages/threads/<uuid:pk>/unarchive/', search_views.UnarchiveThreadView.as_view(), name='thread-unarchive'),
    path('messages/archived/', search_views.ArchivedThreadListView.as_view(), name='thread-archived-list'),
    path('messages/threads/<uuid:pk>/reply/', legacy_views.MessageReplyView.as_view(), name='thread-reply'),

    # ── Messaging engine extensions ─────────────────────────────────────────
    path('messages/unread-count/', messaging_views.MessagingUnreadCountView.as_view(), name='messaging-unread-count'),
    path('messages/threads/entity/', messaging_views.EntityThreadView.as_view(), name='messaging-entity-thread'),
    path('messages/threads/<uuid:pk>/participants/', messaging_views.ThreadParticipantAddView.as_view(), name='messaging-participant-add'),
    path('messages/participants/<uuid:participant_id>/', messaging_views.ThreadParticipantRemoveView.as_view(), name='messaging-participant-remove'),

    # ── Notification API ────────────────────────────────────────────────────
    path('notifications/', legacy_views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', legacy_views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('notifications/mark-all-read/', legacy_views.NotificationReadAllView.as_view(), name='notification-mark-all-read'),
    path('notifications/<uuid:pk>/mark-read/', legacy_views.NotificationReadView.as_view(), name='notification-mark-read'),
    # Legacy URLs (backward compat)
    path('notifications/<uuid:pk>/read/', legacy_views.NotificationReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', legacy_views.NotificationReadAllView.as_view(), name='notification-read-all'),

    # ── Notification Control Center (Admin) ────────────────────────────────
    path('notification-control/rules/', ctrl_views.NotificationRuleListView.as_view(), name='nc-rule-list'),
    path('notification-control/rules/<str:event_key>/', ctrl_views.NotificationRuleDetailView.as_view(), name='nc-rule-detail'),
    path('notification-control/channel-settings/', ctrl_views.NotificationChannelSettingsView.as_view(), name='nc-channel-settings'),
    path('notification-control/default-preferences/', ctrl_views.NotificationPreferenceDefaultsView.as_view(), name='nc-default-prefs'),
    path('notification-control/summary/', ctrl_views.NotificationControlSummaryView.as_view(), name='nc-summary'),
    path('notification-control/rules/<str:event_key>/test/', orch_views.NotificationRuleTestView.as_view(), name='nc-rule-test'),

    # ── Automation Job Control ──────────────────────────────────────────────
    path('notification-control/jobs/', orch_views.NotificationAutomationJobListView.as_view(), name='nc-jobs-list'),
    path('notification-control/jobs/<uuid:job_id>/retry/', orch_views.NotificationAutomationJobRetryView.as_view(), name='nc-job-retry'),
    path('notification-control/jobs/<uuid:job_id>/cancel/', orch_views.NotificationAutomationJobCancelView.as_view(), name='nc-job-cancel'),

    # ── Escalation Logs ─────────────────────────────────────────────────────
    path('notification-control/escalations/', orch_views.NotificationEscalationLogListView.as_view(), name='nc-escalations-list'),

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

    # ── Automation delivery observability ───────────────────────────────────
    path('communications/email/deliveries/', dispatch_views.EmailDeliveryListView.as_view(), name='email-delivery-list'),
    path('communications/email/deliveries/<uuid:delivery_id>/', dispatch_views.EmailDeliveryDetailView.as_view(), name='email-delivery-detail'),
    path('communications/email/deliveries/<uuid:delivery_id>/retry/', dispatch_views.EmailDeliveryRetryView.as_view(), name='email-delivery-retry'),
    path('communications/email/health/', dispatch_views.EmailHealthView.as_view(), name='email-health'),

    # ── Multi-channel engine — observability ────────────────────────────────
    path('communications/deliveries/', channel_views.CommunicationDeliveryListView.as_view(), name='channel-delivery-list'),
    path('communications/deliveries/<uuid:delivery_id>/', channel_views.CommunicationDeliveryDetailView.as_view(), name='channel-delivery-detail'),
    path('communications/deliveries/<uuid:delivery_id>/retry/', channel_views.CommunicationDeliveryRetryView.as_view(), name='channel-delivery-retry'),
    path('communications/channel-health/', channel_views.ChannelHealthView.as_view(), name='channel-health'),
    path('communications/fallback-jobs/', channel_views.FallbackJobListView.as_view(), name='channel-fallback-jobs'),
    path('communications/channel-stats/', channel_views.ChannelStatsView.as_view(), name='channel-stats'),

    # ── Multi-channel engine — tenant config ────────────────────────────────
    path('communications/channel-configs/', channel_views.TenantChannelConfigListView.as_view(), name='channel-config-list'),
    path('communications/channel-configs/<uuid:config_id>/', channel_views.TenantChannelConfigDetailView.as_view(), name='channel-config-detail'),
]
