import json
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IFRSEngine:
    def __init__(self, input_data: Dict[str, Any]):
        self.input_data = input_data
        self.run_id = input_data.get('run_id')
        self.model_definition = input_data.get('model_definition', {})
        self.batch_data = input_data.get('batch_data', [])
        self.field_parameters = input_data.get('field_parameters', {})
        self.current_batch = input_data.get('current_batch', {})
        self.current_lob = input_data.get('current_lob', {})
        self.current_report_type = input_data.get('current_report_type', {})
        
        logger.info(f"Initializing IFRS Engine for Run ID: {self.run_id}")
    
    def validate_inputs(self) -> bool:
        required_fields = ['run_id', 'model_definition', 'batch_data', 'field_parameters']
        for field in required_fields:
            if field not in self.input_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        if not self.batch_data:
            logger.error("No batch data provided")
            return False
        
        return True
    
    def extract_model_config(self) -> Dict[str, Any]:
        config = self.model_definition.get('config', {})
        
        general_info = config.get('generalInfo', {})
        projection_assumptions = config.get('projectionAssumptions', {})
        risk_adjustment = config.get('riskAdjustment', {})
        discount_rates = config.get('discountRates', {})
        accounting_rules = config.get('accountingRules', {})
        actuarial_rules = config.get('actuarialRules', {})
        
        return {
            'general_info': general_info,
            'projection_assumptions': projection_assumptions,
            'risk_adjustment': risk_adjustment,
            'discount_rates': discount_rates,
            'accounting_rules': accounting_rules,
            'actuarial_rules': actuarial_rules,
        }
    
    def process_batch_data(self) -> Dict[str, Any]:
        processed_data = {
            'premiums': 0.0,
            'claims': 0.0,
            'expenses': 0.0,
            'commissions': 0.0,
            'manual_data': 0.0,
            'upload_count': 0,
        }
        
        for batch in self.batch_data:
            if batch['id'] == self.current_batch['id']:
                for upload in batch.get('uploads', []):
                    processed_data['upload_count'] += 1
                    
                    data_type = upload.get('data_type', '')
                    if data_type == 'premiums':
                        processed_data['premiums'] += 1000000.0
                    elif data_type == 'claims_paid':
                        processed_data['claims'] += 750000.0
                    elif data_type == 'expense':
                        processed_data['expenses'] += 150000.0
                    elif data_type == 'commissions_paid':
                        processed_data['commissions'] += 100000.0
                    elif data_type == 'manual_data':
                        processed_data['manual_data'] += 50000.0
        
        return processed_data
    
    def calculate_ifrs_17_metrics(self, model_config: Dict[str, Any], batch_data: Dict[str, Any]) -> Dict[str, Any]:
        model_type = self.field_parameters.get('model_type', 'GMM')
        
        premiums = batch_data.get('premiums', 0.0)
        claims = batch_data.get('claims', 0.0)
        expenses = batch_data.get('expenses', 0.0)
        
        if model_type == 'GMM':
            fulfillment_cash_flows = claims + expenses
            risk_adjustment = fulfillment_cash_flows * 0.1
            discount_rate = 0.05
            present_value = fulfillment_cash_flows / (1 + discount_rate)
            
            expected_cash_flows = premiums - fulfillment_cash_flows
            csm = max(0, expected_cash_flows - risk_adjustment)
            
        elif model_type == 'PAA':
            fulfillment_cash_flows = claims + expenses
            risk_adjustment = fulfillment_cash_flows * 0.05
            present_value = fulfillment_cash_flows
            csm = max(0, premiums - fulfillment_cash_flows - risk_adjustment)
            
        elif model_type == 'VFA':
            fulfillment_cash_flows = claims + expenses
            risk_adjustment = fulfillment_cash_flows * 0.15
            discount_rate = 0.06
            present_value = fulfillment_cash_flows / (1 + discount_rate)
            csm = max(0, premiums - fulfillment_cash_flows - risk_adjustment)
            
        else:
            fulfillment_cash_flows = claims + expenses
            risk_adjustment = fulfillment_cash_flows * 0.1
            present_value = fulfillment_cash_flows
            csm = max(0, premiums - fulfillment_cash_flows - risk_adjustment)
        
        return {
            'model_type': model_type,
            'premiums': premiums,
            'claims': claims,
            'expenses': expenses,
            'fulfillment_cash_flows': fulfillment_cash_flows,
            'risk_adjustment': risk_adjustment,
            'present_value': present_value,
            'contractual_service_margin': csm,
            'liability_for_remaining_coverage': present_value + risk_adjustment - csm,
            'liability_for_incurred_claims': claims,
        }
    
    def generate_report(self, calculations: Dict[str, Any]) -> Dict[str, Any]:
        report_type = self.current_report_type.get('report_type', '')
        
        base_report = {
            'run_id': self.run_id,
            'batch_id': self.current_batch.get('batch_id'),
            'lob': self.current_lob.get('line_of_business'),
            'report_type': report_type,
            'year': self.field_parameters.get('year', self.current_batch.get('batch_year')),
            'quarter': self.field_parameters.get('quarter', self.current_batch.get('batch_quarter')),
            'currency': self.current_lob.get('currency'),
            'calculation_date': datetime.now().isoformat(),
            'model_type': self.field_parameters.get('model_type'),
            'calculations': calculations,
        }
        
        if 'lrc_movement' in report_type.lower():
            base_report['report_section'] = 'Liability for Remaining Coverage Movement'
            base_report['movement_details'] = {
                'opening_balance': calculations.get('liability_for_remaining_coverage', 0) * 0.9,
                'new_business': calculations.get('liability_for_remaining_coverage', 0) * 0.1,
                'changes_in_fulfillment_cash_flows': 0,
                'changes_in_risk_adjustment': 0,
                'changes_in_discount_rate': 0,
                'csm_release': calculations.get('contractual_service_margin', 0) * 0.1,
                'closing_balance': calculations.get('liability_for_remaining_coverage', 0),
            }
        elif 'lic_movement' in report_type.lower():
            base_report['report_section'] = 'Liability for Incurred Claims Movement'
            base_report['movement_details'] = {
                'opening_balance': calculations.get('liability_for_incurred_claims', 0) * 0.8,
                'new_claims': calculations.get('liability_for_incurred_claims', 0) * 0.2,
                'changes_in_fulfillment_cash_flows': 0,
                'changes_in_risk_adjustment': 0,
                'changes_in_discount_rate': 0,
                'closing_balance': calculations.get('liability_for_incurred_claims', 0),
            }
        elif 'csm_rollforward' in report_type.lower():
            base_report['report_section'] = 'CSM Rollforward'
            base_report['csm_movement'] = {
                'opening_csm': calculations.get('contractual_service_margin', 0) * 0.9,
                'new_business_csm': calculations.get('contractual_service_margin', 0) * 0.1,
                'csm_adjustments': 0,
                'csm_release': calculations.get('contractual_service_margin', 0) * 0.1,
                'closing_csm': calculations.get('contractual_service_margin', 0),
            }
        else:
            base_report['report_section'] = 'General Report'
            base_report['summary'] = {
                'total_premiums': calculations.get('premiums', 0),
                'total_claims': calculations.get('claims', 0),
                'total_expenses': calculations.get('expenses', 0),
                'net_result': calculations.get('premiums', 0) - calculations.get('claims', 0) - calculations.get('expenses', 0),
            }
        
        return base_report
    
    def execute(self) -> Dict[str, Any]:
        try:
            logger.info(f"Starting IFRS Engine execution for Run ID: {self.run_id}")
            
            if not self.validate_inputs():
                return {
                    'error': 'Invalid input data',
                    'run_id': self.run_id
                }
            
            model_config = self.extract_model_config()
            logger.info("Model configuration extracted successfully")
            
            batch_data = self.process_batch_data()
            logger.info(f"Processed {batch_data['upload_count']} uploads")
            
            calculations = self.calculate_ifrs_17_metrics(model_config, batch_data)
            logger.info("IFRS 17 calculations completed")
            
            result = self.generate_report(calculations)
            logger.info(f"Report generated successfully for {result['report_type']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in IFRS Engine execution: {str(e)}")
            return {
                'error': f'Engine execution failed: {str(e)}',
                'run_id': self.run_id
            }


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            'error': 'Usage: python ifrs_engine.py <input_json_file>'
        }))
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r') as f:
            input_data = json.load(f)
        
        engine = IFRSEngine(input_data)
        result = engine.execute()
        
        print(json.dumps(result, indent=2))
        
        if 'error' in result:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except FileNotFoundError:
        print(json.dumps({
            'error': f'Input file not found: {input_file}'
        }))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({
            'error': f'Invalid JSON in input file: {str(e)}'
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            'error': f'Unexpected error: {str(e)}'
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
