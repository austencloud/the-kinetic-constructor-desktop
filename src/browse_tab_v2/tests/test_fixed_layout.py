"""
Test script for the fixed layout system in BrowseTabV2.

This script validates the pre-calculated fixed layout system with length-based sorting
and aspect-ratio-aware image scaling to ensure zero layout shifts during chunked loading.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer, QSize

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.browse_tab_v2.components.responsive_thumbnail_grid import ResponsiveThumbnailGrid
from src.browse_tab_v2.components.modern_thumbnail_card import ModernThumbnailCard
from src.browse_tab_v2.core.interfaces import BrowseTabConfig
from src.browse_tab_v2.core.state import SequenceModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSequence:
    """Mock sequence for testing with different lengths and aspect ratios."""
    def __init__(self, name: str, length: int, thumbnails: list):
        self.id = f"{name}_{length}_{hash(name) % 1000}"
        self.name = name
        self.length = length
        self.thumbnails = thumbnails
        self.difficulty = min(max(1, length // 2), 5)
        self.author = "Test"
        self.tags = [f"length_{length}"]
        self.is_favorite = False
        self.metadata = {"test": True}


class FixedLayoutTestWindow(QMainWindow):
    """Test window for fixed layout system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fixed Layout System Test")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Testing fixed layout system with length-based sorting")
        layout.addWidget(self.status_label)
        
        # Control buttons
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        self.test_button = QPushButton("Start Fixed Layout Test")
        self.test_button.clicked.connect(self.start_test)
        controls_layout.addWidget(self.test_button)
        
        self.resize_button = QPushButton("Test Resize During Loading")
        self.resize_button.clicked.connect(self.test_resize_during_loading)
        controls_layout.addWidget(self.resize_button)
        
        layout.addWidget(controls_widget)
        
        # Create responsive thumbnail grid
        self.config = BrowseTabConfig()
        self.grid = ResponsiveThumbnailGrid(self.config, parent=central_widget)
        self.grid.set_item_creator(self.create_thumbnail_card)
        layout.addWidget(self.grid)
        
        # Connect signals for monitoring
        self.grid.get_chunked_loader().loading_started.connect(self.on_loading_started)
        self.grid.get_chunked_loader().loading_progress.connect(self.on_loading_progress)
        self.grid.get_chunked_loader().loading_finished.connect(self.on_loading_finished)
        
        # Test data
        self.test_sequences = []
        self.resize_count = 0
        self.layout_shift_count = 0
        
        self.create_test_data()
        
        logger.info("Fixed layout test window initialized")
    
    def create_test_data(self):
        """Create test sequences with varying lengths for sorting validation."""
        # Create sequences with different lengths to test sorting
        sequence_data = [
            ("Alpha", 4, ["test_4_landscape.png"]),
            ("Beta", 8, ["test_8_portrait.png"]),
            ("Gamma", 4, ["test_4_square.png"]),
            ("Delta", 6, ["test_6_landscape.png"]),
            ("Epsilon", 8, ["test_8_landscape.png"]),
            ("Zeta", 4, ["test_4_portrait.png"]),
            ("Eta", 6, ["test_6_portrait.png"]),
            ("Theta", 8, ["test_8_square.png"]),
            ("Iota", 6, ["test_6_square.png"]),
            ("Kappa", 4, ["test_4_mixed.png"]),
            ("Lambda", 12, ["test_12_landscape.png"]),
            ("Mu", 16, ["test_16_portrait.png"]),
            ("Nu", 12, ["test_12_square.png"]),
            ("Xi", 16, ["test_16_landscape.png"]),
            ("Omicron", 12, ["test_12_portrait.png"]),
        ]
        
        # Create SequenceModel objects
        for name, length, thumbnails in sequence_data:
            sequence = SequenceModel(
                id=f"{name}_{length}",
                name=name,
                thumbnails=thumbnails,
                difficulty=min(max(1, length // 3), 5),
                length=length,
                author="Test",
                tags=[f"length_{length}"],
                is_favorite=False,
                metadata={"test": True, "length": length}
            )
            self.test_sequences.append(sequence)
        
        logger.info(f"Created {len(self.test_sequences)} test sequences with varying lengths")
    
    def create_thumbnail_card(self, sequence, index):
        """Create a thumbnail card for testing."""
        card = ModernThumbnailCard(sequence, self.config, parent=self.grid)
        
        # Monitor for resize events to detect layout shifts
        original_resize_event = card.resizeEvent
        def monitored_resize_event(event):
            self.layout_shift_count += 1
            logger.warning(f"Layout shift detected on card {index}: {event.oldSize()} -> {event.size()}")
            return original_resize_event(event)
        card.resizeEvent = monitored_resize_event
        
        return card
    
    def start_test(self):
        """Start the fixed layout test."""
        self.test_button.setEnabled(False)
        self.resize_count = 0
        self.layout_shift_count = 0
        
        self.status_label.setText("Starting fixed layout test with length-based sorting...")
        
        # Set sequences - this should trigger length-based sorting and fixed layout calculation
        logger.info("Setting sequences with length-based sorting")
        self.grid.set_sequences(self.test_sequences)
        
        # Monitor fixed card size
        fixed_size = self.grid.get_fixed_card_size()
        if fixed_size:
            logger.info(f"Fixed card size calculated: {fixed_size.width()}x{fixed_size.height()}")
            self.status_label.setText(
                f"Fixed layout active: {fixed_size.width()}x{fixed_size.height()} cards, "
                f"Layout locked: {self.grid.is_layout_locked()}"
            )
        else:
            logger.warning("Fixed card size not calculated!")
            self.status_label.setText("WARNING: Fixed card size not calculated!")
    
    def test_resize_during_loading(self):
        """Test resizing the window during chunked loading."""
        if not self.grid.get_chunked_loader().is_loading():
            self.status_label.setText("No loading in progress - start test first")
            return
        
        # Resize the window multiple times during loading
        self.resize_count += 1
        current_size = self.size()
        new_width = current_size.width() + (50 if self.resize_count % 2 == 0 else -50)
        new_height = current_size.height() + (30 if self.resize_count % 2 == 0 else -30)
        
        logger.info(f"Resize test {self.resize_count}: {current_size.width()}x{current_size.height()} -> {new_width}x{new_height}")
        self.resize(new_width, new_height)
        
        # Schedule another resize if loading is still in progress
        if self.resize_count < 5:
            QTimer.singleShot(200, self.test_resize_during_loading)
    
    def on_loading_started(self, total_count: int):
        """Handle loading started signal."""
        self.status_label.setText(f"Loading started: {total_count} images, Layout locked: {self.grid.is_layout_locked()}")
        logger.info(f"Loading started: {total_count} images, Layout locked: {self.grid.is_layout_locked()}")
    
    def on_loading_progress(self, current: int, total: int):
        """Handle loading progress signal."""
        progress = (current / total) * 100 if total > 0 else 0
        self.status_label.setText(
            f"Loading progress: {current}/{total} ({progress:.1f}%), "
            f"Layout shifts: {self.layout_shift_count}, "
            f"Layout locked: {self.grid.is_layout_locked()}"
        )
    
    def on_loading_finished(self, success: bool):
        """Handle loading finished signal."""
        status = "completed successfully" if success else "failed"
        self.status_label.setText(
            f"Loading {status}! Layout shifts detected: {self.layout_shift_count}, "
            f"Layout locked: {self.grid.is_layout_locked()}"
        )
        self.test_button.setEnabled(True)
        
        # Validate results
        if self.layout_shift_count == 0:
            logger.info("✅ SUCCESS: Zero layout shifts detected during chunked loading!")
        else:
            logger.warning(f"❌ FAILURE: {self.layout_shift_count} layout shifts detected during loading")
        
        # Check if sequences are sorted by length
        sequences = self.grid._sequences
        if sequences:
            lengths = [seq.length for seq in sequences]
            is_sorted = all(lengths[i] <= lengths[i+1] for i in range(len(lengths)-1))
            if is_sorted:
                logger.info("✅ SUCCESS: Sequences are correctly sorted by length")
            else:
                logger.warning(f"❌ FAILURE: Sequences not sorted by length: {lengths}")
        
        logger.info(f"Test completed - Layout shifts: {self.layout_shift_count}, Resize events: {self.resize_count}")


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = FixedLayoutTestWindow()
    window.show()
    
    # Auto-start test after a short delay
    QTimer.singleShot(1000, window.start_test)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
