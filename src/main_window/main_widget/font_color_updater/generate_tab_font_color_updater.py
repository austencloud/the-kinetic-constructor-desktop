from typing import TYPE_CHECKING
from .base_font_color_updater import BaseFontColorUpdater

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class GenerateTabFontColorUpdater(BaseFontColorUpdater):
    def __init__(self, main_widget: "MainWidget", font_color: str):
        super().__init__(font_color)
        self.main_widget = main_widget

    def update(self):
        gen_tab = self._get_generate_tab()
        if not gen_tab:
            return  # Graceful fallback if generate tab is not available

        labels = [
            gen_tab.length_adjuster.length_label,
            gen_tab.length_adjuster.length_value_label,
            gen_tab.turn_intensity.intensity_label,
            gen_tab.turn_intensity.intensity_value_label,
        ]

        self._apply_font_colors(labels)

    def _get_generate_tab(self):
        """Get the generate tab using the new MVVM architecture with graceful fallbacks."""
        try:
            # Try to get generate tab through the new coordinator pattern
            return self.main_widget.tab_manager.get_tab_widget("generate")
        except AttributeError:
            # Fallback: try through tab_manager for backward compatibility
            try:
                return self.main_widget.tab_manager.get_tab_widget("generate")
            except AttributeError:
                # Final fallback: try direct access for legacy compatibility
                try:
                    if hasattr(self.main_widget, "generate_tab"):
                        return self.main_widget.generate_tab
                except AttributeError:
                    pass
        return None
