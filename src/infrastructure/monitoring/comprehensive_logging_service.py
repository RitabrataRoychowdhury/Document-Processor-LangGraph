"""
Comprehensive Logging Service

This service provides comprehensive logging capabilities for QME processing,
including structured logging, performance metrics, quality metrics, and system health monitoring.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
from collections import defaultdict, deque

from src.infrastructure.storage.results_storage_service import ResultsStorageService


class ProcessingStage(Enum):
    """Processing stages for logging."""
    INITIALIZATION = "initialization"
    DOCUMENT_UPLOAD = "document_upload"
    FIELD_EXTRACTION = "field_extraction"
    VALIDATION = "validation"
    TEMPLATE_GENERATION = "template_generation"
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPLETION = "completion"
    ERROR_RECOVERY = "error_recovery"


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ProcessingMetrics:
    """Metrics for processing operations."""
    stage: ProcessingStage
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark processing stage as complete."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message


@dataclass
class QualityMetrics:
    """Quality metrics for processing results."""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    compliance_score: float
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    validation_issues: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class SystemHealthMetrics:
    """System health metrics."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_processes: int
    error_rate: float
    response_time: float
    system_status: str = "healthy"
    alerts: List[str] = field(default_factory=list)


class ComprehensiveLoggingService:
    """
    Comprehensive logging service for QME processing with structured logging,
    performance monitoring, and system health tracking.
    
    Features:
    - Structured logging with contextual information
    - Performance metrics collection and analysis
    - Quality metrics tracking
    - System health monitoring
    - Error tracking and alerting
    - Log aggregation and search
    - Automatic log rotation and archiving
    """
    
    def __init__(self, 
                 log_directory: str = "logs",
                 storage_service: Optional[ResultsStorageService] = None,
                 max_log_size: int = 10 * 1024 * 1024,  # 10MB
                 max_log_files: int = 10):
        """Initialize the comprehensive logging service."""
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.storage_service = storage_service
        self.max_log_size = max_log_size
        self.max_log_files = max_log_files
        
        # Initialize logging components
        self._setup_loggers()
        
        # Metrics storage
        self.processing_metrics: Dict[str, List[ProcessingMetrics]] = defaultdict(list)
        self.quality_metrics: List[QualityMetrics] = []
        self.system_health_metrics: deque = deque(maxlen=1000)  # Keep last 1000 health checks
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque = deque(maxlen=100)  # Keep last 100 errors
        
        # Performance tracking
        self.performance_history: deque = deque(maxlen=1000)
        
        self.logger.info(
            "Initialized ComprehensiveLoggingService",
            extra={
                "log_directory": str(self.log_directory),
                "max_log_size": self.max_log_size,
                "max_log_files": self.max_log_files
            }
        )
    
    def _setup_loggers(self) -> None:
        """Setup structured loggers."""
        # Main application logger
        self.logger = logging.getLogger("qme_comprehensive")
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_data)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handlers
        main_log_file = self.log_directory / "qme_system.log"
        error_log_file = self.log_directory / "errors.log"
        performance_log_file = self.log_directory / "performance.log"
        
        # Main log handler
        main_handler = logging.FileHandler(main_log_file)
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(detailed_formatter)
        
        # Error log handler
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Performance logger
        self.performance_logger = logging.getLogger("qme_performance")
        self.performance_logger.setLevel(logging.DEBUG)
        
        performance_handler = logging.FileHandler(performance_log_file)
        performance_handler.setLevel(logging.DEBUG)
        performance_handler.setFormatter(detailed_formatter)
        self.performance_logger.addHandler(performance_handler)
    
    def log_processing_start(self, 
                           stage: ProcessingStage, 
                           context: Dict[str, Any]) -> str:
        """Log the start of a processing stage."""
        processing_id = f"{stage.value}_{int(time.time() * 1000)}"
        
        metrics = ProcessingMetrics(
            stage=stage,
            start_time=time.time(),
            custom_metrics=context.copy()
        )
        
        self.processing_metrics[processing_id].append(metrics)
        
        self.logger.info(
            f"Processing stage started: {stage.value}",
            extra={
                "processing_id": processing_id,
                "stage": stage.value,
                "context": context,
                "extra_data": json.dumps(context, default=str)
            }
        )
        
        return processing_id
    
    def log_processing_complete(self, 
                              processing_id: str, 
                              success: bool = True,
                              error_message: Optional[str] = None,
                              results: Optional[Dict[str, Any]] = None) -> None:
        """Log the completion of a processing stage."""
        if processing_id in self.processing_metrics:
            metrics = self.processing_metrics[processing_id][-1]
            metrics.complete(success=success, error_message=error_message)
            
            # Add results to custom metrics
            if results:
                metrics.custom_metrics.update(results)
            
            # Log completion
            log_level = logging.INFO if success else logging.ERROR
            message = f"Processing stage completed: {metrics.stage.value}"
            
            extra_data = {
                "processing_id": processing_id,
                "stage": metrics.stage.value,
                "duration": metrics.duration,
                "success": success,
                "error_message": error_message
            }
            
            if results:
                extra_data["results"] = results
            
            self.logger.log(
                log_level,
                message,
                extra={
                    **extra_data,
                    "extra_data": json.dumps(extra_data, default=str)
                }
            )
            
            # Track errors
            if not success and error_message:
                self._track_error(metrics.stage.value, error_message)
            
            # Store performance metrics
            self.performance_history.append({
                "timestamp": datetime.now().isoformat(),
                "stage": metrics.stage.value,
                "duration": metrics.duration,
                "success": success,
                "processing_id": processing_id
            })
    
    def log_quality_metrics(self, 
                          document_id: str,
                          quality_metrics: QualityMetrics) -> None:
        """Log quality assessment metrics."""
        self.quality_metrics.append(quality_metrics)
        
        self.logger.info(
            "Quality metrics recorded",
            extra={
                "document_id": document_id,
                "overall_score": quality_metrics.overall_score,
                "completeness_score": quality_metrics.completeness_score,
                "accuracy_score": quality_metrics.accuracy_score,
                "validation_issues_count": len(quality_metrics.validation_issues),
                "extra_data": json.dumps(asdict(quality_metrics), default=str)
            }
        )
        
        # Store quality metrics if storage service is available
        if self.storage_service:
            try:
                quality_data = {
                    "document_id": document_id,
                    "quality_metrics": asdict(quality_metrics),
                    "timestamp": datetime.now().isoformat(),
                    "result_type": "quality_report"
                }
                self.storage_service.store_quality_report(quality_data)
            except Exception as e:
                self.logger.warning(f"Failed to store quality metrics: {str(e)}")
    
    def log_system_health(self, health_metrics: SystemHealthMetrics) -> None:
        """Log system health metrics."""
        self.system_health_metrics.append(health_metrics)
        
        log_level = logging.INFO
        if health_metrics.system_status != "healthy":
            log_level = logging.WARNING
        if health_metrics.alerts:
            log_level = logging.ERROR
        
        self.logger.log(
            log_level,
            f"System health check: {health_metrics.system_status}",
            extra={
                "cpu_usage": health_metrics.cpu_usage,
                "memory_usage": health_metrics.memory_usage,
                "disk_usage": health_metrics.disk_usage,
                "active_processes": health_metrics.active_processes,
                "error_rate": health_metrics.error_rate,
                "response_time": health_metrics.response_time,
                "alerts": health_metrics.alerts,
                "extra_data": json.dumps(asdict(health_metrics), default=str)
            }
        )
    
    def log_performance_metrics(self, 
                              operation: str,
                              duration: float,
                              metadata: Dict[str, Any]) -> None:
        """Log performance metrics."""
        self.performance_logger.info(
            f"Performance metric: {operation}",
            extra={
                "operation": operation,
                "duration": duration,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "extra_data": json.dumps({
                    "operation": operation,
                    "duration": duration,
                    **metadata
                }, default=str)
            }
        )
    
    def log_error(self, 
                  error_type: str,
                  error_message: str,
                  context: Optional[Dict[str, Any]] = None,
                  exception: Optional[Exception] = None) -> None:
        """Log error with context."""
        self._track_error(error_type, error_message)
        
        extra_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        if exception:
            extra_data["exception_type"] = type(exception).__name__
            extra_data["exception_details"] = str(exception)
        
        self.logger.error(
            f"Error occurred: {error_type}",
            extra={
                **extra_data,
                "extra_data": json.dumps(extra_data, default=str)
            },
            exc_info=exception is not None
        )
    
    def _track_error(self, error_type: str, error_message: str) -> None:
        """Track error for statistics."""
        self.error_counts[error_type] += 1
        self.recent_errors.append({
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_processing_statistics(self, 
                                stage: Optional[ProcessingStage] = None) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = {
            "total_processes": 0,
            "successful_processes": 0,
            "failed_processes": 0,
            "average_duration": 0.0,
            "stage_breakdown": {}
        }
        
        all_metrics = []
        for processing_id, metrics_list in self.processing_metrics.items():
            for metrics in metrics_list:
                if stage is None or metrics.stage == stage:
                    all_metrics.append(metrics)
        
        if all_metrics:
            stats["total_processes"] = len(all_metrics)
            stats["successful_processes"] = sum(1 for m in all_metrics if m.success)
            stats["failed_processes"] = sum(1 for m in all_metrics if not m.success)
            
            completed_metrics = [m for m in all_metrics if m.duration is not None]
            if completed_metrics:
                stats["average_duration"] = sum(m.duration for m in completed_metrics) / len(completed_metrics)
            
            # Stage breakdown
            stage_stats = defaultdict(lambda: {"count": 0, "success": 0, "total_duration": 0.0})
            for metrics in all_metrics:
                stage_name = metrics.stage.value
                stage_stats[stage_name]["count"] += 1
                if metrics.success:
                    stage_stats[stage_name]["success"] += 1
                if metrics.duration:
                    stage_stats[stage_name]["total_duration"] += metrics.duration
            
            for stage_name, stage_data in stage_stats.items():
                stats["stage_breakdown"][stage_name] = {
                    "total_count": stage_data["count"],
                    "success_count": stage_data["success"],
                    "success_rate": stage_data["success"] / stage_data["count"] if stage_data["count"] > 0 else 0.0,
                    "average_duration": stage_data["total_duration"] / stage_data["count"] if stage_data["count"] > 0 else 0.0
                }
        
        return stats
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality statistics."""
        if not self.quality_metrics:
            return {"message": "No quality metrics available"}
        
        stats = {
            "total_assessments": len(self.quality_metrics),
            "average_overall_score": sum(m.overall_score for m in self.quality_metrics) / len(self.quality_metrics),
            "average_completeness_score": sum(m.completeness_score for m in self.quality_metrics) / len(self.quality_metrics),
            "average_accuracy_score": sum(m.accuracy_score for m in self.quality_metrics) / len(self.quality_metrics),
            "average_consistency_score": sum(m.consistency_score for m in self.quality_metrics) / len(self.quality_metrics),
            "average_compliance_score": sum(m.compliance_score for m in self.quality_metrics) / len(self.quality_metrics),
            "total_validation_issues": sum(len(m.validation_issues) for m in self.quality_metrics)
        }
        
        return stats
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_breakdown": dict(self.error_counts),
            "recent_errors": list(self.recent_errors)[-10:],  # Last 10 errors
            "error_rate": self._calculate_error_rate()
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        if not self.performance_history:
            return 0.0
        
        recent_operations = list(self.performance_history)[-100:]  # Last 100 operations
        if not recent_operations:
            return 0.0
        
        failed_operations = sum(1 for op in recent_operations if not op.get("success", True))
        return failed_operations / len(recent_operations)
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get system health summary."""
        if not self.system_health_metrics:
            return {"message": "No system health metrics available"}
        
        recent_metrics = list(self.system_health_metrics)[-10:]  # Last 10 health checks
        
        return {
            "current_status": recent_metrics[-1].system_status if recent_metrics else "unknown",
            "average_cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            "average_memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            "average_response_time": sum(m.response_time for m in recent_metrics) / len(recent_metrics),
            "active_alerts": recent_metrics[-1].alerts if recent_metrics else [],
            "health_checks_count": len(self.system_health_metrics)
        }
    
    def export_logs(self, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   log_level: Optional[LogLevel] = None) -> Dict[str, Any]:
        """Export logs for analysis."""
        # This would implement log export functionality
        # For now, return summary statistics
        return {
            "processing_statistics": self.get_processing_statistics(),
            "quality_statistics": self.get_quality_statistics(),
            "error_statistics": self.get_error_statistics(),
            "system_health_summary": self.get_system_health_summary(),
            "export_timestamp": datetime.now().isoformat()
        }
    
    def cleanup_old_logs(self, days_old: int = 30) -> int:
        """Clean up old log files."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for log_file in self.log_directory.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date:
                    try:
                        log_file.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to delete old log file {log_file}: {str(e)}")
            
            self.logger.info(f"Cleaned up {cleaned_count} old log files")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {str(e)}")
            return 0


# Factory function for creating comprehensive logging service
def create_comprehensive_logging_service(
    log_directory: str = "logs",
    storage_service: Optional[ResultsStorageService] = None
) -> ComprehensiveLoggingService:
    """Factory function to create comprehensive logging service."""
    return ComprehensiveLoggingService(
        log_directory=log_directory,
        storage_service=storage_service
    )