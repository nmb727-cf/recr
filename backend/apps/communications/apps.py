from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communications'

    def ready(self):
        # Register event consumers.
        from apps.communications.email_events import consumers  # noqa: F401
