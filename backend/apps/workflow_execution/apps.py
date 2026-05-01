from django.apps import AppConfig


class WorkflowExecutionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workflow_execution'
    label = 'workflow_execution'

    def ready(self):
        from apps.workflow_execution.signals import connect_signals
        connect_signals()
