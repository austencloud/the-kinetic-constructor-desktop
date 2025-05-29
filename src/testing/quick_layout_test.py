"""
Quick Layout Test for Browse Tab

This module provides a simple way to test the Browse Tab layout
directly from the running application instance.
"""

import logging
import time
from typing import Dict, List
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class QuickLayoutTester(QObject):
    """Simple layout tester that can be run on the current application."""

    test_completed = pyqtSignal(bool, str)

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)
        self.measurements = []

        # Setup console logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - LAYOUT_TEST - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def run_quick_test(self):
        """Run a quick layout test on the current application."""
        self.logger.info("🧪 Starting quick Browse Tab layout test...")

        # Step 1: Measure initial state
        self._measure_and_log("initial_state")

        # Step 2: Switch to Browse Tab
        QTimer.singleShot(500, self._switch_to_browse_tab)

    def _switch_to_browse_tab(self):
        """Switch to Browse Tab and measure."""
        try:
            self.logger.info("🔄 Switching to Browse Tab...")

            # Try to switch to Browse Tab
            tab_manager = getattr(self.main_widget, "tab_manager", None)
            if tab_manager:
                tab_manager.switch_to_tab("browse")
                QApplication.processEvents()
                time.sleep(0.5)

                self._measure_and_log("browse_tab_active")

                # Step 3: Test thumbnail selection
                QTimer.singleShot(1000, self._test_thumbnail_selection)
            else:
                self.logger.error("❌ Tab manager not available")
                self.test_completed.emit(False, "Tab manager not available")

        except Exception as e:
            self.logger.error(f"❌ Failed to switch to Browse Tab: {e}")
            self.test_completed.emit(False, f"Switch failed: {e}")

    def _test_thumbnail_selection(self):
        """Test thumbnail selection and measure layout changes."""
        try:
            self.logger.info("🖱️ Testing thumbnail selection...")

            # Get Browse Tab
            browse_tab = self._get_browse_tab()
            if not browse_tab:
                self.logger.error("❌ Browse Tab not available")
                self.test_completed.emit(False, "Browse Tab not available")
                return

            # Get thumbnail boxes
            scroll_widget = browse_tab.sequence_picker.scroll_widget
            thumbnail_boxes = getattr(scroll_widget, "thumbnail_boxes", {})

            if not thumbnail_boxes:
                self.logger.error("❌ No thumbnail boxes available")
                self.test_completed.emit(False, "No thumbnail boxes available")
                return

            # Select the first available thumbnail
            box_names = list(thumbnail_boxes.keys())
            if box_names:
                selected_box = thumbnail_boxes[box_names[0]]
                image_label = selected_box.image_label

                self.logger.info(f"Selecting thumbnail: {box_names[0]}")

                # Measure before selection
                self._measure_and_log("before_selection")

                # Simulate selection
                browse_tab.selection_handler.on_thumbnail_clicked(image_label)

                # Measure during fade
                QTimer.singleShot(100, lambda: self._measure_and_log("during_fade"))

                # Measure after fade completes
                QTimer.singleShot(
                    1000, lambda: self._measure_and_log("after_selection")
                )

                # Complete test
                QTimer.singleShot(1500, self._complete_test)
            else:
                self.logger.error("❌ No thumbnail boxes found")
                self.test_completed.emit(False, "No thumbnail boxes found")

        except Exception as e:
            self.logger.error(f"❌ Thumbnail selection test failed: {e}")
            self.test_completed.emit(False, f"Selection test failed: {e}")

    def _measure_and_log(self, event_name: str):
        """Measure layout and log results."""
        try:
            # Get Browse Tab
            browse_tab = self._get_browse_tab()
            if not browse_tab:
                self.logger.warning(f"⚠️ Browse Tab not available for {event_name}")
                return

            # Get dimensions
            main_width = self.main_widget.width()

            # Get stack dimensions
            left_stack = getattr(self.main_widget, "left_stack", None)
            right_stack = getattr(self.main_widget, "right_stack", None)

            left_width = left_stack.width() if left_stack else 0
            right_width = right_stack.width() if right_stack else 0

            # Get sequence viewer dimensions
            sequence_viewer = browse_tab.sequence_viewer
            viewer_width = sequence_viewer.width()

            # Calculate expected dimensions
            expected_right_width = main_width / 3
            expected_left_width = main_width * 2 / 3

            # Calculate ratios
            actual_ratio = left_width / right_width if right_width > 0 else 0
            expected_ratio = 2.0

            # Detect violations
            width_violation = abs(viewer_width - expected_right_width) > 50
            ratio_violation = abs(actual_ratio - expected_ratio) > 0.3

            # Create measurement
            measurement = {
                "event": event_name,
                "main_width": main_width,
                "left_width": left_width,
                "right_width": right_width,
                "viewer_width": viewer_width,
                "expected_right": expected_right_width,
                "actual_ratio": actual_ratio,
                "expected_ratio": expected_ratio,
                "width_violation": width_violation,
                "ratio_violation": ratio_violation,
            }

            self.measurements.append(measurement)

            # Log results
            if width_violation or ratio_violation:
                self.logger.warning(
                    f"🚨 VIOLATION at {event_name}: "
                    f"Viewer={viewer_width}px (expected={expected_right_width:.0f}px), "
                    f"Ratio={actual_ratio:.2f} (expected=2.0)"
                )
            else:
                self.logger.info(
                    f"✅ OK at {event_name}: "
                    f"Viewer={viewer_width}px, Ratio={actual_ratio:.2f}"
                )

        except Exception as e:
            self.logger.error(f"❌ Measurement failed for {event_name}: {e}")

    def _complete_test(self):
        """Complete the test and generate report."""
        self.logger.info("📊 Generating test report...")

        violations = [
            m
            for m in self.measurements
            if m.get("width_violation") or m.get("ratio_violation")
        ]

        self.logger.info(f"Total measurements: {len(self.measurements)}")
        self.logger.info(f"Violations detected: {len(violations)}")

        if violations:
            self.logger.warning("🚨 VIOLATIONS FOUND:")
            for v in violations:
                self.logger.warning(
                    f"  - {v['event']}: Viewer {v['viewer_width']}px "
                    f"(expected {v['expected_right']:.0f}px), "
                    f"Ratio {v['actual_ratio']:.2f}"
                )

            # Identify the specific issue
            if any(v["event"] == "after_selection" for v in violations):
                self.logger.error(
                    "🎯 ISSUE IDENTIFIED: Sequence viewer expands after thumbnail selection"
                )
            elif any(v["event"] == "during_fade" for v in violations):
                self.logger.error(
                    "🎯 ISSUE IDENTIFIED: Layout breaks during fade operation"
                )
            elif any(v["event"] == "browse_tab_active" for v in violations):
                self.logger.error(
                    "🎯 ISSUE IDENTIFIED: Initial Browse Tab layout is incorrect"
                )

            self.test_completed.emit(False, f"{len(violations)} violations detected")
        else:
            self.logger.info("🎉 ALL TESTS PASSED! No layout violations detected.")
            self.test_completed.emit(True, "All tests passed")

    def _get_browse_tab(self):
        """Get the Browse Tab widget."""
        try:
            return self.main_widget.tab_manager.get_tab_widget("browse")
        except:
            try:
                return getattr(self.main_widget, "browse_tab", None)
            except:
                return None


def run_quick_layout_test(main_widget):
    """Run a quick layout test on the provided main widget."""
    tester = QuickLayoutTester(main_widget)
    tester.run_quick_test()
    return tester


# Console command for easy testing
def test_browse_tab_layout():
    """Console command to test Browse Tab layout."""
    try:
        # Get the current QApplication instance
        app = QApplication.instance()
        if not app:
            print(
                "❌ No QApplication instance found. Run this from within the application."
            )
            return

        # Find the main window
        main_window = None
        for widget in app.topLevelWidgets():
            if hasattr(widget, "main_widget"):
                main_window = widget
                break

        if not main_window:
            print("❌ Main window not found.")
            return

        print("🧪 Starting Browse Tab layout test...")
        tester = run_quick_layout_test(main_window.main_widget)

        def on_test_completed(success, message):
            if success:
                print(f"✅ Test completed successfully: {message}")
            else:
                print(f"❌ Test failed: {message}")

        tester.test_completed.connect(on_test_completed)

    except Exception as e:
        print(f"❌ Test failed to start: {e}")


if __name__ == "__main__":
    test_browse_tab_layout()
