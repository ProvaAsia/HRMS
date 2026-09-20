from django.apps import AppConfig


class OvertimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'overtime'

    def ready(self):
        import overtime.signals  # noqa: F401
