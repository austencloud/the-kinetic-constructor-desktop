"""
Modern Action Buttons for settings dialog with comprehensive state management.
"""

from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QMessageBox,
    QFileDialog,
    QSizePolicy,
    QSpacerItem,
)
import logging
from .modern_components import ModernButton, StatusIndicator
from styles.glassmorphism_styler import GlassmorphismStyler


class ModernActionButtons(QWidget):
    """
    Modern action button panel with Apply, OK, Cancel, Reset, and Safety features.
    """

    # Signals
    apply_requested = pyqtSignal()
    ok_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    safe_settings_requested = pyqtSignal()
    backup_requested = pyqtSignal()
    restore_requested = pyqtSignal(str)  # backup_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_changes = False
        self._last_apply_success = True
        self._setup_ui()
        self._setup_connections()
        self._update_button_states()

    def _setup_ui(self):
        """Setup the action buttons UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            GlassmorphismStyler.SPACING["lg"],
            GlassmorphismStyler.SPACING["md"],
            GlassmorphismStyler.SPACING["lg"],
            GlassmorphismStyler.SPACING["lg"],
        )
        main_layout.setSpacing(GlassmorphismStyler.SPACING["md"])

        # Status indicator section
        self._create_status_section(main_layout)

        # Primary action buttons
        self._create_primary_buttons(main_layout)

        # Secondary action buttons
        self._create_secondary_buttons(main_layout)

        # Safety and backup buttons
        self._create_safety_buttons(main_layout)

    def _create_status_section(self, parent_layout):
        """Create status indicator section."""
        status_layout = QHBoxLayout()
        status_layout.setSpacing(GlassmorphismStyler.SPACING["sm"])

        # Status indicator
        self.status_indicator = StatusIndicator()
        status_layout.addWidget(self.status_indicator)

        # Status text
        self.status_label = QLabel("No changes")
        self.status_label.setFont(GlassmorphismStyler.get_font("body_small"))
        self.status_label.setStyleSheet(
            f"color: {GlassmorphismStyler.get_color('text_muted')};"
        )
        status_layout.addWidget(self.status_label)

        # Spacer
        status_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        parent_layout.addLayout(status_layout)

    def _create_primary_buttons(self, parent_layout):
        """Create primary action buttons (Apply, OK, Cancel)."""
        primary_layout = QHBoxLayout()
        primary_layout.setSpacing(GlassmorphismStyler.SPACING["sm"])

        # Apply button
        self.apply_button = ModernButton("Apply", "primary")
        self.apply_button.setToolTip("Apply changes without closing the dialog")
        primary_layout.addWidget(self.apply_button)

        # OK button
        self.ok_button = ModernButton("OK", "success")
        self.ok_button.setToolTip("Apply changes and close the dialog")
        primary_layout.addWidget(self.ok_button)

        # Cancel button
        self.cancel_button = ModernButton("Cancel", "secondary")
        self.cancel_button.setToolTip("Discard changes and close the dialog")
        primary_layout.addWidget(self.cancel_button)

        parent_layout.addLayout(primary_layout)

    def _create_secondary_buttons(self, parent_layout):
        """Create secondary action buttons (Reset)."""
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(GlassmorphismStyler.SPACING["sm"])

        # Reset to defaults button
        self.reset_button = ModernButton("Reset to Defaults", "warning")
        self.reset_button.setToolTip("Reset all settings to their default values")
        secondary_layout.addWidget(self.reset_button)

        # Spacer
        secondary_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        parent_layout.addLayout(secondary_layout)

    def _create_safety_buttons(self, parent_layout):
        """Create safety and backup buttons."""
        safety_layout = QHBoxLayout()
        safety_layout.setSpacing(GlassmorphismStyler.SPACING["sm"])

        # Save Settings button
        self.safe_button = ModernButton("Save Settings", "error")
        self.safe_button.setToolTip("Revert to known-good configuration")
        safety_layout.addWidget(self.safe_button)

        # Backup button
        self.backup_button = ModernButton("Create Backup", "secondary")
        self.backup_button.setToolTip("Create a backup of current settings")
        safety_layout.addWidget(self.backup_button)

        # Restore button
        self.restore_button = ModernButton("Restore Backup", "secondary")
        self.restore_button.setToolTip("Restore settings from a backup file")
        safety_layout.addWidget(self.restore_button)

        # Spacer
        safety_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        parent_layout.addLayout(safety_layout)

    def _setup_connections(self):
        """Setup button connections."""
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.safe_button.clicked.connect(self._on_safe_settings_clicked)
        self.backup_button.clicked.connect(self._on_backup_clicked)
        self.restore_button.clicked.connect(self._on_restore_clicked)

    def _on_apply_clicked(self):
        """Handle Apply button click."""
        if self._has_changes:
            self.apply_requested.emit()

    def _on_ok_clicked(self):
        """Handle OK button click."""
        self.ok_requested.emit()

    def _on_cancel_clicked(self):
        """Handle Cancel button click."""
        if self._has_changes:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Discard Changes",
                "You have unsaved changes. Are you sure you want to discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_requested.emit()
        else:
            self.cancel_requested.emit()

    def _on_reset_clicked(self):
        """Handle Reset button click."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "This will reset all settings to their default values. This action cannot be undone.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reset_requested.emit()

    def _on_safe_settings_clicked(self):
        """Handle Save Settings button click."""
        reply = QMessageBox.question(
            self,
            "Save Settings",
            "This will revert to a known-good configuration. Any unsaved changes will be lost.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.safe_settings_requested.emit()

    def _on_backup_clicked(self):
        """Handle Backup button click."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Create Settings Backup",
                "settings_backup.json",
                "JSON Files (*.json);;All Files (*)",
            )

            if file_path:
                self.backup_requested.emit()
                self._show_success_message("Backup created successfully!")

        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            self._show_error_message(f"Failed to create backup: {e}")

    def _on_restore_clicked(self):
        """Handle Restore button click."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Restore Settings Backup",
                "",
                "JSON Files (*.json);;All Files (*)",
            )

            if file_path:
                reply = QMessageBox.question(
                    self,
                    "Restore Backup",
                    f"This will restore settings from:\n{file_path}\n\n"
                    "Any unsaved changes will be lost. Are you sure?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.restore_requested.emit(file_path)

        except Exception as e:
            logging.error(f"Error restoring backup: {e}")
            self._show_error_message(f"Failed to restore backup: {e}")

    def set_has_changes(self, has_changes: bool):
        """Update the state to reflect whether there are pending changes."""
        self._has_changes = has_changes
        self._update_button_states()
        self._update_status_display()

    def set_apply_success(self, success: bool):
        """Update the state to reflect the last apply operation result."""
        self._last_apply_success = success

        if success:
            self.status_indicator.set_success()
            self._show_success_message("Settings applied successfully!", auto_hide=True)
        else:
            self.status_indicator.set_error()
            self._show_error_message("Failed to apply some settings", auto_hide=True)

    def _update_button_states(self):
        """Update button enabled/disabled states based on current state."""
        # Apply button only enabled if there are changes
        self.apply_button.setEnabled(self._has_changes)

        # OK button always enabled
        self.ok_button.setEnabled(True)

        # Cancel button always enabled
        self.cancel_button.setEnabled(True)

        # Reset button always enabled
        self.reset_button.setEnabled(True)

        # Safety buttons always enabled
        self.safe_button.setEnabled(True)
        self.backup_button.setEnabled(True)
        self.restore_button.setEnabled(True)

    def _update_status_display(self):
        """Update the status indicator and text."""
        if self._has_changes:
            self.status_indicator.set_modified()
            self.status_label.setText("Settings modified")
            self.status_label.setStyleSheet(
                f"color: {GlassmorphismStyler.get_color('warning')};"
            )
        else:
            self.status_indicator.set_normal()
            self.status_label.setText("No changes")
            self.status_label.setStyleSheet(
                f"color: {GlassmorphismStyler.get_color('text_muted')};"
            )

    def _show_success_message(self, message: str, auto_hide: bool = False):
        """Show a success message."""
        if auto_hide:
            # Update status label temporarily
            old_text = self.status_label.text()
            old_style = self.status_label.styleSheet()

            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"color: {GlassmorphismStyler.get_color('success')};"
            )

            # Revert after 3 seconds
            QTimer.singleShot(
                3000,
                lambda: (
                    self.status_label.setText(old_text),
                    self.status_label.setStyleSheet(old_style),
                ),
            )
        else:
            QMessageBox.information(self, "Success", message)

    def _show_error_message(self, message: str, auto_hide: bool = False):
        """Show an error message."""
        if auto_hide:
            # Update status label temporarily
            old_text = self.status_label.text()
            old_style = self.status_label.styleSheet()

            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"color: {GlassmorphismStyler.get_color('error')};"
            )

            # Revert after 5 seconds
            QTimer.singleShot(
                5000,
                lambda: (
                    self.status_label.setText(old_text),
                    self.status_label.setStyleSheet(old_style),
                ),
            )
        else:
            QMessageBox.critical(self, "Error", message)
