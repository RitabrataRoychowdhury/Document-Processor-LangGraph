#!/usr/bin/env python3
"""
Comprehensive System Validation Script

This script performs comprehensive validation of the QME system including:
- Import statement validation
- Backend service instantiation testing
- UI functionality testing
- API provider validation
- Configuration validation
- Database connectivity testing
- Performance benchmarking
"""

import sys
import os
import asyncio
import importlib
import traceback
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Core validation imports
from src.utils.logging_config import get_logger
from src.utils.error_handling import DocumentQAError, format_error_for_ui

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    success: bool
    message: str
    details: Dict[str, Any]
    duration: float
    error: Optional[str] = None


@dataclass
class SystemValidationReport:
    """Comprehensive system validation report."""
    timestamp: str
    overall_success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration: float
    test_results: List[ValidationResult]
    system_info: Dict[str, Any]
    recommendations: List[str]


class ComprehensiveSystemValidator:
    """
    Comprehensive system validator that tests all aspects of the QME system.
    """
    
    def __init__(self):
        """Initialize the system validator."""
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
    def run_validation(self) -> SystemValidationReport:
        """Run comprehensive system validation."""
        logger.info("Starting comprehensive system validation")
        
        # Test categories
        test_categories = [
            ("Import Validation", self._test_imports),
            ("Configuration Validation", self._test_configuration),
            ("Database Connectivity", self._test_database),
            ("Service Instantiation", self._test_service_instantiation),
            ("API Provider Validation", self._test_api_providers),
            ("UI Component Testing", self._test_ui_components),
            ("Workflow Integration", self._test_workflow_integration),
            ("Performance Benchmarks", self._test_performance)
        ]
        
        # Run all test categories
        for category_name, test_func in test_categories:
            logger.info(f"Running {category_name} tests")
            try:
                test_func()
            except Exception as e:
                logger.error(f"Error in {category_name}: {e}", exc_info=True)
                self._add_result(
                    test_name=f"{category_name} - Critical Error",
                    success=False,
                    message=f"Critical error in {category_name}",
                    details={"error": str(e), "traceback": traceback.format_exc()},
                    duration=0.0,
                    error=str(e)
                )
        
        # Generate report
        return self._generate_report()
    
    def _add_result(self, test_name: str, success: bool, message: str, 
                   details: Dict[str, Any], duration: float, error: Optional[str] = None):
        """Add a test result."""
        result = ValidationResult(
            test_name=test_name,
            success=success,
            message=message,
            details=details,
            duration=duration,
            error=error
        )
        self.results.append(result)
        
        # Log result
        if success:
            logger.info(f"✅ {test_name}: {message}")
        else:
            logger.error(f"❌ {test_name}: {message}")
    
    def _test_imports(self):
        """Test all critical import statements."""
        critical_imports = [
            # Core modules
            "src.app",
            "src.startup",
            "src.config.app_config",
            
            # UI modules
            "src.ui.main_app",
            "src.ui.upload_interface",
            "src.ui.qa_interface_simple",
            "src.ui.document_manager",
            "src.ui.qme_template_interface",
            "src.ui.professional_template_interface",
            
            # Service modules
            "src.services.comprehensive_qme_field_service",
            "src.services.professional_template_assembler_simple",
            
            # Infrastructure modules
            "src.infrastructure.configuration.service_registry",
            "src.infrastructure.configuration.centralized_config_manager",
            "src.infrastructure.api.api_provider_factory",
            "src.infrastructure.monitoring.performance_monitor",
            "src.infrastructure.monitoring.ui_error_handler",
            
            # Core processing modules
            "src.core.interfaces",
            "src.models.document",
            "src.models.extraction_models",
            
            # Storage modules
            "src.storage.database",
            "src.storage.document_storage",
            
            # Utility modules
            "src.utils.error_handling",
            "src.utils.logging_config"
        ]
        
        for module_name in critical_imports:
            start_time = time.time()
            try:
                importlib.import_module(module_name)
                duration = time.time() - start_time
                self._add_result(
                    test_name=f"Import: {module_name}",
                    success=True,
                    message="Import successful",
                    details={"module": module_name, "import_time": duration},
                    duration=duration
                )
            except Exception as e:
                duration = time.time() - start_time
                self._add_result(
                    test_name=f"Import: {module_name}",
                    success=False,
                    message=f"Import failed: {str(e)}",
                    details={"module": module_name, "error": str(e)},
                    duration=duration,
                    error=str(e)
                )
    
    def _test_configuration(self):
        """Test configuration loading and validation."""
        start_time = time.time()
        
        try:
            from src.config.app_config import app_config
            
            # Test basic configuration access
            config_tests = [
                ("database_path", lambda: app_config.database_path),
                ("max_file_size_mb", lambda: app_config.max_file_size_mb),
                ("allowed_file_types", lambda: app_config.allowed_file_types),
                ("gemini_api_key", lambda: app_config.gemini_api_key),
                ("openai_api_key", lambda: app_config.openai_api_key)
            ]
            
            config_details = {}
            for config_name, config_getter in config_tests:
                try:
                    value = config_getter()
                    config_details[config_name] = "configured" if value else "not_configured"
                except Exception as e:
                    config_details[config_name] = f"error: {str(e)}"
            
            duration = time.time() - start_time
            self._add_result(
                test_name="Configuration Loading",
                success=True,
                message="Configuration loaded successfully",
                details=config_details,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_result(
                test_name="Configuration Loading",
                success=False,
                message=f"Configuration loading failed: {str(e)}",
                details={"error": str(e)},
                duration=duration,
                error=str(e)
            )
    
    def _test_database(self):
        """Test database connectivity and basic operations."""
        start_time = time.time()
        
        try:
            from src.storage.database import DatabaseManager
            
            # Test database initialization
            db_manager = DatabaseManager()
            
            # Test basic database operations
            test_operations = []
            
            # Test connection
            try:
                conn = db_manager.get_connection()
                conn.close()
                test_operations.append(("connection", True, "Database connection successful"))
            except Exception as e:
                test_operations.append(("connection", False, f"Database connection failed: {str(e)}"))
            
            # Test basic query
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    test_operations.append(("query", True, f"Database query successful, found {len(tables)} tables"))
            except Exception as e:
                test_operations.append(("query", False, f"Database query failed: {str(e)}"))
            
            duration = time.time() - start_time
            overall_success = all(op[1] for op in test_operations)
            
            self._add_result(
                test_name="Database Connectivity",
                success=overall_success,
                message="Database tests completed" if overall_success else "Database tests failed",
                details={"operations": test_operations},
                duration=duration,
                error=None if overall_success else "Database connectivity issues"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_result(
                test_name="Database Connectivity",
                success=False,
                message=f"Database testing failed: {str(e)}",
                details={"error": str(e)},
                duration=duration,
                error=str(e)
            )
    
    def _test_service_instantiation(self):
        """Test instantiation of all backend services."""
        services_to_test = [
            ("SystemStartup", "src.startup", "SystemStartup"),
            ("ServiceRegistry", "src.infrastructure.configuration.service_registry", "ServiceRegistry"),
            ("ConfigManager", "src.infrastructure.configuration.centralized_config_manager", "CentralizedConfigManager"),
            ("APIProviderFactory", "src.infrastructure.api.api_provider_factory", "APIProviderFactory"),
            ("PerformanceMonitor", "src.infrastructure.monitoring.performance_monitor", "AdvancedPerformanceMonitor"),
            ("QMEFieldService", "src.services.comprehensive_qme_field_service", "ComprehensiveQMEFieldService"),
            ("TemplateAssembler", "src.services.professional_template_assembler_simple", "ProfessionalTemplateAssembler")
        ]
        
        for service_name, module_name, class_name in services_to_test:
            start_time = time.time()
            try:
                module = importlib.import_module(module_name)
                service_class = getattr(module, class_name)
                
                # Try to instantiate the service
                if service_name == "SystemStartup":
                    service_instance = service_class()
                elif service_name in ["QMEFieldService", "TemplateAssembler"]:
                    # These services might need configuration
                    try:
                        service_instance = service_class()
                    except Exception:
                        # Try with None config
                        service_instance = service_class(config=None)
                else:
                    service_instance = service_class()
                
                duration = time.time() - start_time
                self._add_result(
                    test_name=f"Service: {service_name}",
                    success=True,
                    message="Service instantiated successfully",
                    details={
                        "service": service_name,
                        "module": module_name,
                        "class": class_name,
                        "instance_type": str(type(service_instance))
                    },
                    duration=duration
                )
                
            except Exception as e:
                duration = time.time() - start_time
                self._add_result(
                    test_name=f"Service: {service_name}",
                    success=False,
                    message=f"Service instantiation failed: {str(e)}",
                    details={
                        "service": service_name,
                        "module": module_name,
                        "class": class_name,
                        "error": str(e)
                    },
                    duration=duration,
                    error=str(e)
                )
    
    def _test_api_providers(self):
        """Test API provider functionality."""
        start_time = time.time()
        
        try:
            from src.infrastructure.api.api_provider_factory import APIProviderFactory
            
            factory = APIProviderFactory()
            
            # Test available providers
            providers_tested = []
            
            # Test Gemini provider
            try:
                gemini_provider = factory.create_gemini_provider()
                providers_tested.append(("Gemini", True, "Provider created successfully"))
            except Exception as e:
                providers_tested.append(("Gemini", False, f"Provider creation failed: {str(e)}"))
            
            # Test OpenRouter provider
            try:
                openrouter_provider = factory.create_openrouter_provider()
                providers_tested.append(("OpenRouter", True, "Provider created successfully"))
            except Exception as e:
                providers_tested.append(("OpenRouter", False, f"Provider creation failed: {str(e)}"))
            
            # Test fallback mechanism
            try:
                primary_provider = factory.get_primary_provider()
                providers_tested.append(("Primary Provider", True, "Primary provider available"))
            except Exception as e:
                providers_tested.append(("Primary Provider", False, f"Primary provider failed: {str(e)}"))
            
            try:
                fallback_provider = factory.get_fallback_provider()
                providers_tested.append(("Fallback Provider", True, "Fallback provider available"))
            except Exception as e:
                providers_tested.append(("Fallback Provider", False, f"Fallback provider failed: {str(e)}"))
            
            duration = time.time() - start_time
            overall_success = any(p[1] for p in providers_tested)  # At least one provider should work
            
            self._add_result(
                test_name="API Providers",
                success=overall_success,
                message="API provider testing completed",
                details={"providers": providers_tested},
                duration=duration,
                error=None if overall_success else "No API providers available"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_result(
                test_name="API Providers",
                success=False,
                message=f"API provider testing failed: {str(e)}",
                details={"error": str(e)},
                duration=duration,
                error=str(e)
            )
    
    def _test_ui_components(self):
        """Test UI component loading."""
        ui_components = [
            ("MainApp", "src.ui.main_app", "main"),
            ("UploadInterface", "src.ui.upload_interface", "UploadInterface"),
            ("QAInterface", "src.ui.qa_interface_simple", "render_qa_page"),
            ("DocumentManager", "src.ui.document_manager", "render_document_management_page"),
            ("QMETemplateInterface", "src.ui.qme_template_interface", "render_qme_template_page"),
            ("ProfessionalTemplateInterface", "src.ui.professional_template_interface", "ProfessionalTemplateInterface")
        ]
        
        for component_name, module_name, function_or_class in ui_components:
            start_time = time.time()
            try:
                module = importlib.import_module(module_name)
                component = getattr(module, function_or_class)
                
                duration = time.time() - start_time
                self._add_result(
                    test_name=f"UI Component: {component_name}",
                    success=True,
                    message="UI component loaded successfully",
                    details={
                        "component": component_name,
                        "module": module_name,
                        "type": str(type(component))
                    },
                    duration=duration
                )
                
            except Exception as e:
                duration = time.time() - start_time
                self._add_result(
                    test_name=f"UI Component: {component_name}",
                    success=False,
                    message=f"UI component loading failed: {str(e)}",
                    details={
                        "component": component_name,
                        "module": module_name,
                        "error": str(e)
                    },
                    duration=duration,
                    error=str(e)
                )
    
    def _test_workflow_integration(self):
        """Test workflow integration and system startup."""
        start_time = time.time()
        
        try:
            from src.startup import SystemStartup
            
            # Test system startup
            startup = SystemStartup()
            
            # Test async startup process
            async def test_startup():
                return await startup.startup()
            
            startup_success = asyncio.run(test_startup())
            
            duration = time.time() - start_time
            self._add_result(
                test_name="System Startup",
                success=startup_success,
                message="System startup completed" if startup_success else "System startup failed",
                details={
                    "startup_success": startup_success,
                    "config_loaded": hasattr(startup, 'config'),
                    "services_initialized": startup_success
                },
                duration=duration,
                error=None if startup_success else "System startup failed"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_result(
                test_name="System Startup",
                success=False,
                message=f"System startup testing failed: {str(e)}",
                details={"error": str(e)},
                duration=duration,
                error=str(e)
            )
    
    def _test_performance(self):
        """Test basic performance benchmarks."""
        start_time = time.time()
        
        try:
            # Test import performance
            import_start = time.time()
            from src.app import get_app
            import_duration = time.time() - import_start
            
            # Test app initialization performance
            init_start = time.time()
            try:
                app = get_app()
                init_duration = time.time() - init_start
                init_success = True
            except Exception as e:
                init_duration = time.time() - init_start
                init_success = False
            
            duration = time.time() - start_time
            self._add_result(
                test_name="Performance Benchmarks",
                success=True,
                message="Performance benchmarks completed",
                details={
                    "import_time": import_duration,
                    "init_time": init_duration,
                    "init_success": init_success,
                    "total_time": duration
                },
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_result(
                test_name="Performance Benchmarks",
                success=False,
                message=f"Performance testing failed: {str(e)}",
                details={"error": str(e)},
                duration=duration,
                error=str(e)
            )
    
    def _generate_report(self) -> SystemValidationReport:
        """Generate comprehensive validation report."""
        total_duration = time.time() - self.start_time
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = len(self.results) - passed_tests
        overall_success = failed_tests == 0
        
        # Generate recommendations based on failures
        recommendations = []
        
        # Check for common failure patterns
        import_failures = [r for r in self.results if "Import:" in r.test_name and not r.success]
        if import_failures:
            recommendations.append("Fix import errors by checking module paths and dependencies")
        
        service_failures = [r for r in self.results if "Service:" in r.test_name and not r.success]
        if service_failures:
            recommendations.append("Review service configurations and dependencies")
        
        api_failures = [r for r in self.results if "API" in r.test_name and not r.success]
        if api_failures:
            recommendations.append("Check API key configuration and network connectivity")
        
        db_failures = [r for r in self.results if "Database" in r.test_name and not r.success]
        if db_failures:
            recommendations.append("Verify database configuration and file permissions")
        
        if not recommendations:
            recommendations.append("System validation completed successfully - no issues found")
        
        # Collect system information
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "validation_timestamp": datetime.now().isoformat(),
            "total_modules_tested": len([r for r in self.results if "Import:" in r.test_name]),
            "total_services_tested": len([r for r in self.results if "Service:" in r.test_name])
        }
        
        return SystemValidationReport(
            timestamp=datetime.now().isoformat(),
            overall_success=overall_success,
            total_tests=len(self.results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_duration=total_duration,
            test_results=self.results,
            system_info=system_info,
            recommendations=recommendations
        )


def main():
    """Run comprehensive system validation."""
    print("🔍 Starting Comprehensive System Validation")
    print("=" * 60)
    
    validator = ComprehensiveSystemValidator()
    report = validator.run_validation()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    status_icon = "✅" if report.overall_success else "❌"
    print(f"{status_icon} Overall Status: {'PASSED' if report.overall_success else 'FAILED'}")
    print(f"📈 Tests Passed: {report.passed_tests}/{report.total_tests}")
    print(f"⏱️  Total Duration: {report.total_duration:.2f}s")
    
    if report.failed_tests > 0:
        print(f"\n❌ Failed Tests ({report.failed_tests}):")
        for result in report.test_results:
            if not result.success:
                print(f"  • {result.test_name}: {result.message}")
    
    print(f"\n💡 Recommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")
    
    # Save detailed report
    report_path = Path("results/validation_reports/comprehensive_system_validation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(asdict(report), f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if report.overall_success else 1)


if __name__ == "__main__":
    main()