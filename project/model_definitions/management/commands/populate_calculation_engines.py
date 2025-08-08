from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from model_definitions.models import CalculationConfig
import os


class Command(BaseCommand):
    help = 'Populate sample calculation engines for testing'

    def handle(self, *args, **options):
        sample_engine_script = '''
import json
import sys
import datetime
from typing import Dict, Any, List


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
