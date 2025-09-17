# Backend-Frontend Integration Fix Spec

## Overview
This spec focuses on resolving all backend errors and ensuring seamless frontend-backend integration for the production-ready QME system. Based on our analysis, we have identified critical import issues, missing modules, and structural problems that prevent the system from running properly.

## Task 1: Backend Error Resolution

### 1.1 Import Path Corrections
**Problem**: Multiple files have incorrect import paths due to code reorganization.

**Required Fixes**:
- Fix all `src.services.*` imports to point to correct locations in `src.core.*` or `src.infrastructure.*`
- Update QME template generator imports from `src.services.qme_template_generator` to `src.core.generation.qme_template_generator`
- Fix vector store imports from `src.services.vector_store` to `src.infrastructure.storage.vector_store`
- Correct file handler imports from `src.services.file_handler` to `src.infrastructure.storage.file_handler`
- Update health checker and performance monitor imports to use correct class names

**Files to Fix**:
- `src/ui/main_app.py`
- `src/ui/qa_interface.py` 
- `src/ui/qme_template_interface.py`
- `src/ui/professional_template_interface.py`
- `src/ui/document_manager.py`
- `src/startup.py`
- `src/app.py`
- All workflow and core service files

### 1.2 Missing Module Creation
**Problem**: Several modules exist in cache but not in source code.

**Required Actions**:
- Create placeholder implementations for missing services:
  - `src/services/comprehensive_qme_field_service.py`
  - `src/services/professional_template_assembler_simple.py`
  - Any other missing service modules identified during testing

### 1.3 Syntax and Structural Fixes
**Problem**: Multiple files have syntax errors, indentation issues, and broken class structures.

**Required Fixes**:
- Fix indentation errors in `src/infrastructure/monitoring/performance_monitor.py`
- Resolve class inheritance issues in `src/ui/qme_template_interface.py`
- Fix broken function definitions and method structures in `src/ui/qa_interface.py`
- Correct any remaining syntax errors preventing module imports

### 1.4 API Configuration Integration
**Problem**: OpenRouter API support is partially implemented.

**Required Actions**:
- Ensure `OpenRouterLLMStrategy` is properly integrated in QA strategy factory
- Verify both Gemini and OpenRouter API keys are correctly configured
- Test API provider switching functionality

## Task 2: Frontend-Backend Integration Completion

### 2.1 Main Application Entry Point
**Problem**: `src/ui/main_app.py` cannot be imported due to cascading import errors.

**Required Actions**:
- Ensure all UI component imports work correctly
- Fix any remaining import issues in UI modules
- Verify Streamlit application can start without errors
- Test basic navigation between pages

### 2.2 Core UI Components Integration
**Problem**: UI components have broken imports and missing dependencies.

**Required Actions**:
- Fix QA interface to work with current backend structure
- Ensure upload interface integrates with file handler
- Verify document management interface works with storage layer
- Test QME template interface with template generation services

### 2.3 Service Layer Integration
**Problem**: UI components cannot access backend services due to import issues.

**Required Actions**:
- Verify dependency injection container works correctly
- Ensure UI can create and use QA engines
- Test document processing pipeline integration
- Validate template generation workflow

### 2.4 Configuration and Environment Setup
**Problem**: Environment configuration may not be properly loaded in UI context.

**Required Actions**:
- Ensure `.env` file is properly loaded in UI context
- Verify API keys are accessible to UI components
- Test configuration validation in Streamlit environment
- Ensure database connections work from UI

## Success Criteria

### Task 1 Success Criteria:
1. ✅ All Python files can be imported without syntax or import errors
2. ✅ `python -c "from src.ui.main_app import main"` executes successfully
3. ✅ All backend services can be instantiated without errors
4. ✅ Both Gemini and OpenRouter API configurations work correctly
5. ✅ No missing module errors when running the application

### Task 2 Success Criteria:
1. ✅ Streamlit application starts without errors: `streamlit run src/ui/main_app.py`
2. ✅ All main navigation pages load successfully
3. ✅ File upload functionality works end-to-end
4. ✅ Document processing pipeline can be triggered from UI
5. ✅ QA functionality works with uploaded documents
6. ✅ Template generation can be initiated from UI
7. ✅ No runtime errors in browser console or Streamlit logs

## Implementation Approach

### Phase 1: Critical Import Fixes (30 minutes)
1. Run comprehensive import analysis
2. Fix all import path issues systematically
3. Create missing module placeholders
4. Verify basic import chain works

### Phase 2: Syntax and Structure Fixes (20 minutes)
1. Fix all syntax errors preventing imports
2. Resolve class structure issues
3. Fix indentation and formatting problems
4. Test individual module imports

### Phase 3: UI Integration Testing (20 minutes)
1. Test main application startup
2. Verify page navigation works
3. Test basic UI component functionality
4. Ensure no runtime errors

### Phase 4: End-to-End Validation (10 minutes)
1. Test complete document upload workflow
2. Verify QA functionality works
3. Test template generation if possible
4. Confirm system is production-ready

## Testing Strategy

### Automated Testing:
- Create comprehensive import test script
- Test all major UI workflows programmatically
- Validate API configuration and connectivity

### Manual Testing:
- Start Streamlit application and verify UI loads
- Test document upload and processing
- Verify QA interface functionality
- Test template generation workflow

## Deliverables

1. **Fixed Backend**: All import errors resolved, missing modules created
2. **Working UI**: Streamlit application starts and runs without errors
3. **Integration Validation**: End-to-end workflows function correctly
4. **Test Suite**: Comprehensive tests to prevent regression
5. **Documentation**: Updated setup and troubleshooting guide

## Timeline
- **Total Estimated Time**: 80 minutes
- **Priority**: Critical (blocks all other development)
- **Dependencies**: None (foundational work)

This spec focuses exclusively on getting the system to a working state where developers can run the application locally and all major components integrate correctly.