from rest_framework import routers

from django.urls import path, include

from .views import ModelDefinitionViewSet, ModelDefinitionHistoryViewSet

router = routers.SimpleRouter()
router.register(r"", ModelDefinitionViewSet, basename="model-definition")
router.register(r"history", ModelDefinitionHistoryViewSet, basename="model-definition-history")

api_patterns = router.urls 