from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QApplication
from typing import Optional
import logging


from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
    TempBeatFrame,
)
from .generation_manager import GeneratedSequenceData


class ImageGenerationWorker(QThread):
    image_generated = pyqtSignal(str, QPixmap)
    image_failed = pyqtSignal(str, str)
    diagnostic_info = pyqtSignal(str, dict)

    def __init__(self, sequence_data: GeneratedSequenceData, main_widget):
        super().__init__()
        self.sequence_data = sequence_data
        self.main_widget = main_widget

    def run(self):
        diagnostics = {}
        try:
            logging.info(
                f"=== Starting image generation for sequence {self.sequence_data.id} ==="
            )

            diagnostics["sequence_length"] = len(self.sequence_data.sequence_data)
            diagnostics["sequence_word"] = self.sequence_data.word
            diagnostics["has_sequence_data"] = bool(self.sequence_data.sequence_data)

            if not self.sequence_data.sequence_data:
                self.image_failed.emit(
                    self.sequence_data.id, "No sequence data available"
                )
                return

            if len(self.sequence_data.sequence_data) < 3:
                self.image_failed.emit(
                    self.sequence_data.id,
                    f"Insufficient sequence data: {len(self.sequence_data.sequence_data)} beats",
                )
                return

            actual_main_widget = self._get_actual_main_widget()
            diagnostics["main_widget_type"] = (
                type(actual_main_widget).__name__ if actual_main_widget else None
            )
            diagnostics["main_widget_available"] = actual_main_widget is not None

            if not actual_main_widget:
                self.image_failed.emit(
                    self.sequence_data.id, "Main widget not available"
                )
                return

            temp_beat_frame = self._create_temp_beat_frame_with_diagnostics(
                actual_main_widget, diagnostics
            )
            if not temp_beat_frame:
                error_msg = f"Failed to create temp beat frame: {diagnostics.get('temp_frame_error', 'Unknown error')}"
                self.image_failed.emit(self.sequence_data.id, error_msg)
                return

            diagnostics["has_export_manager"] = hasattr(
                temp_beat_frame, "export_manager"
            )
            if not hasattr(temp_beat_frame, "export_manager"):
                self.image_failed.emit(
                    self.sequence_data.id, "Temp beat frame missing export_manager"
                )
                return

            export_manager = temp_beat_frame.export_manager
            diagnostics["export_manager_type"] = (
                type(export_manager).__name__ if export_manager else None
            )
            diagnostics["has_image_creator"] = (
                hasattr(export_manager, "image_creator") if export_manager else False
            )

            if not export_manager:
                self.image_failed.emit(
                    self.sequence_data.id, "Export manager not available"
                )
                return

            if not hasattr(export_manager, "image_creator"):
                self.image_failed.emit(
                    self.sequence_data.id, "Export manager missing image_creator"
                )
                return

            try:
                logging.info(
                    f"Loading sequence into temp beat frame: {len(self.sequence_data.sequence_data)} beats"
                )
                temp_beat_frame.load_sequence(self.sequence_data.sequence_data)
                diagnostics["sequence_loaded"] = True
                logging.info("Sequence loaded successfully")
            except Exception as load_error:
                diagnostics["sequence_loaded"] = False
                diagnostics["load_error"] = str(load_error)
                logging.error(f"Failed to load sequence: {load_error}")
                self.image_failed.emit(
                    self.sequence_data.id, f"Failed to load sequence: {load_error}"
                )
                return

            pixmap = self._generate_image_with_fallbacks(export_manager, diagnostics)

            if pixmap and not pixmap.isNull():
                diagnostics["image_generation_success"] = True
                diagnostics["image_size"] = f"{pixmap.width()}x{pixmap.height()}"
                logging.info(
                    f"Successfully generated image: {diagnostics['image_size']}"
                )
                self.image_generated.emit(self.sequence_data.id, pixmap)
            else:
                diagnostics["image_generation_success"] = False
                error_msg = f"Image generation failed: {diagnostics.get('image_error', 'Unknown error')}"
                self.image_failed.emit(self.sequence_data.id, error_msg)

        except Exception as e:
            diagnostics["fatal_error"] = str(e)
            logging.error(f"Fatal error in image generation: {e}")
            import traceback

            traceback.print_exc()
            self.image_failed.emit(self.sequence_data.id, f"Fatal error: {str(e)}")
        finally:
            self.diagnostic_info.emit(self.sequence_data.id, diagnostics)

    def _create_temp_beat_frame_with_diagnostics(self, actual_main_widget, diagnostics):
        try:

            class MockBrowseTab:
                def __init__(self, main_widget):
                    self.main_widget = main_widget

            mock_browse_tab = MockBrowseTab(actual_main_widget)
            diagnostics["mock_browse_tab_created"] = True

            temp_beat_frame = TempBeatFrame(mock_browse_tab)
            diagnostics["temp_beat_frame_created"] = True
            diagnostics["temp_beat_frame_type"] = type(temp_beat_frame).__name__

            required_attrs = [
                "json_manager",
                "settings_manager",
                "export_manager",
                "beat_views",
            ]
            for attr in required_attrs:
                has_attr = hasattr(temp_beat_frame, attr)
                diagnostics[f"has_{attr}"] = has_attr
                if not has_attr:
                    logging.warning(f"Temp beat frame missing {attr}")

            return temp_beat_frame

        except Exception as e:
            diagnostics["temp_frame_error"] = str(e)
            logging.error(f"Error creating temp beat frame: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _generate_image_with_fallbacks(self, export_manager, diagnostics):
        try:
            logging.info("Attempting standard image generation")
            options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": True,
                "add_user_info": True,
                "add_word": True,
                "add_difficulty_level": True,
                "include_start_position": True,  # Enable start position for approval dialog
                "combined_grids": False,
                "additional_height_top": 0,
                "additional_height_bottom": 0,
            }

            qimage = export_manager.image_creator.create_sequence_image(
                self.sequence_data.sequence_data,
                options,
                dictionary=True,
                fullscreen_preview=False,
            )

            if qimage and not qimage.isNull():
                pixmap = QPixmap.fromImage(qimage)
                if not pixmap.isNull():
                    diagnostics["generation_strategy"] = "standard"
                    return pixmap

        except Exception as e:
            diagnostics["standard_generation_error"] = str(e)
            logging.warning(f"Standard generation failed: {e}")

        try:
            logging.info("Attempting minimal options image generation")
            minimal_options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": True,
                "add_user_info": True,
                "add_word": True,
                "add_difficulty_level": True,
                "include_start_position": True,  # Enable start position for approval dialog
                "combined_grids": False,
                "additional_height_top": 0,
                "additional_height_bottom": 0,
            }

            qimage = export_manager.image_creator.create_sequence_image(
                self.sequence_data.sequence_data,
                minimal_options,
                dictionary=True,
                fullscreen_preview=False,
            )

            if qimage and not qimage.isNull():
                pixmap = QPixmap.fromImage(qimage)
                if not pixmap.isNull():
                    diagnostics["generation_strategy"] = "minimal"
                    return pixmap

        except Exception as e:
            diagnostics["minimal_generation_error"] = str(e)
            logging.warning(f"Minimal generation failed: {e}")

        try:
            logging.info("Attempting alternative image generation method")

            if hasattr(export_manager.image_creator, "create_basic_sequence_image"):
                qimage = export_manager.image_creator.create_basic_sequence_image(
                    self.sequence_data.sequence_data
                )
                if qimage and not qimage.isNull():
                    pixmap = QPixmap.fromImage(qimage)
                    if not pixmap.isNull():
                        diagnostics["generation_strategy"] = "alternative"
                        return pixmap

        except Exception as e:
            diagnostics["alternative_generation_error"] = str(e)
            logging.warning(f"Alternative generation failed: {e}")

        try:
            logging.info("Creating placeholder image")
            from PyQt6.QtGui import QPainter, QPen, QFont
            from PyQt6.QtCore import Qt

            placeholder_pixmap = QPixmap(300, 200)
            placeholder_pixmap.fill(Qt.GlobalColor.lightGray)

            painter = QPainter(placeholder_pixmap)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(
                placeholder_pixmap.rect(),
                Qt.AlignmentFlag.AlignCenter,
                f"Sequence: {self.sequence_data.word}\n({len(self.sequence_data.sequence_data)} beats)",
            )
            painter.end()

            diagnostics["generation_strategy"] = "placeholder"
            return placeholder_pixmap

        except Exception as e:
            diagnostics["placeholder_generation_error"] = str(e)
            logging.error(f"Even placeholder generation failed: {e}")

        diagnostics["all_strategies_failed"] = True
        return None

    def _get_actual_main_widget(self):
        try:
            if hasattr(self.main_widget, "main_widget"):
                logging.info("Found main_widget through coordinator")
                return self.main_widget.main_widget

            main_widget_indicators = [
                "widget_manager",
                "tab_manager",
                "sequence_workbench",
            ]
            if any(hasattr(self.main_widget, attr) for attr in main_widget_indicators):
                logging.info("Using main_widget directly")
                return self.main_widget

            current = self.main_widget
            search_depth = 0
            while current and hasattr(current, "parent") and search_depth < 10:
                parent = current.parent()
                if parent and any(
                    hasattr(parent, attr) for attr in main_widget_indicators
                ):
                    logging.info(
                        f"Found main_widget through parent hierarchy at depth {search_depth}"
                    )
                    return parent
                current = parent
                search_depth += 1

            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if any(hasattr(widget, attr) for attr in main_widget_indicators):
                        logging.info(
                            "Found main_widget through application widget search"
                        )
                        return widget

            logging.warning("Could not find actual main widget using any strategy")
            return self.main_widget

        except Exception as e:
            logging.error(f"Error finding actual main widget: {e}")
            return self.main_widget
