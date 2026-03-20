from django.urls import path
from apps.communications import views

urlpatterns = [
    # Messages
    path('messages/threads/', views.MessageThreadListView.as_view(), name='thread-list'),
    path('messages/threads/<uuid:pk>/', views.MessageThreadDetailView.as_view(), name='thread-detail'),
    path('messages/threads/<uuid:pk>/reply/', views.MessageReplyView.as_view(), name='thread-reply'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/read/', views.NotificationReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', views.NotificationReadAllView.as_view(), name='notification-read-all'),

    # Email templates
    path('communication/templates/', views.EmailTemplateListView.as_view(), name='email-template-list'),
    path('communication/templates/<uuid:pk>/', views.EmailTemplateDetailView.as_view(), name='email-template-detail'),
]