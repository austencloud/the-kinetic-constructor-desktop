"""
Performance Pre-initialization System for Browse Tab v2

This module provides comprehensive startup pre-initialization to eliminate
first-run performance penalties identified through performance testing.

Performance Targets (Based on Maximum Speed Test Results):
- Widget Creation: Eliminate 118ms → 17ms first-run penalty (7.2x improvement)
- Viewer Initialization: Eliminate 473ms → 33ms first-run penalty (14.3x improvement)
- Maintain steady-state performance: 17.1ms average widget creation, 33.1ms viewer initialization

Key Features:
- Animation system pre-initialization
- Widget creation pre-warming
- Image loading system preparation
- Qt property system warm-up
- Comprehensive error handling and fallback
- Performance monitoring and logging
"""

import logging
import time
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)

# Global pre-initialization state
_preinitialization_completed = False
_preinitialization_results: Dict[str, Any] = {}


def initialize_browse_tab_performance_systems(progress_callback=None) -> Dict[str, Any]:
    """
    Main entry point for browse tab v2 performance pre-initialization.

    This function should be called during application startup, after QApplication
    creation but before any browse tab components are instantiated.

    Returns:
        Dict[str, Any]: Results of pre-initialization including timing and success status
    """
    global _preinitialization_completed, _preinitialization_results

    if _preinitialization_completed:
        logger.debug("Browse tab performance systems already initialized")
        return _preinitialization_results

    logger.info("🚀 Starting Browse Tab v2 Performance Pre-initialization...")
    overall_start_time = time.time()

    results = {
        "overall_success": False,
        "overall_duration_ms": 0.0,
        "systems": {},
        "total_systems": 0,
        "successful_systems": 0,
        "failed_systems": [],
        "warnings": [],
    }

    # Ensure QApplication is available
    if not QApplication.instance():
        error_msg = "QApplication not available for pre-initialization"
        logger.error(error_msg)
        results["failed_systems"].append(("QApplication", error_msg))
        return results

    # System pre-initialization sequence
    systems_to_initialize = [
        ("Animation System", _initialize_animation_system),
        ("Widget System", _initialize_widget_system),
        ("Image Loading System", _initialize_image_loading_system),
        ("Property System", _initialize_property_system),
    ]

    results["total_systems"] = len(systems_to_initialize)

    # Initialize each system
    for i, (system_name, init_function) in enumerate(systems_to_initialize):
        logger.info(f"Initializing {system_name}...")
        system_start_time = time.time()

        # Update progress if callback provided
        if progress_callback:
            progress_callback(1, f"Initializing {system_name}...")

        try:
            success = init_function()
            duration_ms = (time.time() - system_start_time) * 1000

            results["systems"][system_name] = {
                "success": success,
                "duration_ms": duration_ms,
            }

            if success:
                results["successful_systems"] += 1
                logger.info(
                    f"✅ {system_name} initialized successfully in {duration_ms:.1f}ms"
                )
                # Update progress on successful completion
                if progress_callback:
                    progress_callback(0, f"{system_name} ready")
            else:
                results["failed_systems"].append(
                    (system_name, "Initialization returned False")
                )
                logger.warning(f"❌ {system_name} initialization failed")
                # Update progress even on failure
                if progress_callback:
                    progress_callback(0, f"{system_name} failed")

        except Exception as e:
            duration_ms = (time.time() - system_start_time) * 1000
            error_msg = str(e)

            results["systems"][system_name] = {
                "success": False,
                "duration_ms": duration_ms,
                "error": error_msg,
            }
            results["failed_systems"].append((system_name, error_msg))
            logger.error(f"❌ {system_name} initialization error: {e}")

    # Calculate overall results
    overall_duration_ms = (time.time() - overall_start_time) * 1000
    results["overall_duration_ms"] = overall_duration_ms
    results["overall_success"] = (
        results["successful_systems"] == results["total_systems"]
    )

    # Log summary
    success_rate = (results["successful_systems"] / results["total_systems"]) * 100
    logger.info(
        f"🎯 Pre-initialization complete: {results['successful_systems']}/{results['total_systems']} "
        f"systems ({success_rate:.0f}% success) in {overall_duration_ms:.1f}ms"
    )

    if results["failed_systems"]:
        logger.warning(
            f"Failed systems: {[name for name, _ in results['failed_systems']]}"
        )

    # Store results globally
    _preinitialization_results = results
    _preinitialization_completed = True

    return results


def _initialize_animation_system() -> bool:
    """Initialize the animation system."""
    try:
        from ..components.animation_system import preinitialize_animation_system

        return preinitialize_animation_system()
    except ImportError as e:
        logger.error(f"Could not import animation system: {e}")
        return False


def _initialize_widget_system() -> bool:
    """Initialize the widget system."""
    try:
        from .widget_prewarming import prewarm_widget_system
        from ..core.interfaces import BrowseTabConfig

        # Create default config for widget prewarming
        config = BrowseTabConfig()
        return prewarm_widget_system(config)
    except ImportError as e:
        logger.error(f"Could not import widget pre-warming system: {e}")
        return False


def _initialize_image_loading_system() -> bool:
    """Initialize the image loading system."""
    try:
        from .widget_prewarming import prewarm_image_loading_system

        return prewarm_image_loading_system()
    except ImportError as e:
        logger.error(f"Could not import image loading system: {e}")
        return False


def _initialize_property_system() -> bool:
    """Initialize Qt property system optimizations."""
    try:
        logger.debug("Initializing Qt property system optimizations...")
        start_time = time.time()

        # Create a temporary widget to warm up Qt's property system
        from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation

        # Create temporary widget
        temp_widget = QLabel("Property System Warmup")
        temp_widget.setFixedSize(50, 50)

        # Create opacity effect to warm up graphics effects
        opacity_effect = QGraphicsOpacityEffect()
        temp_widget.setGraphicsEffect(opacity_effect)

        # Create property animation to warm up animation properties
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(100)
        animation.setStartValue(1.0)
        animation.setEndValue(0.5)

        # Process events to ensure initialization
        QApplication.processEvents()

        # Clean up
        animation.deleteLater()
        temp_widget.deleteLater()
        QApplication.processEvents()

        duration_ms = (time.time() - start_time) * 1000
        logger.debug(f"Qt property system warmed up in {duration_ms:.1f}ms")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize property system: {e}")
        return False


def get_preinitialization_results() -> Optional[Dict[str, Any]]:
    """
    Get the results of the pre-initialization process.

    Returns:
        Dict[str, Any]: Pre-initialization results, or None if not completed
    """
    global _preinitialization_results, _preinitialization_completed

    if _preinitialization_completed:
        return _preinitialization_results.copy()
    return None


def is_preinitialization_completed() -> bool:
    """
    Check if pre-initialization has been completed.

    Returns:
        bool: True if pre-initialization is complete
    """
    global _preinitialization_completed
    return _preinitialization_completed


def get_performance_improvement_summary() -> Dict[str, str]:
    """
    Get a summary of expected performance improvements.

    Returns:
        Dict[str, str]: Summary of performance improvements
    """
    return {
        "widget_creation": "118ms → 17ms (7.2x faster)",
        "viewer_initialization": "473ms → 33ms (14.3x faster)",
        "animation_system": "First-run penalty eliminated",
        "image_loading": "Reduced initialization overhead",
        "overall_benefit": "Consistent optimal performance from first use",
    }


def validate_preinitialization_effectiveness() -> Dict[str, Any]:
    """
    Validate that pre-initialization was effective by checking system states.

    Returns:
        Dict[str, Any]: Validation results
    """
    validation_results = {
        "animation_system_ready": False,
        "widget_system_ready": False,
        "image_system_ready": False,
        "overall_ready": False,
    }

    try:
        # Check animation system
        from ..components.animation_system import is_animation_system_preinitialized

        validation_results["animation_system_ready"] = (
            is_animation_system_preinitialized()
        )

        # Check widget system
        from .widget_prewarming import is_widget_system_prewarmed

        validation_results["widget_system_ready"] = is_widget_system_prewarmed()

        # Check if image loading components are available
        try:
            from ..services.image_loader import AsyncImageLoader
            from ..services.cache_service import CacheService

            validation_results["image_system_ready"] = True
        except ImportError:
            validation_results["image_system_ready"] = False

        # Overall readiness
        validation_results["overall_ready"] = all(
            [
                validation_results["animation_system_ready"],
                validation_results["widget_system_ready"],
                validation_results["image_system_ready"],
            ]
        )

    except Exception as e:
        logger.error(f"Error validating pre-initialization effectiveness: {e}")

    return validation_results
