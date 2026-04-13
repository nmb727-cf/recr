"""
WebSocket URL routing for the Communications module.
Add to your ASGI application when Django Channels is installed.

Usage in asgi.py:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from apps.communications.ws_routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        'http': django_asgi_app,
        'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    })
"""

websocket_urlpatterns = []

try:
    from django.urls import re_path
    from apps.communications.realtime import UserConsumer, ThreadConsumer, TenantConsumer, CHANNELS_AVAILABLE

    if CHANNELS_AVAILABLE:
        websocket_urlpatterns = [
            re_path(r'^ws/user/$', UserConsumer.as_asgi()),
            re_path(r'^ws/tenant/$', TenantConsumer.as_asgi()),
            re_path(r'^ws/threads/(?P<thread_id>[0-9a-f-]+)/$', ThreadConsumer.as_asgi()),
        ]
except ImportError:
    pass
