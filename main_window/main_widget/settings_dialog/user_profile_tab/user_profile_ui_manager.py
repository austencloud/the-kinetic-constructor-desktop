from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QFont

if TYPE_CHECKING:
    from main_window.main_widget.settings_dialog.user_profile_tab.user_profile_tab import (
        UserProfileTab,
    )


class UserProfileUIManager:
    """Handles UI updates, font scaling, and warnings for UserProfileTab."""

    def __init__(self, user_profile_tab: "UserProfileTab"):
        self.tab = user_profile_tab

    def update_user_button_styles(self):
        """Updates the styles of all user buttons to show the selected user."""
        current_user = self.tab.user_manager.get_current_user()
        for user_name, user_button in self.tab.tab_controller.user_buttons.items():
            user_button.set_button_style(user_name == current_user)

    def confirm_deletion(self, user_name):
        """Asks for user confirmation before deletion."""
        reply = QMessageBox.question(
            self.tab,
            "Confirm Deletion",
            f"Are you sure you want to delete user '{user_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        return reply == QMessageBox.StandardButton.Yes

    def show_warning(self, message):
        """Shows a warning message."""
        QMessageBox.warning(self.tab, "Warning", message)

    def get_title_font(self):
        """Returns a styled font for the header."""
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        return font

    def handle_resize_event(self):
        """Handles resizing of the user buttons."""
        self.tab.header.setFont(self.tab.ui_manager.get_title_font())
        for user_button in self.tab.tab_controller.user_buttons.values():
            user_button.button.setFont(user_button._get_scaled_font())
