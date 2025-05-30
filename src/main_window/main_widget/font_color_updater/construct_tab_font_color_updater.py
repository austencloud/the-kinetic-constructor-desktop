from typing import TYPE_CHECKING
from .base_font_color_updater import BaseFontColorUpdater

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class ConstructTabFontColorUpdater(BaseFontColorUpdater):
    def __init__(self, main_widget: "MainWidget", font_color: str):
        super().__init__(font_color)
        self.main_widget = main_widget

    def update(self):
        """Apply font color to the ConstructTab-related widgets."""
        construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
        if construct_tab and hasattr(construct_tab, "option_picker"):
            # For example, any labels in the construct tab:
            construct_labels = [
                construct_tab.option_picker.reversal_filter.combo_box_label,
            ]
            self._apply_font_colors(construct_labels)
