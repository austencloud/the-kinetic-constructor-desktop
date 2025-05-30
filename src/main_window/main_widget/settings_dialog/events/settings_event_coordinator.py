"""
Settings event coordinator for the modern settings dialog.

Handles event coordination and signal management.
"""

from typing import TYPE_CHECKING, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget
import logging

if TYPE_CHECKING:
    from src.core.application_context import ApplicationContext
    from ..core.settings_state_manager import SettingsStateManager
    from ..tabs.settings_tab_manager import SettingsTabManager

logger = logging.getLogger(__name__)


class SettingsEventCoordinator(QObject):
    """
    Coordinates events and signals for the settings dialog.

    Responsibilities:
    - Handle button click events
    - Coordinate tab selection events
    - Manage settings change events
    - Handle validation and backup events
    """

    # Signals
    settings_applied = pyqtSignal(bool)  # success
    dialog_closed = pyqtSignal()

    def __init__(
        self,
        settings_manager,
        state_manager: "SettingsStateManager",
        tab_manager: "SettingsTabManager",
        app_context: "ApplicationContext" = None,
        parent=None,
    ):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.state_manager = state_manager
        self.tab_manager = tab_manager
        self.app_context = app_context

    def setup_connections(self, components: Dict[str, Any], tabs: Dict[str, QWidget]):
        """
        Setup all signal connections.

        Args:
            components: Dictionary of dialog components
            tabs: Dictionary of tab widgets
        """
        try:
            # Sidebar selection
            if "sidebar" in components:
                components["sidebar"].currentRowChanged.connect(self._on_tab_selected)

            # Action button connections
            if "action_buttons" in components:
                action_buttons = components["action_buttons"]
                action_buttons.apply_requested.connect(self._on_apply_settings)
                action_buttons.ok_requested.connect(self._on_ok_clicked)
                action_buttons.cancel_requested.connect(self._on_cancel_clicked)

            # Close button connection
            if "close_button" in components:
                components["close_button"].clicked.connect(self._on_cancel_clicked)

            # State manager connections
            self.state_manager.settings_changed.connect(self._on_setting_changed)
            self.state_manager.validation_failed.connect(self._on_validation_failed)
            self.state_manager.backup_created.connect(self._on_backup_created)
            self.state_manager.backup_restored.connect(self._on_backup_restored)

            # General Tab connections
            if "General" in tabs and hasattr(tabs["General"], "setting_changed"):
                tabs["General"].setting_changed.connect(self._on_tab_setting_changed)

            # Store components for event handling
            self.components = components
            self.tabs = tabs

            logger.debug("Event connections setup complete")

        except Exception as e:
            logger.error(f"Error setting up connections: {e}")

    def _on_tab_selected(self, index: int):
        """Handle tab selection."""
        try:
            if "content_area" in self.components:
                content_area = self.components["content_area"]
                if 0 <= index < content_area.count():
                    content_area.setCurrentIndex(index)

                    # Save current tab to settings
                    tab_order = self.tab_manager.get_tab_order()
                    tab_name = tab_order[index] if index < len(tab_order) else None
                    if tab_name and self.settings_manager:
                        self.settings_manager.global_settings.set_current_settings_dialog_tab(
                            tab_name
                        )

                    logger.debug(f"Selected tab: {tab_name} (index: {index})")

        except Exception as e:
            logger.error(f"Error selecting tab: {e}")

    def _on_setting_changed(self, setting_key: str, old_value: Any, new_value: Any):
        """Handle setting change from state manager."""
        try:
            # Update action buttons to reflect changes
            if "action_buttons" in self.components:
                has_changes = self.state_manager.is_modified()
                self.components["action_buttons"].set_has_changes(has_changes)

            logger.debug(
                f"Setting changed: {setting_key} = {new_value} (was: {old_value})"
            )

        except Exception as e:
            logger.error(f"Error handling setting change: {e}")

    def _on_tab_setting_changed(self, setting_key: str, old_value: Any, new_value: Any):
        """Handle setting change from tab widgets."""
        # This is already handled by the state manager, but we can add additional logic here if needed
        logger.debug(f"Tab setting changed: {setting_key} = {new_value}")

    def _on_validation_failed(self, setting_key: str, error_message: str):
        """Handle validation failure."""
        logger.warning(f"Validation failed for {setting_key}: {error_message}")
        # Could show a tooltip or status message here

    def _on_apply_settings(self):
        """Apply all pending settings changes."""
        try:
            success = self.state_manager.apply_changes()
            if "action_buttons" in self.components:
                self.components["action_buttons"].set_apply_success(success)
            self.settings_applied.emit(success)

            if success:
                logger.info("Settings applied successfully")
            else:
                logger.warning("Some settings failed to apply")

        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            if "action_buttons" in self.components:
                self.components["action_buttons"].set_apply_success(False)

    def _on_ok_clicked(self):
        """Handle OK button click."""
        try:
            # Apply changes first
            if self.state_manager.is_modified():
                success = self.state_manager.apply_changes()
                self.settings_applied.emit(success)

            # Close dialog (handled by coordinator)
            self.dialog_closed.emit()

        except Exception as e:
            logger.error(f"Error in OK action: {e}")

    def _on_cancel_clicked(self):
        """Handle Cancel button click."""
        try:
            # Revert any changes
            self.state_manager.revert_changes()

            # Close dialog (handled by coordinator)
            self.dialog_closed.emit()

        except Exception as e:
            logger.error(f"Error in Cancel action: {e}")

    def _on_backup_created(self, backup_path: str):
        """Handle backup created signal."""
        logger.info(f"Backup created successfully: {backup_path}")

    def _on_backup_restored(self, backup_path: str):
        """Handle backup restored signal."""
        logger.info(f"Backup restored successfully: {backup_path}")
        # Refresh all tabs after backup restoration
        self.tab_manager.refresh_all_tabs()

    def update_tab_on_show(self, tab_name: str):
        """Update specific tab when dialog is shown."""
        try:
            tab_widget = self.tab_manager.get_tab(tab_name)
            if not tab_widget:
                return

            # Call specific update methods based on tab type
            if tab_name == "Prop Type" and hasattr(
                tab_widget, "update_active_prop_type_from_settings"
            ):
                tab_widget.update_active_prop_type_from_settings()
            elif tab_name == "Visibility" and hasattr(tab_widget, "buttons_widget"):
                tab_widget.buttons_widget.update_visibility_buttons_from_settings()
            elif tab_name == "Beat Layout" and hasattr(
                tab_widget, "on_sequence_length_changed"
            ):
                # This requires access to main_widget - will be handled by coordinator
                pass
            elif tab_name == "Image Export" and hasattr(
                tab_widget, "update_image_export_tab_from_settings"
            ):
                tab_widget.update_image_export_tab_from_settings()
            elif tab_name == "Codex Exporter" and hasattr(
                tab_widget, "update_codex_exporter_tab_from_settings"
            ):
                tab_widget.update_codex_exporter_tab_from_settings()
            elif tab_name == "General" and hasattr(tab_widget, "refresh_settings"):
                tab_widget.refresh_settings()

        except Exception as e:
            logger.error(f"Error updating tab {tab_name} on show: {e}")
