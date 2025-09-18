---
inclusion: always
---

# Root Project Files

## Purpose
Essential project configuration, documentation, and entry point files at the project root level.

## Application Entry Points
- **`main.py`**: Primary application entry point with CLI interface and web server startup
- **`run_direct.py`**: Direct application runner bypassing shell scripts (recommended for development)
- **`run_fixed.sh`**: Fixed shell script runner with proper dependency management

## Configuration Files
- **`.env`**: Environment variables for local development (not in version control)
- **`.env.example`**: Template for environment variables with example values
- **`pyproject.toml`**: Modern Python project configuration with build system and dependencies
- **`requirements.txt`**: Python package dependencies for pip installation
- **`setup.cfg`**: Legacy Python package configuration and tool settings

## Docker Configuration
- **`Dockerfile`**: Docker container definition for application deployment
- **`docker-compose.yml`**: Docker Compose orchestration for multi-container deployment
- **`.dockerignore`**: Files and directories to exclude from Docker build context

## Development Tools
- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration for code quality
- **`.gitignore`**: Git ignore patterns (implied, standard for Python projects)

## Documentation Files
- **`README.md`**: Primary project documentation with setup and usage instructions
- **`BYPASS_RUN_SCRIPT_SOLUTION.md`**: Solution documentation for script execution issues
- **`COMPLETE_EXTRACTION_PIPELINE_SOLUTION.md`**: Complete extraction pipeline implementation guide
- **`EXTRACTION_PIPELINE_FIX_SUMMARY.md`**: Summary of extraction pipeline fixes
- **`FINAL_EXTRACTION_FIX_INSTRUCTIONS.md`**: Final instructions for extraction fixes

## File Purposes and Usage

### Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

### Application Startup
```bash
# Recommended: Direct Python execution
python run_direct.py

# Alternative: Fixed shell script
./run_fixed.sh

# Main entry point with options
python main.py --web
python main.py --check
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Build Docker image
docker build -t qme-system .

# Run container
docker run -p 8501:8501 qme-system
```

## Configuration Hierarchy
1. **Environment Variables**: Highest priority (production secrets)
2. **`.env` File**: Local development configuration
3. **Default Values**: Fallback values in application code

## Security Considerations
- **`.env` File**: Never commit to version control (contains secrets)
- **API Keys**: Store in environment variables, not in code
- **Docker Secrets**: Use Docker secrets for production deployments
- **File Permissions**: Restrict access to configuration files

## Development Workflow
1. **Setup**: Copy `.env.example` to `.env` and configure
2. **Dependencies**: Install with `pip install -r requirements.txt`
3. **Development**: Use `python run_direct.py` for testing
4. **Production**: Use Docker Compose for deployment

## File Maintenance
- **Dependencies**: Keep `requirements.txt` and `pyproject.toml` synchronized
- **Documentation**: Update README.md with new features and changes
- **Docker**: Update Dockerfile and docker-compose.yml for new dependencies
- **Environment**: Update `.env.example` with new configuration options

## Best Practices
- **Version Pinning**: Pin dependency versions in requirements.txt
- **Documentation**: Keep README.md current and comprehensive
- **Configuration**: Use environment variables for all configurable values
- **Security**: Regular security updates for dependencies
- **Testing**: Validate all entry points and configuration options