from datetime import datetime
from typing import TYPE_CHECKING

# Try both absolute and relative imports for compatibility
try:
    from src.settings_manager.global_settings.app_context import AppContext
except ImportError:
    try:
        from settings_manager.global_settings.app_context import AppContext
    except ImportError:
        # Fallback for testing environments
        class AppContext:
            @staticmethod
            def settings_manager():
                class MockImageExportSettings:
                    def get_image_export_setting(self, setting_name):
                        return (
                            True if setting_name == "include_start_position" else False
                        )

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

                class MockSettingsManager:
                    def __init__(self):
                        self.image_export = MockImageExportSettings()

                return MockSettingsManager()


from .image_export_layout_handler import ImageExportLayoutHandler
from .image_creator.image_creator import ImageCreator
from .image_export_beat_factory import ImageExportBeatFactory
from .image_saver import ImageSaver


if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
        SequenceBeatFrame,
    )


class ImageExportManager:
    last_save_directory = None
    include_start_pos: bool

    def __init__(
        self,
        beat_frame: "SequenceBeatFrame",
        beat_frame_class: type,
    ) -> None:
        self.beat_frame = beat_frame
        self.main_widget = beat_frame.main_widget
        self.settings_manager = AppContext.settings_manager()

        if beat_frame_class.__name__ == "SequenceWorkbenchBeatFrame":
            self.sequence_workbench = beat_frame.sequence_workbench
        elif beat_frame_class.__name__ == "TempBeatFrame":
            self.dictionary_widget = beat_frame.browse_tab
        # Get the include_start_position setting from image export settings
        self.include_start_pos = (
            AppContext.settings_manager().image_export.get_image_export_setting(
                "include_start_position"
            )
        )
        # Initialize components
        self.layout_handler = ImageExportLayoutHandler(self)
        self.beat_factory = ImageExportBeatFactory(self, beat_frame_class)
        self.image_creator = ImageCreator(self)
        self.image_saver = ImageSaver(self)

    def export_image_directly(self, sequence=None) -> None:
        """Immediately exports the image using current settings and opens the save dialog."""
        if sequence is None:
            try:
                json_manager = self.main_widget.app_context.json_manager
                sequence = json_manager.loader_saver.load_current_sequence()

            except AttributeError:
                # Fallback when json_manager not available
                sequence = []

        # Validate sequence parameter - ensure it's a list/sequence, not a boolean or other type
        if not isinstance(sequence, (list, tuple)):
            print(
                f"Warning: export_image_directly received invalid sequence type: {type(sequence)}, value: {sequence}"
            )
            # Try to extract sequence if it's a dict with 'sequence' key
            if isinstance(sequence, dict) and "sequence" in sequence:
                sequence = sequence["sequence"]
            else:
                # Fallback to empty sequence
                sequence = []

        # Ensure sequence is a list
        if not isinstance(sequence, list):
            sequence = []

        # Check if the sequence is empty (no beats and no start position)
        include_start_pos = self.settings_manager.image_export.get_image_export_setting(
            "include_start_position"
        )

        # Check if the sequence has any beats (excluding the start position)
        has_beats = len(sequence) >= 3

        if not has_beats and not include_start_pos:
            # If there's no start position to show, inform the user and return
            self.main_widget.sequence_workbench.indicator_label.show_message(
                "The sequence is empty and 'Show Start Position' is disabled."
            )
            return
        elif not has_beats and include_start_pos:
            # If there's only a start position and it's enabled, we'll export just that
            self.main_widget.sequence_workbench.indicator_label.show_message(
                "Exporting only the start position."
            )

        # Retrieve the export settings
        try:
            settings_manager = self.main_widget.app_context.settings_manager
            options = settings_manager.image_export.get_all_image_export_options()
            options["user_name"] = settings_manager.users.get_current_user()
            options["export_date"] = datetime.now().strftime("%m-%d-%Y")
        except AttributeError:
            # Fallback when settings_manager not available
            options = {
                "user_name": "Unknown",
                "export_date": datetime.now().strftime("%m-%d-%Y"),
            }

        # Generate the image
        image_creator = self.image_creator
        sequence_image = image_creator.create_sequence_image(
            sequence, options, dictionary=False, fullscreen_preview=False
        )

        # Save the image
        self.image_saver.save_image(sequence_image)
        # open the folder containing the image

        try:
            sequence_workbench = self.main_widget.widget_manager.get_widget(
                "sequence_workbench"
            )
            if sequence_workbench and hasattr(sequence_workbench, "indicator_label"):
                sequence_workbench.indicator_label.show_message(
                    "Image saved successfully!"
                )
        except AttributeError:
            # Fallback when sequence_workbench not available
            pass
