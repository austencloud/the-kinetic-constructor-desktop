from typing import TYPE_CHECKING, Callable, Iterator

from base_widgets.pictograph.elements.views.lesson_pictograph_view import (
    LessonPictographView,
)

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
            self._collect_from_lessons,
        ]
        return list(self._collect_pictographs(collectors))

    def _collect_pictographs(
        self, collectors: list[Callable[[], list["Pictograph"]]]
    ) -> Iterator["Pictograph"]:
        for collector in collectors:
            yield from collector()

    def _collect_from_advanced_start_pos_picker(self) -> list["Pictograph"]:
        # Use dynamic lookup instead of cached reference
        construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
        if not construct_tab or not hasattr(construct_tab, "advanced_start_pos_picker"):
            return []

        advanced_start_pos_picker = construct_tab.advanced_start_pos_picker
        if not advanced_start_pos_picker or not hasattr(
            advanced_start_pos_picker, "start_options"
        ):
            return []

        pictographs = []
        for pictograph in advanced_start_pos_picker.start_options.values():
            if pictograph:  # Additional null check
                pictographs.append(pictograph)
        return pictographs

    def _collect_from_start_pos_picker(self) -> list["Pictograph"]:
        # Use dynamic lookup instead of cached reference
        construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
        if not construct_tab or not hasattr(construct_tab, "start_pos_picker"):
            return []

        start_pos_picker = construct_tab.start_pos_picker
        if not start_pos_picker or not hasattr(start_pos_picker, "pictograph_frame"):
            return []

        pictograph_frame = start_pos_picker.pictograph_frame
        if not pictograph_frame or not hasattr(pictograph_frame, "start_positions"):
            return []

        pictographs = []
        for pictograph in pictograph_frame.start_positions.values():
            if pictograph:  # Additional null check
                pictographs.append(pictograph)
        return pictographs

    def _collect_from_sequence_beat_frame(self) -> list["Pictograph"]:
        # Use dynamic lookup instead of cached reference
        sequence_workbench = self.main_widget.get_widget("sequence_workbench")
        if not sequence_workbench or not hasattr(sequence_workbench, "beat_frame"):
            return []

        beat_frame = sequence_workbench.beat_frame
        if not beat_frame:
            return []

        pictographs = []

        # Collect from start_pos_view if available
        if hasattr(beat_frame, "start_pos_view") and beat_frame.start_pos_view:
            if (
                hasattr(beat_frame.start_pos_view, "beat")
                and beat_frame.start_pos_view.beat
            ):
                pictographs.append(beat_frame.start_pos_view.beat)

        # Collect from beat_views if available
        if hasattr(beat_frame, "beat_views") and beat_frame.beat_views:
            for beat_view in beat_frame.beat_views:
                if beat_view and hasattr(beat_view, "beat") and beat_view.beat:
                    pictographs.append(beat_view.beat)

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
        construct_tab = self.main_widget.tab_manager.get_tab_widget("construct")
        if construct_tab and hasattr(construct_tab, "option_picker"):
            return [
                option for option in construct_tab.option_picker.option_pool if option
            ]
        return []

    def _collect_from_graph_editor(self) -> list["Pictograph"]:
        sequence_workbench = self.main_widget.get_widget("sequence_workbench")
        if sequence_workbench and hasattr(sequence_workbench, "graph_editor"):
            graph_editor = sequence_workbench.graph_editor
            ge_view = graph_editor.pictograph_container.GE_view
            return [ge_view.pictograph]
        return []

    def _collect_from_codex(self) -> list["Pictograph"]:
        codex = self.main_widget.get_widget("codex")
        if codex and hasattr(codex, "section_manager"):
            codex_views = codex.section_manager.codex_views.values()
            return [view.pictograph for view in codex_views]
        return []

    def _collect_from_settings_dialog(self) -> list["Pictograph"]:
        # Use dynamic lookup instead of cached reference
        settings_dialog = self.main_widget.get_widget("settings_dialog")
        if not settings_dialog or not hasattr(settings_dialog, "ui"):
            return []

        ui = settings_dialog.ui
        if not ui or not hasattr(ui, "visibility_tab"):
            return []

        visibility_tab = ui.visibility_tab
        if not visibility_tab or not hasattr(visibility_tab, "pictograph"):
            return []

        visibility_pictograph = visibility_tab.pictograph
        if visibility_pictograph:
            return [visibility_pictograph]
        return []

    def _collect_from_lessons(self) -> list["Pictograph"]:
        # Use dynamic lookup instead of cached reference
        learn_tab = self.main_widget.tab_manager.get_tab_widget("learn")
        if not learn_tab or not hasattr(learn_tab, "lessons"):
            return []

        lesson_widgets_dict = learn_tab.lessons
        if not lesson_widgets_dict:
            return []

        pictographs = []
        views: list["LessonPictographView"] = []

        # Safely get lessons
        lesson1 = lesson_widgets_dict.get("Lesson1")
        lesson2 = lesson_widgets_dict.get("Lesson2")
        lesson3 = lesson_widgets_dict.get("Lesson3")

        # Collect from lesson1 if available
        if lesson1 and hasattr(lesson1, "question_widget"):
            question_widget = lesson1.question_widget
            if (
                question_widget
                and hasattr(question_widget, "renderer")
                and question_widget.renderer
                and hasattr(question_widget.renderer, "view")
                and question_widget.renderer.view
                and hasattr(question_widget.renderer.view, "pictograph")
            ):
                pictograph = question_widget.renderer.view.pictograph
                if pictograph:
                    pictographs.append(pictograph)

        # Collect from lesson2 answers if available
        if lesson2 and hasattr(lesson2, "answers_widget"):
            answers_widget = lesson2.answers_widget
            if (
                answers_widget
                and hasattr(answers_widget, "renderer")
                and answers_widget.renderer
                and hasattr(answers_widget.renderer, "pictograph_views")
            ):
                pictograph_views = answers_widget.renderer.pictograph_views
                if pictograph_views:
                    views.extend([view for view in pictograph_views.values() if view])

        # Collect from lesson3 if available
        if lesson3 and hasattr(lesson3, "question_widget"):
            question_widget = lesson3.question_widget
            if (
                question_widget
                and hasattr(question_widget, "renderer")
                and question_widget.renderer
                and hasattr(question_widget.renderer, "view")
                and question_widget.renderer.view
                and hasattr(question_widget.renderer.view, "pictograph")
            ):
                pictograph = question_widget.renderer.view.pictograph
                if pictograph:
                    pictographs.append(pictograph)

        # Collect from lesson3 answers if available
        if lesson3 and hasattr(lesson3, "answers_widget"):
            answers_widget = lesson3.answers_widget
            if (
                answers_widget
                and hasattr(answers_widget, "renderer")
                and answers_widget.renderer
                and hasattr(answers_widget.renderer, "pictograph_views")
            ):
                pictograph_views = answers_widget.renderer.pictograph_views
                if pictograph_views:
                    views.extend([view for view in pictograph_views.values() if view])

        # Extract pictographs from views
        for view in views:
            if view and hasattr(view, "pictograph") and view.pictograph:
                pictographs.append(view.pictograph)

        # Filter out None values
        pictographs = [pictograph for pictograph in pictographs if pictograph]
        return pictographs
