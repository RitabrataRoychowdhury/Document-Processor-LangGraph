#!/usr/bin/env python3
"""
Simple FastAPI server for testing document extraction via API.
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

# Add project root to path
sys.path.append('.')

try:
    from src.config.app_config import AppConfig
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    from src.config.openrouter_config_manager import OpenRouterConfigManager
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="QME Document Extraction API",
    description="API for testing QME document field extraction with OpenRouter",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
extraction_service: Optional[ComprehensiveQMEFieldService] = None
openrouter_service: Optional[OpenRouterExtractionService] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global extraction_service, openrouter_service
    
    try:
        logger.info("Initializing QME extraction services...")
        
        # Load configuration
        config = AppConfig.from_env()
        
        # Initialize OpenRouter service
        openrouter_config_path = "config/settings/openrouter_config.yaml"
        
        openrouter_service = OpenRouterExtractionService(openrouter_config_path)
        
        # Initialize comprehensive QME field service
        extraction_service = ComprehensiveQMEFieldService(
            config=config,
            openrouter_service=openrouter_service
        )
        
        logger.info("✅ Services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "QME Document Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "extract": "/extract (POST with file upload)",
            "extract_openrouter": "/extract/openrouter (POST with file upload)",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if services are initialized
        if extraction_service is None or openrouter_service is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Services not initialized",
                    "extraction_service": extraction_service is not None,
                    "openrouter_service": openrouter_service is not None
                }
            )
        
        # Check OpenRouter configuration
        config_status = "configured" if openrouter_service.config else "not configured"
        
        return {
            "status": "healthy",
            "message": "All services operational",
            "services": {
                "extraction_service": "initialized",
                "openrouter_service": "initialized",
                "openrouter_config": config_status
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

@app.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Extract fields from uploaded document using comprehensive QME field service.
    
    This endpoint uses the full QME extraction pipeline with fallback methods.
    """
    if extraction_service is None:
        raise HTTPException(status_code=503, detail="Extraction service not initialized")
    
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    # Create temporary file
    temp_file = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Processing uploaded file: {file.filename} -> {temp_file_path}")
        
        # Extract fields using comprehensive service
        result = await extraction_service.extract_fields_comprehensive(temp_file_path)
        
        # Convert result to JSON-serializable format
        response_data = {
            "success": result.success,
            "document_id": result.document_id,
            "processing_time": result.processing_time,
            "extraction_strategy": result.extraction_strategy.value if result.extraction_strategy else "unknown",
            "extracted_fields": {},
            "confidence_scores": result.confidence_scores,
            "evidence_snippets": result.evidence_snippets,
            "quality_assessment": {
                "overall_score": result.quality_assessment.overall_score if result.quality_assessment else 0.0,
                "completeness_score": result.quality_assessment.completeness_score if result.quality_assessment else 0.0,
                "accuracy_score": result.quality_assessment.accuracy_score if result.quality_assessment else 0.0
            } if result.quality_assessment else None,
            "extraction_errors": result.extraction_errors,
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "type": file_ext
            }
        }
        
        # Convert ExtractedField objects to dict
        for field_name, field in result.extracted_fields.items():
            response_data["extracted_fields"][field_name] = {
                "name": field.name,
                "value": field.value,
                "confidence": field.confidence,
                "source_location": field.source_location,
                "validation_status": field.validation_status,
                "notes": field.notes
            }
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        # Cleanup on error
        if temp_file and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Extraction failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

@app.post("/extract/openrouter")
async def extract_with_openrouter(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Extract fields from uploaded document using OpenRouter service directly.
    
    This endpoint tests the OpenRouter extraction service specifically.
    """
    if openrouter_service is None:
        raise HTTPException(status_code=503, detail="OpenRouter service not initialized")
    
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
        )
    
    # Create temporary file
    temp_file = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Processing uploaded file with OpenRouter: {file.filename} -> {temp_file_path}")
        
        # Create extraction config
        from src.models.extraction_models import ExtractionConfig
        extraction_config = ExtractionConfig(
            prompt_template="patient_info",
            enable_vision=False,
            quality_threshold=0.7
        )
        
        # Extract fields using OpenRouter service directly
        result = await openrouter_service.extract_from_document(temp_file_path, extraction_config)
        
        # Convert result to JSON-serializable format
        response_data = {
            "success": True,
            "document_id": result.document_id,
            "extraction_method": result.extraction_method,
            "confidence_score": result.confidence_score,
            "extracted_fields": {},
            "quality_assessment": {
                "overall_score": result.quality_assessment.overall_score,
                "completeness_score": result.quality_assessment.completeness_score,
                "accuracy_score": result.quality_assessment.accuracy_score,
                "consistency_score": result.quality_assessment.consistency_score,
                "compliance_score": result.quality_assessment.compliance_score,
                "identified_issues": [
                    {
                        "issue_type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "affected_fields": issue.affected_fields,
                        "suggested_fix": issue.suggested_fix
                    } for issue in result.quality_assessment.identified_issues
                ]
            },
            "processing_metadata": {
                "extraction_method": result.processing_metadata.extraction_method,
                "processing_time": result.processing_metadata.processing_time,
                "model_used": result.processing_metadata.model_used,
                "prompt_template": result.processing_metadata.prompt_template,
                "api_version": result.processing_metadata.api_version
            },
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "type": file_ext
            }
        }
        
        # Convert ExtractedField objects to dict
        for field_name, field in result.extracted_fields.items():
            response_data["extracted_fields"][field_name] = {
                "name": field.name,
                "value": field.value,
                "confidence": field.confidence,
                "source_location": field.source_location,
                "validation_status": field.validation_status,
                "notes": field.notes
            }
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return response_data
        
    except Exception as e:
        logger.error(f"OpenRouter extraction failed: {e}")
        # Cleanup on error
        if temp_file and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "OpenRouter extraction failed",
                "message": str(e),
                "file_info": {
                    "filename": file.filename,
                    "size": len(content) if 'content' in locals() else 0
                }
            }
        )

def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup temporary file {file_path}: {e}")

if __name__ == "__main__":
    print("🚀 Starting QME Document Extraction API Server")
    print("=" * 50)
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📄 Upload Endpoint: http://localhost:8000/extract")
    print("🤖 OpenRouter Endpoint: http://localhost:8000/extract/openrouter")
    print("=" * 50)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )