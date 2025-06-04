#!/usr/bin/env python3
"""
Maximum Speed Performance Test for Browse Tab v2

This test eliminates first-run penalties by running multiple iterations within
a single session to measure true steady-state performance.
"""

import sys
import time
import logging
import statistics
from pathlib import Path
from typing import List, Dict, Any, Tuple
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
class SpeedTestResult:
    """Container for speed test results."""

    test_name: str
    iterations: int
    first_run_ms: float
    steady_state_avg_ms: float
    steady_state_min_ms: float
    steady_state_max_ms: float
    steady_state_std_ms: float
    target_ms: float
    steady_state_passed: bool
    improvement_factor: float


class MaximumSpeedTest:
    """Maximum speed testing with multiple iterations."""

    def __init__(self):
        self.timer = QElapsedTimer()
        self.results: List[SpeedTestResult] = []
        self.app = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_test_environment(self):
        """Setup test environment."""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        self.logger.info("Maximum speed test environment setup complete")

    def create_test_sequence(self, name: str, beat_count: int) -> SequenceModel:
        """Create a test sequence with proper structure."""
        return SequenceModel(
            id=f"speed_test_{name}_{beat_count}",
            name=name,
            thumbnails=[f"speed_test_thumbnail_{name}.png"],
            difficulty=3,
            length=beat_count,
            author="Speed Test",
            tags=["speed", "performance"],
            is_favorite=False,
            metadata={"beat_count": beat_count},
        )

    def run_widget_creation_speed_test(self, iterations: int = 20):
        """Test widget creation speed with multiple iterations."""
        self.logger.info(
            f"=== WIDGET CREATION SPEED TEST ({iterations} iterations) ==="
        )

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping widget speed tests")
            return

        test_cases = [("simple", 3), ("medium", 6), ("complex", 10)]

        for test_name, beat_count in test_cases:
            sequence = self.create_test_sequence(test_name, beat_count)
            config = BrowseTabConfig()

            times = []

            for i in range(iterations):
                self.timer.start()
                try:
                    widget = ThumbnailCard(sequence, config)
                    widget.show()
                    QApplication.processEvents()
                    duration_ms = self.timer.elapsed()

                    # Clean up immediately
                    widget.deleteLater()
                    QApplication.processEvents()

                    times.append(duration_ms)

                    if i == 0:
                        self.logger.info(
                            f"  First run {test_name}: {duration_ms:.1f}ms"
                        )
                    elif i % 5 == 0:
                        recent_avg = sum(times[-5:]) / min(5, len(times))
                        self.logger.info(
                            f"  Iteration {i}: {duration_ms:.1f}ms (recent avg: {recent_avg:.1f}ms)"
                        )

                except Exception as e:
                    self.logger.error(f"Widget creation failed at iteration {i}: {e}")
                    continue

            if len(times) > 1:
                first_run = times[0]
                steady_state = times[1:]  # Exclude first run

                result = SpeedTestResult(
                    test_name=f"widget_creation_{test_name}",
                    iterations=len(times),
                    first_run_ms=first_run,
                    steady_state_avg_ms=statistics.mean(steady_state),
                    steady_state_min_ms=min(steady_state),
                    steady_state_max_ms=max(steady_state),
                    steady_state_std_ms=(
                        statistics.stdev(steady_state) if len(steady_state) > 1 else 0
                    ),
                    target_ms=50.0,
                    steady_state_passed=statistics.mean(steady_state) <= 50.0,
                    improvement_factor=first_run / statistics.mean(steady_state),
                )

                self.results.append(result)

                status = "✅ PASS" if result.steady_state_passed else "❌ FAIL"
                self.logger.info(
                    f"{status} Widget {test_name}: {result.steady_state_avg_ms:.1f}ms avg "
                    f"(first: {result.first_run_ms:.1f}ms, improvement: {result.improvement_factor:.1f}x)"
                )

    def run_sequence_viewer_speed_test(self, iterations: int = 15):
        """Test sequence viewer speed with multiple iterations."""
        self.logger.info(
            f"=== SEQUENCE VIEWER SPEED TEST ({iterations} iterations) ==="
        )

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping viewer speed tests")
            return

        test_sequences = [
            self.create_test_sequence("viewer_simple", 3),
            self.create_test_sequence("viewer_medium", 6),
            self.create_test_sequence("viewer_complex", 10),
        ]

        config = BrowseTabConfig()

        # Test viewer initialization speed
        init_times = []
        display_times = []

        for i in range(iterations):
            try:
                # Test initialization
                self.timer.start()
                viewer = SequenceViewer(config)
                viewer.show()
                QApplication.processEvents()
                init_duration = self.timer.elapsed()
                init_times.append(init_duration)

                # Test display speed with a sequence
                sequence = test_sequences[i % len(test_sequences)]
                self.timer.restart()
                viewer.display_sequence(sequence)
                QApplication.processEvents()
                display_duration = self.timer.elapsed()
                display_times.append(display_duration)

                if i == 0:
                    self.logger.info(
                        f"  First run init: {init_duration:.1f}ms, display: {display_duration:.1f}ms"
                    )
                elif i % 3 == 0:
                    recent_init_avg = sum(init_times[-3:]) / min(3, len(init_times))
                    recent_display_avg = sum(display_times[-3:]) / min(
                        3, len(display_times)
                    )
                    self.logger.info(
                        f"  Iteration {i}: init {init_duration:.1f}ms, display {display_duration:.1f}ms "
                        f"(recent avg: {recent_init_avg:.1f}ms/{recent_display_avg:.1f}ms)"
                    )

                # Clean up
                viewer.deleteLater()
                QApplication.processEvents()

            except Exception as e:
                self.logger.error(f"Viewer test failed at iteration {i}: {e}")
                continue

        # Process initialization results
        if len(init_times) > 1:
            first_init = init_times[0]
            steady_init = init_times[1:]

            init_result = SpeedTestResult(
                test_name="viewer_initialization",
                iterations=len(init_times),
                first_run_ms=first_init,
                steady_state_avg_ms=statistics.mean(steady_init),
                steady_state_min_ms=min(steady_init),
                steady_state_max_ms=max(steady_init),
                steady_state_std_ms=(
                    statistics.stdev(steady_init) if len(steady_init) > 1 else 0
                ),
                target_ms=100.0,
                steady_state_passed=statistics.mean(steady_init) <= 100.0,
                improvement_factor=first_init / statistics.mean(steady_init),
            )

            self.results.append(init_result)

        # Process display results
        if len(display_times) > 1:
            first_display = display_times[0]
            steady_display = display_times[1:]

            display_result = SpeedTestResult(
                test_name="viewer_display",
                iterations=len(display_times),
                first_run_ms=first_display,
                steady_state_avg_ms=statistics.mean(steady_display),
                steady_state_min_ms=min(steady_display),
                steady_state_max_ms=max(steady_display),
                steady_state_std_ms=(
                    statistics.stdev(steady_display) if len(steady_display) > 1 else 0
                ),
                target_ms=200.0,
                steady_state_passed=statistics.mean(steady_display) <= 200.0,
                improvement_factor=first_display / statistics.mean(steady_display),
            )

            self.results.append(display_result)

    def run_rapid_fire_test(self, iterations: int = 50):
        """Test rapid-fire widget creation for maximum throughput."""
        self.logger.info(f"=== RAPID FIRE TEST ({iterations} iterations) ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping rapid fire test")
            return

        sequence = self.create_test_sequence("rapid_fire", 5)
        config = BrowseTabConfig()

        # Warm up first
        for _ in range(3):
            widget = ThumbnailCard(sequence, config)
            widget.show()
            QApplication.processEvents()
            widget.deleteLater()
            QApplication.processEvents()

        # Rapid fire test
        start_time = time.time()
        times = []

        for i in range(iterations):
            self.timer.start()
            widget = ThumbnailCard(sequence, config)
            widget.show()
            QApplication.processEvents()
            duration_ms = self.timer.elapsed()
            widget.deleteLater()
            QApplication.processEvents()

            times.append(duration_ms)

            if i % 10 == 0:
                recent_avg = sum(times[-10:]) / min(10, len(times))
                self.logger.info(
                    f"  Rapid fire {i}: {duration_ms:.1f}ms (recent avg: {recent_avg:.1f}ms)"
                )

        total_time = time.time() - start_time
        throughput = iterations / total_time

        rapid_result = SpeedTestResult(
            test_name="rapid_fire_widgets",
            iterations=iterations,
            first_run_ms=times[0],
            steady_state_avg_ms=statistics.mean(times),
            steady_state_min_ms=min(times),
            steady_state_max_ms=max(times),
            steady_state_std_ms=statistics.stdev(times),
            target_ms=50.0,
            steady_state_passed=statistics.mean(times) <= 50.0,
            improvement_factor=1.0,  # No first-run penalty in this test
        )

        self.results.append(rapid_result)

        self.logger.info(
            f"🚀 Rapid fire complete: {throughput:.1f} widgets/second, "
            f"avg: {rapid_result.steady_state_avg_ms:.1f}ms"
        )

    def run_all_speed_tests(self):
        """Run all maximum speed tests."""
        self.logger.info("🚀 Starting MAXIMUM SPEED performance tests...")

        self.setup_test_environment()

        # Run speed tests
        self.run_widget_creation_speed_test(iterations=20)
        self.run_sequence_viewer_speed_test(iterations=15)
        self.run_rapid_fire_test(iterations=50)

        # Generate comprehensive report
        self.generate_speed_report()

    def generate_speed_report(self):
        """Generate comprehensive speed analysis report."""
        self.logger.info("\n" + "🚀" * 40)
        self.logger.info("MAXIMUM SPEED PERFORMANCE ANALYSIS")
        self.logger.info("🚀" * 40)

        if not self.results:
            self.logger.warning("No speed test results available")
            return

        # Overall statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.steady_state_passed)

        self.logger.info(f"Total Speed Tests: {total_tests}")
        self.logger.info(f"Passed (Steady State): {passed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # Detailed results
        self.logger.info("\nDETAILED SPEED ANALYSIS:")
        self.logger.info("-" * 60)

        for result in self.results:
            status = "✅ PASS" if result.steady_state_passed else "❌ FAIL"
            self.logger.info(f"{status} {result.test_name}:")
            self.logger.info(f"  First Run: {result.first_run_ms:.1f}ms")
            self.logger.info(
                f"  Steady State: {result.steady_state_avg_ms:.1f}ms ± {result.steady_state_std_ms:.1f}ms"
            )
            self.logger.info(
                f"  Range: {result.steady_state_min_ms:.1f}ms - {result.steady_state_max_ms:.1f}ms"
            )
            self.logger.info(f"  Target: {result.target_ms:.1f}ms")
            self.logger.info(
                f"  Improvement: {result.improvement_factor:.1f}x faster after warmup"
            )
            self.logger.info("")

        # Performance insights
        self.logger.info("🎯 MAXIMUM SPEED INSIGHTS:")
        self.logger.info("-" * 40)

        widget_results = [r for r in self.results if "widget" in r.test_name]
        if widget_results:
            avg_widget_speed = statistics.mean(
                [r.steady_state_avg_ms for r in widget_results]
            )
            min_widget_speed = min([r.steady_state_min_ms for r in widget_results])
            max_improvement = max([r.improvement_factor for r in widget_results])

            self.logger.info(f"🔧 Widget Creation Maximum Speed:")
            self.logger.info(f"   Average Steady State: {avg_widget_speed:.1f}ms")
            self.logger.info(f"   Fastest Single Widget: {min_widget_speed:.1f}ms")
            self.logger.info(
                f"   Maximum Improvement: {max_improvement:.1f}x after warmup"
            )

        viewer_results = [r for r in self.results if "viewer" in r.test_name]
        if viewer_results:
            for result in viewer_results:
                self.logger.info(f"🖼️ {result.test_name.replace('_', ' ').title()}:")
                self.logger.info(f"   Steady State: {result.steady_state_avg_ms:.1f}ms")
                self.logger.info(
                    f"   Improvement: {result.improvement_factor:.1f}x after warmup"
                )

        rapid_results = [r for r in self.results if "rapid_fire" in r.test_name]
        if rapid_results:
            rapid = rapid_results[0]
            throughput = 1000 / rapid.steady_state_avg_ms  # widgets per second
            self.logger.info(f"⚡ Rapid Fire Performance:")
            self.logger.info(f"   Maximum Throughput: {throughput:.1f} widgets/second")
            self.logger.info(
                f"   Consistent Speed: {rapid.steady_state_avg_ms:.1f}ms ± {rapid.steady_state_std_ms:.1f}ms"
            )

        self.logger.info("\n" + "🚀" * 40)


def main():
    """Main execution function."""
    speed_test = MaximumSpeedTest()
    speed_test.run_all_speed_tests()
    return 0


if __name__ == "__main__":
    sys.exit(main())
