from django.apps import AppConfig


class CustomLoginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom_login'

    def ready(self):
        import custom_login.signals

