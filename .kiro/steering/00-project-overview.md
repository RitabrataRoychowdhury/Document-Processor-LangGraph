---
inclusion: always
---

# QME System - Project Overview

## Project Purpose
This is a Production-Ready QME (Qualified Medical Evaluator) System designed to automate the generation of compliant medical evaluation reports for California Workers' Compensation cases. The system implements evidence-first workflows with dual-pipeline architecture for document processing and template generation.

## Core Architecture
- **Evidence-First Approach**: All content generation is based on extracted evidence with confidence scoring
- **Dual-Pipeline Architecture**: 
  - Pipeline 1: Document ingestion → extraction → validation → knowledge graph population
  - Pipeline 2: Validated evidence → content generation → template assembly → compliance validation
- **Service-Oriented Design**: Modular services with dependency injection and loose coupling
- **Production Infrastructure**: Comprehensive monitoring, error handling, and deployment capabilities

## Key Technologies
- **Backend**: Python 3.13, FastAPI, SQLAlchemy, Streamlit
- **AI/ML**: OpenRouter API, Gemini API, OpenAI API, spaCy NLP
- **Storage**: SQLite (development), PostgreSQL (production), Vector databases
- **Infrastructure**: Docker, Docker Compose, comprehensive logging and monitoring

## Development Standards
- **Code Quality**: Type hints, docstrings, comprehensive error handling
- **Testing**: Unit, integration, end-to-end, and performance testing
- **Documentation**: Inline documentation, API specs, implementation summaries
- **Security**: Secure API key management, input validation, audit trails

## Compliance Requirements
- **AMA Guidelines 5th Edition**: Programmatic calculations with zero LLM involvement
- **California Labor Code 4062.3**: Legal compliance declarations and mandatory sections
- **Evidence-Based**: All content must be traceable to source documents with confidence scores
- **Professional Standards**: Gold-standard formatting and quality assurance