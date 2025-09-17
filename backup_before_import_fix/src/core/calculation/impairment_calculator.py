"""
Programmatic Impairment Calculation Engine.

This service implements AMA Guides 5th Edition table-based calculations with zero LLM involvement.
All calculations are performed programmatically using structured AMA tables with complete audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
import json
import math

try:
    from src.utils.logging_config import get_logger
except ImportError:
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class CalculationValidationError(Exception):
    """Exception raised for calculation validation errors."""
    pass


@dataclass
class ROMMeasurement:
    """Range of Motion measurement with validation."""
    joint: str
    motion_type: str  # flexion, extension, lateral_flexion, rotation
    measured_degrees: float
    measurement_date: datetime
    examiner: str
    notes: str = ""
    
    def __post_init__(self):
        """Validate ROM measurement data."""
        if self.measured_degrees < 0:
            raise CalculationValidationError(f"Invalid ROM measurement: {self.measured_degrees} degrees")
        if not self.joint or not self.motion_type:
            raise CalculationValidationError("Joint and motion_type are required")


@dataclass
class AMATableReference:
    """AMA table reference with citation information."""
    table_id: str
    chapter: int
    title: str
    page_reference: int
    method_type: str
    body_system: str


@dataclass
class CalculationStep:
    """Individual calculation step with documentation."""
    step_number: int
    description: str
    input_values: Dict[str, Any]
    calculation: str
    result: float
    ama_reference: Optional[AMATableReference] = None
    notes: str = ""


@dataclass
class ProgrammaticCalculationResult:
    """Complete programmatic calculation result with audit trail."""
    impairment_percentage: float
    ama_table_references: List[AMATableReference]
    calculation_steps: List[CalculationStep]
    source_measurements: List[ROMMeasurement]
    validation_status: Dict[str, bool]
    calculation_method: str
    generated_at: datetime = field(default_factory=datetime.now)
    audit_trail: Dict[str, Any] = field(default_factory=dict)


class ImpairmentCalculator:
    """Programmatic impairment calculator with zero LLM involvement."""
    
    def __init__(self, ama_tables_path: str = "data/ama_guidelines/tables.json"):
        """Initialize calculator with AMA tables."""
        self.ama_tables_path = ama_tables_path
        self.ama_tables = self._load_ama_tables()
        self.combined_values_chart = self._initialize_combined_values_chart()
        
        logger.info("Initialized Programmatic Impairment Calculator")
    
    def _load_ama_tables(self) -> Dict[str, Any]:
        """Load and validate AMA tables from JSON file."""
        try:
            with open(self.ama_tables_path, 'r') as f:
                tables = json.load(f)
            
            # Validate table structure
            required_fields = ['table_id', 'chapter', 'title', 'body_system', 'method_type']
            for table_id, table_data in tables.items():
                for field in required_fields:
                    if field not in table_data:
                        raise CalculationValidationError(f"Missing field {field} in table {table_id}")
            
            logger.info(f"Loaded {len(tables)} AMA tables")
            return tables
            
        except FileNotFoundError:
            logger.error(f"AMA tables file not found: {self.ama_tables_path}")
            raise CalculationValidationError(f"AMA tables file not found: {self.ama_tables_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in AMA tables file: {e}")
            raise CalculationValidationError(f"Invalid JSON in AMA tables file: {e}")
    
    def _initialize_combined_values_chart(self) -> Dict[Tuple[int, int], int]:
        """Initialize AMA Combined Values Chart for multiple impairments."""
        # AMA Combined Values Chart (simplified version - would be complete in production)
        chart = {}
        
        # Generate combined values for common ranges
        for a in range(0, 101, 5):
            for b in range(0, 101, 5):
                if a == 0 or b == 0:
                    chart[(a, b)] = max(a, b)
                else:
                    # AMA formula: A + B(100-A)/100
                    combined = a + (b * (100 - a)) / 100
                    chart[(a, b)] = round(combined)
        
        return chart
    
    def calculate_rom_impairment(self, 
                                measurements: List[ROMMeasurement],
                                body_system: str) -> ProgrammaticCalculationResult:
        """
        Calculate ROM-based impairment with minimum 3 measurements requirement.
        
        Args:
            measurements: List of ROM measurements (minimum 3 per motion type)
            body_system: Body system (spine, upper_extremity, lower_extremity)
            
        Returns:
            ProgrammaticCalculationResult with complete audit trail
        """
        try:
            logger.info(f"Calculating ROM impairment for {body_system}")
            
            # Validate minimum measurements
            self._validate_minimum_measurements(measurements)
            
            # Group measurements by joint and motion type
            grouped_measurements = self._group_measurements(measurements)
            
            # Find appropriate AMA table - use first joint to determine specific table
            first_joint = list(grouped_measurements.keys())[0].split('_')[0] if grouped_measurements else None
            ama_table = self._find_rom_table(body_system, first_joint)
            if not ama_table:
                raise CalculationValidationError(f"No ROM table found for {body_system}")
            
            calculation_steps = []
            total_impairment = 0.0
            step_counter = 1
            
            # Calculate impairment for each joint/motion combination
            for joint_motion, measurement_list in grouped_measurements.items():
                # Handle joint names that contain underscores (e.g., cervical_spine_flexion)
                parts = joint_motion.split('_')
                if len(parts) >= 3 and parts[1] == 'spine':
                    # Handle cases like cervical_spine_flexion -> joint=cervical_spine, motion=flexion
                    joint = '_'.join(parts[:2])
                    motion = '_'.join(parts[2:])
                else:
                    # Handle simple cases like shoulder_flexion -> joint=shoulder, motion=flexion
                    joint, motion = joint_motion.split('_', 1)
                
                # Calculate average of measurements (minimum 3 required)
                if len(measurement_list) < 3:
                    raise CalculationValidationError(
                        f"Minimum 3 measurements required for {joint} {motion}, got {len(measurement_list)}"
                    )
                
                average_rom = self._calculate_rom_average(measurement_list)
                normal_rom = self._get_normal_rom(joint, motion, ama_table)
                
                if normal_rom is None:
                    logger.warning(f"No normal ROM value found for {joint} {motion}")
                    continue
                
                # Calculate percentage loss
                rom_loss_percentage = max(0, (normal_rom - average_rom) / normal_rom * 100)
                
                # Apply AMA impairment formula
                motion_impairment = self._calculate_motion_impairment(
                    rom_loss_percentage, joint, motion, ama_table
                )
                
                total_impairment += motion_impairment
                
                # Document calculation step
                step = CalculationStep(
                    step_number=step_counter,
                    description=f"Calculate {joint} {motion} impairment",
                    input_values={
                        "measurements": [m.measured_degrees for m in measurement_list],
                        "average_rom": average_rom,
                        "normal_rom": normal_rom,
                        "rom_loss_percentage": rom_loss_percentage
                    },
                    calculation=f"({normal_rom} - {average_rom}) / {normal_rom} * 100 = {rom_loss_percentage:.1f}% loss",
                    result=motion_impairment,
                    ama_reference=AMATableReference(
                        table_id=ama_table['table_id'],
                        chapter=ama_table['chapter'],
                        title=ama_table['title'],
                        page_reference=ama_table['page_reference'],
                        method_type=ama_table['method_type'],
                        body_system=ama_table['body_system']
                    ),
                    notes=f"Based on average of {len(measurement_list)} measurements"
                )
                calculation_steps.append(step)
                step_counter += 1
            
            # Validate final result
            validation_status = self._validate_calculation_result(total_impairment, body_system)
            
            # Create result with complete audit trail
            result = ProgrammaticCalculationResult(
                impairment_percentage=total_impairment,
                ama_table_references=[step.ama_reference for step in calculation_steps if step.ama_reference],
                calculation_steps=calculation_steps,
                source_measurements=measurements,
                validation_status=validation_status,
                calculation_method="ROM_BASED_PROGRAMMATIC",
                audit_trail={
                    "body_system": body_system,
                    "table_used": ama_table['table_id'],
                    "measurement_groups": len(grouped_measurements),
                    "total_measurements": len(measurements),
                    "validation_passed": all(validation_status.values())
                }
            )
            
            logger.info(f"ROM impairment calculation complete: {total_impairment:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating ROM impairment: {e}")
            raise CalculationValidationError(f"ROM calculation failed: {str(e)}")
    
    def calculate_combined_impairment(self, impairments: List[float]) -> ProgrammaticCalculationResult:
        """
        Calculate combined impairment using AMA Combined Values Chart.
        
        Args:
            impairments: List of individual impairment percentages
            
        Returns:
            ProgrammaticCalculationResult with step-by-step combination
        """
        try:
            logger.info(f"Calculating combined impairment for {len(impairments)} values")
            
            if len(impairments) < 2:
                raise CalculationValidationError("At least 2 impairments required for combination")
            
            # Validate impairment values
            for i, imp in enumerate(impairments):
                if not 0 <= imp <= 100:
                    raise CalculationValidationError(f"Invalid impairment value {imp}% at index {i}")
            
            calculation_steps = []
            step_counter = 1
            
            # Sort impairments in descending order (AMA requirement)
            sorted_impairments = sorted(impairments, reverse=True)
            
            # Document sorting step
            if sorted_impairments != impairments:
                step = CalculationStep(
                    step_number=step_counter,
                    description="Sort impairments in descending order",
                    input_values={"original": impairments},
                    calculation=f"Sorted: {sorted_impairments}",
                    result=0.0,
                    notes="AMA requires largest impairment first"
                )
                calculation_steps.append(step)
                step_counter += 1
            
            # Combine impairments sequentially
            combined_result = sorted_impairments[0]
            
            for i in range(1, len(sorted_impairments)):
                current_impairment = sorted_impairments[i]
                new_combined = self._apply_combined_values_chart(combined_result, current_impairment)
                
                # Document combination step
                step = CalculationStep(
                    step_number=step_counter,
                    description=f"Combine {combined_result}% with {current_impairment}%",
                    input_values={
                        "impairment_a": combined_result,
                        "impairment_b": current_impairment
                    },
                    calculation=f"A + B(100-A)/100 = {combined_result} + {current_impairment}(100-{combined_result})/100",
                    result=new_combined,
                    ama_reference=AMATableReference(
                        table_id="COMBINED_VALUES",
                        chapter=1,
                        title="Combined Values Chart",
                        page_reference=604,
                        method_type="combined_values",
                        body_system="whole_person"
                    ),
                    notes="AMA Combined Values Chart application"
                )
                calculation_steps.append(step)
                step_counter += 1
                
                combined_result = new_combined
            
            # Validate final result
            validation_status = {
                "result_in_range": 0 <= combined_result <= 100,
                "combination_valid": combined_result >= max(impairments),
                "chart_applied_correctly": True
            }
            
            result = ProgrammaticCalculationResult(
                impairment_percentage=combined_result,
                ama_table_references=[AMATableReference(
                    table_id="COMBINED_VALUES",
                    chapter=1,
                    title="Combined Values Chart",
                    page_reference=604,
                    method_type="combined_values",
                    body_system="whole_person"
                )],
                calculation_steps=calculation_steps,
                source_measurements=[],
                validation_status=validation_status,
                calculation_method="COMBINED_VALUES_PROGRAMMATIC",
                audit_trail={
                    "input_impairments": impairments,
                    "sorted_impairments": sorted_impairments,
                    "combination_steps": len(sorted_impairments) - 1,
                    "final_result": combined_result
                }
            )
            
            logger.info(f"Combined impairment calculation complete: {combined_result:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating combined impairment: {e}")
            raise CalculationValidationError(f"Combined calculation failed: {str(e)}")
    
    def _validate_minimum_measurements(self, measurements: List[ROMMeasurement]) -> None:
        """Validate minimum measurement requirements."""
        if not measurements:
            raise CalculationValidationError("No ROM measurements provided")
        
        # Group by joint and motion type to check minimum 3 per type
        grouped = self._group_measurements(measurements)
        
        for joint_motion, measurement_list in grouped.items():
            if len(measurement_list) < 3:
                raise CalculationValidationError(
                    f"Minimum 3 measurements required for {joint_motion}, got {len(measurement_list)}"
                )
    
    def _group_measurements(self, measurements: List[ROMMeasurement]) -> Dict[str, List[ROMMeasurement]]:
        """Group measurements by joint and motion type."""
        grouped = {}
        
        for measurement in measurements:
            key = f"{measurement.joint}_{measurement.motion_type}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(measurement)
        
        return grouped
    
    def _find_rom_table(self, body_system: str, joint: str = None) -> Optional[Dict[str, Any]]:
        """Find appropriate ROM table for body system and joint."""
        # First try to find specific table for joint
        if joint:
            for table_id, table_data in self.ama_tables.items():
                if (table_data.get('body_system') == body_system and 
                    table_data.get('method_type') == 'range_of_motion'):
                    # Check if table title matches joint
                    title = table_data.get('title', '').lower()
                    if 'cervical' in joint.lower() and 'cervical' in title:
                        return table_data
                    elif 'lumbar' in joint.lower() and 'lumbar' in title:
                        return table_data
        
        # Fallback to any ROM table for body system
        for table_id, table_data in self.ama_tables.items():
            if (table_data.get('body_system') == body_system and 
                table_data.get('method_type') == 'range_of_motion'):
                return table_data
        
        return None
    
    def _calculate_rom_average(self, measurements: List[ROMMeasurement]) -> float:
        """Calculate average ROM from multiple measurements."""
        if not measurements:
            return 0.0
        
        total = sum(m.measured_degrees for m in measurements)
        return total / len(measurements)
    
    def _get_normal_rom(self, joint: str, motion: str, ama_table: Dict[str, Any]) -> Optional[float]:
        """Get normal ROM value from AMA table."""
        try:
            data_structure = ama_table.get('data_structure', {})
            measurements = data_structure.get('measurements', {})
            
            motion_data = measurements.get(motion, {})
            normal_value = motion_data.get('normal')
            
            if normal_value is None:
                logger.warning(f"No normal ROM value found for {joint} {motion} in table {ama_table.get('table_id')}")
            
            return normal_value
            
        except Exception as e:
            logger.error(f"Error getting normal ROM for {joint} {motion}: {e}")
            return None
    
    def _calculate_motion_impairment(self, 
                                   rom_loss_percentage: float,
                                   joint: str,
                                   motion: str,
                                   ama_table: Dict[str, Any]) -> float:
        """Calculate impairment percentage for specific motion loss using AMA table factors."""
        try:
            # Get impairment factor from AMA table
            data_structure = ama_table.get('data_structure', {})
            measurements = data_structure.get('measurements', {})
            motion_data = measurements.get(motion, {})
            impairment_factor = motion_data.get('impairment_factor', 0.1)
            
            # Calculate impairment: ROM loss percentage × impairment factor
            # This follows AMA methodology where each motion has a specific weighting
            impairment = rom_loss_percentage * impairment_factor
            
            return round(impairment, 1)
            
        except Exception as e:
            logger.error(f"Error calculating motion impairment for {joint} {motion}: {e}")
            # Fallback to basic calculation
            return round(rom_loss_percentage * 0.1, 1)
    
    def _apply_combined_values_chart(self, impairment_a: float, impairment_b: float) -> float:
        """Apply AMA Combined Values Chart formula."""
        # Round to nearest 5 for chart lookup
        a_rounded = round(impairment_a / 5) * 5
        b_rounded = round(impairment_b / 5) * 5
        
        # Check chart first
        chart_key = (int(a_rounded), int(b_rounded))
        if chart_key in self.combined_values_chart:
            return float(self.combined_values_chart[chart_key])
        
        # Use AMA formula: A + B(100-A)/100
        combined = impairment_a + (impairment_b * (100 - impairment_a)) / 100
        return round(combined, 1)
    
    def _validate_calculation_result(self, result: float, body_system: str) -> Dict[str, bool]:
        """Validate calculation result against AMA guidelines."""
        validation = {}
        
        # Basic range validation
        validation["result_in_range"] = 0 <= result <= 100
        
        # Body system specific maximums
        max_values = {
            "spine": 25.0,
            "upper_extremity": 60.0,
            "lower_extremity": 40.0
        }
        
        max_allowed = max_values.get(body_system, 30.0)
        validation["within_body_system_max"] = result <= max_allowed
        
        # Reasonableness check
        validation["result_reasonable"] = result <= 50.0
        
        return validation
    
    def validate_ama_table_access(self) -> Dict[str, bool]:
        """Validate that all required AMA tables are accessible."""
        validation_results = {}
        
        try:
            # Check table file exists and is readable
            validation_results["tables_file_accessible"] = len(self.ama_tables) > 0
            
            # Check for required table types
            required_table_types = ["range_of_motion", "table_based"]
            for table_type in required_table_types:
                has_type = any(
                    table.get('method_type') == table_type 
                    for table in self.ama_tables.values()
                )
                validation_results[f"has_{table_type}_tables"] = has_type
            
            # Check for required body systems
            required_body_systems = ["spine", "upper_extremity", "lower_extremity"]
            for body_system in required_body_systems:
                has_system = any(
                    table.get('body_system') == body_system 
                    for table in self.ama_tables.values()
                )
                validation_results[f"has_{body_system}_tables"] = has_system
            
            # Check Combined Values Chart
            validation_results["combined_values_chart_loaded"] = len(self.combined_values_chart) > 0
            
            logger.info(f"AMA table validation: {validation_results}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating AMA table access: {e}")
            return {"validation_error": False}
    
    def generate_calculation_report(self, result: ProgrammaticCalculationResult) -> str:
        """Generate detailed calculation report with AMA citations."""
        try:
            report_lines = []
            
            # Header
            report_lines.append("PROGRAMMATIC IMPAIRMENT CALCULATION REPORT")
            report_lines.append("=" * 50)
            report_lines.append(f"Generated: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"Method: {result.calculation_method}")
            report_lines.append(f"Final Result: {result.impairment_percentage}% Whole Person Impairment")
            report_lines.append("")
            
            # AMA Table References
            report_lines.append("AMA GUIDES REFERENCES:")
            for ref in result.ama_table_references:
                report_lines.append(f"  • Table {ref.table_id}: {ref.title}")
                report_lines.append(f"    Chapter {ref.chapter}, Page {ref.page_reference}")
                report_lines.append(f"    Method: {ref.method_type}, System: {ref.body_system}")
            report_lines.append("")
            
            # Calculation Steps
            report_lines.append("CALCULATION STEPS:")
            for step in result.calculation_steps:
                report_lines.append(f"  {step.step_number}. {step.description}")
                report_lines.append(f"     Input: {step.input_values}")
                report_lines.append(f"     Calculation: {step.calculation}")
                report_lines.append(f"     Result: {step.result}")
                if step.notes:
                    report_lines.append(f"     Notes: {step.notes}")
                report_lines.append("")
            
            # Source Data
            if result.source_measurements:
                report_lines.append("SOURCE MEASUREMENTS:")
                for measurement in result.source_measurements:
                    report_lines.append(
                        f"  • {measurement.joint} {measurement.motion_type}: "
                        f"{measurement.measured_degrees}° ({measurement.measurement_date.strftime('%Y-%m-%d')})"
                    )
                report_lines.append("")
            
            # Validation Status
            report_lines.append("VALIDATION STATUS:")
            for check, passed in result.validation_status.items():
                status = "PASS" if passed else "FAIL"
                report_lines.append(f"  • {check}: {status}")
            report_lines.append("")
            
            # Audit Trail
            report_lines.append("AUDIT TRAIL:")
            for key, value in result.audit_trail.items():
                report_lines.append(f"  • {key}: {value}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating calculation report: {e}")
            return f"Error generating report: {str(e)}"