from rest_framework import routers

from django.urls import path, include

from .views import (
    ModelDefinitionViewSet, 
    ModelDefinitionHistoryViewSet,
    DataUploadBatchViewSet,
    DataUploadViewSet,
    DataUploadTemplateViewSet,
    APIUploadLogViewSet,
    DataBatchStatusViewSet
)

router = routers.SimpleRouter()
router.register(r"history", ModelDefinitionHistoryViewSet, basename="model-definition-history")

router.register(r"data-upload-batches", DataUploadBatchViewSet, basename="data-upload-batch")
router.register(r"data-uploads", DataUploadViewSet, basename="data-upload")
router.register(r"data-upload-templates", DataUploadTemplateViewSet, basename="data-upload-template")
router.register(r"api-upload-logs", APIUploadLogViewSet, basename="api-upload-log")
router.register(r"data-batch-status", DataBatchStatusViewSet, basename="data-batch-status")
router.register(r"", ModelDefinitionViewSet, basename="model-definition")

api_patterns = router.urls 