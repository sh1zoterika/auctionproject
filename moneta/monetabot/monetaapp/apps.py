from django.apps import AppConfig


class MonetaappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monetaapp'

    def ready(self):
        from . import signals