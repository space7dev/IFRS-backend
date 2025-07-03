from django.contrib import admin
from .models import ModelDefinition, ModelDefinitionHistory


@admin.register(ModelDefinition)
class ModelDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'get_product_type', 'get_measurement_model', 'get_status', 'created_by', 'modified_on']
    list_filter = ['created_on']
    search_fields = ['name']
    readonly_fields = ['created_on', 'modified_on', 'locked_at', 'get_product_type', 'get_measurement_model', 'get_status', 'get_description']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'version']
        }),
        ('Configuration', {
            'fields': ['config'],
            'description': 'All model configuration including product type, measurement model, status, and description is stored in this JSON field.'
        }),
        ('Derived Fields (Read-only)', {
            'fields': ['get_product_type', 'get_measurement_model', 'get_status', 'get_description'],
            'classes': ['collapse'],
            'description': 'These fields are automatically derived from the config JSON.'
        }),
        ('Relationships', {
            'fields': ['cloned_from']
        }),
        ('User Tracking', {
            'fields': ['created_by', 'last_modified_by']
        }),
        ('Locking', {
            'fields': ['locked_by', 'locked_at'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def get_product_type(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('productType', 'Not specified')
        return 'Not specified'
    get_product_type.short_description = 'Product Type'
    
    def get_measurement_model(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('measurementModel', 'GMM')
        return 'GMM'
    get_measurement_model.short_description = 'Measurement Model'
    
    def get_status(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('status', 'draft')
        return 'draft'
    get_status.short_description = 'Status'
    
    def get_description(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('description', '')
        return ''
    get_description.short_description = 'Description'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModelDefinitionHistory)
class ModelDefinitionHistoryAdmin(admin.ModelAdmin):
    list_display = ['model', 'version', 'get_product_type', 'get_measurement_model', 'get_status', 'modified_by', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['name', 'model__name']
    readonly_fields = ['saved_at', 'get_product_type', 'get_measurement_model', 'get_status', 'get_description']
    
    def get_product_type(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('productType', 'Not specified')
        return 'Not specified'
    get_product_type.short_description = 'Product Type'
    
    def get_measurement_model(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('measurementModel', 'GMM')
        return 'GMM'
    get_measurement_model.short_description = 'Measurement Model'
    
    def get_status(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('status', 'draft')
        return 'draft'
    get_status.short_description = 'Status'
    
    def get_description(self, obj):
        if obj.config and 'generalInfo' in obj.config:
            return obj.config['generalInfo'].get('description', '')
        return ''
    get_description.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
