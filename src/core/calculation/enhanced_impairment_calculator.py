"""
Enhanced Impairment Rating Calculator.

This service implements automatic impairment rating calculations with proper
AMA table citations and rationale generation, integrating with the AMA
Guidelines Engine for comprehensive impairment assessment.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
import math

try:
    from src.infrastructure.knowledge.ama_guidelines_engine import (
        AMAGuidelinesEngine, ImpairmentCalculation, AMAMethodType, BodySystemType
    )
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.utils.logging_config import get_logger
except ImportError:
    from src.infrastructure.knowledge.ama_guidelines_engine import (
        AMAGuidelinesEngine, ImpairmentCalculation, AMAMethodType, BodySystemType
    )
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RangeOfMotionMeasurement:
    """Range of motion measurement data."""
    joint: str
    motion_type: str  # flexion, extension, abduction, etc.
    measured_value: float
    normal_value: float
    units: str = "degrees"
    measurement_date: Optional[datetime] = None
    examiner_notes: str = ""


@dataclass
class StrengthTestResult:
    """Strength testing result."""
    muscle_group: str
    strength_grade: str  # 0/5 to 5/5 scale
    numeric_value: float  # 0.0 to 5.0
    testing_method: str
    bilateral_comparison: bool = False
    notes: str = ""


@dataclass
class FunctionalAssessment:
    """Functional capacity assessment."""
    activity: str
    limitation_level: str  # none, mild, moderate, severe
    percentage_limitation: float
    objective_basis: List[str]
    impact_on_adl: str


@dataclass
class ImpairmentComponents:
    """Components contributing to total impairment."""
    primary_impairment: float
    secondary_impairments: List[float]
    combined_impairment: float
    regional_impairments: Dict[str, float]
    whole_person_conversion: float
    calculation_method: AMAMethodType
    supporting_data: Dict[str, Any]


@dataclass
class DetailedImpairmentResult:
    """Comprehensive impairment calculation result."""
    final_percentage: float
    components: ImpairmentComponents
    ama_citations: List[str]
    calculation_steps: List[str]
    rationale: str
    confidence_score: float
    quality_indicators: Dict[str, Any]
    recommendations: List[str]
    validation_results: Dict[str, bool]
    generated_at: datetime = field(default_factory=datetime.now)


class ImpairmentValidationError(Exception):
    """Exception raised for impairment calculation validation errors."""
    pass


class EnhancedImpairmentCalculator:
    """Enhanced impairment calculator with comprehensive AMA integration."""
    
    def __init__(self):
        """Initialize enhanced impairment calculator."""
        self.ama_engine = AMAGuidelinesEngine()
        self.validation_rules = self._load_validation_rules()
        self.calculation_history: List[DetailedImpairmentResult] = []
        
        logger.info("Initialized Enhanced Impairment Calculator")
    
    def calculate_comprehensive_impairment(self,
                                         diagnosis: Diagnosis,
                                         rom_measurements: List[RangeOfMotionMeasurement],
                                         strength_tests: List[StrengthTestResult],
                                         functional_assessments: List[FunctionalAssessment],
                                         additional_findings: List[Finding],
                                         patient_factors: Dict[str, Any]) -> DetailedImpairmentResult:
        """
        Calculate comprehensive impairment rating with detailed analysis.
        
        Args:
            diagnosis: Primary diagnosis
            rom_measurements: Range of motion measurements
            strength_tests: Strength testing results
            functional_assessments: Functional capacity assessments
            additional_findings: Additional clinical findings
            patient_factors: Patient-specific factors (age, occupation, etc.)
            
        Returns:
            DetailedImpairmentResult with comprehensive analysis
        """
        try:
            logger.info(f"Calculating comprehensive impairment for: {diagnosis.description}")
            
            # Prepare clinical data
            clinical_data = self._prepare_clinical_data(
                rom_measurements, strength_tests, functional_assessments, additional_findings
            )
            
            # Calculate primary impairment using AMA engine
            ama_calculation = self.ama_engine.calculate_impairment_rating(
                diagnosis, clinical_data
            )
            
            # Calculate additional impairment components
            components = self._calculate_impairment_components(
                diagnosis, clinical_data, ama_calculation, patient_factors
            )
            
            # Validate calculations
            validation_results = self._validate_calculations(components, clinical_data)
            
            # Generate comprehensive rationale
            rationale = self._generate_comprehensive_rationale(
                diagnosis, components, clinical_data, patient_factors
            )
            
            # Calculate quality indicators
            quality_indicators = self._calculate_quality_indicators(
                components, clinical_data, validation_results
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                components, validation_results, quality_indicators
            )
            
            # Create detailed result
            result = DetailedImpairmentResult(
                final_percentage=components.combined_impairment,
                components=components,
                ama_citations=ama_calculation.ama_citations,
                calculation_steps=ama_calculation.calculation_steps,
                rationale=rationale,
                confidence_score=ama_calculation.confidence_score,
                quality_indicators=quality_indicators,
                recommendations=recommendations,
                validation_results=validation_results
            )
            
            # Store in history
            self.calculation_history.append(result)
            
            logger.info(f"Comprehensive impairment calculation complete: {result.final_percentage}%")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive impairment: {e}")
            raise ImpairmentValidationError(f"Impairment calculation failed: {str(e)}")
    
    def calculate_range_of_motion_impairment(self,
                                           rom_measurements: List[RangeOfMotionMeasurement],
                                           body_system: BodySystemType) -> Tuple[float, List[str], Dict[str, Any]]:
        """
        Calculate impairment based on range of motion limitations.
        
        Args:
            rom_measurements: Range of motion measurements
            body_system: Body system being evaluated
            
        Returns:
            Tuple of (impairment_percentage, calculation_steps, supporting_data)
        """
        try:
            logger.info(f"Calculating ROM impairment for {body_system.value}")
            
            if not rom_measurements:
                return 0.0, ["No ROM measurements provided"], {}
            
            calculation_steps = []
            total_impairment = 0.0
            supporting_data = {}
            
            # Group measurements by joint
            joint_measurements = self._group_measurements_by_joint(rom_measurements)
            
            for joint, measurements in joint_measurements.items():
                joint_impairment, joint_steps = self._calculate_joint_impairment(
                    joint, measurements, body_system
                )
                
                total_impairment += joint_impairment
                calculation_steps.extend(joint_steps)
                supporting_data[joint] = {
                    "impairment": joint_impairment,
                    "measurements": [
                        {
                            "motion": m.motion_type,
                            "measured": m.measured_value,
                            "normal": m.normal_value,
                            "loss_percentage": max(0, (m.normal_value - m.measured_value) / m.normal_value * 100)
                        }
                        for m in measurements
                    ]
                }
            
            # Apply body system specific adjustments
            adjusted_impairment = self._apply_body_system_adjustments(
                total_impairment, body_system, joint_measurements
            )
            
            if adjusted_impairment != total_impairment:
                calculation_steps.append(
                    f"Applied {body_system.value} adjustment: {total_impairment}% → {adjusted_impairment}%"
                )
            
            calculation_steps.append(f"Total ROM impairment: {adjusted_impairment}%")
            
            return adjusted_impairment, calculation_steps, supporting_data
            
        except Exception as e:
            logger.error(f"Error calculating ROM impairment: {e}")
            return 0.0, [f"ROM calculation error: {str(e)}"], {}
    
    def calculate_strength_impairment(self,
                                    strength_tests: List[StrengthTestResult],
                                    body_system: BodySystemType) -> Tuple[float, List[str], Dict[str, Any]]:
        """
        Calculate impairment based on strength testing results.
        
        Args:
            strength_tests: Strength testing results
            body_system: Body system being evaluated
            
        Returns:
            Tuple of (impairment_percentage, calculation_steps, supporting_data)
        """
        try:
            logger.info(f"Calculating strength impairment for {body_system.value}")
            
            if not strength_tests:
                return 0.0, ["No strength tests provided"], {}
            
            calculation_steps = []
            total_impairment = 0.0
            supporting_data = {}
            
            # Strength impairment conversion table (simplified)
            strength_impairment_table = {
                5.0: 0,    # Normal strength
                4.0: 5,    # Good strength (mild weakness)
                3.0: 15,   # Fair strength (moderate weakness)
                2.0: 35,   # Poor strength (severe weakness)
                1.0: 60,   # Trace strength
                0.0: 100   # No strength (paralysis)
            }
            
            for test in strength_tests:
                # Get impairment percentage for strength grade
                base_impairment = strength_impairment_table.get(test.numeric_value, 5)
                
                # Apply muscle group weighting
                muscle_weight = self._get_muscle_group_weight(test.muscle_group, body_system)
                weighted_impairment = base_impairment * muscle_weight
                
                total_impairment += weighted_impairment
                
                calculation_steps.append(
                    f"{test.muscle_group}: {test.strength_grade} = {base_impairment}% × {muscle_weight} = {weighted_impairment}%"
                )
                
                supporting_data[test.muscle_group] = {
                    "grade": test.strength_grade,
                    "numeric_value": test.numeric_value,
                    "base_impairment": base_impairment,
                    "weight": muscle_weight,
                    "weighted_impairment": weighted_impairment
                }
            
            # Cap total strength impairment at reasonable maximum
            max_strength_impairment = 50.0  # Configurable maximum
            if total_impairment > max_strength_impairment:
                calculation_steps.append(
                    f"Strength impairment capped at {max_strength_impairment}% (was {total_impairment}%)"
                )
                total_impairment = max_strength_impairment
            
            calculation_steps.append(f"Total strength impairment: {total_impairment}%")
            
            return total_impairment, calculation_steps, supporting_data
            
        except Exception as e:
            logger.error(f"Error calculating strength impairment: {e}")
            return 0.0, [f"Strength calculation error: {str(e)}"], {}
    
    def calculate_functional_impairment(self,
                                      functional_assessments: List[FunctionalAssessment]) -> Tuple[float, List[str], Dict[str, Any]]:
        """
        Calculate impairment based on functional limitations.
        
        Args:
            functional_assessments: Functional capacity assessments
            
        Returns:
            Tuple of (impairment_percentage, calculation_steps, supporting_data)
        """
        try:
            logger.info("Calculating functional impairment")
            
            if not functional_assessments:
                return 0.0, ["No functional assessments provided"], {}
            
            calculation_steps = []
            total_impairment = 0.0
            supporting_data = {}
            
            # Functional limitation severity weights
            severity_weights = {
                "none": 0.0,
                "mild": 0.25,
                "moderate": 0.50,
                "severe": 0.75,
                "complete": 1.0
            }
            
            # Activity importance weights (ADL vs work activities)
            activity_weights = {
                "lifting": 0.3,
                "carrying": 0.25,
                "walking": 0.2,
                "sitting": 0.15,
                "standing": 0.15,
                "reaching": 0.2,
                "grasping": 0.15,
                "fine_motor": 0.1
            }
            
            for assessment in functional_assessments:
                # Get severity and activity weights
                severity_weight = severity_weights.get(assessment.limitation_level.lower(), 0.5)
                activity_weight = activity_weights.get(assessment.activity.lower(), 0.1)
                
                # Calculate functional impairment for this activity
                activity_impairment = assessment.percentage_limitation * severity_weight * activity_weight
                total_impairment += activity_impairment
                
                calculation_steps.append(
                    f"{assessment.activity}: {assessment.limitation_level} ({assessment.percentage_limitation}%) "
                    f"× {severity_weight} × {activity_weight} = {activity_impairment:.1f}%"
                )
                
                supporting_data[assessment.activity] = {
                    "limitation_level": assessment.limitation_level,
                    "percentage_limitation": assessment.percentage_limitation,
                    "severity_weight": severity_weight,
                    "activity_weight": activity_weight,
                    "activity_impairment": activity_impairment,
                    "objective_basis": assessment.objective_basis
                }
            
            calculation_steps.append(f"Total functional impairment: {total_impairment:.1f}%")
            
            return total_impairment, calculation_steps, supporting_data
            
        except Exception as e:
            logger.error(f"Error calculating functional impairment: {e}")
            return 0.0, [f"Functional calculation error: {str(e)}"], {}
    
    def _prepare_clinical_data(self,
                             rom_measurements: List[RangeOfMotionMeasurement],
                             strength_tests: List[StrengthTestResult],
                             functional_assessments: List[FunctionalAssessment],
                             additional_findings: List[Finding]) -> Dict[str, Any]:
        """Prepare clinical data for AMA engine."""
        clinical_data = {}
        
        if rom_measurements:
            clinical_data["range_of_motion"] = {
                measurement.joint + "_" + measurement.motion_type: measurement.measured_value
                for measurement in rom_measurements
            }
        
        if strength_tests:
            clinical_data["strength_testing"] = {
                test.muscle_group: test.numeric_value
                for test in strength_tests
            }
        
        if functional_assessments:
            clinical_data["functional_limitations"] = {
                assessment.activity: assessment.percentage_limitation
                for assessment in functional_assessments
            }
        
        if additional_findings:
            clinical_data["additional_findings"] = [
                finding.description for finding in additional_findings
            ]
        
        return clinical_data
    
    def _calculate_impairment_components(self,
                                       diagnosis: Diagnosis,
                                       clinical_data: Dict[str, Any],
                                       ama_calculation: ImpairmentCalculation,
                                       patient_factors: Dict[str, Any]) -> ImpairmentComponents:
        """Calculate all impairment components."""
        try:
            # Primary impairment from AMA calculation
            primary_impairment = ama_calculation.final_percentage
            
            # Calculate secondary impairments if applicable
            secondary_impairments = []
            
            # Age-related adjustments (if applicable)
            age = patient_factors.get("age", 45)
            if age > 65:
                age_adjustment = min(2.0, (age - 65) * 0.2)  # Small age adjustment
                secondary_impairments.append(age_adjustment)
            
            # Occupation-related adjustments
            occupation = patient_factors.get("occupation", "")
            if "heavy" in occupation.lower() or "manual" in occupation.lower():
                occupational_adjustment = 1.0  # Small occupational factor
                secondary_impairments.append(occupational_adjustment)
            
            # Calculate combined impairment
            all_impairments = [primary_impairment] + secondary_impairments
            if len(all_impairments) > 1:
                combined_impairment, _, _ = self.ama_engine.calculator.calculate_combined_impairment(all_impairments)
            else:
                combined_impairment = primary_impairment
            
            # Regional to whole person conversion (if needed)
            whole_person_conversion = combined_impairment  # Simplified
            
            components = ImpairmentComponents(
                primary_impairment=primary_impairment,
                secondary_impairments=secondary_impairments,
                combined_impairment=combined_impairment,
                regional_impairments={},  # Would be populated for regional ratings
                whole_person_conversion=whole_person_conversion,
                calculation_method=ama_calculation.method_used,
                supporting_data=clinical_data
            )
            
            return components
            
        except Exception as e:
            logger.error(f"Error calculating impairment components: {e}")
            raise
    
    def _group_measurements_by_joint(self, measurements: List[RangeOfMotionMeasurement]) -> Dict[str, List[RangeOfMotionMeasurement]]:
        """Group ROM measurements by joint."""
        joint_groups = {}
        for measurement in measurements:
            if measurement.joint not in joint_groups:
                joint_groups[measurement.joint] = []
            joint_groups[measurement.joint].append(measurement)
        return joint_groups
    
    def _calculate_joint_impairment(self,
                                  joint: str,
                                  measurements: List[RangeOfMotionMeasurement],
                                  body_system: BodySystemType) -> Tuple[float, List[str]]:
        """Calculate impairment for a specific joint."""
        try:
            calculation_steps = []
            joint_impairment = 0.0
            
            # Calculate impairment for each motion
            for measurement in measurements:
                if measurement.normal_value > 0:
                    loss_percentage = max(0, (measurement.normal_value - measurement.measured_value) / measurement.normal_value)
                    
                    # Motion-specific weighting
                    motion_weight = self._get_motion_weight(measurement.motion_type, joint)
                    motion_impairment = loss_percentage * motion_weight * 100
                    
                    joint_impairment += motion_impairment
                    
                    calculation_steps.append(
                        f"{joint} {measurement.motion_type}: {measurement.measured_value}°/{measurement.normal_value}° "
                        f"= {loss_percentage:.1%} loss × {motion_weight} = {motion_impairment:.1f}%"
                    )
            
            # Apply joint-specific maximum
            max_joint_impairment = self._get_max_joint_impairment(joint, body_system)
            if joint_impairment > max_joint_impairment:
                calculation_steps.append(
                    f"{joint} impairment capped at {max_joint_impairment}% (was {joint_impairment:.1f}%)"
                )
                joint_impairment = max_joint_impairment
            
            return joint_impairment, calculation_steps
            
        except Exception as e:
            logger.error(f"Error calculating joint impairment for {joint}: {e}")
            return 0.0, [f"Joint calculation error: {str(e)}"]
    
    def _get_motion_weight(self, motion_type: str, joint: str) -> float:
        """Get weighting factor for specific motion type."""
        # Motion weights by joint (simplified)
        motion_weights = {
            "spine": {
                "flexion": 0.4,
                "extension": 0.3,
                "lateral_flexion": 0.15,
                "rotation": 0.15
            },
            "shoulder": {
                "flexion": 0.3,
                "extension": 0.2,
                "abduction": 0.3,
                "adduction": 0.1,
                "internal_rotation": 0.05,
                "external_rotation": 0.05
            },
            "knee": {
                "flexion": 0.8,
                "extension": 0.2
            }
        }
        
        joint_weights = motion_weights.get(joint.lower(), {})
        return joint_weights.get(motion_type.lower(), 0.1)
    
    def _get_muscle_group_weight(self, muscle_group: str, body_system: BodySystemType) -> float:
        """Get weighting factor for muscle group importance."""
        # Muscle group weights by body system
        if body_system == BodySystemType.SPINE:
            weights = {
                "paraspinal": 0.4,
                "abdominal": 0.3,
                "hip_flexors": 0.2,
                "gluteal": 0.1
            }
        elif body_system == BodySystemType.UPPER_EXTREMITY:
            weights = {
                "deltoid": 0.3,
                "biceps": 0.2,
                "triceps": 0.2,
                "grip": 0.3
            }
        else:
            weights = {}
        
        return weights.get(muscle_group.lower(), 0.1)
    
    def _apply_body_system_adjustments(self,
                                     impairment: float,
                                     body_system: BodySystemType,
                                     joint_measurements: Dict[str, List[RangeOfMotionMeasurement]]) -> float:
        """Apply body system specific adjustments."""
        # Body system specific caps and adjustments
        if body_system == BodySystemType.SPINE:
            return min(impairment, 25.0)  # Spine ROM cap
        elif body_system == BodySystemType.UPPER_EXTREMITY:
            return min(impairment, 60.0)  # Upper extremity cap
        elif body_system == BodySystemType.LOWER_EXTREMITY:
            return min(impairment, 40.0)  # Lower extremity cap
        else:
            return min(impairment, 30.0)  # General cap
    
    def _get_max_joint_impairment(self, joint: str, body_system: BodySystemType) -> float:
        """Get maximum impairment for specific joint."""
        joint_maxes = {
            "cervical_spine": 25.0,
            "lumbar_spine": 25.0,
            "shoulder": 24.0,
            "elbow": 28.0,
            "wrist": 15.0,
            "hip": 20.0,
            "knee": 37.0,
            "ankle": 20.0
        }
        
        return joint_maxes.get(joint.lower(), 15.0)
    
    def _validate_calculations(self, components: ImpairmentComponents, clinical_data: Dict[str, Any]) -> Dict[str, bool]:
        """Validate impairment calculations."""
        validation_results = {}
        
        try:
            # Validate percentage range
            validation_results["percentage_in_range"] = 0 <= components.combined_impairment <= 100
            
            # Validate calculation method appropriateness
            validation_results["method_appropriate"] = components.calculation_method is not None
            
            # Validate supporting data completeness
            validation_results["data_complete"] = len(clinical_data) >= 2
            
            # Validate combined calculation if multiple impairments
            if len(components.secondary_impairments) > 0:
                validation_results["combination_valid"] = (
                    components.combined_impairment >= components.primary_impairment
                )
            else:
                validation_results["combination_valid"] = True
            
            # Validate reasonableness
            validation_results["result_reasonable"] = (
                components.combined_impairment <= 50.0  # Reasonable maximum for most cases
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating calculations: {e}")
            return {"validation_error": False}
    
    def _generate_comprehensive_rationale(self,
                                        diagnosis: Diagnosis,
                                        components: ImpairmentComponents,
                                        clinical_data: Dict[str, Any],
                                        patient_factors: Dict[str, Any]) -> str:
        """Generate comprehensive rationale for impairment rating."""
        try:
            rationale_parts = []
            
            # Introduction
            rationale_parts.append(
                f"The impairment rating for {diagnosis.description} was calculated using the "
                f"{components.calculation_method.value} method as specified in the AMA Guides "
                f"to the Evaluation of Permanent Impairment, Fifth Edition."
            )
            
            # Primary impairment explanation
            rationale_parts.append(
                f"The primary impairment of {components.primary_impairment}% is based on "
                f"objective clinical findings and standardized measurement techniques."
            )
            
            # Clinical data support
            if clinical_data:
                data_types = list(clinical_data.keys())
                rationale_parts.append(
                    f"The rating incorporates {', '.join(data_types)} to ensure comprehensive "
                    f"assessment of functional limitations."
                )
            
            # Secondary impairments
            if components.secondary_impairments:
                rationale_parts.append(
                    f"Additional factors contributing {sum(components.secondary_impairments):.1f}% "
                    f"were considered in the combined calculation."
                )
            
            # Combined calculation
            if components.combined_impairment != components.primary_impairment:
                rationale_parts.append(
                    f"The Combined Values Chart was used to determine the final rating of "
                    f"{components.combined_impairment}% whole person impairment."
                )
            
            # Patient factors
            age = patient_factors.get("age")
            if age and age > 65:
                rationale_parts.append(
                    f"Age-related factors were considered in the assessment given the patient's age of {age}."
                )
            
            # Conclusion
            rationale_parts.append(
                f"This rating represents the permanent impairment to the whole person and is "
                f"consistent with AMA Guidelines methodology and clinical findings."
            )
            
            return " ".join(rationale_parts)
            
        except Exception as e:
            logger.error(f"Error generating rationale: {e}")
            return f"Impairment rating of {components.combined_impairment}% based on AMA Guidelines methodology."
    
    def _calculate_quality_indicators(self,
                                    components: ImpairmentComponents,
                                    clinical_data: Dict[str, Any],
                                    validation_results: Dict[str, bool]) -> Dict[str, Any]:
        """Calculate quality indicators for the impairment assessment."""
        try:
            quality_indicators = {}
            
            # Data completeness score
            expected_data_types = ["range_of_motion", "strength_testing", "functional_limitations"]
            present_data_types = [dt for dt in expected_data_types if dt in clinical_data]
            quality_indicators["data_completeness"] = len(present_data_types) / len(expected_data_types)
            
            # Validation score
            passed_validations = sum(1 for result in validation_results.values() if result)
            total_validations = len(validation_results)
            quality_indicators["validation_score"] = passed_validations / total_validations if total_validations > 0 else 0
            
            # Method appropriateness
            quality_indicators["method_appropriate"] = components.calculation_method != AMAMethodType.TABLE_BASED
            
            # Supporting evidence strength
            evidence_count = len(components.supporting_data)
            quality_indicators["evidence_strength"] = min(evidence_count / 5.0, 1.0)
            
            # Overall quality score
            quality_indicators["overall_quality"] = (
                quality_indicators["data_completeness"] * 0.3 +
                quality_indicators["validation_score"] * 0.4 +
                (1.0 if quality_indicators["method_appropriate"] else 0.5) * 0.2 +
                quality_indicators["evidence_strength"] * 0.1
            )
            
            return quality_indicators
            
        except Exception as e:
            logger.error(f"Error calculating quality indicators: {e}")
            return {"overall_quality": 0.5}
    
    def _generate_recommendations(self,
                                components: ImpairmentComponents,
                                validation_results: Dict[str, bool],
                                quality_indicators: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving the impairment assessment."""
        recommendations = []
        
        try:
            # Data completeness recommendations
            if quality_indicators.get("data_completeness", 0) < 0.8:
                recommendations.append("Consider obtaining additional objective measurements to strengthen the assessment")
            
            # Validation recommendations
            if not validation_results.get("result_reasonable", True):
                recommendations.append("Review calculation methodology - result may be outside expected range")
            
            if not validation_results.get("combination_valid", True):
                recommendations.append("Verify combined values calculation using AMA Combined Values Chart")
            
            # Method recommendations
            if components.calculation_method == AMAMethodType.TABLE_BASED:
                recommendations.append("Consider range of motion or functional assessment methods for more precise rating")
            
            # Quality recommendations
            overall_quality = quality_indicators.get("overall_quality", 0)
            if overall_quality < 0.7:
                recommendations.append("Consider additional clinical documentation to improve assessment quality")
            
            # General recommendations
            recommendations.extend([
                "Ensure all measurements are performed using standardized techniques",
                "Document patient cooperation and effort during testing",
                "Consider repeat measurements if initial results are inconsistent"
            ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review calculation methodology and supporting documentation"]
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for impairment calculations."""
        return {
            "percentage_limits": {
                "minimum": 0.0,
                "maximum": 100.0,
                "typical_maximum": 50.0
            },
            "data_requirements": {
                "minimum_measurements": 2,
                "preferred_measurements": 5
            },
            "calculation_tolerances": {
                "rounding_precision": 0.5,
                "combination_tolerance": 1.0
            }
        }
    
    def get_calculation_summary(self, result: DetailedImpairmentResult) -> str:
        """Generate a summary of the impairment calculation."""
        try:
            summary_lines = []
            
            summary_lines.append("IMPAIRMENT CALCULATION SUMMARY")
            summary_lines.append("=" * 40)
            summary_lines.append("")
            
            summary_lines.append(f"Final Impairment Rating: {result.final_percentage}% whole person")
            summary_lines.append(f"Calculation Method: {result.components.calculation_method.value}")
            summary_lines.append(f"Confidence Score: {result.confidence_score:.1%}")
            summary_lines.append("")
            
            # Components breakdown
            summary_lines.append("COMPONENTS:")
            summary_lines.append(f"  Primary Impairment: {result.components.primary_impairment}%")
            
            if result.components.secondary_impairments:
                summary_lines.append(f"  Secondary Impairments: {', '.join(f'{imp}%' for imp in result.components.secondary_impairments)}")
                summary_lines.append(f"  Combined Total: {result.components.combined_impairment}%")
            
            summary_lines.append("")
            
            # Quality indicators
            overall_quality = result.quality_indicators.get("overall_quality", 0)
            quality_level = "Excellent" if overall_quality >= 0.9 else \
                           "Good" if overall_quality >= 0.8 else \
                           "Fair" if overall_quality >= 0.7 else "Needs Improvement"
            
            summary_lines.append(f"Assessment Quality: {quality_level} ({overall_quality:.1%})")
            
            # Top recommendations
            if result.recommendations:
                summary_lines.append("")
                summary_lines.append("KEY RECOMMENDATIONS:")
                for rec in result.recommendations[:3]:
                    summary_lines.append(f"  • {rec}")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"Error generating calculation summary: {e}")
            return f"Impairment Rating: {result.final_percentage}% whole person"