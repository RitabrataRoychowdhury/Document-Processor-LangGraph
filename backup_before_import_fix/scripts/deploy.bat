@echo off
REM Deployment script for Document Q&A System (Windows)
REM This script sets up the SQLite database, initializes canonical documents,
REM and starts the Streamlit interface

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set VENV_PATH=%PROJECT_ROOT%\venv
set DATABASE_PATH=%PROJECT_ROOT%\data\database\documents.db
set LOG_DIR=%PROJECT_ROOT%\logs

REM Function to print colored output (Windows doesn't support colors easily, so just use prefixes)
set INFO_PREFIX=[INFO]
set SUCCESS_PREFIX=[SUCCESS]
set WARNING_PREFIX=[WARNING]
set ERROR_PREFIX=[ERROR]

echo %INFO_PREFIX% Starting Document Q&A System deployment...

REM Check Python version
echo %INFO_PREFIX% Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %SUCCESS_PREFIX% Python version: %PYTHON_VERSION%

REM Setup virtual environment
echo %INFO_PREFIX% Setting up virtual environment...
if not exist "%VENV_PATH%" (
    echo %INFO_PREFIX% Creating virtual environment at %VENV_PATH%
    python -m venv "%VENV_PATH%"
) else (
    echo %INFO_PREFIX% Virtual environment already exists
)

REM Activate virtual environment
call "%VENV_PATH%\Scripts\activate.bat"

REM Upgrade pip
echo %INFO_PREFIX% Upgrading pip...
python -m pip install --upgrade pip

echo %SUCCESS_PREFIX% Virtual environment ready

REM Install dependencies
echo %INFO_PREFIX% Installing dependencies...
if exist "%PROJECT_ROOT%\requirements.txt" (
    pip install -r "%PROJECT_ROOT%\requirements.txt"
    echo %SUCCESS_PREFIX% Dependencies installed
) else (
    echo %ERROR_PREFIX% requirements.txt not found
    exit /b 1
)

REM Create necessary directories
echo %INFO_PREFIX% Creating necessary directories...
if not exist "%PROJECT_ROOT%\data" mkdir "%PROJECT_ROOT%\data"
if not exist "%PROJECT_ROOT%\data\database" mkdir "%PROJECT_ROOT%\data\database"
if not exist "%PROJECT_ROOT%\data\documents" mkdir "%PROJECT_ROOT%\data\documents"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo %SUCCESS_PREFIX% Directories created

REM Validate environment configuration
echo %INFO_PREFIX% Validating environment configuration...
if not exist "%PROJECT_ROOT%\.env" (
    if exist "%PROJECT_ROOT%\.env.example" (
        echo %WARNING_PREFIX% .env file not found. Copying from .env.example
        copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env"
        echo %WARNING_PREFIX% Please edit .env file with your API keys before continuing
    ) else (
        echo %WARNING_PREFIX% .env file not found and no .env.example available
    )
)

REM Check for canonical documents
set MISSING_DOCS=0
if not exist "%PROJECT_ROOT%\AMAGuides 5th Edition.pdf" (
    echo %WARNING_PREFIX% Missing: AMAGuides 5th Edition.pdf
    set MISSING_DOCS=1
)
if not exist "%PROJECT_ROOT%\QME-Study-Guide.pdf" (
    echo %WARNING_PREFIX% Missing: QME-Study-Guide.pdf
    set MISSING_DOCS=1
)
if not exist "%PROJECT_ROOT%\Sample3.pdf" (
    echo %WARNING_PREFIX% Missing: Sample3.pdf
    set MISSING_DOCS=1
)

if %MISSING_DOCS%==1 (
    echo %WARNING_PREFIX% System will start without missing canonical documents
) else (
    echo %SUCCESS_PREFIX% All canonical documents found
)

REM Initialize database
echo %INFO_PREFIX% Initializing SQLite database...
cd /d "%PROJECT_ROOT%"
python -c "import sys; sys.path.append('%PROJECT_ROOT%'); from src.storage.database import DatabaseManager; from src.config.app_config import AppConfig; config = AppConfig.from_env(); db_manager = DatabaseManager(config.database_path); db_manager.initialize_database(); print('Database initialized successfully')"
echo %SUCCESS_PREFIX% Database initialized

REM Run health checks
echo %INFO_PREFIX% Running system health checks...
python -c "import sys; import asyncio; sys.path.append('%PROJECT_ROOT%'); from src.services.health_checker import HealthChecker; from src.config.app_config import AppConfig; async def main(): config = AppConfig.from_env(); health_checker = HealthChecker(config); health = health_checker.get_overall_health(); print(f'Overall Health: {\"HEALTHY\" if health[\"overall_healthy\"] else \"UNHEALTHY\"}'); print(f'Healthy Components: {health[\"healthy_components\"]}/{health[\"total_components\"]}'); [print(f'  {component}: {\"PASS\" if status[\"healthy\"] else \"FAIL\"} - {status[\"message\"]}') for component, status in health['checks'].items()]; return health['overall_healthy']; result = asyncio.run(main())"
echo %SUCCESS_PREFIX% Health checks completed

REM Initialize knowledge base
echo %INFO_PREFIX% Initializing knowledge base with canonical documents...
python -c "import sys; import asyncio; sys.path.append('%PROJECT_ROOT%'); from src.services.knowledge_base_initializer import initialize_system_startup; from src.services.ingestion_pipeline import IngestionPipeline; from src.config.app_config import AppConfig; from src.config.dependency_injection import DependencyContainer; async def main(): config = AppConfig.from_env(); container = DependencyContainer(config); pipeline = container.get_ingestion_pipeline(); result = await initialize_system_startup(config, pipeline); print(f'Initialization Result: {\"SUCCESS\" if result.success else \"FAILED\"}'); print(f'Processed Documents: {len(result.processed_documents)}'); print(f'Failed Documents: {len(result.failed_documents)}'); print(f'Total Time: {result.total_processing_time:.2f}s'); return result.success; result = asyncio.run(main()); print('Knowledge base initialization completed')"
echo %SUCCESS_PREFIX% Knowledge base initialization completed

REM Start Streamlit application
echo %INFO_PREFIX% Starting Streamlit application...
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%
echo %SUCCESS_PREFIX% Starting Streamlit on http://localhost:8501
echo %INFO_PREFIX% Press Ctrl+C to stop the application
streamlit run src\ui\main_app.py --server.port=8501 --server.address=localhost

pause