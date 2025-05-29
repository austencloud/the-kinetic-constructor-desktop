"""
Browse Tab Layout Measurement and Testing System

This module provides data-driven testing for the Browse Tab layout with concrete measurements
and automated verification of the 2:1 ratio requirement.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, pyqtSignal


class BrowseTabLayoutMeasurements:
    """Measures and analyzes Browse Tab layout dimensions with concrete data."""

    def __init__(self, main_widget):
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)
        self.measurement_history = []

        # Setup detailed logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - LAYOUT_MEASURE - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def measure_layout_dimensions(self, event_name: str = "measurement") -> Dict:
        """Measure all layout dimensions and calculate ratios with concrete data."""
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📏 MEASURING LAYOUT DIMENSIONS: {event_name}")
            self.logger.info(f"{'='*60}")

            # Get main widget dimensions
            main_width = self.main_widget.width()
            main_height = self.main_widget.height()

            self.logger.info(f"🖥️  Main Widget: {main_width}px × {main_height}px")

            # Get stack dimensions
            left_stack = getattr(self.main_widget, "left_stack", None)
            right_stack = getattr(self.main_widget, "right_stack", None)

            left_width = left_stack.width() if left_stack else 0
            right_width = right_stack.width() if right_stack else 0

            self.logger.info(f"📦 Left Stack:  {left_width}px")
            self.logger.info(f"📦 Right Stack: {right_width}px")

            # Get Browse Tab components if available
            browse_tab = self._get_browse_tab()
            sequence_picker_width = 0
            sequence_viewer_width = 0

            if browse_tab:
                sequence_picker = getattr(browse_tab, "sequence_picker", None)
                sequence_viewer = getattr(browse_tab, "sequence_viewer", None)

                if sequence_picker:
                    sequence_picker_width = sequence_picker.width()
                    self.logger.info(f"🔍 Sequence Picker: {sequence_picker_width}px")

                if sequence_viewer:
                    sequence_viewer_width = sequence_viewer.width()
                    self.logger.info(f"👁️  Sequence Viewer: {sequence_viewer_width}px")

            # Calculate expected dimensions
            expected_left_width = main_width * 2 / 3
            expected_right_width = main_width * 1 / 3

            self.logger.info(f"\n📊 EXPECTED DIMENSIONS:")
            self.logger.info(
                f"Expected Left:  {expected_left_width:.0f}px (2/3 of {main_width}px)"
            )
            self.logger.info(
                f"Expected Right: {expected_right_width:.0f}px (1/3 of {main_width}px)"
            )

            # Calculate actual ratios
            actual_ratio = left_width / right_width if right_width > 0 else 0
            expected_ratio = 2.0

            # Calculate percentage differences
            left_diff_pct = (
                abs(left_width - expected_left_width) / expected_left_width * 100
                if expected_left_width > 0
                else 0
            )
            right_diff_pct = (
                abs(right_width - expected_right_width) / expected_right_width * 100
                if expected_right_width > 0
                else 0
            )
            ratio_diff_pct = (
                abs(actual_ratio - expected_ratio) / expected_ratio * 100
                if expected_ratio > 0
                else 0
            )

            self.logger.info(f"\n📈 ACTUAL vs EXPECTED:")
            self.logger.info(
                f"Left Panel:  {left_width}px vs {expected_left_width:.0f}px (diff: {left_diff_pct:.1f}%)"
            )
            self.logger.info(
                f"Right Panel: {right_width}px vs {expected_right_width:.0f}px (diff: {right_diff_pct:.1f}%)"
            )
            self.logger.info(
                f"Ratio:       {actual_ratio:.3f} vs {expected_ratio:.3f} (diff: {ratio_diff_pct:.1f}%)"
            )

            # Determine pass/fail (5% tolerance)
            tolerance = 5.0
            left_pass = left_diff_pct <= tolerance
            right_pass = right_diff_pct <= tolerance
            ratio_pass = ratio_diff_pct <= tolerance
            overall_pass = left_pass and right_pass and ratio_pass

            self.logger.info(f"\n✅ PASS/FAIL ANALYSIS (±{tolerance}% tolerance):")
            self.logger.info(
                f"Left Panel:  {'✅ PASS' if left_pass else '❌ FAIL'} ({left_diff_pct:.1f}%)"
            )
            self.logger.info(
                f"Right Panel: {'✅ PASS' if right_pass else '❌ FAIL'} ({right_diff_pct:.1f}%)"
            )
            self.logger.info(
                f"Ratio:       {'✅ PASS' if ratio_pass else '❌ FAIL'} ({ratio_diff_pct:.1f}%)"
            )
            self.logger.info(f"OVERALL:     {'🎉 PASS' if overall_pass else '🚨 FAIL'}")

            # Create measurement record
            measurement = {
                "timestamp": time.time(),
                "event": event_name,
                "main_width": main_width,
                "main_height": main_height,
                "left_stack_width": left_width,
                "right_stack_width": right_width,
                "sequence_picker_width": sequence_picker_width,
                "sequence_viewer_width": sequence_viewer_width,
                "expected_left_width": expected_left_width,
                "expected_right_width": expected_right_width,
                "actual_ratio": actual_ratio,
                "expected_ratio": expected_ratio,
                "left_diff_pct": left_diff_pct,
                "right_diff_pct": right_diff_pct,
                "ratio_diff_pct": ratio_diff_pct,
                "left_pass": left_pass,
                "right_pass": right_pass,
                "ratio_pass": ratio_pass,
                "overall_pass": overall_pass,
                "tolerance": tolerance,
            }

            self.measurement_history.append(measurement)
            self.logger.info(f"{'='*60}\n")

            return measurement

        except Exception as e:
            error_msg = f"❌ Measurement failed for {event_name}: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg, "event": event_name}

    def _get_browse_tab(self):
        """Get the Browse Tab widget."""
        try:
            return self.main_widget.tab_manager.get_tab_widget("browse")
        except:
            try:
                return getattr(self.main_widget, "browse_tab", None)
            except:
                return None

    def generate_measurement_report(self):
        """Generate a comprehensive report of all measurements."""
        if not self.measurement_history:
            self.logger.info("📊 No measurements recorded.")
            return

        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"📊 COMPREHENSIVE MEASUREMENT REPORT")
        self.logger.info(f"{'='*80}")

        total_measurements = len(self.measurement_history)
        passed_measurements = sum(
            1 for m in self.measurement_history if m.get("overall_pass", False)
        )

        self.logger.info(f"Total measurements: {total_measurements}")
        self.logger.info(f"Passed measurements: {passed_measurements}")
        self.logger.info(
            f"Failed measurements: {total_measurements - passed_measurements}"
        )
        self.logger.info(
            f"Success rate: {passed_measurements/total_measurements*100:.1f}%"
        )

        # Show failed measurements
        failed_measurements = [
            m for m in self.measurement_history if not m.get("overall_pass", True)
        ]
        if failed_measurements:
            self.logger.info(f"\n🚨 FAILED MEASUREMENTS:")
            for m in failed_measurements:
                self.logger.info(
                    f"  - {m['event']}: Ratio {m['actual_ratio']:.3f} (expected 2.0)"
                )

        # Show latest measurement
        if self.measurement_history:
            latest = self.measurement_history[-1]
            self.logger.info(f"\n📈 LATEST MEASUREMENT ({latest['event']}):")
            self.logger.info(
                f"  Left: {latest['left_stack_width']}px ({latest['left_diff_pct']:.1f}% diff)"
            )
            self.logger.info(
                f"  Right: {latest['right_stack_width']}px ({latest['right_diff_pct']:.1f}% diff)"
            )
            self.logger.info(
                f"  Ratio: {latest['actual_ratio']:.3f} ({latest['ratio_diff_pct']:.1f}% diff)"
            )
            self.logger.info(
                f"  Status: {'✅ PASS' if latest['overall_pass'] else '❌ FAIL'}"
            )

        self.logger.info(f"{'='*80}\n")


class BrowseTabLayoutTester(QObject):
    """Automated testing system for Browse Tab layout verification."""

    test_completed = pyqtSignal(bool, str, dict)

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.measurements = BrowseTabLayoutMeasurements(main_widget)
        self.logger = logging.getLogger(__name__)

        # Setup logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - LAYOUT_TEST - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def run_comprehensive_layout_test(self):
        """Run comprehensive layout test with measurements at each stage."""
        self.logger.info("🚀 Starting comprehensive Browse Tab layout test...")

        # Step 1: Initial measurement
        initial = self.measurements.measure_layout_dimensions("initial_state")

        # Step 2: Switch to Browse Tab and measure
        QTimer.singleShot(500, self._test_browse_tab_activation)

    def _test_browse_tab_activation(self):
        """Test Browse Tab activation and measure layout."""
        try:
            self.logger.info("🔄 Testing Browse Tab activation...")

            # Switch to Browse Tab
            tab_manager = getattr(self.main_widget, "tab_manager", None)
            if tab_manager:
                tab_manager.switch_to_tab("browse")
                QApplication.processEvents()
                time.sleep(0.5)

                # Measure after activation
                activation = self.measurements.measure_layout_dimensions(
                    "browse_tab_activated"
                )

                # Step 3: Test thumbnail selection
                QTimer.singleShot(1000, self._test_thumbnail_selection)
            else:
                self.logger.error("❌ Tab manager not available")
                self._complete_test(False, "Tab manager not available")

        except Exception as e:
            self.logger.error(f"❌ Browse Tab activation test failed: {e}")
            self._complete_test(False, f"Activation test failed: {e}")

    def _test_thumbnail_selection(self):
        """Test thumbnail selection and measure layout changes."""
        try:
            self.logger.info("🖱️ Testing thumbnail selection...")

            # Get Browse Tab
            browse_tab = self.measurements._get_browse_tab()
            if not browse_tab:
                self.logger.error("❌ Browse Tab not available")
                self._complete_test(False, "Browse Tab not available")
                return

            # Get thumbnail boxes
            scroll_widget = browse_tab.sequence_picker.scroll_widget
            thumbnail_boxes = getattr(scroll_widget, "thumbnail_boxes", {})

            if thumbnail_boxes:
                # Select the first available thumbnail
                box_names = list(thumbnail_boxes.keys())
                selected_box = thumbnail_boxes[box_names[0]]
                image_label = selected_box.image_label

                self.logger.info(f"Selecting thumbnail: {box_names[0]}")

                # Measure before selection
                before = self.measurements.measure_layout_dimensions(
                    "before_thumbnail_selection"
                )

                # Simulate selection
                browse_tab.selection_handler.on_thumbnail_clicked(image_label)

                # Measure after selection
                QTimer.singleShot(1000, lambda: self._measure_after_selection())
            else:
                self.logger.warning("⚠️ No thumbnail boxes available, completing test")
                self._complete_test(True, "No thumbnails to test")

        except Exception as e:
            self.logger.error(f"❌ Thumbnail selection test failed: {e}")
            self._complete_test(False, f"Selection test failed: {e}")

    def _measure_after_selection(self):
        """Measure layout after thumbnail selection."""
        after = self.measurements.measure_layout_dimensions("after_thumbnail_selection")
        self._complete_test(after.get("overall_pass", False), "Test completed")

    def _complete_test(self, success: bool, message: str):
        """Complete the test and generate final report."""
        self.measurements.generate_measurement_report()

        # Get the latest measurement for detailed results
        latest_measurement = (
            self.measurements.measurement_history[-1]
            if self.measurements.measurement_history
            else {}
        )

        if success:
            self.logger.info(f"✅ LAYOUT TEST PASSED: {message}")
        else:
            self.logger.error(f"❌ LAYOUT TEST FAILED: {message}")

        self.test_completed.emit(success, message, latest_measurement)


def run_browse_tab_layout_test(main_widget):
    """Run the comprehensive Browse Tab layout test."""
    tester = BrowseTabLayoutTester(main_widget)
    tester.run_comprehensive_layout_test()
    return tester


def quick_measure_layout(main_widget, event_name="quick_measure"):
    """Quick function to measure layout at any time."""
    measurements = BrowseTabLayoutMeasurements(main_widget)
    return measurements.measure_layout_dimensions(event_name)


# Console command for easy testing
def test_layout_now():
    """Console command to test layout immediately."""
    try:
        app = QApplication.instance()
        if not app:
            print("❌ No QApplication instance found.")
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

        print("📏 Running immediate layout measurement...")
        result = quick_measure_layout(main_window.main_widget, "immediate_test")

        if result.get("overall_pass"):
            print("✅ Layout test PASSED!")
        else:
            print("❌ Layout test FAILED!")

        return result

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_layout_now()
