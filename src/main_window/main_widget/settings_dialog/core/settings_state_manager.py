"""
Settings State Manager for tracking changes and managing settings state.
"""

from typing import Dict, Any, Optional, Callable, Set
from PyQt6.QtCore import QObject, pyqtSignal
import copy
import json
import logging
import time


class SettingsStateManager(QObject):
    """
    Manages settings state, change tracking, and validation.
    Provides comprehensive state management for the settings dialog.
    """

    # Signals for state changes
    settings_changed = pyqtSignal(str, Any, Any)  # setting_key, old_value, new_value
    validation_failed = pyqtSignal(str, str)  # setting_key, error_message
    state_reset = pyqtSignal()
    backup_created = pyqtSignal(str)  # backup_path
    backup_restored = pyqtSignal(str)  # backup_path

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._original_state: Dict[str, Any] = {}
        self._current_state: Dict[str, Any] = {}
        self._modified_keys: Set[str] = set()
        self._validators: Dict[str, Callable] = {}
        self._change_callbacks: Dict[str, list] = {}

        # Initialize state
        self._capture_original_state()

    def _capture_original_state(self):
        """Capture the original state of all settings when dialog opens."""
        try:
            # Capture browse tab settings (simplified - cache settings removed)
            browse_settings = self.settings_manager.browse_tab_settings
            self._original_state.update(
                {
                    "browse/sort_method": browse_settings.get_sort_method(),
                    "browse/current_section": browse_settings.get_current_section(),
                    "browse/current_filter": browse_settings.get_current_filter(),
                    "browse/browse_ratio": browse_settings.get_browse_ratio(),
                }
            )

            # Capture global settings
            global_settings = self.settings_manager.global_settings
            self._original_state.update(
                {
                    "global/current_tab": global_settings.get_current_tab(),
                    "global/grid_mode": global_settings.get_grid_mode(),
                    "global/prop_type": global_settings.get_prop_type(),
                    "global/background_type": global_settings.get_background_type(),
                    "global/grow_sequence": global_settings.get_grow_sequence(),
                    "global/enable_fades": global_settings.get_enable_fades(),
                    "global/show_welcome_screen": global_settings.get_show_welcome_screen(),
                }
            )

            # Copy to current state
            self._current_state = copy.deepcopy(self._original_state)

            logging.debug(
                f"Captured original state: {len(self._original_state)} settings"
            )

        except Exception as e:
            logging.error(f"Failed to capture original settings state: {e}")

    def register_validator(self, setting_key: str, validator: Callable[[Any], bool]):
        """Register a validator function for a specific setting."""
        self._validators[setting_key] = validator

    def register_change_callback(
        self, setting_key: str, callback: Callable[[Any, Any], None]
    ):
        """Register a callback for when a specific setting changes."""
        if setting_key not in self._change_callbacks:
            self._change_callbacks[setting_key] = []
        self._change_callbacks[setting_key].append(callback)

    def set_setting(self, setting_key: str, value: Any, validate: bool = True) -> bool:
        """
        Set a setting value with validation and change tracking.

        Args:
            setting_key: The setting identifier
            value: The new value
            validate: Whether to run validation

        Returns:
            True if setting was successfully set, False if validation failed
        """
        # Validate if requested
        if validate and setting_key in self._validators:
            try:
                if not self._validators[setting_key](value):
                    self.validation_failed.emit(setting_key, f"Invalid value: {value}")
                    return False
            except Exception as e:
                self.validation_failed.emit(setting_key, f"Validation error: {e}")
                return False

        # Get old value
        old_value = self._current_state.get(setting_key)

        # Update current state
        self._current_state[setting_key] = value

        # Track modification
        if value != self._original_state.get(setting_key):
            self._modified_keys.add(setting_key)
        else:
            self._modified_keys.discard(setting_key)

        # Emit change signal
        self.settings_changed.emit(setting_key, old_value, value)

        # Call registered callbacks
        if setting_key in self._change_callbacks:
            for callback in self._change_callbacks[setting_key]:
                try:
                    callback(old_value, value)
                except Exception as e:
                    logging.error(f"Error in change callback for {setting_key}: {e}")

        return True

    def get_setting(self, setting_key: str, default: Any = None) -> Any:
        """Get current value of a setting."""
        return self._current_state.get(setting_key, default)

    def is_modified(self, setting_key: Optional[str] = None) -> bool:
        """Check if settings have been modified."""
        if setting_key:
            return setting_key in self._modified_keys
        return len(self._modified_keys) > 0

    def get_modified_keys(self) -> Set[str]:
        """Get set of all modified setting keys."""
        return self._modified_keys.copy()

    def get_changes(self) -> Dict[str, Dict[str, Any]]:
        """Get dictionary of all changes with old and new values."""
        changes = {}
        for key in self._modified_keys:
            changes[key] = {
                "old": self._original_state.get(key),
                "new": self._current_state.get(key),
            }
        return changes

    def apply_changes(self) -> bool:
        """Apply all pending changes to the actual settings."""
        try:
            success_count = 0
            total_changes = len(self._modified_keys)

            for setting_key in self._modified_keys.copy():
                if self._apply_single_setting(setting_key):
                    success_count += 1

            if success_count == total_changes:
                # All changes applied successfully
                self._original_state = copy.deepcopy(self._current_state)
                self._modified_keys.clear()
                logging.info(f"Successfully applied {success_count} setting changes")
                return True
            else:
                logging.warning(
                    f"Applied {success_count}/{total_changes} setting changes"
                )
                return False

        except Exception as e:
            logging.error(f"Error applying settings changes: {e}")
            return False

    def _apply_single_setting(self, setting_key: str) -> bool:
        """Apply a single setting to the settings manager."""
        try:
            value = self._current_state[setting_key]

            # Route to appropriate settings manager
            if setting_key.startswith("browse/"):
                return self._apply_browse_setting(setting_key, value)
            elif setting_key.startswith("global/"):
                return self._apply_global_setting(setting_key, value)
            else:
                logging.warning(f"Unknown setting category: {setting_key}")
                return False

        except Exception as e:
            logging.error(f"Error applying setting {setting_key}: {e}")
            return False

    def _apply_browse_setting(self, setting_key: str, value: Any) -> bool:
        """Apply browse tab setting."""
        browse_settings = self.settings_manager.browse_tab_settings
        setting_name = setting_key.replace("browse/", "")

        setting_map = {
            "enable_disk_cache": browse_settings.set_enable_disk_cache,
            "cache_mode": browse_settings.set_cache_mode,
            "cache_max_size_mb": browse_settings.set_cache_max_size_mb,
            "cache_location": browse_settings.set_cache_location,
            "cache_quality_mode": browse_settings.set_cache_quality_mode,
            "preload_thumbnails": browse_settings.set_preload_thumbnails,
            "ultra_quality_enabled": browse_settings.set_ultra_quality_enabled,
            "sharpening_enabled": browse_settings.set_sharpening_enabled,
            "enhancement_enabled": browse_settings.set_enhancement_enabled,
        }

        if setting_name in setting_map:
            setting_map[setting_name](value)
            return True
        return False

    def _apply_global_setting(self, setting_key: str, value: Any) -> bool:
        """Apply global setting."""
        global_settings = self.settings_manager.global_settings
        setting_name = setting_key.replace("global/", "")

        setting_map = {
            "current_tab": global_settings.set_current_tab,
            "grid_mode": global_settings.set_grid_mode,
            "prop_type": global_settings.set_prop_type,
            "background_type": global_settings.set_background_type,
            "grow_sequence": global_settings.set_grow_sequence,
            "enable_fades": global_settings.set_enable_fades,
            "show_welcome_screen": global_settings.set_show_welcome_screen,
        }

        if setting_name in setting_map:
            setting_map[setting_name](value)
            return True
        return False

    def revert_changes(self):
        """Revert all changes back to original state."""
        self._current_state = copy.deepcopy(self._original_state)
        self._modified_keys.clear()
        self.state_reset.emit()
        logging.info("Reverted all settings changes")

    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        # This would need to be implemented based on default values
        # For now, we'll just clear modifications
        self.revert_changes()

    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of current settings."""
        if not backup_path:
            backup_path = f"settings_backup_{int(time.time())}.json"

        try:
            backup_data = {"timestamp": time.time(), "settings": self._current_state}

            with open(backup_path, "w") as f:
                json.dump(backup_data, f, indent=2)

            self.backup_created.emit(backup_path)
            logging.info(f"Settings backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logging.error(f"Failed to create settings backup: {e}")
            raise

    def restore_backup(self, backup_path: str) -> bool:
        """Restore settings from a backup file."""
        try:
            with open(backup_path, "r") as f:
                backup_data = json.load(f)

            if "settings" in backup_data:
                self._current_state = backup_data["settings"]
                self._modified_keys = set(self._current_state.keys())
                self.backup_restored.emit(backup_path)
                logging.info(f"Settings restored from backup: {backup_path}")
                return True
            else:
                logging.error("Invalid backup file format")
                return False

        except Exception as e:
            logging.error(f"Failed to restore settings backup: {e}")
            return False
