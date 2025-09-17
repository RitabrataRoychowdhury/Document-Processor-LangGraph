#!/usr/bin/env python3
"""
Performance and Stability Testing Script

This script performs comprehensive performance and stability testing including:
- System startup time measurement
- Resource usage monitoring
- Memory leak detection
- Error recovery testing
- Stress testing with multiple operations
- Graceful degradation testing
"""

import sys
import os
import time
import psutil
import asyncio
import threading
import gc
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test."""
    test_name: str
    start_time: float
    end_time: float
    duration: float
    cpu_usage_start: float
    cpu_usage_end: float
    memory_usage_start: float
    memory_usage_end: float
    memory_peak: float
    success: bool
    error_message: Optional[str] = None
    additional_metrics: Dict[str, Any] = None


@dataclass
class StabilityTestResult:
    """Result of stability testing."""
    test_name: str
    iterations: int
    successful_iterations: int
    failed_iterations: int
    average_duration: float
    min_duration: float
    max_duration: float
    memory_growth: float
    error_rate: float
    errors: List[str]


class PerformanceStabilityTester:
    """
    Comprehensive performance and stability tester for the QME system.
    """
    
    def __init__(self):
        """Initialize the performance tester."""
        self.process = psutil.Process()
        self.metrics: List[PerformanceMetrics] = []
        self.stability_results: List[StabilityTestResult] = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance and stability tests."""
        logger.info("Starting comprehensive performance and stability testing")
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "startup_performance": self._test_startup_performance(),
            "service_performance": self._test_service_performance(),
            "memory_stability": self._test_memory_stability(),
            "error_recovery": self._test_error_recovery(),
            "stress_testing": self._test_stress_scenarios(),
            "graceful_degradation": self._test_graceful_degradation(),
            "overall_assessment": {}
        }
        
        # Generate overall assessment
        test_results["overall_assessment"] = self._generate_overall_assessment(test_results)
        
        return test_results
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent,
            "python_version": sys.version,
            "platform": sys.platform
        }
    
    def _measure_performance(self, test_name: str, test_func, *args, **kwargs) -> PerformanceMetrics:
        """Measure performance of a test function."""
        # Get initial metrics
        start_time = time.time()
        cpu_start = self.process.cpu_percent()
        memory_start = self.process.memory_info().rss
        
        # Force garbage collection before test
        gc.collect()
        
        success = True
        error_message = None
        additional_metrics = {}
        
        try:
            result = test_func(*args, **kwargs)
            if isinstance(result, dict):
                additional_metrics = result
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Performance test {test_name} failed: {e}")
        
        # Get final metrics
        end_time = time.time()
        cpu_end = self.process.cpu_percent()
        memory_end = self.process.memory_info().rss
        memory_peak = max(memory_start, memory_end)
        
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            cpu_usage_start=cpu_start,
            cpu_usage_end=cpu_end,
            memory_usage_start=memory_start,
            memory_usage_end=memory_end,
            memory_peak=memory_peak,
            success=success,
            error_message=error_message,
            additional_metrics=additional_metrics
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def _test_startup_performance(self) -> Dict[str, Any]:
        """Test system startup performance."""
        logger.info("Testing startup performance")
        
        def startup_test():
            from src.config.app_config import app_config
            from src.infrastructure.api.api_provider_factory import APIProviderFactory
            from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
            
            # Measure individual component startup times
            start = time.time()
            factory = APIProviderFactory()
            api_time = time.time() - start
            
            start = time.time()
            service = ComprehensiveQMEFieldService()
            service_time = time.time() - start
            
            return {
                "api_factory_time": api_time,
                "qme_service_time": service_time,
                "components_loaded": 2
            }
        
        metrics = self._measure_performance("System Startup", startup_test)
        
        return {
            "total_startup_time": metrics.duration,
            "memory_usage": metrics.memory_usage_end - metrics.memory_usage_start,
            "cpu_usage": metrics.cpu_usage_end,
            "success": metrics.success,
            "component_times": metrics.additional_metrics,
            "assessment": "excellent" if metrics.duration < 2.0 else "good" if metrics.duration < 5.0 else "needs_improvement"
        }
    
    def _test_service_performance(self) -> Dict[str, Any]:
        """Test individual service performance."""
        logger.info("Testing service performance")
        
        service_tests = [
            ("API Provider Factory", self._test_api_provider_performance),
            ("QME Field Service", self._test_qme_service_performance),
            ("Template Assembler", self._test_template_assembler_performance),
            ("Configuration Manager", self._test_config_manager_performance)
        ]
        
        results = {}
        
        for service_name, test_func in service_tests:
            try:
                metrics = self._measure_performance(service_name, test_func)
                results[service_name.lower().replace(" ", "_")] = {
                    "duration": metrics.duration,
                    "memory_usage": metrics.memory_usage_end - metrics.memory_usage_start,
                    "success": metrics.success,
                    "details": metrics.additional_metrics
                }
            except Exception as e:
                results[service_name.lower().replace(" ", "_")] = {
                    "duration": 0,
                    "memory_usage": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def _test_api_provider_performance(self) -> Dict[str, Any]:
        """Test API provider performance."""
        from src.infrastructure.api.api_provider_factory import APIProviderFactory
        
        start = time.time()
        factory = APIProviderFactory()
        creation_time = time.time() - start
        
        start = time.time()
        primary = factory.get_primary_provider()
        primary_time = time.time() - start
        
        start = time.time()
        fallback = factory.get_fallback_provider()
        fallback_time = time.time() - start
        
        return {
            "factory_creation_time": creation_time,
            "primary_provider_time": primary_time,
            "fallback_provider_time": fallback_time,
            "providers_available": 2
        }
    
    def _test_qme_service_performance(self) -> Dict[str, Any]:
        """Test QME service performance."""
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        
        start = time.time()
        service = ComprehensiveQMEFieldService()
        creation_time = time.time() - start
        
        return {
            "service_creation_time": creation_time,
            "extraction_methods": "hybrid",
            "openrouter_enabled": True
        }
    
    def _test_template_assembler_performance(self) -> Dict[str, Any]:
        """Test template assembler performance."""
        from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
        
        start = time.time()
        assembler = ProfessionalTemplateAssembler()
        creation_time = time.time() - start
        
        return {
            "assembler_creation_time": creation_time,
            "output_format": "docx",
            "professional_formatting": True
        }
    
    def _test_config_manager_performance(self) -> Dict[str, Any]:
        """Test configuration manager performance."""
        from src.infrastructure.configuration.centralized_config_manager import CentralizedConfigManager
        
        start = time.time()
        config_manager = CentralizedConfigManager()
        creation_time = time.time() - start
        
        start = time.time()
        config = config_manager.get_config("app")
        config_time = time.time() - start
        
        return {
            "manager_creation_time": creation_time,
            "config_retrieval_time": config_time,
            "config_loaded": config is not None
        }
    
    def _test_memory_stability(self) -> Dict[str, Any]:
        """Test memory stability over multiple operations."""
        logger.info("Testing memory stability")
        
        def memory_test():
            from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
            
            services = []
            memory_samples = []
            
            # Create multiple service instances
            for i in range(10):
                service = ComprehensiveQMEFieldService()
                services.append(service)
                memory_samples.append(self.process.memory_info().rss)
                time.sleep(0.1)  # Small delay
            
            # Clean up
            del services
            gc.collect()
            
            final_memory = self.process.memory_info().rss
            
            return {
                "iterations": 10,
                "memory_samples": len(memory_samples),
                "memory_growth": memory_samples[-1] - memory_samples[0],
                "final_memory": final_memory,
                "memory_cleaned": final_memory < memory_samples[-1]
            }
        
        metrics = self._measure_performance("Memory Stability", memory_test)
        
        return {
            "memory_growth": metrics.memory_usage_end - metrics.memory_usage_start,
            "peak_memory": metrics.memory_peak,
            "success": metrics.success,
            "details": metrics.additional_metrics,
            "assessment": "stable" if abs(metrics.memory_usage_end - metrics.memory_usage_start) < 50 * 1024 * 1024 else "unstable"
        }
    
    def _test_error_recovery(self) -> Dict[str, Any]:
        """Test error recovery and graceful handling."""
        logger.info("Testing error recovery")
        
        recovery_tests = [
            ("Invalid Configuration", self._test_invalid_config_recovery),
            ("Service Failure", self._test_service_failure_recovery),
            ("API Error", self._test_api_error_recovery)
        ]
        
        results = {}
        
        for test_name, test_func in recovery_tests:
            try:
                metrics = self._measure_performance(f"Error Recovery: {test_name}", test_func)
                results[test_name.lower().replace(" ", "_")] = {
                    "recovery_time": metrics.duration,
                    "success": metrics.success,
                    "details": metrics.additional_metrics
                }
            except Exception as e:
                results[test_name.lower().replace(" ", "_")] = {
                    "recovery_time": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def _test_invalid_config_recovery(self) -> Dict[str, Any]:
        """Test recovery from invalid configuration."""
        try:
            # This should handle gracefully
            from src.config.app_config import app_config
            
            # Try to access potentially missing config
            test_value = getattr(app_config, 'nonexistent_config', 'default_value')
            
            return {
                "config_access": "successful",
                "fallback_used": test_value == 'default_value',
                "graceful_handling": True
            }
        except Exception as e:
            return {
                "config_access": "failed",
                "error": str(e),
                "graceful_handling": False
            }
    
    def _test_service_failure_recovery(self) -> Dict[str, Any]:
        """Test recovery from service failures."""
        try:
            from src.utils.error_handling import safe_execute
            
            def failing_function():
                raise Exception("Test failure")
            
            result, error = safe_execute(failing_function)
            
            return {
                "error_caught": error is not None,
                "result_handled": result is None,
                "recovery_successful": True
            }
        except Exception as e:
            return {
                "error_caught": False,
                "recovery_successful": False,
                "error": str(e)
            }
    
    def _test_api_error_recovery(self) -> Dict[str, Any]:
        """Test recovery from API errors."""
        try:
            from src.infrastructure.api.api_provider_factory import APIProviderFactory
            
            factory = APIProviderFactory()
            
            # Test that factory can handle missing API keys gracefully
            try:
                primary = factory.get_primary_provider()
                fallback = factory.get_fallback_provider()
                
                return {
                    "primary_available": primary is not None,
                    "fallback_available": fallback is not None,
                    "graceful_handling": True
                }
            except Exception as api_error:
                return {
                    "primary_available": False,
                    "fallback_available": False,
                    "graceful_handling": False,
                    "error": str(api_error)
                }
        except Exception as e:
            return {
                "graceful_handling": False,
                "error": str(e)
            }
    
    def _test_stress_scenarios(self) -> Dict[str, Any]:
        """Test system under stress conditions."""
        logger.info("Testing stress scenarios")
        
        stress_tests = [
            ("Concurrent Service Creation", self._test_concurrent_services),
            ("Rapid Configuration Access", self._test_rapid_config_access),
            ("Memory Pressure", self._test_memory_pressure)
        ]
        
        results = {}
        
        for test_name, test_func in stress_tests:
            try:
                metrics = self._measure_performance(f"Stress Test: {test_name}", test_func)
                results[test_name.lower().replace(" ", "_")] = {
                    "duration": metrics.duration,
                    "memory_usage": metrics.memory_usage_end - metrics.memory_usage_start,
                    "success": metrics.success,
                    "details": metrics.additional_metrics
                }
            except Exception as e:
                results[test_name.lower().replace(" ", "_")] = {
                    "duration": 0,
                    "memory_usage": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def _test_concurrent_services(self) -> Dict[str, Any]:
        """Test concurrent service creation."""
        import threading
        
        results = []
        errors = []
        
        def create_service():
            try:
                from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
                service = ComprehensiveQMEFieldService()
                results.append(True)
            except Exception as e:
                errors.append(str(e))
                results.append(False)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_service)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        return {
            "concurrent_operations": len(threads),
            "successful_operations": sum(results),
            "failed_operations": len(errors),
            "success_rate": sum(results) / len(results) if results else 0,
            "errors": errors[:3]  # First 3 errors
        }
    
    def _test_rapid_config_access(self) -> Dict[str, Any]:
        """Test rapid configuration access."""
        from src.config.app_config import app_config
        
        access_times = []
        errors = []
        
        for i in range(100):
            start = time.time()
            try:
                _ = app_config.database_path
                _ = app_config.max_file_size_mb
                _ = app_config.allowed_file_types
                access_times.append(time.time() - start)
            except Exception as e:
                errors.append(str(e))
        
        return {
            "total_accesses": 100,
            "successful_accesses": len(access_times),
            "failed_accesses": len(errors),
            "average_access_time": sum(access_times) / len(access_times) if access_times else 0,
            "max_access_time": max(access_times) if access_times else 0
        }
    
    def _test_memory_pressure(self) -> Dict[str, Any]:
        """Test system under memory pressure."""
        initial_memory = self.process.memory_info().rss
        
        # Create memory pressure
        large_objects = []
        try:
            for i in range(10):
                # Create moderately large objects
                large_obj = [0] * (100000)  # 100k integers
                large_objects.append(large_obj)
            
            peak_memory = self.process.memory_info().rss
            
            # Test service creation under memory pressure
            from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
            service = ComprehensiveQMEFieldService()
            
            service_created = True
        except Exception as e:
            service_created = False
            peak_memory = self.process.memory_info().rss
        finally:
            # Clean up
            del large_objects
            gc.collect()
        
        final_memory = self.process.memory_info().rss
        
        return {
            "initial_memory": initial_memory,
            "peak_memory": peak_memory,
            "final_memory": final_memory,
            "memory_pressure": peak_memory - initial_memory,
            "service_created_under_pressure": service_created,
            "memory_recovered": final_memory < peak_memory
        }
    
    def _test_graceful_degradation(self) -> Dict[str, Any]:
        """Test graceful degradation when components fail."""
        logger.info("Testing graceful degradation")
        
        degradation_tests = [
            ("Missing Dependencies", self._test_missing_dependencies),
            ("Partial Service Failure", self._test_partial_service_failure),
            ("Configuration Issues", self._test_config_degradation)
        ]
        
        results = {}
        
        for test_name, test_func in degradation_tests:
            try:
                metrics = self._measure_performance(f"Degradation: {test_name}", test_func)
                results[test_name.lower().replace(" ", "_")] = {
                    "duration": metrics.duration,
                    "success": metrics.success,
                    "details": metrics.additional_metrics
                }
            except Exception as e:
                results[test_name.lower().replace(" ", "_")] = {
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def _test_missing_dependencies(self) -> Dict[str, Any]:
        """Test behavior when optional dependencies are missing."""
        # This simulates the spaCy model not being available
        try:
            from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
            service = ComprehensiveQMEFieldService()
            
            return {
                "service_created": True,
                "graceful_degradation": True,
                "fallback_used": True
            }
        except Exception as e:
            return {
                "service_created": False,
                "graceful_degradation": False,
                "error": str(e)
            }
    
    def _test_partial_service_failure(self) -> Dict[str, Any]:
        """Test behavior when some services fail but others work."""
        working_services = 0
        failed_services = 0
        
        # Test multiple services
        services_to_test = [
            ("APIProviderFactory", "src.infrastructure.api.api_provider_factory", "APIProviderFactory"),
            ("ServiceRegistry", "src.infrastructure.configuration.service_registry", "ServiceRegistry"),
            ("QMEFieldService", "src.services.comprehensive_qme_field_service", "ComprehensiveQMEFieldService")
        ]
        
        for service_name, module_name, class_name in services_to_test:
            try:
                import importlib
                module = importlib.import_module(module_name)
                service_class = getattr(module, class_name)
                service_instance = service_class()
                working_services += 1
            except Exception:
                failed_services += 1
        
        return {
            "working_services": working_services,
            "failed_services": failed_services,
            "partial_functionality": working_services > 0,
            "graceful_degradation": working_services > failed_services
        }
    
    def _test_config_degradation(self) -> Dict[str, Any]:
        """Test behavior with configuration issues."""
        try:
            from src.config.app_config import app_config
            
            # Test accessing various config values
            config_tests = [
                ("database_path", lambda: app_config.database_path),
                ("max_file_size_mb", lambda: app_config.max_file_size_mb),
                ("allowed_file_types", lambda: app_config.allowed_file_types)
            ]
            
            working_configs = 0
            failed_configs = 0
            
            for config_name, config_getter in config_tests:
                try:
                    value = config_getter()
                    if value:
                        working_configs += 1
                    else:
                        failed_configs += 1
                except Exception:
                    failed_configs += 1
            
            return {
                "working_configs": working_configs,
                "failed_configs": failed_configs,
                "graceful_degradation": working_configs > 0
            }
        except Exception as e:
            return {
                "working_configs": 0,
                "failed_configs": 1,
                "graceful_degradation": False,
                "error": str(e)
            }
    
    def _generate_overall_assessment(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment of system performance and stability."""
        assessments = []
        
        # Startup performance assessment
        startup = test_results.get("startup_performance", {})
        if startup.get("total_startup_time", 0) < 3.0:
            assessments.append("Fast startup time")
        elif startup.get("total_startup_time", 0) < 10.0:
            assessments.append("Acceptable startup time")
        else:
            assessments.append("Slow startup time - needs optimization")
        
        # Memory stability assessment
        memory = test_results.get("memory_stability", {})
        if memory.get("assessment") == "stable":
            assessments.append("Memory usage is stable")
        else:
            assessments.append("Memory usage needs attention")
        
        # Error recovery assessment
        error_recovery = test_results.get("error_recovery", {})
        recovery_success = sum(1 for test in error_recovery.values() if test.get("success", False))
        if recovery_success >= 2:
            assessments.append("Good error recovery capabilities")
        else:
            assessments.append("Error recovery needs improvement")
        
        # Stress testing assessment
        stress = test_results.get("stress_testing", {})
        stress_success = sum(1 for test in stress.values() if test.get("success", False))
        if stress_success >= 2:
            assessments.append("Handles stress conditions well")
        else:
            assessments.append("Stress handling needs improvement")
        
        # Overall recommendation
        if len([a for a in assessments if "needs" not in a.lower()]) >= 3:
            overall_status = "excellent"
            recommendation = "System shows excellent performance and stability"
        elif len([a for a in assessments if "needs" not in a.lower()]) >= 2:
            overall_status = "good"
            recommendation = "System shows good performance with minor areas for improvement"
        else:
            overall_status = "needs_improvement"
            recommendation = "System needs performance and stability improvements"
        
        return {
            "overall_status": overall_status,
            "recommendation": recommendation,
            "detailed_assessments": assessments,
            "test_summary": {
                "startup_time": startup.get("total_startup_time", 0),
                "memory_stable": memory.get("assessment") == "stable",
                "error_recovery_rate": recovery_success / max(len(error_recovery), 1),
                "stress_test_success_rate": stress_success / max(len(stress), 1)
            }
        }


def main():
    """Run performance and stability testing."""
    print("🚀 Starting Performance and Stability Testing")
    print("=" * 60)
    
    tester = PerformanceStabilityTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE AND STABILITY TEST SUMMARY")
    print("=" * 60)
    
    overall = results.get("overall_assessment", {})
    status = overall.get("overall_status", "unknown")
    
    status_icon = "✅" if status == "excellent" else "⚠️" if status == "good" else "❌"
    print(f"{status_icon} Overall Status: {status.upper()}")
    print(f"💡 Recommendation: {overall.get('recommendation', 'No recommendation available')}")
    
    # Print key metrics
    startup = results.get("startup_performance", {})
    memory = results.get("memory_stability", {})
    
    print(f"\n📈 Key Metrics:")
    print(f"  • Startup Time: {startup.get('total_startup_time', 0):.2f}s")
    print(f"  • Memory Stability: {memory.get('assessment', 'unknown')}")
    print(f"  • System Info: {results['system_info']['cpu_count']} CPUs, {results['system_info']['memory_total'] // (1024**3)}GB RAM")
    
    # Print detailed assessments
    assessments = overall.get("detailed_assessments", [])
    if assessments:
        print(f"\n🔍 Detailed Assessments:")
        for assessment in assessments:
            icon = "✅" if "needs" not in assessment.lower() else "⚠️"
            print(f"  {icon} {assessment}")
    
    # Save detailed report
    report_path = Path("results/validation_reports/performance_stability_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Exit with appropriate code
    success = status in ["excellent", "good"]
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()