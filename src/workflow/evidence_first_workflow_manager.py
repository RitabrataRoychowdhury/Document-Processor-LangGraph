"""
Evidence-First QME Workflow Manager

This module implements the two-pipeline workflow integration for the evidence-first QME system.
It orchestrates Pipeline 1 (extraction/validation) and Pipeline 2 (generation/compliance) with
comprehensive workflow state management and audit trail generation.
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import json

from src.workflow.base.workflow_graph import WorkflowGraph, GraphResult, GraphStatus
from src.workflow.base.state_manager import StateManager
from src.workflow.state.workflow_state import WorkflowState, WorkflowStateFactory
from src.utils.logging_config import get_logger

# Conditional imports for services that may have external dependencies
try:
    from src.core.extraction.structured_extractor import StructuredExtractor, ExtractionContext
    STRUCTURED_EXTRACTOR_AVAILABLE = True
except ImportError:
    STRUCTURED_EXTRACTOR_AVAILABLE = False
    StructuredExtractor = None
    ExtractionContext = None

try:
    from src.core.validation.qme_field_validator import EvidenceFirstValidator, ValidationReport, ConfidenceThresholds
    FIELD_VALIDATOR_AVAILABLE = True
except ImportError:
    FIELD_VALIDATOR_AVAILABLE = False
    EvidenceFirstValidator = None
    ValidationReport = None
    ConfidenceThresholds = None

try:
    from src.core.calculation.impairment_calculator import ImpairmentCalculator, ProgrammaticCalculationResult
    IMPAIRMENT_CALCULATOR_AVAILABLE = True
except ImportError:
    IMPAIRMENT_CALCULATOR_AVAILABLE = False
    ImpairmentCalculator = None
    ProgrammaticCalculationResult = None

try:
    from src.core.generation.intelligent_content_generator import IntelligentContentGenerator
    CONTENT_GENERATOR_AVAILABLE = True
except ImportError:
    CONTENT_GENERATOR_AVAILABLE = False
    IntelligentContentGenerator = None

try:
    from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
    TEMPLATE_ASSEMBLER_AVAILABLE = True
except ImportError:
    TEMPLATE_ASSEMBLER_AVAILABLE = False
    ProfessionalTemplateAssembler = None

try:
    from src.core.validation.qme_rules_engine import QMERulesEngine
    RULES_ENGINE_AVAILABLE = True
except ImportError:
    RULES_ENGINE_AVAILABLE = False
    QMERulesEngine = None

try:
    from src.infrastructure.knowledge.knowledge_base_initializer import KnowledgeBaseInitializer
    KNOWLEDGE_INITIALIZER_AVAILABLE = True
except ImportError:
    KNOWLEDGE_INITIALIZER_AVAILABLE = False
    KnowledgeBaseInitializer = None

try:
    from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
    KG_REPOSITORY_AVAILABLE = True
except ImportError:
    KG_REPOSITORY_AVAILABLE = False
    KnowledgeGraphRepository = None

try:
    from src.storage.document_storage import DocumentStorage
    DOCUMENT_STORAGE_AVAILABLE = True
except ImportError:
    DOCUMENT_STORAGE_AVAILABLE = False
    DocumentStorage = None

logger = get_logger(__name__)


class PipelineStatus(Enum):
    """Status of individual pipeline execution."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowPhase(Enum):
    """Phases of the evidence-first workflow."""
    INITIALIZATION = "initialization"
    PIPELINE_1_EXTRACTION = "pipeline_1_extraction"
    PIPELINE_1_VALIDATION = "pipeline_1_validation"
    PIPELINE_2_CALCULATION = "pipeline_2_calculation"
    PIPELINE_2_GENERATION = "pipeline_2_generation"
    PIPELINE_2_COMPLIANCE = "pipeline_2_compliance"
    FINALIZATION = "finalization"


@dataclass
class PipelineResult:
    """Result of a single pipeline execution."""
    pipeline_name: str
    status: PipelineStatus
    execution_time: float
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    audit_entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowProgress:
    """Progress tracking for the evidence-first workflow."""
    current_phase: WorkflowPhase
    phase_progress: float  # 0.0 to 1.0
    overall_progress: float  # 0.0 to 1.0
    pipeline_1_status: PipelineStatus
    pipeline_2_status: PipelineStatus
    evidence_completeness: float
    validation_results: Optional[ValidationReport] = None
    calculation_results: Optional[ProgrammaticCalculationResult] = None
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class EvidenceFirstWorkflowResult:
    """Complete result of evidence-first workflow execution."""
    workflow_id: str
    success: bool
    message: str
    final_state: Dict[str, Any] = field(default_factory=dict)
    pipeline_results: Dict[str, PipelineResult] = field(default_factory=dict)
    progress: Optional[WorkflowProgress] = None
    validation_report: Optional[ValidationReport] = None
    calculation_result: Optional[ProgrammaticCalculationResult] = None
    generated_content: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EvidenceFirstWorkflowManager:
    """
    Evidence-First QME Workflow Manager orchestrating two-pipeline architecture.
    
    Implements:
    - Pipeline 1: document processing → structured extraction → confidence scoring → 
                  evidence validation → knowledge graph population
    - Pipeline 2: validated evidence → programmatic calculations → evidence-driven 
                  content generation → compliance validation
    - Workflow state management with progress tracking
    - Comprehensive audit trail generation
    """
    
    def __init__(self,
                 storage: Optional[Any] = None,
                 kg_repository: Optional[Any] = None,
                 confidence_thresholds: Optional[Any] = None):
        """Initialize the evidence-first workflow manager."""
        # Check dependencies
        missing_deps = []
        if not DOCUMENT_STORAGE_AVAILABLE:
            missing_deps.append("DocumentStorage")
        if not KG_REPOSITORY_AVAILABLE:
            missing_deps.append("KnowledgeGraphRepository")
        if not STRUCTURED_EXTRACTOR_AVAILABLE:
            missing_deps.append("StructuredExtractor")
        if not FIELD_VALIDATOR_AVAILABLE:
            missing_deps.append("EvidenceFirstValidator")
        
        if missing_deps:
            logger.warning(f"Some dependencies not available: {missing_deps}")
        
        # Core dependencies
        if DOCUMENT_STORAGE_AVAILABLE:
            self.storage = storage or DocumentStorage()
        else:
            self.storage = None
        
        if KG_REPOSITORY_AVAILABLE and kg_repository is None:
            try:
                from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
                self.kg_repository = SQLiteKnowledgeGraphRepository()
            except ImportError:
                self.kg_repository = None
        else:
            self.kg_repository = kg_repository
        
        # Initialize services with conditional availability
        self.structured_extractor = StructuredExtractor() if STRUCTURED_EXTRACTOR_AVAILABLE else None
        self.evidence_validator = EvidenceFirstValidator(confidence_thresholds) if FIELD_VALIDATOR_AVAILABLE else None
        self.impairment_calculator = ImpairmentCalculator() if IMPAIRMENT_CALCULATOR_AVAILABLE else None
        
        # Initialize content generator with required dependencies
        if CONTENT_GENERATOR_AVAILABLE:
            try:
                from src.infrastructure.knowledge.ama_guidelines_engine import AMAGuidelinesEngine
                from src.config.qme_gold_standard_config import QMEGoldStandardConfig
                from src.models.knowledge_graph import KnowledgeGraph
                ama_engine = AMAGuidelinesEngine()
                config = QMEGoldStandardConfig()
                knowledge_graph = KnowledgeGraph()
                self.content_generator = IntelligentContentGenerator(ama_engine, knowledge_graph, config, logger)
            except ImportError as e:
                logger.warning(f"Could not initialize IntelligentContentGenerator: {e}")
                self.content_generator = None
        else:
            self.content_generator = None
        
        self.template_assembler = ProfessionalTemplateAssembler() if TEMPLATE_ASSEMBLER_AVAILABLE else None
        self.rules_engine = QMERulesEngine() if RULES_ENGINE_AVAILABLE else None
        
        # Initialize knowledge base initializer with required dependencies
        if KNOWLEDGE_INITIALIZER_AVAILABLE:
            try:
                from src.config.app_config import AppConfig
                from src.core.extraction.ingestion_pipeline import IngestionPipeline
                from src.factories.processor_factory import ProcessorFactory
                from src.strategies.embedding_strategy import LocalEmbeddingStrategy
                from src.infrastructure.knowledge.knowledge_graph_vector_service import KnowledgeGraphVectorService
                
                config = AppConfig()
                processor_factory = ProcessorFactory()
                embedding_strategy = LocalEmbeddingStrategy()
                kg_service = KnowledgeGraphVectorService(self.kg_repository, embedding_strategy)
                ingestion_pipeline = IngestionPipeline(processor_factory, embedding_strategy, kg_service)
                self.knowledge_initializer = KnowledgeBaseInitializer(config, ingestion_pipeline)
            except (ImportError, Exception) as e:
                logger.warning(f"Could not initialize KnowledgeBaseInitializer: {e}")
                self.knowledge_initializer = None
        else:
            self.knowledge_initializer = None
        
        # Workflow management
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # Configuration
        if FIELD_VALIDATOR_AVAILABLE and ConfidenceThresholds:
            self.confidence_thresholds = confidence_thresholds or ConfidenceThresholds()
        else:
            self.confidence_thresholds = confidence_thresholds
        
        logger.info("Initialized Evidence-First QME Workflow Manager")
    
    def check_service_availability(self) -> Dict[str, bool]:
        """Check availability of all required services."""
        return {
            'structured_extractor': STRUCTURED_EXTRACTOR_AVAILABLE and self.structured_extractor is not None,
            'evidence_validator': FIELD_VALIDATOR_AVAILABLE and self.evidence_validator is not None,
            'impairment_calculator': IMPAIRMENT_CALCULATOR_AVAILABLE and self.impairment_calculator is not None,
            'content_generator': CONTENT_GENERATOR_AVAILABLE and self.content_generator is not None,
            'template_assembler': TEMPLATE_ASSEMBLER_AVAILABLE and self.template_assembler is not None,
            'rules_engine': RULES_ENGINE_AVAILABLE and self.rules_engine is not None,
            'knowledge_initializer': KNOWLEDGE_INITIALIZER_AVAILABLE and self.knowledge_initializer is not None,
            'storage': DOCUMENT_STORAGE_AVAILABLE and self.storage is not None,
            'kg_repository': KG_REPOSITORY_AVAILABLE and self.kg_repository is not None
        }
    
    def execute_evidence_first_workflow(self,
                                      document_path: str,
                                      document_id: str = None,
                                      workflow_config: Dict[str, Any] = None) -> str:
        """
        Execute complete evidence-first workflow with two-pipeline architecture.
        
        Args:
            document_path: Path to the document to process
            document_id: Optional document identifier
            workflow_config: Optional workflow configuration
            
        Returns:
            Workflow execution ID for tracking
        """
        workflow_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        
        logger.info(f"Starting evidence-first workflow {workflow_id} for document {document_path}")
        
        # Check service availability
        service_availability = self.check_service_availability()
        missing_services = [service for service, available in service_availability.items() if not available]
        
        if missing_services:
            error_msg = f"Cannot execute workflow: missing required services: {missing_services}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            # Initialize workflow state
            initial_state = {
                'workflow_id': workflow_id,
                'correlation_id': correlation_id,
                'document_path': document_path,
                'document_id': document_id or str(uuid.uuid4()),
                'workflow_type': 'evidence_first_qme',
                'config': workflow_config or {},
                'created_at': datetime.now().isoformat(),
                'status': 'initialized'
            }
            
            # Create progress tracker
            progress = WorkflowProgress(
                current_phase=WorkflowPhase.INITIALIZATION,
                phase_progress=0.0,
                overall_progress=0.0,
                pipeline_1_status=PipelineStatus.NOT_STARTED,
                pipeline_2_status=PipelineStatus.NOT_STARTED,
                evidence_completeness=0.0
            )
            
            # Register workflow
            self.active_workflows[workflow_id] = {
                'workflow_id': workflow_id,
                'state': initial_state,
                'progress': progress,
                'created_at': datetime.now(),
                'thread': None
            }
            
            # Execute workflow asynchronously
            workflow_thread = threading.Thread(
                target=self._execute_workflow_async,
                args=(workflow_id, initial_state),
                daemon=True
            )
            workflow_thread.start()
            
            self.active_workflows[workflow_id]['thread'] = workflow_thread
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start evidence-first workflow: {e}")
            raise
    
    def _execute_workflow_async(self, workflow_id: str, initial_state: Dict[str, Any]) -> None:
        """Execute the complete evidence-first workflow asynchronously."""
        start_time = time.time()
        
        try:
            workflow_info = self.active_workflows[workflow_id]
            progress = workflow_info['progress']
            
            # Initialize audit trail
            audit_trail = []
            pipeline_results = {}
            
            # Phase 1: Initialization
            logger.info(f"Phase 1: Initialization - Workflow {workflow_id}")
            progress.current_phase = WorkflowPhase.INITIALIZATION
            progress.phase_progress = 0.5
            progress.overall_progress = 0.05
            
            # Ensure knowledge graph is initialized
            init_result = self._ensure_knowledge_graph_initialized(workflow_id, audit_trail)
            if not init_result:
                raise Exception("Knowledge graph initialization failed")
            
            progress.phase_progress = 1.0
            progress.overall_progress = 0.1
            
            # PIPELINE 1: STRUCTURED EXTRACTION & VALIDATION
            logger.info(f"Starting Pipeline 1: Extraction & Validation - Workflow {workflow_id}")
            progress.pipeline_1_status = PipelineStatus.RUNNING
            
            # Phase 2: Document Processing & Structured Extraction
            progress.current_phase = WorkflowPhase.PIPELINE_1_EXTRACTION
            progress.phase_progress = 0.0
            progress.overall_progress = 0.15
            
            extraction_result = self._execute_pipeline_1_extraction(
                initial_state, audit_trail
            )
            pipeline_results['pipeline_1_extraction'] = extraction_result
            
            if extraction_result.status != PipelineStatus.COMPLETED:
                raise Exception(f"Pipeline 1 extraction failed: {extraction_result.errors}")
            
            progress.phase_progress = 1.0
            progress.overall_progress = 0.3
            
            # Phase 3: Evidence Validation
            progress.current_phase = WorkflowPhase.PIPELINE_1_VALIDATION
            progress.phase_progress = 0.0
            progress.overall_progress = 0.35
            
            validation_result = self._execute_pipeline_1_validation(
                extraction_result.data, audit_trail
            )
            pipeline_results['pipeline_1_validation'] = validation_result
            
            if validation_result.status != PipelineStatus.COMPLETED:
                raise Exception(f"Pipeline 1 validation failed: {validation_result.errors}")
            
            # Update progress with validation results
            validation_report = validation_result.data.get('validation_report')
            if validation_report:
                progress.validation_results = validation_report
                progress.evidence_completeness = validation_report.evidence_completeness
            
            progress.phase_progress = 1.0
            progress.overall_progress = 0.5
            progress.pipeline_1_status = PipelineStatus.COMPLETED
            
            # Check if we can proceed to Pipeline 2
            if not validation_report or not validation_report.can_generate_report:
                logger.warning(f"Insufficient evidence for Pipeline 2 - Workflow {workflow_id}")
                # Still complete the workflow but mark Pipeline 2 as skipped
                progress.pipeline_2_status = PipelineStatus.SKIPPED
                progress.overall_progress = 1.0
                
                result = self._create_workflow_result(
                    workflow_id, True, "Pipeline 1 completed, Pipeline 2 skipped due to insufficient evidence",
                    pipeline_results, progress, audit_trail, time.time() - start_time
                )
                self._complete_workflow(workflow_id, result)
                return
            
            # PIPELINE 2: EVIDENCE-DRIVEN GENERATION & COMPLIANCE
            logger.info(f"Starting Pipeline 2: Generation & Compliance - Workflow {workflow_id}")
            progress.pipeline_2_status = PipelineStatus.RUNNING
            
            # Phase 4: Programmatic Calculations
            progress.current_phase = WorkflowPhase.PIPELINE_2_CALCULATION
            progress.phase_progress = 0.0
            progress.overall_progress = 0.55
            
            calculation_result = self._execute_pipeline_2_calculation(
                validation_result.data, audit_trail
            )
            pipeline_results['pipeline_2_calculation'] = calculation_result
            
            if calculation_result.status == PipelineStatus.FAILED:
                logger.warning(f"Pipeline 2 calculation failed, continuing - Workflow {workflow_id}")
            
            progress.phase_progress = 1.0
            progress.overall_progress = 0.7
            
            # Phase 5: Evidence-Driven Content Generation
            progress.current_phase = WorkflowPhase.PIPELINE_2_GENERATION
            progress.phase_progress = 0.0
            progress.overall_progress = 0.75
            
            generation_result = self._execute_pipeline_2_generation(
                validation_result.data, calculation_result.data, audit_trail
            )
            pipeline_results['pipeline_2_generation'] = generation_result
            
            if generation_result.status != PipelineStatus.COMPLETED:
                raise Exception(f"Pipeline 2 generation failed: {generation_result.errors}")
            
            progress.phase_progress = 1.0
            progress.overall_progress = 0.85
            
            # Phase 6: Compliance Validation
            progress.current_phase = WorkflowPhase.PIPELINE_2_COMPLIANCE
            progress.phase_progress = 0.0
            progress.overall_progress = 0.9
            
            compliance_result = self._execute_pipeline_2_compliance(
                generation_result.data, audit_trail
            )
            pipeline_results['pipeline_2_compliance'] = compliance_result
            
            if compliance_result.status != PipelineStatus.COMPLETED:
                logger.warning(f"Pipeline 2 compliance validation failed - Workflow {workflow_id}")
            
            progress.phase_progress = 1.0
            progress.overall_progress = 0.95
            progress.pipeline_2_status = PipelineStatus.COMPLETED
            
            # Phase 7: Finalization
            progress.current_phase = WorkflowPhase.FINALIZATION
            progress.phase_progress = 0.5
            progress.overall_progress = 0.98
            
            # Create final workflow result
            result = self._create_workflow_result(
                workflow_id, True, "Evidence-first workflow completed successfully",
                pipeline_results, progress, audit_trail, time.time() - start_time
            )
            
            progress.phase_progress = 1.0
            progress.overall_progress = 1.0
            
            # Complete workflow
            self._complete_workflow(workflow_id, result)
            
            logger.info(f"Evidence-first workflow {workflow_id} completed successfully in {result.execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in evidence-first workflow {workflow_id}: {e}")
            
            # Create failure result
            result = self._create_workflow_result(
                workflow_id, False, f"Workflow failed: {str(e)}",
                pipeline_results, progress, audit_trail, time.time() - start_time
            )
            
            self._complete_workflow(workflow_id, result)
    
    def _ensure_knowledge_graph_initialized(self, workflow_id: str, 
                                          audit_trail: List[Dict[str, Any]]) -> bool:
        """Ensure knowledge graph is properly initialized."""
        try:
            logger.info(f"Checking knowledge graph initialization - Workflow {workflow_id}")
            
            # Check if knowledge graph has sufficient data
            node_count = self.kg_repository.get_entity_count()
            relationship_count = self.kg_repository.get_relationship_count()
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'knowledge_graph_check',
                'workflow_id': workflow_id,
                'details': {
                    'node_count': node_count,
                    'relationship_count': relationship_count,
                    'required_nodes': 1000,
                    'required_relationships': 500
                }
            }
            
            if node_count >= 1000 and relationship_count >= 500:
                audit_entry['status'] = 'sufficient'
                audit_trail.append(audit_entry)
                return True
            
            # Initialize knowledge graph
            logger.info(f"Initializing knowledge graph - Workflow {workflow_id}")
            audit_entry['status'] = 'initializing'
            audit_trail.append(audit_entry)
            
            init_result = self.knowledge_initializer.initialize_complete_knowledge_base()
            
            if init_result.get('success', False):
                audit_trail.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'knowledge_graph_initialized',
                    'workflow_id': workflow_id,
                    'details': init_result
                })
                return True
            else:
                logger.error(f"Knowledge graph initialization failed - Workflow {workflow_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring knowledge graph initialization: {e}")
            audit_trail.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'knowledge_graph_error',
                'workflow_id': workflow_id,
                'error': str(e)
            })
            return False
    
    def _execute_pipeline_1_extraction(self, initial_state: Dict[str, Any],
                                     audit_trail: List[Dict[str, Any]]) -> PipelineResult:
        """Execute Pipeline 1: Structured Extraction with confidence scoring."""
        pipeline_start = time.time()
        workflow_id = initial_state['workflow_id']
        document_path = initial_state['document_path']
        
        try:
            logger.info(f"Executing Pipeline 1 extraction - Workflow {workflow_id}")
            
            # Read document content
            with open(document_path, 'r', encoding='utf-8', errors='ignore') as f:
                document_text = f.read()
            
            # Create extraction context
            context = ExtractionContext(
                document_id=initial_state['document_id'],
                document_text=document_text,
                source_file=document_path,
                processing_timestamp=datetime.now().isoformat()
            )
            
            # Perform structured extraction with confidence scoring
            extraction_result = self.structured_extractor.extract_with_confidence(context)
            
            # Log extraction results
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'structured_extraction',
                'workflow_id': workflow_id,
                'details': {
                    'fields_extracted': len(extraction_result.field_data.field_extractions),
                    'overall_confidence': extraction_result.overall_confidence,
                    'evidence_completeness': extraction_result.evidence_completeness,
                    'extraction_errors': len(extraction_result.extraction_errors)
                }
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_1_extraction",
                status=PipelineStatus.COMPLETED,
                execution_time=time.time() - pipeline_start,
                data={
                    'extraction_result': extraction_result,
                    'context': context
                },
                audit_entries=[audit_entry]
            )
            
        except Exception as e:
            logger.error(f"Pipeline 1 extraction failed - Workflow {workflow_id}: {e}")
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'structured_extraction_error',
                'workflow_id': workflow_id,
                'error': str(e)
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_1_extraction",
                status=PipelineStatus.FAILED,
                execution_time=time.time() - pipeline_start,
                errors=[str(e)],
                audit_entries=[audit_entry]
            )
    
    def _execute_pipeline_1_validation(self, extraction_data: Dict[str, Any],
                                     audit_trail: List[Dict[str, Any]]) -> PipelineResult:
        """Execute Pipeline 1: Evidence validation with confidence thresholds."""
        pipeline_start = time.time()
        
        try:
            extraction_result = extraction_data['extraction_result']
            context = extraction_data['context']
            
            logger.info(f"Executing Pipeline 1 validation - Document {context.document_id}")
            
            # Perform evidence-first validation
            validation_report = self.evidence_validator.validate_evidence_first(
                extraction_result, context.document_id
            )
            
            # Populate knowledge graph with validated fields only
            kg_population_result = self._populate_knowledge_graph_with_validated_fields(
                validation_report, context, audit_trail
            )
            
            # Log validation results
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'evidence_validation',
                'workflow_id': context.document_id,
                'details': {
                    'accepted_fields': len(validation_report.accepted_fields),
                    'flagged_fields': len(validation_report.flagged_fields),
                    'missing_fields': len(validation_report.missing_fields),
                    'overall_confidence': validation_report.overall_confidence,
                    'evidence_completeness': validation_report.evidence_completeness,
                    'can_generate_report': validation_report.can_generate_report,
                    'kg_population_success': kg_population_result
                }
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_1_validation",
                status=PipelineStatus.COMPLETED,
                execution_time=time.time() - pipeline_start,
                data={
                    'validation_report': validation_report,
                    'kg_population_result': kg_population_result
                },
                audit_entries=[audit_entry]
            )
            
        except Exception as e:
            logger.error(f"Pipeline 1 validation failed: {e}")
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'evidence_validation_error',
                'error': str(e)
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_1_validation",
                status=PipelineStatus.FAILED,
                execution_time=time.time() - pipeline_start,
                errors=[str(e)],
                audit_entries=[audit_entry]
            )
    
    def _populate_knowledge_graph_with_validated_fields(self, 
                                                       validation_report: ValidationReport,
                                                       context: ExtractionContext,
                                                       audit_trail: List[Dict[str, Any]]) -> bool:
        """Populate knowledge graph with only validated fields."""
        try:
            logger.info(f"Populating knowledge graph with validated fields - Document {context.document_id}")
            
            # Only use accepted fields (confidence >= 0.8) for knowledge graph population
            validated_entities = []
            
            for field_name, field_value in validation_report.accepted_fields.items():
                # Create knowledge graph entity from validated field
                entity_data = {
                    'id': f"{context.document_id}_{field_name}",
                    'type': self._map_field_to_entity_type(field_name),
                    'content': str(field_value),
                    'source_document': context.document_id,
                    'confidence': validation_report.overall_confidence,
                    'validation_status': 'accepted'
                }
                validated_entities.append(entity_data)
            
            # Store entities in knowledge graph
            for entity_data in validated_entities:
                self.kg_repository.create_entity(
                    entity_data['id'],
                    entity_data['type'],
                    entity_data['content'],
                    entity_data
                )
            
            audit_trail.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'knowledge_graph_population',
                'document_id': context.document_id,
                'details': {
                    'entities_created': len(validated_entities),
                    'validation_threshold': 'accepted_only'
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error populating knowledge graph: {e}")
            audit_trail.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'knowledge_graph_population_error',
                'document_id': context.document_id,
                'error': str(e)
            })
            return False
    
    def _map_field_to_entity_type(self, field_name: str) -> str:
        """Map field name to knowledge graph entity type."""
        field_mapping = {
            'name': 'PATIENT',
            'case_number': 'CASE',
            'claim_number': 'CLAIM',
            'injury_date': 'INJURY_DATE',
            'age': 'PATIENT_AGE',
            'gender': 'PATIENT_GENDER',
            'body_parts': 'BODY_PART',
            'occupation': 'OCCUPATION',
            'employer': 'EMPLOYER',
            'rom_measurements': 'ROM_MEASUREMENT',
            'ama_table_references': 'AMA_REFERENCE'
        }
        return field_mapping.get(field_name, 'UNKNOWN')
    
    def _execute_pipeline_2_calculation(self, validation_data: Dict[str, Any],
                                       audit_trail: List[Dict[str, Any]]) -> PipelineResult:
        """Execute Pipeline 2: Programmatic impairment calculations."""
        pipeline_start = time.time()
        
        try:
            validation_report = validation_data['validation_report']
            
            logger.info("Executing Pipeline 2 programmatic calculations")
            
            # Extract ROM measurements from accepted fields
            rom_data = validation_report.accepted_fields.get('rom_measurements', {})
            
            if not rom_data:
                logger.info("No ROM measurements available for calculation")
                return PipelineResult(
                    pipeline_name="pipeline_2_calculation",
                    status=PipelineStatus.SKIPPED,
                    execution_time=time.time() - pipeline_start,
                    warnings=["No ROM measurements available for programmatic calculation"]
                )
            
            # Convert ROM data to measurement objects
            rom_measurements = self._convert_rom_data_to_measurements(rom_data)
            
            # Perform programmatic calculation
            calculation_result = self.impairment_calculator.calculate_rom_impairment(
                rom_measurements, "spine"  # Default to spine, could be determined from body_parts
            )
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'programmatic_calculation',
                'details': {
                    'calculation_method': calculation_result.calculation_method,
                    'impairment_percentage': calculation_result.impairment_percentage,
                    'ama_tables_used': len(calculation_result.ama_table_references),
                    'calculation_steps': len(calculation_result.calculation_steps),
                    'validation_passed': all(calculation_result.validation_status.values())
                }
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_2_calculation",
                status=PipelineStatus.COMPLETED,
                execution_time=time.time() - pipeline_start,
                data={
                    'calculation_result': calculation_result
                },
                audit_entries=[audit_entry]
            )
            
        except Exception as e:
            logger.error(f"Pipeline 2 calculation failed: {e}")
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'programmatic_calculation_error',
                'error': str(e)
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_2_calculation",
                status=PipelineStatus.FAILED,
                execution_time=time.time() - pipeline_start,
                errors=[str(e)],
                audit_entries=[audit_entry]
            )
    
    def _convert_rom_data_to_measurements(self, rom_data: Dict[str, Any]) -> List:
        """Convert ROM data dictionary to measurement objects."""
        from src.core.calculation.impairment_calculator import ROMMeasurement
        
        measurements = []
        
        for joint, measurement_list in rom_data.items():
            if isinstance(measurement_list, list):
                for i, measurement_value in enumerate(measurement_list):
                    measurements.append(ROMMeasurement(
                        joint=joint,
                        motion_type="flexion",  # Default, could be parsed from joint name
                        measured_degrees=float(measurement_value),
                        measurement_date=datetime.now(),
                        examiner="QME System",
                        notes=f"Extracted measurement {i+1} for {joint}"
                    ))
        
        return measurements
    
    def _execute_pipeline_2_generation(self, validation_data: Dict[str, Any],
                                     calculation_data: Dict[str, Any],
                                     audit_trail: List[Dict[str, Any]]) -> PipelineResult:
        """Execute Pipeline 2: Evidence-driven content generation."""
        pipeline_start = time.time()
        
        try:
            validation_report = validation_data['validation_report']
            calculation_result = calculation_data.get('calculation_result')
            
            logger.info("Executing Pipeline 2 evidence-driven content generation")
            
            # Generate content using only accepted evidence fields
            content_context = {
                'accepted_fields': validation_report.accepted_fields,
                'evidence_completeness': validation_report.evidence_completeness,
                'calculation_result': calculation_result
            }
            
            # Generate QME report sections
            generated_content = self.content_generator.generate_qme_sections(
                self.kg_repository, content_context
            )
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'evidence_driven_generation',
                'details': {
                    'sections_generated': len(generated_content),
                    'evidence_fields_used': len(validation_report.accepted_fields),
                    'calculation_included': calculation_result is not None
                }
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_2_generation",
                status=PipelineStatus.COMPLETED,
                execution_time=time.time() - pipeline_start,
                data={
                    'generated_content': generated_content
                },
                audit_entries=[audit_entry]
            )
            
        except Exception as e:
            logger.error(f"Pipeline 2 generation failed: {e}")
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'evidence_driven_generation_error',
                'error': str(e)
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_2_generation",
                status=PipelineStatus.FAILED,
                execution_time=time.time() - pipeline_start,
                errors=[str(e)],
                audit_entries=[audit_entry]
            )
    
    def _execute_pipeline_2_compliance(self, generation_data: Dict[str, Any],
                                     audit_trail: List[Dict[str, Any]]) -> PipelineResult:
        """Execute Pipeline 2: Legal compliance validation."""
        pipeline_start = time.time()
        
        try:
            generated_content = generation_data['generated_content']
            
            logger.info("Executing Pipeline 2 compliance validation")
            
            # Validate legal compliance using rules engine
            compliance_result = self.rules_engine.validate_qme_compliance(generated_content)
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'compliance_validation',
                'details': {
                    'compliance_checks': len(compliance_result.get('checks', [])),
                    'passed_checks': len([c for c in compliance_result.get('checks', []) if c.get('passed', False)]),
                    'overall_compliance': compliance_result.get('overall_compliance', False)
                }
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_2_compliance",
                status=PipelineStatus.COMPLETED,
                execution_time=time.time() - pipeline_start,
                data={
                    'compliance_result': compliance_result
                },
                audit_entries=[audit_entry]
            )
            
        except Exception as e:
            logger.error(f"Pipeline 2 compliance validation failed: {e}")
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'compliance_validation_error',
                'error': str(e)
            }
            audit_trail.append(audit_entry)
            
            return PipelineResult(
                pipeline_name="pipeline_2_compliance",
                status=PipelineStatus.FAILED,
                execution_time=time.time() - pipeline_start,
                errors=[str(e)],
                audit_entries=[audit_entry]
            )
    
    def _create_workflow_result(self, workflow_id: str, success: bool, message: str,
                              pipeline_results: Dict[str, PipelineResult],
                              progress: WorkflowProgress,
                              audit_trail: List[Dict[str, Any]],
                              execution_time: float) -> EvidenceFirstWorkflowResult:
        """Create comprehensive workflow result."""
        # Extract key results
        validation_report = None
        calculation_result = None
        generated_content = {}
        compliance_status = {}
        
        if 'pipeline_1_validation' in pipeline_results:
            validation_report = pipeline_results['pipeline_1_validation'].data.get('validation_report')
        
        if 'pipeline_2_calculation' in pipeline_results:
            calculation_result = pipeline_results['pipeline_2_calculation'].data.get('calculation_result')
        
        if 'pipeline_2_generation' in pipeline_results:
            generated_content = pipeline_results['pipeline_2_generation'].data.get('generated_content', {})
        
        if 'pipeline_2_compliance' in pipeline_results:
            compliance_result = pipeline_results['pipeline_2_compliance'].data.get('compliance_result', {})
            compliance_status = compliance_result.get('checks', {})
        
        return EvidenceFirstWorkflowResult(
            workflow_id=workflow_id,
            success=success,
            message=message,
            pipeline_results=pipeline_results,
            progress=progress,
            validation_report=validation_report,
            calculation_result=calculation_result,
            generated_content=generated_content,
            compliance_status=compliance_status,
            audit_trail=audit_trail,
            execution_time=execution_time
        )
    
    def _complete_workflow(self, workflow_id: str, result: EvidenceFirstWorkflowResult) -> None:
        """Complete workflow and move to history."""
        if workflow_id in self.active_workflows:
            workflow_info = self.active_workflows.pop(workflow_id)
            
            # Create history entry
            history_entry = {
                'workflow_id': workflow_id,
                'success': result.success,
                'message': result.message,
                'created_at': workflow_info['created_at'],
                'completed_at': datetime.now(),
                'execution_time': result.execution_time,
                'pipeline_1_status': result.progress.pipeline_1_status.value if result.progress else 'unknown',
                'pipeline_2_status': result.progress.pipeline_2_status.value if result.progress else 'unknown',
                'evidence_completeness': result.progress.evidence_completeness if result.progress else 0.0
            }
            
            self.workflow_history.append(history_entry)
            
            # Limit history size
            if len(self.workflow_history) > 1000:
                self.workflow_history = self.workflow_history[-1000:]
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        if workflow_id in self.active_workflows:
            workflow_info = self.active_workflows[workflow_id]
            progress = workflow_info['progress']
            
            return {
                'workflow_id': workflow_id,
                'status': 'running',
                'current_phase': progress.current_phase.value,
                'overall_progress': progress.overall_progress,
                'pipeline_1_status': progress.pipeline_1_status.value,
                'pipeline_2_status': progress.pipeline_2_status.value,
                'evidence_completeness': progress.evidence_completeness,
                'created_at': workflow_info['created_at'].isoformat(),
                'last_updated': progress.last_updated.isoformat()
            }
        
        # Check history
        for entry in reversed(self.workflow_history):
            if entry['workflow_id'] == workflow_id:
                return {
                    'workflow_id': workflow_id,
                    'status': 'completed' if entry['success'] else 'failed',
                    'message': entry['message'],
                    'created_at': entry['created_at'].isoformat(),
                    'completed_at': entry['completed_at'].isoformat(),
                    'execution_time': entry['execution_time'],
                    'pipeline_1_status': entry['pipeline_1_status'],
                    'pipeline_2_status': entry['pipeline_2_status'],
                    'evidence_completeness': entry['evidence_completeness']
                }
        
        return None
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get list of active workflows."""
        active_workflows = []
        
        for workflow_id, workflow_info in self.active_workflows.items():
            progress = workflow_info['progress']
            
            active_workflows.append({
                'workflow_id': workflow_id,
                'current_phase': progress.current_phase.value,
                'overall_progress': progress.overall_progress,
                'pipeline_1_status': progress.pipeline_1_status.value,
                'pipeline_2_status': progress.pipeline_2_status.value,
                'evidence_completeness': progress.evidence_completeness,
                'created_at': workflow_info['created_at'].isoformat(),
                'last_updated': progress.last_updated.isoformat()
            })
        
        return active_workflows
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow."""
        if workflow_id not in self.active_workflows:
            return False
        
        try:
            workflow_info = self.active_workflows[workflow_id]
            
            # Note: In a production system, you would need proper thread cancellation
            # For now, we'll just mark it as cancelled in history
            
            history_entry = {
                'workflow_id': workflow_id,
                'success': False,
                'message': 'Workflow cancelled by user',
                'created_at': workflow_info['created_at'],
                'completed_at': datetime.now(),
                'execution_time': (datetime.now() - workflow_info['created_at']).total_seconds(),
                'pipeline_1_status': 'cancelled',
                'pipeline_2_status': 'cancelled',
                'evidence_completeness': 0.0
            }
            
            self.workflow_history.append(history_entry)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Cancelled workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling workflow {workflow_id}: {e}")
            return False
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics."""
        total_workflows = len(self.workflow_history) + len(self.active_workflows)
        completed_workflows = len([w for w in self.workflow_history if w['success']])
        failed_workflows = len([w for w in self.workflow_history if not w['success']])
        
        # Calculate average execution time
        execution_times = [w['execution_time'] for w in self.workflow_history if 'execution_time' in w]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        # Calculate evidence completeness statistics
        evidence_scores = [w['evidence_completeness'] for w in self.workflow_history if 'evidence_completeness' in w]
        avg_evidence_completeness = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0
        
        return {
            'total_workflows': total_workflows,
            'active_workflows': len(self.active_workflows),
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'success_rate': (completed_workflows / len(self.workflow_history)) * 100 if self.workflow_history else 0.0,
            'average_execution_time': avg_execution_time,
            'average_evidence_completeness': avg_evidence_completeness,
            'pipeline_1_success_rate': len([w for w in self.workflow_history if w.get('pipeline_1_status') == 'completed']) / len(self.workflow_history) * 100 if self.workflow_history else 0.0,
            'pipeline_2_success_rate': len([w for w in self.workflow_history if w.get('pipeline_2_status') == 'completed']) / len(self.workflow_history) * 100 if self.workflow_history else 0.0
        }
    
    def shutdown(self) -> None:
        """Shutdown the workflow manager."""
        logger.info("Shutting down Evidence-First QME Workflow Manager")
        
        # Cancel all active workflows
        active_workflow_ids = list(self.active_workflows.keys())
        for workflow_id in active_workflow_ids:
            self.cancel_workflow(workflow_id)
        
        logger.info("Evidence-First QME Workflow Manager shutdown complete")


# Convenience functions

def create_evidence_first_workflow_manager() -> EvidenceFirstWorkflowManager:
    """Create an evidence-first workflow manager with default configuration."""
    return EvidenceFirstWorkflowManager()


def create_evidence_first_workflow_manager_with_config(
    confidence_thresholds: Any = None,
    storage: Any = None,
    kg_repository: Any = None
) -> EvidenceFirstWorkflowManager:
    """Create an evidence-first workflow manager with custom configuration."""
    return EvidenceFirstWorkflowManager(
        storage=storage,
        kg_repository=kg_repository,
        confidence_thresholds=confidence_thresholds
    )