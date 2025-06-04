#!/usr/bin/env python3
"""
Pre-initialization Validation Test for Browse Tab v2

This test validates that the startup pre-initialization system is working
correctly and achieving the expected performance improvements.

Expected Results After Pre-initialization:
- Widget Creation: Consistent ~17ms (not 118ms first-run)
- Viewer Initialization: Consistent ~33ms (not 473ms first-run)
- Animation System: Pre-initialized and ready
- No first-run performance penalties
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
        get_preinitialization_results,
        validate_preinitialization_effectiveness,
    )
    from browse_tab.components.thumbnail_card import ThumbnailCard
    from browse_tab.components.sequence_viewer import SequenceViewer
    from browse_tab.core.interfaces import SequenceModel, BrowseTabConfig
    from browse_tab.services.cache_service import CacheService

    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Browse tab v2 components not available: {e}")
    COMPONENTS_AVAILABLE = False


@dataclass
class ValidationResult:
    """Container for validation test results."""

    test_name: str
    expected_max_ms: float
    actual_ms: float
    passed: bool
    improvement_achieved: bool
    details: Dict[str, Any]


class PreinitializationValidationTest:
    """Validation test for pre-initialization effectiveness."""

    def __init__(self):
        self.timer = QElapsedTimer()
        self.results: List[ValidationResult] = []
        self.app = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_test_environment(self):
        """Setup test environment with pre-initialization."""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        self.logger.info("Test environment setup complete")

    def run_preinitialization(self) -> bool:
        """Run the pre-initialization system."""
        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping pre-initialization")
            return False

        self.logger.info("=== RUNNING PRE-INITIALIZATION ===")

        # Run pre-initialization
        results = initialize_browse_tab_performance_systems()

        # Log results
        if results["overall_success"]:
            self.logger.info(
                f"✅ Pre-initialization successful in {results['overall_duration_ms']:.1f}ms"
            )
            for system_name, system_result in results["systems"].items():
                status = "✅" if system_result["success"] else "❌"
                self.logger.info(
                    f"  {status} {system_name}: {system_result['duration_ms']:.1f}ms"
                )
        else:
            self.logger.warning(f"⚠️ Pre-initialization partially failed")

        return results["overall_success"]

    def validate_system_states(self):
        """Validate that systems are properly pre-initialized."""
        self.logger.info("=== VALIDATING SYSTEM STATES ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping validation")
            return

        validation_results = validate_preinitialization_effectiveness()

        for system, ready in validation_results.items():
            status = "✅" if ready else "❌"
            self.logger.info(
                f"  {status} {system}: {'Ready' if ready else 'Not Ready'}"
            )

    def test_widget_creation_performance(self):
        """Test that widget creation achieves expected performance."""
        self.logger.info("=== TESTING WIDGET CREATION PERFORMANCE ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping widget tests")
            return

        # Create test sequence
        sequence = SequenceModel(
            id="validation_test_widget",
            name="Validation Test Widget",
            thumbnails=["validation_test.png"],
            difficulty=3,
            length=5,
            author="Validation Test",
            tags=["validation"],
            is_favorite=False,
            metadata={},
        )

        config = BrowseTabConfig()

        # Test multiple widget creations to ensure consistency
        creation_times = []

        for i in range(5):
            self.timer.start()
            try:
                widget = ThumbnailCard(sequence, config)
                widget.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                # Clean up
                widget.deleteLater()
                QApplication.processEvents()

                creation_times.append(duration_ms)
                self.logger.info(f"  Widget creation {i+1}: {duration_ms:.1f}ms")

            except Exception as e:
                self.logger.error(f"Widget creation test {i+1} failed: {e}")

        if creation_times:
            avg_time = sum(creation_times) / len(creation_times)
            max_time = max(creation_times)
            min_time = min(creation_times)

            # Expected: consistent ~17ms (not 118ms first-run)
            expected_max = 50.0  # Allow some margin
            passed = max_time <= expected_max
            improvement_achieved = max_time < 100  # Much better than 118ms

            result = ValidationResult(
                test_name="widget_creation_consistency",
                expected_max_ms=expected_max,
                actual_ms=avg_time,
                passed=passed,
                improvement_achieved=improvement_achieved,
                details={
                    "average_ms": avg_time,
                    "max_ms": max_time,
                    "min_ms": min_time,
                    "samples": len(creation_times),
                    "all_times": creation_times,
                },
            )

            self.results.append(result)

            status = "✅ PASS" if passed else "❌ FAIL"
            improvement_status = (
                "🚀 IMPROVED" if improvement_achieved else "⚠️ NO IMPROVEMENT"
            )

            self.logger.info(
                f"{status} Widget creation: avg={avg_time:.1f}ms, max={max_time:.1f}ms "
                f"(target: <{expected_max}ms)"
            )
            self.logger.info(f"{improvement_status} vs baseline 118ms first-run")

    def test_viewer_initialization_performance(self):
        """Test that viewer initialization achieves expected performance."""
        self.logger.info("=== TESTING VIEWER INITIALIZATION PERFORMANCE ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping viewer tests")
            return

        config = BrowseTabConfig()

        # Test multiple viewer initializations
        init_times = []

        for i in range(3):
            self.timer.start()
            try:
                viewer = SequenceViewer(config)
                viewer.show()
                QApplication.processEvents()
                duration_ms = self.timer.elapsed()

                # Clean up
                viewer.deleteLater()
                QApplication.processEvents()

                init_times.append(duration_ms)
                self.logger.info(f"  Viewer initialization {i+1}: {duration_ms:.1f}ms")

            except Exception as e:
                self.logger.error(f"Viewer initialization test {i+1} failed: {e}")

        if init_times:
            avg_time = sum(init_times) / len(init_times)
            max_time = max(init_times)
            min_time = min(init_times)

            # Expected: consistent ~33ms (not 473ms first-run)
            expected_max = 100.0  # Allow some margin
            passed = max_time <= expected_max
            improvement_achieved = max_time < 400  # Much better than 473ms

            result = ValidationResult(
                test_name="viewer_initialization_consistency",
                expected_max_ms=expected_max,
                actual_ms=avg_time,
                passed=passed,
                improvement_achieved=improvement_achieved,
                details={
                    "average_ms": avg_time,
                    "max_ms": max_time,
                    "min_ms": min_time,
                    "samples": len(init_times),
                    "all_times": init_times,
                },
            )

            self.results.append(result)

            status = "✅ PASS" if passed else "❌ FAIL"
            improvement_status = (
                "🚀 IMPROVED" if improvement_achieved else "⚠️ NO IMPROVEMENT"
            )

            self.logger.info(
                f"{status} Viewer initialization: avg={avg_time:.1f}ms, max={max_time:.1f}ms "
                f"(target: <{expected_max}ms)"
            )
            self.logger.info(f"{improvement_status} vs baseline 473ms first-run")

    def run_validation_tests(self):
        """Run all validation tests."""
        self.logger.info("🔍 Starting Pre-initialization Validation Tests...")

        self.setup_test_environment()

        # Run pre-initialization
        preinitialization_success = self.run_preinitialization()

        # Validate system states
        self.validate_system_states()

        # Run performance tests
        self.test_widget_creation_performance()
        self.test_viewer_initialization_performance()

        # Generate validation report
        self.generate_validation_report(preinitialization_success)

    def generate_validation_report(self, preinitialization_success: bool):
        """Generate comprehensive validation report."""
        self.logger.info("\n" + "🔍" * 60)
        self.logger.info("PRE-INITIALIZATION VALIDATION REPORT")
        self.logger.info("🔍" * 60)

        # Pre-initialization status
        preinit_status = "✅ SUCCESS" if preinitialization_success else "❌ FAILED"
        self.logger.info(f"Pre-initialization Status: {preinit_status}")

        if not self.results:
            self.logger.warning("No validation test results available")
            return

        # Test results summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        improved_tests = sum(1 for r in self.results if r.improvement_achieved)

        self.logger.info(f"\nValidation Tests: {passed_tests}/{total_tests} passed")
        self.logger.info(
            f"Performance Improvements: {improved_tests}/{total_tests} achieved"
        )

        # Detailed results
        self.logger.info("\nDETAILED RESULTS:")
        self.logger.info("-" * 50)

        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            improvement = (
                "🚀 IMPROVED" if result.improvement_achieved else "⚠️ NO IMPROVEMENT"
            )

            self.logger.info(f"{status} {result.test_name}:")
            self.logger.info(
                f"  Performance: {result.actual_ms:.1f}ms (target: <{result.expected_max_ms}ms)"
            )
            self.logger.info(f"  Status: {improvement}")

            if "all_times" in result.details:
                times = result.details["all_times"]
                self.logger.info(
                    f"  Consistency: {min(times):.1f}ms - {max(times):.1f}ms"
                )

        # Overall assessment
        self.logger.info("\nOVERALL ASSESSMENT:")
        self.logger.info("-" * 30)

        if (
            preinitialization_success
            and passed_tests == total_tests
            and improved_tests == total_tests
        ):
            self.logger.info("🎉 EXCELLENT: Pre-initialization working perfectly!")
            self.logger.info(
                "   All performance targets achieved with significant improvements"
            )
        elif preinitialization_success and passed_tests == total_tests:
            self.logger.info("✅ GOOD: Pre-initialization working well")
            self.logger.info("   All performance targets met")
        elif preinitialization_success:
            self.logger.info("⚠️ PARTIAL: Pre-initialization partially effective")
            self.logger.info("   Some performance improvements achieved")
        else:
            self.logger.info("❌ FAILED: Pre-initialization not working")
            self.logger.info("   Performance improvements not achieved")

        self.logger.info("\n" + "🔍" * 60)


def main():
    """Main execution function."""
    validation_test = PreinitializationValidationTest()
    validation_test.run_validation_tests()
    return 0


if __name__ == "__main__":
    sys.exit(main())
