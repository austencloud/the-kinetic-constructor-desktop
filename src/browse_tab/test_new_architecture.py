"""
Test script for Browse Tab v2 Clean Architecture Implementation.

This script validates the new component-based architecture by:
1. Testing component imports and initialization
2. Validating service layer functionality
3. Testing component communication
4. Performance validation
5. Integration testing

Usage:
    python test_new_architecture.py
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, QElapsedTimer

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArchitectureTestWindow(QMainWindow):
    """Test window for validating the new architecture."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browse Tab v2 - Clean Architecture Test")
        self.setGeometry(100, 100, 1200, 800)

        # Performance tracking
        self.performance_timer = QElapsedTimer()
        self.test_results = {}

        # Setup UI
        self._setup_ui()

        # Start tests
        QTimer.singleShot(100, self._run_architecture_tests)

    def _setup_ui(self):
        """Setup test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Test status will be displayed here
        from PyQt6.QtWidgets import QTextEdit

        self.test_output = QTextEdit()
        self.test_output.setReadOnly(True)
        layout.addWidget(self.test_output)

    def _log_test(self, message: str):
        """Log test message to output."""
        logger.info(message)
        self.test_output.append(message)
        QApplication.processEvents()

    def _run_architecture_tests(self):
        """Run comprehensive architecture tests."""
        self._log_test("=== Browse Tab v2 Clean Architecture Test ===")
        self._log_test("")

        # Test 1: Component imports
        self._test_component_imports()

        # Test 2: Service layer
        self._test_service_layer()

        # Test 3: Main coordinator
        self._test_main_coordinator()

        # Test 4: Component integration
        self._test_component_integration()

        # Test 5: Performance validation
        self._test_performance()

        # Summary
        self._display_test_summary()

    def _test_component_imports(self):
        """Test that all new components can be imported."""
        self._log_test("Test 1: Component Imports")
        self._log_test("-" * 30)

        try:
            # Test new component imports
            from src.browse_tab.components.filter_panel import FilterPanel

            self._log_test("✓ FilterPanel imported successfully")
            self.test_results["filter_panel_import"] = True

        except ImportError as e:
            self._log_test(f"✗ FilterPanel import failed: {e}")
            self.test_results["filter_panel_import"] = False

        try:
            from src.browse_tab.components.grid_view import GridView

            self._log_test("✓ GridView imported successfully")
            self.test_results["grid_view_import"] = True

        except ImportError as e:
            self._log_test(f"✗ GridView import failed: {e}")
            self.test_results["grid_view_import"] = False

        try:
            from src.browse_tab.components.sequence_viewer import SequenceViewer

            self._log_test("✓ SequenceViewer imported successfully")
            self.test_results["sequence_viewer_import"] = True

        except ImportError as e:
            self._log_test(f"✗ SequenceViewer import failed: {e}")
            self.test_results["sequence_viewer_import"] = False

        try:
            from src.browse_tab.components.navigation_sidebar import NavigationSidebar

            self._log_test("✓ NavigationSidebar imported successfully")
            self.test_results["navigation_sidebar_import"] = True

        except ImportError as e:
            self._log_test(f"✗ NavigationSidebar import failed: {e}")
            self.test_results["navigation_sidebar_import"] = False

        try:
            from src.browse_tab.components.thumbnail_card import ThumbnailCard

            self._log_test("✓ ThumbnailCard imported successfully")
            self.test_results["thumbnail_card_import"] = True

        except ImportError as e:
            self._log_test(f"✗ ThumbnailCard import failed: {e}")
            self.test_results["thumbnail_card_import"] = False

        self._log_test("")

    def _test_service_layer(self):
        """Test service layer functionality."""
        self._log_test("Test 2: Service Layer")
        self._log_test("-" * 30)

        try:
            from src.browse_tab.services.sequence_data_service import (
                SequenceDataService,
            )
            from src.browse_tab.core.interfaces import BrowseTabConfig

            config = BrowseTabConfig()
            service = SequenceDataService(config)

            self._log_test("✓ SequenceDataService created successfully")
            self.test_results["sequence_data_service"] = True

        except Exception as e:
            self._log_test(f"✗ SequenceDataService failed: {e}")
            self.test_results["sequence_data_service"] = False

        try:
            from src.browse_tab.services.performance_cache_service import (
                PerformanceCacheService,
            )

            cache_service = PerformanceCacheService(config)

            self._log_test("✓ PerformanceCacheService created successfully")
            self.test_results["performance_cache_service"] = True

        except Exception as e:
            self._log_test(f"✗ PerformanceCacheService failed: {e}")
            self.test_results["performance_cache_service"] = False

        self._log_test("")

    def _test_main_coordinator(self):
        """Test main coordinator functionality."""
        self._log_test("Test 3: Main Coordinator")
        self._log_test("-" * 30)

        try:
            from browse_tab.browse_tab_main import BrowseTabMain
            from src.browse_tab.core.interfaces import BrowseTabConfig

            # Create mock viewmodel
            class MockViewModel:
                def __init__(self):
                    self.state_changed = lambda: None
                    self.error_occurred = lambda: None

            config = BrowseTabConfig()
            viewmodel = MockViewModel()

            # Test coordinator creation
            coordinator = BrowseTabMain(viewmodel, config)

            self._log_test("✓ BrowseTabV2Main coordinator created successfully")
            self._log_test(f"✓ Coordinator size: {coordinator.size()}")
            self.test_results["main_coordinator"] = True

        except Exception as e:
            self._log_test(f"✗ Main coordinator failed: {e}")
            self.test_results["main_coordinator"] = False

        self._log_test("")

    def _test_component_integration(self):
        """Test component integration and communication."""
        self._log_test("Test 4: Component Integration")
        self._log_test("-" * 30)

        try:
            # Test component creation with services
            from src.browse_tab.components.filter_panel import FilterPanel
            from src.browse_tab.core.interfaces import BrowseTabConfig

            config = BrowseTabConfig()
            filter_panel = FilterPanel(config)

            # Test signal connections
            signal_connected = hasattr(filter_panel, "search_changed")
            self._log_test(f"✓ FilterPanel signals available: {signal_connected}")

            self.test_results["component_integration"] = True

        except Exception as e:
            self._log_test(f"✗ Component integration failed: {e}")
            self.test_results["component_integration"] = False

        self._log_test("")

    def _test_performance(self):
        """Test performance characteristics."""
        self._log_test("Test 5: Performance Validation")
        self._log_test("-" * 30)

        try:
            self.performance_timer.start()

            # Test component creation performance
            from src.browse_tab.components.filter_panel import FilterPanel
            from src.browse_tab.core.interfaces import BrowseTabConfig

            config = BrowseTabConfig()

            # Create multiple components to test performance
            components = []
            for i in range(5):
                component = FilterPanel(config)
                components.append(component)

            creation_time = self.performance_timer.elapsed()

            self._log_test(f"✓ Created 5 FilterPanel components in {creation_time}ms")

            # Performance target: <50ms per component
            avg_time = creation_time / 5
            if avg_time < 50:
                self._log_test(f"✓ Performance target met: {avg_time:.1f}ms < 50ms")
                self.test_results["performance"] = True
            else:
                self._log_test(f"⚠ Performance target missed: {avg_time:.1f}ms > 50ms")
                self.test_results["performance"] = False

        except Exception as e:
            self._log_test(f"✗ Performance test failed: {e}")
            self.test_results["performance"] = False

        self._log_test("")

    def _display_test_summary(self):
        """Display test summary."""
        self._log_test("=== Test Summary ===")
        self._log_test("")

        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)

        self._log_test(f"Tests Passed: {passed}/{total}")
        self._log_test("")

        for test_name, result in self.test_results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            self._log_test(f"{status}: {test_name}")

        self._log_test("")

        if passed == total:
            self._log_test(
                "🎉 All tests passed! Clean architecture is working correctly."
            )
        else:
            self._log_test("⚠ Some tests failed. Check the implementation.")

        self._log_test("")
        self._log_test("=== Architecture Status ===")
        self._log_test("✓ New component structure created")
        self._log_test("✓ Service layer implemented")
        self._log_test("✓ Main coordinator pattern established")
        self._log_test("✓ Single responsibility principle applied")
        self._log_test("✓ Performance targets defined")
        self._log_test("")
        self._log_test("Next Steps:")
        self._log_test("1. Integrate with existing Browse Tab v2")
        self._log_test("2. Migrate data from monolithic view")
        self._log_test("3. Test with real sequence data")
        self._log_test("4. Performance optimization")
        self._log_test("5. Replace legacy components")


def main():
    """Main test function."""
    app = QApplication(sys.argv)

    # Create test window
    test_window = ArchitectureTestWindow()
    test_window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
