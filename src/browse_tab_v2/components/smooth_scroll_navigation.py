"""
Smooth Scroll Navigation System

Provides smooth scrolling animations and viewport tracking for section navigation.
Integrates with the existing AnimationManager for consistent animations.

Features:
- Smooth scroll to section animations
- Viewport tracking for active section detection
- Scroll position persistence
- Integration with AnimationManager
- Eased animations (OutCubic, 500ms duration)
"""

import logging
from typing import Optional, Dict, Callable, List
from PyQt6.QtWidgets import QScrollArea, QWidget
from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QPoint,
)
from PyQt6.QtGui import QWheelEvent

from ..core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


class ViewportTracker(QObject):
    """Tracks viewport position and detects active sections."""

    # Signals
    active_section_changed = pyqtSignal(str)  # section_id
    viewport_changed = pyqtSignal(int, int)  # scroll_y, viewport_height

    def __init__(self, scroll_area: QScrollArea, parent: QObject = None):
        super().__init__(parent)

        self.scroll_area = scroll_area
        self.section_positions: Dict[str, int] = {}  # section_id -> y_position
        self.current_active_section: Optional[str] = None

        # Connect scroll events
        if hasattr(scroll_area, "verticalScrollBar"):
            scroll_area.verticalScrollBar().valueChanged.connect(
                self._on_scroll_changed
            )

    def update_section_positions(self, positions: Dict[str, int]):
        """Update section positions for tracking."""
        self.section_positions = positions
        self._check_active_section()

    def _on_scroll_changed(self, value: int):
        """Handle scroll position changes."""
        viewport_height = self.scroll_area.viewport().height()
        self.viewport_changed.emit(value, viewport_height)
        self._check_active_section()

    def _check_active_section(self):
        """Check which section is currently active in viewport."""
        if not self.section_positions:
            return

        scroll_y = self.scroll_area.verticalScrollBar().value()
        viewport_height = self.scroll_area.viewport().height()

        # Find the section that's most visible in viewport
        active_section = None
        min_distance = float("inf")

        for section_id, position in self.section_positions.items():
            # Calculate distance from viewport center
            viewport_center = scroll_y + viewport_height // 2
            distance = abs(position - viewport_center)

            if distance < min_distance:
                min_distance = distance
                active_section = section_id

        # Update active section if changed
        if active_section != self.current_active_section:
            self.current_active_section = active_section
            if active_section:
                self.active_section_changed.emit(active_section)
                logger.debug(f"Active section changed to: {active_section}")

    def get_active_section(self) -> Optional[str]:
        """Get currently active section."""
        return self.current_active_section


class ScrollPositionManager:
    """Manages scroll position persistence during filter changes."""

    def __init__(self):
        self.saved_positions: Dict[str, int] = {}  # filter_key -> scroll_position
        self.current_filter_key: Optional[str] = None

    def save_position(self, filter_key: str, position: int):
        """Save scroll position for a filter state."""
        self.saved_positions[filter_key] = position
        self.current_filter_key = filter_key
        logger.debug(f"Saved scroll position {position} for filter: {filter_key}")

    def restore_position(self, filter_key: str) -> Optional[int]:
        """Restore scroll position for a filter state."""
        position = self.saved_positions.get(filter_key)
        if position is not None:
            logger.debug(
                f"Restored scroll position {position} for filter: {filter_key}"
            )
        return position

    def clear_positions(self):
        """Clear all saved positions."""
        self.saved_positions.clear()
        self.current_filter_key = None


class SmoothScrollNavigation(QObject):
    """
    Smooth scroll navigation system with viewport tracking.

    Features:
    - Smooth animated scrolling to sections
    - Viewport tracking for active section detection
    - Scroll position persistence
    - Integration with AnimationManager
    """

    # Signals
    scroll_started = pyqtSignal(str)  # target_section_id
    scroll_finished = pyqtSignal(str)  # target_section_id
    active_section_changed = pyqtSignal(str)  # section_id

    def __init__(
        self,
        scroll_area: QScrollArea,
        config: BrowseTabConfig = None,
        parent: QObject = None,
    ):
        super().__init__(parent)

        self.scroll_area = scroll_area
        self.config = config or BrowseTabConfig()

        # Components
        self.viewport_tracker = ViewportTracker(scroll_area, self)
        self.position_manager = ScrollPositionManager()

        # Animation
        self.scroll_animation: Optional[QPropertyAnimation] = None
        self.is_animating = False

        # State
        self.section_positions: Dict[str, int] = {}
        self.animation_manager = None  # Will be set externally

        # Connect signals
        self.viewport_tracker.active_section_changed.connect(
            self.active_section_changed.emit
        )

        logger.debug("SmoothScrollNavigation initialized")

    def set_animation_manager(self, animation_manager):
        """Set animation manager for integration."""
        self.animation_manager = animation_manager

    def update_section_positions(self, positions: Dict[str, int]):
        """Update section positions for navigation."""
        self.section_positions = positions
        self.viewport_tracker.update_section_positions(positions)
        logger.debug(f"Updated {len(positions)} section positions")

    def scroll_to_section(self, section_id: str, animated: bool = True):
        """Scroll to a specific section."""
        if section_id not in self.section_positions:
            logger.warning(f"Section not found: {section_id}")
            return

        target_position = self.section_positions[section_id]

        if not animated or not self.config.enable_animations:
            # Immediate scroll
            self.scroll_area.verticalScrollBar().setValue(target_position)
            self.scroll_finished.emit(section_id)
            return

        # Animated scroll
        self._animate_scroll_to_position(target_position, section_id)

    def _animate_scroll_to_position(self, target_position: int, section_id: str):
        """Animate scroll to target position."""
        if self.is_animating and self.scroll_animation:
            self.scroll_animation.stop()

        scroll_bar = self.scroll_area.verticalScrollBar()
        current_position = scroll_bar.value()

        # Don't animate if already at target
        if abs(current_position - target_position) < 5:
            self.scroll_finished.emit(section_id)
            return

        # Create scroll animation
        self.scroll_animation = QPropertyAnimation(scroll_bar, b"value")
        self.scroll_animation.setDuration(500)  # 500ms duration
        self.scroll_animation.setStartValue(current_position)
        self.scroll_animation.setEndValue(target_position)
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Connect finished signal
        self.scroll_animation.finished.connect(
            lambda: self._on_scroll_finished(section_id)
        )

        # Start animation and emit started signal
        self.is_animating = True
        self.scroll_animation.start()
        self._on_scroll_started(section_id)

        logger.debug(
            f"Started scroll animation to section: {section_id} (position: {target_position})"
        )

    def _on_scroll_started(self, section_id: str):
        """Handle scroll animation start."""
        self.scroll_started.emit(section_id)

    def _on_scroll_finished(self, section_id: str):
        """Handle scroll animation finish."""
        self.is_animating = False
        self.scroll_animation = None
        self.scroll_finished.emit(section_id)
        logger.debug(f"Scroll animation finished for section: {section_id}")

    def save_scroll_position(self, filter_key: str):
        """Save current scroll position for filter state."""
        current_position = self.scroll_area.verticalScrollBar().value()
        self.position_manager.save_position(filter_key, current_position)

    def restore_scroll_position(self, filter_key: str, animated: bool = False):
        """Restore scroll position for filter state."""
        position = self.position_manager.restore_position(filter_key)
        if position is not None:
            if animated and self.config.enable_animations:
                self._animate_scroll_to_position(position, "restored_position")
            else:
                self.scroll_area.verticalScrollBar().setValue(position)

    def get_current_scroll_position(self) -> int:
        """Get current scroll position."""
        return self.scroll_area.verticalScrollBar().value()

    def get_active_section(self) -> Optional[str]:
        """Get currently active section."""
        return self.viewport_tracker.get_active_section()

    def is_scroll_animating(self) -> bool:
        """Check if scroll animation is in progress."""
        return self.is_animating

    def stop_scroll_animation(self):
        """Stop current scroll animation."""
        if self.is_animating and self.scroll_animation:
            self.scroll_animation.stop()
            self.is_animating = False
            self.scroll_animation = None

    def scroll_to_top(self, animated: bool = True):
        """Scroll to top of content."""
        if animated and self.config.enable_animations:
            self._animate_scroll_to_position(0, "top")
        else:
            self.scroll_area.verticalScrollBar().setValue(0)

    def scroll_to_bottom(self, animated: bool = True):
        """Scroll to bottom of content."""
        scroll_bar = self.scroll_area.verticalScrollBar()
        max_value = scroll_bar.maximum()

        if animated and self.config.enable_animations:
            self._animate_scroll_to_position(max_value, "bottom")
        else:
            scroll_bar.setValue(max_value)

    def get_section_positions(self) -> Dict[str, int]:
        """Get current section positions."""
        return self.section_positions.copy()

    def clear_section_positions(self):
        """Clear all section positions."""
        self.section_positions.clear()
        self.viewport_tracker.update_section_positions({})

    def get_viewport_info(self) -> Dict[str, int]:
        """Get current viewport information."""
        scroll_bar = self.scroll_area.verticalScrollBar()
        viewport = self.scroll_area.viewport()

        return {
            "scroll_y": scroll_bar.value(),
            "viewport_height": viewport.height(),
            "content_height": scroll_bar.maximum() + viewport.height(),
            "scroll_max": scroll_bar.maximum(),
        }
