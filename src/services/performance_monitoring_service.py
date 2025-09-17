"""
Performance Monitoring Service for QME System

This service provides comprehensive performance monitoring and error reporting
with detailed quality assessments for the refactored QME system.
"""

import logging
import time
import psutil
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
import statistics
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    PROCESSING_TIME = "processing_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ERROR_RATE = "error_rate"
    QUALITY_SCORE = "quality_score"
    THROUGHPUT = "throughput"


class AlertLevel(Enum):
    """Alert levels for performance issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    component: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    level: AlertLevel
    message: str
    timestamp: datetime
    component: str
    metric_type: MetricType
    threshold_value: float
    actual_value: float
    suggested_action: Optional[str] = None


@dataclass
class SystemHealthReport:
    """System health report"""
    timestamp: datetime
    overall_health_score: float
    component_health: Dict[str, float]
    active_alerts: List[PerformanceAlert]
    performance_summary: Dict[str, Any]
    recommendations: List[str]


class PerformanceMonitoringService:
    """Comprehensive performance monitoring service"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/monitoring/performance_config.yaml"
        self.metrics_storage = defaultdict(lambda: deque(maxlen=1000))
        self.alerts = deque(maxlen=100)
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Performance thresholds
        self.thresholds = {
            MetricType.PROCESSING_TIME: 30.0,  # seconds
            MetricType.MEMORY_USAGE: 80.0,     # percentage
            MetricType.CPU_USAGE: 85.0,        # percentage
            MetricType.ERROR_RATE: 5.0,        # percentage
            MetricType.QUALITY_SCORE: 0.75,    # minimum score
            MetricType.THROUGHPUT: 1.0         # documents per minute
        }
        
        # Component registry
        self.monitored_components = {
            'extraction_service': 'OpenRouter Extraction Service',
            'rag_pipeline': 'Enhanced RAG Pipeline',
            'assembly_engine': 'Template Assembly Engine',
            'quality_validator': 'Quality Validation Service',
            'overall_system': 'Overall System Performance'
        }
        
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start background performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_alert_conditions()
                time.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric(
                MetricType.MEMORY_USAGE,
                memory.percent,
                'system',
                {'available_gb': memory.available / (1024**3)}
            )
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric(
                MetricType.CPU_USAGE,
                cpu_percent,
                'system',
                {'cpu_count': psutil.cpu_count()}
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_metric(self, metric_type: MetricType, value: float, 
                     component: str, metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            component=component,
            metadata=metadata or {}
        )
        
        self.metrics_storage[f"{component}_{metric_type.value}"].append(metric)
        
        # Check for immediate alerts
        self._check_metric_threshold(metric)
    
    def _check_metric_threshold(self, metric: PerformanceMetric):
        """Check if metric exceeds threshold and create alert if needed"""
        threshold = self.thresholds.get(metric.metric_type)
        if threshold is None:
            return
        
        alert_needed = False
        alert_level = AlertLevel.INFO
        
        if metric.metric_type in [MetricType.PROCESSING_TIME, MetricType.MEMORY_USAGE, 
                                 MetricType.CPU_USAGE, MetricType.ERROR_RATE]:
            if metric.value > threshold:
                alert_needed = True
                if metric.value > threshold * 1.5:
                    alert_level = AlertLevel.CRITICAL
                elif metric.value > threshold * 1.2:
                    alert_level = AlertLevel.ERROR
                else:
                    alert_level = AlertLevel.WARNING
        
        elif metric.metric_type == MetricType.QUALITY_SCORE:
            if metric.value < threshold:
                alert_needed = True
                if metric.value < threshold * 0.8:
                    alert_level = AlertLevel.CRITICAL
                elif metric.value < threshold * 0.9:
                    alert_level = AlertLevel.ERROR
                else:
                    alert_level = AlertLevel.WARNING
        
        if alert_needed:
            self._create_alert(metric, alert_level, threshold)
    
    def _create_alert(self, metric: PerformanceMetric, level: AlertLevel, threshold: float):
        """Create performance alert"""
        alert_id = f"{metric.component}_{metric.metric_type.value}_{int(time.time())}"
        
        message = f"{metric.component}: {metric.metric_type.value} = {metric.value:.2f}"
        if metric.metric_type == MetricType.QUALITY_SCORE:
            message += f" (below threshold {threshold:.2f})"
        else:
            message += f" (exceeds threshold {threshold:.2f})"
        
        suggested_action = self._get_suggested_action(metric.metric_type, metric.component)
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            level=level,
            message=message,
            timestamp=metric.timestamp,
            component=metric.component,
            metric_type=metric.metric_type,
            threshold_value=threshold,
            actual_value=metric.value,
            suggested_action=suggested_action
        )
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {message}")
    
    def _get_suggested_action(self, metric_type: MetricType, component: str) -> str:
        """Get suggested action for performance issue"""
        suggestions = {
            MetricType.PROCESSING_TIME: {
                'extraction_service': 'Consider optimizing OpenRouter API calls or implementing caching',
                'rag_pipeline': 'Review vector search performance and context retrieval efficiency',
                'assembly_engine': 'Optimize template assembly process and reduce I/O operations',
                'quality_validator': 'Streamline validation rules and reduce redundant checks',
                'default': 'Review component performance and optimize bottlenecks'
            },
            MetricType.MEMORY_USAGE: {
                'default': 'Monitor memory leaks, optimize data structures, consider garbage collection'
            },
            MetricType.CPU_USAGE: {
                'default': 'Review CPU-intensive operations, consider parallel processing'
            },
            MetricType.ERROR_RATE: {
                'default': 'Investigate error patterns, improve error handling and retry logic'
            },
            MetricType.QUALITY_SCORE: {
                'default': 'Review quality validation rules, improve extraction accuracy'
            }
        }
        
        component_suggestions = suggestions.get(metric_type, {})
        return component_suggestions.get(component, component_suggestions.get('default', 'Review performance'))
    
    def _check_alert_conditions(self):
        """Check for complex alert conditions"""
        # Check for sustained high resource usage
        self._check_sustained_high_usage()
        
        # Check for error rate trends
        self._check_error_rate_trends()
        
        # Check for quality degradation
        self._check_quality_degradation()
    
    def _check_sustained_high_usage(self):
        """Check for sustained high resource usage"""
        for component in self.monitored_components:
            # Check memory usage over last 5 minutes
            memory_metrics = [m for m in self.metrics_storage[f"{component}_memory_usage"] 
                            if (datetime.now() - m.timestamp).total_seconds() < 300]
            
            if len(memory_metrics) >= 5:
                avg_memory = statistics.mean(m.value for m in memory_metrics)
                if avg_memory > self.thresholds[MetricType.MEMORY_USAGE]:
                    self._create_sustained_usage_alert(component, 'memory', avg_memory)
    
    def _check_error_rate_trends(self):
        """Check for increasing error rate trends"""
        for component in self.monitored_components:
            error_metrics = [m for m in self.metrics_storage[f"{component}_error_rate"] 
                           if (datetime.now() - m.timestamp).total_seconds() < 600]  # Last 10 minutes
            
            if len(error_metrics) >= 3:
                recent_errors = [m.value for m in error_metrics[-3:]]
                if all(recent_errors[i] <= recent_errors[i+1] for i in range(len(recent_errors)-1)):
                    # Error rate is increasing
                    latest_rate = recent_errors[-1]
                    if latest_rate > self.thresholds[MetricType.ERROR_RATE] * 0.5:
                        self._create_trend_alert(component, 'error_rate', latest_rate, 'increasing')
    
    def _check_quality_degradation(self):
        """Check for quality score degradation"""
        for component in self.monitored_components:
            quality_metrics = [m for m in self.metrics_storage[f"{component}_quality_score"] 
                             if (datetime.now() - m.timestamp).total_seconds() < 1800]  # Last 30 minutes
            
            if len(quality_metrics) >= 5:
                recent_quality = [m.value for m in quality_metrics[-5:]]
                avg_quality = statistics.mean(recent_quality)
                
                if avg_quality < self.thresholds[MetricType.QUALITY_SCORE]:
                    self._create_quality_degradation_alert(component, avg_quality)
    
    def _create_sustained_usage_alert(self, component: str, resource: str, avg_value: float):
        """Create alert for sustained high resource usage"""
        alert_id = f"sustained_{resource}_{component}_{int(time.time())}"
        message = f"Sustained high {resource} usage in {component}: {avg_value:.2f}%"
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            level=AlertLevel.WARNING,
            message=message,
            timestamp=datetime.now(),
            component=component,
            metric_type=MetricType.MEMORY_USAGE if resource == 'memory' else MetricType.CPU_USAGE,
            threshold_value=self.thresholds[MetricType.MEMORY_USAGE if resource == 'memory' else MetricType.CPU_USAGE],
            actual_value=avg_value,
            suggested_action=f"Investigate {resource} usage patterns in {component}"
        )
        
        self.alerts.append(alert)
    
    def _create_trend_alert(self, component: str, metric: str, value: float, trend: str):
        """Create alert for metric trends"""
        alert_id = f"trend_{metric}_{component}_{int(time.time())}"
        message = f"{trend.capitalize()} {metric} trend in {component}: current {value:.2f}"
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            level=AlertLevel.WARNING,
            message=message,
            timestamp=datetime.now(),
            component=component,
            metric_type=MetricType.ERROR_RATE,
            threshold_value=self.thresholds[MetricType.ERROR_RATE],
            actual_value=value,
            suggested_action=f"Investigate {trend} {metric} in {component}"
        )
        
        self.alerts.append(alert)
    
    def _create_quality_degradation_alert(self, component: str, avg_quality: float):
        """Create alert for quality degradation"""
        alert_id = f"quality_degradation_{component}_{int(time.time())}"
        message = f"Quality degradation in {component}: average score {avg_quality:.3f}"
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            level=AlertLevel.ERROR,
            message=message,
            timestamp=datetime.now(),
            component=component,
            metric_type=MetricType.QUALITY_SCORE,
            threshold_value=self.thresholds[MetricType.QUALITY_SCORE],
            actual_value=avg_quality,
            suggested_action=f"Review quality validation and processing in {component}"
        )
        
        self.alerts.append(alert)
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for specified time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        summary = {
            'time_window_minutes': time_window_minutes,
            'component_performance': {},
            'system_performance': {},
            'alert_summary': {},
            'recommendations': []
        }
        
        # Analyze component performance
        for component in self.monitored_components:
            component_summary = self._analyze_component_performance(component, cutoff_time)
            summary['component_performance'][component] = component_summary
        
        # Analyze system performance
        summary['system_performance'] = self._analyze_system_performance(cutoff_time)
        
        # Analyze alerts
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        summary['alert_summary'] = {
            'total_alerts': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
            'error_alerts': len([a for a in recent_alerts if a.level == AlertLevel.ERROR]),
            'warning_alerts': len([a for a in recent_alerts if a.level == AlertLevel.WARNING])
        }
        
        # Generate recommendations
        summary['recommendations'] = self._generate_performance_recommendations(summary)
        
        return summary
    
    def _analyze_component_performance(self, component: str, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze performance for a specific component"""
        component_data = {
            'processing_time': {'avg': 0, 'max': 0, 'count': 0},
            'quality_score': {'avg': 0, 'min': 1.0, 'count': 0},
            'error_rate': {'avg': 0, 'max': 0, 'count': 0},
            'health_score': 1.0
        }
        
        # Analyze processing time
        processing_metrics = [m for m in self.metrics_storage[f"{component}_processing_time"] 
                            if m.timestamp >= cutoff_time]
        if processing_metrics:
            times = [m.value for m in processing_metrics]
            component_data['processing_time'] = {
                'avg': statistics.mean(times),
                'max': max(times),
                'count': len(times)
            }
        
        # Analyze quality scores
        quality_metrics = [m for m in self.metrics_storage[f"{component}_quality_score"] 
                         if m.timestamp >= cutoff_time]
        if quality_metrics:
            scores = [m.value for m in quality_metrics]
            component_data['quality_score'] = {
                'avg': statistics.mean(scores),
                'min': min(scores),
                'count': len(scores)
            }
        
        # Analyze error rates
        error_metrics = [m for m in self.metrics_storage[f"{component}_error_rate"] 
                       if m.timestamp >= cutoff_time]
        if error_metrics:
            rates = [m.value for m in error_metrics]
            component_data['error_rate'] = {
                'avg': statistics.mean(rates),
                'max': max(rates),
                'count': len(rates)
            }
        
        # Calculate health score
        health_factors = []
        
        if component_data['processing_time']['avg'] > 0:
            time_factor = min(1.0, self.thresholds[MetricType.PROCESSING_TIME] / component_data['processing_time']['avg'])
            health_factors.append(time_factor)
        
        if component_data['quality_score']['avg'] > 0:
            quality_factor = component_data['quality_score']['avg']
            health_factors.append(quality_factor)
        
        if component_data['error_rate']['avg'] >= 0:
            error_factor = max(0.0, 1.0 - (component_data['error_rate']['avg'] / 100.0))
            health_factors.append(error_factor)
        
        if health_factors:
            component_data['health_score'] = statistics.mean(health_factors)
        
        return component_data
    
    def _analyze_system_performance(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze overall system performance"""
        system_data = {
            'memory_usage': {'avg': 0, 'max': 0},
            'cpu_usage': {'avg': 0, 'max': 0},
            'overall_health': 1.0
        }
        
        # Analyze memory usage
        memory_metrics = [m for m in self.metrics_storage["system_memory_usage"] 
                        if m.timestamp >= cutoff_time]
        if memory_metrics:
            memory_values = [m.value for m in memory_metrics]
            system_data['memory_usage'] = {
                'avg': statistics.mean(memory_values),
                'max': max(memory_values)
            }
        
        # Analyze CPU usage
        cpu_metrics = [m for m in self.metrics_storage["system_cpu_usage"] 
                     if m.timestamp >= cutoff_time]
        if cpu_metrics:
            cpu_values = [m.value for m in cpu_metrics]
            system_data['cpu_usage'] = {
                'avg': statistics.mean(cpu_values),
                'max': max(cpu_values)
            }
        
        # Calculate overall health
        health_factors = []
        
        if system_data['memory_usage']['avg'] > 0:
            memory_factor = max(0.0, 1.0 - (system_data['memory_usage']['avg'] / 100.0))
            health_factors.append(memory_factor)
        
        if system_data['cpu_usage']['avg'] > 0:
            cpu_factor = max(0.0, 1.0 - (system_data['cpu_usage']['avg'] / 100.0))
            health_factors.append(cpu_factor)
        
        if health_factors:
            system_data['overall_health'] = statistics.mean(health_factors)
        
        return system_data
    
    def _generate_performance_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on analysis"""
        recommendations = []
        
        # Check component health
        for component, data in summary['component_performance'].items():
            health_score = data.get('health_score', 1.0)
            if health_score < 0.7:
                recommendations.append(f"Critical: {component} health score is low ({health_score:.2f})")
            elif health_score < 0.8:
                recommendations.append(f"Warning: {component} performance needs attention ({health_score:.2f})")
        
        # Check system health
        system_health = summary['system_performance'].get('overall_health', 1.0)
        if system_health < 0.7:
            recommendations.append(f"Critical: System health is low ({system_health:.2f})")
        
        # Check alert levels
        alert_summary = summary['alert_summary']
        if alert_summary.get('critical_alerts', 0) > 0:
            recommendations.append(f"Immediate action required: {alert_summary['critical_alerts']} critical alerts")
        
        if alert_summary.get('error_alerts', 0) > 3:
            recommendations.append(f"Review error patterns: {alert_summary['error_alerts']} error alerts")
        
        # Resource usage recommendations
        memory_usage = summary['system_performance'].get('memory_usage', {}).get('avg', 0)
        if memory_usage > 80:
            recommendations.append(f"High memory usage detected ({memory_usage:.1f}%) - consider optimization")
        
        cpu_usage = summary['system_performance'].get('cpu_usage', {}).get('avg', 0)
        if cpu_usage > 80:
            recommendations.append(f"High CPU usage detected ({cpu_usage:.1f}%) - review processing efficiency")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable parameters")
        
        return recommendations
    
    def generate_health_report(self) -> SystemHealthReport:
        """Generate comprehensive system health report"""
        summary = self.get_performance_summary(60)  # Last hour
        
        # Calculate overall health score
        component_health = {}
        health_scores = []
        
        for component, data in summary['component_performance'].items():
            health_score = data.get('health_score', 1.0)
            component_health[component] = health_score
            health_scores.append(health_score)
        
        system_health = summary['system_performance'].get('overall_health', 1.0)
        health_scores.append(system_health)
        
        overall_health = statistics.mean(health_scores) if health_scores else 1.0
        
        # Get recent alerts
        recent_alerts = [a for a in self.alerts 
                        if (datetime.now() - a.timestamp).total_seconds() < 3600]  # Last hour
        
        return SystemHealthReport(
            timestamp=datetime.now(),
            overall_health_score=overall_health,
            component_health=component_health,
            active_alerts=recent_alerts,
            performance_summary=summary,
            recommendations=summary['recommendations']
        )
    
    def export_performance_data(self, output_path: str, time_window_hours: int = 24):
        """Export performance data to file"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'time_window_hours': time_window_hours,
            'metrics': {},
            'alerts': [],
            'summary': self.get_performance_summary(time_window_hours * 60)
        }
        
        # Export metrics
        for key, metrics in self.metrics_storage.items():
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            export_data['metrics'][key] = [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'value': m.value,
                    'metadata': m.metadata
                }
                for m in recent_metrics
            ]
        
        # Export alerts
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        export_data['alerts'] = [
            {
                'alert_id': a.alert_id,
                'level': a.level.value,
                'message': a.message,
                'timestamp': a.timestamp.isoformat(),
                'component': a.component,
                'metric_type': a.metric_type.value,
                'threshold_value': a.threshold_value,
                'actual_value': a.actual_value,
                'suggested_action': a.suggested_action
            }
            for a in recent_alerts
        ]
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Performance data exported to {output_path}")


# Context manager for performance monitoring
class PerformanceMonitor:
    """Context manager for monitoring operation performance"""
    
    def __init__(self, monitoring_service: PerformanceMonitoringService, 
                 component: str, operation: str):
        self.monitoring_service = monitoring_service
        self.component = component
        self.operation = operation
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        self.start_time = time.time()
        try:
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / (1024 * 1024)  # MB
        except:
            self.start_memory = None
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Record processing time
        processing_time = time.time() - self.start_time
        self.monitoring_service.record_metric(
            MetricType.PROCESSING_TIME,
            processing_time,
            self.component,
            {'operation': self.operation}
        )
        
        # Record memory usage if available
        if self.start_memory:
            try:
                process = psutil.Process()
                end_memory = process.memory_info().rss / (1024 * 1024)  # MB
                memory_delta = end_memory - self.start_memory
                self.monitoring_service.record_metric(
                    MetricType.MEMORY_USAGE,
                    memory_delta,
                    self.component,
                    {'operation': self.operation, 'memory_delta_mb': memory_delta}
                )
            except:
                pass
        
        # Record error if exception occurred
        if exc_type is not None:
            self.monitoring_service.record_metric(
                MetricType.ERROR_RATE,
                1.0,  # Error occurred
                self.component,
                {'operation': self.operation, 'error_type': exc_type.__name__}
            )
        else:
            self.monitoring_service.record_metric(
                MetricType.ERROR_RATE,
                0.0,  # No error
                self.component,
                {'operation': self.operation}
            )