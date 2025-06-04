"""
Performance Test for Grid View Widget Creation.

Tests the optimized parallel widget creation system to verify 120fps performance targets.
Measures widget creation times and compares against performance benchmarks.

Performance Targets:
- Widget batch creation: ≤8.33ms per batch (120fps)
- Image loading: ≤50ms per image
- Total widget creation for 372 items: <3 seconds
- Zero UI blocking during widget creation process
"""

import logging
import time
import sys
from typing import List
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, QElapsedTimer

from browse_tab.components.grid_view import GridView
from browse_tab.core.interfaces import SequenceModel, BrowseTabConfig

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


class PerformanceTestWindow(QMainWindow):
    """Test window for performance testing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid View Performance Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create grid view
        self.config = BrowseTabConfig()
        self.grid_view = GridView(config=self.config, parent=central_widget)
        layout.addWidget(self.grid_view)
        
        # Performance tracking
        self.test_timer = QElapsedTimer()
        self.batch_times = []
        self.total_widgets = 0
        
        # Connect signals
        self.grid_view.content_ready.connect(self.on_content_ready)
        
        # Start test after window is shown
        QTimer.singleShot(100, self.start_performance_test)
    
    def create_test_sequences(self, count: int) -> List[SequenceModel]:
        """Create test sequences for performance testing."""
        sequences = []
        for i in range(count):
            sequence = MockSequenceModel(f"seq_{i:03d}", f"Test Sequence {i+1}")
            sequences.append(sequence)
        return sequences
    
    def start_performance_test(self):
        """Start the performance test."""
        logger.info("🚀 Starting Grid View Performance Test")
        logger.info("=" * 60)
        
        # Test with 372 sequences (real-world scenario)
        test_sequences = self.create_test_sequences(372)
        self.total_widgets = len(test_sequences)
        
        logger.info(f"Testing with {self.total_widgets} sequences")
        logger.info("Performance Targets:")
        logger.info("- Widget batch creation: ≤8.33ms per batch (120fps)")
        logger.info("- Total creation time: <3 seconds")
        logger.info("- Zero UI blocking")
        logger.info("-" * 60)
        
        # Start timing
        self.test_timer.start()
        
        # Set sequences (this triggers widget creation)
        self.grid_view.set_sequences(test_sequences)
    
    def on_content_ready(self):
        """Handle content ready signal."""
        total_time = self.test_timer.elapsed()
        
        logger.info("🎯 PERFORMANCE TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total widgets created: {self.total_widgets}")
        logger.info(f"Total creation time: {total_time}ms")
        logger.info(f"Average time per widget: {total_time / self.total_widgets:.2f}ms")
        
        # Analyze batch performance
        if hasattr(self.grid_view, '_creation_times') and self.grid_view._creation_times:
            batch_times = self.grid_view._creation_times
            avg_batch_time = sum(batch_times) / len(batch_times)
            max_batch_time = max(batch_times)
            min_batch_time = min(batch_times)
            
            logger.info(f"Total batches: {len(batch_times)}")
            logger.info(f"Average batch time: {avg_batch_time:.2f}ms")
            logger.info(f"Max batch time: {max_batch_time:.2f}ms")
            logger.info(f"Min batch time: {min_batch_time:.2f}ms")
            
            # Performance analysis
            target_batch_time = 8.33  # 120fps target
            target_total_time = 3000  # 3 seconds target
            
            logger.info("-" * 60)
            logger.info("📊 PERFORMANCE ANALYSIS")
            
            # Batch performance
            if avg_batch_time <= target_batch_time:
                logger.info(f"✅ Batch performance: PASSED ({avg_batch_time:.2f}ms ≤ {target_batch_time}ms)")
            else:
                logger.info(f"❌ Batch performance: FAILED ({avg_batch_time:.2f}ms > {target_batch_time}ms)")
                improvement_needed = ((avg_batch_time / target_batch_time) - 1) * 100
                logger.info(f"   Improvement needed: {improvement_needed:.1f}% faster")
            
            # Total time performance
            if total_time <= target_total_time:
                logger.info(f"✅ Total time: PASSED ({total_time}ms ≤ {target_total_time}ms)")
            else:
                logger.info(f"❌ Total time: FAILED ({total_time}ms > {target_total_time}ms)")
                improvement_needed = ((total_time / target_total_time) - 1) * 100
                logger.info(f"   Improvement needed: {improvement_needed:.1f}% faster")
            
            # Consistency analysis
            batch_variance = max_batch_time - min_batch_time
            if batch_variance <= target_batch_time:
                logger.info(f"✅ Batch consistency: GOOD (variance: {batch_variance:.2f}ms)")
            else:
                logger.info(f"⚠️ Batch consistency: POOR (variance: {batch_variance:.2f}ms)")
            
            # Performance rating
            logger.info("-" * 60)
            if avg_batch_time <= target_batch_time and total_time <= target_total_time:
                logger.info("🏆 OVERALL PERFORMANCE: EXCELLENT - 120fps target achieved!")
            elif avg_batch_time <= target_batch_time * 1.5 and total_time <= target_total_time * 1.5:
                logger.info("🥈 OVERALL PERFORMANCE: GOOD - Close to 120fps target")
            else:
                logger.info("🔧 OVERALL PERFORMANCE: NEEDS OPTIMIZATION")
        
        logger.info("=" * 60)
        
        # Schedule window close
        QTimer.singleShot(2000, self.close)


def run_performance_test():
    """Run the performance test."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create test window
    window = PerformanceTestWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    run_performance_test()
