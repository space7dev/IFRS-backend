from django.apps import AppConfig


class ModelDefinitionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'model_definitions'
    verbose_name = 'Model Definitions'
