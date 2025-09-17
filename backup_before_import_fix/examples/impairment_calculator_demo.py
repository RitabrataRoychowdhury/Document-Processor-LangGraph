"""
Demonstration of Programmatic Impairment Calculator.

This demo shows how to use the impairment calculator with AMA tables
for ROM-based and combined impairment calculations.
"""

from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.services.impairment_calculator import (
        ImpairmentCalculator, ROMMeasurement, CalculationValidationError
    )
except ImportError:
    from services.impairment_calculator import (
        ImpairmentCalculator, ROMMeasurement, CalculationValidationError
    )


def demonstrate_rom_calculation():
    """Demonstrate ROM-based impairment calculation."""
    print("=" * 60)
    print("ROM-BASED IMPAIRMENT CALCULATION DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Initialize calculator with existing AMA tables
        calculator = ImpairmentCalculator()
        
        # Create sample ROM measurements (minimum 3 per motion type)
        cervical_flexion_measurements = [
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=30.0,
                measurement_date=datetime(2024, 1, 15),
                examiner="Dr. Smith",
                notes="Patient reports pain at end range"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=32.0,
                measurement_date=datetime(2024, 1, 15),
                examiner="Dr. Smith",
                notes="Consistent measurement"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=28.0,
                measurement_date=datetime(2024, 1, 15),
                examiner="Dr. Smith",
                notes="Slight variation due to guarding"
            )
        ]
        
        cervical_extension_measurements = [
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="extension",
                measured_degrees=40.0,
                measurement_date=datetime(2024, 1, 15),
                examiner="Dr. Smith",
                notes="Limited by pain"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="extension",
                measured_degrees=42.0,
                measurement_date=datetime(2024, 1, 15),
                examiner="Dr. Smith",
                notes="Consistent with first measurement"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="extension",
                measured_degrees=38.0,
                measurement_date=datetime(2024, 1, 15),
                examiner="Dr. Smith",
                notes="Patient cooperation good"
            )
        ]
        
        all_measurements = cervical_flexion_measurements + cervical_extension_measurements
        
        print(f"Input: {len(all_measurements)} ROM measurements")
        print("Measurements:")
        for i, measurement in enumerate(all_measurements, 1):
            print(f"  {i}. {measurement.joint} {measurement.motion_type}: {measurement.measured_degrees}°")
        
        # Calculate ROM impairment
        result = calculator.calculate_rom_impairment(all_measurements, "spine")
        
        print(f"\nResult: {result.impairment_percentage}% whole person impairment")
        print(f"Calculation Method: {result.calculation_method}")
        print(f"Generated: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show AMA table references
        print("\nAMA Table References:")
        for ref in result.ama_table_references:
            print(f"  • Table {ref.table_id}: {ref.title}")
            print(f"    Chapter {ref.chapter}, Page {ref.page_reference}")
        
        # Show calculation steps
        print("\nCalculation Steps:")
        for step in result.calculation_steps:
            print(f"  {step.step_number}. {step.description}")
            print(f"     Calculation: {step.calculation}")
            print(f"     Result: {step.result}")
            if step.notes:
                print(f"     Notes: {step.notes}")
        
        # Show validation status
        print("\nValidation Status:")
        for check, passed in result.validation_status.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {check}: {status}")
        
        return result
        
    except CalculationValidationError as e:
        print(f"Calculation Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None


def demonstrate_combined_calculation():
    """Demonstrate combined impairment calculation."""
    print("\n" + "=" * 60)
    print("COMBINED IMPAIRMENT CALCULATION DEMONSTRATION")
    print("=" * 60)
    
    try:
        calculator = ImpairmentCalculator()
        
        # Sample individual impairments from different sources
        individual_impairments = [
            15.0,  # ROM impairment
            8.0,   # Strength impairment
            5.0,   # Sensory impairment
            3.0    # Additional functional limitation
        ]
        
        print(f"Input: {len(individual_impairments)} individual impairments")
        print("Individual Impairments:")
        sources = ["ROM limitation", "Strength deficit", "Sensory loss", "Functional limitation"]
        for i, (impairment, source) in enumerate(zip(individual_impairments, sources), 1):
            print(f"  {i}. {source}: {impairment}%")
        
        # Calculate combined impairment
        result = calculator.calculate_combined_impairment(individual_impairments)
        
        print(f"\nResult: {result.impairment_percentage}% whole person impairment")
        print(f"Calculation Method: {result.calculation_method}")
        
        # Show calculation steps
        print("\nCombination Steps:")
        for step in result.calculation_steps:
            print(f"  {step.step_number}. {step.description}")
            print(f"     Calculation: {step.calculation}")
            print(f"     Result: {step.result}%")
        
        # Show audit trail
        print("\nAudit Trail:")
        for key, value in result.audit_trail.items():
            print(f"  {key}: {value}")
        
        return result
        
    except CalculationValidationError as e:
        print(f"Calculation Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None


def demonstrate_table_validation():
    """Demonstrate AMA table validation."""
    print("\n" + "=" * 60)
    print("AMA TABLE VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    try:
        calculator = ImpairmentCalculator()
        
        # Validate table access
        validation_results = calculator.validate_ama_table_access()
        
        print("Table Validation Results:")
        for check, passed in validation_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {check}: {status}")
        
        # Show available tables
        print(f"\nAvailable AMA Tables ({len(calculator.ama_tables)}):")
        for table_id, table_data in calculator.ama_tables.items():
            print(f"  • Table {table_id}: {table_data.get('title', 'Unknown')}")
            print(f"    Body System: {table_data.get('body_system', 'Unknown')}")
            print(f"    Method: {table_data.get('method_type', 'Unknown')}")
            print(f"    Page: {table_data.get('page_reference', 'Unknown')}")
        
        return validation_results
        
    except Exception as e:
        print(f"Validation Error: {e}")
        return None


def demonstrate_calculation_report():
    """Demonstrate calculation report generation."""
    print("\n" + "=" * 60)
    print("CALCULATION REPORT DEMONSTRATION")
    print("=" * 60)
    
    try:
        calculator = ImpairmentCalculator()
        
        # Create simple measurements for report
        measurements = [
            ROMMeasurement("cervical_spine", "flexion", 35.0, datetime.now(), "Dr. Demo"),
            ROMMeasurement("cervical_spine", "flexion", 33.0, datetime.now(), "Dr. Demo"),
            ROMMeasurement("cervical_spine", "flexion", 37.0, datetime.now(), "Dr. Demo")
        ]
        
        # Calculate impairment
        result = calculator.calculate_rom_impairment(measurements, "spine")
        
        # Generate detailed report
        report = calculator.generate_calculation_report(result)
        
        print("Generated Calculation Report:")
        print("-" * 40)
        print(report)
        
        return report
        
    except Exception as e:
        print(f"Report Generation Error: {e}")
        return None


def main():
    """Run all demonstrations."""
    print("PROGRAMMATIC IMPAIRMENT CALCULATOR DEMONSTRATION")
    print("AMA Guides 5th Edition - Zero LLM Involvement")
    print("=" * 80)
    
    # Run demonstrations
    rom_result = demonstrate_rom_calculation()
    combined_result = demonstrate_combined_calculation()
    validation_result = demonstrate_table_validation()
    report = demonstrate_calculation_report()
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMONSTRATION SUMMARY")
    print("=" * 60)
    
    if rom_result:
        print(f"✓ ROM Calculation: {rom_result.impairment_percentage}% impairment")
    else:
        print("✗ ROM Calculation: Failed")
    
    if combined_result:
        print(f"✓ Combined Calculation: {combined_result.impairment_percentage}% impairment")
    else:
        print("✗ Combined Calculation: Failed")
    
    if validation_result:
        passed_checks = sum(1 for v in validation_result.values() if v)
        total_checks = len(validation_result)
        print(f"✓ Table Validation: {passed_checks}/{total_checks} checks passed")
    else:
        print("✗ Table Validation: Failed")
    
    if report:
        print("✓ Report Generation: Successful")
    else:
        print("✗ Report Generation: Failed")
    
    print("\nAll calculations performed programmatically with zero LLM involvement.")
    print("Complete audit trails and AMA table citations provided for all results.")


if __name__ == "__main__":
    main()