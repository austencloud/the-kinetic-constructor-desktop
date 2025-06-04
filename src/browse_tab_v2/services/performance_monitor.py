"""
Performance monitoring service for browse tab v2.

This service provides comprehensive performance monitoring,
metrics collection, and performance analysis capabilities.
"""

import time
import logging
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque, defaultdict
from contextlib import contextmanager
import uuid

from ..core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    name: str
    value: float
    timestamp: float
    unit: str = "ms"
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimerInfo:
    """Information about an active timer."""

    timer_id: str
    operation_name: str
    start_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring service.

    Features:
    - Operation timing
    - Memory usage tracking
    - Frame rate monitoring
    - Cache performance analysis
    - System resource monitoring
    - Performance alerts
    """

    def __init__(self, config: BrowseTabConfig = None):
        self.config = config or BrowseTabConfig()

        # Active timers
        self._active_timers: Dict[str, TimerInfo] = {}

        # Metrics storage
        self._metrics: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self._metrics_by_category: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )

        # Frame rate tracking
        self._frame_times: deque = deque(maxlen=60)  # Last 60 frames
        self._last_frame_time: float = 0

        # Memory tracking
        self._memory_samples: deque = deque(maxlen=100)
        self._process = psutil.Process(os.getpid())

        # Performance thresholds
        self._thresholds = {
            "frame_time_ms": 16.67,  # 60 FPS
            "memory_mb": 500,  # 500 MB
            "cache_hit_rate": 80,  # 80%
            "load_time_ms": 1000,  # 1 second
        }

        # Alerts
        self._alerts: List[Dict[str, Any]] = []
        self._alert_callbacks: List[callable] = []

        logger.info("PerformanceMonitor initialized")

    def start_timer(self, operation_name: str, metadata: Dict[str, Any] = None) -> str:
        """Start timing an operation. Returns timer ID."""
        timer_id = str(uuid.uuid4())

        timer_info = TimerInfo(
            timer_id=timer_id,
            operation_name=operation_name,
            start_time=time.perf_counter(),
            metadata=metadata or {},
        )

        self._active_timers[timer_id] = timer_info

        logger.debug(f"Started timer: {operation_name} ({timer_id})")
        return timer_id

    def stop_timer(self, timer_id: str) -> float:
        """Stop timer and return duration in seconds."""
        if timer_id not in self._active_timers:
            logger.warning(f"Timer not found: {timer_id}")
            return 0.0

        timer_info = self._active_timers.pop(timer_id)
        duration = time.perf_counter() - timer_info.start_time

        # Record metric
        self.record_metric(
            f"{timer_info.operation_name}_duration",
            duration * 1000,  # Convert to milliseconds
            "ms",
            "timing",
            timer_info.metadata,
        )

        # Check for performance alerts
        self._check_performance_alert(timer_info.operation_name, duration * 1000)

        logger.debug(f"Stopped timer: {timer_info.operation_name} ({duration:.3f}s)")
        return duration

    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        category: str = "general",
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=metric_name,
            value=value,
            timestamp=time.time(),
            unit=unit,
            category=category,
            metadata=metadata or {},
        )

        # Store metric
        self._metrics.append(metric)
        self._metrics_by_category[category].append(metric)

        logger.debug(f"Recorded metric: {metric_name} = {value} {unit}")

    def record_frame_time(self, frame_time_ms: float) -> None:
        """Record frame rendering time."""
        self._frame_times.append(frame_time_ms)
        self._last_frame_time = time.time()

        # Record as metric
        self.record_metric("frame_time", frame_time_ms, "ms", "rendering")

        # Check for frame rate alerts
        if frame_time_ms > self._thresholds["frame_time_ms"]:
            self._trigger_alert(
                "frame_rate",
                f"Frame time {frame_time_ms:.1f}ms exceeds 60fps target",
                {"frame_time_ms": frame_time_ms},
            )

    def record_memory_usage(self) -> None:
        """Record current memory usage."""
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            self._memory_samples.append(memory_mb)

            # Record as metric
            self.record_metric("memory_usage", memory_mb, "MB", "memory")

            # Check for memory alerts
            if memory_mb > self._thresholds["memory_mb"]:
                self._trigger_alert(
                    "memory",
                    f"Memory usage {memory_mb:.1f}MB exceeds threshold",
                    {"memory_mb": memory_mb},
                )

        except Exception as e:
            logger.error(f"Failed to record memory usage: {e}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            # Calculate frame rate statistics
            frame_stats = self._calculate_frame_stats()

            # Calculate memory statistics
            memory_stats = self._calculate_memory_stats()

            # Calculate timing statistics
            timing_stats = self._calculate_timing_stats()

            # Get system information
            system_stats = self._get_system_stats()

            report = {
                "timestamp": time.time(),
                "frame_rate": frame_stats,
                "memory": memory_stats,
                "timing": timing_stats,
                "system": system_stats,
                "alerts": self._alerts[-10:],  # Last 10 alerts
                "active_timers": len(self._active_timers),
                "total_metrics": len(self._metrics),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {}

    def get_metrics_by_category(self, category: str) -> List[PerformanceMetric]:
        """Get metrics by category."""
        return list(self._metrics_by_category.get(category, []))

    def get_recent_metrics(self, count: int = 50) -> List[PerformanceMetric]:
        """Get recent metrics."""
        return list(self._metrics)[-count:]

    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for performance alerts."""
        self._alert_callbacks.append(callback)

    def set_threshold(self, metric_name: str, threshold_value: float) -> None:
        """Set performance threshold."""
        self._thresholds[metric_name] = threshold_value
        logger.info(f"Set threshold: {metric_name} = {threshold_value}")

    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self._metrics.clear()
        self._metrics_by_category.clear()
        self._frame_times.clear()
        self._memory_samples.clear()
        self._alerts.clear()
        logger.info("Performance metrics cleared")

    @contextmanager
    def measure_operation(self, operation_name: str, metadata: Dict[str, Any] = None):
        """Context manager for measuring operation duration."""
        timer_id = self.start_timer(operation_name, metadata)
        try:
            yield timer_id
        finally:
            self.stop_timer(timer_id)

    def _calculate_frame_stats(self) -> Dict[str, Any]:
        """Calculate frame rate statistics."""
        if not self._frame_times:
            return {
                "fps": 0,
                "avg_frame_time": 0,
                "min_frame_time": 0,
                "max_frame_time": 0,
            }

        frame_times = list(self._frame_times)
        avg_frame_time = sum(frame_times) / len(frame_times)
        fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0

        return {
            "fps": fps,
            "avg_frame_time": avg_frame_time,
            "min_frame_time": min(frame_times),
            "max_frame_time": max(frame_times),
            "frame_count": len(frame_times),
        }

    def _calculate_memory_stats(self) -> Dict[str, Any]:
        """Calculate memory usage statistics."""
        if not self._memory_samples:
            return {"current_mb": 0, "avg_mb": 0, "peak_mb": 0}

        memory_samples = list(self._memory_samples)

        return {
            "current_mb": memory_samples[-1],
            "avg_mb": sum(memory_samples) / len(memory_samples),
            "peak_mb": max(memory_samples),
            "min_mb": min(memory_samples),
        }

    def _calculate_timing_stats(self) -> Dict[str, Any]:
        """Calculate timing statistics by operation."""
        timing_metrics = self.get_metrics_by_category("timing")

        stats_by_operation = {}
        for metric in timing_metrics:
            operation = metric.name.replace("_duration", "")

            if operation not in stats_by_operation:
                stats_by_operation[operation] = []

            stats_by_operation[operation].append(metric.value)

        # Calculate statistics for each operation
        timing_stats = {}
        for operation, times in stats_by_operation.items():
            if times:
                timing_stats[operation] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                }

        return timing_stats

    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "memory_total_mb": memory.total / (1024 * 1024),
            }

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}

    def _check_performance_alert(self, operation_name: str, duration_ms: float) -> None:
        """Check if operation duration triggers an alert."""
        threshold_key = f"{operation_name}_ms"

        if threshold_key in self._thresholds:
            threshold = self._thresholds[threshold_key]
            if duration_ms > threshold:
                self._trigger_alert(
                    "timing",
                    f"{operation_name} took {duration_ms:.1f}ms (threshold: {threshold}ms)",
                    {
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "threshold_ms": threshold,
                    },
                )

    def _trigger_alert(
        self, alert_type: str, message: str, metadata: Dict[str, Any]
    ) -> None:
        """Trigger a performance alert."""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "metadata": metadata,
        }

        self._alerts.append(alert)

        # Keep only recent alerts
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-50:]

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.warning(f"Performance alert: {message}")

    def get_current_fps(self) -> float:
        """Get current FPS based on recent frame times."""
        if not self._frame_times:
            return 0.0

        recent_frames = list(self._frame_times)[-10:]  # Last 10 frames
        if not recent_frames:
            return 0.0

        avg_frame_time = sum(recent_frames) / len(recent_frames)
        return 1000 / avg_frame_time if avg_frame_time > 0 else 0.0

    def is_performance_healthy(self) -> bool:
        """Check if overall performance is healthy."""
        try:
            # Check frame rate
            fps = self.get_current_fps()
            if fps < 30:  # Below 30 FPS is concerning
                return False

            # Check memory usage
            if self._memory_samples:
                current_memory = self._memory_samples[-1]
                if current_memory > self._thresholds["memory_mb"]:
                    return False

            # Check recent alerts
            recent_alerts = [
                a for a in self._alerts if time.time() - a["timestamp"] < 60
            ]  # Last minute
            if len(recent_alerts) > 5:  # More than 5 alerts in last minute
                return False

            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
