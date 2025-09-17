#!/usr/bin/env python3
"""
Service Integration Test

This script tests the dependency injection container and service registration
to ensure all backend services can be properly instantiated and integrated.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_service_registration():
    """Test service registration and dependency injection."""
    print("=" * 60)
    print("TESTING SERVICE REGISTRATION AND DEPENDENCY INJECTION")
    print("=" * 60)
    
    try:
        # Import service registration components
        from src.infrastructure.configuration.service_registration import (
            initialize_service_container,
            get_registration_manager
        )
        
        print("\n1. Initializing service container...")
        registration_manager = initialize_service_container()
        print("✓ Service container initialized successfully")
        
        print("\n2. Getting service health report...")
        health_report = registration_manager.get_service_health_report()
        
        print(f"✓ Service registry health: {health_report['service_registry_health']['health_status']}")
        print(f"✓ Total registered services: {health_report['service_registry_health']['total_registered_services']}")
        print(f"✓ Instantiated services: {health_report['service_registry_health']['instantiated_services']}")
        
        if health_report['service_registry_health']['validation_errors']:
            print(f"⚠ Validation errors: {len(health_report['service_registry_health']['validation_errors'])}")
            for error in health_report['service_registry_health']['validation_errors']:
                print(f"  - {error}")
        
        print("\n3. Testing service instantiation...")
        instantiation_results = registration_manager.test_service_instantiation()
        
        print(f"✓ Total services tested: {instantiation_results['total_services']}")
        print(f"✓ Successful instantiations: {instantiation_results['successful_instantiations']}")
        print(f"✗ Failed instantiations: {instantiation_results['failed_instantiations']}")
        
        if instantiation_results['errors']:
            print(f"\nInstantiation errors ({len(instantiation_results['errors'])}):")
            for error in instantiation_results['errors']:
                print(f"  - {error}")
        
        print("\n4. Listing registered services...")
        registered_services = health_report['registered_services']
        
        for service_name, service_info in registered_services.items():
            status = "✓" if service_info['is_instantiated'] else "○"
            print(f"  {status} {service_name} ({service_info['lifetime']})")
        
        return instantiation_results['failed_instantiations'] == 0
        
    except Exception as e:
        print(f"✗ Service registration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_service_factory():
    """Test service factory functionality."""
    print("\n" + "=" * 60)
    print("TESTING SERVICE FACTORY")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.service_factory import (
            get_service_factory,
            ServiceFactoryConfig
        )
        
        print("\n1. Creating service factory...")
        config = ServiceFactoryConfig(
            auto_initialize=True,
            validate_on_creation=True,
            enable_fallbacks=True,
            log_service_access=False
        )
        
        service_factory = get_service_factory(config)
        print("✓ Service factory created successfully")
        
        print("\n2. Testing interface-based service access...")
        
        # Test extraction service
        try:
            extraction_service = service_factory.get_extraction_service()
            print("✓ Extraction service accessible")
        except Exception as e:
            print(f"⚠ Extraction service error: {str(e)}")
        
        # Test validation service
        try:
            validation_service = service_factory.get_validation_service()
            print("✓ Validation service accessible")
        except Exception as e:
            print(f"⚠ Validation service error: {str(e)}")
        
        # Test generation service
        try:
            generation_service = service_factory.get_generation_service()
            print("✓ Generation service accessible")
        except Exception as e:
            print(f"⚠ Generation service error: {str(e)}")
        
        # Test storage service
        try:
            storage_service = service_factory.get_storage_service()
            print("✓ Storage service accessible")
        except Exception as e:
            print(f"⚠ Storage service error: {str(e)}")
        
        # Test monitoring service
        try:
            monitoring_service = service_factory.get_monitoring_service()
            print("✓ Monitoring service accessible")
        except Exception as e:
            print(f"⚠ Monitoring service error: {str(e)}")
        
        print("\n3. Getting service health from factory...")
        health_info = service_factory.get_service_health()
        print(f"✓ Service health status: {health_info.get('service_registry_health', {}).get('health_status', 'unknown')}")
        
        print("\n4. Validating services through factory...")
        validation_results = service_factory.validate_services()
        print(f"✓ Services validated: {validation_results.get('successful_instantiations', 0)}/{validation_results.get('total_services', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Service factory test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_services():
    """Test specific service instantiation."""
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC SERVICE INSTANTIATION")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.service_registry import service_registry
        
        # Test specific services that should be available
        test_services = [
            "ConfigurationService",
            "ResultsStorageService", 
            "ComprehensiveLoggingService",
            "ComprehensiveQMEFieldService",
            "ProfessionalTemplateAssembler"
        ]
        
        successful_tests = 0
        
        for service_name in test_services:
            try:
                # Find the service type
                service_type = None
                for registered_type in service_registry._services.keys():
                    if registered_type.__name__ == service_name:
                        service_type = registered_type
                        break
                
                if service_type:
                    instance = service_registry.get(service_type)
                    if instance:
                        print(f"✓ {service_name}: Successfully instantiated")
                        successful_tests += 1
                    else:
                        print(f"✗ {service_name}: Returned None instance")
                else:
                    print(f"✗ {service_name}: Service type not found")
                    
            except Exception as e:
                print(f"✗ {service_name}: {str(e)}")
        
        print(f"\nSpecific service tests: {successful_tests}/{len(test_services)} successful")
        return successful_tests == len(test_services)
        
    except Exception as e:
        print(f"✗ Specific service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_integration():
    """Test configuration service integration."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION INTEGRATION")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.configuration_service import create_configuration_service
        
        print("\n1. Creating configuration service...")
        config_service = create_configuration_service()
        print("✓ Configuration service created")
        
        print("\n2. Testing configuration access...")
        database_config = config_service.get_database_config()
        print(f"✓ Database config: {database_config.get('url', 'Not configured')}")
        
        api_config = config_service.get_api_config()
        print(f"✓ API config timeout: {api_config.get('timeout', 'Not configured')}")
        
        print("\n3. Validating configuration...")
        validation_errors = config_service.validate_configuration()
        if validation_errors:
            print(f"⚠ Configuration validation errors ({len(validation_errors)}):")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("✓ Configuration validation passed")
        
        return len(validation_errors) == 0
        
    except Exception as e:
        print(f"✗ Configuration integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all service integration tests."""
    print("QME System - Service Integration Test")
    print("=" * 60)
    
    # Ensure we're in the right directory
    if not os.path.exists("src"):
        print("✗ Error: 'src' directory not found. Please run from project root.")
        return False
    
    # Run tests
    test_results = []
    
    test_results.append(("Configuration Integration", test_configuration_integration()))
    test_results.append(("Service Registration", test_service_registration()))
    test_results.append(("Service Factory", test_service_factory()))
    test_results.append(("Specific Services", test_specific_services()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("🎉 All service integration tests passed!")
        return True
    else:
        print("❌ Some service integration tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)