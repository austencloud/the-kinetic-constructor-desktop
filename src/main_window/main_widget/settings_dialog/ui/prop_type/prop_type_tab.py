from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QApplication,
)
from PyQt6.QtCore import Qt
from enums.prop_type import PropType
from main_window.main_widget.settings_dialog.ui.prop_type.prop_button import PropButton
from utils.path_helpers import get_image_path
from styles.glassmorphism_styler import GlassmorphismStyler


if TYPE_CHECKING:
    from ...modern_settings_dialog import ModernSettingsDialog


class PropTypeTab(QWidget):
    buttons: dict[str, PropButton] = {}

    def __init__(self, settings_dialog: "ModernSettingsDialog"):
        super().__init__()
        self.settings_dialog = settings_dialog
        self.main_widget = settings_dialog.main_widget
        self._setup_ui()

    def _setup_ui(self):
        """Setup modern glassmorphism UI for prop type selection."""
        # Main layout with minimal spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(8)

        # Simple title only
        self.header = QLabel("Select Prop Type")
        self.header.setFont(GlassmorphismStyler.get_font("heading_small"))
        self.header.setStyleSheet(
            f"color: {GlassmorphismStyler.get_color('text_primary')};"
        )
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.header)

        # Props grid in a modern container
        props_container = QWidget()
        props_container.setObjectName("props_container")
        props_container.setStyleSheet(
            f"""
            QWidget#props_container {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {GlassmorphismStyler.get_color('surface', 0.6)},
                    stop:1 {GlassmorphismStyler.get_color('surface_light', 0.4)});
                border: 1px solid {GlassmorphismStyler.get_color('border', 0.4)};
                border-radius: {GlassmorphismStyler.RADIUS['md']}px;
            }}
        """
        )

        container_layout = QVBoxLayout(props_container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)

        # Create grid layout for prop buttons
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)  # Tighter spacing
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Define props with better organization
        props = {
            "Staff": "props/staff.svg",
            "Simplestaff": "props/simple_staff.svg",
            "Club": "props/club.svg",
            "Fan": "props/fan.svg",
            "Triad": "props/triad.svg",
            "Minihoop": "props/minihoop.svg",
            "Buugeng": "props/buugeng.svg",
            "Triquetra": "props/triquetra.svg",
            "Sword": "props/sword.svg",
            "Chicken": "props/chicken.png",
            "Hand": "props/hand.svg",
            "Guitar": "props/guitar.svg",
            "Ukulele": "props/ukulele.svg",
        }

        # Create prop buttons in a 4-column grid for better layout
        row, col = 0, 0
        for prop, icon_path in props.items():
            # Create prop button
            button = PropButton(
                prop,
                get_image_path(icon_path),
                self,
                self._set_current_prop_type,
            )
            self.buttons[prop] = button

            # Create label
            label = QLabel(prop)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(GlassmorphismStyler.get_font("body_small"))
            label.setStyleSheet(
                f"color: {GlassmorphismStyler.get_color('text_secondary')};"
            )

            # Create cell container
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(4, 4, 4, 4)
            cell_layout.setSpacing(3)
            cell_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
            cell_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

            grid_layout.addWidget(cell_widget, row, col)

            col += 1
            if col >= 4:  # 4 columns for better layout
                col = 0
                row += 1

        container_layout.addLayout(grid_layout)
        main_layout.addWidget(props_container)

    def _set_current_prop_type(self, prop_type: str):
        try:
            settings_manager = self.main_widget.app_context.settings_manager
        except AttributeError:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                "settings_manager not available in PropTypeTab._set_current_prop_type"
            )
            return

        self._update_active_button(prop_type)
        QApplication.processEvents()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        pictographs = self.main_widget.pictograph_collector.collect_all_pictographs()
        settings_manager.global_settings.set_prop_type(prop_type, pictographs)
        QApplication.restoreOverrideCursor()

    def _update_active_button(self, active_prop: PropType):
        if not active_prop:
            return

        active_prop_name = (
            active_prop.name if isinstance(active_prop, PropType) else str(active_prop)
        )

        for prop, button in self.buttons.items():
            button.set_active(prop == active_prop_name)

    def update_active_prop_type_from_settings(self):
        try:
            settings_manager = self.main_widget.app_context.settings_manager
            current_prop = settings_manager.global_settings.get_prop_type()
            self._update_active_button(current_prop)
        except AttributeError:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                "settings_manager not available in PropTypeTab.update_active_prop_type_from_settings"
            )

    def resizeEvent(self, event):
        """Handle resize events - modern layout doesn't need dynamic sizing."""
        super().resizeEvent(event)

    def update_size(self):
        """Update size - no longer needed with fixed modern layout."""
        pass  # Keep for compatibility
