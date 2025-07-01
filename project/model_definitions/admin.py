from django.contrib import admin
from .models import ModelDefinition, ModelDefinitionHistory


@admin.register(ModelDefinition)
class ModelDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'get_product_type', 'get_measurement_model', 'status', 'created_by', 'modified_on']
    list_filter = ['status', 'created_on']
    search_fields = ['name', 'description']
    readonly_fields = ['created_on', 'modified_on', 'locked_at', 'get_product_type', 'get_measurement_model']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'version', 'status']
        }),
        ('Configuration', {
            'fields': ['config'],
            'description': 'All model configuration including product type and measurement model is stored in this JSON field.'
        }),
        ('Derived Fields (Read-only)', {
            'fields': ['get_product_type', 'get_measurement_model'],
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
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModelDefinitionHistory)
class ModelDefinitionHistoryAdmin(admin.ModelAdmin):
    list_display = ['model', 'version', 'get_product_type', 'get_measurement_model', 'modified_by', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['name', 'model__name']
    readonly_fields = ['saved_at', 'get_product_type', 'get_measurement_model']
    
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
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
