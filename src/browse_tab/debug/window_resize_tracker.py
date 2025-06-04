"""
Window Resize Tracker - Comprehensive debugging for main window expansion

This module provides detailed logging and tracking of window resize events
throughout the browse tab v2 initialization and display process.
"""

import logging
import time
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QObject, pyqtSignal
import traceback

logger = logging.getLogger(__name__)

class WindowResizeTracker(QObject):
    """Tracks and logs window resize events with detailed context."""
    
    resize_detected = pyqtSignal(str, int, int, int, int)  # component, old_w, old_h, new_w, new_h
    
    def __init__(self):
        super().__init__()
        self.main_window: Optional[QWidget] = None
        self.tracking_enabled = True
        self.resize_log = []
        self.component_sizes = {}
        self.initialization_phase = "startup"
        
    def set_main_window(self, main_window: QWidget):
        """Set the main window to track."""
        self.main_window = main_window
        if main_window:
            initial_size = main_window.size()
            self.log_resize("MainWindow_Initial", 0, 0, initial_size.width(), initial_size.height())
    
    def set_phase(self, phase: str):
        """Set the current initialization phase for context."""
        self.initialization_phase = phase
        logger.info(f"🔄 PHASE CHANGE: {phase}")
    
    def log_resize(self, component_name: str, old_width: int, old_height: int, 
                   new_width: int, new_height: int, extra_context: str = ""):
        """Log a resize event with full context."""
        if not self.tracking_enabled:
            return
            
        timestamp = time.time()
        width_change = new_width - old_width
        height_change = new_height - old_height
        
        # Get current main window size for comparison
        main_window_size = "Unknown"
        if self.main_window:
            mw_size = self.main_window.size()
            main_window_size = f"{mw_size.width()}x{mw_size.height()}"
        
        # Create log entry
        log_entry = {
            'timestamp': timestamp,
            'phase': self.initialization_phase,
            'component': component_name,
            'old_size': (old_width, old_height),
            'new_size': (new_width, new_height),
            'change': (width_change, height_change),
            'main_window_size': main_window_size,
            'extra_context': extra_context
        }
        
        self.resize_log.append(log_entry)
        
        # Log with appropriate level based on significance
        if abs(height_change) > 10 or abs(width_change) > 10:
            level = "WARNING"
            symbol = "⚠️"
        elif height_change != 0 or width_change != 0:
            level = "INFO"
            symbol = "📏"
        else:
            level = "DEBUG"
            symbol = "📐"
        
        log_msg = (f"{symbol} RESIZE [{self.initialization_phase}] {component_name}: "
                  f"{old_width}x{old_height} → {new_width}x{new_height} "
                  f"(Δ{width_change:+d}x{height_change:+d}) "
                  f"MainWindow: {main_window_size}")
        
        if extra_context:
            log_msg += f" | {extra_context}"
        
        if level == "WARNING":
            logger.warning(log_msg)
        elif level == "INFO":
            logger.info(log_msg)
        else:
            logger.debug(log_msg)
        
        # Emit signal for real-time monitoring
        self.resize_detected.emit(component_name, old_width, old_height, new_width, new_height)
    
    def track_component_size(self, component_name: str, widget: QWidget, context: str = ""):
        """Track and log a component's current size."""
        if not widget:
            return
            
        size = widget.size()
        old_size = self.component_sizes.get(component_name, (0, 0))
        
        self.component_sizes[component_name] = (size.width(), size.height())
        
        self.log_resize(component_name, old_size[0], old_size[1], 
                       size.width(), size.height(), context)
    
    def log_main_window_change(self, context: str):
        """Specifically log main window size changes."""
        if not self.main_window:
            return
            
        size = self.main_window.size()
        old_size = self.component_sizes.get("MainWindow", (0, 0))
        
        if old_size != (size.width(), size.height()):
            self.component_sizes["MainWindow"] = (size.width(), size.height())
            self.log_resize("MainWindow", old_size[0], old_size[1], 
                           size.width(), size.height(), context)
            
            # If this is a significant change, log the call stack
            height_change = size.height() - old_size[1]
            if abs(height_change) > 5:
                logger.warning(f"🚨 SIGNIFICANT MAIN WINDOW HEIGHT CHANGE: {height_change:+d}px")
                logger.warning(f"📍 CONTEXT: {context}")
                # Log abbreviated call stack
                stack = traceback.format_stack()
                relevant_stack = [line for line in stack[-10:] if 'browse_tab' in line.lower()]
                if relevant_stack:
                    logger.warning("📚 RELEVANT CALL STACK:")
                    for line in relevant_stack:
                        logger.warning(f"   {line.strip()}")
    
    def get_resize_summary(self) -> Dict[str, Any]:
        """Get a summary of all resize events."""
        if not self.resize_log:
            return {"total_events": 0}
        
        # Find significant changes
        significant_changes = [
            entry for entry in self.resize_log 
            if abs(entry['change'][0]) > 10 or abs(entry['change'][1]) > 10
        ]
        
        # Find main window changes
        main_window_changes = [
            entry for entry in self.resize_log 
            if entry['component'].startswith('MainWindow')
        ]
        
        return {
            "total_events": len(self.resize_log),
            "significant_changes": len(significant_changes),
            "main_window_changes": len(main_window_changes),
            "phases": list(set(entry['phase'] for entry in self.resize_log)),
            "components": list(set(entry['component'] for entry in self.resize_log)),
            "latest_main_window_size": self.component_sizes.get("MainWindow", "Unknown")
        }
    
    def print_detailed_report(self):
        """Print a detailed report of all resize events."""
        logger.info("="*80)
        logger.info("WINDOW RESIZE TRACKING REPORT")
        logger.info("="*80)
        
        summary = self.get_resize_summary()
        logger.info(f"Total resize events: {summary['total_events']}")
        logger.info(f"Significant changes: {summary['significant_changes']}")
        logger.info(f"Main window changes: {summary['main_window_changes']}")
        logger.info(f"Phases tracked: {', '.join(summary['phases'])}")
        
        # Show significant changes in chronological order
        significant_changes = [
            entry for entry in self.resize_log 
            if abs(entry['change'][0]) > 5 or abs(entry['change'][1]) > 5
        ]
        
        if significant_changes:
            logger.info("\n📊 SIGNIFICANT RESIZE EVENTS:")
            for entry in significant_changes:
                change_str = f"{entry['change'][0]:+d}x{entry['change'][1]:+d}"
                logger.info(f"  [{entry['phase']}] {entry['component']}: {change_str} | {entry['extra_context']}")
        
        logger.info("="*80)

# Global tracker instance
_tracker = None

def get_tracker() -> WindowResizeTracker:
    """Get the global resize tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = WindowResizeTracker()
    return _tracker

def init_tracking(main_window: QWidget):
    """Initialize resize tracking for the main window."""
    tracker = get_tracker()
    tracker.set_main_window(main_window)
    logger.info("🔍 Window resize tracking initialized")

def set_phase(phase: str):
    """Set the current tracking phase."""
    get_tracker().set_phase(phase)

def track_component(name: str, widget: QWidget, context: str = ""):
    """Track a component's size."""
    get_tracker().track_component_size(name, widget, context)

def log_main_window_change(context: str):
    """Log main window size change."""
    get_tracker().log_main_window_change(context)

def print_report():
    """Print the final tracking report."""
    get_tracker().print_detailed_report()
