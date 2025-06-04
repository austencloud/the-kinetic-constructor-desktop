"""
Performance Test Suite for Browse Tab V2 Optimizations

This test suite validates the performance improvements implemented:
1. Scroll performance (120fps capability)
2. Navigation response (<100ms)
3. Widget creation optimization
4. Image cache performance (>70% hit rate)
5. Section filtering (O(1) lookup)
"""

import logging
import time
import sys
import os
from typing import List, Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QElapsedTimer
from PyQt6.QtTest import QTest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from browse_tab_v2.components.efficient_virtual_grid import EfficientVirtualGrid
from browse_tab_v2.components.modern_navigation_sidebar import ModernNavigationSidebar
from browse_tab_v2.services.fast_image_service import FastImageService
from browse_tab_v2.config.browse_tab_config import BrowseTabConfig
from browse_tab_v2.models.sequence_model import SequenceModel

logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    """Comprehensive performance test suite for Browse Tab V2."""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.config = BrowseTabConfig()
        self.test_results = {}

        # Performance targets
        self.targets = {
            "scroll_frame_time": 8.33,  # 120fps target
            "navigation_response": 100,  # <100ms
            "widget_creation": 50,  # <50ms viewport
            "cache_hit_rate": 70,  # >70%
            "section_filtering": 1.0,  # <1ms O(1) lookup
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite."""
        logger.info("Starting Browse Tab V2 Performance Test Suite")

        test_methods = [
            ("scroll_performance", self.test_scroll_performance),
            ("navigation_performance", self.test_navigation_performance),
            ("widget_creation_performance", self.test_widget_creation_performance),
            ("image_cache_performance", self.test_image_cache_performance),
            ("section_filtering_performance", self.test_section_filtering_performance),
        ]

        for test_name, test_method in test_methods:
            try:
                logger.info(f"Running test: {test_name}")
                result = test_method()
                self.test_results[test_name] = result

                # Validate against targets
                self._validate_test_result(test_name, result)

            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                self.test_results[test_name] = {"error": str(e), "passed": False}

        # Generate comprehensive report
        self._generate_performance_report()

        return self.test_results

    def test_scroll_performance(self) -> Dict[str, Any]:
        """Test scroll performance targeting 120fps."""
        logger.info("Testing scroll performance (120fps target)")

        # Create test grid with sample data
        grid = EfficientVirtualGrid(self.config)
        test_sequences = self._create_test_sequences(100)

        # Set up grid
        grid.set_item_creator(self._create_test_widget)
        grid.set_sequences(test_sequences)
        grid.show()

        # Wait for initial setup
        QTest.qWait(100)

        # Perform scroll performance test
        frame_times = []
        scroll_events = 50

        for i in range(scroll_events):
            timer = QElapsedTimer()
            timer.start()

            # Simulate scroll event
            scroll_area = grid.scroll_area
            scroll_bar = scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.value() + 50)

            # Process events
            QApplication.processEvents()

            frame_time = timer.elapsed()
            frame_times.append(frame_time)

            # Target 120fps timing
            QTest.qWait(8)  # 8ms for 120fps

        # Analyze results
        avg_frame_time = sum(frame_times) / len(frame_times)
        max_frame_time = max(frame_times)
        frame_drops = sum(
            1 for t in frame_times if t > self.targets["scroll_frame_time"]
        )

        grid.close()

        return {
            "average_frame_time": avg_frame_time,
            "max_frame_time": max_frame_time,
            "frame_drops": frame_drops,
            "total_frames": len(frame_times),
            "target_frame_time": self.targets["scroll_frame_time"],
            "passed": avg_frame_time <= self.targets["scroll_frame_time"]
            and frame_drops <= 5,
        }

    def test_navigation_performance(self) -> Dict[str, Any]:
        """Test navigation response time (<100ms target)."""
        logger.info("Testing navigation performance (<100ms target)")

        # Create test navigation sidebar
        sidebar = ModernNavigationSidebar()
        test_sequences = self._create_test_sequences(372)  # Realistic sequence count

        # Set up sidebar
        sidebar.update_sections(test_sequences, "alphabetical")
        sidebar.show()

        # Wait for setup
        QTest.qWait(50)

        # Test navigation clicks
        response_times = []
        sections = sidebar.get_sections()[:10]  # Test first 10 sections

        for section in sections:
            timer = QElapsedTimer()
            timer.start()

            # Simulate section click
            sidebar._on_section_clicked(section)

            # Process events
            QApplication.processEvents()

            response_time = timer.elapsed()
            response_times.append(response_time)

            QTest.qWait(10)  # Small delay between clicks

        # Analyze results
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        slow_responses = sum(
            1 for t in response_times if t > self.targets["navigation_response"]
        )

        sidebar.close()

        return {
            "average_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "slow_responses": slow_responses,
            "total_clicks": len(response_times),
            "target_response_time": self.targets["navigation_response"],
            "passed": avg_response_time <= self.targets["navigation_response"],
        }

    def test_widget_creation_performance(self) -> Dict[str, Any]:
        """Test widget creation performance (<50ms viewport target)."""
        logger.info("Testing widget creation performance (<50ms viewport)")

        grid = EfficientVirtualGrid(self.config)
        test_sequences = self._create_test_sequences(200)

        # Set up grid
        grid.set_item_creator(self._create_test_widget)

        # Measure widget creation time
        timer = QElapsedTimer()
        timer.start()

        grid.set_sequences(test_sequences)

        creation_time = timer.elapsed()

        # Wait for progressive creation to complete
        QTest.qWait(1000)

        grid.close()

        return {
            "viewport_creation_time": creation_time,
            "total_sequences": len(test_sequences),
            "target_creation_time": self.targets["widget_creation"],
            "passed": creation_time <= self.targets["widget_creation"],
        }

    def test_image_cache_performance(self) -> Dict[str, Any]:
        """Test image cache performance (>70% hit rate target)."""
        logger.info("Testing image cache performance (>70% hit rate)")

        image_service = FastImageService(target_width=260, target_height=220)

        # Create test image paths (simulate real usage)
        test_images = [f"test_image_{i}.png" for i in range(50)]

        # First pass - all cache misses
        for image_path in test_images:
            image_service.get_image_sync(image_path)

        # Second pass - should be cache hits (simulate repeated access)
        cache_hits_before = image_service._cache_hits

        for image_path in test_images[:30]:  # Access subset multiple times
            image_service.get_image_sync(image_path)
            image_service.get_image_sync(image_path)  # Second access

        cache_hits_after = image_service._cache_hits
        total_requests = image_service._cache_hits + image_service._cache_misses
        hit_rate = (
            (image_service._cache_hits / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "cache_hits": image_service._cache_hits,
            "cache_misses": image_service._cache_misses,
            "hit_rate": hit_rate,
            "target_hit_rate": self.targets["cache_hit_rate"],
            "passed": hit_rate >= self.targets["cache_hit_rate"],
        }

    def test_section_filtering_performance(self) -> Dict[str, Any]:
        """Test section filtering performance (O(1) lookup target)."""
        logger.info("Testing section filtering performance (O(1) lookup)")

        sidebar = ModernNavigationSidebar()
        test_sequences = self._create_test_sequences(1000)  # Large dataset

        # Set up sidebar with large dataset
        sidebar.update_sections(test_sequences, "alphabetical")

        # Test O(1) section filtering
        sections = sidebar.get_sections()
        filter_times = []

        for section in sections[:20]:  # Test multiple sections
            timer = QElapsedTimer()
            timer.start()

            # Perform section filtering
            section_sequences = sidebar.get_sequences_for_section(section)

            filter_time = timer.elapsed()
            filter_times.append(filter_time)

        # Analyze results
        avg_filter_time = sum(filter_times) / len(filter_times)
        max_filter_time = max(filter_times)
        slow_filters = sum(
            1 for t in filter_times if t > self.targets["section_filtering"]
        )

        sidebar.close()

        return {
            "average_filter_time": avg_filter_time,
            "max_filter_time": max_filter_time,
            "slow_filters": slow_filters,
            "total_filters": len(filter_times),
            "target_filter_time": self.targets["section_filtering"],
            "passed": avg_filter_time <= self.targets["section_filtering"],
        }

    def _create_test_sequences(self, count: int) -> List[SequenceModel]:
        """Create test sequences for performance testing."""
        sequences = []
        for i in range(count):
            sequence = SequenceModel(
                id=f"test_seq_{i}",
                name=f"Test Sequence {chr(65 + (i % 26))}{i}",  # A1, B2, C3, etc.
                difficulty=1 + (i % 5),
                length=4 + (i % 8),
                author=f"Author_{i % 10}",
                image_path=f"test_image_{i}.png",
            )
            sequences.append(sequence)
        return sequences

    def _create_test_widget(self, sequence: SequenceModel, index: int):
        """Create test widget for performance testing."""
        from PyQt6.QtWidgets import QLabel

        widget = QLabel(f"Test Widget {index}")
        widget.setFixedSize(260, 220)
        return widget

    def _validate_test_result(self, test_name: str, result: Dict[str, Any]):
        """Validate test result against performance targets."""
        passed = result.get("passed", False)
        if passed:
            logger.info(f"✅ {test_name}: PASSED")
        else:
            logger.warning(f"❌ {test_name}: FAILED")

    def _generate_performance_report(self):
        """Generate comprehensive performance report."""
        logger.info("\n" + "=" * 60)
        logger.info("BROWSE TAB V2 PERFORMANCE TEST REPORT")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result.get("passed", False)
        )

        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("-" * 60)

        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
            logger.info(f"{test_name}: {status}")

            # Log key metrics
            if "average_frame_time" in result:
                logger.info(
                    f"  Frame Time: {result['average_frame_time']:.1f}ms (target: {result['target_frame_time']:.1f}ms)"
                )
            if "average_response_time" in result:
                logger.info(
                    f"  Response Time: {result['average_response_time']:.1f}ms (target: {result['target_response_time']:.0f}ms)"
                )
            if "hit_rate" in result:
                logger.info(
                    f"  Cache Hit Rate: {result['hit_rate']:.1f}% (target: {result['target_hit_rate']:.0f}%)"
                )

        logger.info("=" * 60)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run performance tests
    test_suite = PerformanceTestSuite()
    results = test_suite.run_all_tests()

    # Exit with appropriate code
    passed_tests = sum(1 for result in results.values() if result.get("passed", False))
    total_tests = len(results)

    if passed_tests == total_tests:
        print(f"\n🎉 All {total_tests} performance tests PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - passed_tests} of {total_tests} tests FAILED")
        sys.exit(1)
