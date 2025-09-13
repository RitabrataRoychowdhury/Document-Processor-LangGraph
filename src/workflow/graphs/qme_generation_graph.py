"""QME template generation workflow graph implementation."""

from typing import Dict, Any, List, Optional

from src.workflow.base.workflow_graph import WorkflowGraph
from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.workflow.nodes.extraction_node import ExtractionNode
from src.workflow.nodes.ner_node import NERNode
from src.workflow.nodes.template_generation_node import TemplateGenerationNode
from src.factories.processor_factory import ProcessorFactory
from src.services.qme_template_generator import QMETemplateGenerator
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class QMEGenerationGraph(WorkflowGraph):
    """Workflow graph for QME template generation.
    
    Implements the complete QME template generation workflow:
    1. Text extraction from patient document
    2. Named entity recognition for medical information
    3. Template generation with knowledge graph lookup
    
    Follows Single Responsibility Principle - focused on template generation.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 output_directory: str = "output/templates",
                 graph_id: str = None, 
                 correlation_id: str = None):
        super().__init__(graph_id, correlation_id)
        
        # Initialize dependencies
        self.processor_factory = processor_factory or ProcessorFactory()
        self.template_generator = template_generator or QMETemplateGenerator()
        if kg_repository is None:
            from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            self.kg_repository = SQLiteKnowledgeGraphRepository()
        else:
            self.kg_repository = kg_repository
        
        self.output_directory = output_directory
    
    def build_graph(self) -> None:
        """Build the QME template generation workflow graph."""
        logger.info(f"Building QME generation graph {self.graph_id}")
        
        # Create nodes for template generation workflow
        extraction_node = ExtractionNode(
            processor_factory=self.processor_factory,
            node_id="patient_extraction",
            correlation_id=self.correlation_id
        )
        
        ner_node = NERNode(
            node_id="medical_ner",
            correlation_id=self.correlation_id
        )
        
        template_node = TemplateGenerationNode(
            template_generator=self.template_generator,
            kg_repository=self.kg_repository,
            output_directory=self.output_directory,
            node_id="template_generation",
            correlation_id=self.correlation_id
        )
        
        # Add nodes to graph
        self.add_node(extraction_node)
        self.add_node(ner_node)
        self.add_node(template_node)
        
        # Define workflow edges
        self.add_edge("patient_extraction", "medical_ner")
        self.add_edge("medical_ner", "template_generation")
        
        # Set entry and exit points
        self.set_entry_point("patient_extraction")
        self.set_exit_point("template_generation")
        
        logger.info(f"QME generation graph built with {len(self.nodes)} nodes")
    
    def validate_graph(self) -> bool:
        """Validate the QME generation graph structure."""
        # Check that all required nodes exist
        required_nodes = ["patient_extraction", "medical_ner", "template_generation"]
        for node_id in required_nodes:
            if node_id not in self.nodes:
                logger.error(f"Required node '{node_id}' not found in QME generation graph")
                return False
        
        # Check that graph has no cycles
        if self.has_cycles():
            logger.error("QME generation graph contains cycles")
            return False
        
        # Check that entry and exit points are set
        if not self.entry_points:
            logger.error("No entry points defined in QME generation graph")
            return False
        
        if not self.exit_points:
            logger.error("No exit points defined in QME generation graph")
            return False
        
        # Validate node dependencies
        extraction_node = self.nodes["patient_extraction"]
        ner_node = self.nodes["medical_ner"]
        template_node = self.nodes["template_generation"]
        
        # Check that NER node can receive extraction output
        extraction_outputs = set(extraction_node.get_output_keys())
        ner_inputs = set(ner_node.get_required_inputs())
        if not ner_inputs.issubset(extraction_outputs):
            missing_inputs = ner_inputs - extraction_outputs
            logger.error(f"Medical NER node missing required inputs from extraction: {missing_inputs}")
            return False
        
        # Check that template node can receive combined outputs
        ner_outputs = set(ner_node.get_output_keys())
        template_inputs = set(template_node.get_required_inputs())
        combined_outputs = extraction_outputs.union(ner_outputs)
        if not template_inputs.issubset(combined_outputs):
            missing_inputs = template_inputs - combined_outputs
            logger.error(f"Template generation node missing required inputs: {missing_inputs}")
            return False
        
        logger.info("QME generation graph validation successful")
        return True
    
    def get_generation_summary(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the QME template generation results."""
        return {
            'patient_document_id': final_state.get('patient_document_id') or final_state.get('document_id'),
            'patient_file_path': final_state.get('patient_file_path') or final_state.get('file_path'),
            'template_type': final_state.get('template_type', 'qme_report'),
            'template_generated': final_state.get('template_generated', False),
            'output_file_path': final_state.get('output_file_path'),
            'patient_info_extracted': bool(final_state.get('patient_info')),
            'diagnoses_found': len(final_state.get('diagnoses_identified', [])),
            'impairment_ratings_found': len(final_state.get('impairment_ratings_found', [])),
            'missing_information_count': len(final_state.get('missing_information', [])),
            'generation_statistics': final_state.get('generation_statistics', {})
        }


class EnhancedQMEGenerationGraph(QMEGenerationGraph):
    """Enhanced QME generation graph with knowledge graph integration.
    
    Extends QMEGenerationGraph with additional knowledge graph lookup
    and validation steps for better template quality.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 output_directory: str = "output/templates",
                 enable_kg_validation: bool = True,
                 enable_template_validation: bool = True,
                 graph_id: str = None, 
                 correlation_id: str = None):
        super().__init__(processor_factory, template_generator, kg_repository, 
                        output_directory, graph_id, correlation_id)
        
        self.enable_kg_validation = enable_kg_validation
        self.enable_template_validation = enable_template_validation
    
    def build_graph(self) -> None:
        """Build enhanced QME generation graph with validation steps."""
        logger.info(f"Building enhanced QME generation graph {self.graph_id}")
        
        # Build base graph first
        super().build_graph()
        
        # Add validation nodes if enabled
        if self.enable_kg_validation:
            kg_validation_node = KnowledgeGraphValidationNode(
                kg_repository=self.kg_repository,
                node_id="kg_validation",
                correlation_id=self.correlation_id
            )
            self.add_node(kg_validation_node)
            
            # Insert validation between NER and template generation
            self.edges["medical_ner"] = ["kg_validation"]  # Replace direct edge
            self.add_edge("kg_validation", "template_generation")
        
        if self.enable_template_validation:
            template_validation_node = TemplateValidationNode(
                node_id="template_validation",
                correlation_id=self.correlation_id
            )
            self.add_node(template_validation_node)
            
            # Add validation after template generation
            self.edges["template_generation"] = ["template_validation"]
            self.exit_points = {"template_validation"}
        
        logger.info(f"Enhanced QME generation graph built with {len(self.nodes)} nodes")
    
    def validate_graph(self) -> bool:
        """Validate the enhanced QME generation graph."""
        # First run base validation
        if not super().validate_graph():
            return False
        
        # Additional validation for enhanced features
        if self.enable_kg_validation and "kg_validation" not in self.nodes:
            logger.error("KG validation enabled but node not found")
            return False
        
        if self.enable_template_validation and "template_validation" not in self.nodes:
            logger.error("Template validation enabled but node not found")
            return False
        
        logger.info("Enhanced QME generation graph validation successful")
        return True


class BatchQMEGenerationGraph(WorkflowGraph):
    """Batch QME generation graph for processing multiple patient documents.
    
    Processes multiple patient documents in batch to generate QME templates
    efficiently with shared knowledge graph lookups.
    """
    
    def __init__(self, 
                 processor_factory: ProcessorFactory = None,
                 template_generator: QMETemplateGenerator = None,
                 kg_repository: KnowledgeGraphRepository = None,
                 output_directory: str = "output/templates",
                 batch_size: int = 5,
                 graph_id: str = None, 
                 correlation_id: str = None):
        super().__init__(graph_id, correlation_id)
        
        self.processor_factory = processor_factory or ProcessorFactory()
        self.template_generator = template_generator or QMETemplateGenerator()
        if kg_repository is None:
            from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
            self.kg_repository = SQLiteKnowledgeGraphRepository()
        else:
            self.kg_repository = kg_repository
        
        self.output_directory = output_directory
        self.batch_size = batch_size
    
    def build_graph(self) -> None:
        """Build batch QME generation graph."""
        logger.info(f"Building batch QME generation graph {self.graph_id}")
        
        # Create batch processing nodes
        batch_extraction_node = BatchExtractionNode(
            processor_factory=self.processor_factory,
            batch_size=self.batch_size,
            node_id="batch_extraction",
            correlation_id=self.correlation_id
        )
        
        batch_ner_node = BatchNERNode(
            batch_size=self.batch_size,
            node_id="batch_ner",
            correlation_id=self.correlation_id
        )
        
        batch_template_node = BatchTemplateGenerationNode(
            template_generator=self.template_generator,
            kg_repository=self.kg_repository,
            output_directory=self.output_directory,
            batch_size=self.batch_size,
            node_id="batch_template_generation",
            correlation_id=self.correlation_id
        )
        
        # Add nodes to graph
        self.add_node(batch_extraction_node)
        self.add_node(batch_ner_node)
        self.add_node(batch_template_node)
        
        # Define workflow edges
        self.add_edge("batch_extraction", "batch_ner")
        self.add_edge("batch_ner", "batch_template_generation")
        
        # Set entry and exit points
        self.set_entry_point("batch_extraction")
        self.set_exit_point("batch_template_generation")
        
        logger.info(f"Batch QME generation graph built with {len(self.nodes)} nodes")
    
    def validate_graph(self) -> bool:
        """Validate the batch QME generation graph."""
        required_nodes = ["batch_extraction", "batch_ner", "batch_template_generation"]
        
        for node_id in required_nodes:
            if node_id not in self.nodes:
                logger.error(f"Required batch node '{node_id}' not found")
                return False
        
        if self.has_cycles():
            logger.error("Batch QME generation graph contains cycles")
            return False
        
        logger.info("Batch QME generation graph validation successful")
        return True
    
    def process_patient_documents(self, patient_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple patient documents in batch."""
        logger.info(f"Processing {len(patient_documents)} patient documents in batch")
        
        # Group documents into batches
        batches = [patient_documents[i:i + self.batch_size] 
                  for i in range(0, len(patient_documents), self.batch_size)]
        
        all_results = []
        
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i + 1}/{len(batches)} with {len(batch)} documents")
            
            batch_state = {
                'patient_documents': batch,
                'batch_id': i,
                'correlation_id': self.correlation_id
            }
            
            try:
                result = self.execute(batch_state)
                if result.success:
                    all_results.extend(result.final_state.get('generated_templates', []))
                else:
                    logger.error(f"Batch {i + 1} processing failed: {result.message}")
            except Exception as e:
                logger.error(f"Error processing batch {i + 1}: {e}")
        
        return {
            'total_documents': len(patient_documents),
            'total_batches': len(batches),
            'successful_templates': len(all_results),
            'generated_templates': all_results
        }


# Placeholder nodes for enhanced and batch functionality
# These would be implemented with full functionality in a complete system

class KnowledgeGraphValidationNode(WorkflowNode):
    """Node for validating extracted information against knowledge graph."""
    
    def __init__(self, kg_repository: KnowledgeGraphRepository, 
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.kg_repository = kg_repository
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Validate entities against knowledge graph."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        entities = state.get('entities_extracted', [])
        
        # Validate entities against existing knowledge graph
        validated_entities = []
        for entity in entities:
            # Simple validation - check if similar entities exist
            entity['validated'] = True
            entity['confidence'] = min(entity.get('confidence', 0.0) + 0.1, 1.0)
            validated_entities.append(entity)
        
        return NodeResult.success_result(
            f"Validated {len(validated_entities)} entities",
            data={'entities_extracted': validated_entities, 'validation_completed': True}
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'entities_extracted' in state
    
    def get_required_inputs(self) -> List[str]:
        return ['entities_extracted']
    
    def get_output_keys(self) -> List[str]:
        return ['entities_extracted', 'validation_completed']


class TemplateValidationNode(WorkflowNode):
    """Node for validating generated templates."""
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Validate generated template."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        output_file_path = state.get('output_file_path')
        
        if output_file_path and os.path.exists(output_file_path):
            validation_results = {
                'file_exists': True,
                'file_size': os.path.getsize(output_file_path),
                'validation_passed': True
            }
        else:
            validation_results = {
                'file_exists': False,
                'validation_passed': False
            }
        
        return NodeResult.success_result(
            "Template validation completed",
            data={'template_validation': validation_results}
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return True  # Can validate any state
    
    def get_required_inputs(self) -> List[str]:
        return []
    
    def get_output_keys(self) -> List[str]:
        return ['template_validation']


class BatchExtractionNode(WorkflowNode):
    """Node for batch text extraction."""
    
    def __init__(self, processor_factory: ProcessorFactory, batch_size: int,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.processor_factory = processor_factory
        self.batch_size = batch_size
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute batch text extraction."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        patient_documents = state.get('patient_documents', [])
        
        extracted_documents = []
        for doc in patient_documents:
            # Simulate extraction
            extracted_documents.append({
                'document_id': doc.get('document_id'),
                'extracted_text': f"Extracted text from {doc.get('file_path', 'unknown')}",
                'file_path': doc.get('file_path')
            })
        
        return NodeResult.success_result(
            f"Batch extraction completed for {len(extracted_documents)} documents",
            data={'extracted_documents': extracted_documents}
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'patient_documents' in state
    
    def get_required_inputs(self) -> List[str]:
        return ['patient_documents']
    
    def get_output_keys(self) -> List[str]:
        return ['extracted_documents']


class BatchNERNode(WorkflowNode):
    """Node for batch named entity recognition."""
    
    def __init__(self, batch_size: int, node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.batch_size = batch_size
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute batch NER."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        extracted_documents = state.get('extracted_documents', [])
        
        for doc in extracted_documents:
            doc['entities_extracted'] = [
                {'type': 'patient', 'text': 'John Doe', 'confidence': 0.9},
                {'type': 'diagnosis', 'text': 'Lower back pain', 'confidence': 0.8}
            ]
        
        return NodeResult.success_result(
            f"Batch NER completed for {len(extracted_documents)} documents",
            data={'extracted_documents': extracted_documents}
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'extracted_documents' in state
    
    def get_required_inputs(self) -> List[str]:
        return ['extracted_documents']
    
    def get_output_keys(self) -> List[str]:
        return ['extracted_documents']


class BatchTemplateGenerationNode(WorkflowNode):
    """Node for batch template generation."""
    
    def __init__(self, template_generator: QMETemplateGenerator,
                 kg_repository: KnowledgeGraphRepository,
                 output_directory: str, batch_size: int,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        self.template_generator = template_generator
        self.kg_repository = kg_repository
        self.output_directory = output_directory
        self.batch_size = batch_size
    
    def execute(self, state: Dict[str, Any]) -> 'NodeResult':
        """Execute batch template generation."""
        from src.workflow.base.workflow_node import NodeResult
        
        # Placeholder implementation
        extracted_documents = state.get('extracted_documents', [])
        
        generated_templates = []
        for doc in extracted_documents:
            template_path = f"{self.output_directory}/template_{doc.get('document_id', 'unknown')}.docx"
            generated_templates.append({
                'document_id': doc.get('document_id'),
                'template_path': template_path,
                'generated': True
            })
        
        return NodeResult.success_result(
            f"Batch template generation completed for {len(generated_templates)} documents",
            data={'generated_templates': generated_templates}
        )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return 'extracted_documents' in state
    
    def get_required_inputs(self) -> List[str]:
        return ['extracted_documents']
    
    def get_output_keys(self) -> List[str]:
        return ['generated_templates']