from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtSvg import QSvgRenderer

from data.letter_engine_data import letter_types
from objects.arrow.arrow import Arrow
from objects.prop.prop import Prop
from objects.motion import Motion
from constants.string_constants import (
    BLUE,
    COLOR,
    END_LOCATION,
    LETTER_SVG_DIR,
    MOTION_TYPE,
    RED,
    ROTATION_DIRECTION,
    START_LOCATION,
    TURNS,
    START_ORIENTATION,
    END_ORIENTATION,
    START_LAYER,
    END_LAYER,
    ARROW_LOCATION,
)
from utilities.TypeChecking.Letters import Letters
from utilities.letter_engine import LetterEngine
from utilities.TypeChecking.TypeChecking import (
    TYPE_CHECKING,
    Layers,
    MotionAttributesDicts,
    List,
    MotionTypes,
    Optional,
    Orientations,
    Tuple,
)
from widgets.graph_editor.pictograph.pictograph import Pictograph
from widgets.graph_editor.pictograph.pictograph_menu_handler import (
    PictographMenuHandler,
)
from widgets.graph_editor.pictograph.position_engines.arrow_positioner import (
    ArrowPositioner,
)
from widgets.graph_editor.pictograph.position_engines.prop_positioner import (
    PropPositioner,
)
from widgets.sequence_widget.beat_frame.beat_frame import BeatFrame

if TYPE_CHECKING:
    from widgets.main_widget import MainWidget


class Beat(Pictograph):
    def __init__(self, main_widget: "MainWidget", Sequence: "BeatFrame") -> None:
        super().__init__(main_widget, main_widget.graph_editor_widget.graph_editor)
        self.main_widget = main_widget
        self.sequence = Sequence

        self.setup_scene()
        self.setup_components(main_widget)

    def set_letter_renderer(self, letter: str) -> None:
        letter_type = self.get_current_letter_type()
        svg_path = f"{LETTER_SVG_DIR}/{letter_type}/{letter}.svg"
        renderer = QSvgRenderer(svg_path)
        if renderer.isValid():
            self.letter_item.setSharedRenderer(renderer)

    def setup_managers(self, main_widget: "MainWidget") -> None:
        self.pictograph_menu_handler = PictographMenuHandler(main_widget, self)
        self.arrow_positioner = ArrowPositioner(self)
        self.prop_positioner = PropPositioner(self)
        self.letter_engine = LetterEngine(self)

    ### GETTERS ###

    def get_current_arrow_coordinates(
        self,
    ) -> Tuple[Optional[QPointF], Optional[QPointF]]:
        red_position = None
        blue_position = None

        for arrow in self.arrows.values():
            center = arrow.pos() + arrow.boundingRect().center()
            if arrow.color == RED:
                red_position = center
            elif arrow.color == BLUE:
                blue_position = center
        return red_position, blue_position

    def get_state(self) -> List[MotionAttributesDicts]:
        state = []
        for motion in self.motions.values():
            state.append(
                {
                    COLOR: motion.color,
                    MOTION_TYPE: motion.motion_type,
                    ROTATION_DIRECTION: motion.rotation_direction,
                    ARROW_LOCATION: motion.arrow.motion.arrow_location,
                    START_LOCATION: motion.start_location,
                    END_LOCATION: motion.end_location,
                    TURNS: motion.turns,
                    START_LOCATION: motion.start_location,
                    END_LOCATION: motion.end_location,
                    START_ORIENTATION: motion.start_orientation,
                    END_ORIENTATION: motion.end_orientation,
                    START_LAYER: motion.start_layer,
                    END_LAYER: motion.end_layer,
                }
            )
        return state

    def get_current_letter_type(self) -> Optional[Letters]:
        if self.current_letter is not None:
            for letter_type, letters in letter_types.items():
                if self.current_letter in letters:
                    return letter_type
        else:
            return None

    def get_prop_by_color(self, color: str) -> Optional[Prop]:
        for prop in self.props.values():
            if prop.color == color:
                return prop

    ### HELPERS ###

    def add_to_sequence_callback(self) -> None:
        copied_scene = self.copy_scene()
        self.main_widget.sequence_widget.beat_frame.add_scene_to_sequence(copied_scene)
        self.clear_pictograph()

    def rotate_pictograph(self, direction: str) -> None:
        for arrow in self.arrows.values():
            arrow.manipulator.rotate_arrow(direction)

    def clear_pictograph(self) -> None:
        self.arrows = []
        self.props = []
        self.motions = []
        for item in self.items():
            if isinstance(item, Arrow) or isinstance(item, Prop):
                self.removeItem(item)

        self.update_pictograph()

    def clear_selections(self) -> None:
        for arrow in self.arrows.values():
            arrow.setSelected(False)
        for prop in self.props.values():
            prop.setSelected(False)
        self.dragged_prop = None
        self.dragged_arrow = None

    ### UPDATERS ###

    def update_pictograph(self) -> None:
        self.update_letter()
        self.update_arrows()
        self.update_props()

    def update_arrows(self) -> None:
        self.arrow_positioner.update_arrow_positions()

    def update_props(self) -> None:
        self.prop_positioner.update_prop_positions()

    def update_letter_item(self, letter: str) -> None:
        if letter:
            self.set_letter_renderer(letter)
        else:
            self.letter_item.setSharedRenderer(
                QSvgRenderer(f"{LETTER_SVG_DIR}/blank.svg")
            )
