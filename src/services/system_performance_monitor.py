"""
System Performance Monitor for QME System Refactor
Provides detailed performance monitoring and error reporting
"""

import time
import psutil
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

from ..services.comprehensive_quality_validation_service import QualityValidationResult


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class SystemResourceUsage:
    """System resource usage snapshot"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    timestamp: datetime


@dataclass
class ProcessingSession:
    """Processing session tracking"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    document_count: int
    success_count: int
    error_count: int
    total_processing_time: float
    avg_processing_time: float
    resource_usage: List[SystemResourceUsage]
    errors: List[Dict[str, Any]]


@dataclass
class ErrorReport:
    """Detailed error report"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    severity: str
    component: str
    document_id: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class SystemPerformanceMonitor:
    """
    Comprehensive system performance monitoring and error reporting
    """
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.logger = logging.getLogger(__name__)
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Performance tracking
        self.metrics_history = deque(maxlen=1000)
        self.resource_history = deque(maxlen=1000)
        self.processing_sessions = {}
        self.error_reports = deque(maxlen=500)
        
        # Performance thresholds
        self.performance_thresholds = {
            "max_processing_time": 30.0,  # seconds
            "max_cpu_percent": 80.0,
            "max_memory_percent": 85.0,
            "min_success_rate": 0.90
        }
        
        # Error categorization
        self.error_categories = {
            "extraction_error": "Document extraction failed",
            "template_error": "Template generation failed", 
            "validation_error": "Quality validation failed",
            "system_error": "System-level error",
            "configuration_error": "Configuration issue",
            "network_error": "Network connectivity issue"
        }
        
        # Initialize baseline metrics
        self._initialize_baseline_metrics()
    
    def _initialize_baseline_metrics(self):
        """Initialize baseline performance metrics"""
        self.baseline_metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    
    def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.is_monitoring:
            self.logger.warning("Monitoring already active")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("System performance monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous system monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("System performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect resource usage
                resource_usage = self._collect_resource_usage()
                self.resource_history.append(resource_usage)
                
                # Check for performance issues
                self._check_performance_thresholds(resource_usage)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_resource_usage(self) -> SystemResourceUsage:
        """Collect current system resource usage"""
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        
        return SystemResourceUsage(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_io_read_mb=disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
            disk_io_write_mb=disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
            timestamp=datetime.now()
        )
    
    def _check_performance_thresholds(self, resource_usage: SystemResourceUsage):
        """Check if performance thresholds are exceeded"""
        if resource_usage.cpu_percent > self.performance_thresholds["max_cpu_percent"]:
            self.record_performance_alert(
                "high_cpu_usage",
                f"CPU usage {resource_usage.cpu_percent:.1f}% exceeds threshold {self.performance_thresholds['max_cpu_percent']:.1f}%",
                {"cpu_percent": resource_usage.cpu_percent}
            )
        
        if resource_usage.memory_percent > self.performance_thresholds["max_memory_percent"]:
            self.record_performance_alert(
                "high_memory_usage",
                f"Memory usage {resource_usage.memory_percent:.1f}% exceeds threshold {self.performance_thresholds['max_memory_percent']:.1f}%",
                {"memory_percent": resource_usage.memory_percent}
            )
    
    @contextmanager
    def track_processing_session(self, session_id: str):
        """Context manager for tracking processing sessions"""
        session = ProcessingSession(
            session_id=session_id,
            start_time=datetime.now(),
            end_time=None,
            document_count=0,
            success_count=0,
            error_count=0,
            total_processing_time=0.0,
            avg_processing_time=0.0,
            resource_usage=[],
            errors=[]
        )
        
        self.processing_sessions[session_id] = session
        
        try:
            yield session
        finally:
            session.end_time = datetime.now()
            session_duration = (session.end_time - session.start_time).total_seconds()
            session.avg_processing_time = (
                session.total_processing_time / session.document_count 
                if session.document_count > 0 else 0
            )
            
            self.logger.info(f"Processing session {session_id} completed: "
                           f"{session.success_count}/{session.document_count} successful, "
                           f"avg time: {session.avg_processing_time:.2f}s")
    
    @contextmanager
    def track_document_processing(self, document_id: str, session_id: Optional[str] = None):
        """Context manager for tracking individual document processing"""
        start_time = time.time()
        start_resource_usage = self._collect_resource_usage()
        
        try:
            yield
            
            # Success case
            processing_time = time.time() - start_time
            end_resource_usage = self._collect_resource_usage()
            
            self.record_processing_success(
                document_id, processing_time, start_resource_usage, end_resource_usage
            )
            
            if session_id and session_id in self.processing_sessions:
                session = self.processing_sessions[session_id]
                session.document_count += 1
                session.success_count += 1
                session.total_processing_time += processing_time
                session.resource_usage.append(end_resource_usage)
            
        except Exception as e:
            # Error case
            processing_time = time.time() - start_time
            end_resource_usage = self._collect_resource_usage()
            
            error_report = self.record_processing_error(
                document_id, str(e), processing_time, start_resource_usage, end_resource_usage
            )
            
            if session_id and session_id in self.processing_sessions:
                session = self.processing_sessions[session_id]
                session.document_count += 1
                session.error_count += 1
                session.errors.append(asdict(error_report))
            
            raise
    
    def record_processing_success(self, document_id: str, processing_time: float,
                                start_usage: SystemResourceUsage, end_usage: SystemResourceUsage):
        """Record successful document processing"""
        metric = PerformanceMetric(
            name="document_processing_time",
            value=processing_time,
            unit="seconds",
            timestamp=datetime.now(),
            context={
                "document_id": document_id,
                "cpu_delta": end_usage.cpu_percent - start_usage.cpu_percent,
                "memory_delta": end_usage.memory_used_mb - start_usage.memory_used_mb,
                "success": True
            }
        )
        
        self.metrics_history.append(metric)
        
        # Check processing time threshold
        if processing_time > self.performance_thresholds["max_processing_time"]:
            self.record_performance_alert(
                "slow_processing",
                f"Document {document_id} processing time {processing_time:.2f}s exceeds threshold",
                {"document_id": document_id, "processing_time": processing_time}
            )
    
    def record_processing_error(self, document_id: str, error_message: str, 
                              processing_time: float, start_usage: SystemResourceUsage, 
                              end_usage: SystemResourceUsage) -> ErrorReport:
        """Record processing error with detailed context"""
        import traceback
        
        error_report = ErrorReport(
            error_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{document_id}",
            timestamp=datetime.now(),
            error_type=self._categorize_error(error_message),
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            context={
                "document_id": document_id,
                "processing_time": processing_time,
                "cpu_usage": end_usage.cpu_percent,
                "memory_usage": end_usage.memory_percent,
                "memory_delta": end_usage.memory_used_mb - start_usage.memory_used_mb
            },
            severity=self._determine_error_severity(error_message),
            component=self._identify_error_component(error_message),
            document_id=document_id
        )
        
        self.error_reports.append(error_report)
        
        # Log error based on severity
        if error_report.severity == "critical":
            self.logger.critical(f"Critical error processing {document_id}: {error_message}")
        elif error_report.severity == "high":
            self.logger.error(f"High severity error processing {document_id}: {error_message}")
        else:
            self.logger.warning(f"Error processing {document_id}: {error_message}")
        
        return error_report
    
    def record_performance_alert(self, alert_type: str, message: str, context: Dict[str, Any]):
        """Record performance alert"""
        alert_metric = PerformanceMetric(
            name=f"alert_{alert_type}",
            value=1.0,
            unit="count",
            timestamp=datetime.now(),
            context={"alert_message": message, **context}
        )
        
        self.metrics_history.append(alert_metric)
        self.logger.warning(f"Performance alert [{alert_type}]: {message}")
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content"""
        error_lower = error_message.lower()
        
        if "extraction" in error_lower or "openrouter" in error_lower:
            return "extraction_error"
        elif "template" in error_lower or "assembly" in error_lower:
            return "template_error"
        elif "validation" in error_lower or "quality" in error_lower:
            return "validation_error"
        elif "config" in error_lower or "setting" in error_lower:
            return "configuration_error"
        elif "network" in error_lower or "connection" in error_lower:
            return "network_error"
        else:
            return "system_error"
    
    def _determine_error_severity(self, error_message: str) -> str:
        """Determine error severity based on message content"""
        error_lower = error_message.lower()
        
        critical_keywords = ["critical", "fatal", "crash", "corruption"]
        high_keywords = ["failed", "error", "exception", "timeout"]
        
        if any(keyword in error_lower for keyword in critical_keywords):
            return "critical"
        elif any(keyword in error_lower for keyword in high_keywords):
            return "high"
        else:
            return "medium"
    
    def _identify_error_component(self, error_message: str) -> str:
        """Identify which component caused the error"""
        error_lower = error_message.lower()
        
        if "openrouter" in error_lower or "extraction" in error_lower:
            return "extraction_service"
        elif "template" in error_lower or "assembly" in error_lower:
            return "template_engine"
        elif "rag" in error_lower or "pipeline" in error_lower:
            return "rag_pipeline"
        elif "validation" in error_lower or "quality" in error_lower:
            return "quality_validator"
        else:
            return "unknown"
    
    def get_performance_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Filter metrics within time window
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        recent_resources = [r for r in self.resource_history if r.timestamp >= cutoff_time]
        recent_errors = [e for e in self.error_reports if e.timestamp >= cutoff_time]
        
        # Calculate processing metrics
        processing_times = [m.value for m in recent_metrics 
                          if m.name == "document_processing_time" and m.context.get("success")]
        
        # Calculate resource metrics
        cpu_usage = [r.cpu_percent for r in recent_resources]
        memory_usage = [r.memory_percent for r in recent_resources]
        
        # Error analysis
        error_by_type = defaultdict(int)
        error_by_severity = defaultdict(int)
        error_by_component = defaultdict(int)
        
        for error in recent_errors:
            error_by_type[error.error_type] += 1
            error_by_severity[error.severity] += 1
            error_by_component[error.component] += 1
        
        return {
            "time_window_hours": time_window_hours,
            "summary_timestamp": datetime.now().isoformat(),
            "processing_metrics": {
                "total_documents": len(processing_times),
                "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
                "min_processing_time": min(processing_times) if processing_times else 0,
                "max_processing_time": max(processing_times) if processing_times else 0,
                "documents_over_threshold": sum(1 for t in processing_times 
                                              if t > self.performance_thresholds["max_processing_time"])
            },
            "resource_metrics": {
                "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                "max_cpu_usage": max(cpu_usage) if cpu_usage else 0,
                "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                "max_memory_usage": max(memory_usage) if memory_usage else 0,
                "resource_alerts": len([m for m in recent_metrics if m.name.startswith("alert_")])
            },
            "error_metrics": {
                "total_errors": len(recent_errors),
                "errors_by_type": dict(error_by_type),
                "errors_by_severity": dict(error_by_severity),
                "errors_by_component": dict(error_by_component),
                "error_rate": len(recent_errors) / max(len(processing_times) + len(recent_errors), 1)
            },
            "session_metrics": {
                "active_sessions": len([s for s in self.processing_sessions.values() if s.end_time is None]),
                "completed_sessions": len([s for s in self.processing_sessions.values() if s.end_time is not None])
            }
        }
    
    def get_error_analysis(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get detailed error analysis"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_errors = [e for e in self.error_reports if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return {"message": "No errors in specified time window"}
        
        # Group errors by type and component
        error_patterns = defaultdict(list)
        for error in recent_errors:
            pattern_key = f"{error.error_type}_{error.component}"
            error_patterns[pattern_key].append(error)
        
        # Identify recurring issues
        recurring_issues = []
        for pattern, errors in error_patterns.items():
            if len(errors) >= 3:  # 3 or more similar errors
                recurring_issues.append({
                    "pattern": pattern,
                    "count": len(errors),
                    "first_occurrence": min(e.timestamp for e in errors).isoformat(),
                    "last_occurrence": max(e.timestamp for e in errors).isoformat(),
                    "sample_message": errors[0].error_message,
                    "affected_documents": list(set(e.document_id for e in errors if e.document_id))
                })
        
        # Critical errors requiring immediate attention
        critical_errors = [e for e in recent_errors if e.severity == "critical"]
        
        return {
            "time_window_hours": time_window_hours,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_errors": len(recent_errors),
            "critical_errors": len(critical_errors),
            "recurring_issues": recurring_issues,
            "critical_error_details": [
                {
                    "error_id": e.error_id,
                    "timestamp": e.timestamp.isoformat(),
                    "message": e.error_message,
                    "component": e.component,
                    "document_id": e.document_id
                }
                for e in critical_errors
            ],
            "recommendations": self._generate_error_recommendations(recent_errors)
        }
    
    def _generate_error_recommendations(self, errors: List[ErrorReport]) -> List[str]:
        """Generate recommendations based on error patterns"""
        recommendations = []
        
        # Analyze error types
        error_types = defaultdict(int)
        components = defaultdict(int)
        
        for error in errors:
            error_types[error.error_type] += 1
            components[error.component] += 1
        
        # Generate specific recommendations
        if error_types.get("extraction_error", 0) > 3:
            recommendations.append("High number of extraction errors - review OpenRouter configuration and prompts")
        
        if error_types.get("template_error", 0) > 2:
            recommendations.append("Template generation issues detected - validate template configurations")
        
        if error_types.get("network_error", 0) > 1:
            recommendations.append("Network connectivity issues - check API endpoints and retry logic")
        
        if components.get("extraction_service", 0) > 5:
            recommendations.append("Extraction service instability - consider implementing circuit breaker pattern")
        
        # Resource-based recommendations
        high_memory_errors = [e for e in errors if e.context.get("memory_usage", 0) > 80]
        if high_memory_errors:
            recommendations.append("High memory usage during errors - optimize memory management")
        
        return recommendations
    
    def save_performance_report(self, output_path: Optional[str] = None) -> str:
        """Save comprehensive performance report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/performance_reports/system_performance_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate comprehensive report
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_status": self.is_monitoring,
            "performance_summary_24h": self.get_performance_summary(24),
            "performance_summary_1h": self.get_performance_summary(1),
            "error_analysis_24h": self.get_error_analysis(24),
            "system_configuration": {
                "performance_thresholds": self.performance_thresholds,
                "monitoring_interval": self.monitoring_interval
            },
            "baseline_metrics": self.baseline_metrics,
            "active_sessions": {
                session_id: asdict(session) for session_id, session in self.processing_sessions.items()
                if session.end_time is None
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Performance report saved to {output_file}")
        return str(output_file)