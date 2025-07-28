from django.contrib import admin
from .models import ModelDefinition, ModelDefinitionHistory, DataUploadBatch, DataUpload, DataUploadTemplate, APIUploadLog, DataBatchStatus, DocumentTypeConfig, CalculationConfig, ConversionConfig


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


@admin.register(DataUploadBatch)
class DataUploadBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_id', 'name', 'batch_type', 'batch_model', 'insurance_type', 'batch_year', 'batch_quarter', 'batch_status', 'upload_count', 'created_by', 'created_on']
    list_filter = ['batch_status', 'batch_type', 'batch_model', 'insurance_type', 'batch_year', 'batch_quarter', 'created_on']
    search_fields = ['batch_id', 'name', 'created_by__username']
    readonly_fields = ['batch_id', 'upload_count', 'created_on', 'modified_on']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['batch_id', 'name', 'batch_type', 'batch_status']
        }),
        ('IFRS Configuration', {
            'fields': ['batch_model', 'insurance_type', 'batch_year', 'batch_quarter']
        }),
        ('Statistics', {
            'fields': ['upload_count'],
            'classes': ['collapse']
        }),
        ('User Tracking', {
            'fields': ['created_by', 'last_modified_by']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DataUpload)
class DataUploadAdmin(admin.ModelAdmin):
    list_display = ['upload_id', 'source', 'data_type', 'insurance_type', 'quarter', 'year', 'validation_status', 'uploaded_by', 'created_on']
    list_filter = ['source', 'data_type', 'insurance_type', 'quarter', 'year', 'validation_status', 'created_on']
    search_fields = ['upload_id', 'batch__batch_id', 'uploaded_by__username', 'original_filename']
    readonly_fields = ['upload_id', 'original_filename', 'file_size', 'rows_processed', 'error_count', 'created_on', 'modified_on']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['upload_id', 'batch', 'source']
        }),
        ('Metadata', {
            'fields': ['insurance_type', 'data_type', 'quarter', 'year']
        }),
        ('File Information', {
            'fields': ['file_upload', 'original_filename', 'file_size', 'api_payload']
        }),
        ('Validation', {
            'fields': ['validation_status', 'rows_processed', 'error_count', 'validation_errors']
        }),
        ('User Tracking', {
            'fields': ['uploaded_by']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DataUploadTemplate)
class DataUploadTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'data_type', 'version', 'is_active', 'is_standard_template', 'created_on']
    list_filter = ['data_type', 'is_active', 'is_standard_template', 'created_on']
    search_fields = ['name', 'data_type']
    readonly_fields = ['created_on', 'modified_on']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'data_type', 'version']
        }),
        ('Template File', {
            'fields': ['template_file']
        }),
        ('Configuration', {
            'fields': ['is_active', 'is_standard_template']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]


@admin.register(APIUploadLog)
class APIUploadLogAdmin(admin.ModelAdmin):
    list_display = ['reporting_date', 'upload_date', 'sum_of_premiums', 'sum_of_paid_claims', 'sum_of_commissions', 'status']
    list_filter = ['status', 'reporting_date', 'upload_date']
    search_fields = ['data_upload__upload_id']
    readonly_fields = ['upload_date', 'created_on', 'modified_on']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['reporting_date', 'upload_date', 'status']
        }),
        ('Financial Data', {
            'fields': ['sum_of_premiums', 'sum_of_paid_claims', 'sum_of_commissions']
        }),
        ('Related Upload', {
            'fields': ['data_upload']
        }),
        ('API Data', {
            'fields': ['api_payload', 'error_message']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DataBatchStatus)
class DataBatchStatusAdmin(admin.ModelAdmin):
    list_display = ['batch_id', 'document_type', 'upload_status', 'get_batch_name', 'get_batch_type']
    list_filter = ['document_type', 'upload_status']
    search_fields = ['batch_id', 'document_type']
    readonly_fields = ['get_batch_name', 'get_batch_type', 'get_batch_status']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['batch_id', 'document_type', 'upload_status']
        }),
        ('Related Batch Info (Read-only)', {
            'fields': ['get_batch_name', 'get_batch_type', 'get_batch_status'],
            'classes': ['collapse'],
            'description': 'Information from the related batch record'
        })
    ]
    
    def get_batch_name(self, obj):
        batch = obj.batch
        return batch.name if batch else 'N/A'
    get_batch_name.short_description = 'Batch Name'
    
    def get_batch_type(self, obj):
        batch = obj.batch
        return batch.get_batch_type_display() if batch else 'N/A'
    get_batch_type.short_description = 'Batch Type'
    
    def get_batch_status(self, obj):
        batch = obj.batch
        return batch.get_batch_status_display() if batch else 'N/A'
    get_batch_status.short_description = 'Batch Status'


@admin.register(DocumentTypeConfig)
class DocumentTypeConfigAdmin(admin.ModelAdmin):
    list_display = ['batch_type', 'batch_model', 'insurance_type', 'document_type', 'required', 'template', 'created_on']
    list_filter = ['batch_type', 'batch_model', 'insurance_type', 'required', 'created_on']
    search_fields = ['document_type', 'batch_type', 'insurance_type']
    readonly_fields = ['created_on', 'modified_on']
    
    fieldsets = [
        ('Configuration', {
            'fields': ['batch_type', 'batch_model', 'insurance_type', 'document_type', 'required', 'template']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(CalculationConfig)
class CalculationConfigAdmin(admin.ModelAdmin):
    list_display = ['batch_type', 'batch_model', 'insurance_type', 'engine_type', 'required', 'script', 'created_on']
    list_filter = ['batch_type', 'batch_model', 'insurance_type', 'required', 'created_on']
    search_fields = ['engine_type', 'batch_type', 'insurance_type']
    readonly_fields = ['created_on', 'modified_on']
    
    fieldsets = [
        ('Configuration', {
            'fields': ['batch_type', 'batch_model', 'insurance_type', 'engine_type', 'required', 'script']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(ConversionConfig)
class ConversionConfigAdmin(admin.ModelAdmin):
    list_display = ['batch_type', 'batch_model', 'insurance_type', 'engine_type', 'required', 'script', 'created_on']
    list_filter = ['batch_type', 'batch_model', 'insurance_type', 'required', 'created_on']
    search_fields = ['engine_type', 'batch_type', 'insurance_type']
    readonly_fields = ['created_on', 'modified_on']
    
    fieldsets = [
        ('Configuration', {
            'fields': ['batch_type', 'batch_model', 'insurance_type', 'engine_type', 'required', 'script']
        }),
        ('Timestamps', {
            'fields': ['created_on', 'modified_on'],
            'classes': ['collapse']
        })
    ]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
