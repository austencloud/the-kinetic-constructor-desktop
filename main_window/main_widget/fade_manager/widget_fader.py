from typing import TYPE_CHECKING, Optional, Union
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsItem
from PyQt6.QtCore import (
    QParallelAnimationGroup,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
)
from Enums.Enums import Glyph
from base_widgets.pictograph.grid.non_radial_points_group import (
    NonRadialPointsGroup,
)
from main_window.main_widget.fade_manager.fadeable_opacity_effect import (
    FadableOpacityEffect,
)

if TYPE_CHECKING:
    from main_window.main_widget.fade_manager.fade_manager import FadeManager


class WidgetFader:
    def __init__(self, manager: "FadeManager"):
        self.manager = manager
        # Cache animation groups keyed by a tuple of (widget_ids, fade_in, duration)
        self._animation_cache = {}

    def _get_animation_cache_key(
        self, widgets: list[QWidget], fade_in: bool, duration: int
    ):
        # Create a key based on the unique ids of the widgets, fade direction, and duration.
        widget_ids = tuple(sorted(id(w) for w in widgets))
        return (widget_ids, fade_in, duration)

    def fade_widgets(self, widgets, fade_in, duration, callback=None):
        if not widgets:
            if callback:
                callback()
            return

        # 🛑 Before fading, ensure no active QPainter exists!
        for widget in widgets:
            widget.update()

        self.manager.graphics_effect_remover.clear_graphics_effects(widgets)

        if not self.manager.fades_enabled():
            for widget in widgets:
                effect = self._ensure_opacity_effect(widget)
                effect.setOpacity(1.0 if fade_in else 0.0)
                widget.setGraphicsEffect(effect)
            if callback:
                callback()
            return

        key = self._get_animation_cache_key(widgets, fade_in, duration)
        anim_group = self._animation_cache.get(key)
        if anim_group and anim_group.state() == QParallelAnimationGroup.State.Running:
            if callback:
                anim_group.finished.connect(callback)
            return

        anim_group = QParallelAnimationGroup(self.manager)
        for widget in widgets:
            effect = self._ensure_opacity_effect(widget)
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(0.0 if fade_in else 1.0)
            animation.setEndValue(1.0 if fade_in else 0.0)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim_group.addAnimation(animation)

        if callback:
            anim_group.finished.connect(callback)

        self._animation_cache[key] = anim_group
        anim_group.finished.connect(lambda: self._animation_cache.pop(key, None))
        anim_group.start()

    def _ensure_opacity_effect(self, widget: QWidget) -> QGraphicsOpacityEffect:
        effect = widget.graphicsEffect()
        if effect and isinstance(effect, QGraphicsOpacityEffect):
            return effect  # Don't create a new effect if one already exists

        effect = FadableOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        return effect

    def fade_and_update(
        self,
        widgets: list[QWidget],
        callback: Union[callable, tuple[callable, callable]] = None,
        duration: int = 250,
    ) -> None:
        fade_enabled = self.manager.fades_enabled()

        def on_fade_out_finished():
            self.manager.graphics_effect_remover.clear_graphics_effects(widgets)
            if callback:
                if isinstance(callback, tuple):
                    callback[0]()
                    if fade_enabled:
                        self.fade_widgets(
                            widgets,
                            True,
                            duration,
                            lambda: QTimer.singleShot(0, callback[1]),
                        )
                    else:
                        for widget in widgets:
                            effect = self._ensure_opacity_effect(widget)
                            effect.setOpacity(1.0)
                            widget.setGraphicsEffect(effect)
                        callback[1]()
                else:
                    callback()
                    if fade_enabled:
                        self.fade_widgets(widgets, True, duration)
                    else:
                        for widget in widgets:
                            effect = self._ensure_opacity_effect(widget)
                            effect.setOpacity(1.0)
                            widget.setGraphicsEffect(effect)

        if fade_enabled:
            self.fade_widgets(widgets, False, duration, on_fade_out_finished)
        else:
            for widget in widgets:
                effect = self._ensure_opacity_effect(widget)
                effect.setOpacity(1.0)
                widget.setGraphicsEffect(effect)
            on_fade_out_finished()

    def fade_visibility_items_to_opacity(
        self,
        visibility_element: Union[Glyph, NonRadialPointsGroup],
        opacity: float,
        duration: int = 300,
        callback: Optional[callable] = None,
    ) -> None:
        if not visibility_element:
            if callback:
                callback()
            return
        items = self._get_corresponding_items(visibility_element)
        self.manager.graphics_effect_remover.clear_graphics_effects(
            [visibility_element]
        )
        anim_group = QParallelAnimationGroup(self.manager)
        for item in items:
            self.manager.graphics_effect_remover.clear_graphics_effects([item])
            if isinstance(item, QGraphicsItem):
                item.setOpacity(opacity)
            elif isinstance(item, QWidget):
                effect = self._ensure_opacity_effect(item)
                start_opacity = effect.opacity() if effect else 1.0
                animation = QPropertyAnimation(effect, b"opacity")
                animation.setDuration(duration)
                animation.setStartValue(start_opacity)
                animation.setEndValue(opacity)
                animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
                anim_group.addAnimation(animation)
        if callback:
            anim_group.finished.connect(callback)
        anim_group.start()

    def _get_corresponding_items(
        self, element: Union[Glyph, NonRadialPointsGroup]
    ) -> list[Union[Glyph, NonRadialPointsGroup]]:
        if element.name == "TKA":
            items = element.get_all_items()
        elif element.name == "VTG":
            items = [element]
        elif element.name == "Elemental":
            items = [element]
        elif element.name == "Positions":
            items = element.get_all_items()
        elif element.name == "Reversals":
            items = list(element.reversal_items.values())
        elif element.name == "non_radial_points":
            items = element.child_points
        return items

    def fade_widgets_and_element(
        self,
        widgets: list[QWidget],
        element: Union[Glyph, NonRadialPointsGroup],
        opacity: float,
        duration: int = 300,
        callback: Optional[callable] = None,
    ) -> None:
        if not widgets and not element:
            if callback:
                callback()
            return

        anim_group = QParallelAnimationGroup(self.manager)
        for widget in widgets:
            effect = self._ensure_opacity_effect(widget)
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(effect.opacity() if effect else 1.0)
            animation.setEndValue(opacity)
            animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim_group.addAnimation(animation)

        if isinstance(element, QGraphicsItem):
            element.setOpacity(opacity)
        elif element:
            items = self._get_corresponding_items(element)
            for item in items:
                if isinstance(item, QGraphicsItem):
                    item.setOpacity(opacity)
                elif isinstance(item, QWidget):
                    effect = self._ensure_opacity_effect(item)
                    animation = QPropertyAnimation(effect, b"opacity")
                    animation.setDuration(duration)
                    animation.setStartValue(effect.opacity() if effect else 1.0)
                    animation.setEndValue(opacity)
                    animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
                    anim_group.addAnimation(animation)

        if callback:
            anim_group.finished.connect(callback)
        anim_group.start()
