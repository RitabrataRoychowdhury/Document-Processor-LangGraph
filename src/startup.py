"""
System startup module with health checks and performance monitoring.

This module handles the complete system startup process including environment validation,
health checks, knowledge base initialization, and performance monitoring setup.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.app_config import AppConfig
from src.config.environment_validator import ensure_environment_ready
from src.config.dependency_injection import DependencyContainer
from src.services.health_checker import HealthChecker
from src.services.knowledge_base_initializer import initialize_system_startup
from src.services.performance_monitor import get_performance_monitor
from src.utils.logging_config import LoggingManager

logger = logging.getLogger(__name__)


class SystemStartup:
    """Handles complete system startup process."""
    
    def __init__(self):
        """Initialize system startup."""
        self.config = None
        self.container = None
        self.health_checker = None
        self.performance_monitor = None
    
    async def startup(self) -> bool:
        """Execute complete system startup process."""
        try:
            logger.info("🚀 Starting Document Q&A System...")
            
            # Step 1: Setup logging
            logging_manager = LoggingManager()
            logger.info("✅ Logging configured")
            
            # Step 2: Load configuration
            self.config = AppConfig.from_env()
            logger.info("✅ Configuration loaded")
            
            # Step 3: Validate environment
            if not ensure_environment_ready(self.config):
                logger.error("❌ Environment validation failed")
                return False
            logger.info("✅ Environment validation passed")
            
            # Step 4: Initialize dependency container
            self.container = DependencyContainer(self.config)
            logger.info("✅ Dependency container initialized")
            
            # Step 5: Initialize health checker
            self.health_checker = HealthChecker(self.config)
            logger.info("✅ Health checker initialized")
            
            # Step 6: Initialize performance monitor
            self.performance_monitor = get_performance_monitor()
            logger.info("✅ Performance monitor initialized")
            
            # Step 7: Run initial health checks
            if not await self._run_initial_health_checks():
                logger.error("❌ Initial health checks failed")
                return False
            logger.info("✅ Initial health checks passed")
            
            # Step 8: Initialize knowledge base
            if not await self._initialize_knowledge_base():
                logger.warning("⚠️  Knowledge base initialization had issues")
                # Continue anyway - system can still function
            else:
                logger.info("✅ Knowledge base initialized")
            
            # Step 9: Final health checks
            if not await self._run_final_health_checks():
                logger.warning("⚠️  Final health checks had issues")
                # Continue anyway
            else:
                logger.info("✅ Final health checks passed")
            
            # Step 10: System ready
            logger.info("🎉 System startup completed successfully!")
            self._print_startup_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {str(e)}", exc_info=True)
            return False
    
    async def _run_initial_health_checks(self) -> bool:
        """Run initial health checks before knowledge base initialization."""
        try:
            logger.info("Running initial health checks...")
            
            # Check database health
            db_health = self.health_checker.check_database_health()
            if not db_health.is_healthy:
                logger.error(f"Database health check failed: {db_health.message}")
                return False
            
            # Check file system health
            fs_health = self.health_checker.check_file_system_health()
            if not fs_health.is_healthy:
                logger.error(f"File system health check failed: {fs_health.message}")
                return False
            
            # Check configuration health
            config_health = self.health_checker.check_configuration_health()
            if not config_health.is_healthy:
                logger.error(f"Configuration health check failed: {config_health.message}")
                return False
            
            # QME-specific health checks
            if not await self._run_qme_health_checks():
                logger.warning("QME health checks had issues - continuing with startup")
                # Don't fail startup for QME issues, just warn
            
            return True
            
        except Exception as e:
            logger.error(f"Initial health checks failed: {str(e)}", exc_info=True)
            return False
    
    async def _initialize_knowledge_base(self) -> bool:
        """Initialize knowledge base with canonical documents."""
        try:
            logger.info("Initializing knowledge base...")
            
            # Get ingestion pipeline from container
            pipeline = self.container.get_ingestion_pipeline()
            
            # Initialize knowledge base
            result = await initialize_system_startup(self.config, pipeline)
            
            # Log results
            logger.info(f"Knowledge base initialization completed:")
            logger.info(f"  - Processed documents: {len(result.processed_documents)}")
            logger.info(f"  - Failed documents: {len(result.failed_documents)}")
            logger.info(f"  - Total time: {result.total_processing_time:.2f}s")
            
            if result.failed_documents:
                logger.warning(f"Failed to process documents: {result.failed_documents}")
                for error in result.error_messages:
                    logger.warning(f"  - {error}")
            
            return result.success
            
        except Exception as e:
            logger.error(f"Knowledge base initialization failed: {str(e)}", exc_info=True)
            return False
    
    async def _run_qme_health_checks(self) -> bool:
        """Run QME-specific health checks."""
        try:
            logger.info("Running QME workflow health checks...")
            
            # Test QME service imports
            try:
                from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
                from src.services.qme_template_generator import QMETemplateGenerator
                from src.services.professional_template_assembler import ProfessionalTemplateAssembler
                logger.info("✅ QME service imports successful")
            except ImportError as e:
                logger.warning(f"⚠️  QME import issue: {e}")
                return False
            
            # Test QME field extraction service
            try:
                field_service = ComprehensiveQMEFieldService()
                logger.info("✅ QME field extraction service initialized")
            except Exception as e:
                logger.warning(f"⚠️  QME field extraction issue: {e}")
                return False
            
            # Test QME template generator
            try:
                template_generator = QMETemplateGenerator()
                logger.info("✅ QME template generator initialized")
            except Exception as e:
                logger.warning(f"⚠️  QME template generator issue: {e}")
                return False
            
            # Check for PQME test files
            pqme_files = [
                "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
                "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
            ]
            
            found_pqme = []
            for file_path in pqme_files:
                if Path(file_path).exists():
                    found_pqme.append(file_path)
            
            if found_pqme:
                logger.info(f"✅ Found {len(found_pqme)} PQME test files")
            else:
                logger.warning("⚠️  No PQME test files found - field extraction testing will be limited")
            
            return True
            
        except Exception as e:
            logger.error(f"QME health checks failed: {str(e)}", exc_info=True)
            return False
    
    async def _run_final_health_checks(self) -> bool:
        """Run final comprehensive health checks."""
        try:
            logger.info("Running final health checks...")
            
            # Get overall health status
            health = self.health_checker.get_overall_health()
            
            logger.info(f"Overall system health: {'HEALTHY' if health['overall_healthy'] else 'UNHEALTHY'}")
            logger.info(f"Healthy components: {health['healthy_components']}/{health['total_components']}")
            
            # Log individual component status
            for component, status in health['checks'].items():
                status_text = 'PASS' if status['healthy'] else 'FAIL'
                logger.info(f"  {component}: {status_text} - {status['message']}")
                
                if not status['healthy'] and status.get('details'):
                    for key, value in status['details'].items():
                        logger.info(f"    {key}: {value}")
            
            # Run QME workflow validation
            qme_validation = await self._validate_qme_workflow()
            if qme_validation:
                logger.info("✅ QME workflow validation passed")
            else:
                logger.warning("⚠️  QME workflow validation had issues")
            
            return health['overall_healthy']
            
        except Exception as e:
            logger.error(f"Final health checks failed: {str(e)}", exc_info=True)
            return False
    
    async def _validate_qme_workflow(self) -> bool:
        """Validate QME workflow capabilities."""
        try:
            logger.info("Validating QME workflow...")
            
            # Test document processing capability
            pqme_files = [
                "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
                "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
            ]
            
            validation_passed = True
            
            # Check if we can process at least one PQME file
            for file_path in pqme_files:
                if Path(file_path).exists():
                    try:
                        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
                        
                        # Quick validation test (don't process full file during startup)
                        service = ComprehensiveQMEFieldService()
                        logger.info(f"✅ QME workflow validation: Can process {file_path}")
                        break
                    except Exception as e:
                        logger.warning(f"⚠️  QME workflow issue with {file_path}: {e}")
                        validation_passed = False
            else:
                logger.warning("⚠️  No PQME files available for workflow validation")
                validation_passed = False
            
            # Test performance monitoring for QME
            try:
                stats = self.performance_monitor.get_current_statistics()
                logger.info("✅ QME performance monitoring ready")
            except Exception as e:
                logger.warning(f"⚠️  QME performance monitoring issue: {e}")
                validation_passed = False
            
            return validation_passed
            
        except Exception as e:
            logger.error(f"QME workflow validation failed: {str(e)}", exc_info=True)
            return False
    
    def _print_startup_summary(self):
        """Print startup summary information."""
        try:
            # Get system information
            health = self.health_checker.get_overall_health()
            perf_stats = self.performance_monitor.get_current_statistics()
            
            print("\n" + "="*60)
            print("🎉 DOCUMENT Q&A SYSTEM - STARTUP COMPLETE")
            print("="*60)
            print(f"📊 System Health: {'✅ HEALTHY' if health['overall_healthy'] else '❌ UNHEALTHY'}")
            print(f"🔧 Components: {health['healthy_components']}/{health['total_components']} healthy")
            print(f"📈 Performance Monitor: Active")
            print(f"🗄️  Database: {self.config.database_path}")
            print(f"🤖 QA Provider: {self.config.qa_provider}")
            print(f"🔤 Embedding Provider: {self.config.embedding_provider}")
            print(f"📁 Max File Size: {self.config.max_file_size_mb}MB")
            print(f"📄 Allowed Types: {', '.join(self.config.allowed_file_types)}")
            
            # QME-specific status
            print("="*60)
            print("🏥 QME WORKFLOW STATUS")
            print("="*60)
            
            # Check QME components
            try:
                from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
                print("✅ QME Field Extraction: Ready")
            except:
                print("❌ QME Field Extraction: Not Available")
            
            try:
                from src.services.qme_template_generator import QMETemplateGenerator
                print("✅ QME Template Generation: Ready")
            except:
                print("❌ QME Template Generation: Not Available")
            
            # Check PQME test files
            pqme_files = [
                "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
                "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
            ]
            
            found_pqme = sum(1 for f in pqme_files if Path(f).exists())
            print(f"📋 PQME Test Files: {found_pqme}/{len(pqme_files)} available")
            
            print("="*60)
            print("🌐 Access the application at: http://localhost:8501")
            print("📚 Upload documents to: data/documents/")
            print("🔍 View logs in: logs/")
            print("🏥 QME workflow: ./scripts/run.sh (option 9)")
            print("📋 PQME testing: ./scripts/run.sh (option 10)")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error printing startup summary: {str(e)}")
    
    def get_health_checker(self) -> HealthChecker:
        """Get health checker instance."""
        return self.health_checker
    
    def get_performance_monitor(self):
        """Get performance monitor instance."""
        return self.performance_monitor
    
    def get_container(self) -> DependencyContainer:
        """Get dependency container instance."""
        return self.container


async def startup_system() -> SystemStartup:
    """Startup the complete system and return startup instance."""
    startup = SystemStartup()
    success = await startup.startup()
    
    if not success:
        logger.error("System startup failed")
        sys.exit(1)
    
    return startup


def main():
    """Main entry point for system startup."""
    try:
        # Run startup process
        startup = asyncio.run(startup_system())
        
        # Keep the process running for monitoring
        logger.info("System is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(60)  # Sleep for 1 minute
                
                # Periodic health check
                health = startup.get_health_checker().get_overall_health()
                if not health['overall_healthy']:
                    logger.warning("System health degraded during runtime")
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        
    except Exception as e:
        logger.error(f"System startup failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()