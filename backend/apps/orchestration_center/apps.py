from django.apps import AppConfig


class OrchestrationCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orchestration_center'
    verbose_name = 'Intelligence Control Center'

    def ready(self):
        from apps.orchestration_center.consumers import event_consumers  # noqa: F401
