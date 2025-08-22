import os
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.contrib.auth import get_user_model
from django.utils import timezone

from model_definitions.models import (
    ModelDefinition, 
    ModelDefinitionHistory, 
    DataUploadBatch, 
    DataBatchStatus, 
    DataUploadTemplate, 
    DataUpload, 
    APIUploadLog,
    DocumentTypeConfig,
    CalculationConfig,
    ConversionConfig,
    Currency,
    LineOfBusiness,
    ReportType,
    IFRSEngineResult,
    IFRSEngineInput
)

User = get_user_model()


class ModelDefinitionListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    last_modified_by_name = serializers.SerializerMethodField()
    locked_by_name = serializers.SerializerMethodField()
    is_locked = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ModelDefinition
        fields = [
            'id',
            'name',
            'version',
            'config',
            'created_by',
            'created_by_name',
            'last_modified_by',
            'last_modified_by_name',
            'locked_by',
            'locked_by_name',
            'locked_at',
            'is_locked',
            'can_edit',
            'created_on',
            'modified_on',
        ]
        read_only_fields = [
            'id', 'created_by', 'last_modified_by', 'locked_by', 
            'locked_at', 'created_on', 'modified_on'
        ]

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_edit(request.user)
        return False

    def get_created_by_name(self, obj):
        if obj.created_by:
            full_name = obj.created_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.created_by.username}"
        return "Unknown"

    def get_last_modified_by_name(self, obj):
        if obj.last_modified_by:
            full_name = obj.last_modified_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.last_modified_by.username}"
        return "Unknown"

    def get_locked_by_name(self, obj):
        if obj.locked_by:
            full_name = obj.locked_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.locked_by.username}"
        return None


class ModelDefinitionDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    last_modified_by_name = serializers.SerializerMethodField()
    locked_by_name = serializers.SerializerMethodField()
    cloned_from_name = serializers.CharField(source='cloned_from.name', read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ModelDefinition  
        fields = [
            'id',
            'name',
            'version',
            'config',
            'created_by',
            'created_by_name',
            'last_modified_by',
            'last_modified_by_name',
            'cloned_from',
            'cloned_from_name',
            'locked_by',
            'locked_by_name',
            'locked_at',
            'is_locked',
            'can_edit',
            'created_on',
            'modified_on',
        ]
        read_only_fields = [
            'id', 'created_by', 'last_modified_by', 'locked_by', 
            'locked_at', 'created_on', 'modified_on'
        ]

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_edit(request.user)
        return False

    def get_created_by_name(self, obj):
        if obj.created_by:
            full_name = obj.created_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.created_by.username}"
        return "Unknown"

    def get_last_modified_by_name(self, obj):
        if obj.last_modified_by:
            full_name = obj.last_modified_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.last_modified_by.username}"
        return "Unknown"

    def get_locked_by_name(self, obj):
        if obj.locked_by:
            full_name = obj.locked_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.locked_by.username}"
        return None


class ModelDefinitionCreateSerializer(serializers.ModelSerializer):
    cloned_from = serializers.PrimaryKeyRelatedField(
        queryset=ModelDefinition.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = ModelDefinition
        fields = [
            'name',
            'config',
            'cloned_from'
        ]

    def validate_name(self, value):
        if ModelDefinition.objects.filter(name=value).exists():
            raise ValidationError("A model with this name already exists.")
        return value

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Config must be a valid JSON object.")
        
        general_info = value.get('general_info', {})
        frontend_general_info = value.get('generalInfo', {})
        
        if general_info:
            product_type = general_info.get('product_type')
            measurement_model = general_info.get('measurement_model')
        else:
            product_type = frontend_general_info.get('productType')
            measurement_model = frontend_general_info.get('measurementModel')
        
        if not product_type:
            raise ValidationError("Product type is required in config.general_info.product_type or config.generalInfo.productType")
        if not measurement_model:
            raise ValidationError("Measurement model is required in config.general_info.measurement_model or config.generalInfo.measurementModel")
            
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        cloned_from = validated_data.pop('cloned_from', None)
        
        validated_data['created_by'] = request.user
        validated_data['last_modified_by'] = request.user
        
        if cloned_from:
            validated_data['config'] = cloned_from.config.copy()
            validated_data['cloned_from'] = cloned_from
        
        if 'config' not in validated_data:
            validated_data['config'] = {}
        
        config = validated_data['config']
        
        if 'generalInfo' in config and 'general_info' not in config:
            general_info = config['generalInfo']
            config['general_info'] = {
                'product_type': general_info.get('productType', ''),
                'measurement_model': general_info.get('measurementModel', ''),
                **{k: v for k, v in general_info.items() if k not in ['productType', 'measurementModel']}
            }
        elif 'general_info' not in config:
            config['general_info'] = {}
        
        return super().create(validated_data)


class ModelDefinitionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelDefinition
        fields = [
            'config'
        ]

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Config must be a valid JSON object.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if not self.instance.can_edit(request.user):
            raise ValidationError("You cannot edit this model. It may be locked by another user.")
        return attrs

    def update(self, instance, validated_data):
        request = self.context.get('request')
        
        ModelDefinitionHistory.objects.create(
            model=instance,
            name=instance.name,
            version=instance.version,
            config=instance.config,
            modified_by=request.user
        )
        
        if 'config' in validated_data:
            config = validated_data['config']
            general_info = config.get('generalInfo', {})
            
            if 'modelName' in general_info:
                instance.name = general_info['modelName']
            
            version_parts = instance.version.replace('v', '').split('.')
            if len(version_parts) >= 2:
                minor = int(version_parts[1]) + 1
                instance.version = f"v{version_parts[0]}.{minor}"
        
        instance.last_modified_by = request.user
        
        return super().update(instance, validated_data)


class ModelDefinitionHistorySerializer(serializers.ModelSerializer):
    modified_by_name = serializers.SerializerMethodField()
    model_name = serializers.CharField(source='model.name', read_only=True)

    class Meta:
        model = ModelDefinitionHistory
        fields = [
            'id',
            'model',
            'model_name',
            'name',
            'version',
            'config',
            'saved_at',
            'modified_by',
            'modified_by_name'
        ]
        read_only_fields = (
            'id', 'model', 'model_name', 'name', 'version',
            'config', 'saved_at', 'modified_by', 'modified_by_name'
        )

    def get_modified_by_name(self, obj):
        if obj.modified_by:
            full_name = obj.modified_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.modified_by.username}"
        return "Unknown"


class DataUploadBatchSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    last_modified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DataUploadBatch
        fields = [
            'id',
            'batch_id',
            'name',
            'batch_type',
            'batch_model',
            'insurance_type',
            'batch_year',
            'batch_quarter',
            'created_by',
            'created_by_name',
            'last_modified_by',
            'last_modified_by_name',
            'batch_status',
            'upload_count',
            'created_on',
            'modified_on',
        ]
        read_only_fields = [
            'id', 'batch_id', 'created_by', 'last_modified_by', 'upload_count', 'created_on', 'modified_on'
        ]
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            full_name = obj.created_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.created_by.username}"
        return "Unknown"
    
    def get_last_modified_by_name(self, obj):
        if obj.last_modified_by:
            full_name = obj.last_modified_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.last_modified_by.username}"
        return "Unknown"
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['last_modified_by'] = request.user
        return super().create(validated_data)


class DataUploadSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    batch_id = serializers.CharField(source='batch.batch_id', read_only=True)
    file_upload = serializers.FileField(required=False)
    
    class Meta:
        model = DataUpload
        fields = [
            'id',
            'upload_id',
            'batch',
            'batch_id',
            'source',
            'insurance_type',
            'data_type',
            'quarter',
            'year',
            'uploaded_by',
            'uploaded_by_name',
            'file_upload',
            'original_filename',
            'file_size',
            'validation_status',
            'rows_processed',
            'error_count',
            'validation_errors',
            'api_payload',
            'created_on',
            'modified_on',
        ]
        read_only_fields = [
            'id', 'upload_id', 'uploaded_by', 'original_filename', 'file_size',
            'rows_processed', 'error_count', 'validation_errors', 'created_on', 'modified_on'
        ]
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            full_name = obj.uploaded_by.get_full_name().strip()
            if full_name:
                return full_name
            return f"{obj.uploaded_by.username}"
        return "Unknown"
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['uploaded_by'] = request.user
        return super().create(validated_data)


class DataUploadTemplateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DataUploadTemplate
        fields = [
            'id',
            'name',
            'data_type',
            'template_file',
            'version',
            'is_active',
            'is_standard_template',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class APIUploadLogSerializer(serializers.ModelSerializer):
    data_upload_id = serializers.CharField(source='data_upload.upload_id', read_only=True)
    
    class Meta:
        model = APIUploadLog
        fields = [
            'id',
            'reporting_date',
            'upload_date',
            'sum_of_premiums',
            'sum_of_paid_claims',
            'sum_of_commissions',
            'status',
            'data_upload',
            'data_upload_id',
            'api_payload',
            'error_message',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'upload_date', 'created_on', 'modified_on']


class DataBatchStatusSerializer(serializers.ModelSerializer):
    batch_name = serializers.SerializerMethodField()
    batch_type_display = serializers.SerializerMethodField()
    batch_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DataBatchStatus
        fields = [
            'id',
            'batch_id',
            'document_type',
            'upload_status',
            'batch_name',
            'batch_type_display',
            'batch_status_display',
        ]
        read_only_fields = ['id', 'batch_name', 'batch_type_display', 'batch_status_display']
    
    def get_batch_name(self, obj):
        batch = obj.batch
        return batch.name if batch else 'N/A'
    
    def get_batch_type_display(self, obj):
        batch = obj.batch
        return batch.get_batch_type_display() if batch else 'N/A'
    
    def get_batch_status_display(self, obj):
        batch = obj.batch
        return batch.get_batch_status_display() if batch else 'N/A'

class FileUploadSerializer(serializers.ModelSerializer):
    file_upload = serializers.FileField()
    
    class Meta:
        model = DataUpload
        fields = [
            'batch',
            'source',
            'insurance_type',
            'data_type',
            'quarter',
            'year',
            'file_upload',
        ]
    
    def validate_file_upload(self, value):
        if value.size > 50 * 1024 * 1024:  # 50MB limit
            raise ValidationError("File size cannot exceed 50MB")
        
        if not value.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Only Excel files (.xlsx, .xls) are allowed")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['uploaded_by'] = request.user
        return super().create(validated_data)


class BulkUploadSerializer(serializers.Serializer):
    batch_id = serializers.CharField(required=True)
    uploads = serializers.JSONField(
        help_text="List of upload objects with fields: source, insurance_type, data_type, quarter, year"
    )
    
    def validate_batch_id(self, value):
        try:
            batch = DataUploadBatch.objects.get(batch_id=value)
            if batch.batch_status != 'draft':
                raise ValidationError("Cannot add uploads to a batch that is not in draft status")
        except DataUploadBatch.DoesNotExist:
            raise ValidationError("Batch not found")
        return value
    
    def validate_uploads(self, value):
        if not isinstance(value, list):
            raise ValidationError("Uploads must be a list")
        
        if len(value) < 1 or len(value) > 10:
            raise ValidationError("Uploads list must contain between 1 and 10 items")
        
        required_fields = ['source', 'insurance_type', 'data_type', 'quarter', 'year']
        
        for i, upload in enumerate(value):
            if not isinstance(upload, dict):
                raise ValidationError(f"Upload {i+1} must be an object")
            
            for field in required_fields:
                if field not in upload:
                    raise ValidationError(f"Upload {i+1} is missing required field: {field}")
        
        return value
    
    def create(self, validated_data):
        batch_id = validated_data['batch_id']
        uploads_data = validated_data['uploads']
        
        batch = DataUploadBatch.objects.get(batch_id=batch_id)
        request = self.context.get('request')
        
        created_uploads = []
        for upload_data in uploads_data:
            file_upload = upload_data.get('file_upload')
            if file_upload:
                if file_upload.size > 50 * 1024 * 1024:  # 50MB limit
                    raise ValidationError("File size cannot exceed 50MB")
                if not file_upload.name.endswith(('.xlsx', '.xls')):
                    raise ValidationError("Only Excel files (.xlsx, .xls) are allowed")
            
            upload_data['batch'] = batch
            upload_data['uploaded_by'] = request.user
            upload = DataUpload.objects.create(**upload_data)
            created_uploads.append(upload)
        
        return created_uploads 


class DocumentTypeConfigSerializer(serializers.ModelSerializer):
    template = serializers.FileField(required=True)
    
    class Meta:
        model = DocumentTypeConfig
        fields = [
            'id',
            'batch_type',
            'batch_model', 
            'insurance_type',
            'document_type',
            'required',
            'template',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']
    
    def validate_template(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("Template file size cannot exceed 10MB")
        
        if not value.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Only Excel files (.xlsx, .xls) are allowed")
        
        return value


class DocumentTypeConfigListSerializer(serializers.ModelSerializer):
    template_name = serializers.SerializerMethodField()
    template_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentTypeConfig
        fields = [
            'id',
            'batch_type',
            'batch_model',
            'insurance_type', 
            'document_type',
            'required',
            'template_name',
            'template_url',
            'created_on',
            'modified_on',
        ]
    
    def get_template_name(self, obj):
        if obj.template:
            return obj.template.name.split('/')[-1]
        return None
    
    def get_template_url(self, obj):
        if obj.template:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.template.url)
        return None


class DocumentTypeConfigCreateSerializer(serializers.ModelSerializer):
    template = serializers.FileField(required=False)
    
    class Meta:
        model = DocumentTypeConfig
        fields = [
            'batch_type',
            'batch_model',
            'insurance_type',
            'document_type',
            'required',
            'template',
        ]
    
    def validate_template(self, value):
        if value and value.size > 10 * 1024 * 1024:
            raise ValidationError("Template file size cannot exceed 10MB")
        
        if value and not value.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Only Excel files (.xlsx, .xls) are allowed")
        
        return value
    
    def validate(self, data):
        existing = DocumentTypeConfig.objects.filter(
            batch_type=data['batch_type'],
            batch_model=data['batch_model'],
            insurance_type=data['insurance_type'],
            document_type=data['document_type']
        ).exists()
        
        if existing:
            raise ValidationError("This document type configuration already exists.")
        
        return data


class DocumentTypeConfigUpdateSerializer(serializers.ModelSerializer):
    template = serializers.FileField(required=False)
    
    class Meta:
        model = DocumentTypeConfig
        fields = [
            'batch_type',
            'batch_model',
            'insurance_type',
            'document_type',
            'required',
            'template',
        ]
    
    def validate_template(self, value):
        if value and value.size > 10 * 1024 * 1024:
            raise ValidationError("Template file size cannot exceed 10MB")
        
        if value and not value.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Only Excel files (.xlsx, .xls) are allowed")
        
        return value
    
    def validate(self, data):
        instance = self.instance
        
        existing = DocumentTypeConfig.objects.filter(
            batch_type=data.get('batch_type', instance.batch_type),
            batch_model=data.get('batch_model', instance.batch_model),
            insurance_type=data.get('insurance_type', instance.insurance_type),
            document_type=data.get('document_type', instance.document_type)
        ).exclude(pk=instance.pk).exists()
        
        if existing:
            raise ValidationError("This document type configuration already exists.")
        
        return data


# Calculation Config Serializers
class CalculationConfigSerializer(serializers.ModelSerializer):
    script = serializers.FileField(required=True)
    
    class Meta:
        model = CalculationConfig
        fields = [
            'id',
            'batch_type',
            'batch_model', 
            'insurance_type',
            'engine_type',
            'required',
            'script',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']
    
    def validate_script(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("Script file size cannot exceed 10MB")
        
        if not value.name.endswith('.py'):
            raise ValidationError("Only Python files (.py) are allowed")
        
        return value


class CalculationConfigListSerializer(serializers.ModelSerializer):
    script_name = serializers.SerializerMethodField()
    script_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CalculationConfig
        fields = [
            'id',
            'batch_type',
            'batch_model',
            'insurance_type', 
            'engine_type',
            'required',
            'script_name',
            'script_url',
            'created_on',
            'modified_on',
        ]
    
    def get_script_name(self, obj):
        if obj.script:
            return obj.script.name.split('/')[-1]
        return None
    
    def get_script_url(self, obj):
        if obj.script:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.script.url)
        return None


class CalculationConfigCreateSerializer(serializers.ModelSerializer):
    script = serializers.FileField(required=True)
    
    class Meta:
        model = CalculationConfig
        fields = [
            'batch_type',
            'batch_model',
            'insurance_type',
            'engine_type',
            'required',
            'script',
        ]
    
    def validate_script(self, value):
        if value and value.size > 10 * 1024 * 1024:
            raise ValidationError("Script file size cannot exceed 10MB")
        
        if value and not value.name.endswith('.py'):
            raise ValidationError("Only Python files (.py) are allowed")
        
        return value
    
    def validate(self, data):
        existing = CalculationConfig.objects.filter(
            batch_type=data['batch_type'],
            batch_model=data['batch_model'],
            insurance_type=data['insurance_type'],
            engine_type=data['engine_type']
        ).exists()
        
        if existing:
            raise ValidationError("This calculation configuration already exists.")
        
        return data


class CalculationConfigUpdateSerializer(serializers.ModelSerializer):
    script = serializers.FileField(required=False)
    
    class Meta:
        model = CalculationConfig
        fields = [
            'batch_type',
            'batch_model',
            'insurance_type',
            'engine_type',
            'required',
            'script',
        ]
    
    def validate_script(self, value):
        if value and value.size > 10 * 1024 * 1024:
            raise ValidationError("Script file size cannot exceed 10MB")
        
        if value and not value.name.endswith('.py'):
            raise ValidationError("Only Python files (.py) are allowed")
        
        return value
    
    def validate(self, data):
        instance = self.instance
        
        existing = CalculationConfig.objects.filter(
            batch_type=data.get('batch_type', instance.batch_type),
            batch_model=data.get('batch_model', instance.batch_model),
            insurance_type=data.get('insurance_type', instance.insurance_type),
            engine_type=data.get('engine_type', instance.engine_type)
        ).exclude(pk=instance.pk).exists()
        
        if existing:
            raise ValidationError("This calculation configuration already exists.")
        
        return data


# Conversion Config Serializers
class ConversionConfigSerializer(serializers.ModelSerializer):
    script = serializers.FileField(required=True)
    
    class Meta:
        model = ConversionConfig
        fields = [
            'id',
            'batch_type',
            'batch_model', 
            'insurance_type',
            'engine_type',
            'required',
            'script',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']
    
    def validate_script(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("Script file size cannot exceed 10MB")
        
        if not value.name.endswith('.py'):
            raise ValidationError("Only Python files (.py) are allowed")
        
        return value


class ConversionConfigListSerializer(serializers.ModelSerializer):
    script_name = serializers.SerializerMethodField()
    script_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ConversionConfig
        fields = [
            'id',
            'batch_type',
            'batch_model',
            'insurance_type', 
            'engine_type',
            'required',
            'script_name',
            'script_url',
            'created_on',
            'modified_on',
        ]
    
    def get_script_name(self, obj):
        if obj.script:
            return obj.script.name.split('/')[-1]
        return None
    
    def get_script_url(self, obj):
        if obj.script:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.script.url)
        return None


class ConversionConfigCreateSerializer(serializers.ModelSerializer):
    script = serializers.FileField(required=True)
    
    class Meta:
        model = ConversionConfig
        fields = [
            'batch_type',
            'batch_model',
            'insurance_type',
            'engine_type',
            'required',
            'script',
        ]
    
    def validate_script(self, value):
        if value and value.size > 10 * 1024 * 1024:
            raise ValidationError("Script file size cannot exceed 10MB")
        
        if value and not value.name.endswith('.py'):
            raise ValidationError("Only Python files (.py) are allowed")
        
        return value
    
    def validate(self, data):
        existing = ConversionConfig.objects.filter(
            batch_type=data['batch_type'],
            batch_model=data['batch_model'],
            insurance_type=data['insurance_type'],
            engine_type=data['engine_type']
        ).exists()
        
        if existing:
            raise ValidationError("This conversion configuration already exists.")
        
        return data


class ConversionConfigUpdateSerializer(serializers.ModelSerializer):
    script = serializers.FileField(required=False)
    
    class Meta:
        model = ConversionConfig
        fields = [
            'id',
            'batch_type',
            'batch_model', 
            'insurance_type',
            'engine_type',
            'required',
            'script',
        ]
        read_only_fields = ['id']
    
    def validate_script(self, value):
        if value:
            allowed_extensions = ['.py']
            file_extension = os.path.splitext(value.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise ValidationError(f"Only Python files (.py) are allowed. Got: {file_extension}")
            
            if value.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be less than 5MB")
        
        return value
    
    def validate(self, data):
        batch_type = data.get('batch_type')
        batch_model = data.get('batch_model')
        insurance_type = data.get('insurance_type')
        engine_type = data.get('engine_type')
        
        if all([batch_type, batch_model, insurance_type, engine_type]):
            existing = ConversionConfig.objects.filter(
                batch_type=batch_type,
                batch_model=batch_model,
                insurance_type=insurance_type,
                engine_type=engine_type
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing.exists():
                raise ValidationError(
                    f"A conversion configuration already exists for {batch_type} - {batch_model} - {insurance_type} - {engine_type}"
                )
        
        return data


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            'id',
            'code',
            'name',
            'is_active',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class CurrencyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            'id',
            'code',
            'name',
            'is_active',
        ]
        read_only_fields = ['id']


class CurrencyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            'code',
            'name',
            'is_active',
        ]
    
    def validate_code(self, value):
        if not value.isalpha() or len(value) != 3:
            raise ValidationError("Currency code must be exactly 3 alphabetic characters")
        return value.upper()


class CurrencyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            'code',
            'name',
            'is_active',
        ]
    
    def validate_code(self, value):
        if not value.isalpha() or len(value) != 3:
            raise ValidationError("Currency code must be exactly 3 alphabetic characters")
        return value.upper()


class LineOfBusinessSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    
    class Meta:
        model = LineOfBusiness
        fields = [
            'id',
            'batch_model',
            'insurance_type',
            'line_of_business',
            'currency',
            'currency_code',
            'currency_name',
            'is_active',
            'created_on',
            'modified_on',
        ]
        read_only_fields = ['id', 'created_on', 'modified_on']


class LineOfBusinessListSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    
    class Meta:
        model = LineOfBusiness
        fields = [
            'id',
            'batch_model',
            'insurance_type',
            'line_of_business',
            'currency',
            'currency_code',
            'currency_name',
            'is_active',
        ]
        read_only_fields = ['id']


class LineOfBusinessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineOfBusiness
        fields = [
            'batch_model',
            'insurance_type',
            'line_of_business',
            'currency',
            'is_active',
        ]
    
    def validate(self, data):
        batch_model = data.get('batch_model')
        insurance_type = data.get('insurance_type')
        line_of_business = data.get('line_of_business')
        
        if all([batch_model, insurance_type, line_of_business]):
            existing = LineOfBusiness.objects.filter(
                batch_model=batch_model,
                insurance_type=insurance_type,
                line_of_business=line_of_business
            )
            
            if existing.exists():
                raise ValidationError(
                    f"A line of business already exists for {batch_model} - {insurance_type} - {line_of_business}"
                )
        
        return data


class LineOfBusinessUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineOfBusiness
        fields = [
            'batch_model',
            'insurance_type',
            'line_of_business',
            'currency',
            'is_active',
        ]
    
    def validate(self, data):
        batch_model = data.get('batch_model')
        insurance_type = data.get('insurance_type')
        line_of_business = data.get('line_of_business')
        
        if all([batch_model, insurance_type, line_of_business]):
            existing = LineOfBusiness.objects.filter(
                batch_model=batch_model,
                insurance_type=insurance_type,
                line_of_business=line_of_business
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing.exists():
                raise ValidationError(
                    f"A line of business already exists for {batch_model} - {insurance_type} - {line_of_business}"
                )
        
        return data 

class ReportTypeSerializer(serializers.ModelSerializer):
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    batch_model_display = serializers.CharField(source='get_batch_model_display', read_only=True)

    class Meta:
        model = ReportType
        fields = '__all__'


class ReportTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportType
        fields = ['batch_model', 'report_type', 'is_enabled', 'notes']


class ReportTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportType
        fields = ['batch_model', 'report_type', 'is_enabled', 'notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.required = False


class IFRSEngineInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = IFRSEngineInput
        fields = [
            'id',
            'run_id',
            'model_definition',
            'batch_data',
            'field_parameters',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class IFRSEngineResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IFRSEngineResult
        fields = [
            'id',
            'run_id',
            'model_guid',
            'model_type',
            'report_type',
            'year',
            'quarter',
            'currency',
            'status',
            'result_json',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class IFRSEngineResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IFRSEngineResult
        fields = [
            'run_id',
            'model_guid',
            'model_type',
            'report_type',
            'year',
            'quarter',
            'currency',
            'status',
            'result_json',
            'created_by'
        ]


class ReportGenerationSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(choices=['PAA', 'GMM', 'VFA'])
    model_id = serializers.IntegerField()
    batch_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    year = serializers.IntegerField()
    quarter = serializers.ChoiceField(choices=['Q1', 'Q2', 'Q3', 'Q4'])
    line_of_business_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    conversion_engine_id = serializers.IntegerField()
    ifrs_engine_id = serializers.IntegerField()
    report_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    ) 