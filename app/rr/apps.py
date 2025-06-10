from django.apps import AppConfig


class RrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rr'

    def ready(self):
        import rr.signals  # Import signals when the app is ready 