import logging
import time
from typing import Dict, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class BrowseTabLayoutMonitor(QObject):
    layout_violation_detected = pyqtSignal(str, dict)

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.logger = logging.getLogger(__name__)
        self.measurements: List[Dict] = []
        self.monitoring_active = False

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def start_monitoring(self):
        self.monitoring_active = True
        self.logger.info("🔍 Starting Browse Tab layout monitoring...")

    def stop_monitoring(self):
        self.monitoring_active = False
        self.logger.info("⏹️ Stopping Browse Tab layout monitoring...")
        self._generate_report()

    def measure_layout(self, event_name: str = "measurement") -> Dict:
        try:
            browse_tab = self._get_browse_tab()
            if not browse_tab:
                return {"error": "Browse Tab not available"}

            main_width = self.main_widget.width()
            main_height = self.main_widget.height()

            left_stack_width = getattr(self.main_widget, "left_stack", None)
            right_stack_width = getattr(self.main_widget, "right_stack", None)

            left_width = left_stack_width.width() if left_stack_width else 0
            right_width = right_stack_width.width() if right_stack_width else 0

            sequence_viewer = browse_tab.sequence_viewer
            viewer_width = sequence_viewer.width()
            viewer_height = sequence_viewer.height()

            expected_right_width = main_width / 3
            expected_left_width = main_width * 2 / 3

            width_violation = abs(viewer_width - expected_right_width) > 50
            ratio_violation = (
                abs(left_width / right_width - 2.0) > 0.3 if right_width > 0 else True
            )

            measurement = {
                "timestamp": time.time(),
                "event": event_name,
                "main_width": main_width,
                "main_height": main_height,
                "left_stack_width": left_width,
                "right_stack_width": right_width,
                "sequence_viewer_width": viewer_width,
                "sequence_viewer_height": viewer_height,
                "expected_right_width": expected_right_width,
                "expected_left_width": expected_left_width,
                "width_violation": width_violation,
                "ratio_violation": ratio_violation,
                "actual_ratio": left_width / right_width if right_width > 0 else 0,
                "expected_ratio": 2.0,
            }

            self.measurements.append(measurement)

            if width_violation or ratio_violation:
                self.logger.warning(
                    f"🚨 LAYOUT VIOLATION at {event_name}: "
                    f"Viewer width: {viewer_width}px (expected: {expected_right_width:.0f}px), "
                    f"Ratio: {measurement['actual_ratio']:.2f} (expected: 2.0)"
                )
                self.layout_violation_detected.emit(event_name, measurement)
            else:
                self.logger.info(
                    f"✅ Layout OK at {event_name}: "
                    f"Viewer width: {viewer_width}px, Ratio: {measurement['actual_ratio']:.2f}"
                )

            return measurement

        except Exception as e:
            error_msg = f"Error measuring layout: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg}

    def _get_browse_tab(self):
        try:
            return self.main_widget.get_tab_widget("browse")
        except:
            try:
                return getattr(self.main_widget, "browse_tab", None)
            except:
                return None

    def _generate_report(self):
        if not self.measurements:
            self.logger.info("No measurements recorded.")
            return

        violations = [
            m
            for m in self.measurements
            if m.get("width_violation") or m.get("ratio_violation")
        ]

        self.logger.info(f"\n📊 BROWSE TAB LAYOUT REPORT")
        self.logger.info(f"Total measurements: {len(self.measurements)}")
        self.logger.info(f"Layout violations: {len(violations)}")

        if violations:
            self.logger.warning("🚨 VIOLATIONS DETECTED:")
            for v in violations:
                self.logger.warning(
                    f"  - {v['event']}: Viewer {v['sequence_viewer_width']}px "
                    f"(expected {v['expected_right_width']:.0f}px), "
                    f"Ratio {v['actual_ratio']:.2f}"
                )
