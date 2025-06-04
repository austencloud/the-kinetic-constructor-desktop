from typing import TYPE_CHECKING
from PyQt6.QtCore import QObject

from main_window.main_widget.fade_manager.widget_and_stack_fader import (
    WidgetAndStackFader,
)
from .graphics_effect_remover import GraphicsEffectRemover
from .widget_fader import WidgetFader
from .stack_fader import StackFader
from .parallel_stack_fader import ParallelStackFader

if TYPE_CHECKING:
    from ..main_widget import MainWidget
    from core.application_context import ApplicationContext


class FadeManager(QObject):
    def __init__(
        self, main_widget: "MainWidget", app_context: "ApplicationContext" = None
    ):
        super().__init__()
        self.main_widget = main_widget
        self.app_context = app_context or getattr(main_widget, "app_context", None)
        self.widget_fader = WidgetFader(self)
        self.stack_fader = StackFader(self)
        self.parallel_stack_fader = ParallelStackFader(self)
        self.widget_and_stack_fader = WidgetAndStackFader(self)
        self.graphics_effect_remover = GraphicsEffectRemover(self)
        self._temporary_fade_override = (
            None  # Initialize the temporary override attribute
        )

    def set_fades_enabled(self, enabled: bool) -> None:
        """Temporarily override fade settings."""
        self._temporary_fade_override = enabled

    def fades_enabled(self) -> bool:
        """Check if fades are enabled through dependency injection or fallback to legacy."""
        # Check for temporary override first
        if self._temporary_fade_override is not None:
            return self._temporary_fade_override

        try:
            if self.app_context and hasattr(self.app_context, "settings_manager"):
                return (
                    self.app_context.settings_manager.global_settings.get_enable_fades()
                )
        except (AttributeError, RuntimeError):
            pass

        # Fallback to legacy AppContext for backward compatibility
        try:
            from src.settings_manager.global_settings.app_context import AppContext

            return AppContext.settings_manager().global_settings.get_enable_fades()
        except (AttributeError, RuntimeError):
            # If all else fails, default to True (fades enabled)
            return True
