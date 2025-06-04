"""
Performance-Optimized Hover Animation Manager - Phase 4 Implementation

Unified, conflict-free hover animation system that ensures 60fps performance
and eliminates all timing conflicts in the browse_tab_v2 system.
"""

import logging
from typing import Dict, Set, Optional
from weakref import WeakSet
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import (
    QObject,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QTimer,
)

logger = logging.getLogger(__name__)


class OptimizedHoverManager(QObject):
    """
    Performance-optimized hover manager using Qt-native property animations.

    This manager eliminates all animation conflicts and ensures consistent
    60fps performance across the entire browse_tab_v2 system.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Track registered widgets to prevent memory leaks
        self._registered_widgets: WeakSet[QWidget] = WeakSet()
        self._hover_states: Dict[int, bool] = {}  # widget_id -> hover_state
        self._active_animations: Dict[int, QPropertyAnimation] = (
            {}
        )  # widget_id -> active_animation

        # Performance tracking
        self._hover_event_count = 0

        # Virtual scrolling integration
        self._virtual_scroll_active = False
        self._viewport_change_in_progress = False

        logger.debug("OptimizedHoverManager initialized")

    def register_widget(self, widget: QWidget) -> None:
        """Register a widget for optimized hover management."""
        if widget in self._registered_widgets:
            return

        widget_id = id(widget)
        self._registered_widgets.add(widget)
        self._hover_states[widget_id] = False

        # Setup opacity effect for smooth animations
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.8)
        widget.setGraphicsEffect(opacity_effect)

        logger.debug(f"Registered widget {widget_id} for optimized hover")

    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister a widget from hover management."""
        widget_id = id(widget)
        self._registered_widgets.discard(widget)
        self._hover_states.pop(widget_id, None)
        self._active_animations.pop(widget_id, None)

        logger.debug(f"Unregistered widget {widget_id}")

    def set_hover_state(self, widget: QWidget, hovered: bool) -> None:
        """Set hover state using optimized Qt-native property animations."""
        widget_id = id(widget)

        # Skip if virtual scrolling is active to prevent conflicts
        if self._viewport_change_in_progress:
            return

        # Skip if state hasn't changed
        current_state = self._hover_states.get(widget_id, False)
        if current_state == hovered:
            return

        # Update state
        self._hover_states[widget_id] = hovered
        self._hover_event_count += 1

        # Stop any existing animation
        if widget_id in self._active_animations:
            self._active_animations[widget_id].stop()

        # Create Qt-native property animation
        opacity_effect = widget.graphicsEffect()
        if opacity_effect:
            animation = QPropertyAnimation(opacity_effect, b"opacity")
            animation.setDuration(150)  # Fast transition
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            if hovered:
                animation.setStartValue(0.8)
                animation.setEndValue(1.0)
            else:
                animation.setStartValue(1.0)
                animation.setEndValue(0.8)

            animation.start()
            self._active_animations[widget_id] = animation

    def set_virtual_scroll_active(self, active: bool) -> None:
        """Set virtual scrolling state to prevent hover conflicts."""
        self._virtual_scroll_active = active

        if active:
            # Reset all hover states during virtual scrolling
            self._reset_all_hover_states()

    def set_viewport_change_in_progress(self, in_progress: bool) -> None:
        """Set viewport change state to prevent hover event conflicts."""
        self._viewport_change_in_progress = in_progress

    def _reset_all_hover_states(self) -> None:
        """Reset all hover states to prevent conflicts during virtual scrolling."""
        for widget in self._registered_widgets:
            widget_id = id(widget)
            self._hover_states[widget_id] = False
            widget.setProperty("hovered", False)
            widget.style().polish(widget)


class VirtualScrollIntegratedHoverMixin:
    """
    Mixin to integrate optimized hover management with virtual scrolling widgets.

    This mixin should be applied to thumbnail cards in virtual scrolling environments
    to ensure proper hover animation performance.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hover_manager: Optional[OptimizedHoverManager] = None
        self._hover_enabled = True

    def set_hover_manager(self, hover_manager: OptimizedHoverManager) -> None:
        """Set the hover manager for this widget."""
        if self._hover_manager:
            self._hover_manager.unregister_widget(self)

        self._hover_manager = hover_manager
        if hover_manager:
            hover_manager.register_widget(self)

    def enterEvent(self, event):
        """Optimized hover enter using centralized manager."""
        if self._hover_manager and self._hover_enabled:
            self._hover_manager.set_hover_state(self, True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Optimized hover leave using centralized manager."""
        if self._hover_manager and self._hover_enabled:
            self._hover_manager.set_hover_state(self, False)
        super().leaveEvent(event)


class VirtualScrollHoverCoordinator:
    """
    Coordinates hover animations with virtual scrolling operations to prevent conflicts.

    This coordinator should be integrated with the EfficientVirtualGrid to ensure
    hover animations don't interfere with viewport changes and widget recycling.
    """

    def __init__(self, hover_manager: OptimizedHoverManager):
        self.hover_manager = hover_manager
        self._viewport_change_timer = QTimer()
        self._viewport_change_timer.setSingleShot(True)
        self._viewport_change_timer.timeout.connect(self._on_viewport_change_complete)

    def notify_viewport_change_start(self) -> None:
        """Notify that a viewport change is starting."""
        self.hover_manager.set_viewport_change_in_progress(True)

        # Start timer to re-enable hover after viewport change completes
        self._viewport_change_timer.stop()
        self._viewport_change_timer.start(100)  # 100ms buffer

    def notify_widget_recycling_start(self) -> None:
        """Notify that widget recycling is starting."""
        self.hover_manager.set_virtual_scroll_active(True)

    def notify_widget_recycling_complete(self) -> None:
        """Notify that widget recycling is complete."""
        self.hover_manager.set_virtual_scroll_active(False)

    def _on_viewport_change_complete(self) -> None:
        """Re-enable hover processing after viewport change completes."""
        self.hover_manager.set_viewport_change_in_progress(False)
        logger.debug("Viewport change complete - re-enabled hover processing")


# Global hover manager instance for the browse_tab_v2 system
_global_hover_manager: Optional[OptimizedHoverManager] = None


def get_global_hover_manager() -> OptimizedHoverManager:
    """Get the global hover manager instance."""
    global _global_hover_manager
    if _global_hover_manager is None:
        _global_hover_manager = OptimizedHoverManager()
        logger.info("Created global optimized hover manager")
    return _global_hover_manager


def initialize_hover_system(virtual_grid) -> VirtualScrollHoverCoordinator:
    """Initialize the optimized hover system for a virtual grid."""
    hover_manager = get_global_hover_manager()
    coordinator = VirtualScrollHoverCoordinator(hover_manager)

    # Connect virtual grid signals if available
    if hasattr(virtual_grid, "viewport_changed"):
        virtual_grid.viewport_changed.connect(
            lambda start, end: coordinator.notify_viewport_change_start()
        )

    logger.info("Initialized optimized hover system")
    return coordinator
