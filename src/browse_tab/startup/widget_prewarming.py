"""
Widget Pre-warming System for Browse Tab v2

Pre-initializes widgets and systems to eliminate first-run performance penalties.
This system "warms up" expensive widget creation processes during application startup.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QApplication

from ..core.interfaces import BrowseTabConfig, SequenceModel
from ..components.animation_system import (
    preinitialize_animation_system,
    AnimationManager,
)
from ..components.thumbnail_card import ThumbnailCard
from ..components.sequence_viewer import SequenceViewer

logger = logging.getLogger(__name__)

# Global state tracking
_widget_system_prewarmed = False
_prewarming_widgets: List[QWidget] = []
_prewarming_stats: Dict[str, float] = {}


def prewarm_widget_systems(config: BrowseTabConfig) -> bool:
    """
    Pre-warm all widget systems for optimal performance.

    This function should be called during application startup to eliminate
    first-run performance penalties when creating browse tab widgets.
    """
    global _widget_system_prewarmed

    if _widget_system_prewarmed:
        logger.debug("Widget systems already pre-warmed")
        return True

    try:
        logger.info("Starting widget systems pre-warming...")
        start_time = time.time()

        if not QApplication.instance():
            logger.warning("QApplication not available for widget pre-warming")
            return False

        # Pre-warm core Qt systems
        _prewarm_qt_systems()

        # Pre-warm animation system
        preinitialize_animation_system()

        # Create test sequences for pre-warming
        test_sequences = _create_test_sequences()

        # Pre-warm ThumbnailCard widgets
        _prewarm_thumbnail_cards(test_sequences, config)

        # Pre-warm SequenceViewer widget
        _prewarm_sequence_viewer(config)

        # Additional system pre-warming
        _prewarm_image_loading_system()

        _widget_system_prewarmed = True

        total_time = time.time() - start_time
        logger.info(
            f"Widget systems pre-warmed successfully in {total_time*1000:.1f}ms"
        )

        # Log pre-warming statistics
        _log_prewarming_stats()

        # Schedule cleanup
        QTimer.singleShot(30000, _cleanup_prewarming_widgets)  # Clean up after 30s

        return True

    except Exception as e:
        logger.error(f"Failed to pre-warm widget systems: {e}")
        return False


def _create_test_sequences() -> List[SequenceModel]:
    """Create test sequences for pre-warming."""
    test_sequences = []

    for i in range(3):  # Create 3 test sequences
        sequence = SequenceModel(
            id=f"prewarm_test_{i}",
            name=f"Test Sequence {i}",
            thumbnails=[f"test_image_{i}.png"],
            difficulty=1,
            length=5,
            author="System",
            tags=["test"],
            metadata={},
        )
        test_sequences.append(sequence)

    return test_sequences


def _prewarm_thumbnail_cards(
    test_sequences: List[SequenceModel], config: BrowseTabConfig
):
    """Pre-warm ThumbnailCard widgets."""
    global _prewarming_widgets

    logger.debug("Pre-warming ThumbnailCard widgets...")

    for i, sequence in enumerate(test_sequences):
        try:
            # Create widget (this triggers the expensive initialization)
            widget = ThumbnailCard(sequence, config)
            widget.setVisible(False)  # Keep hidden

            # Store for cleanup
            _prewarming_widgets.append(widget)

            # Process events to ensure initialization completes
            QApplication.processEvents()

            logger.debug(f"Pre-warmed thumbnail card {i+1}/{len(test_sequences)}")

        except Exception as e:
            logger.warning(f"Failed to pre-warm thumbnail card {i}: {e}")


def _prewarm_sequence_viewer(config: BrowseTabConfig):
    """Pre-warm SequenceViewer widget."""
    global _prewarming_widgets

    logger.debug("Pre-warming SequenceViewer...")

    try:
        # Create sequence viewer (this triggers animation system initialization)
        viewer = SequenceViewer(config)
        viewer.setVisible(False)  # Keep hidden

        # Store for cleanup
        _prewarming_widgets.append(viewer)

        # Process events to ensure initialization completes
        QApplication.processEvents()

        logger.debug("Pre-warmed sequence viewer")

    except Exception as e:
        logger.warning(f"Failed to pre-warm sequence viewer: {e}")


def _prewarm_qt_systems():
    """Pre-warm additional Qt systems for optimal performance."""
    logger.debug("Pre-warming Qt systems...")

    try:
        # Force Qt to initialize common systems
        temp_widget = QWidget()
        temp_widget.setFixedSize(1, 1)
        temp_widget.show()
        temp_widget.hide()
        temp_widget.deleteLater()

        # Process events to ensure initialization
        QApplication.processEvents()

        logger.debug("Qt systems pre-warmed")

    except Exception as e:
        logger.warning(f"Failed to pre-warm Qt systems: {e}")


def _prewarm_image_loading_system() -> bool:
    """Pre-warm image loading system."""
    logger.debug("Pre-warming image loading system...")

    try:
        # This would normally pre-load common image formats and pixmap caches
        # For now, we'll just ensure the system is touched
        from PyQt6.QtGui import QPixmap

        # Create a small test pixmap to warm up the system
        test_pixmap = QPixmap(1, 1)
        test_pixmap.fill()

        logger.debug("Image loading system pre-warmed")
        return True

    except Exception as e:
        logger.warning(f"Failed to pre-warm image loading system: {e}")
        return False


def _cleanup_prewarming_widgets():
    """Clean up pre-warming widgets after initialization."""
    global _prewarming_widgets

    logger.debug(f"Cleaning up {len(_prewarming_widgets)} pre-warming widgets...")

    for widget in _prewarming_widgets:
        try:
            if widget and not widget.isVisible():
                widget.deleteLater()
        except Exception as e:
            logger.warning(f"Error cleaning up pre-warming widget: {e}")

    _prewarming_widgets.clear()
    logger.debug("Pre-warming widgets cleaned up")


def _log_prewarming_stats():
    """Log pre-warming statistics."""
    global _prewarming_stats

    logger.info("Pre-warming Statistics:")
    for component, duration in _prewarming_stats.items():
        logger.info(f"  {component}: {duration*1000:.1f}ms")


def is_widget_system_prewarmed() -> bool:
    """Check if widget system has been pre-warmed."""
    global _widget_system_prewarmed
    return _widget_system_prewarmed


def prewarm_image_loading_system() -> bool:
    """Public interface for pre-warming image loading system."""
    return _prewarm_image_loading_system()


def prewarm_all_systems() -> bool:
    """Pre-warm all systems with default configuration."""
    config = BrowseTabConfig()
    return prewarm_widget_systems(config)


# Alias for backwards compatibility
prewarm_widget_system = prewarm_widget_systems
