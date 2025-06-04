"""
Hover Animation Issues Reproduction Test - Phase 2

This test isolates and reproduces the critical hover animation issues
identified in the browse_tab_v2 system to understand root causes.
"""

import sys
import time
import logging
from typing import Dict, List
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QTextEdit,
)
from PyQt6.QtCore import (
    QTimer,
    pyqtSignal,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
)
from PyQt6.QtGui import QMouseEvent, QEnterEvent

# Configure logging to capture animation events
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class HoverTestCard(QWidget):
    """Test card that reproduces the hover animation issues"""

    def __init__(self, card_id: int, parent=None):
        super().__init__(parent)
        self.card_id = card_id
        self.setFixedSize(200, 150)

        # Animation state tracking (like FastThumbnailCard)
        self._hover_animation_active = False
        self._is_hovered = False
        self._hover_animation = None
        self._hover_count = 0
        self._enter_count = 0
        self._leave_count = 0

        # Create UI
        layout = QVBoxLayout(self)
        self.label = QLabel(f"Card {card_id}")
        self.status_label = QLabel("Normal")
        self.counter_label = QLabel("Events: 0")

        layout.addWidget(self.label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.counter_label)

        # Style
        self.setStyleSheet(
            """
            HoverTestCard {
                background: rgba(200, 200, 200, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
            }
            HoverTestCard:hover {
                background: rgba(220, 220, 220, 0.9);
            }
        """
        )

        # Performance tracking
        self._last_enter_time = 0
        self._last_leave_time = 0

    def enterEvent(self, event: QEnterEvent):
        """Reproduce FastThumbnailCard hover enter logic"""
        current_time = time.time()
        self._enter_count += 1

        logger.debug(
            f"CARD {self.card_id}: enterEvent #{self._enter_count} "
            f"(time since last: {(current_time - self._last_enter_time)*1000:.1f}ms)"
        )

        # Reproduce the duplicate prevention logic
        if not self._is_hovered and not self._hover_animation_active:
            self._is_hovered = True
            self._hover_animation_active = True
            self._hover_count += 1

            logger.debug(
                f"CARD {self.card_id}: Starting hover animation #{self._hover_count}"
            )
            self.status_label.setText(f"Hovering #{self._hover_count}")
            self.counter_label.setText(
                f"Enter: {self._enter_count}, Leave: {self._leave_count}"
            )

            # Start animation (like FastThumbnailCard)
            self._start_hover_animation()

            # Reset flag after delay (like FastThumbnailCard)
            QTimer.singleShot(250, self._reset_hover_animation_flag)
        else:
            logger.warning(
                f"CARD {self.card_id}: DUPLICATE ENTER EVENT BLOCKED "
                f"(hovered={self._is_hovered}, active={self._hover_animation_active})"
            )

        self._last_enter_time = current_time
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reproduce FastThumbnailCard hover leave logic"""
        current_time = time.time()
        self._leave_count += 1

        logger.debug(
            f"CARD {self.card_id}: leaveEvent #{self._leave_count} "
            f"(time since last: {(current_time - self._last_leave_time)*1000:.1f}ms)"
        )

        if self._is_hovered:
            self._is_hovered = False
            logger.debug(f"CARD {self.card_id}: Starting leave animation")
            self.status_label.setText("Leaving")
            self.counter_label.setText(
                f"Enter: {self._enter_count}, Leave: {self._leave_count}"
            )

            # Start leave animation
            self._start_leave_animation()
        else:
            logger.warning(
                f"CARD {self.card_id}: UNEXPECTED LEAVE EVENT (not hovering)"
            )

        self._last_leave_time = current_time
        super().leaveEvent(event)

    def _start_hover_animation(self):
        """Start hover animation (reproduces glassmorphic glow)"""
        if self._hover_animation:
            self._hover_animation.stop()

        self._hover_animation = QParallelAnimationGroup()

        # Scale animation (like ModernThumbnailCard)
        scale_anim = QPropertyAnimation(self, b"geometry")
        scale_anim.setDuration(200)

        current_geo = self.geometry()
        scaled_geo = current_geo.adjusted(-5, -5, 5, 5)  # Slightly larger

        scale_anim.setStartValue(current_geo)
        scale_anim.setEndValue(scaled_geo)
        scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._hover_animation.addAnimation(scale_anim)

        # Connect to track completion
        self._hover_animation.finished.connect(
            lambda: logger.debug(f"CARD {self.card_id}: Hover animation completed")
        )

        self._hover_animation.start()

    def _start_leave_animation(self):
        """Start leave animation"""
        if self._hover_animation:
            self._hover_animation.stop()

        self._hover_animation = QParallelAnimationGroup()

        # Scale back
        scale_anim = QPropertyAnimation(self, b"geometry")
        scale_anim.setDuration(200)

        current_geo = self.geometry()
        original_geo = current_geo.adjusted(5, 5, -5, -5)  # Back to original

        scale_anim.setStartValue(current_geo)
        scale_anim.setEndValue(original_geo)
        scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._hover_animation.addAnimation(scale_anim)

        # Connect to track completion
        self._hover_animation.finished.connect(
            lambda: logger.debug(f"CARD {self.card_id}: Leave animation completed")
        )

        self._hover_animation.start()

    def _reset_hover_animation_flag(self):
        """Reset animation flag (like FastThumbnailCard)"""
        self._hover_animation_active = False
        logger.debug(f"CARD {self.card_id}: Animation flag reset")


class VirtualScrollTest(QWidget):
    """Reproduce virtual scrolling + hover animation conflicts"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hover Animation Issues Test")
        self.setGeometry(100, 100, 800, 600)

        # Create UI
        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start Virtual Scroll Test")
        self.stop_btn = QPushButton("Stop Test")
        self.clear_btn = QPushButton("Clear Log")

        self.start_btn.clicked.connect(self.start_test)
        self.stop_btn.clicked.connect(self.stop_test)
        self.clear_btn.clicked.connect(self.clear_log)

        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.clear_btn)

        layout.addLayout(controls)

        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(300)

        self.scroll_content = QFrame()
        self.scroll_layout = QHBoxLayout(self.scroll_content)

        # Create test cards
        self.cards: List[HoverTestCard] = []
        for i in range(20):
            card = HoverTestCard(i)
            self.cards.append(card)
            self.scroll_layout.addWidget(card)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setFixedHeight(200)
        layout.addWidget(self.log_output)

        # Test timers (reproduce QTimer.singleShot conflicts)
        self.viewport_timer = QTimer()
        self.viewport_timer.setSingleShot(True)
        self.viewport_timer.timeout.connect(self._simulate_viewport_change)

        self.image_loading_timer = QTimer()
        self.image_loading_timer.setSingleShot(True)
        self.image_loading_timer.timeout.connect(self._simulate_image_loading)

        # Set up logging capture
        self.setup_logging()

        self.test_running = False

    def setup_logging(self):
        """Capture logs to display in UI"""

        class LogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(msg)
                # Auto-scroll to bottom
                scrollbar = self.text_widget.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

        handler = LogHandler(self.log_output)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(handler)

    def start_test(self):
        """Start the reproduction test"""
        self.test_running = True
        logger.info("=== HOVER ANIMATION ISSUE TEST STARTED ===")
        logger.info("Move mouse rapidly over cards to reproduce issues")

        # Simulate virtual scrolling conflicts
        self._start_virtual_scroll_simulation()

    def stop_test(self):
        """Stop the test"""
        self.test_running = False
        self.viewport_timer.stop()
        self.image_loading_timer.stop()
        logger.info("=== TEST STOPPED ===")

    def clear_log(self):
        """Clear the log output"""
        self.log_output.clear()

    def _start_virtual_scroll_simulation(self):
        """Simulate virtual scrolling operations that conflict with hover"""
        if not self.test_running:
            return

        # Simulate viewport changes (like EfficientVirtualGrid)
        logger.debug("VIRTUAL_SCROLL: Simulating viewport change")
        self.viewport_timer.start(100)  # Every 100ms

        # Simulate image loading operations
        logger.debug("VIRTUAL_SCROLL: Simulating image loading")
        self.image_loading_timer.start(150)  # Every 150ms

    def _simulate_viewport_change(self):
        """Simulate viewport change operations"""
        if not self.test_running:
            return

        logger.debug("VIEWPORT: Processing viewport change (conflicts with hover)")

        # Simulate widget recycling (like virtual scrolling)
        if self.cards:
            # Hide/show random cards to simulate widget pool operations
            import random

            card = random.choice(self.cards)
            if card.isVisible():
                logger.debug(f"VIEWPORT: Hiding card {card.card_id} (widget recycling)")
                card.hide()
                QTimer.singleShot(50, lambda: self._show_card(card))

        # Continue simulation
        if self.test_running:
            self.viewport_timer.start(100)

    def _show_card(self, card):
        """Show card after simulated recycling"""
        if self.test_running:
            logger.debug(f"VIEWPORT: Showing card {card.card_id} (widget reuse)")
            card.show()

    def _simulate_image_loading(self):
        """Simulate image loading operations"""
        if not self.test_running:
            return

        logger.debug("IMAGE_LOAD: Processing image loading (frame drops)")

        # Simulate CPU-intensive operation
        import time

        start = time.time()

        # Simulate image processing delay
        time.sleep(0.005)  # 5ms delay to simulate image operations

        end = time.time()
        logger.debug(f"IMAGE_LOAD: Completed in {(end-start)*1000:.1f}ms")

        # Continue simulation
        if self.test_running:
            self.image_loading_timer.start(150)


def main():
    """Run the hover animation issues reproduction test"""
    app = QApplication(sys.argv)

    # Create test window
    test_window = VirtualScrollTest()
    test_window.show()

    print("=== HOVER ANIMATION ISSUES REPRODUCTION TEST ===")
    print("1. Click 'Start Virtual Scroll Test'")
    print("2. Move mouse rapidly over cards")
    print("3. Observe issues in log:")
    print("   - Multiple hover triggers")
    print("   - Animation conflicts")
    print("   - Performance drops")
    print("   - Event propagation issues")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
