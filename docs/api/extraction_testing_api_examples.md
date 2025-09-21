# QME Document Extraction Testing API - cURL Examples and Documentation

## Overview

This document provides comprehensive cURL examples, testing procedures, and troubleshooting guidance for the QME Document Extraction Testing API.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required for testing endpoints. In production, implement appropriate authentication mechanisms.

## File Upload Requirements

- **Supported formats**: PDF, DOCX, TXT
- **Maximum file size**: 50MB
- **Content-Type**: multipart/form-data

## API Endpoints and Examples

### 1. Health Check

Check the status of all services and API configurations.

```bash
# Basic health check
curl -X GET "http://localhost:8000/health" \
  -H "accept: application/json"

# Expected Response:
{
  "status": "healthy",
  "message": "All services operational",
  "services": {
    "extraction_service": true,
    "openrouter_service": true,
    "gemini_service": true,
    "template_assembler": true
  },
  "api_configurations": {
    "openrouter": "configured",
    "gemini": "configured"
  },
  "capabilities": {
    "openrouter_extraction": true,
    "gemini_extraction": true,
    "multi_layer_fallback": true,
    "template_generation": true,
    "quality_validation": true
  }
}
```

### 2. OpenRouter Extraction Testing

Test OpenRouter extraction service with Sonoma Sky Alpha model.

```bash
# Basic OpenRouter extraction
curl -X POST "http://localhost:8000/api/v1/extract/openrouter" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_document.pdf" \
  -F "prompt_template=patient_info"

# With custom prompt template
curl -X POST "http://localhost:8000/api/v1/extract/openrouter?prompt_template=medical_record" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@medical_record.docx"

# Expected Response:
{
  "success": true,
  "document_id": "doc_20250918_143052_a1b2c3d4",
  "extraction_method": "openrouter_claude_3_5_sonnet",
  "processing_time": 2.45,
  "extracted_fields": {
    "patient_name": "John Doe",
    "case_number": "WC-2024-001234",
    "injury_date": "2024-03-15",
    "body_parts": "Lower back, left knee"
  },
  "confidence_scores": {
    "patient_name": 0.95,
    "case_number": 0.88,
    "injury_date": 0.92,
    "body_parts": 0.85
  },
  "evidence_snippets": {
    "patient_name": ["Patient: John Doe"],
    "case_number": ["Case No: WC-2024-001234"]
  },
  "quality_assessment": {
    "overall_score": 87.5,
    "completeness_score": 85.0,
    "accuracy_score": 90.0,
    "consistency_score": 88.0,
    "compliance_score": 87.0
  },
  "extraction_errors": [],
  "file_info": {
    "filename": "sample_document.pdf",
    "size": 245760,
    "type": ".pdf",
    "prompt_template": "patient_info"
  }
}
```

### 3. Gemini Extraction Testing

Test Gemini extraction service as fallback option.

```bash
# Basic Gemini extraction
curl -X POST "http://localhost:8000/api/v1/extract/gemini" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_document.pdf" \
  -F "prompt_template=patient_info"

# Expected Response:
{
  "success": true,
  "document_id": "doc_20250918_143152_e5f6g7h8",
  "extraction_method": "gemini_extraction",
  "processing_time": 1.85,
  "extracted_fields": {
    "patient_name": "John Doe",
    "case_number": "WC-2024-001234",
    "injury_date": "2024-03-15"
  },
  "confidence_scores": {
    "patient_name": 0.88,
    "case_number": 0.82,
    "injury_date": 0.85
  },
  "quality_assessment": {
    "overall_score": 78.5,
    "completeness_score": 75.0,
    "accuracy_score": 82.0
  },
  "file_info": {
    "filename": "sample_document.pdf",
    "size": 245760,
    "type": ".pdf"
  }
}
```

### 4. Multi-Layer Fallback System Testing

Test the complete fallback chain: OpenRouter → Gemini → Rule-based.

```bash
# Test hybrid extraction strategy
curl -X POST "http://localhost:8000/api/v1/extract/multi-layer" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_document.pdf" \
  -F "extraction_strategy=hybrid" \
  -F "confidence_threshold=0.7"

# Test AI-enhanced strategy
curl -X POST "http://localhost:8000/api/v1/extract/multi-layer?extraction_strategy=ai_enhanced&confidence_threshold=0.8" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@complex_document.docx"

# Test rule-based strategy
curl -X POST "http://localhost:8000/api/v1/extract/multi-layer?extraction_strategy=rule_based" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@simple_document.txt"

# Expected Response:
{
  "success": true,
  "document_id": "doc_20250918_143252_i9j0k1l2",
  "extraction_method": "multi_layer_hybrid",
  "processing_time": 3.12,
  "extracted_fields": {
    "patient_name": "John Doe",
    "case_number": "WC-2024-001234",
    "injury_date": "2024-03-15",
    "body_parts": "Lower back, left knee",
    "diagnosis": "Lumbar strain, knee contusion"
  },
  "confidence_scores": {
    "patient_name": 0.95,
    "case_number": 0.88,
    "injury_date": 0.92,
    "body_parts": 0.85,
    "diagnosis": 0.78
  },
  "quality_assessment": {
    "overall_score": 89.2,
    "completeness_score": 88.0,
    "accuracy_score": 91.0,
    "consistency_score": 89.0,
    "compliance_score": 88.5
  },
  "file_info": {
    "filename": "sample_document.pdf",
    "size": 245760,
    "type": ".pdf",
    "strategy_used": "hybrid",
    "confidence_threshold": 0.7
  }
}
```

### 5. Extraction Method Comparison

Compare results across all available extraction methods.

```bash
# Compare all methods
curl -X POST "http://localhost:8000/api/v1/extract/compare" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_document.pdf" \
  -F "include_openrouter=true" \
  -F "include_gemini=true" \
  -F "include_multi_layer=true"

# Compare specific methods only
curl -X POST "http://localhost:8000/api/v1/extract/compare?include_openrouter=true&include_gemini=false&include_multi_layer=true" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.docx"

# Expected Response:
{
  "success": true,
  "document_id": "comparison_1726665172",
  "processing_time": 4.85,
  "extraction_results": {
    "openrouter": {
      "success": true,
      "extraction_method": "openrouter_claude_3_5_sonnet",
      "processing_time": 2.45,
      "extracted_fields": {
        "patient_name": "John Doe",
        "case_number": "WC-2024-001234"
      },
      "quality_assessment": {
        "overall_score": 87.5
      }
    },
    "gemini": {
      "success": true,
      "extraction_method": "gemini_extraction",
      "processing_time": 1.85,
      "extracted_fields": {
        "patient_name": "John Doe",
        "case_number": "WC-2024-001234"
      },
      "quality_assessment": {
        "overall_score": 78.5
      }
    },
    "multi_layer": {
      "success": true,
      "extraction_method": "multi_layer_hybrid",
      "processing_time": 3.12,
      "extracted_fields": {
        "patient_name": "John Doe",
        "case_number": "WC-2024-001234",
        "diagnosis": "Lumbar strain"
      },
      "quality_assessment": {
        "overall_score": 89.2
      }
    }
  },
  "comparison_analysis": {
    "field_coverage": {
      "openrouter": 2,
      "gemini": 2,
      "multi_layer": 3
    },
    "quality_comparison": {
      "openrouter": 87.5,
      "gemini": 78.5,
      "multi_layer": 89.2
    },
    "performance_comparison": {
      "openrouter": 2.45,
      "gemini": 1.85,
      "multi_layer": 3.12
    },
    "consensus_fields": {
      "patient_name": {
        "openrouter": "John Doe",
        "gemini": "John Doe",
        "multi_layer": "John Doe"
      }
    },
    "discrepancies": []
  },
  "best_method": "multi_layer",
  "file_info": {
    "filename": "sample_document.pdf",
    "size": 245760,
    "type": ".pdf",
    "methods_compared": ["openrouter", "gemini", "multi_layer"],
    "successful_methods": ["openrouter", "gemini", "multi_layer"]
  }
}
```

### 6. QME Template Generation

Generate complete QME reports from uploaded documents.

```bash
# Basic QME template generation
curl -X POST "http://localhost:8000/api/v1/qme/generate" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@pqme_report.pdf" \
  -F "output_format=docx" \
  -F "apply_professional_formatting=true" \
  -F "quality_threshold=70.0"

# Generate with specific parameters
curl -X POST "http://localhost:8000/api/v1/qme/generate?output_format=pdf&quality_threshold=80.0" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@medical_examination.docx"

# Expected Response:
{
  "success": true,
  "document_id": "doc_20250918_143352_m3n4o5p6",
  "processing_time": 8.75,
  "template_path": "/results/generated_documents/QME_Report_John_Doe_20250918_143352.docx",
  "extraction_results": {
    "success": true,
    "document_id": "doc_20250918_143352_m3n4o5p6",
    "extraction_method": "hybrid",
    "processing_time": 3.12,
    "extracted_fields": {
      "patient_name": "John Doe",
      "case_number": "WC-2024-001234",
      "injury_date": "2024-03-15",
      "diagnosis": "Lumbar strain, knee contusion"
    },
    "confidence_scores": {
      "patient_name": 0.95,
      "case_number": 0.88,
      "injury_date": 0.92,
      "diagnosis": 0.78
    }
  },
  "quality_assessment": {
    "overall_score": 85.5,
    "completeness_score": 82.0,
    "accuracy_score": 89.0,
    "assembly_strategy": "full_professional",
    "format_used": "docx"
  },
  "validation_issues": [
    {
      "rule_name": "impairment_rating_missing",
      "severity": "medium",
      "description": "Impairment rating not found in document",
      "field_name": "impairment_rating",
      "auto_fixable": false,
      "suggested_fix": "Manual review required for impairment rating"
    }
  ],
  "file_info": {
    "filename": "pqme_report.pdf",
    "size": 512000,
    "type": ".pdf",
    "output_format": "docx",
    "professional_formatting": true
  }
}
```

### 7. End-to-End QME Processing

Complete QME processing with full control over extraction and generation parameters.

```bash
# End-to-end processing with custom parameters
curl -X POST "http://localhost:8000/api/v1/qme/extract-and-generate" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@comprehensive_report.pdf" \
  -F "extraction_strategy=ai_enhanced" \
  -F "output_format=docx" \
  -F "confidence_threshold=0.8" \
  -F "quality_threshold=75.0"

# Expected Response: Same as QME generate endpoint
```

### 8. QME Template Validation

Validate QME template quality and compliance.

```bash
# Comprehensive validation
curl -X POST "http://localhost:8000/api/v1/qme/validate" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@qme_document.pdf" \
  -F "validation_level=comprehensive"

# Basic validation
curl -X POST "http://localhost:8000/api/v1/qme/validate?validation_level=basic" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@simple_report.txt"

# Expected Response:
{
  "success": true,
  "document_id": "doc_20250918_143452_q7r8s9t0",
  "validation_score": 82.5,
  "validation_issues": [
    {
      "type": "completeness",
      "severity": "medium",
      "message": "Completeness score (75.0%) indicates missing required fields",
      "field": "completeness"
    },
    {
      "type": "missing_field",
      "severity": "critical",
      "message": "Critical field 'case_number' is missing or empty",
      "field": "case_number"
    }
  ],
  "quality_metrics": {
    "overall_score": 82.5,
    "completeness_score": 75.0,
    "accuracy_score": 90.0,
    "consistency_score": 85.0,
    "compliance_score": 80.0
  },
  "recommendations": [
    "Ensure case number is clearly specified in the document",
    "Review template for regulatory compliance requirements"
  ]
}
```

## Performance Benchmarking

### Load Testing with Multiple Files

```bash
# Sequential processing test
for i in {1..10}; do
  echo "Processing file $i..."
  curl -X POST "http://localhost:8000/api/v1/extract/multi-layer" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@test_document_$i.pdf" \
    -w "Time: %{time_total}s\n" \
    -o "result_$i.json"
done

# Parallel processing test (requires GNU parallel)
parallel -j 5 curl -X POST "http://localhost:8000/api/v1/extract/openrouter" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@{}" \
  -w "Time: %{time_total}s\n" \
  -o "parallel_result_{#}.json" ::: test_document_*.pdf
```

### Performance Measurement Script

```bash
#!/bin/bash
# performance_test.sh

API_BASE="http://localhost:8000"
TEST_FILE="sample_document.pdf"
ITERATIONS=5

echo "QME API Performance Test"
echo "========================"

# Test each endpoint
endpoints=(
  "api/v1/extract/openrouter"
  "api/v1/extract/gemini"
  "api/v1/extract/multi-layer"
  "api/v1/qme/generate"
)

for endpoint in "${endpoints[@]}"; do
  echo "Testing $endpoint..."
  total_time=0
  
  for i in $(seq 1 $ITERATIONS); do
    response_time=$(curl -X POST "$API_BASE/$endpoint" \
      -H "Content-Type: multipart/form-data" \
      -F "file=@$TEST_FILE" \
      -w "%{time_total}" \
      -s -o /dev/null)
    
    total_time=$(echo "$total_time + $response_time" | bc)
    echo "  Iteration $i: ${response_time}s"
  done
  
  avg_time=$(echo "scale=3; $total_time / $ITERATIONS" | bc)
  echo "  Average: ${avg_time}s"
  echo ""
done
```

## Error Handling and Troubleshooting

### Common Error Responses

#### 400 Bad Request - Unsupported File Type
```json
{
  "detail": "Unsupported file type: .jpg. Allowed: ['.pdf', '.docx', '.txt']"
}
```

#### 422 Unprocessable Entity - Extraction Failed
```json
{
  "detail": "Field extraction failed: OpenRouter API timeout; Gemini service unavailable"
}
```

#### 500 Internal Server Error - Service Failure
```json
{
  "detail": {
    "error": "OpenRouter extraction failed",
    "message": "API call failed: Connection timeout",
    "file_info": {
      "filename": "document.pdf",
      "size": 245760
    }
  }
}
```

#### 503 Service Unavailable - Service Not Initialized
```json
{
  "detail": "OpenRouter service not available"
}
```

### Troubleshooting Guide

#### 1. Service Initialization Issues

**Problem**: Services not initializing properly
```bash
# Check health endpoint
curl -X GET "http://localhost:8000/health"
```

**Solutions**:
- Verify API keys are set in environment variables
- Check configuration files exist and are valid
- Ensure all dependencies are installed
- Review server logs for initialization errors

#### 2. File Upload Issues

**Problem**: File upload fails or times out
```bash
# Test with smaller file
curl -X POST "http://localhost:8000/api/v1/extract/openrouter" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@small_test.txt"
```

**Solutions**:
- Check file size (max 50MB)
- Verify file format is supported
- Ensure file is not corrupted
- Try with different file types

#### 3. API Rate Limiting

**Problem**: Getting 429 Too Many Requests
```bash
# Add delays between requests
sleep 2
curl -X POST "http://localhost:8000/api/v1/extract/openrouter" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Solutions**:
- Implement request throttling
- Use different API providers
- Check API quotas and limits
- Consider upgrading API plans

#### 4. Quality Issues

**Problem**: Low extraction quality scores
```bash
# Try different extraction strategies
curl -X POST "http://localhost:8000/api/v1/extract/multi-layer?extraction_strategy=ai_enhanced&confidence_threshold=0.6" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Solutions**:
- Lower confidence thresholds
- Try different extraction strategies
- Use comparison endpoint to find best method
- Improve document quality (scan resolution, text clarity)

#### 5. Template Generation Issues

**Problem**: Template generation fails
```bash
# Try simplified template generation
curl -X POST "http://localhost:8000/api/v1/qme/generate?output_format=txt&quality_threshold=50.0" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Solutions**:
- Lower quality thresholds
- Use text output format as fallback
- Check extracted fields have required data
- Review validation issues in response

## Sample Test Files

Create these sample files for testing:

### 1. Simple Text File (simple_test.txt)
```
Patient Name: John Doe
Case Number: WC-2024-001234
Date of Injury: March 15, 2024
Body Parts Affected: Lower back, left knee
Diagnosis: Lumbar strain, knee contusion
```

### 2. Complex Test Script
```bash
#!/bin/bash
# comprehensive_test.sh

# Test all endpoints with sample data
echo "Starting comprehensive API test..."

# Health check
echo "1. Health check..."
curl -s "http://localhost:8000/health" | jq '.status'

# OpenRouter extraction
echo "2. OpenRouter extraction..."
curl -s -X POST "http://localhost:8000/api/v1/extract/openrouter" \
  -F "file=@simple_test.txt" | jq '.success'

# Gemini extraction
echo "3. Gemini extraction..."
curl -s -X POST "http://localhost:8000/api/v1/extract/gemini" \
  -F "file=@simple_test.txt" | jq '.success'

# Multi-layer extraction
echo "4. Multi-layer extraction..."
curl -s -X POST "http://localhost:8000/api/v1/extract/multi-layer" \
  -F "file=@simple_test.txt" | jq '.success'

# Comparison
echo "5. Method comparison..."
curl -s -X POST "http://localhost:8000/api/v1/extract/compare" \
  -F "file=@simple_test.txt" | jq '.best_method'

# QME generation
echo "6. QME template generation..."
curl -s -X POST "http://localhost:8000/api/v1/qme/generate" \
  -F "file=@simple_test.txt" | jq '.success'

# Validation
echo "7. Template validation..."
curl -s -X POST "http://localhost:8000/api/v1/qme/validate" \
  -F "file=@simple_test.txt" | jq '.validation_score'

echo "Test completed!"
```

## Production Considerations

### Security
- Implement authentication and authorization
- Add rate limiting and request throttling
- Validate and sanitize all inputs
- Use HTTPS in production
- Implement proper CORS policies

### Monitoring
- Add request/response logging
- Implement health checks and metrics
- Monitor API performance and errors
- Set up alerting for service failures

### Scalability
- Implement request queuing for heavy processing
- Add caching for repeated requests
- Consider horizontal scaling with load balancers
- Optimize file handling and storage

### Documentation
- Keep API documentation updated
- Provide SDK/client libraries
- Include integration examples
- Maintain changelog for API versions