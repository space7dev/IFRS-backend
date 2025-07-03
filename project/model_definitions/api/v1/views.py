from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from django.utils import timezone
from django.db import transaction

from model_definitions.models import ModelDefinition, ModelDefinitionHistory
from .serializers import (
    ModelDefinitionListSerializer,
    ModelDefinitionDetailSerializer,
    ModelDefinitionCreateSerializer,
    ModelDefinitionUpdateSerializer,
    ModelDefinitionHistorySerializer
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