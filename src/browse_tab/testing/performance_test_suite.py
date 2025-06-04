"""
Comprehensive Performance Testing Suite for Browse Tab V2

This module provides real-world performance testing to identify and resolve
user-perceived performance issues in the browse tab navigation system.
"""

import logging
import time
import statistics
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QTimer, QElapsedTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

logger = logging.getLogger(__name__)


class PerformanceTestSuite(QObject):
    """Comprehensive performance testing suite for browse tab components."""

    # Signals for test results
    test_completed = pyqtSignal(str, dict)  # test_name, results
    test_failed = pyqtSignal(str, str)  # test_name, error_message

    def __init__(self, browse_tab_view):
        super().__init__()
        self.browse_tab_view = browse_tab_view
        self.timer = QElapsedTimer()
        self.test_results = {}

        # Performance targets (user-perceived)
        self.targets = {
            "navigation_click_response": 100,  # 100ms for section navigation
            "scroll_smoothness": 16.67,  # 60fps for smooth scrolling
            "thumbnail_click_response": 200,  # 200ms for sequence viewer start
            "sidebar_scroll_performance": 16.67,  # 60fps for sidebar scrolling
            "rapid_navigation_stability": 150,  # 150ms for rapid section switching
            "memory_stability": 1.2,  # Max 20% memory increase during tests
        }

    def run_comprehensive_tests(self):
        """Run all performance tests in sequence."""
        logger.info("Starting comprehensive performance test suite...")

        tests = [
            self.test_navigation_section_jumping,
            self.test_sidebar_scroll_performance,
            self.test_thumbnail_click_pipeline,
            self.test_rapid_section_switching,
            self.test_memory_usage_stability,
            self.test_concurrent_operations,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed: {e}")
                self.test_failed.emit(test.__name__, str(e))

        self._generate_performance_report()

    def test_navigation_section_jumping(self):
        """Test complete click-to-scroll pipeline for navigation sections."""
        logger.info("Testing navigation section jumping performance...")

        if not hasattr(self.browse_tab_view, "navigation_sidebar"):
            logger.warning("Navigation sidebar not available for testing")
            return

        sidebar = self.browse_tab_view.navigation_sidebar
        sections = sidebar.get_sections()

        if not sections:
            logger.warning("No sections available for testing")
            return

        response_times = []

        # Test clicking each section and measure end-to-end response
        for section_id in sections[:10]:  # Test first 10 sections
            self.timer.start()

            # Simulate section click
            sidebar._on_section_clicked(section_id)

            # Wait for scroll completion and measure total time
            start_time = self.timer.elapsed()
            self._wait_for_scroll_completion()
            total_time = self.timer.elapsed() - start_time

            response_times.append(total_time)
            logger.debug(f"Section {section_id} response time: {total_time:.1f}ms")

            # Small delay between tests
            QTest.qWait(50)

        # Analyze results
        avg_response = statistics.mean(response_times)
        max_response = max(response_times)
        target = self.targets["navigation_click_response"]

        results = {
            "average_response_time": avg_response,
            "max_response_time": max_response,
            "target": target,
            "passed": avg_response <= target,
            "samples": len(response_times),
            "raw_times": response_times,
        }

        self.test_results["navigation_section_jumping"] = results
        self.test_completed.emit("navigation_section_jumping", results)

        logger.info(
            f"Navigation test: avg={avg_response:.1f}ms, max={max_response:.1f}ms, target={target}ms"
        )

    def test_sidebar_scroll_performance(self):
        """Test scroll performance within the navigation sidebar."""
        logger.info("Testing sidebar scroll performance...")

        if not hasattr(self.browse_tab_view, "navigation_sidebar"):
            logger.warning("Navigation sidebar not available for testing")
            return

        sidebar = self.browse_tab_view.navigation_sidebar
        content_area = getattr(sidebar, "content_area", None)

        if not content_area:
            logger.warning("Sidebar content area not available for testing")
            return

        frame_times = []
        scroll_events = 20  # Number of scroll events to test

        # Simulate continuous scrolling in sidebar
        for i in range(scroll_events):
            self.timer.start()

            # Simulate scroll wheel event
            scroll_bar = content_area.verticalScrollBar()
            current_value = scroll_bar.value()
            new_value = min(current_value + 50, scroll_bar.maximum())
            scroll_bar.setValue(new_value)

            # Process events and measure frame time
            QApplication.processEvents()
            frame_time = self.timer.elapsed()
            frame_times.append(frame_time)

            QTest.qWait(16)  # ~60fps timing

        # Analyze frame performance
        avg_frame_time = statistics.mean(frame_times)
        max_frame_time = max(frame_times)
        target = self.targets["sidebar_scroll_performance"]

        results = {
            "average_frame_time": avg_frame_time,
            "max_frame_time": max_frame_time,
            "target": target,
            "passed": avg_frame_time <= target,
            "frame_drops": sum(1 for t in frame_times if t > target),
            "samples": len(frame_times),
            "raw_times": frame_times,
        }

        self.test_results["sidebar_scroll_performance"] = results
        self.test_completed.emit("sidebar_scroll_performance", results)

        logger.info(
            f"Sidebar scroll test: avg={avg_frame_time:.1f}ms, max={max_frame_time:.1f}ms, drops={results['frame_drops']}"
        )

    def test_thumbnail_click_pipeline(self):
        """Test complete pictograph click-to-animation pipeline."""
        logger.info("Testing thumbnail click pipeline performance...")

        if not hasattr(self.browse_tab_view, "thumbnail_grid"):
            logger.warning("Thumbnail grid not available for testing")
            return

        grid = self.browse_tab_view.thumbnail_grid
        sequences = getattr(self.browse_tab_view, "_sequences", [])

        if not sequences:
            logger.warning("No sequences available for testing")
            return

        response_times = []

        # Test clicking first 5 thumbnails
        for i, sequence in enumerate(sequences[:5]):
            self.timer.start()

            # Simulate thumbnail click
            sequence_id = getattr(sequence, "id", f"test_seq_{i}")
            self.browse_tab_view._on_item_clicked(sequence_id, i)

            # Wait for sequence viewer to update
            self._wait_for_sequence_viewer_update()
            total_time = self.timer.elapsed()

            response_times.append(total_time)
            logger.debug(f"Thumbnail {sequence_id} response time: {total_time:.1f}ms")

            QTest.qWait(100)  # Delay between tests

        # Analyze results
        avg_response = statistics.mean(response_times)
        max_response = max(response_times)
        target = self.targets["thumbnail_click_response"]

        results = {
            "average_response_time": avg_response,
            "max_response_time": max_response,
            "target": target,
            "passed": avg_response <= target,
            "samples": len(response_times),
            "raw_times": response_times,
        }

        self.test_results["thumbnail_click_pipeline"] = results
        self.test_completed.emit("thumbnail_click_pipeline", results)

        logger.info(
            f"Thumbnail test: avg={avg_response:.1f}ms, max={max_response:.1f}ms, target={target}ms"
        )

    def test_rapid_section_switching(self):
        """Test rapid section switching for cumulative performance degradation."""
        logger.info("Testing rapid section switching performance...")

        if not hasattr(self.browse_tab_view, "navigation_sidebar"):
            logger.warning("Navigation sidebar not available for testing")
            return

        sidebar = self.browse_tab_view.navigation_sidebar
        sections = sidebar.get_sections()

        if len(sections) < 4:
            logger.warning("Not enough sections for rapid switching test")
            return

        # Test rapid switching pattern: A→Ω→B→Σ (if available)
        test_pattern = []
        for target in ["A", "Ω", "B", "Σ"]:
            if target in sections:
                test_pattern.append(target)

        if len(test_pattern) < 2:
            # Fallback to first few sections
            test_pattern = sections[:4]

        response_times = []

        # Perform rapid switching
        for i, section_id in enumerate(test_pattern * 3):  # Repeat pattern 3 times
            self.timer.start()

            sidebar._on_section_clicked(section_id)
            self._wait_for_scroll_completion()

            total_time = self.timer.elapsed()
            response_times.append(total_time)

            logger.debug(f"Rapid switch {i+1} to {section_id}: {total_time:.1f}ms")

            # Minimal delay for rapid switching
            QTest.qWait(20)

        # Analyze for performance degradation
        first_half = response_times[: len(response_times) // 2]
        second_half = response_times[len(response_times) // 2 :]

        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        degradation = (
            ((avg_second - avg_first) / avg_first) * 100 if avg_first > 0 else 0
        )

        target = self.targets["rapid_navigation_stability"]

        results = {
            "average_first_half": avg_first,
            "average_second_half": avg_second,
            "performance_degradation_percent": degradation,
            "target": target,
            "passed": avg_second <= target,
            "samples": len(response_times),
            "raw_times": response_times,
        }

        self.test_results["rapid_section_switching"] = results
        self.test_completed.emit("rapid_section_switching", results)

        logger.info(
            f"Rapid switching test: degradation={degradation:.1f}%, avg_second={avg_second:.1f}ms"
        )

    def test_memory_usage_stability(self):
        """Test memory usage stability during extended operations."""
        logger.info("Testing memory usage stability...")

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform extended operations
            for _ in range(20):
                # Simulate heavy usage
                if hasattr(self.browse_tab_view, "navigation_sidebar"):
                    sidebar = self.browse_tab_view.navigation_sidebar
                    sections = sidebar.get_sections()

                    for section in sections[:5]:
                        sidebar._on_section_clicked(section)
                        QTest.qWait(10)

                # Force garbage collection
                import gc

                gc.collect()
                QTest.qWait(50)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = (final_memory - initial_memory) / initial_memory

            target = self.targets["memory_stability"]

            results = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_percent": memory_increase * 100,
                "target_max_increase_percent": (target - 1) * 100,
                "passed": memory_increase <= target,
            }

            self.test_results["memory_usage_stability"] = results
            self.test_completed.emit("memory_usage_stability", results)

            logger.info(
                f"Memory test: {memory_increase*100:.1f}% increase, target={target*100:.1f}%"
            )

        except ImportError:
            logger.warning("psutil not available for memory testing")

    def test_concurrent_operations(self):
        """Test performance during simultaneous operations."""
        logger.info("Testing concurrent operations performance...")

        response_times = []

        # Test simultaneous scrolling and navigation
        for i in range(10):
            self.timer.start()

            # Simulate concurrent operations
            if hasattr(self.browse_tab_view, "thumbnail_grid"):
                grid = self.browse_tab_view.thumbnail_grid
                scroll_area = getattr(grid, "scroll_area", None)

                if scroll_area:
                    # Scroll in main area
                    scroll_bar = scroll_area.verticalScrollBar()
                    scroll_bar.setValue(scroll_bar.value() + 100)

            # Navigate to section simultaneously
            if hasattr(self.browse_tab_view, "navigation_sidebar"):
                sidebar = self.browse_tab_view.navigation_sidebar
                sections = sidebar.get_sections()
                if sections:
                    section = sections[i % len(sections)]
                    sidebar._on_section_clicked(section)

            # Process events and measure
            QApplication.processEvents()
            total_time = self.timer.elapsed()
            response_times.append(total_time)

            QTest.qWait(50)

        avg_response = statistics.mean(response_times)
        max_response = max(response_times)

        results = {
            "average_response_time": avg_response,
            "max_response_time": max_response,
            "samples": len(response_times),
            "raw_times": response_times,
        }

        self.test_results["concurrent_operations"] = results
        self.test_completed.emit("concurrent_operations", results)

        logger.info(
            f"Concurrent ops test: avg={avg_response:.1f}ms, max={max_response:.1f}ms"
        )

    def _wait_for_scroll_completion(self, timeout_ms: int = 1000):
        """Wait for scroll animation to complete."""
        if hasattr(self.browse_tab_view, "smooth_scroll"):
            smooth_scroll = self.browse_tab_view.smooth_scroll

            # Wait for animation to complete
            start_time = time.time()
            while time.time() - start_time < timeout_ms / 1000:
                if not getattr(smooth_scroll, "_animation_active", False):
                    break
                QApplication.processEvents()
                QTest.qWait(10)
        else:
            # Fallback wait
            QTest.qWait(100)

    def _wait_for_sequence_viewer_update(self, timeout_ms: int = 500):
        """Wait for sequence viewer to update."""
        if hasattr(self.browse_tab_view, "sequence_viewer"):
            # Wait for viewer to process the update
            QTest.qWait(100)
            QApplication.processEvents()
        else:
            QTest.qWait(50)

    def _generate_performance_report(self):
        """Generate comprehensive performance report."""
        logger.info("=== PERFORMANCE TEST RESULTS ===")

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result.get("passed", False)
        )

        logger.info(f"Tests passed: {passed_tests}/{total_tests}")

        for test_name, results in self.test_results.items():
            logger.info(f"\n{test_name.upper()}:")

            if "average_response_time" in results:
                logger.info(f"  Average: {results['average_response_time']:.1f}ms")
                logger.info(f"  Maximum: {results['max_response_time']:.1f}ms")
                logger.info(f"  Target: {results.get('target', 'N/A')}ms")
                logger.info(f"  Status: {'PASS' if results.get('passed') else 'FAIL'}")

            if "frame_drops" in results:
                logger.info(f"  Frame drops: {results['frame_drops']}")

            if "memory_increase_percent" in results:
                logger.info(
                    f"  Memory increase: {results['memory_increase_percent']:.1f}%"
                )

        logger.info("=== END PERFORMANCE REPORT ===")

        return self.test_results
