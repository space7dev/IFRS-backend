from rest_framework import routers

from django.urls import path, include

from .views import (
    ModelDefinitionViewSet, 
    ModelDefinitionHistoryViewSet,
    DataUploadBatchViewSet,
    DataUploadViewSet,
    DataUploadTemplateViewSet,
    APIUploadLogViewSet,
    DataBatchStatusViewSet,
    DocumentTypeConfigViewSet,
    CalculationConfigViewSet,
    ConversionConfigViewSet,
    CurrencyViewSet,
    LineOfBusinessViewSet,
    ReportTypeViewSet,
    IFRSEngineResultViewSet,
    IFRSEngineInputViewSet
)

router = routers.SimpleRouter()
router.register(r"history", ModelDefinitionHistoryViewSet, basename="model-definition-history")

router.register(r"data-upload-batches", DataUploadBatchViewSet, basename="data-upload-batch")
router.register(r"data-uploads", DataUploadViewSet, basename="data-upload")
router.register(r"data-upload-templates", DataUploadTemplateViewSet, basename="data-upload-template")
router.register(r"api-upload-logs", APIUploadLogViewSet, basename="api-upload-log")
router.register(r"data-batch-status", DataBatchStatusViewSet, basename="data-batch-status")
router.register(r"document-type-config", DocumentTypeConfigViewSet, basename="document-type-config")
router.register(r"calculation-config", CalculationConfigViewSet, basename="calculation-config")
router.register(r"conversion-config", ConversionConfigViewSet, basename="conversion-config")
router.register(r'ifrs-engine-inputs', IFRSEngineInputViewSet)
router.register(r"currencies", CurrencyViewSet, basename="currency")
router.register(r"line-of-business", LineOfBusinessViewSet, basename="line-of-business")
router.register(r"report-types", ReportTypeViewSet, basename="report-type")
router.register(r"ifrs-engine-results", IFRSEngineResultViewSet, basename="ifrs-engine-result")
router.register(r"", ModelDefinitionViewSet, basename="model-definition")

api_patterns = router.urls 