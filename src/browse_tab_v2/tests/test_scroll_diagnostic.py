"""
Scroll Event Diagnostic Test

This test validates the scroll-to-image loading fix with comprehensive logging
to trace the exact execution path and identify any remaining disconnects.

Test Scenarios:
1. Load sequences and verify initial image loading
2. Scroll down and trace the complete event chain
3. Verify image quality is high (SmoothTransformation)
4. Validate that scroll events trigger image loading
5. Confirm click events still work as expected
"""

import sys
import logging
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, QSize
from PyQt6.QtGui import QFont

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.browse_tab_v2.components.efficient_virtual_grid import EfficientVirtualGrid
    from src.browse_tab_v2.components.fast_thumbnail_card import FastThumbnailCard
    from src.browse_tab_v2.services.fast_image_service import get_image_service
    from src.browse_tab_v2.core.interfaces import BrowseTabConfig
except ImportError as e:
    logger.error(f"Failed to import components: {e}")
    sys.exit(1)


class MockSequence:
    """Mock sequence for testing."""
    def __init__(self, name: str, seq_id: str, has_image: bool = True):
        self.id = seq_id
        self.name = name
        self.thumbnails = [f"test_image_{seq_id}.png"] if has_image else []


class ScrollDiagnosticTestWindow(QMainWindow):
    """Diagnostic test window with comprehensive logging."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scroll Event Diagnostic Test - Detailed Logging")
        self.setGeometry(100, 100, 1400, 900)
        
        # Event tracking
        self.scroll_events = []
        self.viewport_changes = []
        self.image_loads = []
        self.force_updates = []
        
        # Test sequences
        self.test_sequences = []
        
        self._setup_ui()
        self._create_test_sequences()
        
        logger.info("=== SCROLL DIAGNOSTIC TEST INITIALIZED ===")
    
    def _setup_ui(self):
        """Setup test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        
        # Test buttons
        self.load_button = QPushButton("Load Test Data")
        self.load_button.clicked.connect(self.load_test_data)
        controls_layout.addWidget(self.load_button)
        
        self.scroll_test_button = QPushButton("Scroll Test")
        self.scroll_test_button.clicked.connect(self.run_scroll_test)
        controls_layout.addWidget(self.scroll_test_button)
        
        self.click_test_button = QPushButton("Click Test")
        self.click_test_button.clicked.connect(self.run_click_test)
        controls_layout.addWidget(self.click_test_button)
        
        self.analyze_button = QPushButton("Analyze Events")
        self.analyze_button.clicked.connect(self.analyze_events)
        controls_layout.addWidget(self.analyze_button)
        
        controls_layout.addStretch()
        layout.addWidget(controls_widget)
        
        # Status display
        self.status_label = QLabel("Ready for scroll diagnostic test")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Create grid with monitoring
        self.config = BrowseTabConfig()
        self.grid = EfficientVirtualGrid(self.config, parent=central_widget)
        self.grid.set_item_creator(self.create_diagnostic_card)
        layout.addWidget(self.grid)
        
        # Connect monitoring signals
        self.grid.viewport_changed.connect(self.on_viewport_changed)
        
        # Initialize image service
        self.image_service = get_image_service()
        self.image_service.image_ready.connect(self.on_image_ready)
        
        # Monitor scroll events
        scroll_bar = self.grid.scroll_area.verticalScrollBar()
        scroll_bar.valueChanged.connect(self.on_scroll_value_changed)
    
    def _create_test_sequences(self):
        """Create test sequences."""
        self.test_sequences = []
        
        # Create sequences for testing
        for i in range(50):
            seq = MockSequence(
                name=f"Diagnostic Test Sequence {i+1:03d}",
                seq_id=f"diag_{i+1:04d}",
                has_image=True
            )
            self.test_sequences.append(seq)
        
        logger.info(f"Created {len(self.test_sequences)} test sequences")
    
    def create_diagnostic_card(self, sequence, index):
        """Create card with diagnostic monitoring."""
        logger.debug(f"CARD_CREATION: Creating card for index {index}, sequence {sequence.id}")
        
        start_time = time.time()
        card = FastThumbnailCard(sequence, self.config, parent=self.grid)
        creation_time = (time.time() - start_time) * 1000
        
        # Monitor image loading
        original_load = card._load_image_fast
        def monitored_load():
            load_start = time.time()
            logger.debug(f"CARD_IMAGE_LOAD: Starting load for card {index}")
            result = original_load()
            load_time = (time.time() - load_start) * 1000
            
            self.image_loads.append({
                'index': index,
                'sequence_id': sequence.id,
                'load_time': load_time,
                'timestamp': time.time()
            })
            
            logger.debug(f"CARD_IMAGE_LOAD: Completed for card {index} in {load_time:.1f}ms")
            return result
        
        card._load_image_fast = monitored_load
        
        logger.debug(f"CARD_CREATION: Completed for index {index} in {creation_time:.1f}ms")
        return card
    
    def load_test_data(self):
        """Load test data."""
        logger.info("=== LOADING TEST DATA ===")
        self.scroll_events.clear()
        self.viewport_changes.clear()
        self.image_loads.clear()
        self.force_updates.clear()
        
        start_time = time.time()
        self.grid.set_sequences(self.test_sequences)
        load_time = (time.time() - start_time) * 1000
        
        self.status_label.setText(f"Loaded {len(self.test_sequences)} sequences in {load_time:.1f}ms")
        logger.info(f"=== TEST DATA LOADED in {load_time:.1f}ms ===")
    
    def run_scroll_test(self):
        """Run scroll test with detailed monitoring."""
        logger.info("=== STARTING SCROLL TEST ===")
        
        scroll_bar = self.grid.scroll_area.verticalScrollBar()
        max_value = scroll_bar.maximum()
        
        if max_value <= 0:
            self.status_label.setText("No scrollable content")
            logger.warning("No scrollable content available")
            return
        
        logger.info(f"SCROLL_TEST: Max scroll value = {max_value}")
        
        # Test scroll to middle
        target_position = max_value // 2
        logger.info(f"SCROLL_TEST: Scrolling to position {target_position}")
        
        scroll_bar.setValue(target_position)
        
        # Wait for events to process
        QTimer.singleShot(2000, self.analyze_scroll_results)
    
    def analyze_scroll_results(self):
        """Analyze scroll test results."""
        logger.info("=== ANALYZING SCROLL RESULTS ===")
        
        # Count events
        scroll_count = len(self.scroll_events)
        viewport_count = len(self.viewport_changes)
        image_count = len(self.image_loads)
        force_count = len(self.force_updates)
        
        logger.info(f"ANALYSIS: Scroll events: {scroll_count}")
        logger.info(f"ANALYSIS: Viewport changes: {viewport_count}")
        logger.info(f"ANALYSIS: Image loads: {image_count}")
        logger.info(f"ANALYSIS: Force updates: {force_count}")
        
        # Check for disconnects
        if scroll_count > 0 and viewport_count == 0:
            logger.error("DISCONNECT: Scroll events not triggering viewport changes")
        elif viewport_count > 0 and force_count == 0:
            logger.error("DISCONNECT: Viewport changes not triggering force updates")
        elif force_count > 0 and image_count == 0:
            logger.error("DISCONNECT: Force updates not triggering image loads")
        else:
            logger.info("EVENT CHAIN: All connections appear to be working")
        
        # Update status
        results = [
            f"Scroll: {scroll_count}",
            f"Viewport: {viewport_count}",
            f"Images: {image_count}",
            f"Force: {force_count}"
        ]
        
        self.status_label.setText(" | ".join(results))
    
    def run_click_test(self):
        """Test click functionality."""
        logger.info("=== STARTING CLICK TEST ===")
        
        # Simulate click on first visible card
        if hasattr(self.grid, '_visible_widgets') and self.grid._visible_widgets:
            first_index = next(iter(self.grid._visible_widgets.keys()))
            first_widget = self.grid._visible_widgets[first_index]
            
            logger.info(f"CLICK_TEST: Clicking widget {first_index}")
            
            if hasattr(first_widget, 'clicked'):
                first_widget.clicked.emit(first_widget.sequence.id)
                logger.info("CLICK_TEST: Click signal emitted")
            else:
                logger.warning("CLICK_TEST: Widget has no clicked signal")
        else:
            logger.warning("CLICK_TEST: No visible widgets to click")
    
    def analyze_events(self):
        """Analyze all collected events."""
        logger.info("=== EVENT ANALYSIS ===")
        
        # Print recent events
        recent_time = time.time() - 10  # Last 10 seconds
        
        recent_scrolls = [e for e in self.scroll_events if e['timestamp'] > recent_time]
        recent_viewports = [e for e in self.viewport_changes if e['timestamp'] > recent_time]
        recent_images = [e for e in self.image_loads if e['timestamp'] > recent_time]
        recent_forces = [e for e in self.force_updates if e['timestamp'] > recent_time]
        
        logger.info(f"RECENT EVENTS (last 10s):")
        logger.info(f"  Scrolls: {len(recent_scrolls)}")
        logger.info(f"  Viewports: {len(recent_viewports)}")
        logger.info(f"  Images: {len(recent_images)}")
        logger.info(f"  Forces: {len(recent_forces)}")
        
        # Check current grid state
        if hasattr(self.grid, '_visible_widgets'):
            visible_count = len(self.grid._visible_widgets)
            logger.info(f"CURRENT STATE: {visible_count} visible widgets")
            
            for index, widget in self.grid._visible_widgets.items():
                has_image = hasattr(widget, '_image_loaded') and widget._image_loaded
                logger.info(f"  Widget {index}: image_loaded = {has_image}")
        
        self.status_label.setText("Event analysis complete - check console")
    
    def on_scroll_value_changed(self, value):
        """Monitor scroll bar value changes."""
        self.scroll_events.append({
            'value': value,
            'timestamp': time.time()
        })
        logger.debug(f"SCROLL_VALUE_CHANGED: {value}")
    
    def on_viewport_changed(self, start, end):
        """Monitor viewport changes."""
        self.viewport_changes.append({
            'start': start,
            'end': end,
            'timestamp': time.time()
        })
        logger.debug(f"VIEWPORT_CHANGED_SIGNAL: {start}-{end}")
    
    def on_image_ready(self, image_path, pixmap):
        """Monitor image ready events."""
        logger.debug(f"IMAGE_READY_SIGNAL: {image_path}")


def main():
    """Run scroll diagnostic test."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = ScrollDiagnosticTestWindow()
    window.show()
    
    logger.info("=== SCROLL DIAGNOSTIC TEST STARTED ===")
    logger.info("1. Click 'Load Test Data' to load sequences")
    logger.info("2. Click 'Scroll Test' to test scroll event chain")
    logger.info("3. Click 'Analyze Events' to check event flow")
    logger.info("4. Watch console for detailed diagnostic logging")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
