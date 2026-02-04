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


class ReportType(TimeStampedMixin):
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('staging_table', 'Staging Table'),
        ('lrc_movement_report', 'LRC Movement Report'),
        ('lic_movement_report', 'LIC Movement Report'),
        ('insurance_revenue_expense_report', 'Insurance Revenue and Expense Report'),
        ('disclosure_report', 'Disclosure Report (DR)'),
        ('financial_statement_items_report', 'Financial Statement Items (FSI) Report'),
        ('coverage_units_report', 'Coverage Units Report'),
        ('premium_allocation_reconciliation', 'Premium Allocation Reconciliation'),
        ('loss_component_report', 'Loss Component Report'),
        ('discount_rate_reconciliation', 'Discount Rate Reconciliation'),
        ('experience_adjustment_report', 'Experience Adjustment Report'),
        ('reinsurance_report', 'Reinsurance Report'),
        ('underlying_assumption_summary', 'Underlying Assumption Summary'),
        ('reconciliation_to_gaap_report', 'Reconciliation to GAAP Report'),
        
        ('csm_rollforward_report', 'CSM Rollforward Report'),
        ('risk_adjustment_rollforward', 'Risk Adjustment Rollforward'),
        ('csm_sensitivity_report', 'CSM Sensitivity Report'),
        
    ]
    
    batch_model = models.CharField(
        max_length=10,
        choices=BATCH_MODEL_CHOICES,
        help_text="PAA, GMM, VFA"
    )
    report_type = models.CharField(
        max_length=100,
        choices=REPORT_TYPE_CHOICES,
        help_text="Type of report"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this report type is enabled"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this report type"
    )
    
    class Meta:
        ordering = ['batch_model', 'report_type']
        verbose_name = 'Report Type'
        verbose_name_plural = 'Report Types'
        unique_together = ['batch_model', 'report_type']
    
    def __str__(self):
        return f"{self.batch_model} - {self.get_report_type_display()}"
    
    def get_default_notes(self):
        notes_map = {
            'lrc_movement_report': 'Tracks opening balance, premiums, acquisition cash flows, revenue, loss component...',
            'lic_movement_report': 'Tracks claims paid, changes in estimates, and closing LIC.',
            'insurance_revenue_expense_report': 'Summarizes recognized insurance revenue and incurred claims/expenses.',
            'disclosure_report': 'Flexible format for publishing required financial disclosures.',
            'financial_statement_items_report': 'Aggregates required values for P&L and Balance Sheet.',
            'coverage_units_report': 'Provides units used to allocate revenue over time.',
            'premium_allocation_reconciliation': 'PAA-specific; reconciles premiums written, earned, deferred, etc.',
            'loss_component_report': 'Details creation and reversal of loss component (onerous contracts).',
            'discount_rate_reconciliation': 'Shows impact of opening/closing discount rates on balances.',
            'experience_adjustment_report': 'Compares actual claims and premiums vs expected.',
            'reinsurance_report': 'Mirror of direct reports, adjusted for reinsurance recoverables.',
            'underlying_assumption_summary': 'Documents key assumptions and methods used.',
            'reconciliation_to_gaap_report': 'Optional; bridges IFRS 17 figures to local GAAP.',
            
            'csm_rollforward_report': 'Mandatory; details CSM opening, new business, changes, and release.',
            'risk_adjustment_rollforward': 'Required if RA is material; tracks RA changes.',
            'csm_sensitivity_report': 'For stress testing and sensitivity disclosures.',
            
        }
        return notes_map.get(self.report_type, '')
    
    def save(self, *args, **kwargs):
        if not self.notes:
            self.notes = self.get_default_notes()
        super().save(*args, **kwargs)


class SubmittedReport(TimeStampedMixin):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('superseded', 'Superseded'),
    ]
    
    QUARTER_CHOICES = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
    ]
    
    run_id = models.CharField(
        max_length=100,
        help_text="Calculation Run ID (e.g., RUN-ABC12345678)"
    )
    report_type = models.CharField(
        max_length=100,
        help_text="Type of report (e.g., lrc_movement_report)"
    )
    report_type_display = models.CharField(
        max_length=200,
        blank=True,
        help_text="Display name of the report type"
    )
    model_type = models.CharField(
        max_length=10,
        help_text="PAA, GMM, or VFA"
    )
    assign_year = models.IntegerField(
        help_text="Reporting year this report is submitted for"
    )
    assign_quarter = models.CharField(
        max_length=10,
        choices=QUARTER_CHOICES,
        help_text="Reporting quarter this report is submitted for"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Status of the submitted report"
    )
    ifrs_engine_result_id = models.IntegerField(
        help_text="Foreign key reference to IFRSEngineResult"
    )
    model_used = models.CharField(
        max_length=255,
        blank=True,
        help_text="Model name and version used"
    )
    batch_used = models.CharField(
        max_length=255,
        blank=True,
        help_text="Batch ID used"
    )
    line_of_business_used = models.TextField(
        blank=True,
        help_text="Comma-separated list of LOBs used"
    )
    conversion_engine_used = models.CharField(
        max_length=255,
        blank=True,
        help_text="Conversion engine type used"
    )
    ifrs_engine_used = models.CharField(
        max_length=255,
        blank=True,
        help_text="IFRS engine type used"
    )
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_reports'
    )
    
    class Meta:
        ordering = ['-assign_year', '-assign_quarter', '-created_on']
        verbose_name = 'Submitted Report'
        verbose_name_plural = 'Submitted Reports'
        indexes = [
            models.Index(fields=['assign_year', 'assign_quarter']),
            models.Index(fields=['report_type', 'assign_year', 'assign_quarter']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.report_type} - {self.assign_year} {self.assign_quarter} ({self.status})"
    
    def save(self, *args, **kwargs):
        if self.status == 'active':
            SubmittedReport.objects.filter(
                report_type=self.report_type,
                assign_year=self.assign_year,
                assign_quarter=self.assign_quarter,
                status='active'
            ).exclude(pk=self.pk).update(status='superseded')
        
        super().save(*args, **kwargs)


class IFRSEngineInput(models.Model):
    run_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique Run ID for this engine execution"
    )
    model_definition = models.JSONField(
        help_text="JSON model definition data"
    )
    batch_data = models.JSONField(
        help_text="JSON batch data from uploads"
    )
    field_parameters = models.JSONField(
        help_text="JSON field parameters from report generation"
    )
    created_by = models.CharField(
        max_length=100,
        help_text="Username or system"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Insert timestamp"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'IFRS Engine Input'
        verbose_name_plural = 'IFRS Engine Inputs'
        db_table = 'ifrs_engine_inputs'
    
    def __str__(self):
        return f"Run {self.run_id} - {self.created_at}"


class IFRSApiConfig(TimeStampedMixin):
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
    ]
    
    AUTH_TYPE_CHOICES = [
        ('api_key', 'API Key'),
        ('oauth', 'OAuth'),
        ('basic', 'Basic Auth'),
        ('bearer', 'Bearer Token'),
        ('none', 'None'),
    ]
    
    SCHEDULE_CHOICES = [
        ('manual', 'Manual'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-Annually'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disabled', 'Disabled'),
        ('error', 'Error'),
    ]
    
    PAGINATION_STRATEGY_CHOICES = [
        ('none', 'None'),
        ('page_limit', 'Page/Limit'),
        ('cursor_next_token', 'Cursor/Next Token'),
        ('link_based', 'Link-based'),
    ]
    
    WATERMARK_FORMAT_CHOICES = [
        ('iso8601', 'ISO8601'),
        ('date', 'Date'),
        ('epoch', 'Epoch'),
    ]
    
    WATERMARK_LOCATION_CHOICES = [
        ('query_param', 'Query Parameter'),
        ('header', 'Header'),
        ('body', 'Body'),
    ]
    
    BEHAVIOR_CHOICES = [
        ('append_only', 'Append Only'),
        ('upsert_on_key', 'Upsert on Key'),
    ]
    
    api_source_name = models.CharField(
        max_length=255,
        help_text="API source name"
    )
    client_id = models.CharField(
        max_length=255,
        help_text="Client ID / System name"
    )
    api_endpoint = models.CharField(
        max_length=500,
        help_text="API endpoint (masked for security)"
    )
    data_type = models.CharField(
        max_length=100,
        help_text="Data type"
    )
    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        default='GET',
        help_text="HTTP method"
    )
    auth_type = models.CharField(
        max_length=20,
        choices=AUTH_TYPE_CHOICES,
        default='api_key',
        help_text="Authentication type"
    )
    schedule = models.CharField(
        max_length=20,
        choices=SCHEDULE_CHOICES,
        default='manual',
        help_text="Execution schedule"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Configuration status"
    )
    
    headers_query_params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Headers and query parameters as key-value pairs"
    )
    
    pagination_strategy = models.CharField(
        max_length=20,
        choices=PAGINATION_STRATEGY_CHOICES,
        default='none',
        help_text="Pagination strategy"
    )
    page_param_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Page parameter name for pagination"
    )
    limit_param_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Limit parameter name for pagination"
    )
    next_token_jsonpath = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="JSONPath for next page token"
    )
    limit_value = models.IntegerField(
        blank=True,
        null=True,
        help_text="Default limit value for pagination"
    )
    
    watermark_field_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Watermark field name (e.g., updated_at)"
    )
    watermark_format = models.CharField(
        max_length=20,
        choices=WATERMARK_FORMAT_CHOICES,
        default='iso8601',
        blank=True,
        null=True,
        help_text="Watermark format"
    )
    watermark_location = models.CharField(
        max_length=20,
        choices=WATERMARK_LOCATION_CHOICES,
        default='query_param',
        blank=True,
        null=True,
        help_text="Watermark location"
    )
    default_initial_watermark = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Default initial watermark value"
    )
    
    records_jsonpath = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="JSONPath for records (e.g., $.data.items[*])"
    )
    next_page_token_jsonpath = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="JSONPath for next page token"
    )
    total_count_jsonpath = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="JSONPath for total count"
    )
    
    primary_key_fields = models.JSONField(
        default=list,
        blank=True,
        help_text="Primary key fields for deduplication"
    )
    behavior = models.CharField(
        max_length=20,
        choices=BEHAVIOR_CHOICES,
        default='append_only',
        help_text="Drop/Upsert behavior"
    )
    
    max_rps = models.IntegerField(
        default=10,
        help_text="Maximum requests per second"
    )
    retry_count = models.IntegerField(
        default=3,
        help_text="Number of retries on failure"
    )
    backoff_min_ms = models.IntegerField(
        default=200,
        help_text="Minimum backoff time in milliseconds"
    )
    backoff_max_ms = models.IntegerField(
        default=2000,
        help_text="Maximum backoff time in milliseconds"
    )
    timeout_ms = models.IntegerField(
        default=30000,
        help_text="Request timeout in milliseconds"
    )
    
    secret_references = models.JSONField(
        default=dict,
        blank=True,
        help_text="Secret references stored in vault"
    )
    tls_required = models.BooleanField(
        default=True,
        help_text="Whether TLS is required"
    )
    mtls_certs = models.FileField(
        upload_to='api_certs/',
        blank=True,
        null=True,
        help_text="mTLS certificates file"
    )
    ip_allowlist_note = models.TextField(
        blank=True,
        help_text="IP allowlist notes"
    )
    
    raw_landing_mode = models.BooleanField(
        default=True,
        help_text="Whether to use raw landing mode (JSON per row)"
    )
    mapping_profile = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Mapping profile reference"
    )
    validation_profile = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Validation profile reference"
    )
    
    owner = models.CharField(
        max_length=100,
        help_text="Configuration owner"
    )
    alert_emails = models.JSONField(
        default=list,
        blank=True,
        help_text="Alert email addresses on failure"
    )
    alert_webhooks = models.JSONField(
        default=list,
        blank=True,
        help_text="Alert webhook URLs on failure"
    )
    auto_disable_on_failures = models.IntegerField(
        default=5,
        help_text="Auto-disable after N consecutive failures"
    )
    
    last_test_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last connection test date"
    )
    last_test_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Last test status"
    )
    last_run_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last execution date"
    )
    consecutive_failures = models.IntegerField(
        default=0,
        help_text="Count of consecutive failures"
    )
    
    class Meta:
        ordering = ['api_source_name', 'client_id']
        verbose_name = 'IFRS API Configuration'
        verbose_name_plural = 'IFRS API Configurations'
        db_table = 'ifrs_apis'
        
    def __str__(self):
        return f"{self.api_source_name} - {self.client_id}"
    
    def mask_endpoint(self):
        if not self.api_endpoint:
            return ""
        parts = self.api_endpoint.split('/')
        if len(parts) > 3:
            return f"{parts[0]}//{parts[2]}/***"
        return self.api_endpoint


class IFRSEngineResult(models.Model):
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Error', 'Error'),
    ]
    
    BATCH_MODEL_CHOICES = [
        ('PAA', 'PAA'),
        ('GMM', 'GMM'),
        ('VFA', 'VFA'),
    ]
    
    QUARTER_CHOICES = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
    ]
    
    run_id = models.CharField(
        max_length=50,
        help_text="Reference to engine run ID",
        default="LEGACY-RUN"
    )
    model_guid = models.UUIDField(
        help_text="Reference to model run"
    )
    model_type = models.CharField(
        max_length=10,
        choices=BATCH_MODEL_CHOICES,
        help_text="PAA, GMM, VFA"
    )
    report_type = models.CharField(
        max_length=50,
        help_text="e.g., LRC_Movement, LIC_Movement, DR_LRC"
    )
    year = models.IntegerField(
        help_text="Reporting year"
    )
    quarter = models.CharField(
        max_length=2,
        choices=QUARTER_CHOICES,
        help_text="Reporting quarter"
    )

    currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Currency code"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Success or Error"
    )
    result_json = models.JSONField(
        help_text="Output or error message"
    )
    created_by = models.CharField(
        max_length=100,
        help_text="Username or system"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Insert timestamp"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'IFRS Engine Result'
        verbose_name_plural = 'IFRS Engine Results'
        indexes = [
            models.Index(fields=['run_id']),
            models.Index(fields=['model_type', 'report_type']),
            models.Index(fields=['year', 'quarter']),
            models.Index(fields=['created_by']),
        ]
        db_table = 'ifrs_engine_results'
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['Success', 'Error']),
                name='status_check'
            )
        ]
    
    def __str__(self):
        return f"{self.model_type} - {self.report_type} - {self.year} {self.quarter} - {self.lob}"


class CalculationValue(models.Model):
    value_id = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Unique identifier for this value (e.g., 'DR.MA.Opening.Liabilities.Total')"
    )
    run_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Reference to engine run ID"
    )
    report_type = models.CharField(
        max_length=50,
        help_text="Type of report this value belongs to"
    )
    
    period = models.CharField(
        max_length=20,
        help_text="Reporting period (e.g., '2026 Q4')"
    )
    legal_entity = models.CharField(
        max_length=200,
        help_text="Legal entity name"
    )
    currency = models.CharField(
        max_length=10,
        help_text="Currency code (e.g., 'USD', 'EUR')"
    )
    
    label = models.CharField(
        max_length=300,
        help_text="Human-readable label/description"
    )
    value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Calculated numeric value"
    )
    unit = models.CharField(
        max_length=50,
        default='currency',
        help_text="Unit of measurement (currency, percentage, count, etc.)"
    )
    
    line_of_business = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Line of business"
    )
    cohort = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Cohort identifier"
    )
    group_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Group identifier"
    )
    
    formula_human_readable = models.TextField(
        blank=True,
        null=True,
        help_text="Human-readable formula description"
    )
    dependencies = models.JSONField(
        default=list,
        help_text="List of value_ids this calculation depends on"
    )
    calculation_method = models.CharField(
        max_length=20,
        help_text="Calculation method (PAA, GMM, VFA)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional calculation notes from engine"
    )
    
    is_missing_data = models.BooleanField(
        default=False,
        help_text="Flag if calculation used missing/incomplete data"
    )
    is_override = models.BooleanField(
        default=False,
        help_text="Flag if value was manually overridden"
    )
    is_fallback = models.BooleanField(
        default=False,
        help_text="Flag if fallback logic was used"
    )
    has_rounding = models.BooleanField(
        default=False,
        help_text="Flag if rounding was applied"
    )
    
    calc_engine_version = models.CharField(
        max_length=50,
        help_text="Calculation engine version"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Calculation timestamp"
    )
    
    engine_result = models.ForeignKey(
        'IFRSEngineResult',
        on_delete=models.CASCADE,
        related_name='calculation_values',
        help_text="Parent IFRS engine result"
    )
    
    class Meta:
        ordering = ['value_id']
        verbose_name = 'Calculation Value'
        verbose_name_plural = 'Calculation Values'
        indexes = [
            models.Index(fields=['run_id', 'value_id']),
            models.Index(fields=['run_id', 'report_type']),
            models.Index(fields=['value_id']),
        ]
        db_table = 'calculation_values'
        unique_together = [['run_id', 'value_id']]
    
    def __str__(self):
        return f"{self.value_id} ({self.run_id})"


class AssumptionReference(models.Model):
    calculation_value = models.ForeignKey(
        'CalculationValue',
        on_delete=models.CASCADE,
        related_name='assumptions',
        help_text="Related calculation value"
    )
    
    assumption_type = models.CharField(
        max_length=100,
        help_text="Type of assumption (discount_curve, risk_adjustment, etc.)"
    )
    assumption_id = models.CharField(
        max_length=200,
        help_text="Unique identifier for this assumption"
    )
    assumption_version = models.CharField(
        max_length=50,
        help_text="Version of the assumption"
    )
    effective_date = models.DateField(
        help_text="Effective date of the assumption"
    )
    
    metadata = models.JSONField(
        default=dict,
        help_text="Additional assumption-specific metadata"
    )
    
    class Meta:
        ordering = ['assumption_type', 'assumption_id']
        verbose_name = 'Assumption Reference'
        verbose_name_plural = 'Assumption References'
        db_table = 'assumption_references'
    
    def __str__(self):
        return f"{self.assumption_type}: {self.assumption_id} (v{self.assumption_version})"


class InputDataReference(models.Model):
    calculation_value = models.ForeignKey(
        'CalculationValue',
        on_delete=models.CASCADE,
        related_name='input_refs',
        help_text="Related calculation value"
    )
    
    dataset_name = models.CharField(
        max_length=200,
        help_text="Name of the input dataset (premiums, claims, etc.)"
    )
    source_snapshot_id = models.CharField(
        max_length=200,
        help_text="Snapshot identifier for data version tracking"
    )
    source_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Hash of source data for change detection"
    )
    record_count = models.IntegerField(
        default=0,
        help_text="Number of records from this dataset"
    )
    
    metadata = models.JSONField(
        default=dict,
        help_text="Additional dataset-specific metadata"
    )
    
    class Meta:
        ordering = ['dataset_name']
        verbose_name = 'Input Data Reference'
        verbose_name_plural = 'Input Data References'
        db_table = 'input_data_references'
    
    def __str__(self):
        return f"{self.dataset_name} ({self.record_count} records)"

