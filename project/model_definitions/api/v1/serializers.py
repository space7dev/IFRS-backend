from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.utils import timezone

from model_definitions.models import ModelDefinition, ModelDefinitionHistory

User = get_user_model()


class ModelDefinitionListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    last_modified_by_name = serializers.CharField(source='last_modified_by.get_full_name', read_only=True)
    locked_by_name = serializers.CharField(source='locked_by.get_full_name', read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ModelDefinition
        fields = [
            'id',
            'name',
            'description',
            'version',
            'config',
            'status',
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


class ModelDefinitionDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    last_modified_by_name = serializers.CharField(source='last_modified_by.get_full_name', read_only=True)
    locked_by_name = serializers.CharField(source='locked_by.get_full_name', read_only=True)
    cloned_from_name = serializers.CharField(source='cloned_from.name', read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ModelDefinition  
        fields = [
            'id',
            'name',
            'description',
            'version',
            'config',
            'status',
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
            'description',
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
            description=instance.description,
            version=instance.version,
            config=instance.config,
            modified_by=request.user
        )
        
        if 'config' in validated_data:
            version_parts = instance.version.replace('v', '').split('.')
            if len(version_parts) >= 2:
                minor = int(version_parts[1]) + 1
                instance.version = f"v{version_parts[0]}.{minor}"
        
        instance.last_modified_by = request.user
        
        return super().update(instance, validated_data)


class ModelDefinitionHistorySerializer(serializers.ModelSerializer):
    modified_by_name = serializers.CharField(source='modified_by.get_full_name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)

    class Meta:
        model = ModelDefinitionHistory
        fields = [
            'id',
            'model',
            'model_name',
            'name',
            'description',
            'version',
            'config',
            'saved_at',
            'modified_by',
            'modified_by_name'
        ]
        read_only_fields = (
            'id', 'model', 'model_name', 'name', 'description', 'version',
            'config', 'saved_at', 'modified_by', 'modified_by_name'
        ) 