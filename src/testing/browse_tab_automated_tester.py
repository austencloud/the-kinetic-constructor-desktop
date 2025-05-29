import logging
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from .browse_tab_layout_monitor import BrowseTabLayoutMonitor
from .browse_tab_mock_interactor import BrowseTabMockInteractor


class BrowseTabAutomatedTester(QObject):
    test_completed = pyqtSignal(bool, str)

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.monitor = BrowseTabLayoutMonitor(main_widget)
        self.interactor = BrowseTabMockInteractor(main_widget, self.monitor)
        self.logger = logging.getLogger(__name__)

        self.test_thumbnails = [0, 1, 2]
        self.current_test_index = 0
        self.violations_detected = []

        self.monitor.layout_violation_detected.connect(self._on_violation_detected)
        self.interactor.interaction_completed.connect(self._on_interaction_completed)

    def start_automated_test(self):
        self.logger.info("🚀 Starting automated Browse Tab layout test...")

        self.monitor.start_monitoring()
        self.monitor.measure_layout("test_start")

        if self.interactor.switch_to_browse_tab():
            QTimer.singleShot(1000, self._test_next_thumbnail)
        else:
            self._complete_test(False, "Failed to switch to Browse Tab")

    def _test_next_thumbnail(self):
        if self.current_test_index >= len(self.test_thumbnails):
            self._complete_test(
                len(self.violations_detected) == 0, "All tests completed"
            )
            return

        thumbnail_index = self.test_thumbnails[self.current_test_index]
        self.logger.info(
            f"Testing thumbnail {thumbnail_index + 1}/{len(self.test_thumbnails)}"
        )

        if self.interactor.simulate_thumbnail_click(thumbnail_index):
            self.current_test_index += 1
            QTimer.singleShot(2000, self._test_next_thumbnail)
        else:
            self._complete_test(False, f"Failed to test thumbnail {thumbnail_index}")

    def _on_violation_detected(self, event_name: str, measurement: dict):
        self.violations_detected.append((event_name, measurement))
        self.logger.error(f"🚨 Violation detected during: {event_name}")

    def _on_interaction_completed(self, interaction_name: str):
        self.logger.info(f"✅ Interaction completed: {interaction_name}")

    def _complete_test(self, success: bool, message: str):
        self.monitor.stop_monitoring()

        if success:
            self.logger.info(f"✅ TEST PASSED: {message}")
        else:
            self.logger.error(f"❌ TEST FAILED: {message}")

        self.test_completed.emit(success, message)


def run_automated_browse_tab_test(main_widget):
    tester = BrowseTabAutomatedTester(main_widget)
    tester.start_automated_test()
    return tester
