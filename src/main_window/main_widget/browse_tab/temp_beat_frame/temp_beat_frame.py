"""
Temporary Beat Frame for Image Export and Sequence Processing

This module provides a lightweight beat frame implementation for use in
image export operations and sequence processing where a full sequence
workbench is not available.

REDESIGN NOTE: This is a compatibility module to maintain existing
functionality while the browse tab architecture is being modernized.
"""

from typing import TYPE_CHECKING, Union
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSize
import logging

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab
    from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab
    from main_window.main_widget.main_widget import MainWidget

logger = logging.getLogger(__name__)


class TempBeatFrame(QWidget):
    """
    Temporary beat frame for image export and sequence processing.

    This class provides a minimal beat frame implementation that can be used
    for image export operations without requiring a full sequence workbench.
    It maintains compatibility with existing code while providing the necessary
    interface for image creation and export operations.
    """

    def __init__(self, parent_widget: Union["BrowseTab", "SequenceCardTab"]):
        """
        Initialize the temporary beat frame.

        Args:
            parent_widget: The parent widget (BrowseTab or SequenceCardTab)
        """
        super().__init__()

        # Store parent reference and extract main_widget
        self.parent_widget = parent_widget

        # Initialize sequence data storage
        self.sequence_data = []

        # Set browse_tab attribute for ImageExportManager compatibility
        # If parent is a BrowseTab, reference it; otherwise set to None
        if (
            hasattr(parent_widget, "__class__")
            and "BrowseTab" in parent_widget.__class__.__name__
        ):
            self.browse_tab = parent_widget
        else:
            self.browse_tab = None

        # Extract main_widget from different parent types
        if hasattr(parent_widget, "main_widget"):
            self.main_widget = parent_widget.main_widget
        elif hasattr(parent_widget, "browse_tab") and hasattr(
            parent_widget.browse_tab, "main_widget"
        ):
            self.main_widget = parent_widget.browse_tab.main_widget
        else:
            # Fallback: try to get from app context
            try:
                from src.settings_manager.global_settings.app_context import AppContext

                app_context = AppContext()
                if hasattr(app_context, "main_widget"):
                    self.main_widget = app_context.main_widget
                else:
                    logger.warning(
                        "Could not determine main_widget from parent or app context"
                    )
                    self.main_widget = None
            except Exception as e:
                logger.warning(f"Failed to get main_widget from app context: {e}")
                self.main_widget = None

        # Initialize image export manager
        self._setup_image_export_manager()

        # Initialize start position view for compatibility
        self._setup_start_pos_view()

        # Initialize populator for compatibility with generation system
        self._setup_populator()

        # Initialize beat factory for compatibility with generation system
        self._setup_beat_factory()

        # Set default size
        self.setFixedSize(QSize(400, 300))

        logger.debug(
            f"TempBeatFrame initialized with parent: {type(parent_widget).__name__}"
        )

    def load_sequence(self, sequence_data):
        """Load sequence data for processing."""
        self.sequence_data = sequence_data
        logger.debug(
            f"Loaded sequence with {len(sequence_data) if sequence_data else 0} beats"
        )

    def set_current_word(self, word):
        """Set current word for overlay generation."""
        self.current_word = word
        logger.debug(f"Set current word to: {word}")

    def _setup_start_pos_view(self):
        """Setup the start position view for compatibility."""
        try:
            # Create a mock start position view for compatibility
            from PyQt6.QtWidgets import QGraphicsView

            class MockStartPosView(QGraphicsView):
                def __init__(self, parent):
                    super().__init__(parent)
                    self.is_start_pos = True
                    self.beat = None  # Add beat attribute for compatibility
                    self.start_pos = None  # Add start_pos attribute for compatibility
                    self.pictograph = None  # Add pictograph attribute for compatibility
                    self.is_filled = False  # Add is_filled attribute for compatibility

                def set_start_pos(self, start_pos_beat):
                    """Mock method for setting start position."""
                    self.beat = start_pos_beat  # Store the beat for compatibility
                    self.start_pos = start_pos_beat  # Store as start_pos too
                    self.pictograph = start_pos_beat  # Store as pictograph too
                    self.is_filled = start_pos_beat is not None

                    # Ensure the start_pos_beat has a valid scene rect if it's not None
                    if start_pos_beat is not None and hasattr(
                        start_pos_beat, "setSceneRect"
                    ):
                        # Set a default scene rect if it doesn't have one
                        from PyQt6.QtCore import QRectF

                        if start_pos_beat.sceneRect().isEmpty():
                            start_pos_beat.setSceneRect(QRectF(0, 0, 950, 950))

                    logger.debug("Mock start_pos_view.set_start_pos() called")

            self.start_pos_view = MockStartPosView(self)
            logger.debug("Mock start position view created for compatibility")
        except Exception as e:
            logger.warning(f"Failed to create start position view: {e}")
            self.start_pos_view = None

    def _setup_populator(self):
        """Setup populator for compatibility with generation system."""
        try:

            class MockPopulator:
                def __init__(self, temp_beat_frame):
                    self.temp_beat_frame = temp_beat_frame

                def modify_layout_for_chosen_number_of_beats(self, beat_count):
                    """Mock implementation of layout modification for beat count."""
                    logger.debug(
                        f"Mock populator: modify_layout_for_chosen_number_of_beats({beat_count})"
                    )
                    # This is a no-op for TempBeatFrame since it doesn't have a real layout manager
                    # The generation system just needs this method to exist

            self.populator = MockPopulator(self)
            logger.debug("Mock populator created for compatibility")
        except Exception as e:
            logger.warning(f"Failed to create populator: {e}")
            self.populator = None

    def _setup_beat_factory(self):
        """Setup beat factory for compatibility with generation system."""
        try:

            class MockBeatFactory:
                def __init__(self, temp_beat_frame):
                    self.temp_beat_frame = temp_beat_frame

                def create_new_beat_and_add_to_sequence(
                    self,
                    pictograph_data,
                    override_grow_sequence=False,
                    update_word=False,
                    update_level=False,
                    reversal_info=None,
                    select_beat=False,
                ):
                    """Mock implementation of beat creation for generation system."""
                    logger.debug(
                        f"Mock beat_factory: create_new_beat_and_add_to_sequence() called"
                    )
                    # This is a no-op for TempBeatFrame since it doesn't have a real beat system
                    # The generation system just needs this method to exist
                    return True

            self.beat_factory = MockBeatFactory(self)
            logger.debug("Mock beat factory created for compatibility")
        except Exception as e:
            logger.warning(f"Failed to create beat factory: {e}")
            self.beat_factory = None

    def _setup_image_export_manager(self):
        """Setup the image export manager for this beat frame."""
        # Try to use real image export manager first, fall back to mock if needed
        try:
            if self.main_widget:
                # Try to create real image export manager
                self.image_export_manager = self._create_real_image_export_manager()
                logger.debug(
                    "Using real image export manager for dictionary regeneration"
                )
            else:
                # Fall back to mock if no main widget
                logger.debug(
                    "No main widget available, using mock image export manager"
                )
                self.image_export_manager = self._create_mock_image_export_manager()
        except Exception as e:
            logger.warning(f"Failed to create real image export manager: {e}")
            logger.debug("Falling back to mock image export manager")
            self.image_export_manager = self._create_mock_image_export_manager()

    def _create_real_image_export_manager(self):
        """Create a real image export manager using the actual ImageExportManager."""
        try:
            # Import the real ImageExportManager
            from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_export_manager import (
                ImageExportManager,
            )

            # Create real image export manager with this beat frame and its class
            real_export_manager = ImageExportManager(self, self.__class__)
            logger.debug("Successfully created real ImageExportManager")
            return real_export_manager

        except Exception as e:
            logger.error(f"Failed to create real ImageExportManager: {e}")
            raise

    def _create_mock_image_export_manager(self):
        """Create a mock image export manager for compatibility."""

        class MockImageExportManager:
            def __init__(self):
                self.image_creator = self._create_mock_image_creator()
                self.settings_manager = self._create_mock_settings_manager()

            def _create_mock_image_creator(self):
                from PyQt6.QtGui import QImage, QColor

                class MockImageCreator:
                    def __init__(self):
                        self.export_manager = self

                    def create_sequence_image(
                        self,
                        sequence,
                        options=None,
                        dictionary=False,
                        fullscreen_preview=False,
                    ):
                        """Create a mock sequence image."""
                        # Return a simple placeholder image
                        placeholder = QImage(800, 600, QImage.Format.Format_RGB32)
                        placeholder.fill(QColor(240, 240, 240))
                        return placeholder

                return MockImageCreator()

            def _create_mock_settings_manager(self):
                class MockSettingsManager:
                    def __init__(self):
                        self.image_export = MockImageExportSettings()

                class MockImageExportSettings:
                    def get_all_image_export_options(self):
                        return {
                            "add_beat_numbers": True,
                            "add_reversal_symbols": True,
                            "add_user_info": True,
                            "add_word": True,
                            "add_difficulty_level": True,
                            "include_start_position": True,
                            "combined_grids": False,
                            "additional_height_top": 0,
                            "additional_height_bottom": 0,
                        }

                return MockSettingsManager()

        logger.debug("Created mock image export manager for compatibility")
        return MockImageExportManager()

    def get_main_widget(self) -> "MainWidget":
        """
        Get the main widget reference.

        Returns:
            The main widget instance
        """
        return self.main_widget

    def get_json_manager(self):
        """
        Get the JSON manager from the main widget.

        Returns:
            The JSON manager instance
        """
        if self.main_widget and hasattr(self.main_widget, "json_manager"):
            return self.main_widget.json_manager
        return None

    def get_settings_manager(self):
        """
        Get the settings manager from the main widget.

        Returns:
            The settings manager instance
        """
        if self.main_widget and hasattr(self.main_widget, "settings_manager"):
            return self.main_widget.settings_manager
        return None

    def get_image_export_manager(self):
        """
        Get the image export manager.

        Returns:
            The image export manager instance
        """
        return self.image_export_manager

    def get(self):
        """Get interface for compatibility with beat frame interface."""
        return MockGetInterface(self)

    def set(self):
        """Set interface for compatibility with beat frame interface."""
        return MockSetInterface(self)

    def cleanup(self):
        """Clean up resources when the beat frame is no longer needed."""
        try:
            if hasattr(self, "image_export_manager") and self.image_export_manager:
                if hasattr(self.image_export_manager, "cleanup"):
                    self.image_export_manager.cleanup()
            logger.debug("TempBeatFrame cleanup completed")
        except Exception as e:
            logger.warning(f"Error during TempBeatFrame cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction


class MockGetInterface:
    """Mock get interface for beat frame compatibility."""

    def __init__(self, temp_beat_frame):
        """Initialize with reference to temp beat frame."""
        self.temp_beat_frame = temp_beat_frame

    def current_word(self):
        """Get current word (mock implementation)."""
        return getattr(self.temp_beat_frame, "_current_word", "TEST")


class MockSetInterface:
    """Mock set interface for beat frame compatibility."""

    def __init__(self, temp_beat_frame):
        """Initialize with reference to temp beat frame."""
        self.temp_beat_frame = temp_beat_frame

    def current_word(self, word):
        """Set current word (mock implementation)."""
        self.temp_beat_frame._current_word = word
        logger.debug(f"Mock: Set current word to: {word}")


# Compatibility aliases for existing code
TempBeatFrameClass = TempBeatFrame
