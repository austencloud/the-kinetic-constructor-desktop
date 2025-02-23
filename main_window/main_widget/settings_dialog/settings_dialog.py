from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QDialog, QHBoxLayout
from PyQt6.QtCore import QEvent

from .settings_dialog_styler import SettingsDialogStyler
from .settings_dialog_ui import SettingsDialogUI
from main_window.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class SettingsDialog(QDialog):
    def __init__(self, main_widget: "MainWidget"):
        super().__init__(main_widget)
        self.main_widget = main_widget
        self.setWindowTitle("Settings")

        self.ui = SettingsDialogUI(self)
        self.ui.setup_ui()
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.ui)
        self.setLayout(main_layout)

        self.update_size()
        SettingsDialogStyler.apply_styles(self)

    def showEvent(self, event: QEvent):
        """Triggered every time the dialog is shown."""
        super().showEvent(event)
        print("[DEBUG] Settings dialog shown - Restoring last tab")

        last_tab = (
            AppContext.settings_manager().global_settings.get_current_settings_dialog_tab()
        )

        # Ensure tab exists, otherwise default to first tab
        if last_tab not in self.ui.tab_selection_manager.tabs:
            print(f"[WARNING] Tab '{last_tab}' not found, defaulting to first tab.")
            last_tab = next(
                iter(self.ui.tab_selection_manager.tabs)
            )  # First tab as fallback

        tab_index = self.ui.tab_selection_manager.get_tab_index(last_tab)

        self.ui.sidebar.setCurrentRow(tab_index)
        self.ui.content_area.setCurrentIndex(tab_index)

        if last_tab == "User Profile":
            self.ui.user_profile_tab.tab_controller.populate_user_buttons()
            self.ui.user_profile_tab.ui_manager.update_active_user_from_settings()
            self.ui.user_profile_tab.update()

        elif last_tab == "Prop Type":
            self.ui.prop_type_tab.update_active_prop_type_from_settings()

        elif last_tab == "Visibility":
            self.ui.visibility_tab.buttons_widget.update_visibility_buttons_from_settings()

    def update_size(self, force: bool = False):
        """Updates the size of the settings dialog, only resizing if necessary."""
        height = int(self.main_widget.height() * 0.8)
        width = int(height * 1.2)

        if force or (self.width() != width or self.height() != height):
            self.setFixedSize(width, height)

    def resizeEvent(self, event: QEvent):
        """Handle window resizing more efficiently."""
        self.update_size(force=False)  # Only resize if it has changed
        super().resizeEvent(event)
