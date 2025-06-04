"""
Test script for the thumbnail size flickering fix in BrowseTabV2.

This script validates that thumbnails maintain consistent dimensions during
chunked loading and do not experience size flickering or oversizing issues.
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


class FlickeringTestWindow(QMainWindow):
    """Test window for thumbnail size flickering fix."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thumbnail Size Flickering Fix Test")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Testing thumbnail size flickering fix")
        layout.addWidget(self.status_label)
        
        # Control buttons
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        self.test_button = QPushButton("Start Flickering Test")
        self.test_button.clicked.connect(self.start_test)
        controls_layout.addWidget(self.test_button)
        
        self.scroll_test_button = QPushButton("Test Scroll-Induced Loading")
        self.scroll_test_button.clicked.connect(self.test_scroll_loading)
        controls_layout.addWidget(self.scroll_test_button)
        
        self.rapid_resize_button = QPushButton("Test Rapid Window Resizing")
        self.rapid_resize_button.clicked.connect(self.test_rapid_resizing)
        controls_layout.addWidget(self.rapid_resize_button)
        
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
        
        # Test data and monitoring
        self.test_sequences = []
        self.size_change_count = 0
        self.unwanted_resize_count = 0
        self.oversizing_events = 0
        self.test_cycle = 0
        
        self.create_test_data()
        
        logger.info("Flickering test window initialized")
    
    def create_test_data(self):
        """Create test sequences with varying aspect ratios."""
        # Create sequences with different aspect ratios to trigger potential flickering
        sequence_data = [
            ("Landscape_A", 4, ["test_landscape_1.png"]),
            ("Portrait_A", 6, ["test_portrait_1.png"]),
            ("Square_A", 8, ["test_square_1.png"]),
            ("Landscape_B", 4, ["test_landscape_2.png"]),
            ("Portrait_B", 6, ["test_portrait_2.png"]),
            ("Square_B", 8, ["test_square_2.png"]),
            ("Wide_Landscape", 12, ["test_wide_landscape.png"]),
            ("Tall_Portrait", 16, ["test_tall_portrait.png"]),
            ("Large_Square", 20, ["test_large_square.png"]),
            ("Mixed_A", 4, ["test_mixed_1.png"]),
            ("Mixed_B", 6, ["test_mixed_2.png"]),
            ("Mixed_C", 8, ["test_mixed_3.png"]),
        ] * 5  # Multiply to create more test data
        
        # Create SequenceModel objects
        for i, (name, length, thumbnails) in enumerate(sequence_data):
            sequence = SequenceModel(
                id=f"{name}_{i}",
                name=f"{name}_{i}",
                thumbnails=thumbnails,
                difficulty=min(max(1, length // 3), 5),
                length=length,
                author="Test",
                tags=[f"length_{length}", "test"],
                is_favorite=False,
                metadata={"test": True, "length": length, "aspect_test": True}
            )
            self.test_sequences.append(sequence)
        
        logger.info(f"Created {len(self.test_sequences)} test sequences with mixed aspect ratios")
    
    def create_thumbnail_card(self, sequence, index):
        """Create a thumbnail card with enhanced monitoring."""
        card = ModernThumbnailCard(sequence, self.config, parent=self.grid)
        
        # Monitor for any size changes to detect flickering
        original_resize_event = card.resizeEvent
        def monitored_resize_event(event):
            old_size = event.oldSize()
            new_size = event.size()
            
            # Count all size changes
            self.size_change_count += 1
            
            # Check for unwanted size changes (not matching fixed dimensions)
            fixed_size = self.grid.get_fixed_card_size()
            if (fixed_size and old_size.isValid() and
                (new_size.width() != fixed_size.width() or 
                 new_size.height() != fixed_size.height())):
                
                self.unwanted_resize_count += 1
                logger.warning(
                    f"FLICKERING DETECTED on card {index}: "
                    f"{old_size.width()}x{old_size.height()} -> "
                    f"{new_size.width()}x{new_size.height()}, "
                    f"expected: {fixed_size.width()}x{fixed_size.height()}"
                )
            
            # Check for oversizing (larger than expected)
            if (fixed_size and 
                (new_size.width() > fixed_size.width() * 1.1 or 
                 new_size.height() > fixed_size.height() * 1.1)):
                
                self.oversizing_events += 1
                logger.error(
                    f"OVERSIZING DETECTED on card {index}: "
                    f"{new_size.width()}x{new_size.height()} vs expected "
                    f"{fixed_size.width()}x{fixed_size.height()}"
                )
            
            return original_resize_event(event)
        
        card.resizeEvent = monitored_resize_event
        return card
    
    def start_test(self):
        """Start the flickering test."""
        self.test_button.setEnabled(False)
        self.size_change_count = 0
        self.unwanted_resize_count = 0
        self.oversizing_events = 0
        self.test_cycle += 1
        
        self.status_label.setText(f"Starting flickering test cycle {self.test_cycle}...")
        
        # Set sequences to trigger chunked loading
        logger.info(f"Starting test cycle {self.test_cycle} with {len(self.test_sequences)} sequences")
        self.grid.set_sequences(self.test_sequences)
        
        # Monitor fixed card size
        fixed_size = self.grid.get_fixed_card_size()
        if fixed_size:
            logger.info(f"Fixed card size: {fixed_size.width()}x{fixed_size.height()}")
            self.status_label.setText(
                f"Test cycle {self.test_cycle}: Fixed size {fixed_size.width()}x{fixed_size.height()}, "
                f"Layout locked: {self.grid.is_layout_locked()}"
            )
        else:
            logger.warning("Fixed card size not calculated!")
    
    def test_scroll_loading(self):
        """Test scroll-induced lazy loading for flickering."""
        if not self.grid.get_chunked_loader().is_loading():
            self.status_label.setText("Simulating scroll-induced loading...")
            
            # Simulate scroll by triggering viewport updates
            for i in range(5):
                QTimer.singleShot(i * 200, lambda: self.grid._render_visible_items())
            
            logger.info("Scroll-induced loading test triggered")
        else:
            self.status_label.setText("Loading in progress - scroll test skipped")
    
    def test_rapid_resizing(self):
        """Test rapid window resizing during loading."""
        if self.grid.get_chunked_loader().is_loading():
            self.status_label.setText("Testing rapid resizing during loading...")
            
            # Perform rapid resizes
            for i in range(10):
                QTimer.singleShot(i * 100, self.perform_resize)
            
            logger.info("Rapid resizing test started")
        else:
            self.status_label.setText("No loading in progress - start test first")
    
    def perform_resize(self):
        """Perform a single resize operation."""
        current_size = self.size()
        new_width = current_size.width() + (20 if self.size_change_count % 2 == 0 else -20)
        new_height = current_size.height() + (15 if self.size_change_count % 2 == 0 else -15)
        self.resize(new_width, new_height)
    
    def on_loading_started(self, total_count: int):
        """Handle loading started signal."""
        self.status_label.setText(
            f"Loading started: {total_count} images, "
            f"Size changes: {self.size_change_count}, "
            f"Layout locked: {self.grid.is_layout_locked()}"
        )
        logger.info(f"Loading started: {total_count} images")
    
    def on_loading_progress(self, current: int, total: int):
        """Handle loading progress signal."""
        progress = (current / total) * 100 if total > 0 else 0
        self.status_label.setText(
            f"Progress: {current}/{total} ({progress:.1f}%), "
            f"Size changes: {self.size_change_count}, "
            f"Unwanted resizes: {self.unwanted_resize_count}, "
            f"Oversizing events: {self.oversizing_events}"
        )
    
    def on_loading_finished(self, success: bool):
        """Handle loading finished signal."""
        status = "completed successfully" if success else "failed"
        self.status_label.setText(
            f"Loading {status}! "
            f"Total size changes: {self.size_change_count}, "
            f"Unwanted resizes: {self.unwanted_resize_count}, "
            f"Oversizing events: {self.oversizing_events}"
        )
        self.test_button.setEnabled(True)
        
        # Validate results
        if self.unwanted_resize_count == 0:
            logger.info("✅ SUCCESS: Zero unwanted resize events detected!")
        else:
            logger.warning(f"❌ FAILURE: {self.unwanted_resize_count} unwanted resize events detected")
        
        if self.oversizing_events == 0:
            logger.info("✅ SUCCESS: Zero oversizing events detected!")
        else:
            logger.warning(f"❌ FAILURE: {self.oversizing_events} oversizing events detected")
        
        logger.info(
            f"Test cycle {self.test_cycle} completed - "
            f"Size changes: {self.size_change_count}, "
            f"Unwanted resizes: {self.unwanted_resize_count}, "
            f"Oversizing: {self.oversizing_events}"
        )


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = FlickeringTestWindow()
    window.show()
    
    # Auto-start test after a short delay
    QTimer.singleShot(1000, window.start_test)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
