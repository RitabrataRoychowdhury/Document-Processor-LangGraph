# QME Document Extraction Testing API

## Overview

The QME Document Extraction Testing API provides comprehensive endpoints for testing document field extraction and QME template generation with multi-layer fallback capabilities.

## Features

- **Multi-layer Extraction**: OpenRouter → Gemini → Rule-based fallback system
- **Individual API Testing**: Test OpenRouter and Gemini services independently
- **Extraction Comparison**: Compare results across all extraction methods
- **QME Template Generation**: Complete end-to-end QME report generation
- **Quality Validation**: Comprehensive template quality assessment
- **Performance Benchmarking**: Built-in performance monitoring and metrics

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn python-multipart requests
```

### 2. Set Environment Variables

```bash
# Required for OpenRouter API
export OPENROUTER_API_KEY="your_openrouter_api_key"

# Required for Gemini API
export GEMINI_API_KEY="your_gemini_api_key"
```

### 3. Start the API Server

```bash
# Using the startup script (recommended)
python scripts/start_extraction_api.py

# Or directly with uvicorn
uvicorn src.api.extraction_testing_api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test the API

```bash
# Run comprehensive tests
python scripts/test_extraction_api.py

# Test specific endpoint
python scripts/test_extraction_api.py --test health

# Test with custom URL
python scripts/test_extraction_api.py --url http://localhost:8000
```

## API Endpoints

### Health and Status
- `GET /health` - Service health check and status

### Extraction Testing
- `POST /api/v1/extract/openrouter` - OpenRouter extraction only
- `POST /api/v1/extract/gemini` - Gemini extraction only
- `POST /api/v1/extract/multi-layer` - Multi-layer fallback system
- `POST /api/v1/extract/compare` - Compare all extraction methods

### QME Template Generation
- `POST /api/v1/qme/generate` - Complete QME report generation
- `POST /api/v1/qme/extract-and-generate` - End-to-end processing
- `POST /api/v1/qme/validate` - Template quality validation

### Documentation
- `/docs` - Interactive Swagger UI documentation
- `/redoc` - Alternative ReDoc documentation

## Usage Examples

### Basic Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

### OpenRouter Extraction

```bash
curl -X POST "http://localhost:8000/api/v1/extract/openrouter" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_document.pdf" \
  -F "prompt_template=patient_info"
```

### Multi-layer Extraction

```bash
curl -X POST "http://localhost:8000/api/v1/extract/multi-layer" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "extraction_strategy=hybrid" \
  -F "confidence_threshold=0.7"
```

### QME Template Generation

```bash
curl -X POST "http://localhost:8000/api/v1/qme/generate" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@pqme_report.pdf" \
  -F "output_format=docx" \
  -F "quality_threshold=70.0"
```

## Supported File Formats

- **PDF** (.pdf) - Portable Document Format
- **DOCX** (.docx) - Microsoft Word Document
- **TXT** (.txt) - Plain Text

Maximum file size: 50MB

## Configuration

### API Keys

Set the following environment variables:

```bash
# OpenRouter API (required for OpenRouter endpoints)
export OPENROUTER_API_KEY="your_key_here"

# Gemini API (required for Gemini endpoints)
export GEMINI_API_KEY="your_key_here"
```

### Configuration Files

The API uses these configuration files (optional):

- `config/settings/openrouter_config.yaml` - OpenRouter API settings
- `config/settings/gemini_config.yaml` - Gemini API settings
- `config/templates/qme_template_structure.yaml` - QME template structure

## Response Formats

### Extraction Response

```json
{
  "success": true,
  "document_id": "doc_20250918_143052_a1b2c3d4",
  "extraction_method": "openrouter_claude_3_5_sonnet",
  "processing_time": 2.45,
  "extracted_fields": {
    "patient_name": "John Doe",
    "case_number": "WC-2024-001234"
  },
  "confidence_scores": {
    "patient_name": 0.95,
    "case_number": 0.88
  },
  "quality_assessment": {
    "overall_score": 87.5,
    "completeness_score": 85.0,
    "accuracy_score": 90.0
  }
}
```

### QME Generation Response

```json
{
  "success": true,
  "document_id": "doc_20250918_143352_m3n4o5p6",
  "processing_time": 8.75,
  "template_path": "/results/generated_documents/QME_Report_John_Doe_20250918_143352.docx",
  "quality_assessment": {
    "overall_score": 85.5,
    "assembly_strategy": "full_professional"
  },
  "validation_issues": [
    {
      "rule_name": "impairment_rating_missing",
      "severity": "medium",
      "description": "Impairment rating not found in document"
    }
  ]
}
```

## Error Handling

### Common Error Codes

- `400` - Bad Request (invalid file type, missing parameters)
- `422` - Unprocessable Entity (extraction failed)
- `500` - Internal Server Error (service failure)
- `503` - Service Unavailable (service not initialized)

### Error Response Format

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

## Performance Monitoring

The API includes built-in performance monitoring:

- Processing time tracking for all endpoints
- Quality score assessment and comparison
- Service availability monitoring
- Error rate tracking

## Testing

### Automated Testing

```bash
# Run all tests
python scripts/test_extraction_api.py

# Run specific test
python scripts/test_extraction_api.py --test openrouter

# Save results to file
python scripts/test_extraction_api.py --output my_results.json
```

### Manual Testing

Use the interactive documentation at `/docs` to test endpoints manually with file uploads and parameter configuration.

## Troubleshooting

### Service Not Starting

1. Check dependencies: `pip install -r requirements.txt`
2. Verify Python version: Python 3.8+
3. Check port availability: `lsof -i :8000`

### API Key Issues

1. Verify environment variables are set
2. Check API key validity
3. Review service logs for authentication errors

### Extraction Failures

1. Check file format and size
2. Verify API service availability
3. Try different extraction strategies
4. Review quality thresholds

### Template Generation Issues

1. Ensure extraction succeeded first
2. Check output directory permissions
3. Verify template configuration files
4. Try lower quality thresholds

## Development

### Project Structure

```
src/api/
├── extraction_testing_api.py    # Main API application
scripts/
├── start_extraction_api.py      # Server startup script
├── test_extraction_api.py       # Automated testing script
docs/api/
├── README.md                    # This file
├── extraction_testing_api_examples.md  # Detailed examples
```

### Adding New Endpoints

1. Define endpoint in `extraction_testing_api.py`
2. Add Pydantic models for request/response
3. Implement business logic
4. Add tests to `test_extraction_api.py`
5. Update documentation

## Support

For issues and questions:

1. Check the health endpoint: `/health`
2. Review server logs for errors
3. Run the test suite for diagnostics
4. Check configuration files and environment variables

## License

This API is part of the QME Document Processing System.