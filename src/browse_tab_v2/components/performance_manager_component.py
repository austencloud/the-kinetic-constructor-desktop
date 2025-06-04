"""
Performance Manager Component - Modular Architecture

Extracted from browse_tab_view.py to provide focused performance tracking functionality.
Handles all performance-related operations including metrics collection, monitoring,
and optimization tracking.

Responsibilities:
- User-perceived performance tracking
- Navigation click performance monitoring
- Thumbnail interaction performance tracking
- Animation performance metrics
- Performance optimization recommendations
"""

import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer, pyqtSignal

from ..core.interfaces import BrowseTabConfig
from ..debug.window_resize_tracker import track_component, log_main_window_change

logger = logging.getLogger(__name__)


class PerformanceManagerComponent(QWidget):
    """
    Modular performance manager component handling performance tracking and optimization.
    
    This component encapsulates all performance-related operations and provides
    a clean interface for monitoring and optimizing application performance.
    """
    
    # Signals for parent coordination
    performance_warning = pyqtSignal(str, float)  # operation, time_ms
    performance_report = pyqtSignal(dict)  # performance_metrics
    
    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)
        
        self.config = config or BrowseTabConfig()
        
        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._interaction_timers: Dict[str, Dict] = {}
        self._performance_metrics = {
            "navigation_clicks": [],
            "scroll_events": [],
            "thumbnail_clicks": [],
            "animation_starts": [],
            "image_loads": [],
        }
        self._max_metric_history = 100
        
        # Performance targets (user-perceived)
        self._targets = {
            "navigation_response": 100,  # 100ms for navigation clicks
            "scroll_smoothness": 16.67,  # 60fps scrolling
            "thumbnail_response": 200,   # 200ms for thumbnail clicks
            "animation_start": 50,       # 50ms for animation start
            "image_load": 500,          # 500ms for image loading
        }
        
        # Monitoring state
        self._monitoring_enabled = True
        self._warning_threshold_multiplier = 2.0  # Warn when 2x target time
        
        track_component("PerformanceManagerComponent_Initial", self, "Constructor start")
        log_main_window_change("PerformanceManagerComponent constructor start")
        
        self._setup_monitoring()
        
        track_component("PerformanceManagerComponent_Complete", self, "Constructor complete")
        log_main_window_change("PerformanceManagerComponent constructor complete")
        logger.info("PerformanceManagerComponent initialized")
    
    def _setup_monitoring(self):
        """Setup performance monitoring systems."""
        self._performance_timer.start()
        
        # Setup periodic performance reporting
        self._report_timer = QTimer()
        self._report_timer.timeout.connect(self._generate_performance_report)
        self._report_timer.start(30000)  # Report every 30 seconds
        
        logger.debug("Performance monitoring systems initialized")
    
    # Navigation performance tracking
    def track_navigation_click_performance(self, section_id: str) -> str:
        """Start tracking navigation click performance."""
        interaction_id = f"nav_click_{section_id}_{self._performance_timer.elapsed()}"
        self._interaction_timers[interaction_id] = {
            "start_time": self._performance_timer.elapsed(),
            "operation": "navigation_click",
            "section_id": section_id,
            "phase": "click_received",
        }
        
        logger.debug(f"Started tracking navigation click: {section_id}")
        return interaction_id
    
    def complete_navigation_performance_tracking(self, interaction_id: str):
        """Complete navigation performance tracking and record metrics."""
        if interaction_id not in self._interaction_timers:
            return
        
        timer_data = self._interaction_timers[interaction_id]
        end_time = self._performance_timer.elapsed()
        total_time = end_time - timer_data["start_time"]
        
        # Record navigation click time
        self._performance_metrics["navigation_clicks"].append(total_time)
        self._trim_metric_history("navigation_clicks")
        
        # Check against target
        target = self._targets["navigation_response"]
        if total_time > target * self._warning_threshold_multiplier:
            logger.warning(
                f"Slow navigation click: {total_time:.1f}ms (target: {target:.1f}ms) "
                f"for section {timer_data.get('section_id', 'unknown')}"
            )
            self.performance_warning.emit("navigation_click", total_time)
        else:
            logger.debug(
                f"Navigation click performance: {total_time:.1f}ms for section {timer_data.get('section_id', 'unknown')}"
            )
        
        # Clean up
        del self._interaction_timers[interaction_id]
    
    # Thumbnail performance tracking
    def track_thumbnail_click_performance(self, sequence_id: str) -> str:
        """Start tracking thumbnail click performance."""
        interaction_id = f"thumb_click_{sequence_id}_{self._performance_timer.elapsed()}"
        self._interaction_timers[interaction_id] = {
            "start_time": self._performance_timer.elapsed(),
            "operation": "thumbnail_click",
            "sequence_id": sequence_id,
            "phase": "click_received",
        }
        
        logger.debug(f"Started tracking thumbnail click: {sequence_id}")
        return interaction_id
    
    def complete_thumbnail_performance_tracking(self, interaction_id: str):
        """Complete thumbnail performance tracking and record metrics."""
        if interaction_id not in self._interaction_timers:
            return
        
        timer_data = self._interaction_timers[interaction_id]
        end_time = self._performance_timer.elapsed()
        total_time = end_time - timer_data["start_time"]
        
        # Record thumbnail click time
        self._performance_metrics["thumbnail_clicks"].append(total_time)
        self._trim_metric_history("thumbnail_clicks")
        
        # Check against target
        target = self._targets["thumbnail_response"]
        if total_time > target * self._warning_threshold_multiplier:
            logger.warning(
                f"Slow thumbnail click: {total_time:.1f}ms (target: {target:.1f}ms) "
                f"for sequence {timer_data.get('sequence_id', 'unknown')}"
            )
            self.performance_warning.emit("thumbnail_click", total_time)
        else:
            logger.debug(
                f"Thumbnail click performance: {total_time:.1f}ms for sequence {timer_data.get('sequence_id', 'unknown')}"
            )
        
        # Clean up
        del self._interaction_timers[interaction_id]
    
    # Scroll performance tracking
    def track_scroll_performance(self, scroll_value: int):
        """Track scroll performance."""
        current_time = self._performance_timer.elapsed()
        
        # Record scroll event time
        self._performance_metrics["scroll_events"].append(current_time)
        self._trim_metric_history("scroll_events")
        
        # Calculate scroll smoothness (time between events)
        if len(self._performance_metrics["scroll_events"]) >= 2:
            last_two = self._performance_metrics["scroll_events"][-2:]
            frame_time = last_two[1] - last_two[0]
            
            target = self._targets["scroll_smoothness"]
            if frame_time > target * self._warning_threshold_multiplier:
                logger.warning(f"Slow scroll frame: {frame_time:.1f}ms (target: {target:.1f}ms)")
                self.performance_warning.emit("scroll_frame", frame_time)
    
    # Animation performance tracking
    def track_animation_start(self, animation_type: str):
        """Track animation start performance."""
        current_time = self._performance_timer.elapsed()
        self._performance_metrics["animation_starts"].append(current_time)
        self._trim_metric_history("animation_starts")
        
        logger.debug(f"Animation started: {animation_type}")
    
    # Image loading performance tracking
    def track_image_load(self, image_path: str, load_time: float):
        """Track image loading performance."""
        self._performance_metrics["image_loads"].append(load_time)
        self._trim_metric_history("image_loads")
        
        target = self._targets["image_load"]
        if load_time > target * self._warning_threshold_multiplier:
            logger.warning(f"Slow image load: {load_time:.1f}ms (target: {target:.1f}ms) for {image_path}")
            self.performance_warning.emit("image_load", load_time)
    
    def _trim_metric_history(self, metric_name: str):
        """Trim metric history to maximum size."""
        if metric_name in self._performance_metrics:
            history = self._performance_metrics[metric_name]
            if len(history) > self._max_metric_history:
                self._performance_metrics[metric_name] = history[-self._max_metric_history:]
    
    def _generate_performance_report(self):
        """Generate comprehensive performance report."""
        if not self._monitoring_enabled:
            return
        
        report = {
            "timestamp": self._performance_timer.elapsed(),
            "targets": self._targets.copy(),
            "metrics": {},
            "warnings": [],
            "recommendations": [],
        }
        
        # Calculate metrics for each category
        for metric_name, values in self._performance_metrics.items():
            if values:
                report["metrics"][metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "recent_avg": sum(values[-10:]) / len(values[-10:]) if len(values) >= 10 else sum(values) / len(values),
                }
            else:
                report["metrics"][metric_name] = {
                    "count": 0,
                    "avg": 0,
                    "max": 0,
                    "min": 0,
                    "recent_avg": 0,
                }
        
        # Generate recommendations
        self._generate_recommendations(report)
        
        # Emit report
        self.performance_report.emit(report)
        
        logger.debug("Performance report generated")
    
    def _generate_recommendations(self, report: Dict):
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Check navigation performance
        nav_metrics = report["metrics"].get("navigation_clicks", {})
        if nav_metrics.get("avg", 0) > self._targets["navigation_response"]:
            recommendations.append("Consider optimizing navigation click handlers")
        
        # Check scroll performance
        scroll_metrics = report["metrics"].get("scroll_events", {})
        if scroll_metrics.get("avg", 0) > self._targets["scroll_smoothness"]:
            recommendations.append("Consider reducing scroll event processing complexity")
        
        # Check thumbnail performance
        thumb_metrics = report["metrics"].get("thumbnail_clicks", {})
        if thumb_metrics.get("avg", 0) > self._targets["thumbnail_response"]:
            recommendations.append("Consider optimizing thumbnail click handlers")
        
        # Check image loading performance
        image_metrics = report["metrics"].get("image_loads", {})
        if image_metrics.get("avg", 0) > self._targets["image_load"]:
            recommendations.append("Consider implementing more aggressive image caching")
        
        report["recommendations"] = recommendations
    
    # Public interface methods
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics."""
        metrics = {}
        for metric_name, values in self._performance_metrics.items():
            if values:
                metrics[metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                }
            else:
                metrics[metric_name] = {"count": 0, "avg": 0, "max": 0, "min": 0}
        
        return metrics
    
    def set_monitoring_enabled(self, enabled: bool):
        """Enable or disable performance monitoring."""
        self._monitoring_enabled = enabled
        logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")
    
    def clear_metrics(self):
        """Clear all performance metrics."""
        for metric_name in self._performance_metrics:
            self._performance_metrics[metric_name].clear()
        self._interaction_timers.clear()
        logger.info("Performance metrics cleared")
    
    def set_targets(self, targets: Dict[str, float]):
        """Update performance targets."""
        self._targets.update(targets)
        logger.info(f"Performance targets updated: {targets}")
    
    def sizeHint(self):
        """Provide size hint (not visible component)."""
        from PyQt6.QtCore import QSize
        return QSize(0, 0)
    
    def minimumSizeHint(self):
        """Provide minimum size hint (not visible component)."""
        from PyQt6.QtCore import QSize
        return QSize(0, 0)
