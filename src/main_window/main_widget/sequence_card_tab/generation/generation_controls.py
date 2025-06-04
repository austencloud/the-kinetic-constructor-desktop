# src/main_window/main_widget/sequence_card_tab/generation/generation_controls.py
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from src.interfaces.settings_manager_interface import ISettingsManager

from .managers.parameter_controls_manager import ParameterControlsManager
from .managers.settings_persistence_manager import SettingsPersistenceManager
from .managers.progress_display_manager import ProgressDisplayManager
from .managers.generation_action_manager import GenerationActionManager
from .managers.style_manager import StyleManager


class GenerationControlsPanel(QWidget):
    generate_requested = pyqtSignal(object, int)
    clear_requested = pyqtSignal()

    def __init__(self, settings_manager: ISettingsManager | None = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        self.settings_manager = SettingsPersistenceManager(settings_manager)
        self.setup_ui()
        self.setup_connections()
        self.load_saved_settings()
        StyleManager.apply_generation_controls_styling(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(12)

        self.create_header(layout)
        self.create_parameter_section(layout)
        self.create_action_section(layout)
        # self.create_progress_section(layout) # Progress section is now part of the header

    def create_header(self, layout):
        self.header_label = QLabel("Generate Sequences")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setWeight(QFont.Weight.Medium)
        self.header_label.setFont(header_font)
        self.header_label.setObjectName("generationHeaderLabel")

        layout.addWidget(self.header_label)

    def create_parameter_section(self, layout):
        self.parameters_frame = QFrame()
        self.parameters_frame.setObjectName("parametersFrame")

        frame_layout = QVBoxLayout(self.parameters_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        self.parameter_controls = ParameterControlsManager()
        frame_layout.addWidget(self.parameter_controls)

        layout.addWidget(self.parameters_frame)

    def create_action_section(self, layout):
        self.controls_frame = QFrame()
        self.controls_frame.setObjectName("controlsFrame")

        frame_layout = QVBoxLayout(self.controls_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        self.action_controls = GenerationActionManager()
        self.action_controls.set_parameter_provider(self.parameter_controls)
        frame_layout.addWidget(self.action_controls)

        layout.addWidget(self.controls_frame)

    def create_progress_section(self, layout):
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("progressFrame")

        frame_layout = QVBoxLayout(self.progress_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_display = ProgressDisplayManager()
        frame_layout.addWidget(self.progress_display)

        # layout.addWidget(self.progress_frame) # Progress section is now part of the header

    def setup_connections(self):
        self.action_controls.generate_requested.connect(self.generate_requested.emit)
        self.action_controls.clear_requested.connect(self.clear_requested.emit)

        self.parameter_controls.parameter_changed.connect(self.save_current_settings)
        self.action_controls.batch_size_combo.currentTextChanged.connect(
            self.save_current_settings
        )

    def load_saved_settings(self):
        try:
            settings = self.settings_manager.load_saved_settings()
            self.parameter_controls.load_values(settings)
            self.action_controls.load_batch_size(settings.get("batch_size", "5"))
            self.logger.info(
                f"Loaded generation controls settings: length={settings.get('length')}, level={settings.get('level')}"
            )
        except Exception as e:
            self.logger.error(f"Error loading saved settings: {e}")

    def save_current_settings(self):
        try:
            settings = self.parameter_controls.get_current_values()
            settings["batch_size"] = self.action_controls.get_current_batch_size()
            self.settings_manager.save_settings(settings)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def get_generation_parameters(self):
        return self.parameter_controls.get_generation_parameters()

    def set_generation_enabled(self, enabled: bool):
        self.action_controls.set_generation_enabled(enabled)

    def show_progress(self, current: int, total: int):
        # self.progress_display.show_progress(current, total) # Progress display is now handled by the header
        if hasattr(self.parent(), "header") and hasattr(
            self.parent().header, "progress_bar"
        ):
            self.parent().header.progress_bar.setMaximum(total)
            self.parent().header.progress_bar.setValue(current)
            self.parent().header.progress_bar.setVisible(True)
            if hasattr(self.parent().header, "progress_container"):
                self.parent().header.progress_container.setVisible(True)

    def hide_progress(self):
        # self.progress_display.hide_progress() # Progress display is now handled by the header
        if hasattr(self.parent(), "header") and hasattr(
            self.parent().header, "progress_bar"
        ):
            self.parent().header.progress_bar.setVisible(False)
            if hasattr(self.parent().header, "progress_container"):
                self.parent().header.progress_container.setVisible(False)
