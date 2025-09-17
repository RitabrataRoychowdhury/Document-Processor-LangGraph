"""
Programmatic Calculation Validation Tests.

Comprehensive testing for programmatic calculation accuracy validating AMA table accuracy,
ROM calculations, and Combined Values Chart applications with zero LLM involvement.

Requirements tested: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch

# Core calculation imports
try:
    from src.core.calculation.impairment_calculator import (
        ImpairmentCalculator, ROMMeasurement, CalculationValidationError,
        ProgrammaticCalculationResult, CalculationStep, AMATableReference
    )
    IMPAIRMENT_CALCULATOR_AVAILABLE = True
except ImportError:
    IMPAIRMENT_CALCULATOR_AVAILABLE = False
    ImpairmentCalculator = None
    ROMMeasurement = None


class TestProgrammaticCalculationValidation:
    """Comprehensive programmatic calculation validation tests."""
    
    @pytest.fixture
    def comprehensive_ama_tables(self):
        """Comprehensive AMA tables data for testing."""
        return {
            "15-5": {
                "table_id": "15-5",
                "chapter": 15,
                "title": "Cervical Spine Range of Motion Impairment",
                "body_system": "spine",
                "method_type": "range_of_motion",
                "description": "AMA Guides 5th Edition Cervical Spine Range of Motion Impairment",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "flexion": {
                            "normal": 50,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "10": 2, "20": 5, "30": 8, "40": 12, "50": 25
                            }
                        },
                        "extension": {
                            "normal": 60,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "15": 2, "30": 5, "45": 8, "60": 25
                            }
                        },
                        "lateral_flexion": {
                            "normal": 45,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "11": 2, "22": 5, "34": 8, "45": 25
                            }
                        },
                        "rotation": {
                            "normal": 80,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "20": 2, "40": 5, "60": 8, "80": 25
                            }
                        }
                    },
                    "calculation_method": "percentage_loss_with_table_lookup"
                },
                "page_reference": 394,
                "usage_criteria": ["Cervical spine injury", "ROM limitations"],
                "validation_rules": {
                    "minimum_measurements": 3,
                    "maximum_impairment": 25,
                    "body_system_max": 25
                }
            },
            "16-3": {
                "table_id": "16-3",
                "chapter": 16,
                "title": "Upper Extremity Shoulder Range of Motion Impairment",
                "body_system": "upper_extremity",
                "method_type": "range_of_motion",
                "description": "AMA Guides 5th Edition Upper Extremity Shoulder Impairment",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "abduction": {
                            "normal": 180,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "45": 5, "90": 10, "135": 15, "180": 25
                            }
                        },
                        "forward_flexion": {
                            "normal": 180,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "45": 5, "90": 10, "135": 15, "180": 25
                            }
                        },
                        "external_rotation": {
                            "normal": 90,
                            "units": "degrees",
                            "impairment_values": {
                                "0": 0, "22": 5, "45": 10, "67": 15, "90": 25
                            }
                        }
                    },
                    "calculation_method": "upper_extremity_conversion"
                },
                "page_reference": 436,
                "conversion_factor": 0.6,  # UE to WP conversion
                "validation_rules": {
                    "minimum_measurements": 3,
                    "maximum_impairment": 60,
                    "body_system_max": 60
                }
            },
            "17-5": {
                "table_id": "17-5",
                "chapter": 17,
                "title": "Lower Extremity Knee Impairment",
                "body_system": "lower_extremity",
                "method_type": "functional_assessment",
                "description": "AMA Guides 5th Edition Lower Extremity Knee Impairment",
                "data_structure": {
                    "type": "functional_assessment",
                    "conditions": {
                        "meniscus_tear": {
                            "mild": {"impairment_range": [8, 10], "units": "percent_le"},
                            "moderate": {"impairment_range": [10, 12], "units": "percent_le"},
                            "severe": {"impairment_range": [12, 15], "units": "percent_le"}
                        },
                        "ligament_injury": {
                            "mild": {"impairment_range": [5, 8], "units": "percent_le"},
                            "moderate": {"impairment_range": [8, 15], "units": "percent_le"},
                            "severe": {"impairment_range": [15, 20], "units": "percent_le"}
                        }
                    },
                    "calculation_method": "functional_assessment_with_conversion"
                },
                "page_reference": 523,
                "conversion_factor": 0.4,  # LE to WP conversion
                "validation_rules": {
                    "maximum_impairment": 40,
                    "body_system_max": 40
                }
            },
            "COMBINED_VALUES": {
                "table_id": "COMBINED_VALUES",
                "chapter": 1,
                "title": "Combined Values Chart",
                "description": "AMA Guides Combined Values Chart for multiple impairments",
                "formula": "A + B(100-A)/100",
                "usage": "Combine multiple impairment ratings",
                "page_reference": 10,
                "validation_rules": {
                    "minimum_impairments": 2,
                    "maximum_individual": 99,
                    "maximum_combined": 100
                }
            }
        }
    
    @pytest.fixture
    def sample_rom_measurements(self):
        """Sample ROM measurements for testing."""
        return {
            "cervical_flexion": [
                ROMMeasurement("cervical_spine", "flexion", 30.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("cervical_spine", "flexion", 32.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("cervical_spine", "flexion", 28.0, datetime.now(), "Dr. Test")
            ],
            "cervical_extension": [
                ROMMeasurement("cervical_spine", "extension", 40.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("cervical_spine", "extension", 42.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("cervical_spine", "extension", 38.0, datetime.now(), "Dr. Test")
            ],
            "shoulder_abduction": [
                ROMMeasurement("right_shoulder", "abduction", 90.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("right_shoulder", "abduction", 95.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("right_shoulder", "abduction", 85.0, datetime.now(), "Dr. Test")
            ]
        }
    
    @pytest.mark.skipif(not IMPAIRMENT_CALCULATOR_AVAILABLE, reason="Impairment calculator not available")
    def test_ama_table_accuracy_validation(self, comprehensive_ama_tables):
        """
        Test AMA table accuracy and data integrity validation.
        
        Requirements: 2.1, 2.5
        """
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            # Initialize calculator
            calculator = ImpairmentCalculator(tables_file)
            
            # Verify table loading
            assert len(calculator.ama_tables) == 4, f"Expected 4 tables, loaded {len(calculator.ama_tables)}"
            
            # Test Table 15-5 accuracy
            table_15_5 = calculator.ama_tables["15-5"]
            assert table_15_5["chapter"] == 15
            assert table_15_5["body_system"] == "spine"
            
            # Verify normal ROM values
            flexion_data = table_15_5["data_structure"]["measurements"]["flexion"]
            assert flexion_data["normal"] == 50, "Incorrect normal flexion value"
            assert flexion_data["units"] == "degrees", "Incorrect units"
            
            # Test impairment value lookup
            impairment_values = flexion_data["impairment_values"]
            assert impairment_values["30"] == 8, "Incorrect impairment value for 30 degrees loss"
            assert impairment_values["50"] == 25, "Incorrect maximum impairment value"
            
            # Test Table 16-3 accuracy
            table_16_3 = calculator.ama_tables["16-3"]
            assert table_16_3["conversion_factor"] == 0.6, "Incorrect UE to WP conversion factor"
            
            # Test Table 17-5 accuracy
            table_17_5 = calculator.ama_tables["17-5"]
            assert table_17_5["conversion_factor"] == 0.4, "Incorrect LE to WP conversion factor"
            
            # Test Combined Values Chart
            combined_chart = calculator.ama_tables["COMBINED_VALUES"]
            assert combined_chart["formula"] == "A + B(100-A)/100", "Incorrect Combined Values formula"
            
            # Validate table access
            validation_results = calculator.validate_ama_table_access()
            assert validation_results["tables_file_accessible"]
            assert validation_results["has_range_of_motion_tables"]
            assert validation_results["combined_values_chart_loaded"]
            
            print("✓ AMA table accuracy validation passed")
            
        finally:
            os.unlink(tables_file)
    
    @pytest.mark.skipif(not IMPAIRMENT_CALCULATOR_AVAILABLE, reason="Impairment calculator not available")
    def test_rom_calculation_accuracy_with_known_values(self, comprehensive_ama_tables, sample_rom_measurements):
        """
        Test ROM calculation accuracy with known expected values.
        
        Requirements: 2.2, 2.3, 2.5
        """
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Test cervical flexion calculation
            cervical_flexion_measurements = sample_rom_measurements["cervical_flexion"]
            result = calculator.calculate_rom_impairment(cervical_flexion_measurements, "spine")
            
            # Verify calculation accuracy
            assert result.calculation_method == "ROM_BASED_PROGRAMMATIC"
            assert result.impairment_percentage > 0
            
            # Verify expected calculation steps
            expected_average = (30.0 + 32.0 + 28.0) / 3  # 30.0 degrees
            loss_from_normal = 50 - expected_average  # 20 degrees loss
            
            # According to Table 15-5, 20 degrees loss = 5% impairment
            expected_impairment = 5.0
            assert abs(result.impairment_percentage - expected_impairment) < 1.0, \
                f"Expected ~{expected_impairment}%, got {result.impairment_percentage}%"
            
            # Verify calculation steps documentation
            assert len(result.calculation_steps) >= 3
            step_descriptions = [step.description for step in result.calculation_steps]
            assert any("average" in desc.lower() for desc in step_descriptions)
            assert any("table lookup" in desc.lower() for desc in step_descriptions)
            
            # Verify AMA table references
            assert len(result.ama_table_references) > 0
            assert result.ama_table_references[0].table_id == "15-5"
            assert result.ama_table_references[0].chapter == 15
            
            # Test shoulder abduction calculation
            shoulder_measurements = sample_rom_measurements["shoulder_abduction"]
            shoulder_result = calculator.calculate_rom_impairment(shoulder_measurements, "upper_extremity")
            
            # Verify upper extremity calculation
            assert shoulder_result.calculation_method == "ROM_BASED_PROGRAMMATIC"
            
            # Expected: average = 90 degrees, loss = 90 degrees (50% loss)
            # According to Table 16-3, 90 degrees loss = 10% UE impairment
            # Convert to WP: 10% * 0.6 = 6% WP impairment
            expected_ue_impairment = 10.0
            expected_wp_impairment = expected_ue_impairment * 0.6  # 6.0%
            
            # The result should be in whole person terms
            assert abs(shoulder_result.impairment_percentage - expected_wp_impairment) < 2.0, \
                f"Expected ~{expected_wp_impairment}% WP, got {shoulder_result.impairment_percentage}%"
            
            print(f"✓ ROM calculation accuracy validated:")
            print(f"  Cervical flexion: {result.impairment_percentage}% (expected ~{expected_impairment}%)")
            print(f"  Shoulder abduction: {shoulder_result.impairment_percentage}% WP (expected ~{expected_wp_impairment}%)")
            
        finally:
            os.unlink(tables_file)
    
    @pytest.mark.skipif(not IMPAIRMENT_CALCULATOR_AVAILABLE, reason="Impairment calculator not available")
    def test_combined_values_chart_accuracy(self, comprehensive_ama_tables):
        """
        Test Combined Values Chart application accuracy with known combinations.
        
        Requirements: 2.4, 2.5
        """
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Test known combinations from Sample3.pdf
            # Right shoulder: 15% UE = 9% WP (15 * 0.6)
            # Cervical spine: 8% WP
            # Combined: 9 + 8(100-9)/100 = 9 + 8*91/100 = 9 + 7.28 = 16.28%
            
            impairments = [9.0, 8.0]  # Shoulder (converted to WP) + Cervical
            result = calculator.calculate_combined_impairment(impairments)
            
            # Verify calculation method
            assert result.calculation_method == "COMBINED_VALUES_PROGRAMMATIC"
            
            # Verify Combined Values Chart formula application
            expected_combined = 9 + (8 * (100 - 9)) / 100  # 16.28%
            assert abs(result.impairment_percentage - expected_combined) < 0.5, \
                f"Expected {expected_combined:.2f}%, got {result.impairment_percentage}%"
            
            # Verify calculation steps
            assert len(result.calculation_steps) >= 2
            
            # Verify AMA table reference
            assert any(ref.table_id == "COMBINED_VALUES" for ref in result.ama_table_references)
            
            # Test multiple impairment combination
            multiple_impairments = [15.0, 10.0, 5.0]
            multiple_result = calculator.calculate_combined_impairment(multiple_impairments)
            
            # Should combine sequentially: 15 + 10, then result + 5
            step1 = 15 + (10 * (100 - 15)) / 100  # 23.5%
            step2 = step1 + (5 * (100 - step1)) / 100  # ~27.3%
            
            assert abs(multiple_result.impairment_percentage - step2) < 1.0, \
                f"Multiple combination incorrect: expected ~{step2:.1f}%, got {multiple_result.impairment_percentage}%"
            
            # Test edge cases
            edge_cases = [
                ([1.0, 1.0], 1.99),  # Small values
                ([50.0, 25.0], 62.5),  # Larger values
                ([90.0, 5.0], 90.5)   # High primary value
            ]
            
            for impairments, expected in edge_cases:
                edge_result = calculator.calculate_combined_impairment(impairments)
                assert abs(edge_result.impairment_percentage - expected) < 1.0, \
                    f"Edge case {impairments} failed: expected {expected}%, got {edge_result.impairment_percentage}%"
            
            print(f"✓ Combined Values Chart accuracy validated:")
            print(f"  Basic combination: {result.impairment_percentage:.2f}% (expected {expected_combined:.2f}%)")
            print(f"  Multiple combination: {multiple_result.impairment_percentage:.2f}% (expected ~{step2:.1f}%)")
            
        finally:
            os.unlink(tables_file)
    
    @pytest.mark.skipif(not IMPAIRMENT_CALCULATOR_AVAILABLE, reason="Impairment calculator not available")
    def test_minimum_measurement_requirements(self, comprehensive_ama_tables):
        """
        Test minimum measurement requirements (3 per motion type).
        
        Requirements: 2.2
        """
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Test with insufficient measurements (only 2)
            insufficient_measurements = [
                ROMMeasurement("cervical_spine", "flexion", 30.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("cervical_spine", "flexion", 32.0, datetime.now(), "Dr. Test")
            ]
            
            with pytest.raises(CalculationValidationError) as exc_info:
                calculator.calculate_rom_impairment(insufficient_measurements, "spine")
            
            assert "Minimum 3 measurements required" in str(exc_info.value)
            
            # Test with exactly 3 measurements (should pass)
            sufficient_measurements = insufficient_measurements + [
                ROMMeasurement("cervical_spine", "flexion", 28.0, datetime.now(), "Dr. Test")
            ]
            
            result = calculator.calculate_rom_impairment(sufficient_measurements, "spine")
            assert result.calculation_method == "ROM_BASED_PROGRAMMATIC"
            assert len(result.source_measurements) == 3
            
            # Test with more than 3 measurements (should pass and use all)
            extra_measurements = sufficient_measurements + [
                ROMMeasurement("cervical_spine", "flexion", 29.0, datetime.now(), "Dr. Test"),
                ROMMeasurement("cervical_spine", "flexion", 31.0, datetime.now(), "Dr. Test")
            ]
            
            extra_result = calculator.calculate_rom_impairment(extra_measurements, "spine")
            assert len(extra_result.source_measurements) == 5
            
            print("✓ Minimum measurement requirements validated")
            
        finally:
            os.unlink(tables_file)
    
    @pytest.mark.skipif(not IMPAIRMENT_CALCULATOR_AVAILABLE, reason="Impairment calculator not available")
    def test_calculation_step_documentation(self, comprehensive_ama_tables, sample_rom_measurements):
        """
        Test comprehensive calculation step documentation and audit trails.
        
        Requirements: 2.5
        """
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Test ROM calculation documentation
            measurements = sample_rom_measurements["cervical_flexion"]
            result = calculator.calculate_rom_impairment(measurements, "spine")
            
            # Verify calculation steps are comprehensive
            assert len(result.calculation_steps) >= 3
            
            # Verify each step has required information
            for i, step in enumerate(result.calculation_steps):
                assert step.step_number == i + 1, f"Step {i+1} has incorrect step number"
                assert len(step.description) > 0, f"Step {i+1} missing description"
                assert isinstance(step.input_values, dict), f"Step {i+1} missing input values"
                assert len(step.calculation) > 0, f"Step {i+1} missing calculation formula"
                assert isinstance(step.result, (int, float)), f"Step {i+1} missing result"
                
                # Verify AMA reference if present
                if step.ama_reference:
                    assert isinstance(step.ama_reference, AMATableReference)
                    assert step.ama_reference.table_id in ["15-5", "COMBINED_VALUES"]
                    assert step.ama_reference.chapter > 0
            
            # Verify specific calculation steps
            step_descriptions = [step.description.lower() for step in result.calculation_steps]
            assert any("average" in desc for desc in step_descriptions), "Missing averaging step"
            assert any("loss" in desc or "difference" in desc for desc in step_descriptions), "Missing loss calculation step"
            assert any("table" in desc or "lookup" in desc for desc in step_descriptions), "Missing table lookup step"
            
            # Test audit trail completeness
            audit_trail = result.audit_trail
            required_audit_fields = [
                "body_system", "table_used", "measurement_groups",
                "total_measurements", "validation_passed"
            ]
            
            for field in required_audit_fields:
                assert field in audit_trail, f"Missing audit trail field: {field}"
            
            # Verify audit trail values
            assert audit_trail["body_system"] == "spine"
            assert audit_trail["table_used"] == "15-5"
            assert audit_trail["total_measurements"] == 3
            assert isinstance(audit_trail["validation_passed"], bool)
            
            # Test calculation report generation
            report = calculator.generate_calculation_report(result)
            
            # Verify report contains all required sections
            required_sections = [
                "PROGRAMMATIC IMPAIRMENT CALCULATION REPORT",
                "AMA GUIDES REFERENCES:",
                "CALCULATION STEPS:",
                "SOURCE MEASUREMENTS:",
                "VALIDATION STATUS:",
                "AUDIT TRAIL:"
            ]
            
            for section in required_sections:
                assert section in report, f"Missing report section: {section}"
            
            # Verify specific content in report
            assert f"{result.impairment_percentage}% Whole Person Impairment" in report
            assert "Table 15-5" in report
            assert "cervical_spine flexion" in report
            
            print("✓ Calculation step documentation validated")
            print(f"  Steps documented: {len(result.calculation_steps)}")
            print(f"  Audit trail fields: {len(audit_trail)}")
            print(f"  Report length: {len(report)} characters")
            
        finally:
            os.unlink(tables_file)
    
    @pytest.mark.skipif(not IMPAIRMENT_CALCULATOR_AVAILABLE, reason="Impairment calculator not available")
    def test_body_system_validation_limits(self, comprehensive_ama_tables):
        """
        Test body system specific validation and maximum impairment limits.
        
        Requirements: 2.5
        """
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Test spine system validation (max 25% WP)
            spine_validation_cases = [
                (20.0, True),   # Within limit
                (25.0, True),   # At limit
                (30.0, False)   # Exceeds limit
            ]
            
            for impairment, should_pass in spine_validation_cases:
                validation = calculator._validate_calculation_result(impairment, "spine")
                assert validation["within_body_system_max"] == should_pass, \
                    f"Spine validation failed for {impairment}%: expected {should_pass}"
            
            # Test upper extremity validation (max 60% UE, 36% WP)
            ue_validation_cases = [
                (50.0, True),   # Within UE limit
                (60.0, True),   # At UE limit
                (70.0, False)   # Exceeds UE limit
            ]
            
            for impairment, should_pass in ue_validation_cases:
                validation = calculator._validate_calculation_result(impairment, "upper_extremity")
                assert validation["within_body_system_max"] == should_pass, \
                    f"UE validation failed for {impairment}%: expected {should_pass}"
            
            # Test lower extremity validation (max 40% LE, 16% WP)
            le_validation_cases = [
                (30.0, True),   # Within LE limit
                (40.0, True),   # At LE limit
                (50.0, False)   # Exceeds LE limit
            ]
            
            for impairment, should_pass in le_validation_cases:
                validation = calculator._validate_calculation_result(impairment, "lower_extremity")
                assert validation["within_body_system_max"] == should_pass, \
                    f"LE validation failed for {impairment}%: expected {should_pass}"
            
            # Test combined impairment validation (max 100%)
            combined_validation_cases = [
                ([50.0, 30.0], True),   # Reasonable combination
                ([90.0, 15.0], True),   # High but valid combination
                ([95.0, 10.0], True)    # Very high but mathematically valid
            ]
            
            for impairments, should_pass in combined_validation_cases:
                try:
                    result = calculator.calculate_combined_impairment(impairments)
                    validation_passed = result.validation_status["combination_valid"]
                    assert validation_passed == should_pass, \
                        f"Combined validation failed for {impairments}: expected {should_pass}"
                except CalculationValidationError:
                    assert not should_pass, f"Unexpected validation error for {impairments}"
            
            print("✓ Body system validation limits tested")
            
        finally:
            os.unlink(tables_file)
    
    def test_calculation_performance_benchmarks(self, comprehensive_ama_tables):
        """Test calculation performance with large datasets."""
        if not IMPAIRMENT_CALCULATOR_AVAILABLE:
            pytest.skip("Impairment calculator not available")
        
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Create large measurement dataset
            large_measurements = []
            for i in range(100):  # 100 measurements
                large_measurements.append(
                    ROMMeasurement("cervical_spine", "flexion", 30.0 + i % 10, datetime.now(), f"Dr. Test {i}")
                )
            
            import time
            start_time = time.time()
            
            # Should handle large datasets efficiently
            result = calculator.calculate_rom_impairment(large_measurements, "spine")
            
            calculation_time = time.time() - start_time
            
            # Should complete within reasonable time
            assert calculation_time < 5.0, f"Calculation took {calculation_time:.2f}s, too slow"
            
            # Should maintain accuracy
            assert result.calculation_method == "ROM_BASED_PROGRAMMATIC"
            assert len(result.source_measurements) == 100
            
            print(f"Performance test: {calculation_time:.3f}s for 100 measurements")
            
        finally:
            os.unlink(tables_file)
    
    def test_zero_llm_involvement_verification(self, comprehensive_ama_tables, sample_rom_measurements):
        """Verify zero LLM involvement in calculations."""
        if not IMPAIRMENT_CALCULATOR_AVAILABLE:
            pytest.skip("Impairment calculator not available")
        
        # Create temporary AMA tables file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(comprehensive_ama_tables, f)
            tables_file = f.name
        
        try:
            calculator = ImpairmentCalculator(tables_file)
            
            # Mock any potential LLM calls to ensure they're not made
            with patch('openai.ChatCompletion.create') as mock_openai, \
                 patch('anthropic.Anthropic') as mock_anthropic, \
                 patch('google.generativeai.GenerativeModel') as mock_gemini:
                
                # Execute calculations
                measurements = sample_rom_measurements["cervical_flexion"]
                result = calculator.calculate_rom_impairment(measurements, "spine")
                
                # Verify no LLM calls were made
                assert not mock_openai.called, "OpenAI API was called during calculation"
                assert not mock_anthropic.called, "Anthropic API was called during calculation"
                assert not mock_gemini.called, "Gemini API was called during calculation"
                
                # Verify calculation is purely programmatic
                assert result.calculation_method == "ROM_BASED_PROGRAMMATIC"
                assert all("PROGRAMMATIC" in step.calculation for step in result.calculation_steps)
                
                # Test combined calculation
                combined_result = calculator.calculate_combined_impairment([15.0, 8.0])
                
                # Verify no LLM calls for combined calculation
                assert not mock_openai.called, "OpenAI API was called during combined calculation"
                assert not mock_anthropic.called, "Anthropic API was called during combined calculation"
                assert not mock_gemini.called, "Gemini API was called during combined calculation"
                
                assert combined_result.calculation_method == "COMBINED_VALUES_PROGRAMMATIC"
            
            print("✓ Zero LLM involvement verified")
            
        finally:
            os.unlink(tables_file)


if __name__ == "__main__":
    # Run programmatic calculation validation tests
    print("Running Programmatic Calculation Validation Tests...")
    
    if not IMPAIRMENT_CALCULATOR_AVAILABLE:
        print("⚠️  Impairment calculator not available")
        exit(1)
    
    # Create test AMA tables
    test_tables = {
        "15-5": {
            "table_id": "15-5",
            "chapter": 15,
            "title": "Cervical Spine Range of Motion",
            "body_system": "spine",
            "data_structure": {
                "measurements": {
                    "flexion": {"normal": 50, "units": "degrees"}
                }
            }
        }
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_tables, f)
        tables_file = f.name
    
    try:
        # Test basic functionality
        calculator = ImpairmentCalculator(tables_file)
        
        # Test ROM calculation
        measurements = [
            ROMMeasurement("cervical_spine", "flexion", 30.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "flexion", 32.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "flexion", 28.0, datetime.now(), "Dr. Test")
        ]
        
        result = calculator.calculate_rom_impairment(measurements, "spine")
        
        print(f"✓ Basic ROM calculation: {result.impairment_percentage}%")
        print(f"✓ Calculation method: {result.calculation_method}")
        print(f"✓ Steps documented: {len(result.calculation_steps)}")
        
        # Test combined calculation
        combined_result = calculator.calculate_combined_impairment([10.0, 5.0])
        print(f"✓ Combined calculation: {combined_result.impairment_percentage}%")
        
    finally:
        os.unlink(tables_file)
    
    print("✓ Programmatic Calculation Validation Tests Ready")