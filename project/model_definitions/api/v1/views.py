from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination

from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, Http404

from model_definitions.models import ModelDefinition, ModelDefinitionHistory, DataUploadBatch, DataUpload, DataUploadTemplate, APIUploadLog, DataBatchStatus, DocumentTypeConfig, CalculationConfig, ConversionConfig, Currency, LineOfBusiness, ReportType, IFRSEngineResult, IFRSEngineInput
from .serializers import (
    ModelDefinitionListSerializer,
    ModelDefinitionDetailSerializer,
    ModelDefinitionCreateSerializer,
    ModelDefinitionUpdateSerializer,
    ModelDefinitionHistorySerializer,
    DataUploadBatchSerializer,
    DataUploadSerializer,
    DataUploadTemplateSerializer,
    APIUploadLogSerializer,
    DataBatchStatusSerializer,
    FileUploadSerializer,
    BulkUploadSerializer,
    DocumentTypeConfigSerializer,
    DocumentTypeConfigListSerializer,
    DocumentTypeConfigCreateSerializer,
    DocumentTypeConfigUpdateSerializer,
    CalculationConfigSerializer,
    CalculationConfigListSerializer,
    CalculationConfigCreateSerializer,
    CalculationConfigUpdateSerializer,
    ConversionConfigSerializer,
    ConversionConfigListSerializer,
    ConversionConfigCreateSerializer,
    ConversionConfigUpdateSerializer,
    CurrencySerializer,
    CurrencyListSerializer,
    CurrencyCreateSerializer,
    CurrencyUpdateSerializer,
    LineOfBusinessSerializer,
    LineOfBusinessListSerializer,
    LineOfBusinessCreateSerializer,
    LineOfBusinessUpdateSerializer,
    ReportTypeSerializer,
    ReportTypeCreateSerializer,
    ReportTypeUpdateSerializer,
    IFRSEngineResultSerializer,
    IFRSEngineResultCreateSerializer,
    ReportGenerationSerializer,
    IFRSEngineInputSerializer
)


class ModelDefinitionViewSet(viewsets.ModelViewSet):
    queryset = ModelDefinition.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['created_by']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on', 'modified_on']
    ordering = ['-modified_on']

    def get_serializer_class(self):
        if self.action == 'list':
            return ModelDefinitionListSerializer
        elif self.action == 'create':
            return ModelDefinitionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ModelDefinitionUpdateSerializer
        return ModelDefinitionDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        measurement_model = self.request.query_params.get('measurement_model')
        if measurement_model:
            queryset = queryset.filter(config__general_info__measurement_model=measurement_model)
        
        product_type = self.request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(config__general_info__product_type=product_type)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(config__general_info__status=status)
        
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Model definitions retrieved successfully.",
                "results": response.data
            })
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Model definition retrieved successfully.",
                "model_definition": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            model_def = serializer.save()
            
            ModelDefinitionHistory.objects.create(
                model=model_def,
                name=model_def.name,
                version=model_def.version,
                config=model_def.config,
                modified_by=request.user
            )
        
        detail_serializer = ModelDefinitionDetailSerializer(
            model_def, context={'request': request}
        )
        
        return Response({
            "detail": "Model definition created successfully.",
            "model_definition": detail_serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if instance.locked_by and instance.locked_by != request.user:
            return Response({
                "detail": f"Model is currently being edited by {instance.locked_by.get_full_name()}."
            }, status=status.HTTP_423_LOCKED)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            updated_instance = serializer.save()
        
        detail_serializer = ModelDefinitionDetailSerializer(
            updated_instance, context={'request': request}
        )
        
        return Response({
            "detail": "Model definition updated successfully.",
            "model_definition": detail_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not instance.can_edit(request.user):
            return Response({
                "detail": "You cannot delete this model."
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        
        return Response({
            "detail": "Model definition deleted successfully."
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        instance = self.get_object()
        
        if instance.locked_by and instance.locked_by != request.user:
            return Response({
                "detail": f"Model is already locked by {instance.locked_by.get_full_name()}.",
                "locked_by": instance.locked_by.get_full_name(),
                "locked_at": instance.locked_at
            }, status=status.HTTP_423_LOCKED)
        
        instance.locked_by = request.user
        instance.locked_at = timezone.now()
        instance.save()
        
        return Response({
            "detail": "Model locked successfully.",
            "locked_by": request.user.get_full_name(),
            "locked_at": instance.locked_at
        })

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        instance = self.get_object()
        
        if instance.locked_by != request.user and not request.user.is_superuser:
            return Response({
                "detail": "You can only unlock models that you have locked."
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.locked_by = None
        instance.locked_at = None
        instance.save()
        
        return Response({
            "detail": "Model unlocked successfully."
        })

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        source_instance = self.get_object()
        
        new_name = request.data.get('name')
        if not new_name:
            return Response({
                "detail": "New model name is required for cloning."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if ModelDefinition.objects.filter(name=new_name).exists():
            return Response({
                "detail": "A model with this name already exists."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cloned_config = source_instance.config.copy()
        
        if 'generalInfo' in cloned_config:
            general_info = cloned_config['generalInfo']
            cloned_config['general_info'] = {
                'product_type': general_info.get('productType', ''),
                'measurement_model': general_info.get('measurementModel', ''),
                **{k: v for k, v in general_info.items() if k not in ['productType', 'measurementModel']}
            }
        elif 'general_info' not in cloned_config:
            cloned_config['general_info'] = {
                'product_type': '',  # Will need to be filled
                'measurement_model': 'GMM',  # Default value
            }
        
        cloned_data = {
            'name': new_name,
            'config': cloned_config,
            'cloned_from': source_instance.id
        }
        
        serializer = ModelDefinitionCreateSerializer(
            data=cloned_data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            cloned_instance = serializer.save()
            
            ModelDefinitionHistory.objects.create(
                model=cloned_instance,
                name=cloned_instance.name,
                version=cloned_instance.version,
                config=cloned_instance.config,
                modified_by=request.user
            )
        
        detail_serializer = ModelDefinitionDetailSerializer(
            cloned_instance, context={'request': request}
        )
        
        return Response({
            "detail": "Model cloned successfully.",
            "model_definition": detail_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        instance = self.get_object()
        history_records = ModelDefinitionHistory.objects.filter(model=instance)
        
        serializer = ModelDefinitionHistorySerializer(
            history_records, many=True, context={'request': request}
        )
        
        return Response({
            "detail": "Model definition history retrieved successfully.",
            "history": serializer.data
        })


class ModelDefinitionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModelDefinitionHistory.objects.all()
    serializer_class = ModelDefinitionHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model', 'modified_by']
    search_fields = ['name', 'model__name']
    ordering_fields = ['saved_at']
    ordering = ['-saved_at']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Model definition history retrieved successfully.",
                "results": response.data
            })
        return response

class DataUploadBatchViewSet(viewsets.ModelViewSet):
    queryset = DataUploadBatch.objects.all()
    serializer_class = DataUploadBatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_status', 'batch_type', 'batch_model', 'insurance_type', 'batch_year', 'batch_quarter', 'created_by']
    search_fields = ['batch_id', 'name']
    ordering_fields = ['created_on', 'modified_on']
    ordering = ['-created_on']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Data upload batches retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        
        return Response({
            "detail": "Data upload batch created successfully.",
            "batch": DataUploadBatchSerializer(batch).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def complete_batch(self, request, pk=None):
        batch = self.get_object()
        
        if batch.batch_status != 'pending':
            return Response({
                "detail": "Only pending batches can be completed."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if batch.upload_count == 0:
            return Response({
                "detail": "Cannot complete batch without any uploads."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        batch.batch_status = 'completed'
        batch.save()
        
        return Response({
            "detail": "Batch completed successfully.",
            "batch": DataUploadBatchSerializer(batch).data
        })

    @action(detail=True, methods=['get'])
    def status_records(self, request, pk=None):
        batch = self.get_object()
        status_records = DataBatchStatus.objects.filter(batch_id=batch.batch_id)
        serializer = DataBatchStatusSerializer(status_records, many=True)
        
        return Response({
            "detail": "Batch status records retrieved successfully.",
            "results": serializer.data
        })


class DataUploadViewSet(viewsets.ModelViewSet):
    queryset = DataUpload.objects.all()
    serializer_class = DataUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['source', 'insurance_type', 'data_type', 'quarter', 'year', 'validation_status', 'batch']
    search_fields = ['upload_id', 'batch__batch_id', 'original_filename']
    ordering_fields = ['created_on', 'modified_on']
    ordering = ['-created_on']

    def get_serializer_class(self):
        if self.action == 'upload_file':
            return FileUploadSerializer
        elif self.action == 'bulk_upload':
            return BulkUploadSerializer
        return DataUploadSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Data uploads retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.save()
        
        return Response({
            "detail": "Data upload created successfully.",
            "upload": DataUploadSerializer(upload).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.save()
        
        return Response({
            "detail": "File uploaded successfully.",
            "upload": DataUploadSerializer(upload).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploads = serializer.save()
        
        return Response({
            "detail": f"{len(uploads)} files uploaded successfully.",
            "uploads": [DataUploadSerializer(upload).data for upload in uploads]
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        upload = self.get_object()
        
        if not upload.file_upload:
            return Response({
                "detail": "No file associated with this upload."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = HttpResponse(upload.file_upload.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{upload.original_filename}"'
            return response
        except Exception as e:
            return Response({
                "detail": "Error downloading file.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def retry_validation(self, request, pk=None):
        upload = self.get_object()
        
        if upload.validation_status != 'failed':
            return Response({
                "detail": "Only failed uploads can be retried."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: Implement retry validation logic
        upload.validation_status = 'in_progress'
        upload.error_count = 0
        upload.validation_errors = []
        upload.save()
        
        return Response({
            "detail": "Validation retry initiated.",
            "upload": DataUploadSerializer(upload).data
        })


class DataUploadTemplateViewSet(viewsets.ModelViewSet):
    queryset = DataUploadTemplate.objects.all()
    serializer_class = DataUploadTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['data_type', 'is_active', 'is_standard_template']
    search_fields = ['name', 'data_type']
    ordering_fields = ['created_on', 'modified_on']
    ordering = ['-created_on']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Data upload templates retrieved successfully.",
                "results": response.data
            })
        return response

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        template = self.get_object()
        
        if not template.template_file:
            return Response({
                "detail": "No template file associated with this template."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = HttpResponse(template.template_file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{template.name}.xlsx"'
            return response
        except Exception as e:
            return Response({
                "detail": "Error downloading template.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def get_by_data_type(self, request):
        data_type = request.query_params.get('data_type')
        if not data_type:
            return Response({
                "detail": "data_type parameter is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        templates = self.get_queryset().filter(data_type=data_type, is_active=True)
        serializer = self.get_serializer(templates, many=True)
        
        return Response({
            "detail": "Templates retrieved successfully.",
            "results": serializer.data
        })


class APIUploadLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = APIUploadLog.objects.all()
    serializer_class = APIUploadLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'reporting_date']
    search_fields = ['data_upload__upload_id']
    ordering_fields = ['upload_date', 'reporting_date']
    ordering = ['-upload_date']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "API upload logs retrieved successfully.",
                "results": response.data
            })
        return response

    @action(detail=True, methods=['post'])
    def retry_upload(self, request, pk=None):
        api_log = self.get_object()
        
        if api_log.status != 'failed':
            return Response({
                "detail": "Only failed uploads can be retried."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: Implement retry upload logic
        # This would typically involve re-processing the API payload
        
        return Response({
            "detail": "API upload retry initiated.",
            "log": APIUploadLogSerializer(api_log).data
        })


class DataBatchStatusViewSet(viewsets.ModelViewSet):
    queryset = DataBatchStatus.objects.all()
    serializer_class = DataBatchStatusSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_id', 'document_type', 'upload_status']
    search_fields = ['batch_id', 'document_type']
    ordering_fields = ['batch_id', 'document_type']
    ordering = ['batch_id', 'document_type']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Batch status records retrieved successfully.",
                "results": response.data
            })
        return response

    @action(detail=False, methods=['get'])
    def get_by_batch(self, request):
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response({
                "detail": "batch_id parameter is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        status_records = self.get_queryset().filter(batch_id=batch_id)
        serializer = self.get_serializer(status_records, many=True)
        
        return Response({
            "detail": "Batch status records retrieved successfully.",
            "results": serializer.data
        })

    @action(detail=False, methods=['post'])
    def update_status(self, request):
        batch_id = request.data.get('batch_id')
        document_type = request.data.get('document_type')
        upload_status = request.data.get('upload_status')
        
        if not batch_id or not document_type or upload_status is None:
            return Response({
                "detail": "batch_id, document_type, and upload_status are required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            status_record = DataBatchStatus.objects.get(
                batch_id=batch_id,
                document_type=document_type
            )
            status_record.upload_status = upload_status
            status_record.save()
            
            return Response({
                "detail": "Status updated successfully.",
                "status_record": DataBatchStatusSerializer(status_record).data
            })
        except DataBatchStatus.DoesNotExist:
            return Response({
                "detail": "Status record not found."
            }, status=status.HTTP_404_NOT_FOUND)


class DocumentTypeConfigViewSet(viewsets.ModelViewSet):
    queryset = DocumentTypeConfig.objects.all()
    serializer_class = DocumentTypeConfigSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_type', 'batch_model', 'insurance_type', 'required']
    search_fields = ['document_type', 'batch_type', 'batch_model', 'insurance_type']
    ordering_fields = ['created_on', 'modified_on', 'batch_type', 'batch_model', 'insurance_type', 'document_type']
    ordering = ['batch_type', 'batch_model', 'insurance_type', 'document_type']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentTypeConfigListSerializer
        elif self.action == 'create':
            return DocumentTypeConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentTypeConfigUpdateSerializer
        return DocumentTypeConfigSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Document type configurations retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_type_config = serializer.save()
        
        return Response({
            "detail": "Document type configuration created successfully.",
            "documentTypeConfig": DocumentTypeConfigSerializer(document_type_config, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        document_type_config = serializer.save()
        
        return Response({
            "detail": "Document type configuration updated successfully.",
            "documentTypeConfig": DocumentTypeConfigSerializer(document_type_config, context={'request': request}).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "detail": "Document type configuration deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download_template(self, request, pk=None):
        document_type_config = self.get_object()
        
        if not document_type_config.template:
            return Response({
                "detail": "No template file associated with this configuration."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = HttpResponse(
                document_type_config.template.read(), 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = document_type_config.template.name.split('/')[-1]
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                "detail": "Error downloading template file.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalculationConfigViewSet(viewsets.ModelViewSet):
    queryset = CalculationConfig.objects.all()
    serializer_class = CalculationConfigSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_type', 'batch_model', 'insurance_type', 'required']
    search_fields = ['engine_type', 'batch_type', 'batch_model', 'insurance_type']
    ordering_fields = ['created_on', 'modified_on', 'batch_type', 'batch_model', 'insurance_type', 'engine_type']
    ordering = ['batch_type', 'batch_model', 'insurance_type', 'engine_type']

    def get_serializer_class(self):
        if self.action == 'list':
            return CalculationConfigListSerializer
        elif self.action == 'create':
            return CalculationConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CalculationConfigUpdateSerializer
        return CalculationConfigSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Calculation configurations retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calculation_config = serializer.save()
        
        return Response({
            "detail": "Calculation configuration created successfully.",
            "engineConfig": CalculationConfigSerializer(calculation_config, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        calculation_config = serializer.save()
        
        return Response({
            "detail": "Calculation configuration updated successfully.",
            "engineConfig": CalculationConfigSerializer(calculation_config, context={'request': request}).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "detail": "Calculation configuration deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download_script(self, request, pk=None):
        calculation_config = self.get_object()
        
        if not calculation_config.script:
            return Response({
                "detail": "No script file associated with this configuration."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = HttpResponse(
                calculation_config.script.read(), 
                content_type='text/x-python'
            )
            filename = calculation_config.script.name.split('/')[-1]
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                "detail": "Error downloading script file.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversionConfigViewSet(viewsets.ModelViewSet):
    queryset = ConversionConfig.objects.all()
    serializer_class = ConversionConfigSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_type', 'batch_model', 'insurance_type', 'required']
    search_fields = ['engine_type', 'batch_type', 'batch_model', 'insurance_type']
    ordering_fields = ['created_on', 'modified_on', 'batch_type', 'batch_model', 'insurance_type', 'engine_type']
    ordering = ['batch_type', 'batch_model', 'insurance_type', 'engine_type']

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversionConfigListSerializer
        elif self.action == 'create':
            return ConversionConfigCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConversionConfigUpdateSerializer
        return ConversionConfigSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Conversion configurations retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                "detail": "Conversion configuration created successfully.",
                "conversion_config": response.data
            }, status=status.HTTP_201_CREATED)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Conversion configuration updated successfully.",
                "conversion_config": response.data
            })
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response({
                "detail": "Conversion configuration deleted successfully."
            }, status=status.HTTP_200_OK)
        return response

    @action(detail=True, methods=['get'])
    def download_script(self, request, pk=None):
        try:
            conversion_config = self.get_object()
            if not conversion_config.script:
                return Response({
                    "detail": "No script file available for this conversion configuration."
                }, status=status.HTTP_404_NOT_FOUND)
            
            response = HttpResponse(conversion_config.script, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{conversion_config.script.name.split("/")[-1]}"'
            return response
        except Http404:
            return Response({
                "detail": "Conversion configuration not found."
            }, status=status.HTTP_404_NOT_FOUND)


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'created_on', 'modified_on']
    ordering = ['code']

    def get_serializer_class(self):
        if self.action == 'list':
            return CurrencyListSerializer
        elif self.action == 'create':
            return CurrencyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CurrencyUpdateSerializer
        return CurrencySerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Currencies retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                "detail": "Currency created successfully.",
                "currency": response.data
            }, status=status.HTTP_201_CREATED)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Currency updated successfully.",
                "currency": response.data
            })
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response({
                "detail": "Currency deleted successfully."
            }, status=status.HTTP_200_OK)
        return response

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active currencies"""
        currencies = Currency.objects.filter(is_active=True).order_by('code')
        serializer = CurrencyListSerializer(currencies, many=True)
        return Response({
            "detail": "Active currencies retrieved successfully.",
            "results": serializer.data
        })


class LineOfBusinessViewSet(viewsets.ModelViewSet):
    queryset = LineOfBusiness.objects.all()
    serializer_class = LineOfBusinessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_model', 'insurance_type', 'currency', 'is_active']
    search_fields = ['line_of_business', 'batch_model', 'insurance_type']
    ordering_fields = ['created_on', 'modified_on', 'batch_model', 'insurance_type', 'line_of_business']
    ordering = ['batch_model', 'insurance_type', 'line_of_business']

    def get_serializer_class(self):
        if self.action == 'list':
            return LineOfBusinessListSerializer
        elif self.action == 'create':
            return LineOfBusinessCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LineOfBusinessUpdateSerializer
        return LineOfBusinessSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Lines of business retrieved successfully.",
                "results": response.data
            })
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                "detail": "Line of business created successfully.",
                "line_of_business": response.data
            }, status=status.HTTP_201_CREATED)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Line of business updated successfully.",
                "line_of_business": response.data
            })
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response({
                "detail": "Line of business deleted successfully."
            }, status=status.HTTP_200_OK)
        return response

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active lines of business"""
        lines_of_business = LineOfBusiness.objects.filter(is_active=True).order_by('batch_model', 'insurance_type', 'line_of_business')
        serializer = LineOfBusinessListSerializer(lines_of_business, many=True)
        return Response({
            "detail": "Active lines of business retrieved successfully.",
            "results": serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_model_and_type(self, request):
        """Get lines of business filtered by batch model and insurance type"""
        batch_model = request.query_params.get('batch_model')
        insurance_type = request.query_params.get('insurance_type')
        
        queryset = LineOfBusiness.objects.filter(is_active=True)
        
        if batch_model:
            queryset = queryset.filter(batch_model=batch_model)
        if insurance_type:
            queryset = queryset.filter(insurance_type=insurance_type)
        
        queryset = queryset.order_by('line_of_business')
        serializer = LineOfBusinessListSerializer(queryset, many=True)
        
        return Response({
            "detail": "Lines of business filtered successfully.",
            "results": serializer.data
        })

class ReportTypeViewSet(viewsets.ModelViewSet):
    queryset = ReportType.objects.all()
    serializer_class = ReportTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch_model', 'is_enabled']
    search_fields = ['report_type']
    ordering_fields = ['batch_model', 'report_type', 'created_on']
    ordering = ['batch_model', 'report_type']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportTypeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReportTypeUpdateSerializer
        return ReportTypeSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "Report types retrieved successfully.",
                "results": response.data
            })
        return response

    @action(detail=False, methods=['get'])
    def by_model(self, request):
        batch_model = request.query_params.get('batch_model')
        if batch_model:
            queryset = ReportType.objects.filter(batch_model=batch_model)
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "detail": "Report types filtered successfully.",
                "results": serializer.data
            })
        return Response({'error': 'batch_model parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def enabled(self, request):
        enabled_reports = ReportType.objects.filter(is_enabled=True)
        serializer = self.get_serializer(enabled_reports, many=True)
        return Response({
            "detail": "Enabled report types retrieved successfully.",
            "results": serializer.data
        })


class IFRSEngineInputViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IFRSEngineInput.objects.all()
    serializer_class = IFRSEngineInputSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['run_id', 'created_by']
    search_fields = ['run_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response({
                "detail": "IFRS Engine Inputs retrieved successfully.",
                "results": response.data
            })
        return response


class IFRSEngineResultViewSet(viewsets.ModelViewSet):
    queryset = IFRSEngineResult.objects.all()
    serializer_class = IFRSEngineResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['run_id', 'model_type', 'report_type', 'year', 'quarter', 'created_by', 'status']
    search_fields = ['run_id', 'model_guid', 'report_type']
    ordering_fields = ['created_at', 'model_type', 'report_type', 'year', 'quarter']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return IFRSEngineResultCreateSerializer
        return IFRSEngineResultSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 12))
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        results = queryset[start:end]
        
        serializer = self.get_serializer(results, many=True)
        
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'count': total_count,
            'next': f"?page={page + 1}&page_size={page_size}" if has_next else None,
            'previous': f"?page={page - 1}&page_size={page_size}" if has_previous else None,
            'results': serializer.data
        })

    def perform_create(self, serializer):
        username = self.request.user.username if self.request.user else 'system'
        serializer.save(created_by=username)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        result = self.get_object()
        return Response({
            'message': 'PDF generation not implemented yet',
            'result_id': result.id,
            'report_type': result.report_type
        })

    @action(detail=True, methods=['get'])
    def download_excel(self, request, pk=None):
        result = self.get_object()
        return Response({
            'message': 'Excel generation not implemented yet',
            'result_id': result.id,
            'report_type': result.report_type
        })

    def destroy(self, request, *args, **kwargs):
        """Delete an IFRS engine result"""
        try:
            result = self.get_object()
            result.delete()
            return Response({
                'detail': 'IFRS engine result deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'error': f'Failed to delete IFRS engine result: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = ReportGenerationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                model = ModelDefinition.objects.get(id=data['model_id'])
            except ModelDefinition.DoesNotExist:
                return Response({'error': 'Model not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            batches = DataUploadBatch.objects.filter(
                id__in=data['batch_ids'],
                batch_status='completed'
            )
            if not batches.exists():
                return Response({'error': 'No completed batches found'}, status=status.HTTP_400_BAD_REQUEST)
            
            line_of_businesses = LineOfBusiness.objects.filter(
                id__in=data['line_of_business_ids'],
                batch_model=data['model_type']
            )
            if not line_of_businesses.exists():
                return Response({'error': 'No line of businesses found'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                ifrs_engine = CalculationConfig.objects.get(id=data['ifrs_engine_id'])
            except CalculationConfig.DoesNotExist:
                return Response({'error': 'IFRS engine not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            report_types = ReportType.objects.filter(
                id__in=data['report_type_ids'],
                batch_model=data['model_type'],
                is_enabled=True
            )
            if not report_types.exists():
                return Response({'error': 'No enabled report types found'}, status=status.HTTP_400_BAD_REQUEST)
            
            import uuid
            import time
            import random
            import string
            
            # Generate 3 random letters
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            # Generate 8 random digits
            numbers = ''.join(random.choices(string.digits, k=8))
            run_id = f"RUN-{letters}{numbers}"
            
            model_definition = {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'config': model.config,
            }
            
            batch_data = []
            for batch in batches:
                batch_info = {
                    'id': batch.id,
                    'batch_id': batch.batch_id,
                    'batch_type': batch.batch_type,
                    'batch_model': batch.batch_model,
                    'insurance_type': batch.insurance_type,
                    'batch_year': batch.batch_year,
                    'batch_quarter': batch.batch_quarter,
                    'uploads': []
                }
                
                uploads = DataUpload.objects.filter(batch=batch)
                for upload in uploads:
                    upload_info = {
                        'id': upload.id,
                        'upload_id': upload.upload_id,
                        'source': upload.source,
                        'insurance_type': upload.insurance_type,
                        'data_type': upload.data_type,
                        'quarter': upload.quarter,
                        'year': upload.year,
                        'validation_status': upload.validation_status,
                        'rows_processed': upload.rows_processed,
                        'error_count': upload.error_count,
                        'validation_errors': upload.validation_errors,
                    }
                    batch_info['uploads'].append(upload_info)
                
                batch_data.append(batch_info)
            
            field_parameters = {
                'model_type': data['model_type'],
                'model_id': data['model_id'],
                'batch_ids': data['batch_ids'],
                'year': data['year'],
                'quarter': data['quarter'],
                'line_of_business_ids': data['line_of_business_ids'],
                'ifrs_engine_id': data['ifrs_engine_id'],
                'report_type_ids': data['report_type_ids'],
                'line_of_businesses': [
                    {
                        'id': lob.id,
                        'line_of_business': lob.line_of_business,
                        'batch_model': lob.batch_model,
                        'insurance_type': lob.insurance_type,
                        'currency': lob.currency.code if lob.currency else None,
                    }
                    for lob in line_of_businesses
                ],
                'report_types': [
                    {
                        'id': rt.id,
                        'report_type': rt.report_type,
                        'batch_model': rt.batch_model,
                        'is_enabled': rt.is_enabled,
                    }
                    for rt in report_types
                ],
            }
            
            results = []
            
            with transaction.atomic():
                engine_input = IFRSEngineInput.objects.create(
                    run_id=run_id,
                    model_definition=model_definition,
                    batch_data=batch_data,
                    field_parameters=field_parameters,
                    created_by=request.user.username if request.user else 'system'
                )
                
                for batch in batches:
                    for report_type in report_types:
                        try:
                            engine_result = self._execute_python_engine(
                                run_id=run_id,
                                model_definition=model_definition,
                                batch_data=batch_data,
                                field_parameters=field_parameters,
                                batch=batch,
                                line_of_businesses=line_of_businesses,
                                report_type=report_type
                            )
                            
                            result = IFRSEngineResult.objects.create(
                                run_id=run_id,
                                model_guid=model.id,
                                model_type=data['model_type'],
                                report_type=report_type.report_type,
                                year=data['year'],
                                quarter=data['quarter'],
                                currency=None,
                                status='Success',
                                result_json=engine_result,
                                created_by=request.user.username if request.user else 'system'
                            )
                            results.append(result)
                            
                        except Exception as e:
                            result = IFRSEngineResult.objects.create(
                                run_id=run_id,
                                model_guid=model.id,
                                model_type=data['model_type'],
                                report_type=report_type.report_type,
                                year=data['year'],
                                quarter=data['quarter'],
                                currency=None,
                                status='Error',
                                result_json={'error': str(e), 'traceback': str(e)},
                                created_by=request.user.username if request.user else 'system'
                            )
                            results.append(result)
            
            result_serializer = IFRSEngineResultSerializer(results, many=True, context={'request': request})
            
            return Response({
                'detail': 'Reports generated successfully',
                'run_id': run_id,
                'results': result_serializer.data,
                'count': len(results)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _execute_python_engine(self, run_id, model_definition, batch_data, field_parameters, batch, line_of_businesses, report_type):
        import json
        import os
        import subprocess
        import tempfile
        
        engine_input = {
            'run_id': run_id,
            'model_definition': model_definition,
            'batch_data': batch_data,
            'field_parameters': field_parameters,
            'current_batch': {
                'id': batch.id,
                'batch_id': batch.batch_id,
                'batch_type': batch.batch_type,
                'batch_model': batch.batch_model,
                'insurance_type': batch.insurance_type,
                'batch_year': batch.batch_year,
                'batch_quarter': batch.batch_quarter,
            },
            'line_of_businesses': [
                {
                    'id': lob.id,
                    'line_of_business': lob.line_of_business,
                    'batch_model': lob.batch_model,
                    'insurance_type': lob.insurance_type,
                    'currency': lob.currency.code if lob.currency else None,
                }
                for lob in line_of_businesses
            ],
            'current_report_type': {
                'id': report_type.id,
                'report_type': report_type.report_type,
                'batch_model': report_type.batch_model,
                'is_enabled': report_type.is_enabled,
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(engine_input, f, indent=2)
            input_file = f.name
        
        try:
            ifrs_engine_id = field_parameters.get('ifrs_engine_id')
            if not ifrs_engine_id:
                return {
                    'error': 'IFRS engine ID not provided in field parameters',
                    'run_id': run_id
                }
            
            try:
                ifrs_engine = CalculationConfig.objects.get(id=ifrs_engine_id)
            except CalculationConfig.DoesNotExist:
                return {
                    'error': f'IFRS engine with ID {ifrs_engine_id} not found',
                    'run_id': run_id
                }
            
            if not ifrs_engine.script:
                return {
                    'error': f'No script uploaded for engine {ifrs_engine.engine_type}',
                    'run_id': run_id
                }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_content = ifrs_engine.script.read().decode('utf-8')
                script_file.write(script_content)
                script_file.flush()
                script_path = script_file.name
            
            try:
                result = subprocess.run(
                    ['python', script_path, input_file],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    try:
                        output_data = json.loads(result.stdout)
                        return output_data
                    except json.JSONDecodeError:
                        return {
                            'message': 'Engine executed successfully but returned invalid JSON',
                            'stdout': result.stdout,
                            'stderr': result.stderr,
                            'run_id': run_id
                        }
                else:
                    return {
                        'error': 'Engine execution failed',
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'return_code': result.returncode,
                        'run_id': run_id
                    }
                    
            finally:
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                'error': 'Engine execution timed out',
                'run_id': run_id
            }
        except Exception as e:
            return {
                'error': f'Engine execution error: {str(e)}',
                'run_id': run_id
            }
        finally:
            try:
                os.unlink(input_file)
            except:
                pass