from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QGraphicsOpacityEffect,
    QStackedLayout,
    QApplication,
)
from PyQt6.QtCore import (
    QObject,
    QPropertyAnimation,
    QAbstractAnimation,
    QEasingCurve,
    pyqtSlot,
    QParallelAnimationGroup,
)

if TYPE_CHECKING:
    from main_widget.main_widget import MainWidget


class MainWidgetFadeManager(QObject):
    """Manages fade-out/fade-in animations for your single stacked widget."""

    duration = 300

    def __init__(self, main_widget: "MainWidget"):
        super().__init__(main_widget)
        self.main_widget = main_widget
        self._old_opacity: Optional[QGraphicsOpacityEffect] = None
        self._new_opacity: Optional[QGraphicsOpacityEffect] = None
        self._is_animating = False

    def fade_to_tab(self, stack: QStackedLayout, new_index: int):
        """
        new_index corresponds to the pages in mw.content_stack:
          0 -> Build
          1 -> Generate
          2 -> Browse
          3 -> Learn
          4 -> Write
        """
        if self._is_animating:
            return
        self.stack = stack
        old_index = self.stack.currentIndex()
        if old_index == new_index:
            return

        self._fade_stack(old_index, new_index)

    def _fade_stack(self, old_index: int, new_index: int):
        self._is_animating = True

        self.old_widget = self.stack.widget(old_index)
        self.new_widget = self.stack.widget(new_index)
        if not self.old_widget or not self.new_widget:
            return

        self._old_opacity = self._ensure_opacity_effect(self.old_widget)
        self._new_opacity = self._ensure_opacity_effect(self.new_widget)

        self.fade_out = QPropertyAnimation(self._old_opacity, b"opacity", self)
        self.fade_out.setDuration(self.duration)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fade_out.finished.connect(lambda: self._switch_and_fade_in(new_index))

        self.fade_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    @pyqtSlot()
    def _switch_and_fade_in(self, new_index: int):
        self.stack.setCurrentIndex(new_index)

        if self._old_opacity:
            self._old_opacity.setOpacity(1.0)

        self.new_widget = self.stack.currentWidget()
        if self.new_widget and self._new_opacity:
            self._new_opacity.setOpacity(0.0)

        # Fade in
        self.fade_in = QPropertyAnimation(self._new_opacity, b"opacity", self)
        self.fade_in.setDuration(self.duration)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_in.finished.connect(self._on_fade_in_finished)

        self.fade_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    @pyqtSlot()
    def _on_fade_in_finished(self):
        self._is_animating = False

    def _ensure_opacity_effect(self, widget: QWidget) -> QGraphicsOpacityEffect:
        effect = widget.graphicsEffect()
        if not effect or not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        return effect

    def fade_both_stacks_in_parallel(
        self,
        right_stack: QStackedLayout,
        right_new_index: int,
        left_stack: QStackedLayout,
        left_new_index: int,
        width_ratio: tuple[float, float] = (0.5, 0.5),
    ):
        """
        Fades out both stacks in parallel, then in the 'finished' callback,
        we switch indexes, do any resizing, and fade them in.
        """
        old_right_idx = right_stack.currentIndex()
        old_left_idx = left_stack.currentIndex()
        if old_right_idx == right_new_index and old_left_idx == left_new_index:
            return

        self.old_right_widget = right_stack.widget(old_right_idx)
        self.old_left_widget = left_stack.widget(old_left_idx)
        self.new_right_widget = right_stack.widget(right_new_index)
        self.new_left_widget = left_stack.widget(left_new_index)

        if not self.old_right_widget or not self.old_left_widget:
            return

        self.fade_out_group = QParallelAnimationGroup(self)  # Keep a reference
        self.old_right_effect = self._ensure_opacity_effect(self.old_right_widget)
        self.old_left_effect = self._ensure_opacity_effect(self.old_left_widget)

        self.anim_out_right = QPropertyAnimation(
            self.old_right_effect, b"opacity", self
        )
        self.anim_out_right.setDuration(self.duration)
        self.anim_out_right.setStartValue(1.0)
        self.anim_out_right.setEndValue(0.0)
        self.anim_out_right.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.anim_out_left = QPropertyAnimation(self.old_left_effect, b"opacity", self)
        self.anim_out_left.setDuration(self.duration)
        self.anim_out_left.setStartValue(1.0)
        self.anim_out_left.setEndValue(0.0)
        self.anim_out_left.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fade_out_group.addAnimation(self.anim_out_right)
        self.fade_out_group.addAnimation(self.anim_out_left)

        self.fade_out_group.finished.connect(
            lambda: self._switch_resize_and_fade_in_both(
                right_stack, right_new_index, left_stack, left_new_index, width_ratio
            )
        )

        self.fade_out_group.start()
        self._is_animating = True

    def _switch_resize_and_fade_in_both(
        self,
        right_stack: QStackedLayout, right_new_index: int,
        left_stack: QStackedLayout, left_new_index: int,
        width_ratio: tuple[float, float]
    ):
        right_stack.setCurrentIndex(right_new_index)
        left_stack.setCurrentIndex(left_new_index)

        self.old_right_effect.setOpacity(1.0)
        self.old_left_effect.setOpacity(1.0)

        self.new_right_widget.hide()
        self.new_left_widget.hide()
        nr_effect = self._ensure_opacity_effect(self.new_right_widget)
        nl_effect = self._ensure_opacity_effect(self.new_left_widget)
        nr_effect.setOpacity(0.0)
        nl_effect.setOpacity(0.0)

        total_width = self.main_widget.width()
        left_width = int(total_width * width_ratio[0])
        right_width = int(total_width * width_ratio[1])
        self.main_widget.left_stack.setMaximumWidth(left_width)
        self.main_widget.right_stack.setMaximumWidth(right_width)

        self._update_layout(self.main_widget)

        self.new_right_widget.show()
        self.new_left_widget.show()

        self.fade_in_group = QParallelAnimationGroup(self)
        anim_in_right = QPropertyAnimation(nr_effect, b"opacity", self)
        anim_in_right.setDuration(self.duration)
        anim_in_right.setStartValue(0.0)
        anim_in_right.setEndValue(1.0)
        anim_in_right.setEasingCurve(QEasingCurve.Type.InOutQuad)

        anim_in_left = QPropertyAnimation(nl_effect, b"opacity", self)
        anim_in_left.setDuration(self.duration)
        anim_in_left.setStartValue(0.0)
        anim_in_left.setEndValue(1.0)
        anim_in_left.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fade_in_group.addAnimation(anim_in_right)
        self.fade_in_group.addAnimation(anim_in_left)
        self.fade_in_group.finished.connect(self._on_fade_in_finished)
        self.fade_in_group.start()

    def _update_layout(self, widget: QWidget):
        layout = widget.layout()
        if layout:
            layout.invalidate()
            layout.activate()
        widget.resize(widget.size().width(), widget.size().height())
