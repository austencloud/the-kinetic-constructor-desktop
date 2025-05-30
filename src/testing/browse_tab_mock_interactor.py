import logging
import time
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from .browse_tab_layout_monitor import BrowseTabLayoutMonitor


class BrowseTabMockInteractor(QObject):
    interaction_completed = pyqtSignal(str)

    def __init__(self, main_widget, monitor: BrowseTabLayoutMonitor):
        super().__init__()
        self.main_widget = main_widget
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)

    def switch_to_browse_tab(self) -> bool:
        try:
            self.logger.info("🔄 Switching to Browse Tab...")

            tab_manager = getattr(self.main_widget, "tab_manager", None)
            if tab_manager:
                tab_manager.switch_to_tab("browse")
                self.monitor.measure_layout("browse_tab_switched")
                QApplication.processEvents()
                time.sleep(0.5)
                return True
            else:
                self.logger.error("Tab manager not available")
                return False

        except Exception as e:
            self.logger.error(f"Failed to switch to Browse Tab: {e}")
            return False

    def simulate_thumbnail_click(self, thumbnail_index: int = 0) -> bool:
        try:
            self.logger.info(
                f"🖱️ Simulating thumbnail click (index: {thumbnail_index})..."
            )

            self.monitor.measure_layout("before_thumbnail_click")

            browse_tab = self.monitor._get_browse_tab()
            if not browse_tab:
                self.logger.error("Browse Tab not available")
                return False

            scroll_widget = browse_tab.sequence_picker.scroll_widget
            thumbnail_boxes = getattr(scroll_widget, "thumbnail_boxes", {})

            if not thumbnail_boxes:
                self.logger.error("No thumbnail boxes available")
                return False

            box_names = list(thumbnail_boxes.keys())
            if thumbnail_index >= len(box_names):
                thumbnail_index = 0

            if not box_names:
                self.logger.error("No thumbnail boxes found")
                return False

            selected_box = thumbnail_boxes[box_names[thumbnail_index]]
            image_label = selected_box.image_label

            self.logger.info(f"Clicking thumbnail: {box_names[thumbnail_index]}")

            self.monitor.measure_layout("during_fade_start")

            browse_tab.selection_handler.on_thumbnail_clicked(image_label)

            QApplication.processEvents()
            time.sleep(0.5)

            self.monitor.measure_layout("after_thumbnail_click")

            self.interaction_completed.emit(f"thumbnail_click_{thumbnail_index}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to simulate thumbnail click: {e}")
            return False
