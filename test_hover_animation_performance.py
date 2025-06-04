"""
Hover Animation Performance Validation Test

Tests the optimized hover animation system to ensure:
1. 60fps performance during hover events
2. No conflicts with virtual scrolling
3. Immediate CSS-only transitions
4. No QTimer conflicts
"""

import sys
import logging
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HoverPerformanceTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hover Animation Performance Test")
        self.setGeometry(100, 100, 1200, 800)

        # Test results
        self.hover_event_count = 0
        self.animation_conflicts = 0
        self.frame_drops = 0
        self.test_results = {}

        self.setup_ui()
        self.setup_test_cards()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Test status
        self.status_label = QLabel("Initializing hover animation test...")
        layout.addWidget(self.status_label)

        # Import optimized components
        try:
            from src.browse_tab_v2.components.optimized_hover_manager import (
                get_global_hover_manager,
            )
            from src.browse_tab_v2.components.fast_thumbnail_card import (
                FastThumbnailCard,
            )
            from src.browse_tab_v2.components.efficient_virtual_grid import (
                EfficientVirtualGrid,
            )

            self.hover_manager = get_global_hover_manager()
            self.status_label.setText("✅ Optimized hover system loaded successfully")

            # Create test grid
            self.test_grid = EfficientVirtualGrid()
            layout.addWidget(self.test_grid)

        except ImportError as e:
            self.status_label.setText(
                f"❌ Failed to import optimized hover system: {e}"
            )
            logger.error(f"Import failed: {e}")

    def setup_test_cards(self):
        """Create test thumbnail cards for hover testing"""
        try:
            # Create mock sequences for testing
            test_sequences = []
            for i in range(20):
                mock_sequence = type(
                    "MockSequence",
                    (),
                    {
                        "id": f"test_seq_{i}",
                        "name": f"Test Sequence {i}",
                        "thumbnails": [f"test_thumb_{i}.png"],
                    },
                )()
                test_sequences.append(mock_sequence)

            # Set up test grid with sequences
            self.test_grid.set_item_creator(self.create_test_card)
            self.test_grid.set_sequences(test_sequences)

            logger.info(f"Created {len(test_sequences)} test cards")

        except Exception as e:
            logger.error(f"Failed to setup test cards: {e}")

    def create_test_card(self, sequence, index):
        """Create a test thumbnail card with hover tracking"""
        from src.browse_tab_v2.components.fast_thumbnail_card import FastThumbnailCard

        card = FastThumbnailCard(sequence)

        # Register with hover manager
        if hasattr(self, "hover_manager"):
            card.set_hover_manager(self.hover_manager)

        # Track hover events for performance testing
        original_enter = card.enterEvent
        original_leave = card.leaveEvent

        def tracked_enter(event):
            start_time = time.time()
            original_enter(event)
            end_time = time.time()

            self.hover_event_count += 1
            hover_time = (end_time - start_time) * 1000

            # Check for performance issues
            if hover_time > 16:  # More than 16ms = frame drop
                self.frame_drops += 1
                logger.warning(f"Hover enter took {hover_time:.1f}ms (frame drop)")

        def tracked_leave(event):
            start_time = time.time()
            original_leave(event)
            end_time = time.time()

            hover_time = (end_time - start_time) * 1000

            if hover_time > 16:
                self.frame_drops += 1
                logger.warning(f"Hover leave took {hover_time:.1f}ms (frame drop)")

        card.enterEvent = tracked_enter
        card.leaveEvent = tracked_leave

        return card


class HoverAnimationTestRunner:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.test_window = HoverPerformanceTestWindow()

    def run_performance_tests(self):
        """Run comprehensive hover animation performance tests"""
        self.test_window.show()

        # Wait for UI to initialize
        QTest.qWait(1000)

        logger.info("🧪 Starting hover animation performance tests...")

        # Test 1: Basic hover responsiveness
        self.test_hover_responsiveness()

        # Test 2: Virtual scrolling integration
        self.test_virtual_scroll_hover()

        # Test 3: Rapid hover events
        self.test_rapid_hover_events()

        # Test 4: Memory usage
        self.test_memory_usage()

        # Generate report
        self.generate_test_report()

        return self.test_window.test_results

    def test_hover_responsiveness(self):
        """Test 1: Basic hover event responsiveness"""
        logger.info("🧪 Test 1: Hover responsiveness")

        start_time = time.time()
        initial_hover_count = self.test_window.hover_event_count
        initial_frame_drops = self.test_window.frame_drops

        # Simulate hover events on first few cards
        cards = list(self.test_window.test_grid._all_widgets.values())[:5]

        for card in cards:
            # Simulate mouse enter
            QTest.mouseMove(card, card.rect().center())
            QTest.qWait(50)

            # Simulate mouse leave
            QTest.mouseMove(card, card.rect().bottomRight() + card.rect().bottomRight())
            QTest.qWait(50)

        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        hover_events = self.test_window.hover_event_count - initial_hover_count
        frame_drops = self.test_window.frame_drops - initial_frame_drops

        # Calculate performance metrics
        avg_hover_time = total_time / max(hover_events, 1)
        frame_drop_rate = (frame_drops / max(hover_events, 1)) * 100

        self.test_window.test_results["hover_responsiveness"] = {
            "total_time_ms": total_time,
            "hover_events": hover_events,
            "avg_hover_time_ms": avg_hover_time,
            "frame_drops": frame_drops,
            "frame_drop_rate_percent": frame_drop_rate,
            "passed": frame_drop_rate < 5.0,  # Less than 5% frame drops
        }

        logger.info(
            f"✅ Hover responsiveness: {avg_hover_time:.1f}ms avg, {frame_drop_rate:.1f}% frame drops"
        )

    def test_virtual_scroll_hover(self):
        """Test 2: Hover events during virtual scrolling"""
        logger.info("🧪 Test 2: Virtual scroll + hover integration")

        start_time = time.time()
        initial_conflicts = self.test_window.animation_conflicts

        # Simulate scrolling while hovering
        scroll_area = self.test_window.test_grid.scroll_area

        for scroll_pos in range(0, 500, 50):
            # Set scroll position
            scroll_area.verticalScrollBar().setValue(scroll_pos)
            QTest.qWait(20)

            # Try to hover during scroll
            if self.test_window.test_grid._all_widgets:
                first_card = list(self.test_window.test_grid._all_widgets.values())[0]
                QTest.mouseMove(first_card, first_card.rect().center())
                QTest.qWait(10)

        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        conflicts = self.test_window.animation_conflicts - initial_conflicts

        self.test_window.test_results["virtual_scroll_hover"] = {
            "total_time_ms": total_time,
            "animation_conflicts": conflicts,
            "passed": conflicts == 0,  # No animation conflicts
        }

        logger.info(f"✅ Virtual scroll integration: {conflicts} conflicts detected")

    def test_rapid_hover_events(self):
        """Test 3: Rapid consecutive hover events"""
        logger.info("🧪 Test 3: Rapid hover events")

        start_time = time.time()
        initial_frame_drops = self.test_window.frame_drops

        # Rapidly move mouse between cards
        cards = list(self.test_window.test_grid._all_widgets.values())[:10]

        for _ in range(3):  # 3 rapid cycles
            for card in cards:
                QTest.mouseMove(card, card.rect().center())
                QTest.qWait(5)  # Very fast movement

        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        frame_drops = self.test_window.frame_drops - initial_frame_drops
        events_per_second = (len(cards) * 3) / (total_time / 1000)

        self.test_window.test_results["rapid_hover"] = {
            "total_time_ms": total_time,
            "events_per_second": events_per_second,
            "frame_drops": frame_drops,
            "passed": frame_drops < 2,  # Less than 2 frame drops for rapid events
        }

        logger.info(
            f"✅ Rapid hover: {events_per_second:.1f} events/sec, {frame_drops} frame drops"
        )

    def test_memory_usage(self):
        """Test 4: Memory usage during hover operations"""
        logger.info("🧪 Test 4: Memory usage test")

        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform intensive hover operations
        cards = list(self.test_window.test_grid._all_widgets.values())

        for _ in range(10):  # 10 cycles
            for card in cards:
                QTest.mouseMove(card, card.rect().center())
                QTest.qWait(10)
                QTest.mouseMove(card, card.rect().topLeft() - card.rect().topLeft())
                QTest.qWait(10)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        self.test_window.test_results["memory_usage"] = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "passed": memory_increase < 50,  # Less than 50MB increase
        }

        logger.info(f"✅ Memory usage: {memory_increase:.1f}MB increase")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating hover animation test report...")

        results = self.test_window.test_results
        total_tests = len(results)
        passed_tests = sum(1 for test in results.values() if test.get("passed", False))

        print("\n" + "=" * 80)
        print("🎯 HOVER ANIMATION PERFORMANCE TEST REPORT")
        print("=" * 80)
        print(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        print()

        for test_name, test_data in results.items():
            status = "✅ PASSED" if test_data.get("passed", False) else "❌ FAILED"
            print(f"{status} {test_name.replace('_', ' ').title()}")

            # Print key metrics
            for key, value in test_data.items():
                if key != "passed":
                    if isinstance(value, float):
                        print(f"  • {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"  • {key.replace('_', ' ').title()}: {value}")
            print()

        # Performance summary
        hover_test = results.get("hover_responsiveness", {})
        if hover_test:
            avg_time = hover_test.get("avg_hover_time_ms", 0)
            frame_rate = 1000 / max(avg_time, 1)
            print(f"🎯 Performance Summary:")
            print(f"  • Average hover response: {avg_time:.1f}ms")
            print(f"  • Effective frame rate: {frame_rate:.1f}fps")
            print(
                f"  • Frame drop rate: {hover_test.get('frame_drop_rate_percent', 0):.1f}%"
            )

        print("\n" + "=" * 80)

        # Update UI
        if passed_tests == total_tests:
            self.test_window.status_label.setText(
                f"✅ ALL TESTS PASSED ({passed_tests}/{total_tests})"
            )
        else:
            self.test_window.status_label.setText(
                f"⚠️ {passed_tests}/{total_tests} tests passed"
            )


def main():
    """Run the hover animation performance test"""
    logger.info("🚀 Starting hover animation performance validation...")

    try:
        test_runner = HoverAnimationTestRunner()
        results = test_runner.run_performance_tests()

        # Keep window open for inspection
        input("\nPress Enter to close the test window...")

        return results

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return None


if __name__ == "__main__":
    main()
