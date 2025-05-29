from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtCore import Qt


from base_widgets.base_beat_frame import BaseBeatFrame
from data.constants import (
    BLUE_ATTRS,
    END_ORI,
    END_POS,
    RED_ATTRS,
    SEQUENCE_START_POSITION,
    START_ORI,
    START_POS,
)
from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame_layout_manager import (
    TempBeatFrameLayoutManager,
)

from base_widgets.pictograph.pictograph import Pictograph
from main_window.main_widget.sequence_workbench.sequence_beat_frame.beat import Beat
from base_widgets.pictograph.elements.views.beat_view import (
    BeatView,
)

from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_export_manager import (
    ImageExportManager,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.start_pos_beat import (
    StartPositionBeat,
)
from main_window.main_widget.sequence_workbench.sequence_beat_frame.start_pos_beat_view import (
    StartPositionBeatView,
)
from src.settings_manager.global_settings.app_context import AppContext


if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import (
        BrowseTab,
    )


class TempBeatFrame(BaseBeatFrame):
    """The purpose of this class is to create images for use within the dictionary or the sequence card tab.
    This beat frame is never seen by the user."""

    def __init__(self, browse_tab: "BrowseTab") -> None:
        super().__init__(browse_tab.main_widget)
        self.main_widget = browse_tab.main_widget
        self.json_manager = AppContext.json_manager()
        self.settings_manager = AppContext.settings_manager()
        self.browse_tab = browse_tab

        self.initialized = True
        self.sequence_changed = False
        self.setObjectName("beat_frame")
        self.setStyleSheet("QFrame#beat_frame { background: transparent; }")
        self._init_beats()
        self._setup_components()
        self._setup_layout()

    def _init_beats(self):
        self.beat_views = [BeatView(self, number=i + 1) for i in range(64)]
        for beat in self.beat_views:
            beat.hide()

    def _setup_components(self) -> None:
        self.layout_manager = TempBeatFrameLayoutManager(self)
        self.start_pos_view = StartPositionBeatView(self)
        self.start_pos = StartPositionBeat(self)
        self.export_manager = ImageExportManager(self, TempBeatFrame)

    def _setup_layout(self) -> None:
        self.layout: QGridLayout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.start_pos_view, 0, 0)
        for i, beat in enumerate(self.beat_views):
            row, col = divmod(i, 8)
            self.layout.addWidget(beat, row + 1, col + 1)
        self.layout_manager.configure_beat_frame(16)

    def add_beat_to_sequence(self, new_beat: "Pictograph") -> None:
        next_beat_index = self.get.next_available_beat()

        if (
            next_beat_index is not None
            and self.beat_views[next_beat_index].is_filled is False
        ):
            self.beat_views[next_beat_index].set_beat(new_beat, next_beat_index + 1)
            self.json_manager.updater.update_current_sequence_file_with_beat(
                self.beat_views[next_beat_index].beat
            )
            self.update_current_word()
            self.adjust_layout_to_sequence_length()

    def adjust_layout_to_sequence_length(self):
        last_filled_index = self.get.next_available_beat() or len(self.beat_views)
        self.layout_manager.configure_beat_frame(last_filled_index)

    def get_last_filled_beat(self) -> BeatView:
        for beat_view in reversed(self.beat_views):
            if beat_view.is_filled:
                return beat_view
        return self.start_pos_view

    def on_beat_adjusted(self) -> None:
        current_sequence_json = self.json_manager.loader_saver.load_current_sequence()
        self.propogate_turn_adjustment(current_sequence_json)

    def propogate_turn_adjustment(self, current_sequence_json) -> None:
        for i, entry in enumerate(current_sequence_json):
            if i == 0:
                continue
            elif i == 1:
                self.update_start_pos_from_current_sequence_json(entry)
            elif i > 1:
                beat = self.beat_views[i - 2].beat
                if beat:
                    if beat.state.pictograph_data != entry:
                        beat.managers.updater.update_pictograph(entry)

    def update_start_pos_from_current_sequence_json(self, entry: dict) -> None:
        entry[RED_ATTRS][START_ORI] = entry[RED_ATTRS][END_ORI]
        entry[BLUE_ATTRS][START_ORI] = entry[BLUE_ATTRS][END_ORI]
        entry[START_POS] = entry[END_POS]
        self.start_pos_view.start_pos.managers.updater.update_pictograph(entry)

    def populate_beat_frame_from_json(
        self, current_sequence_json: list[dict[str, str]]
    ) -> None:
        # Check if there's any sequence data to process
        if not current_sequence_json:
            return

        # Try to get the construct_tab, but handle the case where it might not be available
        self.construct_tab = self._get_construct_tab()
        if not self.construct_tab:
            # If we're being called from the sequence card tab image exporter,
            # the construct_tab might not be available
            print(
                "Warning: construct_tab not available, using simplified sequence loading"
            )
            self._simplified_populate_from_json(current_sequence_json)
            return

        # Clear the current sequence without resetting to start pos picker
        self.clear_sequence(should_reset_to_start_pos_picker=False)

        # Convert the start position entry to a start position pictograph
        start_pos_beat = self.construct_tab.start_pos_picker.convert_current_sequence_json_entry_to_start_pos_pictograph(
            current_sequence_json
        )
        self.json_manager.start_pos_handler.set_start_position_data(start_pos_beat)
        self.start_pos_view.set_start_pos(start_pos_beat)

        # Populate the sequence with the remaining pictographs
        for pictograph_data in current_sequence_json[1:]:
            if pictograph_data.get(SEQUENCE_START_POSITION):
                continue
            self.populate_sequence(pictograph_data)

        # Update the last beat
        last_beat = self.get_last_filled_beat().beat
        self.construct_tab.last_beat = last_beat

        # Update the UI if needed
        if self.construct_tab.start_pos_picker.isVisible():
            self.construct_tab.transition_to_option_picker()

    def _simplified_populate_from_json(
        self, current_sequence_json: list[dict[str, str]]
    ) -> None:
        """
        A simplified version of populate_beat_frame_from_json that doesn't require the construct_tab.
        This is used when loading sequences for image export.

        Args:
            current_sequence_json: The sequence data to load
        """
        # Reset the beat frame
        self._reset_beat_frame()

        # Find the start position entry (usually the second entry)
        start_pos_entry = None
        for entry in current_sequence_json:
            if entry.get(SEQUENCE_START_POSITION):
                start_pos_entry = entry
                break

        # If we found a start position entry, set it
        if start_pos_entry:
            start_pos = StartPositionBeat(self)
            start_pos.managers.updater.update_pictograph(start_pos_entry)
            self.start_pos_view.set_start_pos(start_pos)

        # Populate the sequence with the remaining pictographs
        for pictograph_data in current_sequence_json:
            if pictograph_data.get(SEQUENCE_START_POSITION):
                continue
            self.populate_sequence(pictograph_data)

    def populate_sequence(self, pictograph_data: dict) -> None:
        pictograph = Beat(self)
        pictograph.managers.updater.update_pictograph(pictograph_data)
        self.add_beat_to_sequence(pictograph)
        self.update_current_word()

    def update_current_word(self):
        self.current_word = self.get.current_word()

    def load_sequence_data(self, sequence_data: list[dict]) -> None:
        """
        Load sequence data into the beat frame.

        This is an alias for load_sequence() to maintain compatibility with
        the synchronous image generator and other components that expect this method name.

        Args:
            sequence_data: A list of dictionaries containing the sequence data
        """
        self.load_sequence(sequence_data)

    def load_sequence(self, sequence: list[dict]) -> None:
        """
        Load a sequence into the beat frame.

        This method is used by the image exporter to load a sequence for image generation.
        It clears the current sequence and populates the beat frame with the provided sequence data.

        Args:
            sequence: A list of dictionaries containing the sequence data
        """
        if not sequence:
            return

        # Clear the current sequence
        self.clear_sequence(should_reset_to_start_pos_picker=False)

        # Populate the beat frame with the sequence data
        self.populate_beat_frame_from_json(sequence)

    def clear_sequence(self, should_reset_to_start_pos_picker=True) -> None:
        self._reset_beat_frame()

        # Check if construct_tab attribute exists before using it
        if hasattr(self, "construct_tab"):
            if should_reset_to_start_pos_picker:
                self.construct_tab.transition_to_start_pos_picker()
            self.construct_tab.last_beat = self.start_pos

        # Clear the current sequence file
        self.json_manager.loader_saver.clear_current_sequence_file()

        # Configure the beat frame if needed
        if self.settings_manager.global_settings.get_grow_sequence():
            self.layout_manager.configure_beat_frame(0)

    def _reset_beat_frame(self) -> None:
        for beat_view in self.beat_views:
            beat_view.setScene(beat_view.blank_beat)
            beat_view.is_filled = False
        self.start_pos_view.setScene(self.start_pos_view.blank_beat)
        self.start_pos_view.is_filled = False

    def _get_construct_tab(self):
        """Get the construct tab using the new MVVM architecture with graceful fallbacks."""
        try:
            # Try to get construct tab through the new coordinator pattern
            return self.main_widget.get_tab_widget("construct")
        except AttributeError:
            # Fallback: try through tab_manager for backward compatibility
            try:
                return self.main_widget.tab_manager.get_tab_widget("construct")
            except AttributeError:
                # Final fallback: try direct access for legacy compatibility
                try:
                    if hasattr(self.main_widget, "construct_tab"):
                        return self.main_widget.construct_tab
                except AttributeError:
                    pass
        return None
