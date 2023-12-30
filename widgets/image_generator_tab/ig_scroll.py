from typing import TYPE_CHECKING
from constants import LETTER
from widgets.image_generator_tab.ig_pictograph import IGPictograph
from widgets.pictograph_scroll_area import PictographScrollArea

if TYPE_CHECKING:
    from widgets.image_generator_tab.ig_tab import IGTab
    from widgets.main_widget import MainWidget


class IGScrollArea(PictographScrollArea):
    def __init__(self, main_widget: "MainWidget", ig_tab: "IGTab") -> None:
        super().__init__(main_widget, ig_tab)
        self.main_widget = main_widget
        self.ig_tab = ig_tab

    def update_pictographs(self, letter) -> None:
        while self.layout.count():
            widget = self.layout.takeAt(0).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        for motion_dict_collection in self.main_widget.letters.values():
            for i, motion_dict in enumerate(motion_dict_collection):
                if motion_dict[LETTER] == letter:
                    ig_pictograph: IGPictograph = self._create_pictograph(
                        motion_dict, "ig"
                    )
                    self.pictographs[motion_dict[LETTER]] = ig_pictograph
                    ig_pictograph.update_pictograph()
                    ig_pictograph.view.resize_ig_pictograph()
                    row = i // self.COLUMN_COUNT
                    col = i % self.COLUMN_COUNT
                    self.layout.addWidget(ig_pictograph.view, row, col)

        self.update_scroll_area_content()

    def update_scroll_area_content(self) -> None:
        self.container.adjustSize()
        self.layout.update()
        self.updateGeometry()
