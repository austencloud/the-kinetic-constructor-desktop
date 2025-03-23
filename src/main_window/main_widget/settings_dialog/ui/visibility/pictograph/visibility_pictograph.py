from typing import TYPE_CHECKING

from base_widgets.pictograph.pictograph import Pictograph
from data.constants import (
    ALPHA1,
    BLUE,
    END_POS,
    LETTER,
    MOTION_TYPE,
    RED,
    START_POS,
    PRO,
    ALPHA3,
)

if TYPE_CHECKING:
    from ..visibility_tab import VisibilityTab
    from .......base_widgets.pictograph.elements.views.visibility_pictograph_view import (
        VisibilityPictographView,
    )


class VisibilityPictograph(Pictograph):
    """Special class for the visibility tab pictograph."""

    example_data = {
        LETTER: "A",
        START_POS: ALPHA1,
        END_POS: ALPHA3,
        f"{BLUE}_{MOTION_TYPE}": PRO,
        f"{RED}_{MOTION_TYPE}": PRO,
    }
    view: "VisibilityPictographView" = None

    def __init__(self, tab: "VisibilityTab"):
        super().__init__()
        self.state.red_reversal = True
        self.state.blue_reversal = True
        self.tab = tab
        self.main_widget = tab.main_widget
        pictograph_data = self.main_widget.pictograph_data_loader.find_pictograph_data(
            self.example_data
        )
        self.settings = self.main_widget.settings_manager.visibility
        self.managers.updater.update_pictograph(pictograph_data)
        self.glyphs = self.managers.get.glyphs()
        self.motion_set = self.managers.get.motions()
        for glyph in self.glyphs:
            glyph.setVisible(True)
        self.elements.grid.toggle_non_radial_points(True)
        for motion in self.motion_set.values():
            motion.prop.setVisible(True)
            motion.arrow.setVisible(True)

    def update_opacity(self, element_name: str, state: bool):
        """Animate the opacity of the corresponding element."""
        target_opacity = 1.0 if state else 0.1

        # Handle props and arrows by color
        if element_name in [RED, BLUE]:
            prop = self.elements.props.get(element_name)
            arrow = self.elements.arrows.get(element_name)
            self.main_widget.fade_manager.widget_fader.fade_visibility_items_to_opacity(
                prop, target_opacity
            )
            self.main_widget.fade_manager.widget_fader.fade_visibility_items_to_opacity(
                arrow, target_opacity
            )

            # Also update the reversal if this is a prop color
            # This ensures the reversal opacity is updated when motion visibility changes
            if self.elements.reversal_glyph:
                reversal_item = self.elements.reversal_glyph.reversal_items.get(
                    element_name
                )
                if reversal_item:
                    self.main_widget.fade_manager.widget_fader.fade_visibility_items_to_opacity(
                        reversal_item, target_opacity
                    )

                # Always update the whole reversal glyph positioning
                self.elements.reversal_glyph.update_reversal_symbols(
                    is_visibility_pictograph=True
                )

        # Handle existing glyph case
        elif element_name in ["TKA", "Reversals", "VTG", "Elemental", "Positions"]:
            for glyph in self.glyphs:
                if glyph.name == element_name:
                    self.main_widget.fade_manager.widget_fader.fade_visibility_items_to_opacity(
                        glyph, target_opacity
                    )
        # Handle non-radial points
        elif element_name == "non_radial_points":
            non_radial_points = self.elements.grid.items.get(
                f"{self.elements.grid.grid_mode}_nonradial"
            )
            if non_radial_points:
                self.main_widget.fade_manager.widget_fader.fade_visibility_items_to_opacity(
                    non_radial_points, target_opacity
                )
