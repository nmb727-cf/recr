from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communications'

    def ready(self):
        # Register email event consumers (existing)
        from apps.communications.email_events import consumers  # noqa: F401
        # Register notification + thread event handlers (new)
        from apps.communications import event_handlers  # noqa: F401
