#!/usr/bin/env python3
"""
Focused Performance Test for Browse Tab v2 Components

This test focuses on measuring the specific performance bottlenecks we identified:
- Widget creation speed (target: <50ms, currently 60-130ms)
- Navigation responsiveness (target: <100ms, currently 118-119ms)
- Thumbnail interaction speed (target: <200ms, currently 491ms)

This test works with the actual browse tab v2 components and provides actionable insights.
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QElapsedTimer, QTimer
from PyQt6.QtTest import QTest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from browse_tab.components.thumbnail_card import ThumbnailCard
    from browse_tab.components.sequence_viewer import SequenceViewer
    from browse_tab.core.interfaces import SequenceModel, BrowseTabConfig
    from browse_tab.services.cache_service import CacheService

    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Browse tab v2 components not available: {e}")
    COMPONENTS_AVAILABLE = False


@dataclass
class PerformanceResult:
    """Container for performance test results."""

    test_name: str
    duration_ms: float
    target_ms: float
    passed: bool
    details: Dict[str, Any]


class FocusedPerformanceTest:
    """Focused performance testing for specific bottlenecks."""

    def __init__(self):
        self.timer = QElapsedTimer()
        self.results: List[PerformanceResult] = []
        self.app = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_test_environment(self):
        """Setup minimal test environment."""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        self.logger.info("Test environment setup complete")

    def create_test_sequence(self, name: str, beat_count: int) -> SequenceModel:
        """Create a test sequence with proper structure."""
        return SequenceModel(
            id=f"test_{name}_{beat_count}",
            name=name,
            thumbnails=[f"test_thumbnail_{name}.png"],
            difficulty=3,
            length=beat_count,
            author="Test Author",
            tags=["test", "performance"],
            is_favorite=False,
            metadata={"beat_count": beat_count},
        )

    def test_widget_creation_performance(self):
        """Test 1: Widget Creation Performance (Target: <50ms)"""
        self.logger.info("=== TESTING WIDGET CREATION PERFORMANCE ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping widget tests")
            return

        # Test different sequence complexities
        test_cases = [
            ("simple_2_beats", 2),
            ("simple_3_beats", 3),
            ("medium_5_beats", 5),
            ("medium_7_beats", 7),
            ("complex_10_beats", 10),
            ("complex_12_beats", 12),
        ]

        for test_name, beat_count in test_cases:
            sequence = self.create_test_sequence(test_name, beat_count)

            # Measure widget creation time
            self.timer.start()
            try:
                config = BrowseTabConfig()
                widget = ThumbnailCard(sequence, config)
                widget.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                # Clean up
                widget.deleteLater()
                QApplication.processEvents()

                result = PerformanceResult(
                    test_name=f"widget_creation_{test_name}",
                    duration_ms=duration_ms,
                    target_ms=50.0,
                    passed=duration_ms <= 50.0,
                    details={"beat_count": beat_count, "sequence_name": test_name},
                )

                self.results.append(result)
                status = "✅ PASS" if result.passed else "❌ FAIL"
                self.logger.info(
                    f"{status} Widget creation {test_name}: {duration_ms:.1f}ms (target: 50ms)"
                )

            except Exception as e:
                self.logger.error(f"Widget creation test failed for {test_name}: {e}")

    def test_sequence_viewer_performance(self):
        """Test 2: Sequence Viewer Performance (Target: <200ms)"""
        self.logger.info("=== TESTING SEQUENCE VIEWER PERFORMANCE ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping viewer tests")
            return

        test_sequences = [
            self.create_test_sequence("viewer_test_simple", 3),
            self.create_test_sequence("viewer_test_medium", 6),
            self.create_test_sequence("viewer_test_complex", 10),
        ]

        for sequence in test_sequences:
            # Test viewer initialization
            self.timer.start()
            try:
                config = BrowseTabConfig()
                viewer = SequenceViewer(config)
                viewer.show()
                QApplication.processEvents()
                init_duration = self.timer.elapsed()

                # Test sequence display
                self.timer.restart()
                viewer.display_sequence(sequence)
                QApplication.processEvents()
                display_duration = self.timer.elapsed()

                # Clean up
                viewer.deleteLater()
                QApplication.processEvents()

                # Record initialization result
                init_result = PerformanceResult(
                    test_name=f"viewer_init_{sequence.name}",
                    duration_ms=init_duration,
                    target_ms=100.0,
                    passed=init_duration <= 100.0,
                    details={
                        "operation": "initialization",
                        "beat_count": sequence.length,
                    },
                )

                # Record display result
                display_result = PerformanceResult(
                    test_name=f"viewer_display_{sequence.name}",
                    duration_ms=display_duration,
                    target_ms=200.0,
                    passed=display_duration <= 200.0,
                    details={
                        "operation": "display_sequence",
                        "beat_count": sequence.length,
                    },
                )

                self.results.extend([init_result, display_result])

                init_status = "✅ PASS" if init_result.passed else "❌ FAIL"
                display_status = "✅ PASS" if display_result.passed else "❌ FAIL"

                self.logger.info(
                    f"{init_status} Viewer init {sequence.name}: {init_duration:.1f}ms (target: 100ms)"
                )
                self.logger.info(
                    f"{display_status} Viewer display {sequence.name}: {display_duration:.1f}ms (target: 200ms)"
                )

            except Exception as e:
                self.logger.error(
                    f"Sequence viewer test failed for {sequence.name}: {e}"
                )

    def test_cache_service_performance(self):
        """Test 3: Cache Service Performance"""
        self.logger.info("=== TESTING CACHE SERVICE PERFORMANCE ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping cache tests")
            return

        try:
            cache_service = CacheService()

            # Test cache operations
            test_operations = [
                ("cache_clear", lambda: cache_service.clear_cache()),
                ("cache_get_stats", lambda: cache_service.get_cache_stats()),
            ]

            for op_name, operation in test_operations:
                self.timer.start()
                try:
                    operation()
                    duration_ms = self.timer.elapsed()

                    result = PerformanceResult(
                        test_name=f"cache_{op_name}",
                        duration_ms=duration_ms,
                        target_ms=50.0,
                        passed=duration_ms <= 50.0,
                        details={"operation": op_name},
                    )

                    self.results.append(result)
                    status = "✅ PASS" if result.passed else "❌ FAIL"
                    self.logger.info(
                        f"{status} Cache {op_name}: {duration_ms:.1f}ms (target: 50ms)"
                    )

                except Exception as e:
                    self.logger.error(f"Cache operation {op_name} failed: {e}")

        except Exception as e:
            self.logger.error(f"Cache service test failed: {e}")

    def run_all_tests(self):
        """Run all focused performance tests."""
        self.logger.info("Starting focused performance tests...")

        self.setup_test_environment()

        # Run tests
        self.test_widget_creation_performance()
        self.test_sequence_viewer_performance()
        self.test_cache_service_performance()

        # Generate report
        self.generate_performance_report()

    def generate_performance_report(self):
        """Generate comprehensive performance report with actionable insights."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("FOCUSED PERFORMANCE TEST RESULTS")
        self.logger.info("=" * 80)

        if not self.results:
            self.logger.warning("No test results available")
            return

        # Overall statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # Category analysis
        categories = {}
        for result in self.results:
            category = result.test_name.split("_")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        self.logger.info("\nCATEGORY BREAKDOWN:")
        self.logger.info("-" * 40)

        for category, results in categories.items():
            avg_time = sum(r.duration_ms for r in results) / len(results)
            passed = sum(1 for r in results if r.passed)
            total = len(results)

            self.logger.info(
                f"{category.upper()}: {passed}/{total} passed, avg: {avg_time:.1f}ms"
            )

        # Specific recommendations
        self.logger.info("\nPERFORMANCE RECOMMENDATIONS:")
        self.logger.info("-" * 40)

        widget_tests = [r for r in self.results if "widget_creation" in r.test_name]
        if widget_tests:
            avg_widget_time = sum(r.duration_ms for r in widget_tests) / len(
                widget_tests
            )
            if avg_widget_time > 50:
                self.logger.info(f"🔧 WIDGET CREATION OPTIMIZATION NEEDED:")
                self.logger.info(
                    f"   Current average: {avg_widget_time:.1f}ms, Target: 50ms"
                )
                self.logger.info(f"   Recommendations:")
                self.logger.info(f"   - Optimize ModernThumbnailCard initialization")
                self.logger.info(f"   - Reduce layout calculation complexity")
                self.logger.info(
                    f"   - Implement lazy loading for non-critical elements"
                )

        viewer_tests = [r for r in self.results if "viewer" in r.test_name]
        if viewer_tests:
            avg_viewer_time = sum(r.duration_ms for r in viewer_tests) / len(
                viewer_tests
            )
            if avg_viewer_time > 150:
                self.logger.info(f"🔧 SEQUENCE VIEWER OPTIMIZATION NEEDED:")
                self.logger.info(
                    f"   Current average: {avg_viewer_time:.1f}ms, Target: 150ms"
                )
                self.logger.info(f"   Recommendations:")
                self.logger.info(f"   - Pre-initialize viewer components")
                self.logger.info(f"   - Optimize sequence data processing")
                self.logger.info(f"   - Implement progressive rendering")

        self.logger.info("\n" + "=" * 80)


def main():
    """Main execution function."""
    test_suite = FocusedPerformanceTest()
    test_suite.run_all_tests()
    return 0


if __name__ == "__main__":
    sys.exit(main())
