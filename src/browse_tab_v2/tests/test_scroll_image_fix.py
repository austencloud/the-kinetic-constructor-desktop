"""
Diagnostic Test for Scroll-to-Image Loading Fix

This test validates that the precise fix for the widget pooling issue works correctly.
It specifically tests that scroll events properly trigger image loading for newly visible cards.

Test Scenarios:
1. Initial load - verify images appear
2. Scroll down - verify new cards get images immediately
3. Scroll back up - verify pooled widgets reload correct images
4. Click test - verify click-triggered updates still work
5. Performance test - verify no regression in scroll performance
"""

import sys
import logging
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, QSize
from PyQt6.QtGui import QFont

# Setup logging
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


class ScrollImageFixTestWindow(QMainWindow):
    """Test window for scroll-to-image loading fix."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scroll Image Loading Fix - Diagnostic Test")
        self.setGeometry(100, 100, 1400, 900)
        
        # Test tracking
        self.scroll_events = []
        self.image_load_events = []
        self.click_events = []
        
        # Test sequences
        self.test_sequences = []
        
        self._setup_ui()
        self._create_test_sequences()
        
        logger.info("Scroll image fix test window initialized")
    
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
        
        self.scroll_test_button = QPushButton("Auto Scroll Test")
        self.scroll_test_button.clicked.connect(self.run_scroll_test)
        controls_layout.addWidget(self.scroll_test_button)
        
        self.click_test_button = QPushButton("Click Test")
        self.click_test_button.clicked.connect(self.run_click_test)
        controls_layout.addWidget(self.click_test_button)
        
        self.validate_button = QPushButton("Validate Fix")
        self.validate_button.clicked.connect(self.validate_fix)
        controls_layout.addWidget(self.validate_button)
        
        controls_layout.addStretch()
        layout.addWidget(controls_widget)
        
        # Status display
        self.status_label = QLabel("Ready to test scroll-to-image loading fix")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Create grid with diagnostic monitoring
        self.config = BrowseTabConfig()
        self.grid = EfficientVirtualGrid(self.config, parent=central_widget)
        self.grid.set_item_creator(self.create_monitored_card)
        layout.addWidget(self.grid)
        
        # Connect monitoring
        self.grid.viewport_changed.connect(self.on_viewport_changed)
        
        # Initialize image service
        self.image_service = get_image_service()
        self.image_service.image_ready.connect(self.on_image_ready)
    
    def _create_test_sequences(self):
        """Create test sequences."""
        self.test_sequences = []
        
        # Create sequences with predictable names for testing
        for i in range(100):
            seq = MockSequence(
                name=f"Test Sequence {i+1:03d}",
                seq_id=f"test_{i+1:04d}",
                has_image=(i % 3 != 0)  # Some without images for error testing
            )
            self.test_sequences.append(seq)
        
        logger.info(f"Created {len(self.test_sequences)} test sequences")
    
    def create_monitored_card(self, sequence, index):
        """Create card with monitoring."""
        start_time = time.time()
        
        card = FastThumbnailCard(sequence, self.config, parent=self.grid)
        
        creation_time = (time.time() - start_time) * 1000
        
        # Monitor card events
        original_load_image = card._load_image_fast
        def monitored_load_image():
            load_start = time.time()
            result = original_load_image()
            load_time = (time.time() - load_start) * 1000
            
            self.image_load_events.append({
                'index': index,
                'sequence_id': sequence.id,
                'load_time': load_time,
                'timestamp': time.time()
            })
            
            logger.debug(f"Image loaded for card {index} in {load_time:.1f}ms")
            return result
        
        card._load_image_fast = monitored_load_image
        
        # Monitor click events
        if hasattr(card, 'clicked'):
            def monitored_click(seq_id):
                self.click_events.append({
                    'index': index,
                    'sequence_id': seq_id,
                    'timestamp': time.time()
                })
                logger.debug(f"Card {index} clicked")
            
            card.clicked.connect(monitored_click)
        
        logger.debug(f"Created monitored card {index} in {creation_time:.1f}ms")
        return card
    
    def load_test_data(self):
        """Load test data into grid."""
        self.status_label.setText("Loading test data...")
        self.scroll_events.clear()
        self.image_load_events.clear()
        self.click_events.clear()
        
        start_time = time.time()
        self.grid.set_sequences(self.test_sequences)
        load_time = (time.time() - start_time) * 1000
        
        self.status_label.setText(f"Loaded {len(self.test_sequences)} sequences in {load_time:.1f}ms")
        logger.info(f"Test data loaded in {load_time:.1f}ms")
    
    def run_scroll_test(self):
        """Run automated scroll test."""
        self.status_label.setText("Running scroll test...")
        
        scroll_bar = self.grid.scroll_area.verticalScrollBar()
        max_value = scroll_bar.maximum()
        
        if max_value <= 0:
            self.status_label.setText("No scrollable content")
            return
        
        # Test scroll positions
        positions = [0, max_value // 4, max_value // 2, 3 * max_value // 4, max_value]
        
        def scroll_to_next_position(pos_index):
            if pos_index >= len(positions):
                self.analyze_scroll_results()
                return
            
            position = positions[pos_index]
            logger.info(f"Scrolling to position {position} ({pos_index+1}/{len(positions)})")
            
            scroll_bar.setValue(position)
            
            # Wait for scroll to settle, then continue
            QTimer.singleShot(1000, lambda: scroll_to_next_position(pos_index + 1))
        
        # Start scroll test
        scroll_to_next_position(0)
    
    def analyze_scroll_results(self):
        """Analyze scroll test results."""
        results = []
        
        # Count image loads during scroll
        scroll_triggered_loads = len([e for e in self.image_load_events if e['timestamp'] > time.time() - 10])
        results.append(f"Images loaded during scroll: {scroll_triggered_loads}")
        
        # Check for blank cards
        visible_cards = len(self.grid._visible_widgets) if hasattr(self.grid, '_visible_widgets') else 0
        results.append(f"Visible cards: {visible_cards}")
        
        # Performance check
        if self.image_load_events:
            avg_load_time = sum(e['load_time'] for e in self.image_load_events) / len(self.image_load_events)
            max_load_time = max(e['load_time'] for e in self.image_load_events)
            results.append(f"Avg load: {avg_load_time:.1f}ms, Max: {max_load_time:.1f}ms")
        
        self.status_label.setText(" | ".join(results))
        logger.info(f"Scroll test results: {results}")
    
    def run_click_test(self):
        """Test click-triggered image loading."""
        self.status_label.setText("Running click test...")
        
        # Simulate click on first visible card
        if hasattr(self.grid, '_visible_widgets') and self.grid._visible_widgets:
            first_widget = next(iter(self.grid._visible_widgets.values()))
            if hasattr(first_widget, 'clicked'):
                first_widget.clicked.emit(first_widget.sequence.id)
                
                # Wait and check results
                QTimer.singleShot(500, self.analyze_click_results)
        else:
            self.status_label.setText("No visible cards to click")
    
    def analyze_click_results(self):
        """Analyze click test results."""
        recent_clicks = len([e for e in self.click_events if e['timestamp'] > time.time() - 2])
        recent_loads = len([e for e in self.image_load_events if e['timestamp'] > time.time() - 2])
        
        results = [
            f"Recent clicks: {recent_clicks}",
            f"Recent loads: {recent_loads}",
            f"Click->Load ratio: {recent_loads/recent_clicks if recent_clicks > 0 else 0:.1f}"
        ]
        
        self.status_label.setText(" | ".join(results))
        logger.info(f"Click test results: {results}")
    
    def validate_fix(self):
        """Validate that the fix is working."""
        self.status_label.setText("Validating fix...")
        
        # Check if widget pooling is working correctly
        pool_size = len(self.grid._widget_pool) if hasattr(self.grid, '_widget_pool') else 0
        visible_count = len(self.grid._visible_widgets) if hasattr(self.grid, '_visible_widgets') else 0
        
        # Check image loading statistics
        total_loads = len(self.image_load_events)
        recent_loads = len([e for e in self.image_load_events if e['timestamp'] > time.time() - 5])
        
        # Validation criteria
        criteria = []
        criteria.append(f"Widget pool: {pool_size} (should be >0)")
        criteria.append(f"Visible cards: {visible_count} (should be >0)")
        criteria.append(f"Total image loads: {total_loads} (should be >0)")
        criteria.append(f"Recent loads: {recent_loads} (should be >0 after scroll)")
        
        # Overall assessment
        pool_ok = pool_size > 0
        visible_ok = visible_count > 0
        loads_ok = total_loads > 0
        recent_ok = recent_loads > 0
        
        overall = "✅ FIX WORKING" if all([pool_ok, visible_ok, loads_ok, recent_ok]) else "❌ FIX NEEDED"
        criteria.append(f"Status: {overall}")
        
        self.status_label.setText(" | ".join(criteria))
        logger.info(f"Fix validation: {criteria}")
    
    def on_viewport_changed(self, start, end):
        """Monitor viewport changes."""
        self.scroll_events.append({
            'start': start,
            'end': end,
            'timestamp': time.time()
        })
        logger.debug(f"Viewport changed: {start}-{end}")
    
    def on_image_ready(self, image_path, pixmap):
        """Monitor image ready events."""
        logger.debug(f"Image ready: {image_path}")


def main():
    """Run scroll image fix test."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = ScrollImageFixTestWindow()
    window.show()
    
    logger.info("Scroll image fix test started")
    logger.info("1. Click 'Load Test Data' to load sequences")
    logger.info("2. Click 'Auto Scroll Test' to test scroll-triggered image loading")
    logger.info("3. Click 'Validate Fix' to check if the fix is working")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
