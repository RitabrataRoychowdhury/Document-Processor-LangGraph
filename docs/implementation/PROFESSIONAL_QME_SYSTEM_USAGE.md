# Professional QME Template Assembly System - Usage Guide

## 🏥 Complete System Overview

The Professional QME Template Assembly System is now fully integrated with the existing Document Q&A System, providing a comprehensive solution for medical document processing and professional QME report generation.

## 🚀 Quick Start

### Option 1: Complete Web Interface (Recommended)

```bash
# Run the complete system with web interface
./scripts/run.sh
```

Or use the dedicated runner:

```bash
# Run the professional QME system
python run_professional_qme_system.py
```

This will start the Streamlit web interface at `http://localhost:8501` with all features:

- **Document Q&A System**: Upload and query medical documents
- **QME Template Generator**: Generate basic QME templates
- **Professional Template Assembly**: Create gold-standard compliant templates
- **Knowledge Base Management**: Manage canonical medical documents

### Option 2: Direct Demo

```bash
# Run the Professional Template Assembly demo
python examples/professional_template_assembler_demo.py
```

## 📋 System Features

### 1. Document Processing & Q&A
- Upload medical documents (PDF, DOCX, TXT)
- Intelligent question answering using AI
- Knowledge graph population with medical entities
- Document management and organization

### 2. QME Template Generation
- Extract patient information from medical documents
- Generate basic QME templates with medical findings
- Template customization and formatting options
- Integration with existing medical knowledge base

### 3. Professional Template Assembly ⭐ **NEW**
- **Gold Standard Compliance**: Exact formatting from AI Example QME Report Template.docx
- **Comprehensive Validation**: Pre and post-assembly quality checks
- **Professional DOCX Generation**: High-quality medical formatting
- **Quality Assurance Pipeline**: Detailed quality reports and compliance checking
- **Missing Information Detection**: Automatic placeholder management
- **Download Packages**: Complete packages with quality reports

## 🎯 Workflow Integration

### Complete QME Report Generation Workflow

1. **Document Upload** → Upload patient medical records
2. **Document Processing** → AI extraction and knowledge graph population
3. **QME Template Generation** → Generate basic template with extracted data
4. **Professional Assembly** ⭐ → Upgrade to gold-standard compliant template
5. **Quality Validation** → Comprehensive quality assurance and compliance checking
6. **Professional Download** → Download complete package with quality reports

### Navigation Between Systems

The systems are fully integrated with seamless navigation:

- **From Document Q&A** → Generate QME templates from processed documents
- **From QME Template Generator** → Upgrade to Professional Template Assembly
- **From Professional Assembly** → Access quality validation and compliance reports

## 🔧 Configuration

### Environment Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys** (create `.env` file):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here  # Optional alternative
   ```

3. **Initialize Knowledge Base** (optional but recommended):
   ```bash
   # Place canonical documents in project root:
   # - AMAGuides 5th Edition.pdf
   # - QME-Study-Guide.pdf
   # - Sample3.pdf
   
   # Then run initialization
   ./scripts/run.sh
   # Choose option 6: Initialize knowledge base
   ```

### Professional Template Assembly Configuration

The Professional Template Assembly System uses the following configuration:

```python
# Default Assembly Configuration
TemplateAssemblyConfig(
    include_quality_indicators=False,      # Draft mode indicators
    include_missing_placeholders=True,     # Highlight missing info
    apply_professional_formatting=True,    # Gold standard formatting
    validate_before_assembly=True,         # Pre-assembly validation
    validate_after_assembly=True,          # Post-assembly validation
    generate_quality_report=True,          # Detailed quality report
    output_format="docx",                  # Output format
    template_version="1.0"                 # Version tracking
)
```

## 📊 Quality Assurance Features

### Validation System
- **Pre-Assembly Validation**: Validates template data completeness
- **Post-Assembly Validation**: Validates document structure and formatting
- **Quality Scoring**: Completeness, accuracy, and compliance scores (0-100)
- **Issue Classification**: Critical, High, Medium, Low severity levels

### Compliance Checking
- **Gold Standard Compliance**: Based on AI Example QME Report Template.docx
- **AMA Guidelines Compliance**: Validates against AMA Guides 5th Edition
- **Legal Requirements**: Ensures compliance with QME regulations
- **Missing Information Detection**: Automatic identification and highlighting

### Quality Reports
- **Comprehensive Analysis**: Detailed quality assessment with improvement suggestions
- **Validation History**: Complete audit trail of validation results
- **Compliance Status**: Clear compliance determination (Compliant/Needs Review/Non-Compliant)
- **Actionable Recommendations**: Specific suggestions for improvement

## 🎨 Template Features

### Gold Standard Formatting
- **Professional Typography**: Times New Roman, proper spacing, medical formatting
- **Document Structure**: Headers, footers, signature blocks, confidentiality notices
- **Medical Tables**: Range of Motion tables, neurological examination tables
- **Section Organization**: Exact order and structure from gold standard template

### Content Sections
1. **Patient Identification** - Demographics and case information
2. **History Sections** - Injury history, job description, current condition
3. **Physical Examination** - General appearance, vitals, spine examination
4. **Neurological Examination** - Sensory, motor, reflexes testing
5. **Diagnostic Studies** - Imaging and laboratory results
6. **Diagnosis** - Primary/secondary diagnoses with ICD-10 codes
7. **Impairment Rating** - AMA Guides-based ratings with references
8. **Work Restrictions** - Specific limitations and capacity assessments
9. **Future Medical Care** - Treatment recommendations and prognosis
10. **Causation Analysis** - Medical causation with probability statements
11. **Apportionment** - Industrial vs non-industrial factor analysis
12. **Professional Signature** - Doctor credentials and signature block

## 📥 Download Options

### Template Downloads
- **Professional DOCX**: High-quality template with gold standard formatting
- **Quality Report**: Detailed quality assessment and validation results
- **Complete Package**: ZIP file with template, quality report, and validation summary

### Package Contents
- `QME_Report_[Patient]_[Date].docx` - Main professional template
- `QME_Report_[Patient]_[Date]_quality_report.txt` - Quality assessment
- `validation_summary.txt` - Validation results summary
- `package_info.txt` - Package information and contents

## 🧪 Testing & Demos

### Available Demos

1. **Professional Template Assembly Demo**:
   ```bash
   python examples/professional_template_assembler_demo.py
   ```
   - Basic assembly demonstration
   - Draft mode with quality indicators
   - Download package creation
   - Validation analysis

2. **QME Template Generator Demo**:
   ```bash
   python examples/qme_template_demo.py
   ```

3. **Document Q&A Demo**:
   ```bash
   python examples/hybrid_qa_demo.py
   ```

### Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_professional_template_assembler.py -v
python -m pytest tests/test_qme_template_generator.py -v
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure you're in the project root and virtual environment is activated
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

2. **API Key Issues**:
   ```bash
   # Check .env file exists and has valid API keys
   cat .env
   # Should contain: GEMINI_API_KEY=your_key_here
   ```

3. **Template Generation Errors**:
   - Ensure patient documents contain medical information
   - Check that required fields are present (patient name, case number, etc.)
   - Review validation messages for specific issues

4. **Professional Assembly Issues**:
   - Verify template data is available from QME Template Generator
   - Check system health status in the web interface
   - Review quality validation results for specific problems

### Health Checks

```bash
# Run comprehensive health checks
./scripts/run.sh
# Choose option 3: Run health checks only
```

### Performance Monitoring

The system includes built-in performance monitoring:
- Document processing times
- Template generation metrics
- Quality validation performance
- System resource usage

## 📚 Documentation

### Key Files
- `PROFESSIONAL_TEMPLATE_ASSEMBLER_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `QME_TEMPLATE_IMPLEMENTATION_SUMMARY.md` - QME template system overview
- `docs/` - Additional documentation and guides
- `examples/` - Demo scripts and usage examples

### API Documentation
- `src/services/professional_template_assembler.py` - Main assembly service
- `src/ui/professional_template_interface.py` - Web interface
- `src/services/qme_template_generator.py` - Template generation
- `src/services/qme_rules_engine.py` - Validation and quality assurance

## 🎉 Getting Started

1. **Clone and Setup**:
   ```bash
   git clone [repository]
   cd [project-directory]
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the System**:
   ```bash
   # Option 1: Use the dedicated runner
   python run_professional_qme_system.py
   
   # Option 2: Use the main run script
   ./scripts/run.sh
   
   # Option 3: Direct Streamlit
   streamlit run src/ui/main_app.py
   ```

4. **Access the Web Interface**:
   - Open `http://localhost:8501` in your browser
   - Navigate to "Professional Template Assembly" for the new features
   - Upload medical documents and generate professional QME templates

## 🚀 Next Steps

The Professional QME Template Assembly System is ready for production use with:

- ✅ Complete integration with existing Document Q&A System
- ✅ Gold standard compliance and professional formatting
- ✅ Comprehensive validation and quality assurance
- ✅ Seamless web interface and user experience
- ✅ Professional download packages and quality reports

Start generating professional, compliant QME templates today!