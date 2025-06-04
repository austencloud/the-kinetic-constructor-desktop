#!/usr/bin/env python3
"""
Integrated Performance Test for Browse Tab v2 Pre-initialization

This test runs pre-initialization and performance testing in the same process
to accurately measure the effectiveness of the pre-warming system.
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QElapsedTimer

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from browse_tab.startup.performance_preinitialization import (
        initialize_browse_tab_performance_systems,
    )
    from browse_tab.components.thumbnail_card import ThumbnailCard
    from browse_tab.components.sequence_viewer import SequenceViewer
    from browse_tab.core.interfaces import SequenceModel, BrowseTabConfig

    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Browse tab v2 components not available: {e}")
    COMPONENTS_AVAILABLE = False


@dataclass
class IntegratedTestResult:
    """Container for integrated test results."""

    test_name: str
    before_preinitialization_ms: float
    after_preinitialization_ms: float
    improvement_factor: float
    target_ms: float
    target_achieved: bool
    significant_improvement: bool


class IntegratedPerformanceTest:
    """Integrated performance test with pre-initialization."""

    def __init__(self):
        self.timer = QElapsedTimer()
        self.results: List[IntegratedTestResult] = []
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

        self.logger.info("Integrated test environment setup complete")

    def create_test_sequence(self, name: str) -> SequenceModel:
        """Create a test sequence."""
        return SequenceModel(
            id=f"integrated_test_{name}",
            name=f"Integrated Test {name}",
            thumbnails=[f"integrated_test_{name}.png"],
            difficulty=3,
            length=5,
            author="Integrated Test",
            tags=["integrated", "test"],
            is_favorite=False,
            metadata={},
        )

    def test_widget_creation_before_and_after(self):
        """Test widget creation performance before and after pre-initialization."""
        self.logger.info(
            "=== TESTING WIDGET CREATION: BEFORE vs AFTER PRE-INITIALIZATION ==="
        )

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping widget tests")
            return

        sequence = self.create_test_sequence("widget")
        config = BrowseTabConfig()

        # Test BEFORE pre-initialization (first-run penalty expected)
        self.logger.info("Testing widget creation BEFORE pre-initialization...")
        before_times = []

        for i in range(3):
            self.timer.start()
            try:
                widget = ThumbnailCard(sequence, config)
                widget.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                widget.deleteLater()
                QApplication.processEvents()

                before_times.append(duration_ms)
                self.logger.info(f"  Before pre-init {i+1}: {duration_ms:.1f}ms")

            except Exception as e:
                self.logger.error(f"Widget creation before test {i+1} failed: {e}")

        # Run pre-initialization
        self.logger.info("Running pre-initialization...")
        preinitialization_results = initialize_browse_tab_performance_systems()

        if preinitialization_results["overall_success"]:
            self.logger.info(
                f"✅ Pre-initialization successful in {preinitialization_results['overall_duration_ms']:.1f}ms"
            )
        else:
            self.logger.warning("⚠️ Pre-initialization partially failed")

        # Test AFTER pre-initialization (should be faster)
        self.logger.info("Testing widget creation AFTER pre-initialization...")
        after_times = []

        for i in range(5):
            self.timer.start()
            try:
                widget = ThumbnailCard(sequence, config)
                widget.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                widget.deleteLater()
                QApplication.processEvents()

                after_times.append(duration_ms)
                self.logger.info(f"  After pre-init {i+1}: {duration_ms:.1f}ms")

            except Exception as e:
                self.logger.error(f"Widget creation after test {i+1} failed: {e}")

        # Analyze results
        if before_times and after_times:
            before_avg = sum(before_times) / len(before_times)
            after_avg = sum(after_times) / len(after_times)
            improvement_factor = before_avg / after_avg if after_avg > 0 else 1.0

            result = IntegratedTestResult(
                test_name="widget_creation_integrated",
                before_preinitialization_ms=before_avg,
                after_preinitialization_ms=after_avg,
                improvement_factor=improvement_factor,
                target_ms=50.0,
                target_achieved=after_avg <= 50.0,
                significant_improvement=improvement_factor >= 2.0,
            )

            self.results.append(result)

            self.logger.info(f"Widget Creation Results:")
            self.logger.info(f"  Before: {before_avg:.1f}ms")
            self.logger.info(f"  After: {after_avg:.1f}ms")
            self.logger.info(f"  Improvement: {improvement_factor:.1f}x")

    def test_viewer_initialization_before_and_after(self):
        """Test viewer initialization performance before and after pre-initialization."""
        self.logger.info(
            "=== TESTING VIEWER INITIALIZATION: BEFORE vs AFTER PRE-INITIALIZATION ==="
        )

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping viewer tests")
            return

        config = BrowseTabConfig()

        # Test BEFORE pre-initialization (first-run penalty expected)
        self.logger.info("Testing viewer initialization BEFORE pre-initialization...")
        before_times = []

        for i in range(2):
            self.timer.start()
            try:
                viewer = SequenceViewer(config)
                viewer.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                viewer.deleteLater()
                QApplication.processEvents()

                before_times.append(duration_ms)
                self.logger.info(f"  Before pre-init {i+1}: {duration_ms:.1f}ms")

            except Exception as e:
                self.logger.error(
                    f"Viewer initialization before test {i+1} failed: {e}"
                )

        # Pre-initialization should already be done from widget test
        # Test AFTER pre-initialization (should be faster)
        self.logger.info("Testing viewer initialization AFTER pre-initialization...")
        after_times = []

        for i in range(3):
            self.timer.start()
            try:
                viewer = SequenceViewer(config)
                viewer.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                viewer.deleteLater()
                QApplication.processEvents()

                after_times.append(duration_ms)
                self.logger.info(f"  After pre-init {i+1}: {duration_ms:.1f}ms")

            except Exception as e:
                self.logger.error(f"Viewer initialization after test {i+1} failed: {e}")

        # Analyze results
        if before_times and after_times:
            before_avg = sum(before_times) / len(before_times)
            after_avg = sum(after_times) / len(after_times)
            improvement_factor = before_avg / after_avg if after_avg > 0 else 1.0

            result = IntegratedTestResult(
                test_name="viewer_initialization_integrated",
                before_preinitialization_ms=before_avg,
                after_preinitialization_ms=after_avg,
                improvement_factor=improvement_factor,
                target_ms=100.0,
                target_achieved=after_avg <= 100.0,
                significant_improvement=improvement_factor >= 5.0,
            )

            self.results.append(result)

            self.logger.info(f"Viewer Initialization Results:")
            self.logger.info(f"  Before: {before_avg:.1f}ms")
            self.logger.info(f"  After: {after_avg:.1f}ms")
            self.logger.info(f"  Improvement: {improvement_factor:.1f}x")

    def run_integrated_tests(self):
        """Run all integrated performance tests."""
        self.logger.info(
            "🔄 Starting Integrated Performance Tests (Before/After Pre-initialization)..."
        )

        self.setup_test_environment()

        # Run tests that include pre-initialization
        self.test_widget_creation_before_and_after()
        self.test_viewer_initialization_before_and_after()

        # Generate comprehensive report
        self.generate_integrated_report()

    def generate_integrated_report(self):
        """Generate comprehensive integrated test report."""
        self.logger.info("\n" + "🔄" * 60)
        self.logger.info("INTEGRATED PERFORMANCE TEST RESULTS")
        self.logger.info("🔄" * 60)

        if not self.results:
            self.logger.warning("No integrated test results available")
            return

        # Overall statistics
        total_tests = len(self.results)
        target_achieved_count = sum(1 for r in self.results if r.target_achieved)
        significant_improvement_count = sum(
            1 for r in self.results if r.significant_improvement
        )

        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Targets Achieved: {target_achieved_count}/{total_tests}")
        self.logger.info(
            f"Significant Improvements: {significant_improvement_count}/{total_tests}"
        )

        # Detailed results
        self.logger.info("\nDETAILED BEFORE/AFTER ANALYSIS:")
        self.logger.info("-" * 60)

        for result in self.results:
            target_status = (
                "✅ TARGET MET" if result.target_achieved else "❌ TARGET MISSED"
            )
            improvement_status = (
                "🚀 SIGNIFICANT" if result.significant_improvement else "⚠️ MINIMAL"
            )

            self.logger.info(f"{result.test_name.upper()}:")
            self.logger.info(
                f"  Before Pre-init: {result.before_preinitialization_ms:.1f}ms"
            )
            self.logger.info(
                f"  After Pre-init:  {result.after_preinitialization_ms:.1f}ms"
            )
            self.logger.info(
                f"  Improvement:     {result.improvement_factor:.1f}x faster"
            )
            self.logger.info(
                f"  Target:          {result.target_ms:.1f}ms ({target_status})"
            )
            self.logger.info(f"  Assessment:      {improvement_status}")
            self.logger.info("")

        # Performance insights
        self.logger.info("🎯 INTEGRATED TEST INSIGHTS:")
        self.logger.info("-" * 40)

        if (
            target_achieved_count == total_tests
            and significant_improvement_count == total_tests
        ):
            self.logger.info("🎉 EXCELLENT: Pre-initialization is highly effective!")
            self.logger.info("   All targets achieved with significant improvements")
        elif target_achieved_count == total_tests:
            self.logger.info("✅ GOOD: Pre-initialization is effective")
            self.logger.info("   All performance targets achieved")
        elif significant_improvement_count > 0:
            self.logger.info("⚠️ PARTIAL: Pre-initialization shows some benefits")
            self.logger.info(
                "   Some improvements achieved, but targets may not be met"
            )
        else:
            self.logger.info(
                "❌ INEFFECTIVE: Pre-initialization not providing expected benefits"
            )
            self.logger.info("   Consider alternative optimization strategies")

        # Recommendations
        self.logger.info("\n🔧 OPTIMIZATION RECOMMENDATIONS:")
        self.logger.info("-" * 40)

        widget_results = [r for r in self.results if "widget" in r.test_name]
        if widget_results:
            widget_result = widget_results[0]
            if not widget_result.target_achieved:
                self.logger.info(f"🔧 Widget Creation Optimization:")
                self.logger.info(
                    f"   Current: {widget_result.after_preinitialization_ms:.1f}ms, Target: {widget_result.target_ms:.1f}ms"
                )
                self.logger.info(f"   Recommendations:")
                self.logger.info(f"   - Increase pre-warming iterations")
                self.logger.info(f"   - Pre-initialize more Qt subsystems")
                self.logger.info(f"   - Optimize ModernThumbnailCard initialization")

        viewer_results = [r for r in self.results if "viewer" in r.test_name]
        if viewer_results:
            viewer_result = viewer_results[0]
            if not viewer_result.target_achieved:
                self.logger.info(f"🔧 Viewer Initialization Optimization:")
                self.logger.info(
                    f"   Current: {viewer_result.after_preinitialization_ms:.1f}ms, Target: {viewer_result.target_ms:.1f}ms"
                )
                self.logger.info(f"   Recommendations:")
                self.logger.info(f"   - Pre-create more animation manager instances")
                self.logger.info(
                    f"   - Warm up animation property system more thoroughly"
                )
                self.logger.info(f"   - Consider animation system singleton pattern")

        self.logger.info("\n" + "🔄" * 60)


def main():
    """Main execution function."""
    integrated_test = IntegratedPerformanceTest()
    integrated_test.run_integrated_tests()
    return 0


if __name__ == "__main__":
    sys.exit(main())
