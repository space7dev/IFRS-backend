from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
import os

from utils.models import TimeStampedMixin

User = get_user_model()


class ModelDefinition(TimeStampedMixin):
    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20, default="v1.0")
    config = models.JSONField(default=dict)  # All configuration including generalInfo (description, status, productType, measurementModel), assumptions, formulas, parameters
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_models'
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='modified_models'
    )
    
    cloned_from = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='clones'
    )
    
    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_models'
    )
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-modified_on']
        verbose_name = 'Model Definition'
        verbose_name_plural = 'Model Definitions'

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def is_locked(self):
        return self.locked_by is not None

    def can_edit(self, user):
        if self.locked_by and self.locked_by != user:
            return False
        
        general_info = self.config.get('generalInfo', {})
        status = general_info.get('status', 'draft')
        if status == 'locked':
            return False
            
        return True


class ModelDefinitionHistory(models.Model):
    model = models.ForeignKey(
        ModelDefinition, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    config = models.JSONField(default=dict)  # All configuration data at time of save
    saved_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True
    )

    class Meta:
        ordering = ['-saved_at']
        verbose_name = 'Model Definition History'
        verbose_name_plural = 'Model Definition History'

    def __str__(self):
        return f"{self.name} v{self.version} - {self.saved_at}"


class DataUploadBatch(TimeStampedMixin):
    BATCH_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    BATCH_TYPE_CHOICES = [
        ('custom', 'Custom'),
        ('staging', 'Staging'),
    ]
    
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('reinsurance', 'Reinsurance'),
        ('group', 'Group'),
    ]
    
    QUARTER_CHOICES = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
    ]
    
    batch_id = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=255, blank=True, help_text="Optional batch label")
    batch_type = models.CharField(
        max_length=20, 
        choices=BATCH_TYPE_CHOICES, 
        default='custom',
        help_text="Upload source type"
    )
    batch_model = models.CharField(
        max_length=10, 
        choices=BATCH_MODEL_CHOICES, 
        default='GMM',
        help_text="IFRS 17 model: PAA, GMM, or VFA"
    )
    insurance_type = models.CharField(
        max_length=50, 
        choices=INSURANCE_TYPE_CHOICES,
        default='direct',
        help_text="Insurance type for this batch"
    )
    batch_year = models.IntegerField(
        default=2025,
        help_text="Reporting year"
    )
    batch_quarter = models.CharField(
        max_length=10, 
        choices=QUARTER_CHOICES,
        default='Q1',
        help_text="Reporting quarter"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='data_batches'
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='modified_data_batches'
    )
    batch_status = models.CharField(
        max_length=20, 
        choices=BATCH_STATUS_CHOICES, 
        default='pending'
    )
    upload_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Data Upload Batch'
        verbose_name_plural = 'Data Upload Batches'
    
    def __str__(self):
        return f"{self.batch_id} - {self.batch_status}"
    
    def save(self, *args, **kwargs):
        if not self.batch_id:
            current_date = timezone.now()
            year = current_date.year
            month = current_date.month
            
            last_batch = DataUploadBatch.objects.filter(
                created_on__year=year,
                created_on__month=month
            ).order_by('-created_on').first()
            
            if last_batch and last_batch.batch_id:
                try:
                    last_number = int(last_batch.batch_id.split('-')[-1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            self.batch_id = f"BATCH-{year}-{month:02d}-{next_number:04d}"
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.create_default_document_status_records()

    def create_default_document_status_records(self):
        default_document_types = self.get_default_document_types()
        
        for doc_type in default_document_types:
            DataBatchStatus.objects.get_or_create(
                batch_id=self.batch_id,
                document_type=doc_type,
                defaults={'upload_status': False}
            )

    def get_default_document_types(self):
        base_types = [
            'expense',
            'claims_paid',
            'outstanding_claims',
            'premiums',
            'commissions_paid',
            'manual_data'
        ]
        
        if self.batch_type == 'staging':
            base_types.append('staging_data')
        
        if self.insurance_type == 'reinsurance':
            base_types.append('reinsurance_data')
        
        if self.insurance_type == 'group':
            base_types.append('group_data')
        
        return base_types


class DataBatchStatus(models.Model):
    
    DOCUMENT_TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('claims_paid', 'Claims Paid'),
        ('outstanding_claims', 'Outstanding Claims'),
        ('premiums', 'Premiums'),
        ('commissions_paid', 'Commissions Paid'),
        ('manual_data', 'Manual Data'),
        ('staging_data', 'Staging Data'),
        ('reinsurance_data', 'Reinsurance Data'),
        ('group_data', 'Group Data'),
    ]
    
    batch_id = models.CharField(max_length=50, help_text="Foreign key referencing data_batch(batch_id)")
    document_type = models.CharField(
        max_length=100, 
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Type of document (e.g., Expense, Claims Paid, etc.)"
    )
    upload_status = models.BooleanField(
        default=False,
        help_text="TRUE if uploaded, FALSE by default"
    )
    
    class Meta:
        unique_together = ['batch_id', 'document_type']
        ordering = ['batch_id', 'document_type']
        verbose_name = 'Data Batch Status'
        verbose_name_plural = 'Data Batch Status Records'
    
    def __str__(self):
        return f"{self.batch_id} - {self.document_type} ({'Uploaded' if self.upload_status else 'Not Uploaded'})"
    
    @property
    def batch(self):
        try:
            return DataUploadBatch.objects.get(batch_id=self.batch_id)
        except DataUploadBatch.DoesNotExist:
            return None


class DataUploadTemplate(TimeStampedMixin):
    DATA_TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('claims_paid', 'Claims Paid'),
        ('outstanding_claims', 'Outstanding Claims'),
        ('premiums', 'Premiums'),
        ('commissions_paid', 'Commissions Paid'),
        ('manual_data', 'Manual Data'),
    ]
    
    name = models.CharField(max_length=200)
    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES)
    template_file = models.FileField(upload_to='data_templates/')
    version = models.CharField(max_length=20, default="v1.0")
    is_active = models.BooleanField(default=True)
    is_standard_template = models.BooleanField(default=False)  # For IQ staging templates
    
    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Data Upload Template'
        verbose_name_plural = 'Data Upload Templates'
    
    def __str__(self):
        return f"{self.name} - {self.data_type} ({self.version})"


class DataUpload(TimeStampedMixin):
    SOURCE_CHOICES = [
        ('custom', 'Custom'),
        ('staging', 'Staging'),
        ('api', 'API'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('direct_insurance', 'Direct Insurance'),
        ('reinsurance', 'Reinsurance'),
        ('group_insurance', 'Group Insurance'),
    ]
    
    DATA_TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('claims_paid', 'Claims Paid'),
        ('outstanding_claims', 'Outstanding Claims'),
        ('premiums', 'Premiums'),
        ('commissions_paid', 'Commissions Paid'),
        ('manual_data', 'Manual Data'),
    ]
    
    QUARTER_CHOICES = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
    ]
    
    VALIDATION_STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('validated', 'Validated'),
        ('failed', 'Failed'),
    ]
    
    upload_id = models.CharField(max_length=50, unique=True, blank=True)
    batch = models.ForeignKey(
        DataUploadBatch, 
        on_delete=models.CASCADE, 
        related_name='uploads'
    )
    
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    insurance_type = models.CharField(max_length=50, choices=INSURANCE_TYPE_CHOICES)
    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES)
    quarter = models.CharField(max_length=5, choices=QUARTER_CHOICES)
    year = models.IntegerField()
    
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='data_uploads'
    )
    
    file_upload = models.FileField(upload_to='data_uploads/', null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    validation_status = models.CharField(
        max_length=20, 
        choices=VALIDATION_STATUS_CHOICES, 
        default='in_progress'
    )
    rows_processed = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    validation_errors = models.JSONField(default=list)
    
    # For API uploads
    api_payload = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Data Upload'
        verbose_name_plural = 'Data Uploads'
    
    def __str__(self):
        return f"{self.upload_id} - {self.data_type} ({self.source})"
    
    def save(self, *args, **kwargs):
        if not self.upload_id:
            current_date = timezone.now()
            year = current_date.year
            month = current_date.month
            
            last_upload = DataUpload.objects.filter(
                created_on__year=year,
                created_on__month=month
            ).order_by('-created_on').first()
            
            if last_upload and last_upload.upload_id:
                try:
                    last_number = int(last_upload.upload_id.split('-')[-1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            self.upload_id = f"UPLOAD-{year}-{month:02d}-{next_number:04d}"
        
        if self.file_upload:
            self.original_filename = self.file_upload.name
            self.file_size = self.file_upload.size
        
        super().save(*args, **kwargs)
        
        if self.batch:
            self.batch.upload_count = self.batch.uploads.count()
            self.batch.save()
        
        if self.file_upload and self.batch:
            try:
                status_record = DataBatchStatus.objects.get(
                    batch_id=self.batch.batch_id,
                    document_type=self.data_type
                )
                status_record.upload_status = True
                status_record.save()
            except DataBatchStatus.DoesNotExist:
                DataBatchStatus.objects.create(
                    batch_id=self.batch.batch_id,
                    document_type=self.data_type,
                    upload_status=True
                )


class APIUploadLog(TimeStampedMixin):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    reporting_date = models.DateField()
    upload_date = models.DateTimeField(auto_now_add=True)
    sum_of_premiums = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sum_of_paid_claims = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sum_of_commissions = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    data_upload = models.OneToOneField(
        DataUpload, 
        on_delete=models.CASCADE, 
        related_name='api_log',
        null=True,
        blank=True
    )
    
    api_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = 'API Upload Log'
        verbose_name_plural = 'API Upload Logs'
    
    def __str__(self):
        return f"API Upload - {self.reporting_date} ({self.status})"


class DocumentTypeConfig(TimeStampedMixin):
    BATCH_TYPE_CHOICES = [
        ('custom', 'Custom'),
        ('staging', 'Staging'),
    ]
    
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('reinsurance', 'Reinsurance'),
        ('group', 'Group'),
    ]
    
    batch_type = models.CharField(
        max_length=20,
        choices=BATCH_TYPE_CHOICES,
        help_text="Custom or Staging"
    )
    batch_model = models.CharField(
        max_length=10,
        choices=BATCH_MODEL_CHOICES,
        help_text="PAA, GMM, VFA"
    )
    insurance_type = models.CharField(
        max_length=50,
        choices=INSURANCE_TYPE_CHOICES,
        help_text="Direct, Reinsurance, Group"
    )
    document_type = models.CharField(
        max_length=100,
        help_text="e.g., Premiums, Claims Paid, Manual Data, etc."
    )
    required = models.BooleanField(
        default=True,
        help_text="TRUE if document is required, FALSE if optional"
    )
    template = models.FileField(
        upload_to='document_templates/',
        help_text="Excel template file for this document type"
    )
    
    class Meta:
        ordering = ['batch_type', 'batch_model', 'insurance_type', 'document_type']
        verbose_name = 'Document Type Configuration'
        verbose_name_plural = 'Document Type Configurations'
        unique_together = ['batch_type', 'batch_model', 'insurance_type', 'document_type']
    
    def __str__(self):
        return f"{self.batch_type} - {self.batch_model} - {self.insurance_type} - {self.document_type}"


class CalculationConfig(TimeStampedMixin):
    BATCH_TYPE_CHOICES = [
        ('custom', 'Custom'),
        ('staging', 'Staging'),
    ]
    
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('reinsurance', 'Reinsurance'),
        ('group', 'Group'),
    ]
    
    batch_type = models.CharField(
        max_length=20,
        choices=BATCH_TYPE_CHOICES,
        help_text="Custom or Staging"
    )
    batch_model = models.CharField(
        max_length=10,
        choices=BATCH_MODEL_CHOICES,
        help_text="PAA, GMM, VFA"
    )
    insurance_type = models.CharField(
        max_length=50,
        choices=INSURANCE_TYPE_CHOICES,
        help_text="Direct, Reinsurance, Group"
    )
    engine_type = models.CharField(
        max_length=100,
        help_text="e.g., Premium Calculation, Reserve Calculation, etc."
    )
    required = models.BooleanField(
        default=True,
        help_text="TRUE if engine is required, FALSE if optional"
    )
    script = models.FileField(
        upload_to='calculation_scripts/',
        help_text="Python script file for this calculation engine"
    )
    
    class Meta:
        ordering = ['batch_type', 'batch_model', 'insurance_type', 'engine_type']
        verbose_name = 'Calculation Engine Configuration'
        verbose_name_plural = 'Calculation Engine Configurations'
        unique_together = ['batch_type', 'batch_model', 'insurance_type', 'engine_type']
    
    def __str__(self):
        return f"{self.batch_type} - {self.batch_model} - {self.insurance_type} - {self.engine_type}"


class ConversionConfig(TimeStampedMixin):
    BATCH_TYPE_CHOICES = [
        ('custom', 'Custom'),
        ('staging', 'Staging'),
    ]
    
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('reinsurance', 'Reinsurance'),
        ('group', 'Group'),
    ]
    
    batch_type = models.CharField(
        max_length=20,
        choices=BATCH_TYPE_CHOICES,
        help_text="Custom or Staging"
    )
    batch_model = models.CharField(
        max_length=10,
        choices=BATCH_MODEL_CHOICES,
        help_text="PAA, GMM, VFA"
    )
    insurance_type = models.CharField(
        max_length=50,
        choices=INSURANCE_TYPE_CHOICES,
        help_text="Direct, Reinsurance, Group"
    )
    engine_type = models.CharField(
        max_length=100,
        help_text="e.g., Data Conversion, Format Transformation, etc."
    )
    required = models.BooleanField(
        default=True,
        help_text="TRUE if engine is required, FALSE if optional"
    )
    script = models.FileField(
        upload_to='conversion_scripts/',
        help_text="Python script file for this conversion engine"
    )
    
    class Meta:
        ordering = ['batch_type', 'batch_model', 'insurance_type', 'engine_type']
        verbose_name = 'Conversion Engine Configuration'
        verbose_name_plural = 'Conversion Engine Configurations'
        unique_together = ['batch_type', 'batch_model', 'insurance_type', 'engine_type']
    
    def __str__(self):
        return f"{self.batch_type} - {self.batch_model} - {self.insurance_type} - {self.engine_type}"


class Currency(TimeStampedMixin):
    code = models.CharField(
        max_length=3, 
        unique=True,
        help_text="3-letter currency code (e.g., USD, EUR, GBP)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full currency name (e.g., United States Dollar)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this currency is available for selection"
    )
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class LineOfBusiness(TimeStampedMixin):
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('reinsurance', 'Reinsurance'),
        ('group', 'Group'),
    ]
    
    batch_model = models.CharField(
        max_length=10,
        choices=BATCH_MODEL_CHOICES,
        help_text="PAA, GMM, VFA"
    )
    insurance_type = models.CharField(
        max_length=50,
        choices=INSURANCE_TYPE_CHOICES,
        help_text="Direct, Reinsurance, Group"
    )
    line_of_business = models.CharField(
        max_length=200,
        help_text="Line of business name (e.g., Term Life Insurance, Auto Insurance)"
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='line_of_businesses',
        help_text="Currency for this line of business"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this line of business is active"
    )
    
    class Meta:
        ordering = ['batch_model', 'insurance_type', 'line_of_business']
        verbose_name = 'Line of Business'
        verbose_name_plural = 'Lines of Business'
        unique_together = ['batch_model', 'insurance_type', 'line_of_business']
    
    def __str__(self):
        return f"{self.batch_model} - {self.insurance_type} - {self.line_of_business}"

