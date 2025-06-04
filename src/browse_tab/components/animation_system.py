"""
Animation System for Browse Tab v2

Provides smooth animations and transitions for modern UI components.
"""

import logging
import time
from typing import Dict, Any, Optional
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QObject, QTimer
from PyQt6.QtWidgets import QApplication, QGraphicsOpacityEffect, QWidget

logger = logging.getLogger(__name__)

_animation_system_preinitialized = False
_animation_pools: Dict[str, Any] = {}


def preinitialize_animation_system() -> bool:
    """Pre-initialize the animation system to eliminate first-run penalties."""
    global _animation_system_preinitialized, _animation_pools

    if _animation_system_preinitialized:
        logger.debug("Animation system already pre-initialized")
        return True

    try:
        logger.debug("Pre-initializing animation system...")
        start_time = time.time()

        if not QApplication.instance():
            logger.warning(
                "QApplication not available for animation pre-initialization"
            )
            return False

        # Pre-create animation objects to warm up Qt's animation system
        _create_animation_pools()

        # Warm up easing curves
        _prewarm_easing_curves()

        # Warm up graphics effects
        _prewarm_graphics_effects()

        QApplication.processEvents()

        _animation_system_preinitialized = True
        duration = time.time() - start_time
        logger.debug(f"Animation system pre-initialized in {duration*1000:.1f}ms")
        return True

    except Exception as e:
        logger.error(f"Failed to pre-initialize animation system: {e}")
        return False


def _create_animation_pools():
    """Create pools of pre-initialized animation objects."""
    global _animation_pools

    # Create temporary widget for animations
    temp_widget = QWidget()
    temp_widget.setFixedSize(1, 1)

    # Create opacity animations pool
    opacity_animations = []
    for _ in range(3):
        effect = QGraphicsOpacityEffect()
        temp_widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(250)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        opacity_animations.append(animation)

    # Create geometry animations pool
    geometry_animations = []
    for _ in range(3):
        animation = QPropertyAnimation(temp_widget, b"geometry")
        animation.setDuration(250)
        geometry_animations.append(animation)

    _animation_pools = {
        "opacity": opacity_animations,
        "geometry": geometry_animations,
        "temp_widget": temp_widget,
    }


def _prewarm_easing_curves():
    """Pre-warm common easing curves."""
    curves = [
        QEasingCurve.Type.Linear,
        QEasingCurve.Type.InOutQuad,
        QEasingCurve.Type.OutCubic,
        QEasingCurve.Type.InOutCubic,
    ]

    for curve_type in curves:
        curve = QEasingCurve(curve_type)
        # Touch the curve to ensure it's initialized
        curve.valueForProgress(0.5)


def _prewarm_graphics_effects():
    """Pre-warm graphics effects system."""
    temp_widget = QWidget()
    temp_widget.setFixedSize(1, 1)

    # Create and apply different effects
    effects = [QGraphicsOpacityEffect()]

    for effect in effects:
        temp_widget.setGraphicsEffect(effect)
        QApplication.processEvents()

    temp_widget.deleteLater()


def is_animation_system_preinitialized() -> bool:
    """Check if animation system has been pre-initialized."""
    global _animation_system_preinitialized
    return _animation_system_preinitialized


def cleanup_animation_pools():
    """Clean up animation pools."""
    global _animation_pools

    if "temp_widget" in _animation_pools:
        _animation_pools["temp_widget"].deleteLater()

    _animation_pools.clear()


class AnimationConfig:
    """Configuration for animations."""

    def __init__(self):
        self.duration = 300
        self.easing_curve = QEasingCurve.Type.OutCubic
        self.fade_duration = 200
        self.hover_duration = 150


class AnimationManager(QObject):
    """Manages animations for browse tab components."""

    def __init__(self, config: Optional[AnimationConfig] = None):
        super().__init__()
        self.config = config or AnimationConfig()
        self._active_animations: Dict[str, QPropertyAnimation] = {}

    def fade_in(self, widget: QWidget, duration: Optional[int] = None) -> None:
        """Fade in a widget."""
        if not widget:
            return

        duration = duration or self.config.fade_duration

        # Create opacity effect if needed
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)

        effect = widget.graphicsEffect()
        if effect:
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(self.config.easing_curve)
            animation.start()

            # Store animation reference
            self._active_animations[f"fade_in_{id(widget)}"] = animation

    def fade_out(self, widget: QWidget, duration: Optional[int] = None) -> None:
        """Fade out a widget."""
        if not widget:
            return

        duration = duration or self.config.fade_duration

        # Create opacity effect if needed
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)

        effect = widget.graphicsEffect()
        if effect:
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
            animation.setEasingCurve(self.config.easing_curve)
            animation.start()

            # Store animation reference
            self._active_animations[f"fade_out_{id(widget)}"] = animation

    def hover_scale(self, widget: QWidget, scale_factor: float = 1.05) -> None:
        """Apply hover scale animation."""
        if not widget:
            return

        # Simple hover effect without complex animations
        widget.setStyleSheet(
            f"""
            QWidget:hover {{
                transform: scale({scale_factor});
            }}
        """
        )

    def cleanup(self) -> None:
        """Clean up active animations."""
        for animation in self._active_animations.values():
            if animation:
                animation.stop()
        self._active_animations.clear()
