from PyQt6.QtWidgets import QWidget
from typing import TYPE_CHECKING

from objects.graphical_object import GraphicalObject
from utilities.TypeChecking.TypeChecking import RotationAngle

if TYPE_CHECKING:
    from main import MainWindow
    from widgets.graph_editor.object_panel.objectbox import ObjectBox
    from widgets.graph_editor.pictograph.pictograph import Pictograph
    from widgets.graph_editor.object_panel.arrowbox.arrowbox_drag import ArrowBoxDrag
    from widgets.graph_editor.object_panel.propbox.propbox_drag import PropBoxDrag

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QTransform
from PyQt6.QtSvg import QSvgRenderer


class ObjectBoxDrag(QWidget):
    def __init__(
        self,
        main_window: "MainWindow",
        pictograph: "Pictograph",
        objectbox: "ObjectBox",
    ) -> None:
        super().__init__(main_window)
        self.setParent(main_window)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.reset_drag_state()
        self.setup_dependencies(main_window, pictograph, objectbox)

    def setup_dependencies(
        self,
        main_window: "MainWindow",
        pictograph: "Pictograph",
        objectbox: "ObjectBox",
    ) -> None:
        self.preview = QLabel(self)
        self.transform = QTransform()
        self.objectbox = objectbox
        self.pictograph = pictograph
        self.main_window = main_window
        self.has_entered_pictograph_once = False
        self.current_rotation_angle = 0
        self.previous_location = None
        self.svg_file = None
        self.static_arrow = None

    def create_pixmap(
        self, target_object: GraphicalObject, drag_angle: RotationAngle
    ) -> None:
        new_svg_data = target_object.set_svg_color(self.color)
        renderer = QSvgRenderer()
        renderer.load(new_svg_data)

        scaled_size = renderer.defaultSize() * self.pictograph.view.view_scale
        original_pixmap = QPixmap(scaled_size)
        self.setFixedSize(scaled_size)
        self.preview.setFixedSize(scaled_size)
        original_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(original_pixmap)
        renderer.render(painter)
        painter.end()

        rotate_transform = QTransform().rotate(drag_angle)
        rotated_pixmap = original_pixmap.transformed(rotate_transform)
        self.setFixedSize(rotated_pixmap.size())
        self.preview.setFixedSize(rotated_pixmap.size())
        self.preview.setPixmap(rotated_pixmap)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return rotated_pixmap

    def reset_drag_state(self) -> None:
        self.dragging = False
        self.drag_preview = None
        self.current_rotation_angle = 0

    def match_target_object(self, target_object: GraphicalObject) -> None:
        self.target_object = target_object
        self.color = target_object.color
        self.svg_file = target_object.svg_file
        self.static_arrow = target_object.static_arrow
