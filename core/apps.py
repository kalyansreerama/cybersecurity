# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # By importing models here, we ensure that the signal decorators
        # are registered when Django starts up.
        import core.models