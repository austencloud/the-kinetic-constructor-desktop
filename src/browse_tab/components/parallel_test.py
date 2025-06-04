"""
Parallel Processing Test for Widget Creation.

Tests the parallel widget creation system to verify it's working correctly.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

from browse_tab.components.grid_view import WidgetCreationWorker, WorkerSignals
from browse_tab.core.interfaces import BrowseTabConfig

logger = logging.getLogger(__name__)


class MockSequenceModel:
    """Mock sequence model for testing."""
    
    def __init__(self, sequence_id: str, name: str):
        self.id = sequence_id
        self.name = name
        self.thumbnails = [f"test_image_{sequence_id}.png"]
        self.difficulty = "Medium"
        self.length = 10
        self.author = "Test Author"


class ParallelTestWindow(QMainWindow):
    """Test window for parallel processing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parallel Processing Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test components
        self.config = BrowseTabConfig()
        self.worker_signals = WorkerSignals()
        self.worker_signals.batch_ready.connect(self.on_batch_ready)
        self.worker_signals.batch_error.connect(self.on_batch_error)
        
        # Start test after window is shown
        QTimer.singleShot(100, self.start_parallel_test)
    
    def create_test_sequences(self, count: int):
        """Create test sequences for parallel processing."""
        sequences = []
        for i in range(count):
            sequence = MockSequenceModel(f"seq_{i:03d}", f"Test Sequence {i+1}")
            sequences.append(sequence)
        return sequences
    
    def start_parallel_test(self):
        """Start the parallel processing test."""
        logger.info("🚀 Starting Parallel Processing Test")
        logger.info("=" * 60)
        
        # Test with 10 sequences
        test_sequences = self.create_test_sequences(10)
        
        logger.info(f"Testing parallel processing with {len(test_sequences)} sequences")
        
        try:
            # Create worker
            worker = WidgetCreationWorker(
                test_sequences, self.config, 0, self.worker_signals
            )
            
            logger.info("✅ Worker created successfully")
            
            # Run worker directly (not in thread pool for testing)
            worker.run()
            
        except Exception as e:
            logger.error(f"❌ Worker creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def on_batch_ready(self, widget_data_list):
        """Handle batch ready signal."""
        logger.info(f"✅ Batch ready with {len(widget_data_list)} widget data items")
        
        for i, widget_data in enumerate(widget_data_list):
            logger.info(f"  Widget {i+1}: {widget_data.get('title', 'Unknown')}")
            logger.info(f"    Index: {widget_data.get('index', 'Unknown')}")
            logger.info(f"    Info: {widget_data.get('info', 'No info')}")
        
        logger.info("🎯 Parallel processing test completed successfully!")
        
        # Schedule window close
        QTimer.singleShot(2000, self.close)
    
    def on_batch_error(self, error_message):
        """Handle batch error signal."""
        logger.error(f"❌ Batch error: {error_message}")
        
        # Schedule window close
        QTimer.singleShot(2000, self.close)


def run_parallel_test():
    """Run the parallel processing test."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create test window
    window = ParallelTestWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    run_parallel_test()
