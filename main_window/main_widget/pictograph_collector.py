from typing import TYPE_CHECKING, Callable, Iterator

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget
    from base_widgets.pictograph.pictograph import Pictograph


class PictographCollector:
    def __init__(self, main_widget: "MainWidget") -> None:
        self.main_widget = main_widget

    def collect_all_pictographs(self) -> list["Pictograph"]:
        collectors: list[Callable[[], list["Pictograph"]]] = [
            self._collect_from_graph_editor,
            self._collect_from_advanced_start_pos_picker,
            self._collect_from_start_pos_picker,
            self._collect_from_sequence_beat_frame,
            self._collect_from_pictograph_cache,
            self._collect_from_option_picker,
            self._collect_from_codex,
            self._collect_from_settings_dialog,
        ]
        return list(self._collect_pictographs(collectors))

    def _collect_pictographs(
        self, collectors: list[Callable[[], list["Pictograph"]]]
    ) -> Iterator["Pictograph"]:
        for collector in collectors:
            yield from collector()

    def _collect_from_advanced_start_pos_picker(self) -> list["Pictograph"]:
        advanced_start_pos_picker = (
            self.main_widget.construct_tab.advanced_start_pos_picker
        )
        pictographs = []
        for list in advanced_start_pos_picker.start_pos_cache.values():
            for pictograph in list:
                if pictograph.elements.view and pictograph.elements.view.isVisible():
                    pictographs.append(pictograph)
        return pictographs

    def _collect_from_start_pos_picker(self) -> list["Pictograph"]:
        start_pos_picker = self.main_widget.construct_tab.start_pos_picker
        pictographs = []
        for pictograph in start_pos_picker.pictograph_frame.start_positions.values():
            if pictograph.elements.view and pictograph.elements.view.isVisible():
                pictographs.append(pictograph)
        return pictographs

    def _collect_from_sequence_beat_frame(self) -> list["Pictograph"]:
        sequence_workbench = self.main_widget.sequence_workbench
        beat_frame = sequence_workbench.sequence_beat_frame
        beat_views = beat_frame.beat_views
        pictographs = []
        pictographs.append(beat_frame.start_pos_view.beat)
        pictographs.extend(beat_view.beat for beat_view in beat_views)
        return pictographs

    def _collect_from_pictograph_cache(self) -> list["Pictograph"]:
        pictographs = []
        for pictograph_key_with_scene in self.main_widget.pictograph_cache.values():
            pictographs.extend(
                pictograph
                for pictograph in pictograph_key_with_scene.values()
                if pictograph.elements.view and pictograph.elements.view.isVisible()
            )
        return pictographs

    def _collect_from_option_picker(self) -> list["Pictograph"]:
        option_picker = self.main_widget.construct_tab.option_picker
        return [option for option in option_picker.option_pool if option]

    def _collect_from_graph_editor(self) -> list["Pictograph"]:
        sequence_workbench = self.main_widget.sequence_workbench
        graph_editor = sequence_workbench.graph_editor
        return [graph_editor.pictograph_container.GE_view.pictograph]

    def _collect_from_codex(self) -> list["Pictograph"]:
        codex = self.main_widget.codex
        codex_views = codex.section_manager.codex_views.values()
        return [view.pictograph for view in codex_views]

    def _collect_from_settings_dialog(self) -> list["Pictograph"]:
        visibility_pictograph = (
            self.main_widget.settings_dialog.ui.visibility_tab.pictograph
        )
        if visibility_pictograph:
            return [visibility_pictograph]
        return []
