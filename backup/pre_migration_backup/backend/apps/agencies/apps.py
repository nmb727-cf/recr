from django.apps import AppConfig


class AgenciesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agencies'
    verbose_name = 'Agency Management System'

    def ready(self):
        import apps.agencies.signals  # noqa: F401
