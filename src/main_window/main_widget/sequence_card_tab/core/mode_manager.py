# src/main_window/main_widget/sequence_card_tab/core/mode_manager.py
from enum import Enum
from typing import TYPE_CHECKING, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import logging

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab


class SequenceCardMode(Enum):
    """Enumeration of available sequence card modes."""

    DICTIONARY = "dictionary"
    GENERATION = "generation"


class SequenceCardModeManager(QObject):
    """
    Manages the current mode of the sequence card tab.

    Handles switching between Dictionary Mode (existing sequences) and
    Generation Mode (on-demand sequence creation).
    """

    mode_changed = pyqtSignal(object)  # Emits SequenceCardMode
    mode_switch_requested = pyqtSignal(object)  # Emits SequenceCardMode

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        super().__init__()
        self.sequence_card_tab = sequence_card_tab
        self.current_mode = SequenceCardMode.DICTIONARY
        self._switching_in_progress = False
        self._initialization_complete = False

    def get_current_mode(self) -> SequenceCardMode:
        """Get the currently active mode."""
        return self.current_mode

    def complete_initialization(self):
        """Complete initialization and load saved mode preference."""
        if not self._initialization_complete:
            self._initialization_complete = True

            # CRITICAL FIX: Prevent automatic mode switching during initialization
            # This prevents automatic generation from being triggered
            if (
                hasattr(self.sequence_card_tab, "is_initializing")
                and self.sequence_card_tab.is_initializing
            ):
                logging.info(
                    "BLOCKED: Mode switching during sequence card tab initialization"
                )
                return

            # Now it's safe to load and apply saved mode preference
            saved_mode = self.load_mode_preference()
            if saved_mode != self.current_mode:
                # Only switch if the saved mode is different and available
                if self.is_mode_available(saved_mode):
                    logging.info(f"Auto-switching to saved mode: {saved_mode.value}")
                    self.switch_mode(saved_mode)

    def is_dictionary_mode(self) -> bool:
        """Check if currently in dictionary mode."""
        return self.current_mode == SequenceCardMode.DICTIONARY

    def is_generation_mode(self) -> bool:
        """Check if currently in generation mode."""
        return self.current_mode == SequenceCardMode.GENERATION

    def is_switching(self) -> bool:
        """Check if a mode switch is currently in progress."""
        return self._switching_in_progress

    def request_mode_switch(self, new_mode: SequenceCardMode) -> bool:
        """
        Request a mode switch. Returns True if switch can proceed.

        Args:
            new_mode: The mode to switch to

        Returns:
            bool: True if switch can proceed, False if blocked
        """
        if self._switching_in_progress:
            return False

        if new_mode == self.current_mode:
            return True  # Already in requested mode

        # Emit request signal for validation
        self.mode_switch_requested.emit(new_mode)
        return True

    def switch_mode(self, new_mode: SequenceCardMode) -> bool:
        """
        Switch to the specified mode.

        Args:
            new_mode: The mode to switch to

        Returns:
            bool: True if switch was successful, False otherwise
        """
        if self._switching_in_progress:
            return False

        if new_mode == self.current_mode:
            return True  # Already in requested mode

        try:
            self._switching_in_progress = True

            # Clear current display
            self._clear_current_display()

            # Update mode
            old_mode = self.current_mode
            self.current_mode = new_mode

            # Update UI elements based on new mode
            self._update_ui_for_mode(new_mode)

            # Save mode preference
            self._save_mode_preference(new_mode)

            # Emit mode changed signal
            self.mode_changed.emit(new_mode)

            return True

        except Exception as e:
            # Revert to previous mode on error
            self.current_mode = old_mode
            print(f"Error switching to {new_mode.value} mode: {e}")
            return False

        finally:
            self._switching_in_progress = False

    def _clear_current_display(self):
        """Clear the current display content."""
        try:
            # Clear the content area
            if hasattr(self.sequence_card_tab, "content_area"):
                self.sequence_card_tab.content_area.clear_layout()

            # Cancel any in-progress loading
            if hasattr(self.sequence_card_tab, "printable_displayer"):
                if (
                    hasattr(self.sequence_card_tab.printable_displayer, "manager")
                    and self.sequence_card_tab.printable_displayer.manager.is_loading
                ):
                    self.sequence_card_tab.printable_displayer.manager.cancel_loading()

        except Exception as e:
            print(f"Error clearing display: {e}")

    def _update_ui_for_mode(self, mode: SequenceCardMode):
        """Update UI elements based on the current mode."""
        try:
            # Update header description
            if hasattr(self.sequence_card_tab, "header"):
                if mode == SequenceCardMode.DICTIONARY:
                    self.sequence_card_tab.header.description_label.setText(
                        "Browse sequences from the dictionary"
                    )
                elif mode == SequenceCardMode.GENERATION:
                    self.sequence_card_tab.header.description_label.setText(
                        "Generate new sequences on-demand"
                    )

            # Update sidebar visibility and state
            if hasattr(self.sequence_card_tab, "nav_sidebar"):
                sidebar = self.sequence_card_tab.nav_sidebar

                if mode == SequenceCardMode.DICTIONARY:
                    # Show length selection and level filter
                    if hasattr(sidebar, "scroll_area"):
                        sidebar.scroll_area.setVisible(True)
                    if hasattr(sidebar, "level_filter"):
                        sidebar.level_filter.setVisible(True)

                elif mode == SequenceCardMode.GENERATION:
                    # Hide dictionary-specific controls
                    if hasattr(sidebar, "scroll_area"):
                        sidebar.scroll_area.setVisible(False)
                    if hasattr(sidebar, "level_filter"):
                        sidebar.level_filter.setVisible(False)

        except Exception as e:
            print(f"Error updating UI for mode {mode.value}: {e}")

    def _save_mode_preference(self, mode: SequenceCardMode):
        """Save the current mode preference to settings."""
        try:
            if hasattr(self.sequence_card_tab, "settings_manager_obj"):
                settings = self.sequence_card_tab.settings_manager_obj
                if hasattr(settings, "settings_manager") and settings.settings_manager:
                    settings.settings_manager.set_setting(
                        "sequence_card_tab", "current_mode", mode.value
                    )
        except Exception as e:
            print(f"Error saving mode preference: {e}")

    def load_mode_preference(self) -> SequenceCardMode:
        """Load the saved mode preference from settings."""
        try:
            if hasattr(self.sequence_card_tab, "settings_manager_obj"):
                settings = self.sequence_card_tab.settings_manager_obj
                if hasattr(settings, "settings_manager") and settings.settings_manager:
                    saved_mode = settings.settings_manager.get_setting(
                        "sequence_card_tab",
                        "current_mode",
                        SequenceCardMode.DICTIONARY.value,
                    )

                    # Convert string back to enum
                    if saved_mode == SequenceCardMode.GENERATION.value:
                        return SequenceCardMode.GENERATION

            return SequenceCardMode.DICTIONARY

        except Exception as e:
            print(f"Error loading mode preference: {e}")
            return SequenceCardMode.DICTIONARY

    def get_mode_display_name(self, mode: Optional[SequenceCardMode] = None) -> str:
        """Get a human-readable display name for the mode."""
        if mode is None:
            mode = self.current_mode

        if mode == SequenceCardMode.DICTIONARY:
            return "Dictionary Mode"
        elif mode == SequenceCardMode.GENERATION:
            return "Generation Mode"
        else:
            return "Unknown Mode"

    def get_mode_description(self, mode: Optional[SequenceCardMode] = None) -> str:
        """Get a description of what the mode does."""
        if mode is None:
            mode = self.current_mode

        if mode == SequenceCardMode.DICTIONARY:
            return "Browse and filter sequences from the saved dictionary"
        elif mode == SequenceCardMode.GENERATION:
            return "Generate fresh sequences and view approved sequences as paginated previews"
        else:
            return "Unknown mode"

    def is_mode_available(self, mode: SequenceCardMode) -> bool:
        """Check if a specific mode is available for use."""
        if mode == SequenceCardMode.DICTIONARY:
            return True  # Dictionary mode is always available

        elif mode == SequenceCardMode.GENERATION:
            # Check if generate tab is available
            try:
                main_widget = self.sequence_card_tab.main_widget
                return (
                    hasattr(main_widget, "generate_tab")
                    and main_widget.generate_tab is not None
                )
            except:
                return False

        return False
