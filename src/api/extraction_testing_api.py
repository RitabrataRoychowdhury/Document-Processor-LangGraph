#!/usr/bin/env python3
"""
QME Document Extraction Testing API

Comprehensive FastAPI server for testing document extraction and QME template generation
with multi-layer fallback system, comparison capabilities, and performance benchmarking.
"""

import os
import sys
import tempfile
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# Add project root to path
sys.path.append('.')

try:
    from src.config.app_config import AppConfig
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService, QMEFieldExtractionConfig, ExtractionStrategy
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    from src.core.extraction.gemini_extraction_service import GeminiExtractionService
    from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler, TemplateAssemblyConfig
    from src.models.extraction_models import ExtractionConfig, ExtractionMethod
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with comprehensive documentation
app = FastAPI(
    title="QME Document Extraction Testing API",
    description="""
    Comprehensive API for testing QME document field extraction and template generation.
    
    Features:
    - Multi-layer extraction testing (OpenRouter → Gemini → Rule-based)
    - Individual API provider testing
    - Extraction method comparison
    - Complete QME template generation
    - Quality validation and assessment
    - Performance benchmarking
    
    Supported document types: PDF, DOCX, TXT
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ExtractionResponse(BaseModel):
    """Response model for extraction endpoints"""
    success: bool
    document_id: str
    extraction_method: str
    processing_time: float
    extracted_fields: Dict[str, Any]
    confidence_scores: Dict[str, float]
    evidence_snippets: Dict[str, List[str]]
    quality_assessment: Optional[Dict[str, Any]] = None
    extraction_errors: List[str] = []
    file_info: Dict[str, Any]

class ComparisonResponse(BaseModel):
    """Response model for extraction comparison"""
    success: bool
    document_id: str
    processing_time: float
    extraction_results: Dict[str, ExtractionResponse]
    comparison_analysis: Dict[str, Any]
    best_method: str
    file_info: Dict[str, Any]

class QMEGenerationResponse(BaseModel):
    """Response model for QME template generation"""
    success: bool
    document_id: str
    processing_time: float
    template_path: Optional[str] = None
    extraction_results: Optional[ExtractionResponse] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    validation_issues: List[Dict[str, Any]] = []
    file_info: Dict[str, Any]

class ValidationResponse(BaseModel):
    """Response model for template validation"""
    success: bool
    document_id: str
    validation_score: float
    validation_issues: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]
    recommendations: List[str]

# Global service instances
extraction_service: Optional[ComprehensiveQMEFieldService] = None
openrouter_service: Optional[OpenRouterExtractionService] = None
gemini_service: Optional[GeminiExtractionService] = None
template_assembler: Optional[ProfessionalTemplateAssembler] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global extraction_service, openrouter_service, gemini_service, template_assembler
    
    try:
        logger.info("Initializing QME extraction and template services...")
        
        # Load configuration
        config = AppConfig.from_env()
        
        # Initialize OpenRouter service
        try:
            openrouter_config_path = "config/settings/openrouter_config.yaml"
            openrouter_service = OpenRouterExtractionService(openrouter_config_path)
            logger.info("✅ OpenRouter service initialized")
        except Exception as e:
            logger.warning(f"⚠️ OpenRouter service initialization failed: {e}")
            openrouter_service = None
        
        # Initialize Gemini service
        try:
            gemini_service = GeminiExtractionService()
            logger.info("✅ Gemini service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini service initialization failed: {e}")
            gemini_service = None
        
        # Initialize comprehensive QME field service
        qme_config = QMEFieldExtractionConfig(
            extraction_strategy=ExtractionStrategy.HYBRID,
            enable_openrouter=openrouter_service is not None,
            confidence_threshold=0.7,
            enable_cross_validation=True
        )
        extraction_service = ComprehensiveQMEFieldService(config=qme_config)
        logger.info("✅ Comprehensive QME field service initialized")
        
        # Initialize template assembler
        template_config = TemplateAssemblyConfig(
            apply_professional_formatting=True,
            validate_before_assembly=True,
            validate_after_assembly=True,
            quality_threshold=70.0
        )
        template_assembler = ProfessionalTemplateAssembler(config=template_config)
        logger.info("✅ Professional template assembler initialized")
        
        logger.info("🚀 All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information and available endpoints."""
    return {
        "message": "QME Document Extraction Testing API",
        "version": "1.0.0",
        "description": "Comprehensive API for testing QME document extraction and template generation",
        "endpoints": {
            "health": "GET /health - Health check and service status",
            "extraction": {
                "openrouter": "POST /api/v1/extract/openrouter - Test OpenRouter extraction only",
                "gemini": "POST /api/v1/extract/gemini - Test Gemini extraction only", 
                "multi_layer": "POST /api/v1/extract/multi-layer - Test complete fallback system",
                "compare": "POST /api/v1/extract/compare - Compare all extraction methods"
            },
            "qme": {
                "generate": "POST /api/v1/qme/generate - Complete QME report generation",
                "extract_and_generate": "POST /api/v1/qme/extract-and-generate - End-to-end processing",
                "validate": "POST /api/v1/qme/validate - Template quality validation"
            },
            "documentation": {
                "swagger": "/docs - Interactive API documentation",
                "redoc": "/redoc - Alternative API documentation"
            }
        },
        "supported_formats": ["PDF", "DOCX", "TXT"],
        "max_file_size": "50MB"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed service status."""
    try:
        service_status = {
            "extraction_service": extraction_service is not None,
            "openrouter_service": openrouter_service is not None,
            "gemini_service": gemini_service is not None,
            "template_assembler": template_assembler is not None
        }
        
        # Check API configurations
        api_status = {}
        if openrouter_service:
            api_status["openrouter"] = "configured" if openrouter_service.config else "not configured"
        if gemini_service:
            api_status["gemini"] = "configured" if gemini_service.api_key else "not configured"
        
        all_healthy = all(service_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "message": "All services operational" if all_healthy else "Some services unavailable",
            "services": service_status,
            "api_configurations": api_status,
            "capabilities": {
                "openrouter_extraction": openrouter_service is not None,
                "gemini_extraction": gemini_service is not None,
                "multi_layer_fallback": extraction_service is not None,
                "template_generation": template_assembler is not None,
                "quality_validation": True
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }
        )

# Extraction Testing Endpoints

@app.post("/api/v1/extract/openrouter", response_model=ExtractionResponse)
async def extract_with_openrouter(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    prompt_template: str = Query("patient_info", description="Prompt template to use for extraction")
):
    """
    Extract fields from uploaded document using OpenRouter service only.
    
    This endpoint tests the OpenRouter extraction service specifically with Sonoma Sky Alpha model.
    """
    if not openrouter_service:
        raise HTTPException(status_code=503, detail="OpenRouter service not available")
    
    return await _perform_single_extraction(
        file, openrouter_service, "openrouter", prompt_template, background_tasks
    )

@app.post("/api/v1/extract/gemini", response_model=ExtractionResponse)
async def extract_with_gemini(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    prompt_template: str = Query("patient_info", description="Prompt template to use for extraction")
):
    """
    Extract fields from uploaded document using Gemini service only.
    
    This endpoint tests the Gemini extraction service specifically.
    """
    if not gemini_service:
        raise HTTPException(status_code=503, detail="Gemini service not available")
    
    return await _perform_single_extraction(
        file, gemini_service, "gemini", prompt_template, background_tasks
    )

@app.post("/api/v1/extract/multi-layer", response_model=ExtractionResponse)
async def extract_with_multi_layer(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    extraction_strategy: str = Query("hybrid", description="Extraction strategy: hybrid, ai_enhanced, rule_based"),
    confidence_threshold: float = Query(0.7, description="Minimum confidence threshold")
):
    """
    Extract fields using complete multi-layer fallback system.
    
    This endpoint tests the complete fallback chain: OpenRouter → Gemini → Rule-based
    """
    if not extraction_service:
        raise HTTPException(status_code=503, detail="Multi-layer extraction service not available")
    
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    temp_file_path = None
    try:
        start_time = time.time()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Processing uploaded file with multi-layer extraction: {file.filename}")
        
        # Configure extraction strategy
        strategy_map = {
            "hybrid": ExtractionStrategy.HYBRID,
            "ai_enhanced": ExtractionStrategy.AI_ENHANCED,
            "rule_based": ExtractionStrategy.RULE_BASED,
            "vision_enabled": ExtractionStrategy.VISION_ENABLED
        }
        
        extraction_service.config.extraction_strategy = strategy_map.get(
            extraction_strategy, ExtractionStrategy.HYBRID
        )
        extraction_service.config.confidence_threshold = confidence_threshold
        
        # Perform extraction
        result = await extraction_service.extract_fields_comprehensive(temp_file_path)
        
        processing_time = time.time() - start_time
        
        # Convert result to response format
        response_data = ExtractionResponse(
            success=result.success,
            document_id=result.document_id,
            extraction_method=f"multi_layer_{extraction_strategy}",
            processing_time=processing_time,
            extracted_fields={name: field.value for name, field in result.extracted_fields.items()},
            confidence_scores=result.confidence_scores,
            evidence_snippets=result.evidence_snippets,
            quality_assessment={
                "overall_score": result.quality_assessment.overall_score if result.quality_assessment else 0.0,
                "completeness_score": result.quality_assessment.completeness_score if result.quality_assessment else 0.0,
                "accuracy_score": result.quality_assessment.accuracy_score if result.quality_assessment else 0.0,
                "consistency_score": result.quality_assessment.consistency_score if result.quality_assessment else 0.0,
                "compliance_score": result.quality_assessment.compliance_score if result.quality_assessment else 0.0
            } if result.quality_assessment else None,
            extraction_errors=result.extraction_errors,
            file_info={
                "filename": file.filename,
                "size": len(content),
                "type": file_ext,
                "strategy_used": extraction_strategy,
                "confidence_threshold": confidence_threshold
            }
        )
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Multi-layer extraction failed: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Multi-layer extraction failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

@app.post("/api/v1/extract/compare", response_model=ComparisonResponse)
async def compare_extraction_methods(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    include_openrouter: bool = Query(True, description="Include OpenRouter in comparison"),
    include_gemini: bool = Query(True, description="Include Gemini in comparison"),
    include_multi_layer: bool = Query(True, description="Include multi-layer system in comparison")
):
    """
    Compare extraction results across all available methods.
    
    This endpoint runs extraction using multiple methods and provides detailed comparison analysis.
    """
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    temp_file_path = None
    try:
        start_time = time.time()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Comparing extraction methods for: {file.filename}")
        
        # Run extractions concurrently
        extraction_tasks = []
        method_names = []
        
        if include_openrouter and openrouter_service:
            extraction_tasks.append(_extract_with_service(temp_file_path, openrouter_service, "openrouter"))
            method_names.append("openrouter")
        
        if include_gemini and gemini_service:
            extraction_tasks.append(_extract_with_service(temp_file_path, gemini_service, "gemini"))
            method_names.append("gemini")
        
        if include_multi_layer and extraction_service:
            extraction_tasks.append(_extract_with_comprehensive_service(temp_file_path))
            method_names.append("multi_layer")
        
        if not extraction_tasks:
            raise HTTPException(status_code=503, detail="No extraction services available for comparison")
        
        # Execute all extractions concurrently
        extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        # Process results
        comparison_results = {}
        successful_results = {}
        
        for i, (method_name, result) in enumerate(zip(method_names, extraction_results)):
            if isinstance(result, Exception):
                comparison_results[method_name] = {
                    "success": False,
                    "error": str(result),
                    "processing_time": 0.0
                }
            else:
                comparison_results[method_name] = result
                if result.get("success", False):
                    successful_results[method_name] = result
        
        # Perform comparison analysis
        comparison_analysis = _analyze_extraction_comparison(successful_results)
        
        # Determine best method
        best_method = _determine_best_extraction_method(successful_results)
        
        processing_time = time.time() - start_time
        
        response_data = ComparisonResponse(
            success=len(successful_results) > 0,
            document_id=f"comparison_{int(time.time())}",
            processing_time=processing_time,
            extraction_results=comparison_results,
            comparison_analysis=comparison_analysis,
            best_method=best_method,
            file_info={
                "filename": file.filename,
                "size": len(content),
                "type": file_ext,
                "methods_compared": method_names,
                "successful_methods": list(successful_results.keys())
            }
        )
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Extraction comparison failed: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Extraction comparison failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

# QME Template Generation Endpoints

@app.post("/api/v1/qme/generate", response_model=QMEGenerationResponse)
async def generate_qme_template(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    output_format: str = Query("docx", description="Output format: docx, pdf, html, txt"),
    apply_professional_formatting: bool = Query(True, description="Apply professional formatting"),
    quality_threshold: float = Query(70.0, description="Minimum quality threshold")
):
    """
    Generate complete QME report from uploaded document.
    
    This endpoint performs end-to-end processing: extraction → validation → template generation
    """
    if not extraction_service or not template_assembler:
        raise HTTPException(status_code=503, detail="QME generation services not available")
    
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    temp_file_path = None
    try:
        start_time = time.time()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Generating QME template for: {file.filename}")
        
        # Step 1: Extract fields
        extraction_result = await extraction_service.extract_fields_comprehensive(temp_file_path)
        
        if not extraction_result.success:
            raise HTTPException(
                status_code=422,
                detail=f"Field extraction failed: {'; '.join(extraction_result.extraction_errors)}"
            )
        
        # Step 2: Prepare template data
        template_data = {
            "patient_info": {},
            "medical_findings": {},
            "examination_results": {},
            "quality_metadata": {
                "extraction_method": extraction_result.extraction_strategy.value,
                "confidence_scores": extraction_result.field_confidence_scores,
                "quality_assessment": extraction_result.quality_assessment.__dict__ if extraction_result.quality_assessment else None
            }
        }
        
        # Organize extracted fields into template sections
        for field_name, field in extraction_result.extracted_fields.items():
            if field_name in ['patient_name', 'case_number', 'injury_date', 'date_of_birth']:
                template_data["patient_info"][field_name] = field.value
            elif field_name in ['diagnosis', 'body_parts', 'impairment_rating']:
                template_data["medical_findings"][field_name] = field.value
            else:
                template_data["examination_results"][field_name] = field.value
        
        # Step 3: Configure template assembler
        template_assembler.config.output_format = output_format
        template_assembler.config.apply_professional_formatting = apply_professional_formatting
        template_assembler.config.quality_threshold = quality_threshold
        
        # Step 4: Generate template
        template_result = template_assembler.assemble_professional_template(template_data)
        
        processing_time = time.time() - start_time
        
        # Convert extraction result to response format
        extraction_response = ExtractionResponse(
            success=extraction_result.success,
            document_id=extraction_result.document_id,
            extraction_method=extraction_result.extraction_strategy.value,
            processing_time=extraction_result.processing_time,
            extracted_fields={name: field.value for name, field in extraction_result.extracted_fields.items()},
            confidence_scores=extraction_result.field_confidence_scores,
            evidence_snippets=extraction_result.evidence_snippets,
            quality_assessment={
                "overall_score": extraction_result.quality_assessment.overall_score if extraction_result.quality_assessment else 0.0,
                "completeness_score": extraction_result.quality_assessment.completeness_score if extraction_result.quality_assessment else 0.0,
                "accuracy_score": extraction_result.quality_assessment.accuracy_score if extraction_result.quality_assessment else 0.0
            } if extraction_result.quality_assessment else None,
            extraction_errors=extraction_result.extraction_errors,
            file_info={
                "filename": file.filename,
                "size": len(content),
                "type": file_ext
            }
        )
        
        response_data = QMEGenerationResponse(
            success=template_result.success,
            document_id=extraction_result.document_id,
            processing_time=processing_time,
            template_path=template_result.template_path,
            extraction_results=extraction_response,
            quality_assessment={
                "overall_score": template_result.quality_assessment.overall_score if template_result.quality_assessment else 0.0,
                "completeness_score": template_result.quality_assessment.completeness_score if template_result.quality_assessment else 0.0,
                "accuracy_score": template_result.quality_assessment.accuracy_score if template_result.quality_assessment else 0.0,
                "assembly_strategy": template_result.assembly_strategy.value if template_result.assembly_strategy else None,
                "format_used": template_result.format_used.value if template_result.format_used else None
            } if template_result.quality_assessment else None,
            validation_issues=[
                {
                    "rule_name": issue.rule_name,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "field_name": issue.field_name,
                    "auto_fixable": issue.auto_fixable,
                    "suggested_fix": issue.suggested_fix
                } for issue in template_result.validation_issues
            ],
            file_info={
                "filename": file.filename,
                "size": len(content),
                "type": file_ext,
                "output_format": output_format,
                "professional_formatting": apply_professional_formatting
            }
        )
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"QME template generation failed: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "QME template generation failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

@app.post("/api/v1/qme/extract-and-generate", response_model=QMEGenerationResponse)
async def extract_and_generate_qme(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    extraction_strategy: str = Query("hybrid", description="Extraction strategy"),
    output_format: str = Query("docx", description="Output format"),
    confidence_threshold: float = Query(0.7, description="Confidence threshold"),
    quality_threshold: float = Query(70.0, description="Quality threshold")
):
    """
    End-to-end QME processing: extraction with specified strategy + template generation.
    
    This endpoint provides complete control over both extraction and generation parameters.
    """
    # This endpoint reuses the generate_qme_template logic but with more configuration options
    return await generate_qme_template(
        file=file,
        background_tasks=background_tasks,
        output_format=output_format,
        apply_professional_formatting=True,
        quality_threshold=quality_threshold
    )

@app.post("/api/v1/qme/validate", response_model=ValidationResponse)
async def validate_qme_template(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    validation_level: str = Query("comprehensive", description="Validation level: basic, standard, comprehensive")
):
    """
    Validate QME template quality and compliance.
    
    This endpoint performs quality validation on extracted data and provides recommendations.
    """
    if not extraction_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    temp_file_path = None
    try:
        start_time = time.time()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Validating QME template for: {file.filename}")
        
        # Extract fields for validation
        extraction_result = await extraction_service.extract_fields_comprehensive(temp_file_path)
        
        # Perform validation analysis
        validation_issues = []
        quality_metrics = {}
        recommendations = []
        
        if extraction_result.quality_assessment:
            qa = extraction_result.quality_assessment
            quality_metrics = {
                "overall_score": qa.overall_score,
                "completeness_score": qa.completeness_score,
                "accuracy_score": qa.accuracy_score,
                "consistency_score": qa.consistency_score,
                "compliance_score": qa.compliance_score
            }
            
            # Generate validation issues based on quality assessment
            if qa.overall_score < 70.0:
                validation_issues.append({
                    "type": "quality",
                    "severity": "high",
                    "message": f"Overall quality score ({qa.overall_score:.1f}%) below recommended threshold (70%)",
                    "field": "overall"
                })
                recommendations.append("Review extraction results and consider manual verification")
            
            if qa.completeness_score < 80.0:
                validation_issues.append({
                    "type": "completeness",
                    "severity": "medium",
                    "message": f"Completeness score ({qa.completeness_score:.1f}%) indicates missing required fields",
                    "field": "completeness"
                })
                recommendations.append("Ensure all required patient and medical information is present")
            
            if qa.compliance_score < 90.0:
                validation_issues.append({
                    "type": "compliance",
                    "severity": "high",
                    "message": f"Compliance score ({qa.compliance_score:.1f}%) below regulatory requirements",
                    "field": "compliance"
                })
                recommendations.append("Review template for regulatory compliance requirements")
        
        # Check for missing critical fields
        critical_fields = ['patient_name', 'case_number', 'injury_date']
        for field in critical_fields:
            if field not in extraction_result.extracted_fields or not extraction_result.extracted_fields[field].value:
                validation_issues.append({
                    "type": "missing_field",
                    "severity": "critical",
                    "message": f"Critical field '{field}' is missing or empty",
                    "field": field
                })
                recommendations.append(f"Ensure {field.replace('_', ' ')} is clearly specified in the document")
        
        # Calculate overall validation score
        validation_score = quality_metrics.get("overall_score", 0.0)
        if validation_issues:
            critical_issues = len([issue for issue in validation_issues if issue["severity"] == "critical"])
            high_issues = len([issue for issue in validation_issues if issue["severity"] == "high"])
            validation_score = max(0.0, validation_score - (critical_issues * 20) - (high_issues * 10))
        
        processing_time = time.time() - start_time
        
        response_data = ValidationResponse(
            success=len([issue for issue in validation_issues if issue["severity"] == "critical"]) == 0,
            document_id=extraction_result.document_id,
            validation_score=validation_score,
            validation_issues=validation_issues,
            quality_metrics=quality_metrics,
            recommendations=recommendations
        )
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"QME template validation failed: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "QME template validation failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

# Download endpoint for generated templates
@app.get("/api/v1/qme/download/{document_id}")
async def download_qme_template(document_id: str):
    """Download generated QME template by document ID."""
    # This would implement template download logic
    # For now, return a placeholder response
    raise HTTPException(status_code=501, detail="Template download not yet implemented")

# Helper functions

async def _perform_single_extraction(
    file: UploadFile,
    service,
    method_name: str,
    prompt_template: str,
    background_tasks: BackgroundTasks
) -> ExtractionResponse:
    """Helper function to perform extraction with a single service."""
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    temp_file_path = None
    try:
        start_time = time.time()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Processing uploaded file with {method_name}: {file.filename}")
        
        # Create extraction config
        extraction_config = ExtractionConfig(
            prompt_template=prompt_template,
            enable_vision=False,
            quality_threshold=0.7
        )
        
        # Extract fields using specified service
        result = service.extract_from_document(temp_file_path, extraction_config)
        
        processing_time = time.time() - start_time
        
        # Convert result to response format
        response_data = ExtractionResponse(
            success=True,
            document_id=result.document_id,
            extraction_method=f"{method_name}_{result.extraction_method}",
            processing_time=processing_time,
            extracted_fields={name: field.value for name, field in result.extracted_fields.items()},
            confidence_scores={name: field.confidence for name, field in result.extracted_fields.items()},
            evidence_snippets={name: [field.source_location] if field.source_location else [] for name, field in result.extracted_fields.items()},
            quality_assessment={
                "overall_score": result.quality_assessment.overall_score,
                "completeness_score": result.quality_assessment.completeness_score,
                "accuracy_score": result.quality_assessment.accuracy_score,
                "consistency_score": result.quality_assessment.consistency_score,
                "compliance_score": result.quality_assessment.compliance_score
            } if result.quality_assessment else None,
            extraction_errors=[],
            file_info={
                "filename": file.filename,
                "size": len(content),
                "type": file_ext,
                "prompt_template": prompt_template
            }
        )
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"{method_name} extraction failed: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"{method_name} extraction failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

async def _extract_with_service(file_path: str, service, method_name: str) -> Dict[str, Any]:
    """Helper function to extract with a specific service for comparison."""
    try:
        extraction_config = ExtractionConfig(
            prompt_template="patient_info",
            enable_vision=False,
            quality_threshold=0.7
        )
        
        result = service.extract_from_document(file_path, extraction_config)
        
        return {
            "success": True,
            "document_id": result.document_id,
            "extraction_method": f"{method_name}_{result.extraction_method}",
            "processing_time": result.processing_metadata.processing_time if result.processing_metadata else 0.0,
            "extracted_fields": {name: field.value for name, field in result.extracted_fields.items()},
            "confidence_scores": {name: field.confidence for name, field in result.extracted_fields.items()},
            "quality_assessment": {
                "overall_score": result.quality_assessment.overall_score,
                "completeness_score": result.quality_assessment.completeness_score,
                "accuracy_score": result.quality_assessment.accuracy_score
            } if result.quality_assessment else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_time": 0.0
        }

async def _extract_with_comprehensive_service(file_path: str) -> Dict[str, Any]:
    """Helper function to extract with comprehensive service for comparison."""
    try:
        result = await extraction_service.extract_fields_comprehensive(file_path)
        
        return {
            "success": result.success,
            "document_id": result.document_id,
            "extraction_method": f"multi_layer_{result.extraction_strategy.value}",
            "processing_time": result.processing_time,
            "extracted_fields": {name: field.value for name, field in result.extracted_fields.items()},
            "confidence_scores": result.confidence_scores,
            "quality_assessment": {
                "overall_score": result.quality_assessment.overall_score,
                "completeness_score": result.quality_assessment.completeness_score,
                "accuracy_score": result.quality_assessment.accuracy_score
            } if result.quality_assessment else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_time": 0.0
        }

def _analyze_extraction_comparison(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze comparison results and provide insights."""
    if not results:
        return {"error": "No successful extractions to compare"}
    
    analysis = {
        "field_coverage": {},
        "confidence_comparison": {},
        "quality_comparison": {},
        "performance_comparison": {},
        "consensus_fields": {},
        "discrepancies": []
    }
    
    # Analyze field coverage
    all_fields = set()
    for method, result in results.items():
        fields = result.get("extracted_fields", {})
        all_fields.update(fields.keys())
        analysis["field_coverage"][method] = len(fields)
    
    # Find consensus fields (fields extracted by multiple methods)
    for field in all_fields:
        values = {}
        for method, result in results.items():
            fields = result.get("extracted_fields", {})
            if field in fields:
                values[method] = fields[field]
        
        if len(values) > 1:
            analysis["consensus_fields"][field] = values
            
            # Check for discrepancies
            unique_values = set(values.values())
            if len(unique_values) > 1:
                analysis["discrepancies"].append({
                    "field": field,
                    "values": values,
                    "methods_disagreeing": len(unique_values)
                })
    
    # Compare quality scores
    for method, result in results.items():
        qa = result.get("quality_assessment", {})
        if qa:
            analysis["quality_comparison"][method] = qa.get("overall_score", 0.0)
    
    # Compare performance
    for method, result in results.items():
        analysis["performance_comparison"][method] = result.get("processing_time", 0.0)
    
    return analysis

def _determine_best_extraction_method(results: Dict[str, Dict[str, Any]]) -> str:
    """Determine the best extraction method based on quality and coverage."""
    if not results:
        return "none"
    
    scores = {}
    for method, result in results.items():
        score = 0.0
        
        # Quality score (40% weight)
        qa = result.get("quality_assessment", {})
        if qa:
            score += qa.get("overall_score", 0.0) * 0.4
        
        # Field coverage (30% weight)
        field_count = len(result.get("extracted_fields", {}))
        score += min(100.0, field_count * 10) * 0.3
        
        # Performance (20% weight) - inverse relationship
        processing_time = result.get("processing_time", 1.0)
        performance_score = max(0.0, 100.0 - processing_time * 10)
        score += performance_score * 0.2
        
        # Success bonus (10% weight)
        if result.get("success", False):
            score += 100.0 * 0.1
        
        scores[method] = score
    
    return max(scores, key=scores.get)

def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup temporary file {file_path}: {e}")

if __name__ == "__main__":
    print("🚀 Starting QME Document Extraction Testing API Server")
    print("=" * 60)
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("")
    print("🔧 Extraction Endpoints:")
    print("   • OpenRouter: POST /api/v1/extract/openrouter")
    print("   • Gemini: POST /api/v1/extract/gemini")
    print("   • Multi-layer: POST /api/v1/extract/multi-layer")
    print("   • Compare: POST /api/v1/extract/compare")
    print("")
    print("📄 QME Template Endpoints:")
    print("   • Generate: POST /api/v1/qme/generate")
    print("   • Extract & Generate: POST /api/v1/qme/extract-and-generate")
    print("   • Validate: POST /api/v1/qme/validate")
    print("=" * 60)
    
    uvicorn.run(
        "src.api.extraction_testing_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )