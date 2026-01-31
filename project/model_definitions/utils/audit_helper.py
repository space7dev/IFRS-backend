"""
Helper functions for creating audit trail records
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from model_definitions.models import (
    CalculationValue,
    AssumptionReference,
    InputDataReference,
    IFRSEngineResult
)


def create_calculation_value(
    value_id: str,
    run_id: str,
    report_type: str,
    engine_result: IFRSEngineResult,
    value: float,
    label: str,
    period: str,
    legal_entity: str,
    currency: str,
    calculation_method: str = 'PAA',
    unit: str = 'currency',
    line_of_business: Optional[str] = None,
    cohort: Optional[str] = None,
    group_id: Optional[str] = None,
    formula_human_readable: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    notes: Optional[str] = None,
    is_missing_data: bool = False,
    is_override: bool = False,
    is_fallback: bool = False,
    has_rounding: bool = False,
    calc_engine_version: str = '1.0.0'
) -> CalculationValue:
    calc_value = CalculationValue.objects.create(
        value_id=value_id,
        run_id=run_id,
        report_type=report_type,
        period=period,
        legal_entity=legal_entity,
        currency=currency,
        label=label,
        value=value,
        unit=unit,
        line_of_business=line_of_business,
        cohort=cohort,
        group_id=group_id,
        formula_human_readable=formula_human_readable,
        dependencies=dependencies or [],
        calculation_method=calculation_method,
        notes=notes,
        is_missing_data=is_missing_data,
        is_override=is_override,
        is_fallback=is_fallback,
        has_rounding=has_rounding,
        calc_engine_version=calc_engine_version,
        engine_result=engine_result
    )
    
    return calc_value


def add_assumption_reference(
    calc_value: CalculationValue,
    assumption_type: str,
    assumption_id: str,
    assumption_version: str,
    effective_date: date,
    metadata: Optional[Dict[str, Any]] = None
) -> AssumptionReference:
    return AssumptionReference.objects.create(
        calculation_value=calc_value,
        assumption_type=assumption_type,
        assumption_id=assumption_id,
        assumption_version=assumption_version,
        effective_date=effective_date,
        metadata=metadata or {}
    )


def add_input_data_reference(
    calc_value: CalculationValue,
    dataset_name: str,
    source_snapshot_id: str,
    record_count: int = 0,
    source_hash: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> InputDataReference:
    return InputDataReference.objects.create(
        calculation_value=calc_value,
        dataset_name=dataset_name,
        source_snapshot_id=source_snapshot_id,
        source_hash=source_hash,
        record_count=record_count,
        metadata=metadata or {}
    )


def populate_disclosure_report_audit_trail(
    engine_result: IFRSEngineResult,
    calculations: Dict[str, Any],
    metadata: Dict[str, Any],
    run_id: str,
    calc_engine_version: str = '1.0.0'
) -> int:
    count = 0
    period = f"{metadata.get('year', '')} {metadata.get('quarter', '')}"
    legal_entity = metadata.get('legal_entity_name', 'Unknown')
    currency = metadata.get('currency_name', 'USD')
    
    for key, calc_data in calculations.items():
        value_id = calc_data.get('value_id')
        amount = calc_data.get('amount', 0)
        
        if not value_id:
            continue
        
        label = value_id.replace('_', ' ').replace('.', ' - ')
        
        formula = calc_data.get('formula', None)
        dependencies = calc_data.get('dependencies', [])
        method = calc_data.get('method', 'PAA')
        notes = calc_data.get('notes', None)
        
        flags = calc_data.get('flags', {})
        
        calc_value = create_calculation_value(
            value_id=value_id,
            run_id=run_id,
            report_type='disclosure_report',
            engine_result=engine_result,
            value=float(amount),
            label=label,
            period=period,
            legal_entity=legal_entity,
            currency=currency,
            calculation_method=method,
            formula_human_readable=formula,
            dependencies=dependencies,
            notes=notes,
            is_missing_data=flags.get('is_missing_data', False),
            is_override=flags.get('is_override', False),
            is_fallback=flags.get('is_fallback', False),
            has_rounding=flags.get('has_rounding', False),
            calc_engine_version=calc_engine_version
        )
        
        assumptions = calc_data.get('assumptions', {})
        for assumption_type, assumption_data in assumptions.items():
            if isinstance(assumption_data, dict):
                add_assumption_reference(
                    calc_value=calc_value,
                    assumption_type=assumption_type,
                    assumption_id=assumption_data.get('id', 'unknown'),
                    assumption_version=assumption_data.get('version', '1.0'),
                    effective_date=datetime.now().date(),
                    metadata=assumption_data
                )
        
        inputs = calc_data.get('inputs', {})
        if inputs:
            dataset_name = inputs.get('dataset', 'Unknown')
            snapshot_id = inputs.get('snapshot_id', 'SNAP_DEFAULT')
            record_count = inputs.get('record_count', 0)
            
            add_input_data_reference(
                calc_value=calc_value,
                dataset_name=dataset_name,
                source_snapshot_id=snapshot_id,
                record_count=record_count,
                metadata=inputs
            )
        
        count += 1
    
    return count
