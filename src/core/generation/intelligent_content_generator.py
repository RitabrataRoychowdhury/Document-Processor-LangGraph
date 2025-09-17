"""
Enhanced Evidence-Driven Content Generation Engine for QME Reports

This module provides evidence-constrained content generation that produces
professional medical narratives using only validated fields with complete
provenance tracking and source citation management.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from src.models.knowledge_graph import KnowledgeGraph, MedicalEntity, EntityRelationship, MedicalEntityType
from src.infrastructure.knowledge.ama_guidelines_engine import AMAGuidelinesEngine
from src.infrastructure.knowledge.evidence_rag_service import EvidenceRAGService, EvidenceRetrievalResult, EvidenceSnippet, CanonicalContent
from src.core.validation.qme_field_validator import ValidationReport
from src.config.qme_gold_standard_config import QMEGoldStandardConfig


@dataclass
class MedicalNarrative:
    """Enhanced evidence-driven medical narrative content"""
    section_name: str
    content: str
    confidence_score: float
    source_entities: List[str]
    ama_references: List[str]
    legal_citations: List[str]
    quality_indicators: Dict[str, Any]
    
    # Evidence-first enhancements
    evidence_snippets: List[EvidenceSnippet] = field(default_factory=list)
    validated_fields_used: Dict[str, Any] = field(default_factory=dict)
    source_citations: List[str] = field(default_factory=list)
    provenance_complete: bool = False
    placeholder_text_removed: bool = True
    evidence_backing_complete: bool = False


@dataclass
class ReasoningResult:
    """Medical reasoning analysis result"""
    conclusion: str
    supporting_evidence: List[str]
    confidence_level: str
    medical_probability: str
    citations: List[str]


@dataclass
class ComplianceText:
    """Legal compliance text generation result"""
    content: str
    statutory_references: List[str]
    mandatory_elements: List[str]
    validation_status: bool


@dataclass
class ImpairmentRating:
    """Calculated impairment rating with documentation"""
    body_part: str
    rating_percentage: int
    ama_table_reference: str
    calculation_steps: List[str]
    supporting_measurements: Dict[str, Any]
    confidence_score: float


class IContentGenerator(ABC):
    """Abstract interface for evidence-constrained content generation components"""
    
    @abstractmethod
    def generate_content(self, knowledge_graph: KnowledgeGraph, context: Dict[str, Any]) -> MedicalNarrative:
        """Generate content based on knowledge graph and context"""
        pass
    
    @abstractmethod
    def generate_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                            evidence_retrieval: EvidenceRetrievalResult,
                                            context: Dict[str, Any]) -> MedicalNarrative:
        """Generate content using only validated fields and evidence snippets"""
        pass


class HistoryOfPresentIllnessGenerator(IContentGenerator):
    """Generates evidence-constrained history of present illness narratives"""
    
    def __init__(self, evidence_rag_service: EvidenceRAGService, logger: logging.Logger):
        self.evidence_rag_service = evidence_rag_service
        self.logger = logger
    
    def generate_content(self, knowledge_graph: KnowledgeGraph, context: Dict[str, Any]) -> MedicalNarrative:
        """Generate history of present illness narrative"""
        try:
            # Extract injury mechanism and timeline
            injury_entities = self._extract_injury_timeline(knowledge_graph)
            treatment_history = self._extract_treatment_timeline(knowledge_graph)
            current_symptoms = self._extract_current_symptoms(knowledge_graph)
            
            # Build coherent narrative
            narrative_parts = []
            
            # Injury mechanism
            if injury_entities:
                mechanism_text = self._generate_injury_mechanism_text(injury_entities)
                narrative_parts.append(mechanism_text)
            
            # Treatment progression
            if treatment_history:
                treatment_text = self._generate_treatment_progression_text(treatment_history)
                narrative_parts.append(treatment_text)
            
            # Current status
            if current_symptoms:
                current_text = self._generate_current_status_text(current_symptoms)
                narrative_parts.append(current_text)
            
            content = " ".join(narrative_parts) if narrative_parts else ""
            
            # If no content generated, use fallback
            if not content.strip():
                return self._generate_fallback_history()
            
            return MedicalNarrative(
                section_name="History of Present Illness",
                content=content,
                confidence_score=self._calculate_confidence(injury_entities, treatment_history, current_symptoms),
                source_entities=[e.id for e in injury_entities + treatment_history + current_symptoms],
                ama_references=[],
                legal_citations=[],
                quality_indicators=self._assess_narrative_quality(content)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating history of present illness: {str(e)}")
            return self._generate_fallback_history()
    
    def _extract_injury_timeline(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract injury-related entities with timeline information"""
        injury_entities = []
        for entity in kg.entities.values():
            if entity.entity_type in [MedicalEntityType.WORK_INJURY, MedicalEntityType.CLAIM]:
                injury_entities.append(entity)
        
        # Sort by date if available
        return sorted(injury_entities, key=lambda x: x.metadata.get('date', datetime.min))
    
    def _extract_treatment_timeline(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract treatment entities in chronological order"""
        treatment_entities = []
        for entity in kg.entities.values():
            if entity.entity_type in [MedicalEntityType.TREATMENT, MedicalEntityType.PROCEDURE, 
                                    MedicalEntityType.MEDICATION, MedicalEntityType.THERAPY]:
                treatment_entities.append(entity)
        
        return sorted(treatment_entities, key=lambda x: x.metadata.get('date', datetime.min))
    
    def _extract_current_symptoms(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract current symptom and complaint entities"""
        symptom_entities = []
        for entity in kg.entities.values():
            if entity.entity_type in [MedicalEntityType.SYMPTOM, MedicalEntityType.COMPLAINT, 
                                    MedicalEntityType.PAIN, MedicalEntityType.LIMITATION]:
                symptom_entities.append(entity)
        
        return symptom_entities
    
    def _generate_injury_mechanism_text(self, injury_entities: List[MedicalEntity]) -> str:
        """Generate injury mechanism narrative text"""
        if not injury_entities:
            return ""
        
        primary_injury = injury_entities[0]
        date_text = ""
        if 'date' in primary_injury.metadata:
            date_text = f"On {primary_injury.metadata['date'].strftime('%B %d, %Y')}, "
        
        mechanism = primary_injury.content
        return f"{date_text}the patient sustained {mechanism}."
    
    def _generate_treatment_progression_text(self, treatment_history: List[MedicalEntity]) -> str:
        """Generate treatment progression narrative"""
        if not treatment_history:
            return ""
        
        treatment_text = "The patient subsequently received treatment including "
        treatments = [entity.content for entity in treatment_history[:5]]  # Limit to first 5
        
        if len(treatments) == 1:
            treatment_text += treatments[0]
        elif len(treatments) == 2:
            treatment_text += f"{treatments[0]} and {treatments[1]}"
        else:
            treatment_text += ", ".join(treatments[:-1]) + f", and {treatments[-1]}"
        
        return treatment_text + "."
    
    def _generate_current_status_text(self, current_symptoms: List[MedicalEntity]) -> str:
        """Generate current symptom status text"""
        if not current_symptoms:
            return ""
        
        symptoms = [entity.content for entity in current_symptoms[:3]]  # Limit to top 3
        
        if len(symptoms) == 1:
            return f"The patient currently reports {symptoms[0]}."
        elif len(symptoms) == 2:
            return f"The patient currently reports {symptoms[0]} and {symptoms[1]}."
        else:
            return f"The patient currently reports {', '.join(symptoms[:-1])}, and {symptoms[-1]}."
    
    def _calculate_confidence(self, injury_entities: List, treatment_history: List, current_symptoms: List) -> float:
        """Calculate confidence score based on available information"""
        total_entities = len(injury_entities) + len(treatment_history) + len(current_symptoms)
        if total_entities == 0:
            return 0.0
        elif total_entities < 3:
            return 0.4
        elif total_entities < 6:
            return 0.7
        else:
            return 0.9
    
    def _assess_narrative_quality(self, content: str) -> Dict[str, Any]:
        """Assess quality indicators of generated narrative"""
        return {
            'word_count': len(content.split()),
            'sentence_count': len([s for s in content.split('.') if s.strip()]),
            'has_timeline': 'subsequently' in content.lower() or 'then' in content.lower(),
            'has_mechanism': 'sustained' in content.lower() or 'injured' in content.lower(),
            'completeness_score': min(1.0, len(content.split()) / 100)  # Target ~100 words
        }
    
    def generate_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                            evidence_retrieval: EvidenceRetrievalResult,
                                            context: Dict[str, Any]) -> MedicalNarrative:
        """Generate history using only validated fields and evidence snippets"""
        try:
            self.logger.info("Generating evidence-constrained history of present illness")
            
            # Build narrative from validated fields only
            narrative_parts = []
            
            # Injury mechanism from validated fields
            if 'injury_mechanism' in validated_fields and 'injury_date' in validated_fields:
                injury_text = self._generate_validated_injury_text(
                    validated_fields['injury_mechanism'], 
                    validated_fields['injury_date']
                )
                narrative_parts.append(injury_text)
            
            # Treatment history from validated fields
            if 'treatment_history' in validated_fields:
                treatment_text = self._generate_validated_treatment_text(validated_fields['treatment_history'])
                narrative_parts.append(treatment_text)
            
            # Current symptoms from validated fields
            if 'current_symptoms' in validated_fields:
                symptoms_text = self._generate_validated_symptoms_text(validated_fields['current_symptoms'])
                narrative_parts.append(symptoms_text)
            
            # Use evidence snippets to enhance narrative
            evidence_enhanced_parts = self._enhance_with_evidence_snippets(
                narrative_parts, evidence_retrieval.evidence_snippets
            )
            
            content = " ".join(evidence_enhanced_parts) if evidence_enhanced_parts else ""
            
            # Validate no placeholder text remains
            content = self._remove_placeholder_text(content)
            
            # Generate source citations
            source_citations = self.evidence_rag_service.get_source_citations(
                evidence_retrieval.evidence_snippets, 
                evidence_retrieval.canonical_content
            )
            
            return MedicalNarrative(
                section_name="History of Present Illness",
                content=content,
                confidence_score=self._calculate_evidence_confidence(validated_fields, evidence_retrieval),
                source_entities=list(validated_fields.keys()),
                ama_references=[c.ama_reference for c in evidence_retrieval.canonical_content if c.ama_reference],
                legal_citations=[],
                quality_indicators=self._assess_evidence_quality(content, validated_fields),
                evidence_snippets=evidence_retrieval.evidence_snippets,
                validated_fields_used=validated_fields,
                source_citations=source_citations,
                provenance_complete=evidence_retrieval.provenance_complete,
                placeholder_text_removed=True,
                evidence_backing_complete=len(evidence_retrieval.evidence_snippets) > 0
            )
            
        except Exception as e:
            self.logger.error(f"Error generating evidence-constrained history: {str(e)}")
            return self._generate_evidence_fallback_history()
    
    def _generate_validated_injury_text(self, injury_mechanism: str, injury_date: str) -> str:
        """Generate injury text using only validated fields"""
        try:
            # Parse injury date if it's a string
            if isinstance(injury_date, str):
                date_text = f"On {injury_date}, "
            else:
                date_text = f"On {injury_date.strftime('%B %d, %Y')}, " if hasattr(injury_date, 'strftime') else ""
            
            return f"{date_text}the patient sustained {injury_mechanism}."
        except Exception as e:
            self.logger.warning(f"Error generating validated injury text: {str(e)}")
            return f"The patient sustained {injury_mechanism}."
    
    def _generate_validated_treatment_text(self, treatment_history: List[str]) -> str:
        """Generate treatment text using only validated treatment data"""
        if not treatment_history:
            return ""
        
        treatment_text = "The patient subsequently received treatment including "
        
        if len(treatment_history) == 1:
            treatment_text += treatment_history[0]
        elif len(treatment_history) == 2:
            treatment_text += f"{treatment_history[0]} and {treatment_history[1]}"
        else:
            treatment_text += ", ".join(treatment_history[:-1]) + f", and {treatment_history[-1]}"
        
        return treatment_text + "."
    
    def _generate_validated_symptoms_text(self, current_symptoms: List[str]) -> str:
        """Generate symptoms text using only validated symptom data"""
        if not current_symptoms:
            return ""
        
        if len(current_symptoms) == 1:
            return f"The patient currently reports {current_symptoms[0]}."
        elif len(current_symptoms) == 2:
            return f"The patient currently reports {current_symptoms[0]} and {current_symptoms[1]}."
        else:
            return f"The patient currently reports {', '.join(current_symptoms[:-1])}, and {current_symptoms[-1]}."
    
    def _enhance_with_evidence_snippets(self, narrative_parts: List[str], 
                                      evidence_snippets: List[EvidenceSnippet]) -> List[str]:
        """Enhance narrative with evidence snippet context"""
        enhanced_parts = narrative_parts.copy()
        
        # Add relevant evidence context where appropriate
        for snippet in evidence_snippets[:3]:  # Limit to top 3 most relevant
            if snippet.content and len(snippet.content) > 20:
                # Add evidence context if it provides additional medical detail
                if any(keyword in snippet.content.lower() for keyword in ['mechanism', 'injury', 'treatment']):
                    enhanced_parts.append(f"Medical documentation indicates {snippet.content.lower()}.")
        
        return enhanced_parts
    
    def _remove_placeholder_text(self, content: str) -> str:
        """Remove any placeholder text from generated content"""
        placeholders = [
            '[PLACEHOLDER]', '[TBD]', '[TO BE DETERMINED]', '[NEEDS REVIEW]',
            'PLACEHOLDER', 'TBD', 'TO BE DETERMINED', 'NEEDS REVIEW'
        ]
        
        cleaned_content = content
        for placeholder in placeholders:
            cleaned_content = cleaned_content.replace(placeholder, '')
        
        # Remove empty sentences
        sentences = [s.strip() for s in cleaned_content.split('.') if s.strip()]
        return '. '.join(sentences) + '.' if sentences else ""
    
    def _calculate_evidence_confidence(self, validated_fields: Dict[str, Any], 
                                     evidence_retrieval: EvidenceRetrievalResult) -> float:
        """Calculate confidence based on validated fields and evidence quality"""
        field_confidence = min(1.0, len(validated_fields) / 5.0)  # Target 5 key fields
        evidence_confidence = evidence_retrieval.confidence_score
        
        # Weighted combination: 60% validated fields, 40% evidence quality
        return (field_confidence * 0.6) + (evidence_confidence * 0.4)
    
    def _assess_evidence_quality(self, content: str, validated_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of evidence-based narrative"""
        return {
            'word_count': len(content.split()),
            'validated_fields_count': len(validated_fields),
            'has_injury_mechanism': 'injury_mechanism' in validated_fields,
            'has_treatment_history': 'treatment_history' in validated_fields,
            'has_current_symptoms': 'current_symptoms' in validated_fields,
            'evidence_based': True,
            'placeholder_free': '[' not in content and 'PLACEHOLDER' not in content.upper()
        }
    
    def _generate_evidence_fallback_history(self) -> MedicalNarrative:
        """Generate evidence-based fallback history"""
        return MedicalNarrative(
            section_name="History of Present Illness",
            content="History of present illness requires validated evidence from medical documentation. Additional field extraction and validation needed.",
            confidence_score=0.1,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'evidence_fallback': True},
            evidence_snippets=[],
            validated_fields_used={},
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_fallback_history(self) -> MedicalNarrative:
        """Generate fallback history when extraction fails"""
        return MedicalNarrative(
            section_name="History of Present Illness",
            content="The patient reports an industrial injury. Further details regarding the mechanism of injury, treatment history, and current symptoms require additional documentation review.",
            confidence_score=0.2,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'fallback': True}
        )


class PhysicalExaminationGenerator(IContentGenerator):
    """Generates evidence-constrained physical examination content"""
    
    def __init__(self, evidence_rag_service: EvidenceRAGService, logger: logging.Logger):
        self.evidence_rag_service = evidence_rag_service
        self.logger = logger
    
    def generate_content(self, knowledge_graph: KnowledgeGraph, context: Dict[str, Any]) -> MedicalNarrative:
        """Generate physical examination narrative"""
        try:
            # Extract examination findings
            rom_measurements = self._extract_rom_measurements(knowledge_graph)
            strength_tests = self._extract_strength_tests(knowledge_graph)
            neurological_findings = self._extract_neurological_findings(knowledge_graph)
            general_appearance = self._extract_general_appearance(knowledge_graph)
            
            # Build examination narrative
            narrative_parts = []
            
            # General appearance
            if general_appearance:
                narrative_parts.append(self._generate_general_appearance_text(general_appearance))
            
            # ROM measurements
            if rom_measurements:
                narrative_parts.append(self._generate_rom_text(rom_measurements))
            
            # Strength testing
            if strength_tests:
                narrative_parts.append(self._generate_strength_text(strength_tests))
            
            # Neurological assessment
            if neurological_findings:
                narrative_parts.append(self._generate_neurological_text(neurological_findings))
            
            content = " ".join(narrative_parts) if narrative_parts else ""
            
            # If no content generated, use fallback
            if not content.strip():
                return self._generate_fallback_examination()
            
            return MedicalNarrative(
                section_name="Physical Examination",
                content=content,
                confidence_score=self._calculate_exam_confidence(rom_measurements, strength_tests, neurological_findings),
                source_entities=self._get_all_source_entities(rom_measurements, strength_tests, neurological_findings, general_appearance),
                ama_references=self._extract_ama_references(rom_measurements),
                legal_citations=[],
                quality_indicators=self._assess_exam_quality(content, rom_measurements, strength_tests)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating physical examination: {str(e)}")
            return self._generate_fallback_examination()  
  
    def _extract_rom_measurements(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract range of motion measurement entities"""
        rom_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.ROM:
                rom_entities.append(entity)
            elif any(keyword in entity.content.lower() for keyword in ['flexion', 'extension', 'rotation', 'degrees']):
                rom_entities.append(entity)
        return rom_entities
    
    def _extract_strength_tests(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract strength testing entities"""
        strength_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.STRENGTH_TEST:
                strength_entities.append(entity)
        return strength_entities
    
    def _extract_neurological_findings(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract neurological examination findings"""
        neuro_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.NEUROLOGICAL:
                neuro_entities.append(entity)
        return neuro_entities
    
    def _extract_general_appearance(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract general appearance and inspection findings"""
        appearance_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.APPEARANCE:
                appearance_entities.append(entity)
        return appearance_entities
    
    def _generate_general_appearance_text(self, appearance_entities: List[MedicalEntity]) -> str:
        """Generate general appearance examination text"""
        if not appearance_entities:
            return "The patient appears comfortable and in no acute distress."
        
        findings = [entity.content for entity in appearance_entities]
        return f"On examination, the patient {', '.join(findings)}."
    
    def _generate_rom_text(self, rom_entities: List[MedicalEntity]) -> str:
        """Generate range of motion examination text"""
        if not rom_entities:
            return ""
        
        rom_text = "Range of motion testing reveals: "
        rom_findings = []
        
        for entity in rom_entities:
            if 'measurement' in entity.metadata:
                measurement = entity.metadata['measurement']
                rom_findings.append(f"{entity.content} {measurement} degrees")
            else:
                rom_findings.append(entity.content)
        
        return rom_text + "; ".join(rom_findings) + "."
    
    def _generate_strength_text(self, strength_entities: List[MedicalEntity]) -> str:
        """Generate strength testing examination text"""
        if not strength_entities:
            return ""
        
        strength_text = "Manual muscle testing demonstrates: "
        strength_findings = [entity.content for entity in strength_entities]
        
        return strength_text + "; ".join(strength_findings) + "."
    
    def _generate_neurological_text(self, neuro_entities: List[MedicalEntity]) -> str:
        """Generate neurological examination text"""
        if not neuro_entities:
            return ""
        
        neuro_text = "Neurological examination shows: "
        neuro_findings = [entity.content for entity in neuro_entities]
        
        return neuro_text + "; ".join(neuro_findings) + "."
    
    def _calculate_exam_confidence(self, rom_entities: List, strength_entities: List, neuro_entities: List) -> float:
        """Calculate confidence based on examination completeness"""
        total_findings = len(rom_entities) + len(strength_entities) + len(neuro_entities)
        
        if total_findings == 0:
            return 0.1
        elif total_findings < 3:
            return 0.4
        elif total_findings < 6:
            return 0.7
        else:
            return 0.9
    
    def _get_all_source_entities(self, *entity_lists) -> List[str]:
        """Get all source entity IDs from multiple lists"""
        all_entities = []
        for entity_list in entity_lists:
            all_entities.extend([e.id for e in entity_list])
        return all_entities
    
    def _extract_ama_references(self, rom_entities: List[MedicalEntity]) -> List[str]:
        """Extract AMA table references from ROM measurements"""
        ama_refs = []
        for entity in rom_entities:
            if 'ama_reference' in entity.metadata:
                ama_refs.append(entity.metadata['ama_reference'])
        return ama_refs
    
    def _assess_exam_quality(self, content: str, rom_entities: List, strength_entities: List) -> Dict[str, Any]:
        """Assess quality of examination content"""
        return {
            'word_count': len(content.split()),
            'has_rom_data': len(rom_entities) > 0,
            'has_strength_data': len(strength_entities) > 0,
            'measurement_count': len(rom_entities) + len(strength_entities),
            'completeness_score': min(1.0, (len(rom_entities) + len(strength_entities)) / 5)
        }
    
    def generate_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                            evidence_retrieval: EvidenceRetrievalResult,
                                            context: Dict[str, Any]) -> MedicalNarrative:
        """Generate examination using only validated fields and evidence snippets"""
        try:
            self.logger.info("Generating evidence-constrained physical examination")
            
            narrative_parts = []
            
            # General appearance from validated fields
            if 'general_appearance' in validated_fields:
                appearance_text = self._generate_validated_appearance_text(validated_fields['general_appearance'])
                narrative_parts.append(appearance_text)
            
            # ROM measurements from validated fields
            if 'rom_measurements' in validated_fields:
                rom_text = self._generate_validated_rom_text(validated_fields['rom_measurements'])
                narrative_parts.append(rom_text)
            
            # Strength testing from validated fields
            if 'strength_tests' in validated_fields:
                strength_text = self._generate_validated_strength_text(validated_fields['strength_tests'])
                narrative_parts.append(strength_text)
            
            # Neurological findings from validated fields
            if 'neurological_findings' in validated_fields:
                neuro_text = self._generate_validated_neurological_text(validated_fields['neurological_findings'])
                narrative_parts.append(neuro_text)
            
            # Enhance with evidence snippets
            evidence_enhanced_parts = self._enhance_examination_with_evidence(
                narrative_parts, evidence_retrieval.evidence_snippets
            )
            
            content = " ".join(evidence_enhanced_parts) if evidence_enhanced_parts else ""
            content = self._remove_placeholder_text(content)
            
            # Generate source citations
            source_citations = self.evidence_rag_service.get_source_citations(
                evidence_retrieval.evidence_snippets, 
                evidence_retrieval.canonical_content
            )
            
            return MedicalNarrative(
                section_name="Physical Examination",
                content=content,
                confidence_score=self._calculate_examination_evidence_confidence(validated_fields, evidence_retrieval),
                source_entities=list(validated_fields.keys()),
                ama_references=[c.ama_reference for c in evidence_retrieval.canonical_content if c.ama_reference],
                legal_citations=[],
                quality_indicators=self._assess_examination_evidence_quality(content, validated_fields),
                evidence_snippets=evidence_retrieval.evidence_snippets,
                validated_fields_used=validated_fields,
                source_citations=source_citations,
                provenance_complete=evidence_retrieval.provenance_complete,
                placeholder_text_removed=True,
                evidence_backing_complete=len(evidence_retrieval.evidence_snippets) > 0
            )
            
        except Exception as e:
            self.logger.error(f"Error generating evidence-constrained examination: {str(e)}")
            return self._generate_evidence_fallback_examination()
    
    def _generate_validated_appearance_text(self, appearance_data: Dict[str, Any]) -> str:
        """Generate appearance text using only validated data"""
        if not appearance_data:
            return "The patient appears comfortable and in no acute distress."
        
        findings = []
        if isinstance(appearance_data, dict):
            for key, value in appearance_data.items():
                if value:
                    findings.append(f"{key}: {value}")
        elif isinstance(appearance_data, list):
            findings = [str(item) for item in appearance_data]
        else:
            findings = [str(appearance_data)]
        
        return f"On examination, the patient {', '.join(findings)}."
    
    def _generate_validated_rom_text(self, rom_data: Dict[str, Any]) -> str:
        """Generate ROM text using only validated measurements"""
        if not rom_data:
            return ""
        
        rom_text = "Range of motion testing reveals: "
        rom_findings = []
        
        for movement, measurement in rom_data.items():
            if isinstance(measurement, dict) and 'degrees' in measurement:
                rom_findings.append(f"{movement} {measurement['degrees']} degrees")
            elif isinstance(measurement, (int, float)):
                rom_findings.append(f"{movement} {measurement} degrees")
            else:
                rom_findings.append(f"{movement} {measurement}")
        
        return rom_text + "; ".join(rom_findings) + "."
    
    def _generate_validated_strength_text(self, strength_data: Dict[str, Any]) -> str:
        """Generate strength text using only validated data"""
        if not strength_data:
            return ""
        
        strength_text = "Manual muscle testing demonstrates: "
        strength_findings = []
        
        for muscle_group, strength in strength_data.items():
            strength_findings.append(f"{muscle_group} {strength}")
        
        return strength_text + "; ".join(strength_findings) + "."
    
    def _generate_validated_neurological_text(self, neuro_data: Dict[str, Any]) -> str:
        """Generate neurological text using only validated data"""
        if not neuro_data:
            return ""
        
        neuro_text = "Neurological examination shows: "
        neuro_findings = []
        
        for test, result in neuro_data.items():
            neuro_findings.append(f"{test} {result}")
        
        return neuro_text + "; ".join(neuro_findings) + "."
    
    def _enhance_examination_with_evidence(self, narrative_parts: List[str], 
                                         evidence_snippets: List[EvidenceSnippet]) -> List[str]:
        """Enhance examination narrative with evidence snippets"""
        enhanced_parts = narrative_parts.copy()
        
        # Add relevant AMA methodology context
        for snippet in evidence_snippets[:2]:  # Limit to top 2 most relevant
            if snippet.ama_reference and 'measurement' in snippet.content.lower():
                enhanced_parts.append(f"Measurements performed according to {snippet.ama_reference} methodology.")
        
        return enhanced_parts
    
    def _remove_placeholder_text(self, content: str) -> str:
        """Remove any placeholder text from examination content"""
        placeholders = [
            '[PLACEHOLDER]', '[TBD]', '[TO BE DETERMINED]', '[NEEDS REVIEW]',
            'PLACEHOLDER', 'TBD', 'TO BE DETERMINED', 'NEEDS REVIEW'
        ]
        
        cleaned_content = content
        for placeholder in placeholders:
            cleaned_content = cleaned_content.replace(placeholder, '')
        
        sentences = [s.strip() for s in cleaned_content.split('.') if s.strip()]
        return '. '.join(sentences) + '.' if sentences else ""
    
    def _calculate_examination_evidence_confidence(self, validated_fields: Dict[str, Any], 
                                                 evidence_retrieval: EvidenceRetrievalResult) -> float:
        """Calculate confidence based on validated examination fields and evidence"""
        field_confidence = min(1.0, len(validated_fields) / 4.0)  # Target 4 key examination areas
        evidence_confidence = evidence_retrieval.confidence_score
        
        # Weight ROM and strength data higher
        measurement_bonus = 0.0
        if 'rom_measurements' in validated_fields:
            measurement_bonus += 0.1
        if 'strength_tests' in validated_fields:
            measurement_bonus += 0.1
        
        base_confidence = (field_confidence * 0.6) + (evidence_confidence * 0.4)
        return min(1.0, base_confidence + measurement_bonus)
    
    def _assess_examination_evidence_quality(self, content: str, validated_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of evidence-based examination content"""
        return {
            'word_count': len(content.split()),
            'validated_fields_count': len(validated_fields),
            'has_rom_data': 'rom_measurements' in validated_fields,
            'has_strength_data': 'strength_tests' in validated_fields,
            'has_neurological_data': 'neurological_findings' in validated_fields,
            'has_appearance_data': 'general_appearance' in validated_fields,
            'evidence_based': True,
            'measurement_count': len(validated_fields.get('rom_measurements', {})) + len(validated_fields.get('strength_tests', {})),
            'placeholder_free': '[' not in content and 'PLACEHOLDER' not in content.upper()
        }
    
    def _generate_evidence_fallback_examination(self) -> MedicalNarrative:
        """Generate evidence-based fallback examination"""
        return MedicalNarrative(
            section_name="Physical Examination",
            content="Physical examination requires validated measurement data and examination findings. Additional field extraction and validation needed.",
            confidence_score=0.1,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'evidence_fallback': True},
            evidence_snippets=[],
            validated_fields_used={},
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_fallback_examination(self) -> MedicalNarrative:
        """Generate fallback examination when extraction fails"""
        return MedicalNarrative(
            section_name="Physical Examination",
            content="Physical examination was performed. Detailed findings require additional documentation review and measurement data.",
            confidence_score=0.2,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'fallback': True}
        )


class DiagnosticStudiesGenerator(IContentGenerator):
    """Generates evidence-constrained diagnostic studies content"""
    
    def __init__(self, evidence_rag_service: EvidenceRAGService, logger: logging.Logger):
        self.evidence_rag_service = evidence_rag_service
        self.logger = logger
    
    def generate_content(self, knowledge_graph: KnowledgeGraph, context: Dict[str, Any]) -> MedicalNarrative:
        """Generate diagnostic studies narrative"""
        try:
            # Extract diagnostic study entities
            imaging_studies = self._extract_imaging_studies(knowledge_graph)
            lab_results = self._extract_lab_results(knowledge_graph)
            other_studies = self._extract_other_studies(knowledge_graph)
            
            # Build diagnostic narrative
            narrative_parts = []
            
            if imaging_studies:
                narrative_parts.append(self._generate_imaging_text(imaging_studies))
            
            if lab_results:
                narrative_parts.append(self._generate_lab_text(lab_results))
            
            if other_studies:
                narrative_parts.append(self._generate_other_studies_text(other_studies))
            
            content = " ".join(narrative_parts) if narrative_parts else "No diagnostic studies were available for review."
            
            return MedicalNarrative(
                section_name="Diagnostic Studies",
                content=content,
                confidence_score=self._calculate_diagnostic_confidence(imaging_studies, lab_results, other_studies),
                source_entities=[e.id for e in imaging_studies + lab_results + other_studies],
                ama_references=[],
                legal_citations=[],
                quality_indicators=self._assess_diagnostic_quality(content, imaging_studies, lab_results)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating diagnostic studies: {str(e)}")
            return self._generate_fallback_diagnostic()
    
    def _extract_imaging_studies(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract imaging study entities"""
        imaging_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.IMAGING_STUDY:
                imaging_entities.append(entity)
        return imaging_entities
    
    def _extract_lab_results(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract laboratory result entities"""
        lab_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.LAB_RESULT:
                lab_entities.append(entity)
        return lab_entities
    
    def _extract_other_studies(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract other diagnostic study entities"""
        other_entities = []
        for entity in kg.entities.values():
            # For now, we'll look for any entities that might be diagnostic studies
            # This can be expanded with more specific entity types as needed
            if 'study' in entity.content.lower() or 'test' in entity.content.lower():
                other_entities.append(entity)
        return other_entities
    
    def _generate_imaging_text(self, imaging_entities: List[MedicalEntity]) -> str:
        """Generate imaging studies text with medical interpretation"""
        if not imaging_entities:
            return ""
        
        imaging_text = "Imaging studies include: "
        study_descriptions = []
        
        for entity in imaging_entities:
            study_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
            findings = entity.content
            date_text = ""
            
            if 'date' in entity.metadata:
                date_text = f" dated {entity.metadata['date'].strftime('%m/%d/%Y')}"
            
            study_descriptions.append(f"{study_type}{date_text} showing {findings}")
        
        return imaging_text + "; ".join(study_descriptions) + "."
    
    def _generate_lab_text(self, lab_entities: List[MedicalEntity]) -> str:
        """Generate laboratory results text"""
        if not lab_entities:
            return ""
        
        lab_text = "Laboratory studies reveal: "
        lab_findings = [entity.content for entity in lab_entities]
        
        return lab_text + "; ".join(lab_findings) + "."
    
    def _generate_other_studies_text(self, other_entities: List[MedicalEntity]) -> str:
        """Generate other diagnostic studies text"""
        if not other_entities:
            return ""
        
        other_text = "Additional studies include: "
        other_findings = []
        
        for entity in other_entities:
            study_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
            findings = entity.content
            other_findings.append(f"{study_type} demonstrating {findings}")
        
        return other_text + "; ".join(other_findings) + "."
    
    def _calculate_diagnostic_confidence(self, imaging: List, lab: List, other: List) -> float:
        """Calculate confidence based on diagnostic study availability"""
        total_studies = len(imaging) + len(lab) + len(other)
        
        if total_studies == 0:
            return 0.3  # Still valid if no studies available
        elif total_studies < 2:
            return 0.6
        elif total_studies < 4:
            return 0.8
        else:
            return 0.95
    
    def _assess_diagnostic_quality(self, content: str, imaging: List, lab: List) -> Dict[str, Any]:
        """Assess quality of diagnostic studies content"""
        return {
            'word_count': len(content.split()),
            'has_imaging': len(imaging) > 0,
            'has_lab_results': len(lab) > 0,
            'study_count': len(imaging) + len(lab),
            'interpretation_present': 'showing' in content or 'demonstrating' in content
        }
    
    def generate_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                            evidence_retrieval: EvidenceRetrievalResult,
                                            context: Dict[str, Any]) -> MedicalNarrative:
        """Generate diagnostic studies using only validated fields and evidence"""
        try:
            self.logger.info("Generating evidence-constrained diagnostic studies")
            
            narrative_parts = []
            
            # Imaging studies from validated fields
            if 'imaging_studies' in validated_fields:
                imaging_text = self._generate_validated_imaging_text(validated_fields['imaging_studies'])
                narrative_parts.append(imaging_text)
            
            # Laboratory results from validated fields
            if 'lab_results' in validated_fields:
                lab_text = self._generate_validated_lab_text(validated_fields['lab_results'])
                narrative_parts.append(lab_text)
            
            # Other diagnostic studies from validated fields
            if 'other_studies' in validated_fields:
                other_text = self._generate_validated_other_studies_text(validated_fields['other_studies'])
                narrative_parts.append(other_text)
            
            content = " ".join(narrative_parts) if narrative_parts else "No validated diagnostic studies were available for review."
            content = self._remove_placeholder_text(content)
            
            # Generate source citations
            source_citations = self.evidence_rag_service.get_source_citations(
                evidence_retrieval.evidence_snippets, 
                evidence_retrieval.canonical_content
            )
            
            return MedicalNarrative(
                section_name="Diagnostic Studies",
                content=content,
                confidence_score=self._calculate_diagnostic_evidence_confidence(validated_fields, evidence_retrieval),
                source_entities=list(validated_fields.keys()),
                ama_references=[c.ama_reference for c in evidence_retrieval.canonical_content if c.ama_reference],
                legal_citations=[],
                quality_indicators=self._assess_diagnostic_evidence_quality(content, validated_fields),
                evidence_snippets=evidence_retrieval.evidence_snippets,
                validated_fields_used=validated_fields,
                source_citations=source_citations,
                provenance_complete=evidence_retrieval.provenance_complete,
                placeholder_text_removed=True,
                evidence_backing_complete=len(evidence_retrieval.evidence_snippets) > 0
            )
            
        except Exception as e:
            self.logger.error(f"Error generating evidence-constrained diagnostic studies: {str(e)}")
            return self._generate_evidence_fallback_diagnostic()
    
    def _generate_validated_imaging_text(self, imaging_data: Dict[str, Any]) -> str:
        """Generate imaging text using only validated data"""
        if not imaging_data:
            return ""
        
        imaging_text = "Imaging studies include: "
        study_descriptions = []
        
        for study_type, findings in imaging_data.items():
            if isinstance(findings, dict):
                date_text = f" dated {findings.get('date', '')}" if findings.get('date') else ""
                finding_text = findings.get('findings', findings.get('result', ''))
                study_descriptions.append(f"{study_type}{date_text} showing {finding_text}")
            else:
                study_descriptions.append(f"{study_type} showing {findings}")
        
        return imaging_text + "; ".join(study_descriptions) + "."
    
    def _generate_validated_lab_text(self, lab_data: Dict[str, Any]) -> str:
        """Generate laboratory text using only validated data"""
        if not lab_data:
            return ""
        
        lab_text = "Laboratory studies reveal: "
        lab_findings = []
        
        for test, result in lab_data.items():
            if isinstance(result, dict):
                value = result.get('value', result.get('result', ''))
                lab_findings.append(f"{test} {value}")
            else:
                lab_findings.append(f"{test} {result}")
        
        return lab_text + "; ".join(lab_findings) + "."
    
    def _generate_validated_other_studies_text(self, other_data: Dict[str, Any]) -> str:
        """Generate other studies text using only validated data"""
        if not other_data:
            return ""
        
        other_text = "Additional studies include: "
        other_findings = []
        
        for study_type, findings in other_data.items():
            other_findings.append(f"{study_type} demonstrating {findings}")
        
        return other_text + "; ".join(other_findings) + "."
    
    def _remove_placeholder_text(self, content: str) -> str:
        """Remove any placeholder text from diagnostic content"""
        placeholders = [
            '[PLACEHOLDER]', '[TBD]', '[TO BE DETERMINED]', '[NEEDS REVIEW]',
            'PLACEHOLDER', 'TBD', 'TO BE DETERMINED', 'NEEDS REVIEW'
        ]
        
        cleaned_content = content
        for placeholder in placeholders:
            cleaned_content = cleaned_content.replace(placeholder, '')
        
        sentences = [s.strip() for s in cleaned_content.split('.') if s.strip()]
        return '. '.join(sentences) + '.' if sentences else ""
    
    def _calculate_diagnostic_evidence_confidence(self, validated_fields: Dict[str, Any], 
                                                evidence_retrieval: EvidenceRetrievalResult) -> float:
        """Calculate confidence based on validated diagnostic fields and evidence"""
        field_confidence = min(1.0, len(validated_fields) / 3.0)  # Target 3 types of studies
        evidence_confidence = evidence_retrieval.confidence_score
        
        # Higher confidence if multiple study types present
        study_types = len([k for k in validated_fields.keys() if k in ['imaging_studies', 'lab_results', 'other_studies']])
        type_bonus = min(0.2, study_types * 0.1)
        
        base_confidence = (field_confidence * 0.7) + (evidence_confidence * 0.3)
        return min(1.0, base_confidence + type_bonus)
    
    def _assess_diagnostic_evidence_quality(self, content: str, validated_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of evidence-based diagnostic content"""
        return {
            'word_count': len(content.split()),
            'validated_fields_count': len(validated_fields),
            'has_imaging': 'imaging_studies' in validated_fields,
            'has_lab_results': 'lab_results' in validated_fields,
            'has_other_studies': 'other_studies' in validated_fields,
            'study_count': sum(len(v) if isinstance(v, dict) else 1 for v in validated_fields.values()),
            'evidence_based': True,
            'interpretation_present': 'showing' in content or 'demonstrating' in content,
            'placeholder_free': '[' not in content and 'PLACEHOLDER' not in content.upper()
        }
    
    def _generate_evidence_fallback_diagnostic(self) -> MedicalNarrative:
        """Generate evidence-based fallback diagnostic content"""
        return MedicalNarrative(
            section_name="Diagnostic Studies",
            content="Diagnostic studies require validated imaging and laboratory data. Additional field extraction and validation needed.",
            confidence_score=0.1,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'evidence_fallback': True},
            evidence_snippets=[],
            validated_fields_used={},
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_fallback_diagnostic(self) -> MedicalNarrative:
        """Generate fallback diagnostic studies content"""
        return MedicalNarrative(
            section_name="Diagnostic Studies",
            content="Diagnostic studies require review of available imaging and laboratory reports.",
            confidence_score=0.2,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'fallback': True}
        )


class CausationAnalysisGenerator(IContentGenerator):
    """Generates evidence-constrained causation analysis with medical reasoning"""
    
    def __init__(self, evidence_rag_service: EvidenceRAGService, logger: logging.Logger):
        self.evidence_rag_service = evidence_rag_service
        self.logger = logger
    
    def generate_content(self, knowledge_graph: KnowledgeGraph, context: Dict[str, Any]) -> MedicalNarrative:
        """Generate causation analysis narrative"""
        try:
            # Extract causation-related entities
            industrial_factors = self._extract_industrial_factors(knowledge_graph)
            preexisting_conditions = self._extract_preexisting_conditions(knowledge_graph)
            current_diagnoses = self._extract_current_diagnoses(knowledge_graph)
            
            # Generate causation reasoning
            causation_analysis = self._generate_causation_reasoning(
                industrial_factors, preexisting_conditions, current_diagnoses
            )
            
            # Build medical probability statement
            probability_statement = self._generate_probability_statement(causation_analysis)
            
            content = f"{causation_analysis} {probability_statement}"
            
            return MedicalNarrative(
                section_name="Causation Analysis",
                content=content,
                confidence_score=self._calculate_causation_confidence(industrial_factors, preexisting_conditions),
                source_entities=[e.id for e in industrial_factors + preexisting_conditions + current_diagnoses],
                ama_references=[],
                legal_citations=self._get_legal_citations(),
                quality_indicators=self._assess_causation_quality(content, causation_analysis)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating causation analysis: {str(e)}")
            return self._generate_fallback_causation()
    
    def _extract_industrial_factors(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract work-related injury factors"""
        industrial_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.WORK_INJURY:
                industrial_entities.append(entity)
        return industrial_entities
    
    def _extract_preexisting_conditions(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract pre-existing medical conditions"""
        preexisting_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.PREEXISTING_CONDITION:
                preexisting_entities.append(entity)
        return preexisting_entities
    
    def _extract_current_diagnoses(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract current medical diagnoses"""
        diagnosis_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.DIAGNOSIS:
                diagnosis_entities.append(entity)
        return diagnosis_entities
    
    def _generate_causation_reasoning(self, industrial: List[MedicalEntity], 
                                    preexisting: List[MedicalEntity], 
                                    diagnoses: List[MedicalEntity]) -> str:
        """Generate medical causation reasoning"""
        reasoning_parts = []
        
        # Industrial causation
        if industrial:
            industrial_desc = ", ".join([e.content for e in industrial[:2]])
            reasoning_parts.append(f"The industrial injury involving {industrial_desc} is causally related to the current condition.")
        
        # Pre-existing condition analysis
        if preexisting:
            preexisting_desc = ", ".join([e.content for e in preexisting[:2]])
            reasoning_parts.append(f"While the patient has a history of {preexisting_desc}, the current symptoms and functional limitations are primarily attributable to the industrial injury.")
        
        # Current diagnosis relationship
        if diagnoses:
            primary_diagnosis = diagnoses[0].content
            reasoning_parts.append(f"The diagnosis of {primary_diagnosis} is consistent with the mechanism of injury and clinical presentation.")
        
        return " ".join(reasoning_parts) if reasoning_parts else "Causation analysis requires additional medical documentation."
    
    def _generate_probability_statement(self, causation_analysis: str) -> str:
        """Generate medical probability statement"""
        if "primarily attributable to the industrial injury" in causation_analysis:
            return "Based on reasonable medical probability, the current condition is industrially related."
        elif "causally related" in causation_analysis:
            return "To a reasonable degree of medical probability, the industrial injury is the substantial contributing cause of the current disability."
        else:
            return "The relationship between the industrial exposure and current condition requires further evaluation."
    
    def _calculate_causation_confidence(self, industrial: List, preexisting: List) -> float:
        """Calculate confidence in causation analysis"""
        if len(industrial) > 0 and len(preexisting) > 0:
            return 0.9  # Complete analysis possible
        elif len(industrial) > 0:
            return 0.7  # Industrial factors present
        elif len(preexisting) > 0:
            return 0.5  # Only pre-existing factors
        else:
            return 0.3  # Limited information
    
    def _get_legal_citations(self) -> List[str]:
        """Get relevant legal citations for causation"""
        return [
            "Labor Code Section 3208.1",
            "Labor Code Section 4663",
            "Labor Code Section 4664"
        ]
    
    def _assess_causation_quality(self, content: str, analysis: str) -> Dict[str, Any]:
        """Assess quality of causation analysis"""
        return {
            'word_count': len(content.split()),
            'has_probability_statement': 'reasonable medical probability' in content.lower(),
            'addresses_preexisting': 'pre-existing' in content.lower() or 'history of' in content.lower(),
            'addresses_industrial': 'industrial' in content.lower() or 'work' in content.lower(),
            'legal_standard_met': 'reasonable medical probability' in content.lower()
        }
    
    def generate_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                            evidence_retrieval: EvidenceRetrievalResult,
                                            context: Dict[str, Any]) -> MedicalNarrative:
        """Generate causation analysis using only validated fields and evidence"""
        try:
            self.logger.info("Generating evidence-constrained causation analysis")
            
            # Generate causation reasoning from validated fields
            causation_analysis = self._generate_validated_causation_reasoning(validated_fields)
            
            # Generate medical probability statement
            probability_statement = self._generate_validated_probability_statement(validated_fields, causation_analysis)
            
            content = f"{causation_analysis} {probability_statement}"
            content = self._remove_placeholder_text(content)
            
            # Generate source citations
            source_citations = self.evidence_rag_service.get_source_citations(
                evidence_retrieval.evidence_snippets, 
                evidence_retrieval.canonical_content
            )
            
            return MedicalNarrative(
                section_name="Causation Analysis",
                content=content,
                confidence_score=self._calculate_causation_evidence_confidence(validated_fields, evidence_retrieval),
                source_entities=list(validated_fields.keys()),
                ama_references=[c.ama_reference for c in evidence_retrieval.canonical_content if c.ama_reference],
                legal_citations=self._get_validated_legal_citations(),
                quality_indicators=self._assess_causation_evidence_quality(content, validated_fields),
                evidence_snippets=evidence_retrieval.evidence_snippets,
                validated_fields_used=validated_fields,
                source_citations=source_citations,
                provenance_complete=evidence_retrieval.provenance_complete,
                placeholder_text_removed=True,
                evidence_backing_complete=len(evidence_retrieval.evidence_snippets) > 0
            )
            
        except Exception as e:
            self.logger.error(f"Error generating evidence-constrained causation analysis: {str(e)}")
            return self._generate_evidence_fallback_causation()
    
    def _generate_validated_causation_reasoning(self, validated_fields: Dict[str, Any]) -> str:
        """Generate causation reasoning using only validated fields"""
        reasoning_parts = []
        
        # Industrial causation from validated fields
        if 'industrial_factors' in validated_fields and validated_fields['industrial_factors']:
            industrial_desc = validated_fields['industrial_factors']
            if isinstance(industrial_desc, list):
                industrial_desc = ", ".join(industrial_desc[:2])
            reasoning_parts.append(f"The industrial injury involving {industrial_desc} is causally related to the current condition.")
        
        # Pre-existing condition analysis from validated fields
        if 'preexisting_conditions' in validated_fields and validated_fields['preexisting_conditions']:
            preexisting_desc = validated_fields['preexisting_conditions']
            if isinstance(preexisting_desc, list):
                preexisting_desc = ", ".join(preexisting_desc[:2])
            reasoning_parts.append(f"While the patient has a history of {preexisting_desc}, the current symptoms and functional limitations are primarily attributable to the industrial injury.")
        
        # Current diagnosis relationship from validated fields
        if 'primary_diagnosis' in validated_fields and validated_fields['primary_diagnosis']:
            primary_diagnosis = validated_fields['primary_diagnosis']
            reasoning_parts.append(f"The diagnosis of {primary_diagnosis} is consistent with the mechanism of injury and clinical presentation.")
        
        return " ".join(reasoning_parts) if reasoning_parts else "Causation analysis based on validated medical documentation."
    
    def _generate_validated_probability_statement(self, validated_fields: Dict[str, Any], causation_analysis: str) -> str:
        """Generate medical probability statement based on validated evidence"""
        # Determine probability level based on strength of validated evidence
        has_industrial = 'industrial_factors' in validated_fields and validated_fields['industrial_factors']
        has_diagnosis = 'primary_diagnosis' in validated_fields and validated_fields['primary_diagnosis']
        has_mechanism = 'injury_mechanism' in validated_fields and validated_fields['injury_mechanism']
        
        evidence_strength = sum([has_industrial, has_diagnosis, has_mechanism])
        
        if evidence_strength >= 3:
            return "Based on reasonable medical probability, the current condition is industrially related."
        elif evidence_strength >= 2:
            return "To a reasonable degree of medical probability, the industrial injury is the substantial contributing cause of the current disability."
        elif evidence_strength >= 1:
            return "The relationship between the industrial exposure and current condition is supported by available medical evidence."
        else:
            return "The relationship between the industrial exposure and current condition requires additional validated evidence for determination."
    
    def _get_validated_legal_citations(self) -> List[str]:
        """Get relevant legal citations for causation analysis"""
        return [
            "Labor Code Section 3208.1",
            "Labor Code Section 4663",
            "Labor Code Section 4664"
        ]
    
    def _remove_placeholder_text(self, content: str) -> str:
        """Remove any placeholder text from causation content"""
        placeholders = [
            '[PLACEHOLDER]', '[TBD]', '[TO BE DETERMINED]', '[NEEDS REVIEW]',
            'PLACEHOLDER', 'TBD', 'TO BE DETERMINED', 'NEEDS REVIEW'
        ]
        
        cleaned_content = content
        for placeholder in placeholders:
            cleaned_content = cleaned_content.replace(placeholder, '')
        
        sentences = [s.strip() for s in cleaned_content.split('.') if s.strip()]
        return '. '.join(sentences) + '.' if sentences else ""
    
    def _calculate_causation_evidence_confidence(self, validated_fields: Dict[str, Any], 
                                               evidence_retrieval: EvidenceRetrievalResult) -> float:
        """Calculate confidence based on validated causation fields and evidence"""
        # Key causation fields
        key_fields = ['industrial_factors', 'preexisting_conditions', 'primary_diagnosis', 'injury_mechanism']
        present_key_fields = sum(1 for field in key_fields if field in validated_fields and validated_fields[field])
        
        field_confidence = min(1.0, present_key_fields / len(key_fields))
        evidence_confidence = evidence_retrieval.confidence_score
        
        # Higher confidence if both industrial and diagnosis present
        if 'industrial_factors' in validated_fields and 'primary_diagnosis' in validated_fields:
            field_confidence += 0.1
        
        return min(1.0, (field_confidence * 0.8) + (evidence_confidence * 0.2))
    
    def _assess_causation_evidence_quality(self, content: str, validated_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of evidence-based causation analysis"""
        return {
            'word_count': len(content.split()),
            'validated_fields_count': len(validated_fields),
            'has_probability_statement': 'reasonable medical probability' in content.lower(),
            'addresses_preexisting': 'preexisting_conditions' in validated_fields,
            'addresses_industrial': 'industrial_factors' in validated_fields,
            'has_diagnosis': 'primary_diagnosis' in validated_fields,
            'has_mechanism': 'injury_mechanism' in validated_fields,
            'evidence_based': True,
            'legal_standard_met': 'reasonable medical probability' in content.lower(),
            'placeholder_free': '[' not in content and 'PLACEHOLDER' not in content.upper()
        }
    
    def _generate_evidence_fallback_causation(self) -> MedicalNarrative:
        """Generate evidence-based fallback causation analysis"""
        return MedicalNarrative(
            section_name="Causation Analysis",
            content="Causation analysis requires validated evidence regarding industrial factors, pre-existing conditions, and current medical status. Additional field extraction and validation needed to establish the relationship between industrial exposure and current condition to a reasonable degree of medical probability.",
            confidence_score=0.1,
            source_entities=[],
            ama_references=[],
            legal_citations=["Labor Code Section 3208.1"],
            quality_indicators={'evidence_fallback': True},
            evidence_snippets=[],
            validated_fields_used={},
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_fallback_causation(self) -> MedicalNarrative:
        """Generate fallback causation analysis"""
        return MedicalNarrative(
            section_name="Causation Analysis",
            content="Causation analysis requires comprehensive review of industrial factors, pre-existing conditions, and current medical status. To a reasonable degree of medical probability, further documentation is needed to establish the relationship between industrial exposure and current condition.",
            confidence_score=0.3,
            source_entities=[],
            ama_references=[],
            legal_citations=["Labor Code Section 3208.1"],
            quality_indicators={'fallback': True}
        )


class FutureMedicalCareGenerator(IContentGenerator):
    """Generates evidence-constrained future medical care recommendations"""
    
    def __init__(self, ama_engine: AMAGuidelinesEngine, evidence_rag_service: EvidenceRAGService, logger: logging.Logger):
        self.ama_engine = ama_engine
        self.evidence_rag_service = evidence_rag_service
        self.logger = logger
    
    def generate_content(self, knowledge_graph: KnowledgeGraph, context: Dict[str, Any]) -> MedicalNarrative:
        """Generate future medical care recommendations"""
        try:
            # Extract relevant entities
            diagnoses = self._extract_diagnoses(knowledge_graph)
            current_treatments = self._extract_current_treatments(knowledge_graph)
            functional_limitations = self._extract_functional_limitations(knowledge_graph)
            
            # Generate recommendations based on diagnosis and prognosis
            recommendations = self._generate_treatment_recommendations(
                diagnoses, current_treatments, functional_limitations
            )
            
            # Add AMA-based recommendations
            ama_recommendations = self._get_ama_based_recommendations(diagnoses)
            
            # Combine recommendations
            all_recommendations = recommendations + ama_recommendations
            content = self._format_recommendations(all_recommendations)
            
            return MedicalNarrative(
                section_name="Future Medical Care",
                content=content,
                confidence_score=self._calculate_fmc_confidence(diagnoses, current_treatments),
                source_entities=[e.id for e in diagnoses + current_treatments + functional_limitations],
                ama_references=self._extract_ama_references_for_fmc(diagnoses),
                legal_citations=[],
                quality_indicators=self._assess_fmc_quality(content, all_recommendations)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating future medical care: {str(e)}")
            return self._generate_fallback_fmc()
    
    def _extract_diagnoses(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract diagnosis entities for FMC planning"""
        diagnosis_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.DIAGNOSIS:
                diagnosis_entities.append(entity)
        return diagnosis_entities
    
    def _extract_current_treatments(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract current treatment entities"""
        treatment_entities = []
        for entity in kg.entities.values():
            if entity.entity_type in [MedicalEntityType.TREATMENT, MedicalEntityType.THERAPY, 
                                    MedicalEntityType.MEDICATION, MedicalEntityType.PROCEDURE]:
                treatment_entities.append(entity)
        return treatment_entities
    
    def _extract_functional_limitations(self, kg: KnowledgeGraph) -> List[MedicalEntity]:
        """Extract functional limitation entities"""
        limitation_entities = []
        for entity in kg.entities.values():
            if entity.entity_type == MedicalEntityType.LIMITATION:
                limitation_entities.append(entity)
        return limitation_entities
    
    def _generate_treatment_recommendations(self, diagnoses: List[MedicalEntity], 
                                         current_treatments: List[MedicalEntity],
                                         limitations: List[MedicalEntity]) -> List[str]:
        """Generate treatment recommendations based on medical entities"""
        recommendations = []
        
        # Conservative care recommendations
        if any('pain' in d.content.lower() for d in diagnoses):
            recommendations.append("Conservative pain management including physical therapy and anti-inflammatory medications")
        
        # Physical therapy recommendations
        if any('mobility' in l.content.lower() or 'range of motion' in l.content.lower() for l in limitations):
            recommendations.append("Physical therapy to improve range of motion and functional capacity")
        
        # Injection therapy
        if any('joint' in d.content.lower() or 'arthritis' in d.content.lower() for d in diagnoses):
            recommendations.append("Consideration of intra-articular injection therapy if conservative measures fail")
        
        # Surgical evaluation
        if any('severe' in l.content.lower() or 'significant' in l.content.lower() for l in limitations):
            recommendations.append("Orthopedic surgical evaluation if conservative treatment is unsuccessful")
        
        return recommendations
    
    def _get_ama_based_recommendations(self, diagnoses: List[MedicalEntity]) -> List[str]:
        """Get AMA Guidelines-based recommendations"""
        ama_recommendations = []
        
        for diagnosis in diagnoses:
            try:
                # Query AMA engine for treatment guidelines
                guidelines = self.ama_engine.get_treatment_guidelines(diagnosis.content)
                if guidelines:
                    ama_recommendations.extend(guidelines.get('recommendations', []))
            except Exception as e:
                self.logger.warning(f"Could not get AMA recommendations for {diagnosis.content}: {str(e)}")
        
        return ama_recommendations[:3]  # Limit to top 3 AMA recommendations
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        """Format recommendations into coherent narrative"""
        if not recommendations:
            return "Future medical care recommendations require additional clinical evaluation."
        
        intro = "Based on the current diagnosis and functional limitations, future medical care should include: "
        
        if len(recommendations) == 1:
            return intro + recommendations[0] + "."
        elif len(recommendations) == 2:
            return intro + recommendations[0] + " and " + recommendations[1] + "."
        else:
            formatted_recs = []
            for i, rec in enumerate(recommendations):
                if i == len(recommendations) - 1:
                    formatted_recs.append(f"and {rec}")
                else:
                    formatted_recs.append(rec)
            
            return intro + "; ".join(formatted_recs[:-1]) + "; " + formatted_recs[-1] + "."
    
    def _calculate_fmc_confidence(self, diagnoses: List, treatments: List) -> float:
        """Calculate confidence in FMC recommendations"""
        if len(diagnoses) > 0 and len(treatments) > 0:
            return 0.85
        elif len(diagnoses) > 0:
            return 0.7
        elif len(treatments) > 0:
            return 0.6
        else:
            return 0.4
    
    def _extract_ama_references_for_fmc(self, diagnoses: List[MedicalEntity]) -> List[str]:
        """Extract AMA references relevant to future medical care"""
        ama_refs = []
        for diagnosis in diagnoses:
            if 'ama_chapter' in diagnosis.metadata:
                ama_refs.append(f"AMA Guides Chapter {diagnosis.metadata['ama_chapter']}")
        return ama_refs
    
    def _assess_fmc_quality(self, content: str, recommendations: List[str]) -> Dict[str, Any]:
        """Assess quality of future medical care content"""
        return {
            'word_count': len(content.split()),
            'recommendation_count': len(recommendations),
            'has_conservative_care': any('conservative' in r.lower() for r in recommendations),
            'has_therapy_recs': any('therapy' in r.lower() for r in recommendations),
            'has_surgical_consideration': any('surgical' in r.lower() for r in recommendations),
            'completeness_score': min(1.0, len(recommendations) / 3)
        }
    
    def generate_evidence_constrained_content(self, validated_fields: Dict[str, Any], 
                                            evidence_retrieval: EvidenceRetrievalResult,
                                            context: Dict[str, Any]) -> MedicalNarrative:
        """Generate future medical care using only validated fields and evidence"""
        try:
            self.logger.info("Generating evidence-constrained future medical care")
            
            # Generate recommendations based on validated fields
            recommendations = self._generate_validated_treatment_recommendations(validated_fields)
            
            # Add AMA-based recommendations from evidence
            ama_recommendations = self._get_evidence_based_ama_recommendations(validated_fields, evidence_retrieval)
            
            # Combine recommendations
            all_recommendations = recommendations + ama_recommendations
            content = self._format_validated_recommendations(all_recommendations)
            content = self._remove_placeholder_text(content)
            
            # Generate source citations
            source_citations = self.evidence_rag_service.get_source_citations(
                evidence_retrieval.evidence_snippets, 
                evidence_retrieval.canonical_content
            )
            
            return MedicalNarrative(
                section_name="Future Medical Care",
                content=content,
                confidence_score=self._calculate_fmc_evidence_confidence(validated_fields, evidence_retrieval),
                source_entities=list(validated_fields.keys()),
                ama_references=[c.ama_reference for c in evidence_retrieval.canonical_content if c.ama_reference],
                legal_citations=[],
                quality_indicators=self._assess_fmc_evidence_quality(content, validated_fields, all_recommendations),
                evidence_snippets=evidence_retrieval.evidence_snippets,
                validated_fields_used=validated_fields,
                source_citations=source_citations,
                provenance_complete=evidence_retrieval.provenance_complete,
                placeholder_text_removed=True,
                evidence_backing_complete=len(evidence_retrieval.evidence_snippets) > 0
            )
            
        except Exception as e:
            self.logger.error(f"Error generating evidence-constrained future medical care: {str(e)}")
            return self._generate_evidence_fallback_fmc()
    
    def _generate_validated_treatment_recommendations(self, validated_fields: Dict[str, Any]) -> List[str]:
        """Generate treatment recommendations based only on validated fields"""
        recommendations = []
        
        # Conservative care based on validated diagnosis
        if 'primary_diagnosis' in validated_fields:
            diagnosis = str(validated_fields['primary_diagnosis']).lower()
            if any(term in diagnosis for term in ['pain', 'strain', 'sprain']):
                recommendations.append("Conservative pain management including physical therapy and anti-inflammatory medications")
        
        # Physical therapy based on validated limitations
        if 'functional_limitations' in validated_fields:
            limitations = validated_fields['functional_limitations']
            if isinstance(limitations, (list, dict)) and limitations:
                recommendations.append("Physical therapy to improve range of motion and functional capacity")
        
        # ROM-based recommendations
        if 'rom_measurements' in validated_fields:
            rom_data = validated_fields['rom_measurements']
            if isinstance(rom_data, dict) and rom_data:
                recommendations.append("Range of motion exercises and therapeutic interventions")
        
        # Injection therapy based on validated joint involvement
        if 'body_part' in validated_fields:
            body_part = str(validated_fields['body_part']).lower()
            if any(term in body_part for term in ['joint', 'knee', 'shoulder', 'hip']):
                recommendations.append("Consideration of intra-articular injection therapy if conservative measures fail")
        
        # Surgical evaluation based on validated severity
        if 'impairment_rating' in validated_fields:
            try:
                rating = float(validated_fields['impairment_rating'])
                if rating >= 15:  # Significant impairment
                    recommendations.append("Orthopedic surgical evaluation if conservative treatment is unsuccessful")
            except (ValueError, TypeError):
                pass
        
        return recommendations
    
    def _get_evidence_based_ama_recommendations(self, validated_fields: Dict[str, Any], 
                                              evidence_retrieval: EvidenceRetrievalResult) -> List[str]:
        """Get AMA recommendations based on evidence snippets"""
        ama_recommendations = []
        
        # Extract recommendations from canonical content
        for content in evidence_retrieval.canonical_content:
            if content.content_type == 'future_medical_care' or 'treatment' in content.title.lower():
                if content.content and len(content.content) > 20:
                    ama_recommendations.append(content.content)
        
        # Extract recommendations from evidence snippets with AMA references
        for snippet in evidence_retrieval.evidence_snippets:
            if snippet.ama_reference and 'treatment' in snippet.content.lower():
                if len(snippet.content) > 20 and len(snippet.content) < 200:
                    ama_recommendations.append(snippet.content)
        
        return ama_recommendations[:2]  # Limit to top 2 AMA recommendations
    
    def _format_validated_recommendations(self, recommendations: List[str]) -> str:
        """Format recommendations into coherent narrative using validated content"""
        if not recommendations:
            return "Future medical care recommendations require validated clinical data and evidence-based treatment guidelines."
        
        intro = "Based on validated clinical findings and evidence-based guidelines, future medical care should include: "
        
        if len(recommendations) == 1:
            return intro + recommendations[0] + "."
        elif len(recommendations) == 2:
            return intro + recommendations[0] + " and " + recommendations[1] + "."
        else:
            formatted_recs = []
            for i, rec in enumerate(recommendations):
                if i == len(recommendations) - 1:
                    formatted_recs.append(f"and {rec}")
                else:
                    formatted_recs.append(rec)
            
            return intro + "; ".join(formatted_recs[:-1]) + "; " + formatted_recs[-1] + "."
    
    def _remove_placeholder_text(self, content: str) -> str:
        """Remove any placeholder text from FMC content"""
        placeholders = [
            '[PLACEHOLDER]', '[TBD]', '[TO BE DETERMINED]', '[NEEDS REVIEW]',
            'PLACEHOLDER', 'TBD', 'TO BE DETERMINED', 'NEEDS REVIEW'
        ]
        
        cleaned_content = content
        for placeholder in placeholders:
            cleaned_content = cleaned_content.replace(placeholder, '')
        
        sentences = [s.strip() for s in cleaned_content.split('.') if s.strip()]
        return '. '.join(sentences) + '.' if sentences else ""
    
    def _calculate_fmc_evidence_confidence(self, validated_fields: Dict[str, Any], 
                                         evidence_retrieval: EvidenceRetrievalResult) -> float:
        """Calculate confidence based on validated FMC fields and evidence"""
        # Key FMC fields
        key_fields = ['primary_diagnosis', 'functional_limitations', 'rom_measurements', 'impairment_rating']
        present_key_fields = sum(1 for field in key_fields if field in validated_fields and validated_fields[field])
        
        field_confidence = min(1.0, present_key_fields / len(key_fields))
        evidence_confidence = evidence_retrieval.confidence_score
        
        # Bonus for AMA evidence
        ama_bonus = 0.1 if any(c.ama_reference for c in evidence_retrieval.canonical_content) else 0.0
        
        return min(1.0, (field_confidence * 0.7) + (evidence_confidence * 0.3) + ama_bonus)
    
    def _assess_fmc_evidence_quality(self, content: str, validated_fields: Dict[str, Any], 
                                   recommendations: List[str]) -> Dict[str, Any]:
        """Assess quality of evidence-based FMC content"""
        return {
            'word_count': len(content.split()),
            'validated_fields_count': len(validated_fields),
            'recommendation_count': len(recommendations),
            'has_conservative_care': any('conservative' in r.lower() for r in recommendations),
            'has_therapy_recs': any('therapy' in r.lower() for r in recommendations),
            'has_surgical_consideration': any('surgical' in r.lower() for r in recommendations),
            'has_diagnosis_basis': 'primary_diagnosis' in validated_fields,
            'has_functional_basis': 'functional_limitations' in validated_fields,
            'evidence_based': True,
            'completeness_score': min(1.0, len(recommendations) / 3),
            'placeholder_free': '[' not in content and 'PLACEHOLDER' not in content.upper()
        }
    
    def _generate_evidence_fallback_fmc(self) -> MedicalNarrative:
        """Generate evidence-based fallback FMC content"""
        return MedicalNarrative(
            section_name="Future Medical Care",
            content="Future medical care recommendations require validated clinical findings, functional limitations, and evidence-based treatment guidelines. Additional field extraction and validation needed.",
            confidence_score=0.1,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'evidence_fallback': True},
            evidence_snippets=[],
            validated_fields_used={},
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_fallback_fmc(self) -> MedicalNarrative:
        """Generate fallback future medical care content"""
        return MedicalNarrative(
            section_name="Future Medical Care",
            content="Future medical care recommendations should be based on comprehensive evaluation of current symptoms, functional limitations, and response to conservative treatment. Standard care may include physical therapy, pain management, and periodic medical monitoring.",
            confidence_score=0.4,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'fallback': True}
        )


class IntelligentContentGenerator:
    """Enhanced evidence-driven content generation engine"""
    
    def __init__(self, ama_engine: AMAGuidelinesEngine, knowledge_graph: KnowledgeGraph, 
                 config: QMEGoldStandardConfig, logger: logging.Logger):
        self.ama_engine = ama_engine
        self.knowledge_graph = knowledge_graph
        self.config = config
        self.logger = logger
        
        # Initialize evidence RAG service
        self.evidence_rag_service = EvidenceRAGService(knowledge_graph, ama_engine)
        
        # Initialize content generators with evidence RAG service
        self.history_generator = HistoryOfPresentIllnessGenerator(self.evidence_rag_service, logger)
        self.exam_generator = PhysicalExaminationGenerator(self.evidence_rag_service, logger)
        self.diagnostic_generator = DiagnosticStudiesGenerator(self.evidence_rag_service, logger)
        self.causation_generator = CausationAnalysisGenerator(self.evidence_rag_service, logger)
        self.fmc_generator = FutureMedicalCareGenerator(ama_engine, self.evidence_rag_service, logger)
        
        # Content generator registry
        self.generators = {
            'history_of_present_illness': self.history_generator,
            'physical_examination': self.exam_generator,
            'diagnostic_studies': self.diagnostic_generator,
            'causation_analysis': self.causation_generator,
            'future_medical_care': self.fmc_generator
        }
    
    def generate_section_content(self, section_name: str, knowledge_graph: KnowledgeGraph, 
                               context: Optional[Dict[str, Any]] = None) -> MedicalNarrative:
        """Generate content for a specific report section"""
        try:
            if context is None:
                context = {}
            
            # Get appropriate generator
            generator_key = section_name.lower().replace(' ', '_')
            generator = self.generators.get(generator_key)
            
            if not generator:
                self.logger.warning(f"No generator found for section: {section_name}")
                return self._generate_generic_section(section_name, knowledge_graph)
            
            # Generate content
            narrative = generator.generate_content(knowledge_graph, context)
            
            # Apply quality enhancements
            enhanced_narrative = self._enhance_narrative_quality(narrative)
            
            self.logger.info(f"Generated content for {section_name} with confidence {enhanced_narrative.confidence_score}")
            
            return enhanced_narrative
            
        except Exception as e:
            self.logger.error(f"Error generating content for {section_name}: {str(e)}")
            return self._generate_error_fallback(section_name)
    
    def generate_evidence_constrained_section_content(self, section_name: str, 
                                                    validation_report: ValidationReport,
                                                    context: Optional[Dict[str, Any]] = None) -> MedicalNarrative:
        """Generate content for a specific section using only validated fields"""
        try:
            if context is None:
                context = {}
            
            self.logger.info(f"Generating evidence-constrained content for {section_name}")
            
            # Get appropriate generator
            generator_key = section_name.lower().replace(' ', '_')
            generator = self.generators.get(generator_key)
            
            if not generator:
                self.logger.warning(f"No generator found for section: {section_name}")
                return self._generate_evidence_generic_section(section_name, validation_report.accepted_fields)
            
            # Retrieve evidence for this section
            evidence_retrieval = self.evidence_rag_service.get_evidence_constrained_content(
                validation_report.accepted_fields, 
                generator_key
            )
            
            # Generate evidence-constrained content
            narrative = generator.generate_evidence_constrained_content(
                validation_report.accepted_fields,
                evidence_retrieval,
                context
            )
            
            # Apply quality enhancements
            enhanced_narrative = self._enhance_evidence_narrative_quality(narrative)
            
            # Validate content completeness
            self._validate_content_completeness(enhanced_narrative)
            
            self.logger.info(f"Generated evidence-constrained content for {section_name} with confidence {enhanced_narrative.confidence_score}")
            
            return enhanced_narrative
            
        except Exception as e:
            self.logger.error(f"Error generating evidence-constrained content for {section_name}: {str(e)}")
            return self._generate_evidence_error_fallback(section_name)
    
    def generate_comprehensive_evidence_report_content(self, validation_report: ValidationReport,
                                                     sections: List[str],
                                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, MedicalNarrative]:
        """Generate content for multiple report sections using only validated evidence"""
        try:
            self.logger.info(f"Generating comprehensive evidence-constrained report for {len(sections)} sections")
            
            report_content = {}
            
            # Check if we can generate report based on validation
            if not validation_report.can_generate_report:
                self.logger.warning("Validation report indicates insufficient evidence for report generation")
                return self._generate_insufficient_evidence_content(sections, validation_report)
            
            for section in sections:
                narrative = self.generate_evidence_constrained_section_content(section, validation_report, context)
                report_content[section] = narrative
            
            # Apply cross-section evidence consistency checks
            self._ensure_evidence_content_consistency(report_content, validation_report)
            
            # Validate no placeholder text remains across all sections
            self._validate_no_placeholder_text(report_content)
            
            # Ensure all statements have evidence backing
            self._validate_evidence_backing_completeness(report_content)
            
            self.logger.info(f"Successfully generated evidence-constrained content for {len(report_content)} sections")
            
            return report_content
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive evidence report content: {str(e)}")
            return {}
    
    def generate_comprehensive_report_content(self, knowledge_graph: KnowledgeGraph, 
                                           sections: List[str],
                                           context: Optional[Dict[str, Any]] = None) -> Dict[str, MedicalNarrative]:
        """Generate content for multiple report sections (legacy method)"""
        try:
            report_content = {}
            
            for section in sections:
                narrative = self.generate_section_content(section, knowledge_graph, context)
                report_content[section] = narrative
            
            # Apply cross-section consistency checks
            self._ensure_content_consistency(report_content)
            
            return report_content
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report content: {str(e)}")
            return {}
    
    def _enhance_narrative_quality(self, narrative: MedicalNarrative) -> MedicalNarrative:
        """Apply quality enhancements to generated narrative"""
        try:
            # Improve medical terminology
            enhanced_content = self._improve_medical_terminology(narrative.content)
            
            # Ensure professional tone
            enhanced_content = self._ensure_professional_tone(enhanced_content)
            
            # Add transitional phrases for better flow
            enhanced_content = self._improve_narrative_flow(enhanced_content)
            
            # Update narrative with enhancements
            narrative.content = enhanced_content
            
            # Recalculate quality indicators
            narrative.quality_indicators.update({
                'enhanced': True,
                'final_word_count': len(enhanced_content.split()),
                'readability_score': self._calculate_readability_score(enhanced_content)
            })
            
            return narrative
            
        except Exception as e:
            self.logger.warning(f"Error enhancing narrative quality: {str(e)}")
            return narrative
    
    def _improve_medical_terminology(self, content: str) -> str:
        """Improve medical terminology and precision"""
        # Basic medical terminology improvements
        improvements = {
            'hurt': 'pain',
            'sore': 'tender',
            'stiff': 'limited range of motion',
            'weak': 'decreased strength',
            'bad': 'significant',
            'good': 'adequate'
        }
        
        improved_content = content
        for informal, formal in improvements.items():
            improved_content = improved_content.replace(informal, formal)
        
        return improved_content
    
    def _ensure_professional_tone(self, content: str) -> str:
        """Ensure professional medical tone"""
        # Remove casual language and ensure formal medical tone
        if content.startswith('The patient says') or content.startswith('Patient says'):
            content = content.replace('says', 'reports')
        
        # Ensure proper medical documentation style
        if not content.endswith('.'):
            content += '.'
        
        return content
    
    def _improve_narrative_flow(self, content: str) -> str:
        """Improve narrative flow with appropriate transitions"""
        sentences = content.split('. ')
        if len(sentences) > 1:
            # Add appropriate medical transitions
            transitions = ['Additionally,', 'Furthermore,', 'Subsequently,', 'Moreover,']
            
            for i in range(1, len(sentences)):
                if not any(sentences[i].startswith(t) for t in transitions):
                    if i == len(sentences) - 1:
                        sentences[i] = 'Currently, ' + sentences[i]
                    elif i == 1:
                        sentences[i] = 'Subsequently, ' + sentences[i]
            
            content = '. '.join(sentences)
        
        return content
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate basic readability score for medical content"""
        words = content.split()
        sentences = len([s for s in content.split('.') if s.strip()])
        
        if sentences == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / sentences
        
        # Target 15-20 words per sentence for medical documentation
        if 15 <= avg_words_per_sentence <= 20:
            return 1.0
        elif 10 <= avg_words_per_sentence <= 25:
            return 0.8
        else:
            return 0.6
    
    def _ensure_content_consistency(self, report_content: Dict[str, MedicalNarrative]) -> None:
        """Ensure consistency across report sections"""
        try:
            # Check for consistent entity references
            all_entities = set()
            for narrative in report_content.values():
                all_entities.update(narrative.source_entities)
            
            # Log consistency metrics
            self.logger.info(f"Report uses {len(all_entities)} unique medical entities across {len(report_content)} sections")
            
            # Check for consistent AMA references
            all_ama_refs = set()
            for narrative in report_content.values():
                all_ama_refs.update(narrative.ama_references)
            
            if all_ama_refs:
                self.logger.info(f"Report includes {len(all_ama_refs)} AMA guideline references")
            
        except Exception as e:
            self.logger.warning(f"Error checking content consistency: {str(e)}")
    
    def _generate_generic_section(self, section_name: str, knowledge_graph: KnowledgeGraph) -> MedicalNarrative:
        """Generate generic content for unknown sections"""
        return MedicalNarrative(
            section_name=section_name,
            content=f"{section_name} requires detailed review and documentation based on available medical records and examination findings.",
            confidence_score=0.3,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'generic': True}
        )
    
    def _enhance_evidence_narrative_quality(self, narrative: MedicalNarrative) -> MedicalNarrative:
        """Apply evidence-specific quality enhancements to generated narrative"""
        try:
            # Improve medical terminology
            enhanced_content = self._improve_medical_terminology(narrative.content)
            
            # Ensure professional tone
            enhanced_content = self._ensure_professional_tone(enhanced_content)
            
            # Add transitional phrases for better flow
            enhanced_content = self._improve_narrative_flow(enhanced_content)
            
            # Ensure evidence citations are properly formatted
            enhanced_content = self._format_evidence_citations(enhanced_content, narrative.source_citations)
            
            # Update narrative with enhancements
            narrative.content = enhanced_content
            
            # Recalculate quality indicators
            narrative.quality_indicators.update({
                'enhanced': True,
                'evidence_enhanced': True,
                'final_word_count': len(enhanced_content.split()),
                'readability_score': self._calculate_readability_score(enhanced_content),
                'citation_count': len(narrative.source_citations)
            })
            
            return narrative
            
        except Exception as e:
            self.logger.warning(f"Error enhancing evidence narrative quality: {str(e)}")
            return narrative
    
    def _format_evidence_citations(self, content: str, citations: List[str]) -> str:
        """Format evidence citations within content"""
        if not citations:
            return content
        
        # Add citation references where appropriate
        # This is a simplified implementation - could be enhanced with more sophisticated citation placement
        if citations and not any(cite in content for cite in citations):
            # Add primary citation at end if not already present
            primary_citation = citations[0]
            if content.endswith('.'):
                content = content[:-1] + f" (Source: {primary_citation})."
            else:
                content += f" (Source: {primary_citation})"
        
        return content
    
    def _validate_content_completeness(self, narrative: MedicalNarrative) -> None:
        """Validate that content is complete and evidence-backed"""
        try:
            # Check for placeholder text
            if not narrative.placeholder_text_removed:
                self.logger.warning(f"Placeholder text may remain in {narrative.section_name}")
            
            # Check for evidence backing
            if not narrative.evidence_backing_complete:
                self.logger.warning(f"Evidence backing incomplete for {narrative.section_name}")
            
            # Check for minimum content length
            if len(narrative.content.split()) < 10:
                self.logger.warning(f"Content may be too brief for {narrative.section_name}")
            
            # Check for source citations
            if not narrative.source_citations:
                self.logger.warning(f"No source citations found for {narrative.section_name}")
            
        except Exception as e:
            self.logger.warning(f"Error validating content completeness: {str(e)}")
    
    def _ensure_evidence_content_consistency(self, report_content: Dict[str, MedicalNarrative], 
                                           validation_report: ValidationReport) -> None:
        """Ensure consistency across evidence-based report sections"""
        try:
            # Check for consistent validated field usage
            all_validated_fields = set()
            for narrative in report_content.values():
                all_validated_fields.update(narrative.validated_fields_used.keys())
            
            # Ensure critical fields are used consistently
            critical_fields = ['patient_name', 'case_number', 'primary_diagnosis', 'body_part']
            for field in critical_fields:
                if field in validation_report.accepted_fields:
                    field_usage_count = sum(1 for narrative in report_content.values() 
                                          if field in narrative.validated_fields_used)
                    if field_usage_count == 0:
                        self.logger.warning(f"Critical validated field '{field}' not used in any section")
            
            # Check for consistent evidence backing
            sections_without_evidence = [name for name, narrative in report_content.items() 
                                       if not narrative.evidence_backing_complete]
            if sections_without_evidence:
                self.logger.warning(f"Sections without complete evidence backing: {sections_without_evidence}")
            
            self.logger.info(f"Evidence consistency check completed for {len(report_content)} sections")
            
        except Exception as e:
            self.logger.warning(f"Error checking evidence content consistency: {str(e)}")
    
    def _validate_no_placeholder_text(self, report_content: Dict[str, MedicalNarrative]) -> None:
        """Validate that no placeholder text remains in any section"""
        try:
            placeholders_found = []
            
            for section_name, narrative in report_content.items():
                if not narrative.placeholder_text_removed:
                    placeholders_found.append(section_name)
                
                # Double-check content for common placeholders
                placeholder_patterns = ['[', 'PLACEHOLDER', 'TBD', 'TO BE DETERMINED', 'NEEDS REVIEW']
                for pattern in placeholder_patterns:
                    if pattern in narrative.content.upper():
                        placeholders_found.append(f"{section_name} ({pattern})")
            
            if placeholders_found:
                self.logger.error(f"Placeholder text found in sections: {placeholders_found}")
            else:
                self.logger.info("No placeholder text found in any section")
                
        except Exception as e:
            self.logger.warning(f"Error validating placeholder text removal: {str(e)}")
    
    def _validate_evidence_backing_completeness(self, report_content: Dict[str, MedicalNarrative]) -> None:
        """Validate that all statements have evidence backing with source references"""
        try:
            incomplete_sections = []
            
            for section_name, narrative in report_content.items():
                if not narrative.evidence_backing_complete:
                    incomplete_sections.append(section_name)
                
                # Check for source citations
                if not narrative.source_citations:
                    incomplete_sections.append(f"{section_name} (no citations)")
            
            if incomplete_sections:
                self.logger.warning(f"Incomplete evidence backing in sections: {incomplete_sections}")
            else:
                self.logger.info("All sections have complete evidence backing")
                
        except Exception as e:
            self.logger.warning(f"Error validating evidence backing completeness: {str(e)}")
    
    def _generate_insufficient_evidence_content(self, sections: List[str], 
                                              validation_report: ValidationReport) -> Dict[str, MedicalNarrative]:
        """Generate content when insufficient evidence is available"""
        content = {}
        
        for section in sections:
            content[section] = MedicalNarrative(
                section_name=section,
                content=f"{section} requires additional validated evidence for generation. "
                       f"Current validation status: {validation_report.validation_status.value}. "
                       f"Evidence completeness: {validation_report.evidence_completeness:.1%}.",
                confidence_score=0.1,
                source_entities=[],
                ama_references=[],
                legal_citations=[],
                quality_indicators={'insufficient_evidence': True},
                evidence_snippets=[],
                validated_fields_used={},
                source_citations=[],
                provenance_complete=False,
                placeholder_text_removed=True,
                evidence_backing_complete=False
            )
        
        return content
    
    def _generate_evidence_generic_section(self, section_name: str, validated_fields: Dict[str, Any]) -> MedicalNarrative:
        """Generate generic evidence-based content for unknown sections"""
        return MedicalNarrative(
            section_name=section_name,
            content=f"{section_name} requires detailed review and documentation based on validated evidence fields. "
                   f"Available validated fields: {', '.join(validated_fields.keys()) if validated_fields else 'none'}.",
            confidence_score=0.2,
            source_entities=list(validated_fields.keys()),
            ama_references=[],
            legal_citations=[],
            quality_indicators={'generic_evidence': True},
            evidence_snippets=[],
            validated_fields_used=validated_fields,
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_evidence_error_fallback(self, section_name: str) -> MedicalNarrative:
        """Generate evidence-based error fallback content"""
        return MedicalNarrative(
            section_name=section_name,
            content=f"{section_name} content generation encountered an error during evidence-constrained processing. "
                   "Manual review and completion required with validated evidence sources.",
            confidence_score=0.05,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'evidence_error': True},
            evidence_snippets=[],
            validated_fields_used={},
            source_citations=[],
            provenance_complete=False,
            placeholder_text_removed=True,
            evidence_backing_complete=False
        )
    
    def _generate_error_fallback(self, section_name: str) -> MedicalNarrative:
        """Generate error fallback content"""
        return MedicalNarrative(
            section_name=section_name,
            content=f"{section_name} content generation encountered an error. Manual review and completion required.",
            confidence_score=0.1,
            source_entities=[],
            ama_references=[],
            legal_citations=[],
            quality_indicators={'error': True}
        )