"""
Performance Test for Browse Tab Improvements

This script tests the performance improvements made to address:
1. Monumentally slow loading times
2. High-resolution image scaling bottlenecks
3. Unnecessary resize cascades affecting all thumbnails
4. Loading all sequences at once

Performance targets:
- <100ms initial grid setup
- <16ms scroll response (60fps)
- <5ms per card creation
- <50MB memory usage for 200+ sequences
"""

import sys
import logging
import time
import psutil
import os
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
    from src.browse_tab_v2.components.efficient_virtual_grid import EfficientVirtualGrid
    from src.browse_tab_v2.components.fast_thumbnail_card import FastThumbnailCard
    from src.browse_tab_v2.services.fast_image_service import FastImageService, get_image_service
    from src.browse_tab_v2.core.interfaces import BrowseTabConfig
except ImportError as e:
    logger.error(f"Failed to import components: {e}")
    sys.exit(1)


class MockSequence:
    """Mock sequence for performance testing."""
    def __init__(self, name: str, seq_id: str, length: int = None, difficulty: str = None):
        self.id = seq_id
        self.name = name
        self.length = length or 4
        self.difficulty = difficulty or "Beginner"
        self.category = "Test"
        self.thumbnails = [f"test_image_{seq_id}.png"]
        self.is_favorite = False


class PerformanceTestWindow(QMainWindow):
    """Performance test window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browse Tab Performance Test")
        self.setGeometry(100, 100, 1400, 900)
        
        # Performance tracking
        self.start_time = 0
        self.scroll_times = []
        self.memory_usage = []
        self.card_creation_times = []
        
        # Test data
        self.test_sequences = []
        
        self._setup_ui()
        self._create_test_sequences()
        
        logger.info("Performance test window initialized")
    
    def _setup_ui(self):
        """Setup test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Performance controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        
        # Test buttons
        self.test_load_button = QPushButton("Test Load Performance")
        self.test_load_button.clicked.connect(self.test_load_performance)
        controls_layout.addWidget(self.test_load_button)
        
        self.test_scroll_button = QPushButton("Test Scroll Performance")
        self.test_scroll_button.clicked.connect(self.test_scroll_performance)
        controls_layout.addWidget(self.test_scroll_button)
        
        self.test_memory_button = QPushButton("Test Memory Usage")
        self.test_memory_button.clicked.connect(self.test_memory_usage)
        controls_layout.addWidget(self.test_memory_button)
        
        self.test_all_button = QPushButton("Run All Tests")
        self.test_all_button.clicked.connect(self.run_all_tests)
        controls_layout.addWidget(self.test_all_button)
        
        controls_layout.addStretch()
        layout.addWidget(controls_widget)
        
        # Performance stats display
        self.stats_label = QLabel("Ready to run performance tests")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.stats_label.setFont(font)
        layout.addWidget(self.stats_label)
        
        # Create efficient grid
        self.config = BrowseTabConfig()
        self.grid = EfficientVirtualGrid(self.config, parent=central_widget)
        self.grid.set_item_creator(self.create_performance_card)
        layout.addWidget(self.grid)
        
        # Connect monitoring
        self.grid.viewport_changed.connect(self.on_viewport_changed)
        
        # Initialize image service
        self.image_service = get_image_service()
    
    def _create_test_sequences(self):
        """Create test sequences for performance testing."""
        self.test_sequences = []
        
        # Create a large number of sequences to test performance
        for i in range(500):  # 500 sequences for stress testing
            seq = MockSequence(
                name=f"Performance Test Sequence {i+1:03d}",
                seq_id=f"perf_test_{i+1:04d}",
                length=2 + (i % 8),
                difficulty=["Beginner", "Intermediate", "Advanced", "Expert"][i % 4]
            )
            self.test_sequences.append(seq)
        
        logger.info(f"Created {len(self.test_sequences)} test sequences")
    
    def create_performance_card(self, sequence, index):
        """Create card with performance monitoring."""
        start_time = time.time()
        
        card = FastThumbnailCard(sequence, self.config, parent=self.grid)
        
        creation_time = (time.time() - start_time) * 1000
        self.card_creation_times.append(creation_time)
        
        if creation_time > 10:  # Log slow card creation
            logger.warning(f"Slow card creation: {creation_time:.1f}ms for card {index}")
        
        return card
    
    def test_load_performance(self):
        """Test initial load performance."""
        self.stats_label.setText("Testing load performance...")
        self.card_creation_times.clear()
        
        # Test with different sequence counts
        test_counts = [50, 100, 200, 500]
        results = []
        
        for count in test_counts:
            start_time = time.time()
            
            # Load sequences
            test_sequences = self.test_sequences[:count]
            self.grid.set_sequences(test_sequences)
            
            load_time = (time.time() - start_time) * 1000
            results.append(f"{count} seqs: {load_time:.1f}ms")
            
            logger.info(f"Loaded {count} sequences in {load_time:.1f}ms")
            
            # Wait a bit between tests
            QApplication.processEvents()
            time.sleep(0.1)
        
        # Calculate card creation stats
        if self.card_creation_times:
            avg_card_time = sum(self.card_creation_times) / len(self.card_creation_times)
            max_card_time = max(self.card_creation_times)
            results.append(f"Avg card: {avg_card_time:.1f}ms")
            results.append(f"Max card: {max_card_time:.1f}ms")
        
        self.stats_label.setText(" | ".join(results))
    
    def test_scroll_performance(self):
        """Test scroll performance."""
        self.stats_label.setText("Testing scroll performance...")
        self.scroll_times.clear()
        
        # Load sequences
        self.grid.set_sequences(self.test_sequences)
        
        # Simulate scroll events
        scroll_bar = self.grid.scroll_area.verticalScrollBar()
        max_value = scroll_bar.maximum()
        
        if max_value <= 0:
            self.stats_label.setText("No scrollable content for scroll test")
            return
        
        # Test scroll at different positions
        scroll_positions = [0, max_value // 4, max_value // 2, 3 * max_value // 4, max_value]
        
        for position in scroll_positions:
            start_time = time.time()
            
            scroll_bar.setValue(position)
            QApplication.processEvents()  # Process scroll events
            
            scroll_time = (time.time() - start_time) * 1000
            self.scroll_times.append(scroll_time)
            
            time.sleep(0.05)  # Small delay between scrolls
        
        # Calculate scroll stats
        if self.scroll_times:
            avg_scroll = sum(self.scroll_times) / len(self.scroll_times)
            max_scroll = max(self.scroll_times)
            
            results = [
                f"Avg scroll: {avg_scroll:.1f}ms",
                f"Max scroll: {max_scroll:.1f}ms",
                f"60fps target: {'✅' if max_scroll < 16 else '❌'}"
            ]
            
            self.stats_label.setText(" | ".join(results))
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        self.stats_label.setText("Testing memory usage...")
        self.memory_usage.clear()
        
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test with increasing sequence counts
        test_counts = [100, 200, 300, 500]
        
        for count in test_counts:
            # Load sequences
            test_sequences = self.test_sequences[:count]
            self.grid.set_sequences(test_sequences)
            
            # Force some scrolling to create cards
            scroll_bar = self.grid.scroll_area.verticalScrollBar()
            for pos in [0, scroll_bar.maximum() // 2, scroll_bar.maximum()]:
                scroll_bar.setValue(pos)
                QApplication.processEvents()
                time.sleep(0.02)
            
            # Measure memory
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            self.memory_usage.append((count, memory_increase))
            
            logger.info(f"{count} sequences: {memory_increase:.1f}MB increase")
        
        # Get image service stats
        image_stats = self.image_service.get_cache_stats()
        
        # Display results
        if self.memory_usage:
            final_count, final_memory = self.memory_usage[-1]
            results = [
                f"500 seqs: +{final_memory:.1f}MB",
                f"Image cache: {image_stats['memory_mb']}MB",
                f"Hit rate: {image_stats['hit_rate']}%",
                f"Target <50MB: {'✅' if final_memory < 50 else '❌'}"
            ]
            
            self.stats_label.setText(" | ".join(results))
    
    def run_all_tests(self):
        """Run all performance tests."""
        logger.info("Running comprehensive performance test suite")
        
        # Run tests in sequence
        self.test_load_performance()
        QTimer.singleShot(1000, self.test_scroll_performance)
        QTimer.singleShot(2000, self.test_memory_usage)
        QTimer.singleShot(3000, self.show_final_results)
    
    def show_final_results(self):
        """Show final comprehensive results."""
        results = []
        
        # Load performance
        if self.card_creation_times:
            avg_card = sum(self.card_creation_times) / len(self.card_creation_times)
            results.append(f"Card creation: {avg_card:.1f}ms avg")
        
        # Scroll performance
        if self.scroll_times:
            max_scroll = max(self.scroll_times)
            results.append(f"Scroll: {max_scroll:.1f}ms max")
        
        # Memory usage
        if self.memory_usage:
            _, final_memory = self.memory_usage[-1]
            results.append(f"Memory: +{final_memory:.1f}MB")
        
        # Image service stats
        image_stats = self.image_service.get_cache_stats()
        results.append(f"Cache hit: {image_stats['hit_rate']}%")
        
        # Overall assessment
        load_ok = not self.card_creation_times or max(self.card_creation_times) < 10
        scroll_ok = not self.scroll_times or max(self.scroll_times) < 16
        memory_ok = not self.memory_usage or self.memory_usage[-1][1] < 50
        
        overall = "✅ EXCELLENT" if all([load_ok, scroll_ok, memory_ok]) else "⚠️ NEEDS WORK"
        results.append(f"Overall: {overall}")
        
        self.stats_label.setText(" | ".join(results))
        logger.info(f"Performance test complete: {results}")
    
    def on_viewport_changed(self, start, end):
        """Monitor viewport changes."""
        logger.debug(f"Viewport: {start}-{end}")


def main():
    """Run performance tests."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = PerformanceTestWindow()
    window.show()
    
    logger.info("Performance test application started")
    logger.info("Click buttons to run specific tests or 'Run All Tests' for comprehensive testing")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
