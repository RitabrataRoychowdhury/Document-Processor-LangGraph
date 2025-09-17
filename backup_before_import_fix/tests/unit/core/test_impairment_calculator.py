"""
Unit tests for Programmatic Impairment Calculator.

Tests all calculation methods with known expected values and validates
AMA table-based calculations with zero LLM involvement.
"""

import unittest
from datetime import datetime
from unittest.mock import patch, mock_open
import json
import tempfile
import os

try:
    from src.services.impairment_calculator import (
        ImpairmentCalculator, ROMMeasurement, CalculationValidationError,
        ProgrammaticCalculationResult, CalculationStep, AMATableReference
    )
except ImportError:
    from services.impairment_calculator import (
        ImpairmentCalculator, ROMMeasurement, CalculationValidationError,
        ProgrammaticCalculationResult, CalculationStep, AMATableReference
    )


class TestImpairmentCalculator(unittest.TestCase):
    """Test cases for ImpairmentCalculator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test AMA tables data
        self.test_ama_tables = {
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
                            "units": "degrees"
                        },
                        "extension": {
                            "normal": 60,
                            "units": "degrees"
                        },
                        "lateral_flexion": {
                            "normal": 45,
                            "units": "degrees"
                        },
                        "rotation": {
                            "normal": 80,
                            "units": "degrees"
                        }
                    },
                    "calculation_method": "percentage_loss"
                },
                "page_reference": 394,
                "usage_criteria": [
                    "Cervical spine injury",
                    "ROM limitations"
                ],
                "calculation_steps": [
                    "Measure ROM",
                    "Calculate loss",
                    "Apply table values"
                ]
            },
            "15-7": {
                "table_id": "15-7",
                "chapter": 15,
                "title": "Lumbar Spine Range of Motion Impairment",
                "body_system": "spine",
                "method_type": "range_of_motion",
                "description": "AMA Guides 5th Edition Lumbar Spine Range of Motion Impairment",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "flexion": {
                            "normal": 60,
                            "units": "degrees"
                        },
                        "extension": {
                            "normal": 25,
                            "units": "degrees"
                        }
                    },
                    "calculation_method": "ankylosis_model"
                },
                "page_reference": 399,
                "usage_criteria": [
                    "Lumbar spine injury",
                    "ROM limitations"
                ],
                "calculation_steps": [
                    "Measure flexion/extension",
                    "Calculate impairment",
                    "Apply modifiers"
                ]
            }
        }
        
        # Create temporary file with test data
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(self.test_ama_tables, self.temp_file)
        self.temp_file.close()
        
        # Initialize calculator with test data
        self.calculator = ImpairmentCalculator(self.temp_file.name)
        
        # Create test ROM measurements
        self.test_measurements = [
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=30.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=32.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=28.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)
    
    def test_calculator_initialization(self):
        """Test calculator initialization with AMA tables."""
        self.assertIsInstance(self.calculator, ImpairmentCalculator)
        self.assertEqual(len(self.calculator.ama_tables), 2)
        self.assertIn("15-5", self.calculator.ama_tables)
        self.assertIn("15-7", self.calculator.ama_tables)
    
    def test_invalid_ama_tables_file(self):
        """Test handling of invalid AMA tables file."""
        with self.assertRaises(CalculationValidationError):
            ImpairmentCalculator("nonexistent_file.json")
    
    def test_rom_measurement_validation(self):
        """Test ROM measurement validation."""
        # Valid measurement
        measurement = ROMMeasurement(
            joint="cervical_spine",
            motion_type="flexion",
            measured_degrees=45.0,
            measurement_date=datetime.now(),
            examiner="Dr. Test"
        )
        self.assertEqual(measurement.measured_degrees, 45.0)
        
        # Invalid measurement - negative degrees
        with self.assertRaises(CalculationValidationError):
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="flexion",
                measured_degrees=-10.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            )
        
        # Invalid measurement - missing joint
        with self.assertRaises(CalculationValidationError):
            ROMMeasurement(
                joint="",
                motion_type="flexion",
                measured_degrees=45.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            )
    
    def test_minimum_measurements_validation(self):
        """Test minimum measurements requirement (3 per motion type)."""
        # Test with insufficient measurements
        insufficient_measurements = self.test_measurements[:2]  # Only 2 measurements
        
        with self.assertRaises(CalculationValidationError) as context:
            self.calculator.calculate_rom_impairment(insufficient_measurements, "spine")
        
        self.assertIn("Minimum 3 measurements required", str(context.exception))
    
    def test_rom_impairment_calculation(self):
        """Test ROM impairment calculation with valid measurements."""
        result = self.calculator.calculate_rom_impairment(self.test_measurements, "spine")
        
        # Verify result structure
        self.assertIsInstance(result, ProgrammaticCalculationResult)
        self.assertGreater(result.impairment_percentage, 0)
        self.assertEqual(len(result.source_measurements), 3)
        self.assertEqual(result.calculation_method, "ROM_BASED_PROGRAMMATIC")
        
        # Verify calculation steps are documented
        self.assertGreater(len(result.calculation_steps), 0)
        
        # Verify AMA table references
        self.assertGreater(len(result.ama_table_references), 0)
        self.assertEqual(result.ama_table_references[0].table_id, "15-5")
        
        # Verify validation status
        self.assertIn("result_in_range", result.validation_status)
        self.assertTrue(result.validation_status["result_in_range"])
    
    def test_rom_average_calculation(self):
        """Test ROM average calculation."""
        average = self.calculator._calculate_rom_average(self.test_measurements)
        expected_average = (30.0 + 32.0 + 28.0) / 3
        self.assertEqual(average, expected_average)
    
    def test_combined_impairment_calculation(self):
        """Test combined impairment calculation using Combined Values Chart."""
        impairments = [15.0, 10.0, 5.0]
        result = self.calculator.calculate_combined_impairment(impairments)
        
        # Verify result structure
        self.assertIsInstance(result, ProgrammaticCalculationResult)
        self.assertGreater(result.impairment_percentage, max(impairments))
        self.assertEqual(result.calculation_method, "COMBINED_VALUES_PROGRAMMATIC")
        
        # Verify calculation steps show combination process
        self.assertGreater(len(result.calculation_steps), 1)
        
        # Verify AMA table reference for Combined Values Chart
        self.assertEqual(result.ama_table_references[0].table_id, "COMBINED_VALUES")
        
        # Verify validation
        self.assertTrue(result.validation_status["combination_valid"])
    
    def test_combined_impairment_validation(self):
        """Test combined impairment validation."""
        # Test with insufficient impairments
        with self.assertRaises(CalculationValidationError):
            self.calculator.calculate_combined_impairment([15.0])  # Only 1 impairment
        
        # Test with invalid impairment values
        with self.assertRaises(CalculationValidationError):
            self.calculator.calculate_combined_impairment([15.0, 105.0])  # >100%
        
        with self.assertRaises(CalculationValidationError):
            self.calculator.calculate_combined_impairment([15.0, -5.0])  # Negative
    
    def test_combined_values_chart_formula(self):
        """Test AMA Combined Values Chart formula application."""
        # Test known combinations
        result_1 = self.calculator._apply_combined_values_chart(10.0, 5.0)
        expected_1 = 10 + (5 * (100 - 10)) / 100  # 14.5
        self.assertAlmostEqual(result_1, expected_1, places=1)
        
        result_2 = self.calculator._apply_combined_values_chart(20.0, 15.0)
        expected_2 = 20 + (15 * (100 - 20)) / 100  # 32.0
        self.assertAlmostEqual(result_2, expected_2, places=1)
    
    def test_measurement_grouping(self):
        """Test grouping of measurements by joint and motion type."""
        # Add measurements for different motions
        mixed_measurements = self.test_measurements + [
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="extension",
                measured_degrees=40.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="extension",
                measured_degrees=42.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            ),
            ROMMeasurement(
                joint="cervical_spine",
                motion_type="extension",
                measured_degrees=38.0,
                measurement_date=datetime.now(),
                examiner="Dr. Test"
            )
        ]
        
        grouped = self.calculator._group_measurements(mixed_measurements)
        
        self.assertEqual(len(grouped), 2)  # flexion and extension
        self.assertIn("cervical_spine_flexion", grouped)
        self.assertIn("cervical_spine_extension", grouped)
        self.assertEqual(len(grouped["cervical_spine_flexion"]), 3)
        self.assertEqual(len(grouped["cervical_spine_extension"]), 3)
    
    def test_ama_table_validation(self):
        """Test AMA table access validation."""
        validation_results = self.calculator.validate_ama_table_access()
        
        self.assertIn("tables_file_accessible", validation_results)
        self.assertTrue(validation_results["tables_file_accessible"])
        
        self.assertIn("has_range_of_motion_tables", validation_results)
        self.assertTrue(validation_results["has_range_of_motion_tables"])
        
        self.assertIn("combined_values_chart_loaded", validation_results)
        self.assertTrue(validation_results["combined_values_chart_loaded"])
    
    def test_calculation_report_generation(self):
        """Test calculation report generation."""
        result = self.calculator.calculate_rom_impairment(self.test_measurements, "spine")
        report = self.calculator.generate_calculation_report(result)
        
        # Verify report contains key sections
        self.assertIn("PROGRAMMATIC IMPAIRMENT CALCULATION REPORT", report)
        self.assertIn("AMA GUIDES REFERENCES:", report)
        self.assertIn("CALCULATION STEPS:", report)
        self.assertIn("SOURCE MEASUREMENTS:", report)
        self.assertIn("VALIDATION STATUS:", report)
        self.assertIn("AUDIT TRAIL:", report)
        
        # Verify specific content
        self.assertIn(f"{result.impairment_percentage}% Whole Person Impairment", report)
        self.assertIn("Table 15-5", report)
        self.assertIn("cervical_spine flexion", report)
    
    def test_body_system_validation(self):
        """Test body system specific validation."""
        # Test spine system validation
        validation = self.calculator._validate_calculation_result(20.0, "spine")
        self.assertTrue(validation["within_body_system_max"])  # 20% < 25% spine max
        
        validation = self.calculator._validate_calculation_result(30.0, "spine")
        self.assertFalse(validation["within_body_system_max"])  # 30% > 25% spine max
        
        # Test upper extremity validation
        validation = self.calculator._validate_calculation_result(50.0, "upper_extremity")
        self.assertTrue(validation["within_body_system_max"])  # 50% < 60% UE max
        
        validation = self.calculator._validate_calculation_result(70.0, "upper_extremity")
        self.assertFalse(validation["within_body_system_max"])  # 70% > 60% UE max
    
    def test_normal_rom_lookup(self):
        """Test normal ROM value lookup from AMA tables."""
        ama_table = self.calculator.ama_tables["15-5"]
        
        # Test valid lookups
        flexion_normal = self.calculator._get_normal_rom("cervical_spine", "flexion", ama_table)
        self.assertEqual(flexion_normal, 50)
        
        extension_normal = self.calculator._get_normal_rom("cervical_spine", "extension", ama_table)
        self.assertEqual(extension_normal, 60)
        
        # Test invalid lookup
        invalid_normal = self.calculator._get_normal_rom("cervical_spine", "invalid_motion", ama_table)
        self.assertIsNone(invalid_normal)
    
    def test_calculation_step_documentation(self):
        """Test that calculation steps are properly documented."""
        result = self.calculator.calculate_rom_impairment(self.test_measurements, "spine")
        
        # Verify each step has required fields
        for step in result.calculation_steps:
            self.assertIsInstance(step, CalculationStep)
            self.assertIsInstance(step.step_number, int)
            self.assertIsInstance(step.description, str)
            self.assertIsInstance(step.input_values, dict)
            self.assertIsInstance(step.calculation, str)
            self.assertIsInstance(step.result, (int, float))
            
            # Verify AMA reference is present
            if step.ama_reference:
                self.assertIsInstance(step.ama_reference, AMATableReference)
                self.assertIsInstance(step.ama_reference.table_id, str)
                self.assertIsInstance(step.ama_reference.chapter, int)
    
    def test_audit_trail_completeness(self):
        """Test that audit trail captures all necessary information."""
        result = self.calculator.calculate_rom_impairment(self.test_measurements, "spine")
        
        # Verify audit trail contains key information
        self.assertIn("body_system", result.audit_trail)
        self.assertIn("table_used", result.audit_trail)
        self.assertIn("measurement_groups", result.audit_trail)
        self.assertIn("total_measurements", result.audit_trail)
        self.assertIn("validation_passed", result.audit_trail)
        
        # Verify values are correct
        self.assertEqual(result.audit_trail["body_system"], "spine")
        self.assertEqual(result.audit_trail["total_measurements"], 3)
        self.assertIsInstance(result.audit_trail["validation_passed"], bool)


class TestCalculationIntegration(unittest.TestCase):
    """Integration tests for complete calculation workflows."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Create comprehensive test data
        self.test_ama_tables = {
            "15-5": {
                "table_id": "15-5",
                "chapter": 15,
                "title": "Cervical Spine Range of Motion Impairment",
                "body_system": "spine",
                "method_type": "range_of_motion",
                "data_structure": {
                    "type": "range_of_motion",
                    "measurements": {
                        "flexion": {"normal": 50, "units": "degrees"},
                        "extension": {"normal": 60, "units": "degrees"}
                    }
                },
                "page_reference": 394
            }
        }
        
        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(self.test_ama_tables, self.temp_file)
        self.temp_file.close()
        
        self.calculator = ImpairmentCalculator(self.temp_file.name)
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        os.unlink(self.temp_file.name)
    
    def test_complete_rom_to_combined_workflow(self):
        """Test complete workflow from ROM measurements to combined impairment."""
        # Step 1: Create ROM measurements for multiple motions
        flexion_measurements = [
            ROMMeasurement("cervical_spine", "flexion", 30.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "flexion", 32.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "flexion", 28.0, datetime.now(), "Dr. Test")
        ]
        
        extension_measurements = [
            ROMMeasurement("cervical_spine", "extension", 40.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "extension", 42.0, datetime.now(), "Dr. Test"),
            ROMMeasurement("cervical_spine", "extension", 38.0, datetime.now(), "Dr. Test")
        ]
        
        all_measurements = flexion_measurements + extension_measurements
        
        # Step 2: Calculate ROM impairment
        rom_result = self.calculator.calculate_rom_impairment(all_measurements, "spine")
        
        # Step 3: Simulate additional impairments
        additional_impairments = [5.0, 3.0]  # Other impairment sources
        all_impairments = [rom_result.impairment_percentage] + additional_impairments
        
        # Step 4: Calculate combined impairment
        combined_result = self.calculator.calculate_combined_impairment(all_impairments)
        
        # Verify workflow results
        self.assertGreater(rom_result.impairment_percentage, 0)
        self.assertGreater(combined_result.impairment_percentage, rom_result.impairment_percentage)
        
        # Verify audit trails are maintained
        self.assertIsNotNone(rom_result.audit_trail)
        self.assertIsNotNone(combined_result.audit_trail)
        
        # Verify all calculations are documented
        total_steps = len(rom_result.calculation_steps) + len(combined_result.calculation_steps)
        self.assertGreater(total_steps, 3)  # Should have multiple documented steps


if __name__ == '__main__':
    unittest.main()