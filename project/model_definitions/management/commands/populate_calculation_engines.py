from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from model_definitions.models import CalculationConfig
import os
import json
import datetime
import random


class Command(BaseCommand):
    help = 'Populate sample calculation engines for testing'

    def handle(self, *args, **options):
        sample_engine_script = '''
import json
import sys
import datetime
import random
from typing import Dict, Any, List


def generate_mock_value(base_value: float, variation: float = 0.1) -> float:
    """Generate a mock value with some variation"""
    return round(base_value * (1 + random.uniform(-variation, variation)), 2)


def generate_lrc_movement_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for LRC Movement Report"""
    detailed_view = []
    summary_view = []
    
    # Base values for each LOB
    lob_base_values = {
        "Bonds_BSD": {"opening": 600, "premiums": 300, "claims": 200, "other": 300},
        "Engineering_BSD": {"opening": 570, "premiums": 285, "claims": 190, "other": 285},
        "Fire_BSD": {"opening": 522, "premiums": 261, "claims": 174, "other": 261},
        "General Accident_BSD": {"opening": 552, "premiums": 276, "claims": 184, "other": 276},
        "Liability_BSD": {"opening": 528, "premiums": 264, "claims": 176, "other": 264},
        "Marine_BSD": {"opening": 534, "premiums": 267, "claims": 178, "other": 267},
        "Motor_BSD": {"opening": 549, "premiums": 275, "claims": 183, "other": 274}
    }
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            if lob in lob_base_values:
                base = lob_base_values[lob]
                
                # Generate values with some variation based on year
                year_factor = 1 + (year - 2021) * 0.1
                
                opening_balance = generate_mock_value(base["opening"] * year_factor)
                premiums = generate_mock_value(base["premiums"] * year_factor)
                claims = generate_mock_value(base["claims"] * year_factor)
                other_movements = generate_mock_value(base["other"] * year_factor)
                closing_balance = opening_balance + premiums - claims + other_movements
                
                detailed_row = {
                    "ReportingDate": reporting_date,
                    "Year": year,
                    "LOB": lob,
                    "OpeningBalance": opening_balance,
                    "Premiums": premiums,
                    "Claims": claims,
                    "OtherMovements": other_movements,
                    "ClosingBalance": closing_balance
                }
                detailed_view.append(detailed_row)
                summary_row[lob] = closing_balance
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_lic_movement_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for LIC Movement Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            opening_balance = generate_mock_value(800 + (year - 2021) * 50)
            interest_unwinding = generate_mock_value(40 + (year - 2021) * 5)
            release_of_risk_adjustment = generate_mock_value(30 + (year - 2021) * 3)
            losses_recognized = generate_mock_value(200 + (year - 2021) * 20)
            changes_in_estimates = generate_mock_value(10 + (year - 2021) * 2)
            closing_balance = opening_balance + interest_unwinding - release_of_risk_adjustment - losses_recognized + changes_in_estimates
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "OpeningBalance": opening_balance,
                "InterestUnwinding": interest_unwinding,
                "ReleaseOfRiskAdjustment": release_of_risk_adjustment,
                "LossesRecognized": losses_recognized,
                "ChangesInEstimates": changes_in_estimates,
                "ClosingBalance": closing_balance
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = closing_balance
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_insurance_revenue_expense_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Insurance Revenue Expense Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            insurance_revenue = generate_mock_value(1000 + (year - 2021) * 100)
            insurance_service_expense = generate_mock_value(700 + (year - 2021) * 70)
            insurance_finance_income_expense = generate_mock_value(50 + (year - 2021) * 5)
            acquisition_costs_expensed = generate_mock_value(150 + (year - 2021) * 15)
            result = insurance_revenue - insurance_service_expense + insurance_finance_income_expense - acquisition_costs_expensed
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "InsuranceRevenue": insurance_revenue,
                "InsuranceServiceExpense": insurance_service_expense,
                "InsuranceFinanceIncomeExpense": insurance_finance_income_expense,
                "AcquisitionCostsExpensed": acquisition_costs_expensed,
                "Result": result
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = result
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_disclosure_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Disclosure Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            liability_for_remaining_coverage = generate_mock_value(1200 + (year - 2021) * 120)
            liability_for_incurred_claims = generate_mock_value(800 + (year - 2021) * 80)
            loss_component = generate_mock_value(100 + (year - 2021) * 10)
            risk_adjustment = generate_mock_value(200 + (year - 2021) * 20)
            insurance_finance_income_expense = generate_mock_value(60 + (year - 2021) * 6)
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "LiabilityForRemainingCoverage": liability_for_remaining_coverage,
                "LiabilityForIncurredClaims": liability_for_incurred_claims,
                "LossComponent": loss_component,
                "RiskAdjustment": risk_adjustment,
                "InsuranceFinanceIncomeExpense": insurance_finance_income_expense
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = liability_for_remaining_coverage + liability_for_incurred_claims
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_financial_statement_items_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Financial Statement Items Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            assets = generate_mock_value(2000 + (year - 2021) * 200)
            liabilities = generate_mock_value(1500 + (year - 2021) * 150)
            equity = assets - liabilities
            revenue = generate_mock_value(1000 + (year - 2021) * 100)
            expenses = generate_mock_value(800 + (year - 2021) * 80)
            profit_loss = revenue - expenses
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "Assets": assets,
                "Liabilities": liabilities,
                "Equity": equity,
                "Revenue": revenue,
                "Expenses": expenses,
                "ProfitLoss": profit_loss
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = profit_loss
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_premium_allocation_reconciliation_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Premium Allocation Reconciliation"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            earned_premiums = generate_mock_value(1000 + (year - 2021) * 100)
            unearned_premiums = generate_mock_value(300 + (year - 2021) * 30)
            premium_receivables = generate_mock_value(200 + (year - 2021) * 20)
            adjustments = generate_mock_value(50 + (year - 2021) * 5)
            ending_balance = earned_premiums + unearned_premiums + premium_receivables + adjustments
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "EarnedPremiums": earned_premiums,
                "UnearnedPremiums": unearned_premiums,
                "PremiumReceivables": premium_receivables,
                "Adjustments": adjustments,
                "EndingBalance": ending_balance
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = ending_balance
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_loss_component_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Loss Component Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            opening_loss_component = generate_mock_value(100 + (year - 2021) * 10)
            losses_recognized = generate_mock_value(50 + (year - 2021) * 5)
            reversals = generate_mock_value(20 + (year - 2021) * 2)
            utilization = generate_mock_value(30 + (year - 2021) * 3)
            closing_loss_component = opening_loss_component + losses_recognized - reversals - utilization
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "OpeningLossComponent": opening_loss_component,
                "LossesRecognized": losses_recognized,
                "Reversals": reversals,
                "Utilization": utilization,
                "ClosingLossComponent": closing_loss_component
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = closing_loss_component
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_discount_rate_reconciliation_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Discount Rate Reconciliation"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            opening_effect = generate_mock_value(200 + (year - 2021) * 20)
            changes_in_discount_rate = generate_mock_value(30 + (year - 2021) * 3)
            interest_effect = generate_mock_value(40 + (year - 2021) * 4)
            closing_effect = opening_effect + changes_in_discount_rate + interest_effect
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "OpeningEffect": opening_effect,
                "ChangesInDiscountRate": changes_in_discount_rate,
                "InterestEffect": interest_effect,
                "ClosingEffect": closing_effect
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = closing_effect
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_experience_adjustment_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Experience Adjustment Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            expected = generate_mock_value(1000 + (year - 2021) * 100)
            actual = generate_mock_value(950 + (year - 2021) * 95)
            experience_variance = actual - expected
            assumption_changes = generate_mock_value(20 + (year - 2021) * 2)
            total_adjustment = experience_variance + assumption_changes
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "Expected": expected,
                "Actual": actual,
                "ExperienceVariance": experience_variance,
                "AssumptionChanges": assumption_changes,
                "TotalAdjustment": total_adjustment
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = total_adjustment
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_reinsurance_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Reinsurance Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            ceded_premiums = generate_mock_value(300 + (year - 2021) * 30)
            reinsurance_commissions = generate_mock_value(50 + (year - 2021) * 5)
            reinsurance_recoveries = generate_mock_value(200 + (year - 2021) * 20)
            reinsurance_assets = generate_mock_value(150 + (year - 2021) * 15)
            reinsurance_result = ceded_premiums - reinsurance_commissions - reinsurance_recoveries + reinsurance_assets
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "CededPremiums": ceded_premiums,
                "ReinsuranceCommissions": reinsurance_commissions,
                "ReinsuranceRecoveries": reinsurance_recoveries,
                "ReinsuranceAssets": reinsurance_assets,
                "ReinsuranceResult": reinsurance_result
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = reinsurance_result
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_paa_roll_forward_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for PAA Roll Forward Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            opening_balance = generate_mock_value(800 + (year - 2021) * 80)
            premiums_received = generate_mock_value(400 + (year - 2021) * 40)
            acquisition_cash_flows = generate_mock_value(100 + (year - 2021) * 10)
            amortization_of_acquisition_cash_flows = generate_mock_value(80 + (year - 2021) * 8)
            insurance_service_expense = generate_mock_value(300 + (year - 2021) * 30)
            risk_adjustment_movement = generate_mock_value(50 + (year - 2021) * 5)
            interest_unwinding = generate_mock_value(40 + (year - 2021) * 4)
            claims_paid = generate_mock_value(250 + (year - 2021) * 25)
            closing_balance = opening_balance + premiums_received - acquisition_cash_flows + amortization_of_acquisition_cash_flows - insurance_service_expense - risk_adjustment_movement + interest_unwinding - claims_paid
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "OpeningBalance": opening_balance,
                "PremiumsReceived": premiums_received,
                "AcquisitionCashFlows": acquisition_cash_flows,
                "AmortizationOfAcquisitionCashFlows": amortization_of_acquisition_cash_flows,
                "InsuranceServiceExpense": insurance_service_expense,
                "RiskAdjustmentMovement": risk_adjustment_movement,
                "InterestUnwinding": interest_unwinding,
                "ClaimsPaid": claims_paid,
                "ClosingBalance": closing_balance
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = closing_balance
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def generate_cash_flow_statement_report_data(lobs: List[str], years: List[int], reporting_date: str) -> Dict[str, Any]:
    """Generate mock data for Cash Flow Statement Report"""
    detailed_view = []
    summary_view = []
    
    for year in years:
        summary_row = {"ReportingDate": reporting_date, "Year": year}
        
        for lob in lobs:
            operating_cash_inflows = generate_mock_value(1000 + (year - 2021) * 100)
            operating_cash_outflows = generate_mock_value(700 + (year - 2021) * 70)
            investing_cash_flows = generate_mock_value(200 + (year - 2021) * 20)
            financing_cash_flows = generate_mock_value(100 + (year - 2021) * 10)
            net_change_in_cash = operating_cash_inflows - operating_cash_outflows + investing_cash_flows + financing_cash_flows
            opening_cash = generate_mock_value(500 + (year - 2021) * 50)
            closing_cash = opening_cash + net_change_in_cash
            
            detailed_row = {
                "ReportingDate": reporting_date,
                "Year": year,
                "LOB": lob,
                "OperatingCashInflows": operating_cash_inflows,
                "OperatingCashOutflows": operating_cash_outflows,
                "InvestingCashFlows": investing_cash_flows,
                "FinancingCashFlows": financing_cash_flows,
                "NetChangeInCash": net_change_in_cash,
                "OpeningCash": opening_cash,
                "ClosingCash": closing_cash
            }
            detailed_view.append(detailed_row)
            summary_row[lob] = closing_cash
        
        summary_view.append(summary_row)
    
    return {
        "detailed_view": detailed_view,
        "summary_view": summary_view
    }


def calculate_ifrs_results(engine_input: Dict[str, Any]) -> Dict[str, Any]:
    run_id = engine_input.get('run_id')
    model_definition = engine_input.get('model_definition', {})
    batch_data = engine_input.get('batch_data', [])
    field_parameters = engine_input.get('field_parameters', {})
    current_batch = engine_input.get('current_batch', {})
    current_lob = engine_input.get('current_lob', {})
    current_report_type = engine_input.get('current_report_type', {})
    
    batch_id = current_batch.get('batch_id', 'UNKNOWN')
    lob = current_lob.get('line_of_business', 'Unknown')
    report_type = current_report_type.get('report_type', 'unknown')
    year = current_batch.get('batch_year', 2025)
    quarter = current_batch.get('batch_quarter', 'Q1')
    currency = current_lob.get('currency', 'USD')
    
    model_config = model_definition.get('config', {})
    measurement_model = model_config.get('generalInfo', {}).get('measurementModel', 'GMM')
    
    # Default LOBs and years
    lobs = [
        "Bonds_BSD", "Engineering_BSD", "Fire_BSD", "General Accident_BSD",
        "Liability_BSD", "Marine_BSD", "Motor_BSD"
    ]
    years = [2021, 2022, 2023, 2024]
    reporting_date = "12-31-2024"
    
    # Generate report data based on report type
    if report_type == 'lrc_movement_report':
        results = generate_lrc_movement_report_data(lobs, years, reporting_date)
    elif report_type == 'lic_movement_report':
        results = generate_lic_movement_report_data(lobs, years, reporting_date)
    elif report_type == 'insurance_revenue_expense_report':
        results = generate_insurance_revenue_expense_report_data(lobs, years, reporting_date)
    elif report_type == 'disclosure_report':
        results = generate_disclosure_report_data(lobs, years, reporting_date)
    elif report_type == 'financial_statement_items_report':
        results = generate_financial_statement_items_report_data(lobs, years, reporting_date)
    elif report_type == 'premium_allocation_reconciliation':
        results = generate_premium_allocation_reconciliation_data(lobs, years, reporting_date)
    elif report_type == 'loss_component_report':
        results = generate_loss_component_report_data(lobs, years, reporting_date)
    elif report_type == 'discount_rate_reconciliation':
        results = generate_discount_rate_reconciliation_data(lobs, years, reporting_date)
    elif report_type == 'experience_adjustment_report':
        results = generate_experience_adjustment_report_data(lobs, years, reporting_date)
    elif report_type == 'reinsurance_report':
        results = generate_reinsurance_report_data(lobs, years, reporting_date)
    elif report_type == 'paa_roll_forward_report':
        results = generate_paa_roll_forward_report_data(lobs, years, reporting_date)
    elif report_type == 'cash_flow_statement_report':
        results = generate_cash_flow_statement_report_data(lobs, years, reporting_date)
    else:
        # Default to basic IFRS calculations
        results = perform_calculations(
            measurement_model=measurement_model,
            report_type=report_type,
            batch_data=batch_data,
            model_config=model_config,
            field_parameters=field_parameters
        )
    
    output = {
        "status": "success",
        "run_id": run_id,
        "batch_id": batch_id,
        "lob": lob,
        "report_type": report_type,
        "year": year,
        "quarter": quarter,
        "currency": currency,
        "calculation_date": datetime.datetime.now().isoformat() + "Z",
        "results": results
    }
    
    return output


def perform_calculations(
    measurement_model: str,
    report_type: str,
    batch_data: List[Dict[str, Any]],
    model_config: Dict[str, Any],
    field_parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform IFRS 17 calculations based on measurement model and report type.
    """
    
    base_premiums = 1000000.00
    base_claims = 750000.00
    base_expenses = 150000.00
    
    # Adjust based on measurement model
    if measurement_model == 'PAA':
        # Premium Allocation Approach
        csm = base_premiums * 0.25
        lic = base_claims + base_expenses + csm
        lrc = base_premiums
    elif measurement_model == 'GMM':
        # General Measurement Model
        csm = base_premiums * 0.30
        lic = base_claims + base_expenses + csm
        lrc = base_premiums
    elif measurement_model == 'VFA':
        # Variable Fee Approach
        csm = base_premiums * 0.20
        lic = base_claims + base_expenses + csm
        lrc = base_premiums
    else:
        # Default
        csm = base_premiums * 0.25
        lic = base_claims + base_expenses + csm
        lrc = base_premiums
    
    # Adjust based on report type
    if 'lrc_movement' in report_type:
        results = {
            "premiums": base_premiums,
            "claims": base_claims,
            "expenses": base_expenses,
            "lrc": lrc,
            "csm": csm,
            "risk_adjustment": base_claims * 0.15
        }
    elif 'lic_movement' in report_type:
        results = {
            "claims": base_claims,
            "expenses": base_expenses,
            "lic": lic,
            "risk_adjustment": base_claims * 0.15
        }
    elif 'csm_rollforward' in report_type:
        results = {
            "csm": csm,
            "csm_release": csm * 0.1,
            "csm_adjustment": csm * 0.05
        }
    else:
        results = {
            "premiums": base_premiums,
            "claims": base_claims,
            "expenses": base_expenses,
            "reserves": base_claims * 0.8,
            "csm": csm,
            "risk_adjustment": base_claims * 0.15,
            "lic": lic,
            "lrc": lrc
        }
    
    return results


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            "error": "Usage: python script.py <input_file>",
            "status": "error"
        }))
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r') as f:
            engine_input = json.load(f)
        
        result = calculate_ifrs_results(engine_input)
        
        print(json.dumps(result, indent=2))
        
    except FileNotFoundError:
        print(json.dumps({
            "error": f"Input file not found: {input_file}",
            "status": "error"
        }))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "error": f"Invalid JSON in input file: {str(e)}",
            "status": "error"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "error": f"Calculation error: {str(e)}",
            "status": "error"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

        engines_data = [
            {
                'batch_type': 'custom',
                'batch_model': 'GMM',
                'insurance_type': 'direct',
                'engine_type': 'GMM Direct Calculation Engine',
                'required': True,
            },
            {
                'batch_type': 'custom',
                'batch_model': 'PAA',
                'insurance_type': 'direct',
                'engine_type': 'PAA Direct Calculation Engine',
                'required': True,
            },
            {
                'batch_type': 'custom',
                'batch_model': 'VFA',
                'insurance_type': 'direct',
                'engine_type': 'VFA Direct Calculation Engine',
                'required': True,
            },
            {
                'batch_type': 'staging',
                'batch_model': 'GMM',
                'insurance_type': 'reinsurance',
                'engine_type': 'GMM Reinsurance Calculation Engine',
                'required': True,
            },
            {
                'batch_type': 'staging',
                'batch_model': 'GMM',
                'insurance_type': 'group',
                'engine_type': 'GMM Group Calculation Engine',
                'required': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for engine_data in engines_data:
            engine, created = CalculationConfig.objects.get_or_create(
                batch_type=engine_data['batch_type'],
                batch_model=engine_data['batch_model'],
                insurance_type=engine_data['insurance_type'],
                engine_type=engine_data['engine_type'],
                defaults={
                    'required': engine_data['required'],
                }
            )

            script_filename = f"{engine_data['engine_type'].replace(' ', '_').lower()}.py"
            engine.script.save(script_filename, ContentFile(sample_engine_script.encode('utf-8')), save=True)

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created calculation engine: {engine_data["engine_type"]}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated calculation engine: {engine_data["engine_type"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {created_count + updated_count} calculation engines '
                f'({created_count} created, {updated_count} updated)'
            )
        )
