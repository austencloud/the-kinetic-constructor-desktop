"""
Performance Testing Runner for Browse Tab V2

This script runs comprehensive performance tests to identify real-world
performance bottlenecks in the browse tab navigation system.
"""

import sys
import logging
import asyncio
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.browse_tab.testing.performance_test_suite import PerformanceTestSuite

# Configure logging for performance testing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("performance_test_results.log"),
    ],
)

logger = logging.getLogger(__name__)


class PerformanceTestRunner:
    """Main runner for performance tests."""

    def __init__(self):
        self.app = None
        self.browse_tab_view = None
        self.test_suite = None

    def setup_test_environment(self):
        """Setup the test environment with browse tab view."""
        logger.info("Setting up performance test environment...")

        # Create QApplication if not exists
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        # Import and create browse tab view
        try:
            from src.browse_tab.components.browse_tab_view import BrowseTabView
            from src.browse_tab.viewmodels.browse_tab_viewmodel import (
                BrowseTabViewModel,
            )
            from src.settings_manager.global_settings.app_context import AppContext

            # Initialize app context for testing
            AppContext.initialize_for_testing()

            # Create viewmodel and view
            viewmodel = BrowseTabViewModel()
            self.browse_tab_view = BrowseTabView(viewmodel)

            # Load test data
            asyncio.run(self._load_test_data())

            logger.info("Test environment setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False

    async def _load_test_data(self):
        """Load test data for performance testing."""
        try:
            # Load sequences for testing
            if hasattr(self.browse_tab_view, "viewmodel"):
                await self.browse_tab_view.viewmodel.load_sequences()

            # Wait for UI to stabilize
            QTimer.singleShot(1000, lambda: None)

        except Exception as e:
            logger.error(f"Failed to load test data: {e}")

    def run_performance_tests(self):
        """Run comprehensive performance tests."""
        if not self.browse_tab_view:
            logger.error("Browse tab view not initialized")
            return False

        logger.info("Starting comprehensive performance tests...")

        # Create test suite
        self.test_suite = PerformanceTestSuite(self.browse_tab_view)

        # Connect signals for test results
        self.test_suite.test_completed.connect(self._on_test_completed)
        self.test_suite.test_failed.connect(self._on_test_failed)

        # Run tests
        try:
            self.test_suite.run_comprehensive_tests()
            return True
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            return False

    def _on_test_completed(self, test_name: str, results: dict):
        """Handle test completion."""
        logger.info(f"Test completed: {test_name}")

        # Log detailed results
        if results.get("passed"):
            logger.info(f"✅ {test_name}: PASSED")
        else:
            logger.warning(f"❌ {test_name}: FAILED")

        # Log specific metrics
        if "average_response_time" in results:
            logger.info(
                f"   Average response: {results['average_response_time']:.1f}ms"
            )
            logger.info(f"   Target: {results.get('target', 'N/A')}ms")

        if "frame_drops" in results:
            logger.info(f"   Frame drops: {results['frame_drops']}")

    def _on_test_failed(self, test_name: str, error_message: str):
        """Handle test failure."""
        logger.error(f"Test failed: {test_name} - {error_message}")

    def generate_performance_recommendations(self):
        """Generate performance improvement recommendations based on test results."""
        if not self.test_suite or not self.test_suite.test_results:
            logger.warning("No test results available for recommendations")
            return

        logger.info("\n=== PERFORMANCE RECOMMENDATIONS ===")

        results = self.test_suite.test_results

        # Navigation performance recommendations
        if "navigation_section_jumping" in results:
            nav_results = results["navigation_section_jumping"]
            if not nav_results.get("passed"):
                avg_time = nav_results.get("average_response_time", 0)
                target = nav_results.get("target", 100)

                logger.info(f"🔧 NAVIGATION OPTIMIZATION NEEDED:")
                logger.info(f"   Current: {avg_time:.1f}ms, Target: {target}ms")
                logger.info(f"   Recommendations:")
                logger.info(f"   - Optimize section filtering with better indexing")
                logger.info(f"   - Reduce scroll animation complexity")
                logger.info(f"   - Pre-compute section positions")
                logger.info(f"   - Implement viewport-based lazy loading")

        # Scroll performance recommendations
        if "sidebar_scroll_performance" in results:
            scroll_results = results["sidebar_scroll_performance"]
            frame_drops = scroll_results.get("frame_drops", 0)

            if frame_drops > 0:
                logger.info(f"🔧 SCROLL OPTIMIZATION NEEDED:")
                logger.info(f"   Frame drops: {frame_drops}")
                logger.info(f"   Recommendations:")
                logger.info(f"   - Optimize Qt widget rendering")
                logger.info(f"   - Reduce glassmorphism complexity")
                logger.info(f"   - Implement scroll event debouncing")
                logger.info(f"   - Use hardware acceleration")

        # Thumbnail performance recommendations
        if "thumbnail_click_pipeline" in results:
            thumb_results = results["thumbnail_click_pipeline"]
            if not thumb_results.get("passed"):
                avg_time = thumb_results.get("average_response_time", 0)
                target = thumb_results.get("target", 200)

                logger.info(f"🔧 THUMBNAIL OPTIMIZATION NEEDED:")
                logger.info(f"   Current: {avg_time:.1f}ms, Target: {target}ms")
                logger.info(f"   Recommendations:")
                logger.info(f"   - Optimize image loading pipeline")
                logger.info(f"   - Pre-load sequence viewer components")
                logger.info(f"   - Reduce animation initialization time")
                logger.info(f"   - Implement progressive image loading")

        # Memory recommendations
        if "memory_usage_stability" in results:
            mem_results = results["memory_usage_stability"]
            if not mem_results.get("passed"):
                increase = mem_results.get("memory_increase_percent", 0)

                logger.info(f"🔧 MEMORY OPTIMIZATION NEEDED:")
                logger.info(f"   Memory increase: {increase:.1f}%")
                logger.info(f"   Recommendations:")
                logger.info(f"   - Implement proper widget cleanup")
                logger.info(f"   - Optimize image caching strategy")
                logger.info(f"   - Fix potential memory leaks")
                logger.info(f"   - Use weak references where appropriate")

        logger.info("=== END RECOMMENDATIONS ===\n")


def main():
    """Main entry point for performance testing."""
    logger.info("Starting Browse Tab V2 Performance Testing Suite")

    runner = PerformanceTestRunner()

    # Setup test environment
    if not runner.setup_test_environment():
        logger.error("Failed to setup test environment")
        return 1

    # Run performance tests
    if not runner.run_performance_tests():
        logger.error("Performance tests failed")
        return 1

    # Generate recommendations
    runner.generate_performance_recommendations()

    logger.info("Performance testing completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
