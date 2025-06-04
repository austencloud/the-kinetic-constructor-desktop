#!/usr/bin/env python3
"""
Comprehensive Automated Stress Test Suite for Browse Tab v2 Performance Optimization

This suite systematically identifies and fixes remaining performance bottlenecks:
- Widget creation speed (target: <50ms, currently 60-130ms)
- Navigation responsiveness (target: <100ms, currently 118-119ms)
- Thumbnail interaction speed (target: <200ms, currently 491ms)
- Scroll performance regression testing (maintain 0ms frame drops)

Usage:
    python stress_test_suite.py --all
    python stress_test_suite.py --widget-creation
    python stress_test_suite.py --navigation
    python stress_test_suite.py --thumbnails
    python stress_test_suite.py --scroll-regression
    python stress_test_suite.py --memory-stress
    python stress_test_suite.py --multi-action
"""

import sys
import os
import argparse
import json
import time
import psutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PyQt6.QtCore import QTimer, QElapsedTimer, QCoreApplication, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# Import browse tab v2 components
try:
    from browse_tab_v2.components.browse_tab_view import BrowseTabView
    from browse_tab_v2.components.modern_thumbnail_card import ModernThumbnailCard
    from browse_tab_v2.components.modern_sequence_viewer import ModernSequenceViewer
    from browse_tab_v2.components.efficient_virtual_grid import EfficientVirtualGrid
    from browse_tab_v2.services.sequence_service import SequenceService
    from browse_tab_v2.services.cache_service import CacheService
    from browse_tab_v2.services.fast_image_service import FastImageService
    from browse_tab_v2.viewmodels.browse_tab_viewmodel import BrowseTabViewModel
    from browse_tab_v2.core.interfaces import BrowseTabConfig
    from browse_tab_v2.core.state import SequenceModel
except ImportError as e:
    print(f"Failed to import browse tab v2 components: {e}")
    print(
        "Note: This test suite requires running from within the main application context"
    )

    # Create mock classes for testing infrastructure validation
    class MockBrowseTabView:
        pass

    class MockModernThumbnailCard:
        pass

    class MockModernSequenceViewer:
        pass

    class MockEfficientVirtualGrid:
        pass

    class MockSequenceService:
        pass

    class MockCacheService:
        pass

    class MockFastImageService:
        pass

    class MockBrowseTabViewModel:
        pass

    class MockBrowseTabConfig:
        pass

    class MockSequenceModel:
        pass

    BrowseTabView = MockBrowseTabView
    ModernThumbnailCard = MockModernThumbnailCard
    ModernSequenceViewer = MockModernSequenceViewer
    EfficientVirtualGrid = MockEfficientVirtualGrid
    SequenceService = MockSequenceService
    CacheService = MockCacheService
    FastImageService = MockFastImageService
    BrowseTabViewModel = MockBrowseTabViewModel
    BrowseTabConfig = MockBrowseTabConfig
    SequenceModel = MockSequenceModel


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    test_name: str
    timestamp: datetime
    duration_ms: float
    target_ms: float
    passed: bool
    details: Dict[str, Any]
    memory_usage_mb: float
    cpu_percent: float


@dataclass
class TestResults:
    """Container for complete test suite results."""

    suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    metrics: List[PerformanceMetrics]
    summary: Dict[str, Any]


class PerformanceMonitor:
    """Real-time performance monitoring utility."""

    def __init__(self):
        self.process = psutil.Process()
        self.timer = QElapsedTimer()

    @contextmanager
    def measure(self, test_name: str, target_ms: float):
        """Context manager for measuring performance with automatic resource tracking."""
        # Record initial state
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = self.process.cpu_percent()

        # Start timing
        self.timer.start()

        try:
            yield self
        finally:
            # Record final measurements
            duration_ms = self.timer.elapsed()
            final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = self.process.cpu_percent()

            # Create metrics object
            metrics = PerformanceMetrics(
                test_name=test_name,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                target_ms=target_ms,
                passed=duration_ms <= target_ms,
                details={
                    "memory_delta_mb": final_memory - initial_memory,
                    "cpu_usage_percent": final_cpu,
                },
                memory_usage_mb=final_memory,
                cpu_percent=final_cpu,
            )

            # Store result
            self.last_metrics = metrics


class StressTestSuite:
    """Main stress test suite coordinator."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)

        self.monitor = PerformanceMonitor()
        self.results: List[PerformanceMetrics] = []
        self.app: Optional[QApplication] = None
        self.browse_tab: Optional[BrowseTabView] = None

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Configure comprehensive logging for test execution."""
        log_file = (
            self.output_dir
            / f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("Stress test suite initialized")

    def setup_test_environment(self):
        """Initialize Qt application and browse tab for testing."""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)

        # Create browse tab instance with mock config for testing
        try:
            config = BrowseTabConfig()
            viewmodel = BrowseTabViewModel()
            self.browse_tab = BrowseTabView(viewmodel, config)
        except Exception as e:
            self.logger.warning(f"Could not create real BrowseTabView: {e}")
            # Create mock for testing infrastructure
            self.browse_tab = type(
                "MockBrowseTab",
                (),
                {
                    "navigation_sidebar": None,
                    "main_content_area": None,
                    "thumbnail_grid": None,
                    "sequence_viewer": None,
                },
            )()
        self.logger.info("Test environment setup complete")

    def teardown_test_environment(self):
        """Clean up test environment."""
        if self.browse_tab:
            self.browse_tab.deleteLater()
            self.browse_tab = None

        if self.app:
            self.app.quit()
            self.app = None

        self.logger.info("Test environment cleaned up")

    def run_all_tests(self) -> TestResults:
        """Execute complete stress test suite."""
        start_time = datetime.now()
        self.logger.info("Starting comprehensive stress test suite")

        try:
            self.setup_test_environment()

            # Execute all test categories
            self.run_widget_creation_tests()
            self.run_navigation_performance_tests()
            self.run_thumbnail_interaction_tests()
            self.run_scroll_regression_tests()
            self.run_memory_stress_tests()
            self.run_multi_action_stress_tests()

        except Exception as e:
            self.logger.error(f"Test suite execution failed: {e}")
            raise
        finally:
            self.teardown_test_environment()

        end_time = datetime.now()

        # Compile results
        results = TestResults(
            suite_name="Browse Tab v2 Performance Stress Test",
            start_time=start_time,
            end_time=end_time,
            total_tests=len(self.results),
            passed_tests=sum(1 for r in self.results if r.passed),
            failed_tests=sum(1 for r in self.results if not r.passed),
            metrics=self.results,
            summary=self.generate_summary(),
        )

        # Save results
        self.save_results(results)
        return results

    def run_widget_creation_tests(self):
        """Test 1: Automated Widget Creation Performance Testing."""
        self.logger.info("=== WIDGET CREATION PERFORMANCE TESTS ===")

        # Test 1.1: Simple sequence widget creation
        self._test_simple_widget_creation()

        # Test 1.2: Complex sequence widget creation
        self._test_complex_widget_creation()

        # Test 1.3: Widget creation with cached vs uncached images
        self._test_cached_vs_uncached_widgets()

        # Test 1.4: Widget creation under memory pressure
        self._test_widget_creation_memory_pressure()

        # Test 1.5: Batch widget creation performance
        self._test_batch_widget_creation()

        # Test 1.6: Progressive creation simulation
        self._test_progressive_widget_creation()

    def _test_simple_widget_creation(self):
        """Test individual widget creation with simple sequences (2-3 beats)."""
        self.logger.info("Testing simple widget creation performance")

        # Generate simple test sequences
        simple_sequences = self._generate_test_sequences(
            count=10, beat_count_range=(2, 3)
        )

        for i, sequence in enumerate(simple_sequences):
            with self.monitor.measure(f"simple_widget_creation_{i}", target_ms=50.0):
                # Create widget with timing
                widget = ModernThumbnailCard(sequence)
                widget.show()

                # Force layout and rendering
                QCoreApplication.processEvents()

                # Clean up
                widget.deleteLater()

            self.results.append(self.monitor.last_metrics)
            self.logger.debug(
                f"Simple widget {i}: {self.monitor.last_metrics.duration_ms:.1f}ms"
            )

    def _test_complex_widget_creation(self):
        """Test individual widget creation with complex sequences (8+ beats)."""
        self.logger.info("Testing complex widget creation performance")

        # Generate complex test sequences
        complex_sequences = self._generate_test_sequences(
            count=10, beat_count_range=(8, 12)
        )

        for i, sequence in enumerate(complex_sequences):
            with self.monitor.measure(f"complex_widget_creation_{i}", target_ms=50.0):
                # Create widget with timing
                widget = ModernThumbnailCard(sequence)
                widget.show()

                # Force layout and rendering
                QCoreApplication.processEvents()

                # Clean up
                widget.deleteLater()

            self.results.append(self.monitor.last_metrics)
            self.logger.debug(
                f"Complex widget {i}: {self.monitor.last_metrics.duration_ms:.1f}ms"
            )

    def _test_cached_vs_uncached_widgets(self):
        """Test widget creation performance with different cache states."""
        self.logger.info("Testing cached vs uncached widget creation")

        # Get cache service
        cache_service = CacheService()
        test_sequences = self._generate_test_sequences(count=5, beat_count_range=(4, 6))

        # Test uncached creation
        cache_service.clear_cache()  # Ensure clean state
        for i, sequence in enumerate(test_sequences):
            with self.monitor.measure(f"uncached_widget_creation_{i}", target_ms=50.0):
                widget = ModernThumbnailCard(sequence)
                widget.show()
                QCoreApplication.processEvents()
                widget.deleteLater()

            self.results.append(self.monitor.last_metrics)

        # Test cached creation (same sequences)
        for i, sequence in enumerate(test_sequences):
            with self.monitor.measure(f"cached_widget_creation_{i}", target_ms=50.0):
                widget = ModernThumbnailCard(sequence)
                widget.show()
                QCoreApplication.processEvents()
                widget.deleteLater()

            self.results.append(self.monitor.last_metrics)

    def _test_widget_creation_memory_pressure(self):
        """Test widget creation under simulated memory pressure."""
        self.logger.info("Testing widget creation under memory pressure")

        # Create memory pressure (500+ dummy objects)
        memory_pressure_objects = []
        for _ in range(500):
            # Create large dummy objects to consume memory
            dummy_data = bytearray(1024 * 1024)  # 1MB each
            memory_pressure_objects.append(dummy_data)

        test_sequences = self._generate_test_sequences(count=5, beat_count_range=(4, 6))

        for i, sequence in enumerate(test_sequences):
            with self.monitor.measure(
                f"memory_pressure_widget_creation_{i}", target_ms=50.0
            ):
                widget = ModernThumbnailCard(sequence)
                widget.show()
                QCoreApplication.processEvents()
                widget.deleteLater()

            self.results.append(self.monitor.last_metrics)

        # Clean up memory pressure
        del memory_pressure_objects

    def _test_batch_widget_creation(self):
        """Test batch widget creation with different batch sizes."""
        self.logger.info("Testing batch widget creation performance")

        test_sequences = self._generate_test_sequences(
            count=20, beat_count_range=(3, 7)
        )
        batch_sizes = [1, 2, 3, 5, 10]

        for batch_size in batch_sizes:
            widgets = []

            with self.monitor.measure(
                f"batch_creation_size_{batch_size}", target_ms=batch_size * 50.0
            ):
                # Create batch of widgets
                for i in range(batch_size):
                    if i < len(test_sequences):
                        widget = ModernThumbnailCard(test_sequences[i])
                        widget.show()
                        widgets.append(widget)

                # Process events for all widgets
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

            # Clean up batch
            for widget in widgets:
                widget.deleteLater()

    def _test_progressive_widget_creation(self):
        """Test progressive widget creation simulation."""
        self.logger.info("Testing progressive widget creation")

        test_sequences = self._generate_test_sequences(
            count=50, beat_count_range=(3, 8)
        )

        # Simulate progressive creation with delays
        widgets = []
        creation_times = []

        for i, sequence in enumerate(test_sequences):
            with self.monitor.measure(f"progressive_widget_{i}", target_ms=50.0):
                widget = ModernThumbnailCard(sequence)
                widget.show()
                widgets.append(widget)

                # Simulate background processing delay
                QTest.qWait(15)  # 15ms delay between widgets
                QCoreApplication.processEvents()

            creation_times.append(self.monitor.last_metrics.duration_ms)
            self.results.append(self.monitor.last_metrics)

            # Log progress every 10 widgets
            if (i + 1) % 10 == 0:
                avg_time = sum(creation_times[-10:]) / 10
                self.logger.info(
                    f"Progressive creation: {i+1}/50 widgets, avg time: {avg_time:.1f}ms"
                )

        # Clean up all widgets
        for widget in widgets:
            widget.deleteLater()

    def run_navigation_performance_tests(self):
        """Test 2: Navigation Click Response Performance Testing."""
        self.logger.info("=== NAVIGATION PERFORMANCE TESTS ===")

        # Test 2.1: Basic section navigation
        self._test_basic_section_navigation()

        # Test 2.2: Rapid-fire navigation stress
        self._test_rapid_fire_navigation()

        # Test 2.3: Navigation during widget creation
        self._test_navigation_during_widget_creation()

        # Test 2.4: Navigation with different sequence counts
        self._test_navigation_sequence_count_variations()

        # Test 2.5: Edge case navigation testing
        self._test_navigation_edge_cases()

    def _test_basic_section_navigation(self):
        """Test basic section button navigation performance."""
        self.logger.info("Testing basic section navigation")

        # Get navigation component
        navigation = self.browse_tab.navigation_sidebar
        sections = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

        for section in sections:
            # Find section button
            section_button = self._find_section_button(navigation, section)
            if not section_button:
                self.logger.warning(f"Section button {section} not found")
                continue

            with self.monitor.measure(f"navigation_section_{section}", target_ms=100.0):
                # Simulate click
                QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)

                # Wait for navigation to complete
                QCoreApplication.processEvents()

                # Verify navigation completed
                self._verify_navigation_completion(section)

            self.results.append(self.monitor.last_metrics)
            self.logger.debug(
                f"Navigation to {section}: {self.monitor.last_metrics.duration_ms:.1f}ms"
            )

    def _test_rapid_fire_navigation(self):
        """Test rapid-fire navigation stress (10 clicks within 2 seconds)."""
        self.logger.info("Testing rapid-fire navigation stress")

        navigation = self.browse_tab.navigation_sidebar
        sections = ["A", "C", "E", "G", "I", "K", "M", "O", "Q", "S"]

        start_time = time.time()

        for i, section in enumerate(sections):
            section_button = self._find_section_button(navigation, section)
            if not section_button:
                continue

            with self.monitor.measure(
                f"rapid_navigation_{i}_{section}", target_ms=100.0
            ):
                QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

            # Ensure we complete within 2 seconds
            elapsed = time.time() - start_time
            if elapsed > 2.0:
                self.logger.warning(
                    f"Rapid-fire navigation exceeded 2 seconds at click {i+1}"
                )
                break

    def _test_navigation_during_widget_creation(self):
        """Test navigation performance during background widget creation."""
        self.logger.info("Testing navigation during widget creation")

        # Start background widget creation
        self._start_background_widget_creation()

        navigation = self.browse_tab.navigation_sidebar
        sections = ["B", "D", "F", "H", "J"]

        for section in sections:
            section_button = self._find_section_button(navigation, section)
            if not section_button:
                continue

            with self.monitor.measure(
                f"navigation_during_creation_{section}", target_ms=100.0
            ):
                QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

        # Stop background widget creation
        self._stop_background_widget_creation()

    def _test_navigation_sequence_count_variations(self):
        """Test navigation with different sequence counts per section."""
        self.logger.info("Testing navigation with varying sequence counts")

        # Test sections with different sequence densities
        test_cases = [
            ("A", "low_density"),  # Typically fewer sequences
            ("M", "medium_density"),  # Medium sequence count
            ("S", "high_density"),  # Typically more sequences
        ]

        navigation = self.browse_tab.navigation_sidebar

        for section, density_type in test_cases:
            section_button = self._find_section_button(navigation, section)
            if not section_button:
                continue

            with self.monitor.measure(
                f"navigation_{density_type}_{section}", target_ms=100.0
            ):
                QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

                # Count sequences in section for analysis
                sequence_count = self._count_sequences_in_section(section)

            # Add sequence count to metrics details
            self.monitor.last_metrics.details["sequence_count"] = sequence_count
            self.results.append(self.monitor.last_metrics)

    def _test_navigation_edge_cases(self):
        """Test navigation edge cases."""
        self.logger.info("Testing navigation edge cases")

        navigation = self.browse_tab.navigation_sidebar

        # Test 1: Navigation to empty section
        empty_sections = self._find_empty_sections()
        for section in empty_sections[:3]:  # Test up to 3 empty sections
            section_button = self._find_section_button(navigation, section)
            if not section_button:
                continue

            with self.monitor.measure(f"navigation_empty_{section}", target_ms=100.0):
                QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

        # Test 2: Navigation during scroll operations
        with self.monitor.measure("navigation_during_scroll", target_ms=100.0):
            # Start scroll operation
            scroll_area = self.browse_tab.main_content_area
            QTest.wheelEvent(
                scroll_area,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                delta=120,
            )  # Scroll down

            # Navigate during scroll
            section_button = self._find_section_button(navigation, "M")
            if section_button:
                QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)

            QCoreApplication.processEvents()

        self.results.append(self.monitor.last_metrics)

    def run_thumbnail_interaction_tests(self):
        """Test 3: Thumbnail Click Response Performance Testing."""
        self.logger.info("=== THUMBNAIL INTERACTION PERFORMANCE TESTS ===")

        # Test 3.1: Basic thumbnail clicks
        self._test_basic_thumbnail_clicks()

        # Test 3.2: Thumbnail clicks with different sequence complexities
        self._test_thumbnail_complexity_variations()

        # Test 3.3: Thumbnail clicks with different cache states
        self._test_thumbnail_cache_variations()

        # Test 3.4: Thumbnail clicks with different viewer states
        self._test_thumbnail_viewer_state_variations()

        # Test 3.5: Sequence viewer performance measurement
        self._test_sequence_viewer_performance()

    def _test_basic_thumbnail_clicks(self):
        """Test basic thumbnail click performance."""
        self.logger.info("Testing basic thumbnail click performance")

        # Get visible thumbnails
        thumbnails = self._get_visible_thumbnails()[:10]  # Test first 10 visible

        for i, thumbnail in enumerate(thumbnails):
            sequence_id = self._get_thumbnail_sequence_id(thumbnail)

            with self.monitor.measure(
                f"thumbnail_click_{i}_{sequence_id}", target_ms=200.0
            ):
                # Click thumbnail
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)

                # Wait for sequence loading and viewer display
                QCoreApplication.processEvents()

                # Verify sequence loaded in viewer
                self._verify_sequence_loaded_in_viewer(sequence_id)

            self.results.append(self.monitor.last_metrics)
            self.logger.debug(
                f"Thumbnail {i} ({sequence_id}): {self.monitor.last_metrics.duration_ms:.1f}ms"
            )

    def _test_thumbnail_complexity_variations(self):
        """Test thumbnail clicks with different sequence complexities."""
        self.logger.info("Testing thumbnail clicks with varying sequence complexity")

        # Categorize thumbnails by sequence complexity
        complexity_categories = {
            "simple": self._find_thumbnails_by_beat_count(2, 4),
            "medium": self._find_thumbnails_by_beat_count(5, 7),
            "complex": self._find_thumbnails_by_beat_count(8, 12),
        }

        for complexity, thumbnails in complexity_categories.items():
            for i, thumbnail in enumerate(thumbnails[:5]):  # Test 5 of each complexity
                sequence_id = self._get_thumbnail_sequence_id(thumbnail)
                beat_count = self._get_sequence_beat_count(sequence_id)

                with self.monitor.measure(
                    f"thumbnail_{complexity}_{i}_{sequence_id}", target_ms=200.0
                ):
                    QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                    QCoreApplication.processEvents()

                # Add beat count to metrics
                self.monitor.last_metrics.details["beat_count"] = beat_count
                self.monitor.last_metrics.details["complexity"] = complexity
                self.results.append(self.monitor.last_metrics)

    def _test_thumbnail_cache_variations(self):
        """Test thumbnail clicks with different image cache states."""
        self.logger.info("Testing thumbnail clicks with cache variations")

        cache_service = CacheService()
        test_thumbnails = self._get_visible_thumbnails()[:6]

        # Test with cold cache
        cache_service.clear_cache()
        for i, thumbnail in enumerate(test_thumbnails[:3]):
            sequence_id = self._get_thumbnail_sequence_id(thumbnail)

            with self.monitor.measure(
                f"thumbnail_cold_cache_{i}_{sequence_id}", target_ms=200.0
            ):
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.monitor.last_metrics.details["cache_state"] = "cold"
            self.results.append(self.monitor.last_metrics)

        # Test with warm cache (same thumbnails)
        for i, thumbnail in enumerate(test_thumbnails[:3]):
            sequence_id = self._get_thumbnail_sequence_id(thumbnail)

            with self.monitor.measure(
                f"thumbnail_warm_cache_{i}_{sequence_id}", target_ms=200.0
            ):
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.monitor.last_metrics.details["cache_state"] = "warm"
            self.results.append(self.monitor.last_metrics)

    def _test_thumbnail_viewer_state_variations(self):
        """Test thumbnail clicks with different viewer states."""
        self.logger.info("Testing thumbnail clicks with viewer state variations")

        test_thumbnails = self._get_visible_thumbnails()[:6]

        # Test with empty viewer
        self._clear_sequence_viewer()
        for i, thumbnail in enumerate(test_thumbnails[:3]):
            sequence_id = self._get_thumbnail_sequence_id(thumbnail)

            with self.monitor.measure(
                f"thumbnail_empty_viewer_{i}_{sequence_id}", target_ms=200.0
            ):
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.monitor.last_metrics.details["viewer_state"] = "empty"
            self.results.append(self.monitor.last_metrics)

        # Test with populated viewer (viewer already has content)
        for i, thumbnail in enumerate(test_thumbnails[3:6]):
            sequence_id = self._get_thumbnail_sequence_id(thumbnail)

            with self.monitor.measure(
                f"thumbnail_populated_viewer_{i}_{sequence_id}", target_ms=200.0
            ):
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                QCoreApplication.processEvents()

            self.monitor.last_metrics.details["viewer_state"] = "populated"
            self.results.append(self.monitor.last_metrics)

    def _test_sequence_viewer_performance(self):
        """Test ModernSequenceViewer initialization and update performance."""
        self.logger.info("Testing sequence viewer performance")

        test_sequences = self._generate_test_sequences(
            count=10, beat_count_range=(3, 8)
        )

        # Test viewer initialization
        with self.monitor.measure("sequence_viewer_initialization", target_ms=100.0):
            viewer = ModernSequenceViewer()
            viewer.show()
            QCoreApplication.processEvents()

        self.results.append(self.monitor.last_metrics)

        # Test viewer updates with different sequences
        for i, sequence in enumerate(test_sequences):
            with self.monitor.measure(f"sequence_viewer_update_{i}", target_ms=100.0):
                viewer.display_sequence(sequence)
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

        # Clean up
        viewer.deleteLater()

    def run_scroll_regression_tests(self):
        """Test 4: Scroll Performance Regression Testing."""
        self.logger.info("=== SCROLL REGRESSION PERFORMANCE TESTS ===")

        # Test 4.1: Continuous scroll simulation
        self._test_continuous_scroll_simulation()

        # Test 4.2: Scroll during widget creation
        self._test_scroll_during_widget_creation()

        # Test 4.3: Scroll during navigation
        self._test_scroll_during_navigation()

        # Test 4.4: Viewport update performance
        self._test_viewport_update_performance()

        # Test 4.5: Frame drop detection
        self._test_frame_drop_detection()

    def _test_continuous_scroll_simulation(self):
        """Test continuous scroll for 30+ seconds."""
        self.logger.info("Testing continuous scroll simulation")

        scroll_area = self.browse_tab.main_content_area
        start_time = time.time()
        scroll_events = 0
        frame_drops = 0

        while time.time() - start_time < 30.0:  # 30 second test
            with self.monitor.measure(
                f"scroll_event_{scroll_events}", target_ms=16.67
            ):  # 60fps target
                # Alternate scroll directions
                delta = 120 if scroll_events % 2 == 0 else -120
                QTest.wheelEvent(
                    scroll_area,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                    delta=delta,
                )
                QCoreApplication.processEvents()

            # Check for frame drops
            if self.monitor.last_metrics.duration_ms > 33.0:  # 30fps minimum
                frame_drops += 1

            self.results.append(self.monitor.last_metrics)
            scroll_events += 1

            # Brief pause between scroll events
            QTest.qWait(50)

        self.logger.info(
            f"Scroll test completed: {scroll_events} events, {frame_drops} frame drops"
        )

    def _test_scroll_during_widget_creation(self):
        """Test scroll performance during background widget creation."""
        self.logger.info("Testing scroll during widget creation")

        # Start background widget creation
        self._start_background_widget_creation()

        scroll_area = self.browse_tab.main_content_area

        for i in range(20):  # 20 scroll events during widget creation
            with self.monitor.measure(f"scroll_during_creation_{i}", target_ms=16.67):
                delta = 120 if i % 2 == 0 else -120
                QTest.wheelEvent(
                    scroll_area,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                    delta=delta,
                )
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)
            QTest.qWait(100)  # 100ms between scrolls

        self._stop_background_widget_creation()

    def _test_scroll_during_navigation(self):
        """Test scroll performance during navigation operations."""
        self.logger.info("Testing scroll during navigation")

        scroll_area = self.browse_tab.main_content_area
        navigation = self.browse_tab.navigation_sidebar

        # Trigger navigation
        section_button = self._find_section_button(navigation, "M")
        if section_button:
            QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)

        # Scroll during navigation processing
        for i in range(10):
            with self.monitor.measure(f"scroll_during_navigation_{i}", target_ms=16.67):
                QTest.wheelEvent(
                    scroll_area,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                    delta=120,
                )
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)
            QTest.qWait(50)

    def _test_viewport_update_performance(self):
        """Test viewport update performance specifically."""
        self.logger.info("Testing viewport update performance")

        virtual_grid = self.browse_tab.thumbnail_grid

        for i in range(50):
            with self.monitor.measure(f"viewport_update_{i}", target_ms=16.67):
                # Trigger viewport update
                virtual_grid._on_viewport_changed()
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

    def _test_frame_drop_detection(self):
        """Test frame drop detection during various operations."""
        self.logger.info("Testing frame drop detection")

        scroll_area = self.browse_tab.main_content_area
        frame_drops = []

        # Rapid scroll events to stress test
        for i in range(100):
            with self.monitor.measure(
                f"frame_drop_test_{i}", target_ms=33.0
            ):  # 30fps minimum
                QTest.wheelEvent(
                    scroll_area,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                    delta=120,
                )
                QCoreApplication.processEvents()

            if self.monitor.last_metrics.duration_ms > 33.0:
                frame_drops.append(i)

            self.results.append(self.monitor.last_metrics)

        self.logger.info(f"Frame drop test: {len(frame_drops)} drops out of 100 events")

    def run_memory_stress_tests(self):
        """Test 5: Memory and Resource Stress Testing."""
        self.logger.info("=== MEMORY STRESS PERFORMANCE TESTS ===")

        # Test 5.1: Low memory conditions
        self._test_low_memory_conditions()

        # Test 5.2: Scale testing with large datasets
        self._test_scale_testing()

        # Test 5.3: Image cache stress
        self._test_image_cache_stress()

        # Test 5.4: Memory leak detection
        self._test_memory_leak_detection()

        # Test 5.5: Resource monitoring
        self._test_resource_monitoring()

    def _test_low_memory_conditions(self):
        """Test performance under low memory conditions."""
        self.logger.info("Testing low memory conditions")

        # Create memory pressure
        memory_hogs = []
        for _ in range(100):
            memory_hogs.append(bytearray(10 * 1024 * 1024))  # 10MB each

        # Test basic operations under memory pressure
        test_operations = [
            ("widget_creation_low_memory", self._create_test_widget),
            ("navigation_low_memory", lambda: self._navigate_to_section("A")),
            ("thumbnail_click_low_memory", self._click_first_thumbnail),
            ("scroll_low_memory", self._perform_scroll_operation),
        ]

        for op_name, operation in test_operations:
            with self.monitor.measure(op_name, target_ms=200.0):
                operation()
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

        # Clean up memory pressure
        del memory_hogs

    def _test_scale_testing(self):
        """Test with large datasets (1000+ sequences)."""
        self.logger.info("Testing scale with large datasets")

        # Generate large dataset
        large_dataset = self._generate_test_sequences(
            count=1000, beat_count_range=(2, 10)
        )

        with self.monitor.measure(
            "large_dataset_load", target_ms=5000.0
        ):  # 5 second target
            # Simulate loading large dataset
            self.browse_tab.sequence_service.load_sequences(large_dataset)
            QCoreApplication.processEvents()

        self.results.append(self.monitor.last_metrics)

        # Test navigation with large dataset
        with self.monitor.measure("large_dataset_navigation", target_ms=200.0):
            self._navigate_to_section("M")
            QCoreApplication.processEvents()

        self.results.append(self.monitor.last_metrics)

    def _test_image_cache_stress(self):
        """Test image cache performance under stress."""
        self.logger.info("Testing image cache stress")

        cache_service = CacheService()

        # Fill cache to capacity
        test_sequences = self._generate_test_sequences(
            count=200, beat_count_range=(3, 8)
        )

        with self.monitor.measure(
            "cache_fill_stress", target_ms=10000.0
        ):  # 10 second target
            for sequence in test_sequences:
                # Force cache population
                cache_service.get_sequence_image(sequence)

        self.results.append(self.monitor.last_metrics)

        # Test cache hit performance
        with self.monitor.measure("cache_hit_performance", target_ms=100.0):
            for sequence in test_sequences[:50]:  # Test first 50
                cache_service.get_sequence_image(sequence)

        self.results.append(self.monitor.last_metrics)

    def _test_memory_leak_detection(self):
        """Test for memory leaks over extended session."""
        self.logger.info("Testing memory leak detection")

        initial_memory = self.monitor.process.memory_info().rss / 1024 / 1024

        # Perform repetitive operations
        for cycle in range(10):  # 10 cycles
            # Create and destroy widgets
            widgets = []
            for i in range(20):
                sequence = self._generate_test_sequences(
                    count=1, beat_count_range=(3, 6)
                )[0]
                widget = ModernThumbnailCard(sequence)
                widgets.append(widget)

            # Clean up widgets
            for widget in widgets:
                widget.deleteLater()

            QCoreApplication.processEvents()

            # Check memory usage
            current_memory = self.monitor.process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory

            self.logger.debug(f"Cycle {cycle}: Memory growth: {memory_growth:.1f}MB")

        final_memory = self.monitor.process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory

        # Create memory leak metric
        with self.monitor.measure("memory_leak_test", target_ms=0.0):  # No time target
            pass

        self.monitor.last_metrics.details["memory_growth_mb"] = total_growth
        self.monitor.last_metrics.details["acceptable_growth"] = (
            total_growth < 100
        )  # 100MB threshold
        self.results.append(self.monitor.last_metrics)

    def _test_resource_monitoring(self):
        """Test resource monitoring during operations."""
        self.logger.info("Testing resource monitoring")

        # Monitor resources during various operations
        operations = [
            ("widget_creation_resources", self._create_multiple_widgets),
            ("navigation_resources", lambda: self._navigate_to_section("S")),
            ("scroll_resources", self._perform_extended_scroll),
            ("thumbnail_click_resources", self._click_multiple_thumbnails),
        ]

        for op_name, operation in operations:
            initial_cpu = self.monitor.process.cpu_percent()
            initial_memory = self.monitor.process.memory_info().rss / 1024 / 1024

            with self.monitor.measure(op_name, target_ms=1000.0):
                operation()
                QCoreApplication.processEvents()

            final_cpu = self.monitor.process.cpu_percent()
            final_memory = self.monitor.process.memory_info().rss / 1024 / 1024

            self.monitor.last_metrics.details.update(
                {
                    "cpu_delta": final_cpu - initial_cpu,
                    "memory_delta_mb": final_memory - initial_memory,
                    "peak_cpu": max(initial_cpu, final_cpu),
                    "peak_memory_mb": final_memory,
                }
            )

            self.results.append(self.monitor.last_metrics)

    def run_multi_action_stress_tests(self):
        """Test 6: Realistic Multi-Action Stress Testing."""
        self.logger.info("=== MULTI-ACTION STRESS PERFORMANCE TESTS ===")

        # Test 6.1: Concurrent user action simulation
        self._test_concurrent_user_actions()

        # Test 6.2: Session endurance testing
        self._test_session_endurance()

        # Test 6.3: Workflow simulation
        self._test_workflow_simulation()

        # Test 6.4: Performance baseline comparison
        self._test_performance_baseline()

    def _test_concurrent_user_actions(self):
        """Test simultaneous scroll + navigation + thumbnail clicks."""
        self.logger.info("Testing concurrent user actions")

        # Setup concurrent action timers
        scroll_timer = QTimer()
        navigation_timer = QTimer()
        thumbnail_timer = QTimer()

        action_count = {"scroll": 0, "navigation": 0, "thumbnail": 0}

        def perform_scroll():
            scroll_area = self.browse_tab.main_content_area
            QTest.wheelEvent(
                scroll_area,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                delta=120,
            )
            action_count["scroll"] += 1

        def perform_navigation():
            sections = ["A", "B", "C", "D", "E"]
            section = sections[action_count["navigation"] % len(sections)]
            self._navigate_to_section(section)
            action_count["navigation"] += 1

        def perform_thumbnail_click():
            thumbnails = self._get_visible_thumbnails()
            if thumbnails:
                thumbnail = thumbnails[action_count["thumbnail"] % len(thumbnails)]
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                action_count["thumbnail"] += 1

        # Connect timers
        scroll_timer.timeout.connect(perform_scroll)
        navigation_timer.timeout.connect(perform_navigation)
        thumbnail_timer.timeout.connect(perform_thumbnail_click)

        with self.monitor.measure(
            "concurrent_actions", target_ms=30000.0
        ):  # 30 second test
            # Start concurrent actions
            scroll_timer.start(100)  # Scroll every 100ms
            navigation_timer.start(2000)  # Navigate every 2 seconds
            thumbnail_timer.start(1500)  # Click thumbnail every 1.5 seconds

            # Run for 30 seconds
            start_time = time.time()
            while time.time() - start_time < 30.0:
                QCoreApplication.processEvents()
                QTest.qWait(50)

            # Stop timers
            scroll_timer.stop()
            navigation_timer.stop()
            thumbnail_timer.stop()

        self.monitor.last_metrics.details.update(action_count)
        self.results.append(self.monitor.last_metrics)

    def _test_session_endurance(self):
        """Test session endurance over 30+ minutes."""
        self.logger.info("Testing session endurance (30+ minutes)")

        start_time = time.time()
        cycle_count = 0
        performance_degradation = []

        while time.time() - start_time < 1800:  # 30 minutes
            cycle_start = time.time()

            # Perform typical user workflow
            with self.monitor.measure(
                f"endurance_cycle_{cycle_count}", target_ms=5000.0
            ):
                # Navigate to random section
                sections = ["A", "C", "E", "G", "I", "K", "M", "O", "Q", "S"]
                section = sections[cycle_count % len(sections)]
                self._navigate_to_section(section)

                # Scroll around
                for _ in range(5):
                    self._perform_scroll_operation()
                    QTest.qWait(200)

                # Click some thumbnails
                thumbnails = self._get_visible_thumbnails()[:3]
                for thumbnail in thumbnails:
                    QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                    QTest.qWait(500)

                QCoreApplication.processEvents()

            cycle_duration = self.monitor.last_metrics.duration_ms
            performance_degradation.append(cycle_duration)

            self.results.append(self.monitor.last_metrics)
            cycle_count += 1

            # Log progress every 10 cycles
            if cycle_count % 10 == 0:
                avg_recent = sum(performance_degradation[-10:]) / 10
                self.logger.info(
                    f"Endurance test: {cycle_count} cycles, avg recent: {avg_recent:.1f}ms"
                )

            QTest.qWait(1000)  # 1 second between cycles

        # Analyze performance degradation
        initial_avg = (
            sum(performance_degradation[:5]) / 5
            if len(performance_degradation) >= 5
            else 0
        )
        final_avg = (
            sum(performance_degradation[-5:]) / 5
            if len(performance_degradation) >= 5
            else 0
        )
        degradation_percent = (
            ((final_avg - initial_avg) / initial_avg * 100) if initial_avg > 0 else 0
        )

        self.logger.info(
            f"Endurance test completed: {cycle_count} cycles, {degradation_percent:.1f}% degradation"
        )

    def _test_workflow_simulation(self):
        """Test realistic usage patterns."""
        self.logger.info("Testing workflow simulation")

        workflows = [
            self._workflow_browse_and_select,
            self._workflow_rapid_navigation,
            self._workflow_detailed_examination,
            self._workflow_comparison_browsing,
        ]

        for i, workflow in enumerate(workflows):
            with self.monitor.measure(
                f"workflow_{i}_{workflow.__name__}", target_ms=10000.0
            ):
                workflow()
                QCoreApplication.processEvents()

            self.results.append(self.monitor.last_metrics)

    def _test_performance_baseline(self):
        """Test performance baseline comparison."""
        self.logger.info("Testing performance baseline")

        # Establish baseline measurements
        baseline_tests = [
            ("baseline_widget_creation", lambda: self._create_test_widget()),
            ("baseline_navigation", lambda: self._navigate_to_section("M")),
            ("baseline_thumbnail_click", lambda: self._click_first_thumbnail()),
            ("baseline_scroll", lambda: self._perform_scroll_operation()),
        ]

        baseline_results = {}

        for test_name, test_func in baseline_tests:
            times = []
            for _ in range(5):  # 5 iterations for average
                with self.monitor.measure(f"{test_name}_iteration", target_ms=1000.0):
                    test_func()
                    QCoreApplication.processEvents()

                times.append(self.monitor.last_metrics.duration_ms)
                self.results.append(self.monitor.last_metrics)

            baseline_results[test_name] = {
                "average_ms": sum(times) / len(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "std_dev": self._calculate_std_dev(times),
            }

        # Store baseline for comparison
        self.baseline_results = baseline_results
        self.logger.info(f"Baseline established: {baseline_results}")

    # Utility Methods for Test Operations
    def _generate_test_sequences(
        self, count: int, beat_count_range: Tuple[int, int]
    ) -> List[Any]:
        """Generate test sequences with specified parameters."""
        # This would integrate with the actual sequence generation system
        # For now, return mock sequences
        sequences = []
        for i in range(count):
            # Create mock sequence object
            sequence = {
                "id": f"TEST_{i:04d}",
                "beat_count": beat_count_range[0]
                + (i % (beat_count_range[1] - beat_count_range[0] + 1)),
                "complexity": (
                    "simple" if i % 3 == 0 else "medium" if i % 3 == 1 else "complex"
                ),
            }
            sequences.append(sequence)
        return sequences

    def _find_section_button(self, navigation, section: str):
        """Find section button in navigation sidebar."""
        # This would find the actual button widget
        # For now, return a mock button
        return navigation  # Placeholder

    def _verify_navigation_completion(self, section: str):
        """Verify that navigation to section completed successfully."""
        # This would check the actual UI state
        pass

    def _get_visible_thumbnails(self) -> List[Any]:
        """Get list of currently visible thumbnail widgets."""
        # This would return actual thumbnail widgets
        return []  # Placeholder

    def _get_thumbnail_sequence_id(self, thumbnail) -> str:
        """Get sequence ID from thumbnail widget."""
        return "TEST_SEQUENCE"  # Placeholder

    def _verify_sequence_loaded_in_viewer(self, sequence_id: str):
        """Verify sequence is loaded in the sequence viewer."""
        pass

    def _find_thumbnails_by_beat_count(
        self, min_beats: int, max_beats: int
    ) -> List[Any]:
        """Find thumbnails with sequences in specified beat count range."""
        return []  # Placeholder

    def _get_sequence_beat_count(self, sequence_id: str) -> int:
        """Get beat count for sequence."""
        return 4  # Placeholder

    def _clear_sequence_viewer(self):
        """Clear the sequence viewer."""
        if hasattr(self.browse_tab, "sequence_viewer"):
            self.browse_tab.sequence_viewer.clear()

    def _start_background_widget_creation(self):
        """Start background widget creation process."""
        # This would trigger the actual background widget creation
        pass

    def _stop_background_widget_creation(self):
        """Stop background widget creation process."""
        pass

    def _count_sequences_in_section(self, section: str) -> int:
        """Count sequences in specified section."""
        return 50  # Placeholder

    def _find_empty_sections(self) -> List[str]:
        """Find sections with no sequences."""
        return ["Z"]  # Placeholder

    def _create_test_widget(self):
        """Create a test widget."""
        sequence = self._generate_test_sequences(1, (3, 5))[0]
        widget = ModernThumbnailCard(sequence)
        widget.show()
        QCoreApplication.processEvents()
        widget.deleteLater()

    def _navigate_to_section(self, section: str):
        """Navigate to specified section."""
        navigation = self.browse_tab.navigation_sidebar
        section_button = self._find_section_button(navigation, section)
        if section_button:
            QTest.mouseClick(section_button, Qt.MouseButton.LeftButton)

    def _click_first_thumbnail(self):
        """Click the first visible thumbnail."""
        thumbnails = self._get_visible_thumbnails()
        if thumbnails:
            QTest.mouseClick(thumbnails[0], Qt.MouseButton.LeftButton)

    def _perform_scroll_operation(self):
        """Perform a scroll operation."""
        scroll_area = self.browse_tab.main_content_area
        QTest.wheelEvent(
            scroll_area,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            delta=120,
        )

    # Workflow simulation methods
    def _workflow_browse_and_select(self):
        """Simulate browse and select workflow."""
        # Navigate to section
        self._navigate_to_section("M")
        QTest.qWait(500)

        # Scroll to find interesting sequences
        for _ in range(3):
            self._perform_scroll_operation()
            QTest.qWait(200)

        # Click thumbnail to view sequence
        self._click_first_thumbnail()
        QTest.qWait(1000)

    def _workflow_rapid_navigation(self):
        """Simulate rapid navigation workflow."""
        sections = ["A", "E", "I", "M", "Q"]
        for section in sections:
            self._navigate_to_section(section)
            QTest.qWait(200)

    def _workflow_detailed_examination(self):
        """Simulate detailed examination workflow."""
        # Navigate to section
        self._navigate_to_section("K")
        QTest.qWait(500)

        # Click multiple thumbnails for examination
        thumbnails = self._get_visible_thumbnails()[:5]
        for thumbnail in thumbnails:
            QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
            QTest.qWait(800)  # Examine each sequence

    def _workflow_comparison_browsing(self):
        """Simulate comparison browsing workflow."""
        # Navigate between different sections for comparison
        comparison_sections = ["B", "H", "N", "T"]
        for section in comparison_sections:
            self._navigate_to_section(section)
            # Quick thumbnail examination
            thumbnails = self._get_visible_thumbnails()[:2]
            for thumbnail in thumbnails:
                QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
                QTest.qWait(300)

    def _create_multiple_widgets(self):
        """Create multiple widgets for resource testing."""
        widgets = []
        sequences = self._generate_test_sequences(count=10, beat_count_range=(3, 7))
        for sequence in sequences:
            widget = ModernThumbnailCard(sequence)
            widget.show()
            widgets.append(widget)

        QCoreApplication.processEvents()

        # Clean up
        for widget in widgets:
            widget.deleteLater()

    def _perform_extended_scroll(self):
        """Perform extended scroll operation."""
        scroll_area = self.browse_tab.main_content_area
        for i in range(20):
            delta = 120 if i % 2 == 0 else -120
            QTest.wheelEvent(
                scroll_area,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                delta=delta,
            )
            QTest.qWait(50)

    def _click_multiple_thumbnails(self):
        """Click multiple thumbnails for resource testing."""
        thumbnails = self._get_visible_thumbnails()[:5]
        for thumbnail in thumbnails:
            QTest.mouseClick(thumbnail, Qt.MouseButton.LeftButton)
            QTest.qWait(200)

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5

    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        if not self.results:
            return {"error": "No test results available"}

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        # Calculate performance statistics
        durations = [r.duration_ms for r in self.results]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0

        # Group results by test category
        category_stats = {}
        for result in self.results:
            category = (
                result.test_name.split("_")[0] if "_" in result.test_name else "unknown"
            )
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "passed": 0,
                    "avg_duration": 0,
                    "durations": [],
                }

            category_stats[category]["count"] += 1
            if result.passed:
                category_stats[category]["passed"] += 1
            category_stats[category]["durations"].append(result.duration_ms)

        # Calculate category averages
        for category, stats in category_stats.items():
            if stats["durations"]:
                stats["avg_duration"] = sum(stats["durations"]) / len(
                    stats["durations"]
                )

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
            "performance": {
                "avg_duration_ms": avg_duration,
                "min_duration_ms": min_duration,
                "max_duration_ms": max_duration,
                "std_dev_ms": self._calculate_std_dev(durations),
            },
            "category_breakdown": category_stats,
            "recommendations": self._generate_recommendations(),
        }

        return summary

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on results."""
        recommendations = []

        if not self.results:
            return ["No test data available for recommendations"]

        # Analyze slow operations
        slow_tests = [r for r in self.results if not r.passed]
        if slow_tests:
            recommendations.append(
                f"Found {len(slow_tests)} slow operations that exceeded targets"
            )

            # Group slow tests by type
            slow_by_type = {}
            for test in slow_tests:
                test_type = test.test_name.split("_")[0]
                if test_type not in slow_by_type:
                    slow_by_type[test_type] = []
                slow_by_type[test_type].append(test)

            for test_type, tests in slow_by_type.items():
                avg_slow_duration = sum(t.duration_ms for t in tests) / len(tests)
                recommendations.append(
                    f"Optimize {test_type} operations (avg {avg_slow_duration:.1f}ms)"
                )

        # Memory recommendations
        memory_tests = [r for r in self.results if "memory" in r.test_name.lower()]
        if memory_tests:
            memory_growth = sum(
                r.details.get("memory_growth_mb", 0) for r in memory_tests
            )
            if memory_growth > 50:  # 50MB threshold
                recommendations.append(
                    f"Memory growth detected: {memory_growth:.1f}MB - investigate memory leaks"
                )

        # Performance targets
        widget_creation_tests = [
            r for r in self.results if "widget_creation" in r.test_name
        ]
        if widget_creation_tests:
            avg_widget_time = sum(t.duration_ms for t in widget_creation_tests) / len(
                widget_creation_tests
            )
            if avg_widget_time > 50:
                recommendations.append(
                    f"Widget creation slow ({avg_widget_time:.1f}ms avg) - optimize thumbnail rendering"
                )

        if not recommendations:
            recommendations.append("All performance metrics within acceptable ranges")

        return recommendations

    def save_results(self, results: "TestResults"):
        """Save test results to file."""
        try:
            import json
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"stress_test_results_{timestamp}.json"

            # Convert results to serializable format
            results_dict = {
                "suite_name": results.suite_name,
                "start_time": results.start_time.isoformat(),
                "end_time": results.end_time.isoformat(),
                "total_tests": results.total_tests,
                "passed_tests": results.passed_tests,
                "failed_tests": results.failed_tests,
                "summary": results.summary,
                "test_details": [
                    {
                        "test_name": metric.test_name,
                        "duration_ms": metric.duration_ms,
                        "target_ms": metric.target_ms,
                        "passed": metric.passed,
                        "details": metric.details,
                    }
                    for metric in results.metrics
                ],
            }

            with open(filename, "w") as f:
                json.dump(results_dict, f, indent=2)

            self.logger.info(f"Test results saved to {filename}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")


# Support classes for test results
@dataclass
class PerformanceMetrics:
    test_name: str
    duration_ms: float
    target_ms: float
    passed: bool
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class TestResults:
    suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    metrics: List[PerformanceMetrics]
    summary: Dict[str, Any]


def main():
    """Main execution function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Browse Tab v2 Performance Stress Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python stress_test_suite.py --all
    python stress_test_suite.py --widget-creation --navigation
    python stress_test_suite.py --thumbnails --output-dir ./results
    python stress_test_suite.py --memory-stress --verbose
        """,
    )

    # Test selection arguments
    parser.add_argument("--all", action="store_true", help="Run all stress tests")
    parser.add_argument(
        "--widget-creation",
        action="store_true",
        help="Run widget creation performance tests",
    )
    parser.add_argument(
        "--navigation", action="store_true", help="Run navigation performance tests"
    )
    parser.add_argument(
        "--thumbnails", action="store_true", help="Run thumbnail interaction tests"
    )
    parser.add_argument(
        "--scroll-regression", action="store_true", help="Run scroll regression tests"
    )
    parser.add_argument(
        "--memory-stress",
        action="store_true",
        help="Run memory and resource stress tests",
    )
    parser.add_argument(
        "--multi-action", action="store_true", help="Run multi-action stress tests"
    )

    # Configuration arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_results",
        help="Output directory for test results",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick version of tests (reduced iterations)",
    )

    args = parser.parse_args()

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Initialize test suite
    suite = StressTestSuite(output_dir)

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        print("=" * 80)
        print("BROWSE TAB V2 PERFORMANCE STRESS TEST SUITE")
        print("=" * 80)
        print(f"Output Directory: {output_dir.absolute()}")
        print(f"Quick Mode: {'Enabled' if args.quick else 'Disabled'}")
        print()

        # Determine which tests to run
        if args.all:
            print("Running ALL stress tests...")
            results = suite.run_all_tests()
        else:
            # Run individual test categories
            suite.setup_test_environment()

            if args.widget_creation:
                print("Running widget creation tests...")
                suite.run_widget_creation_tests()

            if args.navigation:
                print("Running navigation tests...")
                suite.run_navigation_performance_tests()

            if args.thumbnails:
                print("Running thumbnail interaction tests...")
                suite.run_thumbnail_interaction_tests()

            if args.scroll_regression:
                print("Running scroll regression tests...")
                suite.run_scroll_regression_tests()

            if args.memory_stress:
                print("Running memory stress tests...")
                suite.run_memory_stress_tests()

            if args.multi_action:
                print("Running multi-action stress tests...")
                suite.run_multi_action_stress_tests()

            # If no specific tests selected, run all
            if not any(
                [
                    args.widget_creation,
                    args.navigation,
                    args.thumbnails,
                    args.scroll_regression,
                    args.memory_stress,
                    args.multi_action,
                ]
            ):
                print("No specific tests selected, running ALL tests...")
                results = suite.run_all_tests()
            else:
                # Compile individual test results
                end_time = datetime.now()
                results = TestResults(
                    suite_name="Browse Tab v2 Performance Stress Test (Selective)",
                    start_time=datetime.now(),  # Approximate
                    end_time=end_time,
                    total_tests=len(suite.results),
                    passed_tests=sum(1 for r in suite.results if r.passed),
                    failed_tests=sum(1 for r in suite.results if not r.passed),
                    metrics=suite.results,
                    summary=suite.generate_summary(),
                )

                suite.save_results(results)
                suite.teardown_test_environment()

        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {results.total_tests}")
        print(f"Passed: {results.passed_tests}")
        print(f"Failed: {results.failed_tests}")
        print(f"Success Rate: {results.summary['overall']['success_rate']:.1f}%")

        # Print category breakdown
        print("\nCATEGORY BREAKDOWN:")
        print("-" * 40)
        for category, stats in results.summary["categories"].items():
            success_rate = (
                (stats["passed"] / stats["count"] * 100) if stats["count"] > 0 else 0
            )
            print(
                f"{category.upper()}: {stats['passed']}/{stats['count']} ({success_rate:.1f}%) "
                f"avg: {stats['avg_time_ms']:.1f}ms"
            )

        # Print target analysis
        print("\nTARGET ANALYSIS:")
        print("-" * 40)
        for target, analysis in results.summary["target_analysis"].items():
            target_name = target.replace("_", " ").title()
            print(f"{target_name}: {analysis['success_rate']:.1f}% success rate")

        # Print top recommendations
        if results.summary["recommendations"]:
            print("\nTOP OPTIMIZATION RECOMMENDATIONS:")
            print("-" * 40)
            for i, rec in enumerate(results.summary["recommendations"][:3], 1):
                print(f"{i}. {rec}")

        print(f"\nDetailed results saved to: {output_dir.absolute()}")

        # Exit with appropriate code
        if results.failed_tests > 0:
            print(
                f"\n⚠️  {results.failed_tests} tests failed. See detailed report for analysis."
            )
            sys.exit(1)
        else:
            print(f"\n✅ All {results.passed_tests} tests passed!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        suite.teardown_test_environment()
        sys.exit(130)

    except Exception as e:
        print(f"\n\nTest execution failed with error: {e}")
        suite.logger.exception("Test execution failed")
        suite.teardown_test_environment()
        sys.exit(1)


if __name__ == "__main__":
    main()
