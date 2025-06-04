"""
Test script for the chunked image loading system.

This script validates the PyQt6-compatible chunked synchronous loading system
to ensure it works correctly with ModernThumbnailCard components.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.browse_tab_v2.services.chunked_image_loader import ChunkedImageLoadingManager
from src.browse_tab_v2.components.modern_thumbnail_card import ModernThumbnailCard
from src.browse_tab_v2.core.interfaces import BrowseTabConfig
from src.browse_tab_v2.core.state import SequenceModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSequence:
    """Mock sequence for testing."""
    def __init__(self, name: str, thumbnails: list):
        self.id = name
        self.name = name
        self.thumbnails = thumbnails
        self.difficulty = "Medium"
        self.length = 8
        self.category = "Test"


class ChunkedLoadingTestWindow(QMainWindow):
    """Test window for chunked loading system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chunked Loading Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Ready to test chunked loading")
        layout.addWidget(self.status_label)
        
        # Test button
        self.test_button = QPushButton("Start Chunked Loading Test")
        self.test_button.clicked.connect(self.start_test)
        layout.addWidget(self.test_button)
        
        # Container for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        layout.addWidget(self.cards_container)
        
        # Create chunked loader
        self.chunked_loader = ChunkedImageLoadingManager(chunk_size=3, parent=self)
        self.chunked_loader.loading_started.connect(self.on_loading_started)
        self.chunked_loader.loading_progress.connect(self.on_loading_progress)
        self.chunked_loader.loading_finished.connect(self.on_loading_finished)
        self.chunked_loader.batch_completed.connect(self.on_batch_completed)
        
        # Test data
        self.test_cards = []
        self.create_test_data()
        
        logger.info("Test window initialized")
    
    def create_test_data(self):
        """Create test sequences and cards."""
        # Create mock sequences
        test_sequences = []
        for i in range(10):
            # Use placeholder images or create simple test images
            thumbnails = [f"test_image_{i}.png"]  # These don't need to exist for this test
            sequence = MockSequence(f"Test Sequence {i+1}", thumbnails)
            test_sequences.append(sequence)
        
        # Create cards
        config = BrowseTabConfig()
        for i, sequence in enumerate(test_sequences):
            card = ModernThumbnailCard(sequence, config, parent=self.cards_container)
            card.set_chunked_loading_manager(self.chunked_loader)
            self.test_cards.append(card)
            self.cards_layout.addWidget(card)
        
        logger.info(f"Created {len(self.test_cards)} test cards")
    
    def start_test(self):
        """Start the chunked loading test."""
        self.test_button.setEnabled(False)
        self.status_label.setText("Starting chunked loading test...")
        
        # Prepare card-path pairs for testing
        card_path_pairs = []
        for i, card in enumerate(self.test_cards):
            # Use a placeholder path - the test focuses on the chunking mechanism
            test_path = f"test_image_{i}.png"
            card_path_pairs.append((card, test_path))
        
        # Start chunked loading
        logger.info(f"Starting chunked loading test with {len(card_path_pairs)} items")
        self.chunked_loader.queue_multiple_loads(card_path_pairs)
    
    def on_loading_started(self, total_count: int):
        """Handle loading started signal."""
        self.status_label.setText(f"Loading started: {total_count} items")
        logger.info(f"Loading started: {total_count} items")
    
    def on_loading_progress(self, current: int, total: int):
        """Handle loading progress signal."""
        progress = (current / total) * 100 if total > 0 else 0
        self.status_label.setText(f"Loading progress: {current}/{total} ({progress:.1f}%)")
        logger.info(f"Loading progress: {current}/{total} ({progress:.1f}%)")
    
    def on_loading_finished(self, success: bool):
        """Handle loading finished signal."""
        status = "completed successfully" if success else "failed"
        self.status_label.setText(f"Loading {status}")
        self.test_button.setEnabled(True)
        logger.info(f"Loading {status}")
        
        # Show failed loads if any
        failed_loads = self.chunked_loader.get_failed_loads()
        if failed_loads:
            logger.warning(f"Failed loads: {len(failed_loads)}")
            for path, error in failed_loads:
                logger.warning(f"  {path}: {error}")
    
    def on_batch_completed(self, batch_number: int):
        """Handle batch completion signal."""
        logger.info(f"Batch {batch_number} completed")


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = ChunkedLoadingTestWindow()
    window.show()
    
    # Auto-start test after a short delay
    QTimer.singleShot(1000, window.start_test)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
