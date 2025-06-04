#!/usr/bin/env python3
"""
Data Pre-loading Test for Browse Tab v2

This test validates that the data pre-loading system is working correctly
and achieving the expected performance improvements for browse tab initialization.

Expected Results:
- Data pre-loading completes during splash screen phase (200-500ms)
- Browse tab displays immediately when accessed (<50ms)
- Navigation sidebar is pre-populated with sections
- Thumbnail grid shows content without loading delays
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
    from browse_tab.startup.data_preloader import (
        preload_browse_tab_data,
        get_preloaded_data,
        is_preloading_completed,
    )
    from browse_tab.components.browse_tab_view import BrowseTabView
    from browse_tab.components.modern_navigation_sidebar import ModernNavigationSidebar
    from browse_tab.viewmodels.browse_tab_viewmodel import BrowseTabViewModel
    from browse_tab.core.interfaces import BrowseTabConfig

    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Browse tab v2 components not available: {e}")
    COMPONENTS_AVAILABLE = False


@dataclass
class PreloadingTestResult:
    """Container for pre-loading test results."""

    test_name: str
    preloading_duration_ms: float
    component_creation_ms: float
    data_availability: bool
    immediate_display: bool
    target_met: bool
    details: Dict[str, Any]


class DataPreloadingTest:
    """Test suite for data pre-loading functionality."""

    def __init__(self):
        self.timer = QElapsedTimer()
        self.results: List[PreloadingTestResult] = []
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

        self.logger.info("Data pre-loading test environment setup complete")

    def test_data_preloading_performance(self):
        """Test data pre-loading performance and timing."""
        self.logger.info("=== TESTING DATA PRE-LOADING PERFORMANCE ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping pre-loading tests")
            return

        # Test data pre-loading timing
        self.timer.start()

        try:
            import asyncio

            # Create progress tracking
            progress_updates = []

            def progress_callback(message: str, progress_percent: int):
                progress_updates.append((message, progress_percent, time.time()))
                self.logger.info(f"Progress: {message} ({progress_percent}%)")

            # Run data pre-loading
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                preloading_results = loop.run_until_complete(
                    preload_browse_tab_data(progress_callback)
                )

                preloading_duration = self.timer.elapsed()

                # Validate results
                success = preloading_results.get("overall_success", False)
                total_sequences = preloading_results.get("total_sequences", 0)
                total_sections = preloading_results.get("total_sections", 0)

                result = PreloadingTestResult(
                    test_name="data_preloading_performance",
                    preloading_duration_ms=preloading_duration,
                    component_creation_ms=0,  # Not applicable for this test
                    data_availability=success and total_sequences > 0,
                    immediate_display=True,  # Will test in component tests
                    target_met=preloading_duration <= 500,  # 500ms target
                    details={
                        "total_sequences": total_sequences,
                        "total_sections": total_sections,
                        "progress_updates": len(progress_updates),
                        "preloading_results": preloading_results,
                    },
                )

                self.results.append(result)

                status = "✅ PASS" if result.target_met else "❌ FAIL"
                self.logger.info(
                    f"{status} Data pre-loading: {preloading_duration:.1f}ms "
                    f"(target: 500ms, sequences: {total_sequences})"
                )

            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"Data pre-loading test failed: {e}")

    def test_navigation_sidebar_preloading(self):
        """Test navigation sidebar with pre-loaded data."""
        self.logger.info("=== TESTING NAVIGATION SIDEBAR PRE-LOADING ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning("Components not available, skipping navigation tests")
            return

        # Ensure data is pre-loaded
        if not is_preloading_completed():
            self.logger.warning("Data not pre-loaded, skipping navigation test")
            return

        # Test navigation sidebar creation with pre-loaded data
        self.timer.start()

        try:
            config = BrowseTabConfig()
            sidebar = ModernNavigationSidebar(config)
            sidebar.show()
            QApplication.processEvents()

            creation_duration = self.timer.elapsed()

            # Check if sidebar has sections
            has_sections = len(sidebar.sections) > 0
            has_buttons = len(sidebar.buttons) > 0

            result = PreloadingTestResult(
                test_name="navigation_sidebar_preloading",
                preloading_duration_ms=0,  # Already done
                component_creation_ms=creation_duration,
                data_availability=has_sections,
                immediate_display=has_buttons,
                target_met=creation_duration <= 50 and has_sections,  # 50ms target
                details={
                    "sections_count": len(sidebar.sections),
                    "buttons_count": len(sidebar.buttons),
                    "sections": sidebar.sections[:5],  # First 5 sections for logging
                },
            )

            self.results.append(result)

            status = "✅ PASS" if result.target_met else "❌ FAIL"
            self.logger.info(
                f"{status} Navigation sidebar: {creation_duration:.1f}ms "
                f"(target: 50ms, sections: {len(sidebar.sections)})"
            )

            # Clean up
            sidebar.deleteLater()
            QApplication.processEvents()

        except Exception as e:
            self.logger.error(f"Navigation sidebar test failed: {e}")

    def test_browse_tab_view_preloading(self):
        """Test browse tab view with pre-loaded data."""
        self.logger.info("=== TESTING BROWSE TAB VIEW PRE-LOADING ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning(
                "Components not available, skipping browse tab view tests"
            )
            return

        # Ensure data is pre-loaded
        if not is_preloading_completed():
            self.logger.warning("Data not pre-loaded, skipping browse tab view test")
            return

        # Test browse tab view creation with pre-loaded data
        self.timer.start()

        try:
            config = BrowseTabConfig()
            viewmodel = BrowseTabViewModel()
            browse_tab = BrowseTabView(viewmodel, config)
            browse_tab.show()
            QApplication.processEvents()

            creation_duration = self.timer.elapsed()

            # Check if browse tab has data
            has_sequences = len(browse_tab._sequences) > 0
            has_navigation = (
                hasattr(browse_tab, "navigation_sidebar")
                and len(browse_tab.navigation_sidebar.sections) > 0
            )

            result = PreloadingTestResult(
                test_name="browse_tab_view_preloading",
                preloading_duration_ms=0,  # Already done
                component_creation_ms=creation_duration,
                data_availability=has_sequences,
                immediate_display=has_navigation,
                target_met=creation_duration <= 100 and has_sequences,  # 100ms target
                details={
                    "sequences_count": len(browse_tab._sequences),
                    "navigation_sections": (
                        len(browse_tab.navigation_sidebar.sections)
                        if has_navigation
                        else 0
                    ),
                    "has_thumbnail_grid": hasattr(browse_tab, "thumbnail_grid"),
                },
            )

            self.results.append(result)

            status = "✅ PASS" if result.target_met else "❌ FAIL"
            self.logger.info(
                f"{status} Browse tab view: {creation_duration:.1f}ms "
                f"(target: 100ms, sequences: {len(browse_tab._sequences)})"
            )

            # Clean up
            browse_tab.deleteLater()
            QApplication.processEvents()

        except Exception as e:
            self.logger.error(f"Browse tab view test failed: {e}")

    def test_preloaded_data_integrity(self):
        """Test integrity and completeness of pre-loaded data."""
        self.logger.info("=== TESTING PRE-LOADED DATA INTEGRITY ===")

        if not COMPONENTS_AVAILABLE:
            self.logger.warning(
                "Components not available, skipping data integrity tests"
            )
            return

        try:
            preloaded_data = get_preloaded_data()

            if not preloaded_data:
                self.logger.error("No pre-loaded data available")
                return

            sequences = preloaded_data.get("sequences", [])
            navigation_sections = preloaded_data.get("navigation_sections", {})
            thumbnail_cache = preloaded_data.get("thumbnail_cache", {})
            metadata_cache = preloaded_data.get("metadata_cache", {})

            # Validate data structure
            data_valid = (
                isinstance(sequences, list)
                and isinstance(navigation_sections, dict)
                and isinstance(thumbnail_cache, dict)
                and isinstance(metadata_cache, dict)
            )

            # Check data completeness
            has_sequences = len(sequences) > 0
            has_alphabetical_sections = (
                "alphabetical" in navigation_sections
                and len(navigation_sections["alphabetical"]) > 0
            )
            has_metadata = len(metadata_cache) > 0

            result = PreloadingTestResult(
                test_name="preloaded_data_integrity",
                preloading_duration_ms=0,
                component_creation_ms=0,
                data_availability=data_valid and has_sequences,
                immediate_display=has_alphabetical_sections,
                target_met=data_valid and has_sequences and has_alphabetical_sections,
                details={
                    "sequences_count": len(sequences),
                    "navigation_sections_count": sum(
                        len(sections) for sections in navigation_sections.values()
                    ),
                    "thumbnail_cache_count": len(thumbnail_cache),
                    "metadata_cache_count": len(metadata_cache),
                    "sort_criteria": list(navigation_sections.keys()),
                },
            )

            self.results.append(result)

            status = "✅ PASS" if result.target_met else "❌ FAIL"
            self.logger.info(
                f"{status} Data integrity: sequences={len(sequences)}, "
                f"sections={sum(len(sections) for sections in navigation_sections.values())}"
            )

        except Exception as e:
            self.logger.error(f"Data integrity test failed: {e}")

    def run_all_tests(self):
        """Run all data pre-loading tests."""
        self.logger.info("🚀 Starting Data Pre-loading Tests...")

        self.setup_test_environment()

        # Run tests in sequence
        self.test_data_preloading_performance()
        self.test_preloaded_data_integrity()
        self.test_navigation_sidebar_preloading()
        self.test_browse_tab_view_preloading()

        # Generate comprehensive report
        self.generate_preloading_report()

    def generate_preloading_report(self):
        """Generate comprehensive pre-loading test report."""
        self.logger.info("\n" + "🚀" * 60)
        self.logger.info("DATA PRE-LOADING TEST RESULTS")
        self.logger.info("🚀" * 60)

        if not self.results:
            self.logger.warning("No test results available")
            return

        # Overall statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.target_met)
        data_available_tests = sum(1 for r in self.results if r.data_availability)
        immediate_display_tests = sum(1 for r in self.results if r.immediate_display)

        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Data Available: {data_available_tests}")
        self.logger.info(f"Immediate Display: {immediate_display_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # Detailed results
        self.logger.info("\nDETAILED RESULTS:")
        self.logger.info("-" * 60)

        for result in self.results:
            status = "✅ PASS" if result.target_met else "❌ FAIL"
            data_status = "📊 DATA OK" if result.data_availability else "❌ NO DATA"
            display_status = (
                "⚡ IMMEDIATE" if result.immediate_display else "⏳ DELAYED"
            )

            self.logger.info(f"{status} {result.test_name}:")

            if result.preloading_duration_ms > 0:
                self.logger.info(
                    f"  Pre-loading: {result.preloading_duration_ms:.1f}ms"
                )
            if result.component_creation_ms > 0:
                self.logger.info(
                    f"  Component Creation: {result.component_creation_ms:.1f}ms"
                )

            self.logger.info(f"  Status: {data_status} | {display_status}")

            # Show key details
            if "sequences_count" in result.details:
                self.logger.info(f"  Sequences: {result.details['sequences_count']}")
            if "sections_count" in result.details:
                self.logger.info(f"  Sections: {result.details['sections_count']}")

        # Performance summary
        self.logger.info("\nPERFORMANCE SUMMARY:")
        self.logger.info("-" * 30)

        preloading_tests = [r for r in self.results if r.preloading_duration_ms > 0]
        if preloading_tests:
            avg_preloading = sum(
                r.preloading_duration_ms for r in preloading_tests
            ) / len(preloading_tests)
            self.logger.info(f"Average Pre-loading Time: {avg_preloading:.1f}ms")

        component_tests = [r for r in self.results if r.component_creation_ms > 0]
        if component_tests:
            avg_component = sum(r.component_creation_ms for r in component_tests) / len(
                component_tests
            )
            self.logger.info(f"Average Component Creation: {avg_component:.1f}ms")

        # Overall assessment
        self.logger.info("\nOVERALL ASSESSMENT:")
        self.logger.info("-" * 30)

        if passed_tests == total_tests and data_available_tests == total_tests:
            self.logger.info("🎉 EXCELLENT: Data pre-loading system working perfectly!")
            self.logger.info("   All tests passed with immediate data availability")
        elif passed_tests >= total_tests * 0.8:
            self.logger.info("✅ GOOD: Data pre-loading system mostly working")
            self.logger.info("   Most tests passed with good performance")
        else:
            self.logger.info("⚠️ NEEDS IMPROVEMENT: Data pre-loading system has issues")
            self.logger.info("   Some tests failed or performance targets not met")

        self.logger.info("\n" + "🚀" * 60)


def main():
    """Main execution function."""
    test_suite = DataPreloadingTest()
    test_suite.run_all_tests()
    return 0


if __name__ == "__main__":
    sys.exit(main())
