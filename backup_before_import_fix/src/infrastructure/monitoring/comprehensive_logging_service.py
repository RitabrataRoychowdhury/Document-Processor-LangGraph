"""
Comprehensive Logging and Monitoring Service

Provides centralized logging and monitoring for all QME system processing stages:
- Document processing pipeline monitoring
- Quality validation tracking
- Performance metrics collection
- Error reporting and analysis
- System health monitoring

This service follows SOLID principles with clear separation of concerns.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
import threading
from collections import defaultdict, deque

from .results_storage_service import ResultsStorageService


class LogLevel(Enum):
    """Log levels for different types of events"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProcessingStage(Enum):
    """Different stages of QME processing"""
    DOCUMENT_INGESTION = "document_ingestion"
    INFORMATION_EXTRACTION = "information_extraction"
    CONTENT_GENERATION = "content_generation"
    TEMPLATE_ASSEMBLY = "template_assembly"
    QUALITY_VALIDATION = "quality_validation"
    DOCUMENT_OUTPUT = "document_output"


@dataclass
class ProcessingMetrics:
    """Metrics for a processing operation"""
    stage: ProcessingStage
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    quality_score: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class SystemHealthMetrics:
    """System health and performance metrics"""
    timestamp: datetime
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_mb: float
    active_processes: int
    error_rate: float
    average_processing_time: float
    queue_size: int


@dataclass
class QualityMetrics:
    """Quality assessment metrics"""
    document_id: str
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    compliance_score: float
    processing_time: float
    validation_issues: List[str]
    timestamp: datetime


class ComprehensiveLoggingService:
    """
    Comprehensive logging and monitoring service for the QME system.
    
    Provides centralized logging, performance monitoring, quality tracking,
    and system health monitoring across all processing stages.
    """
    
    def __init__(
        self,
        log_directory: str = "logs",
        results_storage: Optional[ResultsStorageService] = None,
        max_memory_logs: int = 1000
    ):
        """
        Initialize the comprehensive logging service.
        
        Args:
            log_directory: Directory for log files
            results_storage: Optional results storage service
            max_memory_logs: Maximum number of logs to keep in memory
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        self.results_storage = results_storage or ResultsStorageService()
        self.max_memory_logs = max_memory_logs
        
        # In-memory storage for recent metrics
        self.processing_metrics: deque = deque(maxlen=max_memory_logs)
        self.quality_metrics: deque = deque(maxlen=max_memory_logs)
        self.system_health_metrics: deque = deque(maxlen=max_memory_logs)
        self.error_log: deque = deque(maxlen=max_memory_logs)
        
        # Performance tracking
        self.stage_timers: Dict[str, float] = {}
        self.active_operations: Dict[str, ProcessingMetrics] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Setup loggers
        self._setup_loggers()
        
    def _setup_loggers(self) -> None:
        """Setup structured loggers for different components"""
        # Main system logger
        self.system_logger = self._create_logger(
            "qme_system",
            self.log_directory / "qme_system.log"
        )
        
        # Processing pipeline logger
        self.processing_logger = self._create_logger(
            "qme_processing",
            self.log_directory / "qme_processing.log"
        )
        
        # Quality validation logger
        self.quality_logger = self._create_logger(
            "qme_quality",
            self.log_directory / "qme_quality.log"
        )
        
        # Error logger
        self.error_logger = self._create_logger(
            "qme_errors",
            self.log_directory / "qme_errors.log"
        )
        
        # Performance logger
        self.performance_logger = self._create_logger(
            "qme_performance",
            self.log_directory / "qme_performance.log"
        )
        
    def _create_logger(self, name: str, log_file: Path) -> logging.Logger:
        """Create a structured logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
            
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    @contextmanager
    def track_processing_stage(
        self,
        stage: ProcessingStage,
        operation_id: str,
        input_size: Optional[int] = None
    ):
        """
        Context manager for tracking processing stage metrics.
        
        Args:
            stage: Processing stage being tracked
            operation_id: Unique identifier for this operation
            input_size: Optional size of input data
            
        Yields:
            ProcessingMetrics object that gets updated during processing
        """
        metrics = ProcessingMetrics(
            stage=stage,
            start_time=datetime.now(),
            input_size=input_size
        )
        
        with self._lock:
            self.active_operations[operation_id] = metrics
            
        self.processing_logger.info(
            f"Started {stage.value} for operation {operation_id}"
        )
        
        try:
            yield metrics
            
            # Mark as successful
            metrics.success = True
            self.processing_logger.info(
                f"Completed {stage.value} for operation {operation_id}"
            )
            
        except Exception as e:
            # Mark as failed
            metrics.success = False
            metrics.error_message = str(e)
            
            self.error_logger.error(
                f"Failed {stage.value} for operation {operation_id}: {e}"
            )
            
            # Store error in memory
            with self._lock:
                self.error_log.append({
                    "timestamp": datetime.now(),
                    "stage": stage.value,
                    "operation_id": operation_id,
                    "error": str(e)
                })
                
            raise
            
        finally:
            # Finalize metrics
            metrics.end_time = datetime.now()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            
            # Store metrics
            with self._lock:
                self.processing_metrics.append(metrics)
                if operation_id in self.active_operations:
                    del self.active_operations[operation_id]
                    
            # Log performance metrics
            self.performance_logger.info(
                f"Stage {stage.value} completed in {metrics.duration:.2f}s "
                f"(Success: {metrics.success})"
            )
            
    def log_quality_metrics(self, metrics: QualityMetrics) -> None:
        """
        Log quality assessment metrics.
        
        Args:
            metrics: Quality metrics to log
        """
        with self._lock:
            self.quality_metrics.append(metrics)
            
        self.quality_logger.info(
            f"Quality assessment for {metrics.document_id}: "
            f"Overall={metrics.overall_score:.2f}, "
            f"Completeness={metrics.completeness_score:.2f}, "
            f"Accuracy={metrics.accuracy_score:.2f}, "
            f"Issues={len(metrics.validation_issues)}"
        )
        
        # Store detailed quality report
        quality_report = self._generate_quality_report(metrics)
        self.results_storage.store_validation_report(
            quality_report,
            metrics.document_id,
            metrics.overall_score
        )
        
    def log_system_health(self, metrics: SystemHealthMetrics) -> None:
        """
        Log system health metrics.
        
        Args:
            metrics: System health metrics to log
        """
        with self._lock:
            self.system_health_metrics.append(metrics)
            
        self.system_logger.info(
            f"System Health: Memory={metrics.memory_usage_mb:.1f}MB, "
            f"CPU={metrics.cpu_usage_percent:.1f}%, "
            f"ErrorRate={metrics.error_rate:.2f}%, "
            f"AvgProcessingTime={metrics.average_processing_time:.2f}s"
        )
        
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        stage: Optional[ProcessingStage] = None
    ) -> None:
        """
        Log an error with context information.
        
        Args:
            error: Exception that occurred
            context: Context information about the error
            stage: Optional processing stage where error occurred
        """
        error_info = {
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "stage": stage.value if stage else None
        }
        
        with self._lock:
            self.error_log.append(error_info)
            
        self.error_logger.error(
            f"Error in {stage.value if stage else 'unknown stage'}: "
            f"{type(error).__name__}: {error}. Context: {context}"
        )
        
    def get_processing_statistics(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get processing statistics for a time window.
        
        Args:
            time_window: Optional time window to filter metrics
            
        Returns:
            Dictionary with processing statistics
        """
        with self._lock:
            metrics = list(self.processing_metrics)
            
        if time_window:
            cutoff_time = datetime.now() - time_window
            metrics = [m for m in metrics if m.start_time >= cutoff_time]
            
        if not metrics:
            return {"message": "No metrics available for the specified time window"}
            
        # Calculate statistics
        total_operations = len(metrics)
        successful_operations = len([m for m in metrics if m.success])
        failed_operations = total_operations - successful_operations
        
        durations = [m.duration for m in metrics if m.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Stage-specific statistics
        stage_stats = defaultdict(lambda: {"count": 0, "success": 0, "avg_duration": 0})
        for metric in metrics:
            stage = metric.stage.value
            stage_stats[stage]["count"] += 1
            if metric.success:
                stage_stats[stage]["success"] += 1
            if metric.duration:
                stage_stats[stage]["avg_duration"] += metric.duration
                
        # Calculate averages
        for stage_data in stage_stats.values():
            if stage_data["count"] > 0:
                stage_data["success_rate"] = stage_data["success"] / stage_data["count"]
                stage_data["avg_duration"] /= stage_data["count"]
                
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "average_duration": avg_duration,
            "stage_statistics": dict(stage_stats),
            "time_window": str(time_window) if time_window else "all_time"
        }
        
    def get_quality_statistics(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get quality statistics for a time window.
        
        Args:
            time_window: Optional time window to filter metrics
            
        Returns:
            Dictionary with quality statistics
        """
        with self._lock:
            metrics = list(self.quality_metrics)
            
        if time_window:
            cutoff_time = datetime.now() - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
        if not metrics:
            return {"message": "No quality metrics available for the specified time window"}
            
        # Calculate quality statistics
        overall_scores = [m.overall_score for m in metrics]
        completeness_scores = [m.completeness_score for m in metrics]
        accuracy_scores = [m.accuracy_score for m in metrics]
        consistency_scores = [m.consistency_score for m in metrics]
        compliance_scores = [m.compliance_score for m in metrics]
        
        total_issues = sum(len(m.validation_issues) for m in metrics)
        
        return {
            "total_assessments": len(metrics),
            "average_overall_score": sum(overall_scores) / len(overall_scores),
            "average_completeness_score": sum(completeness_scores) / len(completeness_scores),
            "average_accuracy_score": sum(accuracy_scores) / len(accuracy_scores),
            "average_consistency_score": sum(consistency_scores) / len(consistency_scores),
            "average_compliance_score": sum(compliance_scores) / len(compliance_scores),
            "total_validation_issues": total_issues,
            "average_issues_per_document": total_issues / len(metrics),
            "time_window": str(time_window) if time_window else "all_time"
        }
        
    def get_error_analysis(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get error analysis for a time window.
        
        Args:
            time_window: Optional time window to filter errors
            
        Returns:
            Dictionary with error analysis
        """
        with self._lock:
            errors = list(self.error_log)
            
        if time_window:
            cutoff_time = datetime.now() - time_window
            errors = [e for e in errors if e["timestamp"] >= cutoff_time]
            
        if not errors:
            return {"message": "No errors recorded for the specified time window"}
            
        # Analyze errors
        error_types = defaultdict(int)
        stage_errors = defaultdict(int)
        
        for error in errors:
            error_types[error["error_type"]] += 1
            if error["stage"]:
                stage_errors[error["stage"]] += 1
                
        return {
            "total_errors": len(errors),
            "error_types": dict(error_types),
            "errors_by_stage": dict(stage_errors),
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
            "most_problematic_stage": max(stage_errors.items(), key=lambda x: x[1])[0] if stage_errors else None,
            "time_window": str(time_window) if time_window else "all_time"
        }
        
    def generate_monitoring_report(self) -> str:
        """
        Generate a comprehensive monitoring report.
        
        Returns:
            Formatted monitoring report as string
        """
        # Get statistics for the last 24 hours
        time_window = timedelta(hours=24)
        
        processing_stats = self.get_processing_statistics(time_window)
        quality_stats = self.get_quality_statistics(time_window)
        error_analysis = self.get_error_analysis(time_window)
        
        report = f"""
QME System Monitoring Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Time Window: Last 24 hours

=== PROCESSING STATISTICS ===
Total Operations: {processing_stats.get('total_operations', 0)}
Successful Operations: {processing_stats.get('successful_operations', 0)}
Failed Operations: {processing_stats.get('failed_operations', 0)}
Success Rate: {processing_stats.get('success_rate', 0):.2%}
Average Duration: {processing_stats.get('average_duration', 0):.2f}s

=== QUALITY STATISTICS ===
Total Assessments: {quality_stats.get('total_assessments', 0)}
Average Overall Score: {quality_stats.get('average_overall_score', 0):.2f}
Average Completeness: {quality_stats.get('average_completeness_score', 0):.2f}
Average Accuracy: {quality_stats.get('average_accuracy_score', 0):.2f}
Total Validation Issues: {quality_stats.get('total_validation_issues', 0)}

=== ERROR ANALYSIS ===
Total Errors: {error_analysis.get('total_errors', 0)}
Most Common Error: {error_analysis.get('most_common_error', 'None')}
Most Problematic Stage: {error_analysis.get('most_problematic_stage', 'None')}

=== SYSTEM HEALTH ===
Active Operations: {len(self.active_operations)}
Memory Usage: {self._get_current_memory_usage():.1f}MB
Log Entries: {len(self.processing_metrics) + len(self.quality_metrics) + len(self.error_log)}
"""
        
        return report
        
    def _generate_quality_report(self, metrics: QualityMetrics) -> str:
        """Generate a detailed quality report"""
        return f"""
Quality Assessment Report
Document ID: {metrics.document_id}
Timestamp: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

=== QUALITY SCORES ===
Overall Score: {metrics.overall_score:.2f}/100
Completeness Score: {metrics.completeness_score:.2f}/100
Accuracy Score: {metrics.accuracy_score:.2f}/100
Consistency Score: {metrics.consistency_score:.2f}/100
Compliance Score: {metrics.compliance_score:.2f}/100

=== PROCESSING METRICS ===
Processing Time: {metrics.processing_time:.2f}s

=== VALIDATION ISSUES ===
Total Issues: {len(metrics.validation_issues)}
{chr(10).join(f"- {issue}" for issue in metrics.validation_issues)}

=== RECOMMENDATIONS ===
{"✓ Document meets quality standards" if metrics.overall_score >= 80 else "⚠ Document requires review and improvement"}
"""
        
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0