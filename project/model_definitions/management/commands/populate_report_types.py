from django.core.management.base import BaseCommand
from model_definitions.models import ReportType


class Command(BaseCommand):
    help = 'Populate default report types for PAA, GMM, and VFA models'

    def handle(self, *args, **options):
        # Default report types for each model
        default_report_types = {
            'PAA': [
                ('lrc_movement_report', 'LRC Movement Report', 'Tracks opening balance, premiums, acquisition cash flows, revenue, loss component...'),
                ('lic_movement_report', 'LIC Movement Report', 'Tracks claims paid, changes in estimates, and closing LIC.'),
                ('insurance_revenue_expense_report', 'Insurance Revenue and Expense Report', 'Summarizes recognized insurance revenue and incurred claims/expenses.'),
                ('disclosure_report', 'Disclosure Report (DR)', 'Flexible format for publishing required financial disclosures.'),
                ('financial_statement_items_report', 'Financial Statement Items (FSI) Report', 'Aggregates required values for P&L and Balance Sheet.'),
                ('coverage_units_report', 'Coverage Units Report', 'Provides units used to allocate revenue over time.'),
                ('premium_allocation_reconciliation', 'Premium Allocation Reconciliation', 'PAA-specific; reconciles premiums written, earned, deferred, etc.'),
                ('loss_component_report', 'Loss Component Report', 'Details creation and reversal of loss component (onerous contracts).'),
                ('discount_rate_reconciliation', 'Discount Rate Reconciliation', 'Shows impact of opening/closing discount rates on balances.'),
                ('experience_adjustment_report', 'Experience Adjustment Report', 'Compares actual claims and premiums vs expected.'),
                ('reinsurance_report', 'Reinsurance Report', 'Mirror of direct reports, adjusted for reinsurance recoverables.'),
                ('underlying_assumption_summary', 'Underlying Assumption Summary', 'Documents key assumptions and methods used.'),
                ('reconciliation_to_gaap_report', 'Reconciliation to GAAP Report', 'Optional; bridges IFRS 17 figures to local GAAP.'),
            ],
            'GMM': [
                ('lrc_movement_report', 'LRC Movement Report', 'Includes premiums, acquisition cash flows, interest accretion, CSM release, etc.'),
                ('lic_movement_report', 'LIC Movement Report', 'Includes claims estimates, RA release, changes in discount rates.'),
                ('csm_rollforward_report', 'CSM Rollforward Report', 'Mandatory; details CSM opening, new business, changes, and release.'),
                ('insurance_revenue_expense_report', 'Insurance Revenue and Expense Report', 'Includes earned revenue from CSM + claims incurred + service expenses.'),
                ('disclosure_report', 'Disclosure Report (DR)', 'Includes reconciliation of CSM, RA, and insurance balances.'),
                ('financial_statement_items_report', 'Financial Statement Items (FSI) Report', 'Line-by-line reportable values for financial statements.'),
                ('risk_adjustment_rollforward', 'Risk Adjustment Rollforward', 'Required if RA is material; tracks RA changes.'),
                ('coverage_units_report', 'Coverage Units Report', 'Basis of CSM and revenue allocation.'),
                ('discount_rate_reconciliation', 'Discount Rate Reconciliation', 'Quantifies financial vs insurance result impact.'),
                ('experience_adjustment_report', 'Experience Adjustment Report', 'Measures actual vs expected for assumptions and events.'),
                ('loss_component_report', 'Loss Component Report', 'Applies if contracts become onerous.'),
                ('reinsurance_report', 'Reinsurance Report', 'Tracks CSM, RA, recoverables on reinsurance side.'),
                ('csm_sensitivity_report', 'CSM Sensitivity Report', 'For stress testing and sensitivity disclosures.'),
                ('underlying_assumption_summary', 'Underlying Assumption Summary', 'Disclosure of assumptions (mortality, lapse, etc.).'),
                ('reconciliation_to_gaap_report', 'Reconciliation to GAAP Report', 'Optional; bridges IFRS 17 to local GAAP.'),
            ],
            'VFA': [
                ('lrc_movement_report', 'LRC Movement Report', 'Similar to GMM; includes VFA-specific adjustments.'),
                ('lic_movement_report', 'LIC Movement Report', 'Includes changes in fulfilment cash flows and discounting.'),
                ('csm_rollforward_report', 'CSM Rollforward Report', 'Required; includes financial return service under VFA.'),
                ('insurance_revenue_expense_report', 'Insurance Revenue and Expense Report', 'Includes investment services and shared financial risks.'),
                ('disclosure_report', 'Disclosure Report (DR)', 'Includes VFA-specific disclosures if applicable.'),
                ('financial_statement_items_report', 'Financial Statement Items (FSI) Report', 'Supports P&L and Balance Sheet disclosures.'),
                ('risk_adjustment_rollforward', 'Risk Adjustment Rollforward', 'Required if RA is significant.'),
                ('coverage_units_report', 'Coverage Units Report', 'For release of CSM and services provided.'),
                ('discount_rate_reconciliation', 'Discount Rate Reconciliation', 'Shows impact of discounting and financial returns.'),
                ('experience_adjustment_report', 'Experience Adjustment Report', 'Includes both insurance and financial components.'),
                ('loss_component_report', 'Loss Component Report', 'Applies if VFA contracts become onerous.'),
                ('reinsurance_report', 'Reinsurance Report', 'Adjusted for VFA-reinsurance treatment.'),
                ('csm_sensitivity_report', 'CSM Sensitivity Report', 'Required for scenario testing.'),
                ('underlying_assumption_summary', 'Underlying Assumption Summary', 'Full list of measurement assumptions.'),
                ('reconciliation_to_gaap_report', 'Reconciliation to GAAP Report', 'Optional; for audit and regulatory reconciliation.'),
            ]
        }

        created_count = 0
        updated_count = 0

        for batch_model, report_types in default_report_types.items():
            for report_type_code, report_type_name, notes in report_types:
                report_type, created = ReportType.objects.get_or_create(
                    batch_model=batch_model,
                    report_type=report_type_code,
                    defaults={
                        'is_enabled': True,
                        'notes': notes
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created report type: {batch_model} - {report_type_name}'
                        )
                    )
                else:
                    # Update existing record with latest notes
                    if report_type.notes != notes:
                        report_type.notes = notes
                        report_type.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Updated report type: {batch_model} - {report_type_name}'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed report types. Created: {created_count}, Updated: {updated_count}'
            )
        ) 