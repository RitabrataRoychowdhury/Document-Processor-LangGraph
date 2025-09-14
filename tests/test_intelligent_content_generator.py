"""
Tests for the Intelligent Content Generator

This module tests the intelligent content generation capabilities including
section-by-section content generation, medical reasoning, and quality assessment.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import logging

from src.services.intelligent_content_generator import (
    IntelligentContentGenerator,
    HistoryOfPresentIllnessGenerator,
    PhysicalExaminationGenerator,
    DiagnosticStudiesGenerator,
    CausationAnalysisGenerator,
    FutureMedicalCareGenerator,
    MedicalNarrative
)
from src.models.knowledge_graph import (
    KnowledgeGraph,
    MedicalEntity,
    MedicalEntityType,
    ProvenanceReference,
    ValidationStatus
)
from src.services.ama_guidelines_engine import AMAGuidelinesEngine
from src.config.qme_gold_standard_config import QMEGoldStandardConfig


@pytest.fixture
def mock_logger():
    """Create mock logger for testing"""
    return Mock(spec=logging.Logger)


@pytest.fixture
def mock_ama_engine():
    """Create mock AMA guidelines engine"""
    engine = Mock()
    engine.get_treatment_guidelines.return_value = {
        'recommendations': [
            'Physical therapy for range of motion improvement',
            'Anti-inflammatory medication as needed'
        ]
    }
    return engine


@pytest.fixture
def mock_config():
    """Create mock QME configuration"""
    return Mock()


@pytest.fixture
def sample_knowledge_graph():
    """Create sample knowledge graph for testing"""
    kg = KnowledgeGraph()
    
    # Add injury entity
    injury_entity = MedicalEntity(
        id="injury_1",
        entity_type=MedicalEntityType.WORK_INJURY,
        content="lifting heavy box resulting in lower back strain",
        confidence_score=0.9,
        metadata={'date': datetime(2024, 1, 15)}
    )
    kg.add_entity(injury_entity)
    
    # Add diagnosis entity
    diagnosis_entity = MedicalEntity(
        id="diagnosis_1",
        entity_type=MedicalEntityType.DIAGNOSIS,
        content="lumbar strain with muscle spasm",
        confidence_score=0.85,
        ama_references=["Chapter 15, Table 15-3"]
    )
    kg.add_entity(diagnosis_entity)
    
    # Add symptom entities
    pain_entity = MedicalEntity(
        id="symptom_1",
        entity_type=MedicalEntityType.PAIN,
        content="lower back pain radiating to left leg",
        confidence_score=0.8
    )
    kg.add_entity(pain_entity)
    
    # Add ROM measurement
    rom_entity = MedicalEntity(
        id="rom_1",
        entity_type=MedicalEntityType.ROM,
        content="lumbar flexion",
        confidence_score=0.9,
        metadata={'measurement': 45}
    )
    kg.add_entity(rom_entity)
    
    # Add imaging study
    imaging_entity = MedicalEntity(
        id="imaging_1",
        entity_type=MedicalEntityType.IMAGING_STUDY,
        content="mild disc bulging at L4-L5",
        confidence_score=0.85,
        metadata={'date': datetime(2024, 1, 20)}
    )
    kg.add_entity(imaging_entity)
    
    # Add treatment entity
    treatment_entity = MedicalEntity(
        id="treatment_1",
        entity_type=MedicalEntityType.TREATMENT,
        content="physical therapy and anti-inflammatory medication",
        confidence_score=0.8,
        metadata={'date': datetime(2024, 1, 25)}
    )
    kg.add_entity(treatment_entity)
    
    return kg


class TestHistoryOfPresentIllnessGenerator:
    """Test history of present illness generation"""
    
    def test_generate_complete_history(self, mock_logger, sample_knowledge_graph):
        """Test generating complete history with all components"""
        generator = HistoryOfPresentIllnessGenerator(mock_logger)
        
        narrative = generator.generate_content(sample_knowledge_graph, {})
        
        assert narrative.section_name == "History of Present Illness"
        assert "lifting heavy box" in narrative.content
        assert "physical therapy" in narrative.content
        assert "lower back pain" in narrative.content
        assert narrative.confidence_score > 0.5
        assert len(narrative.source_entities) > 0
    
    def test_generate_minimal_history(self, mock_logger):
        """Test generating history with minimal information"""
        generator = HistoryOfPresentIllnessGenerator(mock_logger)
        empty_kg = KnowledgeGraph()
        
        narrative = generator.generate_content(empty_kg, {})
        
        assert narrative.section_name == "History of Present Illness"
        assert "industrial injury" in narrative.content
        assert narrative.confidence_score < 0.5
    
    def test_injury_mechanism_extraction(self, mock_logger, sample_knowledge_graph):
        """Test extraction of injury mechanism"""
        generator = HistoryOfPresentIllnessGenerator(mock_logger)
        
        injury_entities = generator._extract_injury_timeline(sample_knowledge_graph)
        
        assert len(injury_entities) == 1
        assert injury_entities[0].entity_type == MedicalEntityType.WORK_INJURY
        assert "lifting heavy box" in injury_entities[0].content


class TestPhysicalExaminationGenerator:
    """Test physical examination content generation"""
    
    def test_generate_complete_examination(self, mock_logger, sample_knowledge_graph):
        """Test generating complete physical examination"""
        generator = PhysicalExaminationGenerator(mock_logger)
        
        narrative = generator.generate_content(sample_knowledge_graph, {})
        
        assert narrative.section_name == "Physical Examination"
        assert "Range of motion testing" in narrative.content
        assert "45 degrees" in narrative.content
        assert narrative.confidence_score > 0.3
    
    def test_rom_measurement_extraction(self, mock_logger, sample_knowledge_graph):
        """Test ROM measurement extraction"""
        generator = PhysicalExaminationGenerator(mock_logger)
        
        rom_entities = generator._extract_rom_measurements(sample_knowledge_graph)
        
        assert len(rom_entities) == 1
        assert rom_entities[0].entity_type == MedicalEntityType.ROM
        assert rom_entities[0].metadata['measurement'] == 45
    
    def test_generate_fallback_examination(self, mock_logger):
        """Test fallback examination generation"""
        generator = PhysicalExaminationGenerator(mock_logger)
        empty_kg = KnowledgeGraph()
        
        narrative = generator.generate_content(empty_kg, {})
        
        assert narrative.section_name == "Physical Examination"
        assert "Physical examination was performed" in narrative.content
        assert narrative.confidence_score < 0.5


class TestDiagnosticStudiesGenerator:
    """Test diagnostic studies content generation"""
    
    def test_generate_imaging_content(self, mock_logger, sample_knowledge_graph):
        """Test generating diagnostic studies with imaging"""
        generator = DiagnosticStudiesGenerator(mock_logger)
        
        narrative = generator.generate_content(sample_knowledge_graph, {})
        
        assert narrative.section_name == "Diagnostic Studies"
        assert "Imaging studies include" in narrative.content
        assert "disc bulging" in narrative.content
        assert narrative.confidence_score > 0.5
    
    def test_no_studies_available(self, mock_logger):
        """Test handling when no diagnostic studies are available"""
        generator = DiagnosticStudiesGenerator(mock_logger)
        empty_kg = KnowledgeGraph()
        
        narrative = generator.generate_content(empty_kg, {})
        
        assert "No diagnostic studies were available" in narrative.content
        assert narrative.confidence_score > 0.2  # Still valid if no studies


class TestCausationAnalysisGenerator:
    """Test causation analysis generation"""
    
    def test_generate_causation_with_industrial_factors(self, mock_logger, sample_knowledge_graph):
        """Test causation analysis with industrial factors"""
        generator = CausationAnalysisGenerator(mock_logger)
        
        narrative = generator.generate_content(sample_knowledge_graph, {})
        
        assert narrative.section_name == "Causation Analysis"
        assert "industrially related" in narrative.content or "causally related" in narrative.content
        assert "reasonable" in narrative.content and "medical probability" in narrative.content
        assert len(narrative.legal_citations) > 0
    
    def test_probability_statement_generation(self, mock_logger):
        """Test medical probability statement generation"""
        generator = CausationAnalysisGenerator(mock_logger)
        
        # Test with causally related analysis
        analysis = "The industrial injury is causally related to the current condition."
        probability = generator._generate_probability_statement(analysis)
        
        assert "reasonable degree of medical probability" in probability
    
    def test_legal_citations_included(self, mock_logger, sample_knowledge_graph):
        """Test that legal citations are included"""
        generator = CausationAnalysisGenerator(mock_logger)
        
        citations = generator._get_legal_citations()
        
        assert "Labor Code Section 3208.1" in citations
        assert "Labor Code Section 4663" in citations


class TestFutureMedicalCareGenerator:
    """Test future medical care recommendations generation"""
    
    def test_generate_fmc_recommendations(self, mock_logger, mock_ama_engine, sample_knowledge_graph):
        """Test generating future medical care recommendations"""
        generator = FutureMedicalCareGenerator(mock_ama_engine, mock_logger)
        
        narrative = generator.generate_content(sample_knowledge_graph, {})
        
        assert narrative.section_name == "Future Medical Care"
        assert "future medical care should include" in narrative.content
        assert narrative.confidence_score > 0.5
        mock_ama_engine.get_treatment_guidelines.assert_called()
    
    def test_treatment_recommendation_logic(self, mock_logger, mock_ama_engine, sample_knowledge_graph):
        """Test treatment recommendation logic"""
        generator = FutureMedicalCareGenerator(mock_ama_engine, mock_logger)
        
        # Add pain diagnosis to trigger pain management recommendations
        pain_diagnosis = MedicalEntity(
            id="pain_diagnosis",
            entity_type=MedicalEntityType.DIAGNOSIS,
            content="chronic pain syndrome",
            confidence_score=0.8
        )
        sample_knowledge_graph.add_entity(pain_diagnosis)
        
        diagnoses = generator._extract_diagnoses(sample_knowledge_graph)
        recommendations = generator._generate_treatment_recommendations(diagnoses, [], [])
        
        assert any("pain management" in rec.lower() for rec in recommendations)
    
    def test_ama_recommendations_integration(self, mock_logger, mock_ama_engine, sample_knowledge_graph):
        """Test AMA guidelines integration in recommendations"""
        generator = FutureMedicalCareGenerator(mock_ama_engine, mock_logger)
        
        diagnoses = generator._extract_diagnoses(sample_knowledge_graph)
        ama_recs = generator._get_ama_based_recommendations(diagnoses)
        
        assert len(ama_recs) > 0
        mock_ama_engine.get_treatment_guidelines.assert_called()


class TestIntelligentContentGenerator:
    """Test main intelligent content generator"""
    
    def test_initialization(self, mock_ama_engine, mock_config, mock_logger):
        """Test proper initialization of content generator"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        assert generator.ama_engine == mock_ama_engine
        assert generator.config == mock_config
        assert generator.logger == mock_logger
        assert len(generator.generators) == 5
    
    def test_generate_section_content(self, mock_ama_engine, mock_config, mock_logger, sample_knowledge_graph):
        """Test generating content for a specific section"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        narrative = generator.generate_section_content(
            "History of Present Illness", 
            sample_knowledge_graph
        )
        
        assert narrative.section_name == "History of Present Illness"
        assert len(narrative.content) > 0
        assert narrative.confidence_score > 0
    
    def test_generate_comprehensive_report(self, mock_ama_engine, mock_config, mock_logger, sample_knowledge_graph):
        """Test generating comprehensive report content"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        sections = [
            "History of Present Illness",
            "Physical Examination",
            "Diagnostic Studies"
        ]
        
        report_content = generator.generate_comprehensive_report_content(
            sample_knowledge_graph, 
            sections
        )
        
        assert len(report_content) == 3
        assert all(section in report_content for section in sections)
        assert all(isinstance(narrative, MedicalNarrative) for narrative in report_content.values())
    
    def test_unknown_section_handling(self, mock_ama_engine, mock_config, mock_logger, sample_knowledge_graph):
        """Test handling of unknown section types"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        narrative = generator.generate_section_content(
            "Unknown Section", 
            sample_knowledge_graph
        )
        
        assert narrative.section_name == "Unknown Section"
        assert "requires detailed review" in narrative.content
        assert narrative.confidence_score < 0.5
    
    def test_content_enhancement(self, mock_ama_engine, mock_config, mock_logger):
        """Test content quality enhancement"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        # Create test narrative
        narrative = MedicalNarrative(
            section_name="Test",
            content="The patient hurt their back and it was sore",
            confidence_score=0.8,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={}
        )
        
        enhanced = generator._enhance_narrative_quality(narrative)
        
        assert "pain" in enhanced.content  # 'hurt' should be replaced with 'pain'
        assert "tender" in enhanced.content  # 'sore' should be replaced with 'tender'
        assert enhanced.quality_indicators.get('enhanced') is True
    
    def test_medical_terminology_improvement(self, mock_ama_engine, mock_config, mock_logger):
        """Test medical terminology improvement"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        content = "The patient hurt their back and it was sore and weak"
        improved = generator._improve_medical_terminology(content)
        
        assert "pain" in improved
        assert "tender" in improved
        assert "decreased strength" in improved
    
    def test_professional_tone_enforcement(self, mock_ama_engine, mock_config, mock_logger):
        """Test professional tone enforcement"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        content = "The patient says they have back pain"
        professional = generator._ensure_professional_tone(content)
        
        assert "reports" in professional
        assert professional.endswith('.')
    
    def test_readability_score_calculation(self, mock_ama_engine, mock_config, mock_logger):
        """Test readability score calculation"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        # Test optimal length (15-20 words per sentence)
        optimal_content = "The patient reports lower back pain following an industrial injury that occurred while lifting heavy equipment at work."
        score = generator._calculate_readability_score(optimal_content)
        assert score >= 0.8
        
        # Test too short
        short_content = "Pain. Injury."
        score = generator._calculate_readability_score(short_content)
        assert score < 1.0
    
    def test_error_handling(self, mock_ama_engine, mock_config, mock_logger):
        """Test error handling in content generation"""
        generator = IntelligentContentGenerator(mock_ama_engine, mock_config, mock_logger)
        
        # Mock a generator that raises an exception
        generator.generators['history_of_present_illness'] = Mock()
        generator.generators['history_of_present_illness'].generate_content.side_effect = Exception("Test error")
        
        narrative = generator.generate_section_content(
            "History of Present Illness", 
            KnowledgeGraph()
        )
        
        assert "error" in narrative.content.lower()
        assert narrative.confidence_score < 0.5
        assert narrative.quality_indicators.get('error') is True


if __name__ == "__main__":
    pytest.main([__file__])