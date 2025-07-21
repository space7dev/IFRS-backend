from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, Http404

from model_definitions.models import ModelDefinition, ModelDefinitionHistory, DataUploadBatch, DataUpload, DataUploadTemplate, APIUploadLog, DataBatchStatus, DocumentTypeConfig
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
    DocumentTypeConfigUpdateSerializer
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