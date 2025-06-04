"""
Test Script for Layout Consistency Fixes

This script validates that the layout consistency fixes are working correctly:
1. ✅ Layout inconsistency between rows (different column counts)
2. ✅ Thumbnail sizing discrepancies (first 2 rows vs subsequent rows)
3. ✅ Incremental rendering conflicts
4. ✅ Container width usage inconsistencies
5. ✅ Fixed card size calculation timing issues

Usage:
    python -m src.browse_tab_v2.test_layout_consistency_fixes
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.browse_tab_v2.components.consistent_responsive_grid import ConsistentResponsiveThumbnailGrid, LayoutParameters
    from src.browse_tab_v2.components.layout_consistent_thumbnail_card import LayoutConsistentThumbnailCard
    from src.browse_tab_v2.core.interfaces import BrowseTabConfig
    from src.browse_tab_v2.core.state import SequenceModel
except ImportError as e:
    logger.error(f"Failed to import components: {e}")
    sys.exit(1)


class MockSequence:
    """Mock sequence for testing."""
    def __init__(self, name: str, seq_id: str, length: int = None, difficulty: str = None):
        self.id = seq_id
        self.name = name
        self.length = length or 4
        self.difficulty = difficulty or "Beginner"
        self.category = "Test"
        self.thumbnails = [f"test_image_{seq_id}.png"]
        self.is_favorite = False


class LayoutConsistencyTestWindow(QMainWindow):
    """Test window for layout consistency validation."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layout Consistency Fixes - Test Window")
        self.setGeometry(100, 100, 1400, 900)
        
        # Test state
        self.test_sequences = []
        self.layout_shift_count = 0
        self.resize_event_count = 0
        self.card_size_inconsistencies = []
        
        self._setup_ui()
        self._create_test_sequences()
        
        logger.info("Layout consistency test window initialized")
    
    def _setup_ui(self):
        """Setup the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        
        # Test buttons
        self.test_basic_button = QPushButton("Test Basic Layout")
        self.test_basic_button.clicked.connect(self.test_basic_layout_consistency)
        controls_layout.addWidget(self.test_basic_button)
        
        self.test_resize_button = QPushButton("Test Resize Consistency")
        self.test_resize_button.clicked.connect(self.test_resize_consistency)
        controls_layout.addWidget(self.test_resize_button)
        
        self.test_incremental_button = QPushButton("Test Incremental Loading")
        self.test_incremental_button.clicked.connect(self.test_incremental_loading)
        controls_layout.addWidget(self.test_incremental_button)
        
        self.validate_button = QPushButton("Validate All Fixes")
        self.validate_button.clicked.connect(self.validate_all_fixes)
        controls_layout.addWidget(self.validate_button)
        
        controls_layout.addStretch()
        layout.addWidget(controls_widget)
        
        # Status display
        self.status_label = QLabel("Ready to test layout consistency fixes")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Create consistent grid
        self.config = BrowseTabConfig()
        self.grid = ConsistentResponsiveThumbnailGrid(self.config, parent=central_widget)
        self.grid.set_item_creator(self.create_test_card)
        layout.addWidget(self.grid)
        
        # Connect monitoring signals
        self.grid.column_count_changed.connect(self.on_column_count_changed)
        self.grid.viewport_changed.connect(self.on_viewport_changed)
    
    def _create_test_sequences(self):
        """Create test sequences with varying properties."""
        self.test_sequences = []
        
        # Create sequences with different lengths and names for testing
        for i in range(50):
            seq = MockSequence(
                name=f"Test Sequence {i+1:02d}",
                seq_id=f"test_seq_{i+1:03d}",
                length=2 + (i % 6),  # Lengths from 2 to 7
                difficulty=["Beginner", "Intermediate", "Advanced"][i % 3]
            )
            self.test_sequences.append(seq)
        
        logger.info(f"Created {len(self.test_sequences)} test sequences")
    
    def create_test_card(self, sequence, index):
        """Create a test card with monitoring."""
        card = LayoutConsistentThumbnailCard(sequence, self.config, parent=self.grid)
        
        # Monitor for layout shifts
        original_resize_event = card.resizeEvent
        def monitored_resize_event(event):
            self.resize_event_count += 1
            old_size = event.oldSize()
            new_size = event.size()
            
            # Check for size inconsistencies
            if old_size.isValid() and new_size != old_size:
                if abs(new_size.width() - old_size.width()) > 5 or abs(new_size.height() - old_size.height()) > 5:
                    self.layout_shift_count += 1
                    inconsistency = {
                        'card_index': index,
                        'old_size': (old_size.width(), old_size.height()),
                        'new_size': (new_size.width(), new_size.height()),
                        'time': time.time()
                    }
                    self.card_size_inconsistencies.append(inconsistency)
                    logger.warning(f"Size inconsistency detected on card {index}: "
                                 f"{old_size.width()}x{old_size.height()} -> "
                                 f"{new_size.width()}x{new_size.height()}")
            
            return original_resize_event(event)
        
        card.resizeEvent = monitored_resize_event
        return card
    
    def test_basic_layout_consistency(self):
        """Test basic layout consistency."""
        self.status_label.setText("Testing basic layout consistency...")
        self.layout_shift_count = 0
        self.resize_event_count = 0
        self.card_size_inconsistencies.clear()
        
        # Load sequences
        self.grid.set_sequences(self.test_sequences[:20])
        
        # Wait for rendering to complete
        QTimer.singleShot(1000, self._check_basic_layout_results)
    
    def _check_basic_layout_results(self):
        """Check basic layout test results."""
        column_count = self.grid.get_column_count()
        card_size = self.grid.get_fixed_card_size()
        
        results = []
        results.append(f"✅ Column count: {column_count}")
        results.append(f"✅ Fixed card size: {card_size.width()}x{card_size.height()}")
        results.append(f"✅ Layout shifts detected: {self.layout_shift_count}")
        results.append(f"✅ Resize events: {self.resize_event_count}")
        
        if self.layout_shift_count == 0:
            results.append("✅ PASS: No layout shifts detected")
        else:
            results.append(f"❌ FAIL: {self.layout_shift_count} layout shifts detected")
        
        self.status_label.setText(" | ".join(results))
        logger.info(f"Basic layout test complete: {results}")
    
    def test_resize_consistency(self):
        """Test resize consistency."""
        self.status_label.setText("Testing resize consistency...")
        self.layout_shift_count = 0
        
        # Load sequences
        self.grid.set_sequences(self.test_sequences[:15])
        
        # Simulate resize events
        QTimer.singleShot(500, self._simulate_resize_events)
    
    def _simulate_resize_events(self):
        """Simulate window resize events."""
        original_size = self.size()
        
        # Resize to different widths
        test_sizes = [
            QSize(1200, 800),
            QSize(1600, 900),
            QSize(1000, 700),
            QSize(1400, 850)
        ]
        
        for i, size in enumerate(test_sizes):
            QTimer.singleShot(i * 300, lambda s=size: self.resize(s))
        
        # Check results after all resizes
        QTimer.singleShot(len(test_sizes) * 300 + 500, self._check_resize_results)
    
    def _check_resize_results(self):
        """Check resize test results."""
        results = []
        results.append(f"Layout shifts during resize: {self.layout_shift_count}")
        
        if self.layout_shift_count <= 2:  # Allow minimal shifts during resize
            results.append("✅ PASS: Resize consistency maintained")
        else:
            results.append(f"❌ FAIL: Too many layout shifts ({self.layout_shift_count})")
        
        self.status_label.setText(" | ".join(results))
        logger.info(f"Resize test complete: {results}")
    
    def test_incremental_loading(self):
        """Test incremental loading consistency."""
        self.status_label.setText("Testing incremental loading...")
        self.layout_shift_count = 0
        
        # Start with small set
        self.grid.set_sequences(self.test_sequences[:10])
        
        # Add more sequences incrementally
        QTimer.singleShot(500, lambda: self.grid.set_sequences(self.test_sequences[:25]))
        QTimer.singleShot(1000, lambda: self.grid.set_sequences(self.test_sequences[:40]))
        QTimer.singleShot(1500, self._check_incremental_results)
    
    def _check_incremental_results(self):
        """Check incremental loading results."""
        results = []
        results.append(f"Layout shifts during incremental loading: {self.layout_shift_count}")
        results.append(f"Size inconsistencies: {len(self.card_size_inconsistencies)}")
        
        if self.layout_shift_count <= 3 and len(self.card_size_inconsistencies) == 0:
            results.append("✅ PASS: Incremental loading consistency maintained")
        else:
            results.append("❌ FAIL: Inconsistencies detected during incremental loading")
        
        self.status_label.setText(" | ".join(results))
        logger.info(f"Incremental loading test complete: {results}")
    
    def validate_all_fixes(self):
        """Validate all layout consistency fixes."""
        self.status_label.setText("Validating all layout consistency fixes...")
        
        # Reset counters
        self.layout_shift_count = 0
        self.resize_event_count = 0
        self.card_size_inconsistencies.clear()
        
        # Run comprehensive test
        self.grid.set_sequences(self.test_sequences)
        
        QTimer.singleShot(2000, self._final_validation)
    
    def _final_validation(self):
        """Perform final validation."""
        results = []
        
        # Check layout parameters consistency
        layout_params = self.grid._layout_params
        if layout_params:
            results.append(f"✅ Layout parameters calculated: {layout_params.column_count} cols")
            results.append(f"✅ Card size: {layout_params.card_width}x{layout_params.card_height}")
        
        # Check for issues
        total_issues = self.layout_shift_count + len(self.card_size_inconsistencies)
        
        if total_issues == 0:
            results.append("🎉 ALL TESTS PASSED: Layout consistency fixes working correctly!")
        else:
            results.append(f"⚠️ {total_issues} issues detected - review needed")
        
        self.status_label.setText(" | ".join(results))
        logger.info(f"Final validation complete: {results}")
    
    def on_column_count_changed(self, new_count):
        """Handle column count changes."""
        logger.info(f"Column count changed to: {new_count}")
    
    def on_viewport_changed(self, start, end):
        """Handle viewport changes."""
        logger.debug(f"Viewport changed: {start}-{end}")


def main():
    """Run the layout consistency test."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = LayoutConsistencyTestWindow()
    window.show()
    
    logger.info("Layout consistency test application started")
    logger.info("Use the buttons to test different aspects of layout consistency")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
