"""
Browse Tab Aspect Ratio Test

This script tests the browse tab layout to ensure it maintains the correct 2:1 aspect ratio
(left panel 2/3 width, right panel 1/3 width) after the layout fixes.
"""

import logging
import time
from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer


class BrowseTabAspectRatioTester:
    """Tests the browse tab's 2:1 aspect ratio layout."""

    def __init__(self, main_widget):
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for the test."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def run_test(self) -> bool:
        """Run the aspect ratio test."""
        self.logger.info("🧪 Starting Browse Tab Aspect Ratio Test...")

        # Switch to browse tab
        if not self._switch_to_browse_tab():
            self.logger.error("❌ Failed to switch to browse tab")
            return False

        # Allow UI to settle
        QApplication.processEvents()
        time.sleep(0.5)

        # Measure initial layout
        initial_measurement = self._measure_layout("initial")
        if not self._validate_aspect_ratio(initial_measurement):
            self.logger.error("❌ Initial layout does not meet 2:1 aspect ratio")
            return False

        # Test after window resize simulation
        self._simulate_window_resize()
        QApplication.processEvents()
        time.sleep(0.5)

        resize_measurement = self._measure_layout("after_resize")
        if not self._validate_aspect_ratio(resize_measurement):
            self.logger.error("❌ Layout after resize does not meet 2:1 aspect ratio")
            return False

        # Test after thumbnail selection
        if self._simulate_thumbnail_selection():
            QApplication.processEvents()
            time.sleep(0.5)

            selection_measurement = self._measure_layout("after_thumbnail_selection")
            if not self._validate_aspect_ratio(selection_measurement):
                self.logger.error(
                    "❌ Layout after thumbnail selection does not meet 2:1 aspect ratio"
                )
                return False

        self.logger.info("✅ All aspect ratio tests passed!")
        return True

    def _switch_to_browse_tab(self) -> bool:
        """Switch to the browse tab."""
        try:
            # Try using tab manager
            if hasattr(self.main_widget, "tab_manager"):
                self.main_widget.tab_manager.switch_to_tab("browse")
                return True
            # Try using tab switcher
            elif hasattr(self.main_widget, "tab_switcher"):
                from src.main_window.main_widget.main_widget_tab_switcher import TabName

                self.main_widget.tab_switcher.switch_tab(TabName.BROWSE)
                return True
            else:
                self.logger.error("No tab switching mechanism found")
                return False
        except Exception as e:
            self.logger.error(f"Error switching to browse tab: {e}")
            return False

    def _measure_layout(self, context: str) -> Dict:
        """Measure the current layout dimensions."""
        try:
            main_width = self.main_widget.width()
            main_height = self.main_widget.height()

            left_width = (
                self.main_widget.left_stack.width()
                if hasattr(self.main_widget, "left_stack")
                else 0
            )
            right_width = (
                self.main_widget.right_stack.width()
                if hasattr(self.main_widget, "right_stack")
                else 0
            )

            # Calculate ratios
            total_content_width = left_width + right_width
            left_ratio = (
                left_width / total_content_width if total_content_width > 0 else 0
            )
            right_ratio = (
                right_width / total_content_width if total_content_width > 0 else 0
            )
            aspect_ratio = left_width / right_width if right_width > 0 else 0

            measurement = {
                "context": context,
                "main_width": main_width,
                "main_height": main_height,
                "left_width": left_width,
                "right_width": right_width,
                "total_content_width": total_content_width,
                "left_ratio": left_ratio,
                "right_ratio": right_ratio,
                "aspect_ratio": aspect_ratio,
                "expected_aspect_ratio": 2.0,
            }

            self.logger.info(
                f"📏 Layout measurement ({context}): "
                f"Left: {left_width}px ({left_ratio:.1%}), "
                f"Right: {right_width}px ({right_ratio:.1%}), "
                f"Ratio: {aspect_ratio:.2f} (expected: 2.0)"
            )

            return measurement

        except Exception as e:
            self.logger.error(f"Error measuring layout: {e}")
            return {}

    def _validate_aspect_ratio(self, measurement: Dict) -> bool:
        """Validate that the aspect ratio is close to 2:1."""
        if not measurement:
            return False

        aspect_ratio = measurement.get("aspect_ratio", 0)
        expected_ratio = 2.0
        tolerance = 0.2  # Allow 20% tolerance

        is_valid = abs(aspect_ratio - expected_ratio) <= tolerance

        if is_valid:
            self.logger.info(
                f"✅ Aspect ratio valid: {aspect_ratio:.2f} (within tolerance)"
            )
        else:
            self.logger.error(
                f"❌ Aspect ratio invalid: {aspect_ratio:.2f} (expected: {expected_ratio} ± {tolerance})"
            )

        return is_valid

    def _simulate_window_resize(self):
        """Simulate a window resize to test layout responsiveness."""
        try:
            current_size = self.main_widget.size()
            new_width = int(current_size.width() * 1.2)
            new_height = int(current_size.height() * 1.1)

            self.logger.info(f"🔄 Simulating window resize to {new_width}x{new_height}")
            self.main_widget.resize(new_width, new_height)

        except Exception as e:
            self.logger.error(f"Error simulating window resize: {e}")

    def _simulate_thumbnail_selection(self) -> bool:
        """Simulate selecting a thumbnail to test layout stability."""
        try:
            # Get browse tab
            browse_tab = self._get_browse_tab()
            if not browse_tab:
                self.logger.warning(
                    "Browse tab not available for thumbnail selection test"
                )
                return False

            # Get thumbnail boxes
            scroll_widget = browse_tab.sequence_picker.scroll_widget
            thumbnail_boxes = getattr(scroll_widget, "thumbnail_boxes", {})

            if not thumbnail_boxes:
                self.logger.warning("No thumbnail boxes available for selection test")
                return False

            # Select first available thumbnail
            box_names = list(thumbnail_boxes.keys())
            if box_names:
                selected_box = thumbnail_boxes[box_names[0]]
                image_label = selected_box.image_label

                self.logger.info(f"🖱️ Simulating thumbnail selection: {box_names[0]}")
                browse_tab.selection_handler.on_thumbnail_clicked(image_label)
                return True

        except Exception as e:
            self.logger.error(f"Error simulating thumbnail selection: {e}")

        return False

    def _get_browse_tab(self):
        """Get the browse tab widget."""
        try:
            if hasattr(self.main_widget, "get_tab_widget"):
                return self.main_widget.tab_manager.get_tab_widget("browse")
            elif hasattr(self.main_widget, "browse_tab"):
                return self.main_widget.browse_tab
            else:
                return None
        except Exception:
            return None


def run_aspect_ratio_test(main_widget) -> bool:
    """Run the browse tab aspect ratio test."""
    tester = BrowseTabAspectRatioTester(main_widget)
    return tester.run_test()


if __name__ == "__main__":
    print("This test requires a running main widget instance.")
    print("Import and call run_aspect_ratio_test(main_widget) from your application.")
