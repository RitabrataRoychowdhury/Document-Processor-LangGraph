"""
Tests for AMA Guidelines Integration and Medical Reasoning Engine.

This test suite validates the comprehensive AMA Guidelines integration including
document processing, method selection, impairment calculation, and medical reasoning.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

try:
    from src.services.ama_guidelines_engine import (
        AMAGuidelinesEngine, AMAGuidelinesProcessor, AMAMethodSelector,
        CombinedValuesCalculator, MedicalReasoningEngine, AMAMethodType, BodySystemType
    )
    from src.services.enhanced_impairment_calculator import (
        EnhancedImpairmentCalculator, RangeOfMotionMeasurement, 
        StrengthTestResult, FunctionalAssessment
    )
    from src.services.qme_reference_processor import (
        QMEReferenceIntegrator, QMEStudyGuideProcessor, SampleReportProcessor
    )
    from src.services.comprehensive_ama_integration import (
        ComprehensiveAMAIntegration, ComprehensiveEvaluationData
    )
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
except ImportError:
    from services.ama_guidelines_engine import (
        AMAGuidelinesEngine, AMAGuidelinesProcessor, AMAMethodSelector,
        CombinedValuesCalculator, MedicalReasoningEngine, AMAMethodType, BodySystemType
    )
    from services.enhanced_impairment_calculator import (
        EnhancedImpairmentCalculator, RangeOfMotionMeasurement,
        StrengthTestResult, FunctionalAssessment
    )
    from services.qme_reference_processor import (
        QMEReferenceIntegrator, QMEStudyGuideProcessor, SampleReportProcessor
    )
    from services.comprehensive_ama_integration import (
        ComprehensiveAMAIntegration, ComprehensiveEvaluationData
    )
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating


class TestAMAGuidelinesProcessor(unittest.TestCase):
    """Test AMA Guidelines PDF processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = AMAGuidelinesProcessor("test_ama_guides.pdf")
    
    def test_initialization(self):
        """Test processor initialization."""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.ama_pdf_path, "test_ama_guides.pdf")
        self.assertIsInstance(self.processor.chapters, dict)
        self.assertIsInstance(self.processor.tables, dict)
    
    @patch('src.services.ama_guidelines_engine.DocumentProcessor')
    def test_process_ama_guidelines_success(self, mock_doc_processor):
        """Test successful AMA guidelines processing."""
        # Mock document processor
        mock_doc_processor.return_value.extract_text_from_pdf.return_value = "Sample AMA text"
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            result = self.processor.process_ama_guidelines()
        
        self.assertTrue(result)
        self.assertGreater(len(self.processor.chapters), 0)
        self.assertGreater(len(self.processor.tables), 0)
    
    def test_process_ama_guidelines_file_not_found(self):
        """Test AMA guidelines processing when file not found."""
        with patch('os.path.exists', return_value=False):
            result = self.processor.process_ama_guidelines()
        
        self.assertFalse(result)
        # Should load default structure
        self.assertGreater(len(self.processor.chapters), 0)
    
    def test_extract_impairment_tables(self):
        """Test impairment table extraction."""
        sample_text = "AMA Guides sample text"
        self.processor._extract_impairment_tables(sample_text)
        
        # Should have created some tables
        self.assertGreater(len(self.processor.tables), 0)
        
        # Check specific table
        if "15-3" in self.processor.tables:
            table = self.processor.tables["15-3"]
            self.assertEqual(table.chapter, 15)
            self.assertEqual(table.body_system, BodySystemType.SPINE)
    
    def test_combined_values_chart_creation(self):
        """Test Combined Values Chart creation."""
        self.processor._build_combined_values_chart()
        
        self.assertGreater(len(self.processor.combined_values_chart), 0)
        
        # Check specific entry
        entry = self.processor.combined_values_chart[0]
        self.assertIsNotNone(entry.smaller_value)
        self.assertIsNotNone(entry.larger_value)
        self.assertIsNotNone(entry.combined_value)


class TestAMAMethodSelector(unittest.TestCase):
    """Test AMA method selection logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        mock_processor = Mock()
        mock_processor.chapters = {}
        mock_processor.tables = {}
        self.selector = AMAMethodSelector(mock_processor)
    
    def test_spine_method_selection(self):
        """Test spine-specific method selection."""
        diagnosis = Diagnosis(
            id="test_diag",
            description="Lumbar disc herniation",
            icd_code="M51.26"
        )
        
        available_data = {
            "range_of_motion": {"lumbar_flexion": 30},
            "pathology": "herniated disc"
        }
        
        method_type, table_ref, rationale = self.selector.select_appropriate_method(
            diagnosis, available_data
        )
        
        self.assertIsInstance(method_type, AMAMethodType)
        self.assertIsInstance(table_ref, str)
        self.assertIsInstance(rationale, list)
        self.assertGreater(len(rationale), 0)
    
    def test_upper_extremity_method_selection(self):
        """Test upper extremity method selection."""
        diagnosis = Diagnosis(
            id="test_diag",
            description="Shoulder impingement syndrome",
            icd_code="M75.3"
        )
        
        available_data = {
            "range_of_motion": {"shoulder_flexion": 120}
        }
        
        method_type, table_ref, rationale = self.selector.select_appropriate_method(
            diagnosis, available_data
        )
        
        self.assertIsInstance(method_type, AMAMethodType)
        self.assertTrue(table_ref.startswith("16") if table_ref else False)  # Upper extremity tables start with 16
    
    def test_body_system_identification(self):
        """Test body system identification from diagnosis."""
        spine_diagnosis = Diagnosis(id="1", description="Cervical spine injury", icd_code="M50.0")
        body_system = self.selector._identify_body_system(spine_diagnosis)
        self.assertEqual(body_system, BodySystemType.SPINE)
        
        upper_ext_diagnosis = Diagnosis(id="2", description="Shoulder injury", icd_code="M75.0")
        body_system = self.selector._identify_body_system(upper_ext_diagnosis)
        self.assertEqual(body_system, BodySystemType.UPPER_EXTREMITY)


class TestCombinedValuesCalculator(unittest.TestCase):
    """Test Combined Values Chart calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        mock_processor = Mock()
        mock_processor.combined_values_chart = [
            Mock(smaller_value=5, larger_value=10, combined_value=14),
            Mock(smaller_value=10, larger_value=15, combined_value=24),
            Mock(smaller_value=15, larger_value=20, combined_value=32)
        ]
        self.calculator = CombinedValuesCalculator(mock_processor)
    
    def test_single_impairment(self):
        """Test calculation with single impairment."""
        impairments = [10.0]
        
        combined, steps, valid = self.calculator.calculate_combined_impairment(impairments)
        
        self.assertEqual(combined, 10.0)
        self.assertTrue(valid)
        self.assertIn("Single impairment", steps[0])
    
    def test_multiple_impairments(self):
        """Test calculation with multiple impairments."""
        impairments = [10.0, 5.0]
        
        combined, steps, valid = self.calculator.calculate_combined_impairment(impairments)
        
        self.assertGreater(combined, 10.0)  # Should be greater than largest individual
        self.assertLess(combined, 15.0)     # Should be less than sum
        self.assertTrue(valid)
        self.assertGreater(len(steps), 2)
    
    def test_empty_impairments(self):
        """Test calculation with no impairments."""
        impairments = []
        
        combined, steps, valid = self.calculator.calculate_combined_impairment(impairments)
        
        self.assertEqual(combined, 0.0)
        self.assertFalse(valid)
    
    def test_combined_formula_calculation(self):
        """Test combined formula when chart lookup fails."""
        result = self.calculator._calculate_combined_formula(10.0, 5.0)
        
        # Formula: A + B(100-A)/100 = 10 + 5(100-10)/100 = 10 + 4.5 = 14.5
        expected = 14.5
        self.assertAlmostEqual(result, expected, places=1)


class TestMedicalReasoningEngine(unittest.TestCase):
    """Test medical reasoning generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reasoning_engine = MedicalReasoningEngine()
    
    def test_medical_reasoning_generation(self):
        """Test comprehensive medical reasoning generation."""
        diagnosis = Diagnosis(
            id="test_diag",
            description="Lumbar strain",
            icd_code="M54.5"
        )
        
        findings = [
            Finding(
                id="finding1",
                section_id="section1",
                description="Lower back pain with radiation",
                finding_type="symptom",
                page_reference=1
            )
        ]
        
        patient_history = {
            "injury_date": "2024-01-15",
            "injury_mechanism": "lifting heavy object",
            "initial_symptoms": ["back pain", "stiffness"]
        }
        
        examination_data = {
            "range_of_motion": {"lumbar_flexion": 30},
            "patient_age": 45
        }
        
        reasoning = self.reasoning_engine.generate_medical_reasoning(
            diagnosis, findings, patient_history, examination_data
        )
        
        self.assertIsNotNone(reasoning.injury_mechanism_analysis)
        self.assertIsNotNone(reasoning.symptom_progression_narrative)
        self.assertIsNotNone(reasoning.causation_analysis)
        self.assertIsNotNone(reasoning.prognosis_assessment)
        self.assertGreater(len(reasoning.treatment_recommendations), 0)
        self.assertIsNotNone(reasoning.functional_impact_analysis)
    
    def test_injury_mechanism_analysis(self):
        """Test injury mechanism analysis."""
        diagnosis = Diagnosis(id="1", description="cervical strain", icd_code="M54.2")
        patient_history = {"injury_mechanism": "motor vehicle accident"}
        
        analysis = self.reasoning_engine._analyze_injury_mechanism(diagnosis, patient_history)
        
        self.assertIn("mechanism", analysis.lower())
        self.assertGreater(len(analysis), 10)  # Should have substantial content
    
    def test_causation_analysis(self):
        """Test causation analysis generation."""
        diagnosis = Diagnosis(id="1", description="back injury", icd_code="M54.9")
        patient_history = {"injury_date": "2024-01-15"}
        examination_data = {"findings": ["objective abnormalities"]}
        
        causation = self.reasoning_engine._analyze_causation(
            diagnosis, patient_history, examination_data
        )
        
        self.assertIn("reasonable degree of medical probability", causation.lower())
        self.assertIn("causally related", causation.lower())


class TestEnhancedImpairmentCalculator(unittest.TestCase):
    """Test enhanced impairment calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('src.services.enhanced_impairment_calculator.AMAGuidelinesEngine'):
            self.calculator = EnhancedImpairmentCalculator()
    
    def test_range_of_motion_impairment(self):
        """Test ROM-based impairment calculation."""
        rom_measurements = [
            RangeOfMotionMeasurement(
                joint="lumbar_spine",
                motion_type="flexion",
                measured_value=30.0,
                normal_value=60.0
            ),
            RangeOfMotionMeasurement(
                joint="lumbar_spine",
                motion_type="extension",
                measured_value=15.0,
                normal_value=25.0
            )
        ]
        
        impairment, steps, data = self.calculator.calculate_range_of_motion_impairment(
            rom_measurements, BodySystemType.SPINE
        )
        
        self.assertGreater(impairment, 0.0)
        self.assertLessEqual(impairment, 25.0)  # Spine cap
        self.assertGreater(len(steps), 0)
        self.assertIn("lumbar_spine", data)
    
    def test_strength_impairment(self):
        """Test strength-based impairment calculation."""
        strength_tests = [
            StrengthTestResult(
                muscle_group="paraspinal",
                strength_grade="4/5",
                numeric_value=4.0,
                testing_method="manual"
            ),
            StrengthTestResult(
                muscle_group="abdominal",
                strength_grade="3/5",
                numeric_value=3.0,
                testing_method="manual"
            )
        ]
        
        impairment, steps, data = self.calculator.calculate_strength_impairment(
            strength_tests, BodySystemType.SPINE
        )
        
        self.assertGreater(impairment, 0.0)
        self.assertLessEqual(impairment, 50.0)  # Maximum cap
        self.assertGreater(len(steps), 0)
        self.assertIn("paraspinal", data)
    
    def test_functional_impairment(self):
        """Test functional limitation impairment calculation."""
        functional_assessments = [
            FunctionalAssessment(
                activity="lifting",
                limitation_level="moderate",
                percentage_limitation=50.0,
                objective_basis=["ROM limitations", "strength deficits"],
                impact_on_adl="Significant impact on daily activities"
            ),
            FunctionalAssessment(
                activity="walking",
                limitation_level="mild",
                percentage_limitation=25.0,
                objective_basis=["Gait abnormalities"],
                impact_on_adl="Mild impact on mobility"
            )
        ]
        
        impairment, steps, data = self.calculator.calculate_functional_impairment(
            functional_assessments
        )
        
        self.assertGreater(impairment, 0.0)
        self.assertGreater(len(steps), 0)
        self.assertIn("lifting", data)
        self.assertIn("walking", data)


class TestQMEReferenceProcessor(unittest.TestCase):
    """Test QME reference materials processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.integrator = QMEReferenceIntegrator()
    
    @patch('src.services.qme_reference_processor.Path.exists')
    def test_reference_processing(self, mock_exists):
        """Test reference materials processing."""
        mock_exists.return_value = False  # Simulate files not found
        
        result = self.integrator.process_all_references()
        
        # Should complete even with missing files (using defaults)
        self.assertIsInstance(result, bool)
    
    def test_legal_compliance_patterns(self):
        """Test legal compliance pattern retrieval."""
        patterns = self.integrator.get_legal_compliance_patterns()
        
        self.assertIsInstance(patterns, list)
        # Should have at least default patterns
        if patterns:
            pattern = patterns[0]
            self.assertIsNotNone(pattern.requirement_type)
            self.assertIsNotNone(pattern.statutory_reference)
    
    def test_structure_patterns(self):
        """Test structure pattern retrieval."""
        patterns = self.integrator.get_structure_patterns()
        
        self.assertIsInstance(patterns, list)
        # Should have at least default patterns
        if patterns:
            pattern = patterns[0]
            self.assertIsNotNone(pattern.section_name)
            self.assertIsInstance(pattern.section_order, int)


class TestComprehensiveAMAIntegration(unittest.TestCase):
    """Test comprehensive AMA integration service."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch.multiple(
            'src.services.comprehensive_ama_integration',
            AMAGuidelinesEngine=Mock(),
            EnhancedImpairmentCalculator=Mock(),
            QMEReferenceIntegrator=Mock()
        ):
            self.integration = ComprehensiveAMAIntegration()
    
    def test_initialization(self):
        """Test integration service initialization."""
        self.assertIsNotNone(self.integration.ama_engine)
        self.assertIsNotNone(self.integration.impairment_calculator)
        self.assertIsNotNone(self.integration.reference_integrator)
    
    def test_evaluation_data_creation(self):
        """Test comprehensive evaluation data creation."""
        diagnosis = Diagnosis(
            id="test_diag",
            description="Test diagnosis",
            icd_code="M54.9"
        )
        
        evaluation_data = ComprehensiveEvaluationData(
            patient_id="TEST001",
            diagnosis=diagnosis,
            clinical_findings=[],
            rom_measurements=[],
            strength_tests=[],
            functional_assessments=[],
            patient_history={},
            examination_data={},
            patient_factors={}
        )
        
        self.assertEqual(evaluation_data.patient_id, "TEST001")
        self.assertEqual(evaluation_data.diagnosis, diagnosis)
        self.assertIsInstance(evaluation_data.clinical_findings, list)
    
    @patch('src.services.comprehensive_ama_integration.ComprehensiveAMAIntegration._initialize_reference_materials')
    def test_comprehensive_evaluation_mock(self, mock_init):
        """Test comprehensive evaluation with mocked components."""
        # Mock the calculator and engine responses
        mock_impairment_result = Mock()
        mock_impairment_result.final_percentage = 10.0
        mock_impairment_result.quality_indicators = {"overall_quality": 0.85}
        mock_impairment_result.validation_results = {"overall_valid": True}
        mock_impairment_result.recommendations = ["Test recommendation"]
        mock_impairment_result.ama_citations = ["AMA Guides 5th Edition"]
        mock_impairment_result.calculation_steps = ["Step 1: Test calculation"]
        mock_impairment_result.confidence_score = 0.8
        mock_impairment_result.components = Mock()
        mock_impairment_result.components.calculation_method = AMAMethodType.RANGE_OF_MOTION
        mock_impairment_result.components.primary_impairment = 10.0
        mock_impairment_result.components.secondary_impairments = []
        mock_impairment_result.components.combined_impairment = 10.0
        
        mock_reasoning = Mock()
        mock_reasoning.injury_mechanism_analysis = "Test mechanism analysis"
        mock_reasoning.causation_analysis = "Test causation analysis"
        mock_reasoning.treatment_recommendations = ["Physical therapy"]
        
        self.integration.impairment_calculator.calculate_comprehensive_impairment.return_value = mock_impairment_result
        self.integration.ama_engine.generate_comprehensive_medical_reasoning.return_value = mock_reasoning
        
        # Create test evaluation data
        diagnosis = Diagnosis(id="1", description="Test diagnosis", icd_code="M54.9")
        evaluation_data = ComprehensiveEvaluationData(
            patient_id="TEST001",
            diagnosis=diagnosis,
            clinical_findings=[],
            rom_measurements=[],
            strength_tests=[],
            functional_assessments=[],
            patient_history={"injury_date": "2024-01-15"},
            examination_data={"test": "data"},
            patient_factors={"age": 45}
        )
        
        # Perform evaluation
        result = self.integration.perform_comprehensive_evaluation(evaluation_data)
        
        # Verify result
        self.assertEqual(result.patient_id, "TEST001")
        self.assertIsNotNone(result.impairment_calculation)
        self.assertIsNotNone(result.medical_reasoning)
        self.assertIsInstance(result.quality_metrics, dict)
        self.assertIsInstance(result.validation_results, dict)


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete integration workflow."""
    
    def setUp(self):
        """Set up test fixtures for integration testing."""
        self.test_data = self._create_test_data()
    
    def _create_test_data(self) -> ComprehensiveEvaluationData:
        """Create comprehensive test data."""
        diagnosis = Diagnosis(
            id="test_diag_001",
            description="Lumbar disc herniation with radiculopathy",
            icd_code="M51.16"
        )
        
        clinical_findings = [
            Finding(
                id="finding_001",
                description="Lower back pain with radiation to left leg",
                finding_type="symptom"
            ),
            Finding(
                id="finding_002", 
                description="Positive straight leg raise test",
                finding_type="examination"
            )
        ]
        
        rom_measurements = [
            RangeOfMotionMeasurement(
                joint="lumbar_spine",
                motion_type="flexion",
                measured_value=35.0,
                normal_value=60.0,
                measurement_date=datetime.now()
            ),
            RangeOfMotionMeasurement(
                joint="lumbar_spine",
                motion_type="extension",
                measured_value=15.0,
                normal_value=25.0,
                measurement_date=datetime.now()
            )
        ]
        
        strength_tests = [
            StrengthTestResult(
                muscle_group="paraspinal",
                strength_grade="4/5",
                numeric_value=4.0,
                testing_method="manual muscle testing"
            )
        ]
        
        functional_assessments = [
            FunctionalAssessment(
                activity="lifting",
                limitation_level="moderate",
                percentage_limitation=60.0,
                objective_basis=["ROM limitations", "Pain with movement"],
                impact_on_adl="Significant difficulty with lifting activities"
            )
        ]
        
        patient_history = {
            "injury_date": "2024-01-15",
            "injury_mechanism": "lifting heavy box at work",
            "initial_symptoms": ["acute lower back pain", "muscle spasm"],
            "current_symptoms": ["chronic pain", "intermittent radiation"],
            "pre_existing_conditions": []
        }
        
        examination_data = {
            "general_appearance": "Patient appears uncomfortable",
            "gait": "Antalgic gait favoring left side",
            "neurological": "Decreased sensation L5 distribution",
            "special_tests": "Positive SLR at 45 degrees"
        }
        
        patient_factors = {
            "age": 42,
            "gender": "male",
            "occupation": "warehouse worker",
            "dominant_hand": "right",
            "activity_level": "moderate"
        }
        
        return ComprehensiveEvaluationData(
            patient_id="INTEGRATION_TEST_001",
            diagnosis=diagnosis,
            clinical_findings=clinical_findings,
            rom_measurements=rom_measurements,
            strength_tests=strength_tests,
            functional_assessments=functional_assessments,
            patient_history=patient_history,
            examination_data=examination_data,
            patient_factors=patient_factors
        )
    
    @patch('src.services.comprehensive_ama_integration.AMAGuidelinesEngine')
    @patch('src.services.comprehensive_ama_integration.EnhancedImpairmentCalculator')
    @patch('src.services.comprehensive_ama_integration.QMEReferenceIntegrator')
    def test_complete_workflow(self, mock_integrator, mock_calculator, mock_engine):
        """Test complete AMA integration workflow."""
        # Setup mocks
        mock_impairment_result = self._create_mock_impairment_result()
        mock_reasoning = self._create_mock_reasoning()
        
        mock_calculator.return_value.calculate_comprehensive_impairment.return_value = mock_impairment_result
        mock_engine.return_value.generate_comprehensive_medical_reasoning.return_value = mock_reasoning
        mock_integrator.return_value.process_all_references.return_value = True
        
        # Initialize integration service
        integration = ComprehensiveAMAIntegration()
        
        # Perform comprehensive evaluation
        result = integration.perform_comprehensive_evaluation(self.test_data)
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result.patient_id, "INTEGRATION_TEST_001")
        self.assertIsNotNone(result.impairment_calculation)
        self.assertIsNotNone(result.medical_reasoning)
        self.assertIsInstance(result.quality_metrics, dict)
        self.assertIsInstance(result.validation_results, dict)
        self.assertIsInstance(result.recommendations, list)
        
        # Generate report content
        content = integration.generate_ama_compliant_report_content(result)
        
        # Verify content sections
        expected_sections = [
            "impairment_rating", "medical_reasoning", "causation_analysis",
            "future_medical_care", "work_restrictions", "ama_methodology"
        ]
        
        for section in expected_sections:
            self.assertIn(section, content)
            self.assertIsInstance(content[section], str)
            self.assertGreater(len(content[section]), 0)
        
        # Validate AMA compliance
        compliance_report = integration.validate_ama_compliance(result)
        
        self.assertIsInstance(compliance_report, dict)
        self.assertIn("overall_compliant", compliance_report)
        self.assertIn("compliance_score", compliance_report)
    
    def _create_mock_impairment_result(self):
        """Create mock impairment result for testing."""
        mock_result = Mock()
        mock_result.final_percentage = 12.0
        mock_result.quality_indicators = {
            "overall_quality": 0.85,
            "data_completeness": 0.9,
            "validation_score": 0.8
        }
        mock_result.validation_results = {
            "overall_valid": True,
            "percentage_in_range": True,
            "method_appropriate": True
        }
        mock_result.recommendations = [
            "Consider additional ROM measurements",
            "Document patient cooperation during testing"
        ]
        mock_result.ama_citations = [
            "AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition",
            "Chapter 15, Table 15-7: Lumbar Spine Range of Motion Impairment"
        ]
        mock_result.calculation_steps = [
            "Lumbar flexion: 35°/60° = 42% loss",
            "Lumbar extension: 15°/25° = 40% loss",
            "Combined ROM impairment: 12% whole person"
        ]
        mock_result.confidence_score = 0.82
        
        # Mock components
        mock_components = Mock()
        mock_components.calculation_method = AMAMethodType.RANGE_OF_MOTION
        mock_components.primary_impairment = 12.0
        mock_components.secondary_impairments = []
        mock_components.combined_impairment = 12.0
        mock_result.components = mock_components
        
        return mock_result
    
    def _create_mock_reasoning(self):
        """Create mock medical reasoning for testing."""
        mock_reasoning = Mock()
        mock_reasoning.injury_mechanism_analysis = (
            "The mechanism of injury involving lifting a heavy box is consistent with "
            "lumbar disc herniation. The forces involved in lifting with poor body "
            "mechanics can result in disc protrusion and nerve root compression."
        )
        mock_reasoning.symptom_progression_narrative = (
            "Initially, the patient experienced acute lower back pain and muscle spasm "
            "following the lifting incident. Over time, symptoms have evolved to include "
            "chronic pain with intermittent radiation to the left leg, consistent with "
            "nerve root irritation."
        )
        mock_reasoning.causation_analysis = (
            "Based on reasonable medical probability, the lumbar disc herniation is "
            "causally related to the workplace lifting incident given the temporal "
            "relationship and mechanism of injury."
        )
        mock_reasoning.prognosis_assessment = (
            "The prognosis is fair to good with appropriate treatment. Conservative "
            "management may provide significant improvement, though some residual "
            "symptoms may persist."
        )
        mock_reasoning.treatment_recommendations = [
            "Physical therapy focusing on core strengthening",
            "Anti-inflammatory medications as needed",
            "Ergonomic training for proper lifting techniques",
            "Consider epidural injection if conservative treatment fails"
        ]
        mock_reasoning.functional_impact_analysis = (
            "The lumbar disc herniation results in functional limitations affecting "
            "lifting, bending, and prolonged activities. These limitations impact "
            "both work capacity and activities of daily living."
        )
        mock_reasoning.supporting_evidence = [
            "Objective ROM limitations",
            "Positive neurological findings",
            "Consistent symptom pattern",
            "Temporal relationship to injury"
        ]
        mock_reasoning.confidence_level = "High confidence based on comprehensive clinical data"
        
        return mock_reasoning


if __name__ == '__main__':
    unittest.main()