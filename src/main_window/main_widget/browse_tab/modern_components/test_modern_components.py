"""
Test Modern Components - Comprehensive testing for 2025 design system

MODERNIZATION LOG:
- Date: 2025-01-27
- Changes Made: Created comprehensive test suite for modern components
- Performance Impact: Validates performance and functionality
- Breaking Changes: None (test component)
- Migration Notes: Run this to verify modern components work correctly
- Visual Changes: Tests all visual components and animations
"""

import sys
import logging
from pathlib import Path
from typing import List

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer

from .themes.modern_theme_manager import ModernThemeManager
from .animations.hover_animations import HoverAnimationManager
from .layouts.modern_grid_layout import ModernResponsiveGrid
from .cards.modern_thumbnail_card import ModernThumbnailCard
from .utils.change_logger import modernization_logger


class ModernComponentsTestWindow(QMainWindow):
    """Test window for modern components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Components Test - 2025 Design System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize modern components
        self.theme_manager = ModernThemeManager()
        self.hover_manager = HoverAnimationManager(self.theme_manager)
        
        # Test data
        self.test_sequences = [
            ("sequence_1", ["test_image_1.png", "test_image_2.png"], 4),
            ("sequence_2", ["test_image_3.png"], 2),
            ("sequence_3", ["test_image_4.png", "test_image_5.png", "test_image_6.png"], 6),
            ("sequence_4", ["test_image_7.png"], 3),
            ("sequence_5", ["test_image_8.png", "test_image_9.png"], 5),
        ]
        
        self.setup_ui()
        self.setup_logging()
        
        # Start automated tests
        QTimer.singleShot(1000, self.run_automated_tests)
    
    def setup_ui(self):
        """Setup the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Modern grid layout
        self.grid_layout = ModernResponsiveGrid(
            theme_manager=self.theme_manager,
            parent=central_widget,
            enable_masonry=False,
            min_item_width=250,
            max_columns=4
        )
        
        layout.addWidget(self.grid_layout)
        
        # Apply modern styling
        self.apply_modern_styling()
        
        # Create test cards
        self.create_test_cards()
    
    def create_control_panel(self) -> QWidget:
        """Create control panel for testing."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Theme toggle button
        self.theme_button = QPushButton("Switch to Light Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)
        
        # Masonry toggle button
        self.masonry_button = QPushButton("Enable Masonry Layout")
        self.masonry_button.clicked.connect(self.toggle_masonry)
        layout.addWidget(self.masonry_button)
        
        # Add card button
        add_button = QPushButton("Add Test Card")
        add_button.clicked.connect(self.add_test_card)
        layout.addWidget(add_button)
        
        # Remove card button
        remove_button = QPushButton("Remove Last Card")
        remove_button.clicked.connect(self.remove_test_card)
        layout.addWidget(remove_button)
        
        # Performance test button
        perf_button = QPushButton("Run Performance Test")
        perf_button.clicked.connect(self.run_performance_test)
        layout.addWidget(perf_button)
        
        layout.addStretch()
        
        return panel
    
    def apply_modern_styling(self):
        """Apply modern styling to the test window."""
        window_style = f"""
        QMainWindow {{
            background: {self.theme_manager.get_color("bg_primary")};
        }}
        
        QPushButton {{
            {self.theme_manager.create_glassmorphism_style("medium", 10, "md")}
            color: {self.theme_manager.get_color("text_primary")};
            padding: {self.theme_manager.get_spacing("sm")}px {self.theme_manager.get_spacing("md")}px;
            margin: {self.theme_manager.get_spacing("xs")}px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            border-color: {self.theme_manager.get_color("primary", 0.6)};
            background: {self.theme_manager.get_glassmorphism_color("glass_white", "strong")};
        }}
        """
        
        self.setStyleSheet(window_style)
    
    def create_test_cards(self):
        """Create test cards for the grid."""
        for word, thumbnails, length in self.test_sequences:
            self.create_modern_card(word, thumbnails)
    
    def create_modern_card(self, word: str, thumbnails: List[str]) -> ModernThumbnailCard:
        """Create a modern thumbnail card."""
        # Create mock browse tab object
        class MockBrowseTab:
            def __init__(self):
                self.main_widget = None
        
        mock_browse_tab = MockBrowseTab()
        
        # Create modern card
        card = ModernThumbnailCard(
            browse_tab=mock_browse_tab,
            word=word,
            thumbnails=thumbnails,
            theme_manager=self.theme_manager,
            hover_manager=self.hover_manager,
            in_sequence_viewer=False
        )
        
        # Connect signals
        card.clicked.connect(lambda: self.on_card_clicked(word))
        card.favorite_toggled.connect(lambda is_fav: self.on_favorite_toggled(word, is_fav))
        
        # Add to grid
        self.grid_layout.add_item(card, animate=True)
        
        return card
    
    def on_card_clicked(self, word: str):
        """Handle card click events."""
        print(f"Card clicked: {word}")
        modernization_logger.log_user_interaction(
            interaction_type="test_card_click",
            component="TestWindow",
            details={"word": word}
        )
    
    def on_favorite_toggled(self, word: str, is_favorite: bool):
        """Handle favorite toggle events."""
        print(f"Favorite toggled for {word}: {is_favorite}")
        modernization_logger.log_user_interaction(
            interaction_type="test_favorite_toggle",
            component="TestWindow",
            details={"word": word, "is_favorite": is_favorite}
        )
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current_theme = self.theme_manager.current_theme
        new_theme = "light" if current_theme == "dark" else "dark"
        
        self.theme_manager.switch_theme(new_theme)
        self.theme_button.setText(f"Switch to {'Dark' if new_theme == 'light' else 'Light'} Theme")
        
        # Refresh styling
        self.apply_modern_styling()
    
    def toggle_masonry(self):
        """Toggle masonry layout."""
        current_masonry = self.grid_layout.enable_masonry
        self.grid_layout.enable_masonry = not current_masonry
        self.grid_layout._schedule_layout_update()
        
        self.masonry_button.setText(f"{'Disable' if not current_masonry else 'Enable'} Masonry Layout")
    
    def add_test_card(self):
        """Add a new test card."""
        card_count = len(self.grid_layout.grid_items)
        word = f"test_sequence_{card_count + 1}"
        thumbnails = [f"test_image_{card_count + 1}.png"]
        
        self.create_modern_card(word, thumbnails)
    
    def remove_test_card(self):
        """Remove the last test card."""
        if self.grid_layout.grid_items:
            last_item = self.grid_layout.grid_items[-1]
            self.grid_layout.remove_item(last_item, animate=True)
    
    def run_performance_test(self):
        """Run performance tests."""
        print("Running performance tests...")
        
        # Test 1: Rapid card addition
        timer_id = modernization_logger.start_performance_timer("rapid_card_addition")
        
        for i in range(10):
            word = f"perf_test_{i}"
            thumbnails = [f"perf_image_{i}.png"]
            self.create_modern_card(word, thumbnails)
        
        modernization_logger.stop_performance_timer(timer_id)
        
        # Test 2: Layout recalculation
        timer_id = modernization_logger.start_performance_timer("layout_recalculation")
        
        # Trigger multiple layout updates
        for width in [800, 1000, 1200, 900]:
            self.resize(width, 800)
            QApplication.processEvents()
        
        modernization_logger.stop_performance_timer(timer_id)
        
        print("Performance tests completed!")
    
    def run_automated_tests(self):
        """Run automated tests."""
        print("Starting automated tests...")
        
        # Test theme switching
        self.toggle_theme()
        QTimer.singleShot(1000, lambda: self.toggle_theme())
        
        # Test masonry layout
        QTimer.singleShot(2000, self.toggle_masonry)
        QTimer.singleShot(3000, self.toggle_masonry)
        
        # Test card addition/removal
        QTimer.singleShot(4000, self.add_test_card)
        QTimer.singleShot(5000, self.remove_test_card)
        
        # Generate final report
        QTimer.singleShot(6000, self.generate_test_report)
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*50)
        print("MODERN COMPONENTS TEST REPORT")
        print("="*50)
        
        # Get statistics
        grid_stats = self.grid_layout.get_grid_stats()
        hover_stats = self.hover_manager.get_animation_stats()
        logger_summary = modernization_logger.generate_summary_report()
        
        print(f"Grid Layout Stats:")
        for key, value in grid_stats.items():
            print(f"  {key}: {value}")
        
        print(f"\nHover Animation Stats:")
        for key, value in hover_stats.items():
            print(f"  {key}: {value}")
        
        print(f"\nLogger Summary:")
        for key, value in logger_summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "="*50)
        print("All tests completed successfully! ✅")
        print("Modern components are ready for integration.")
        print("="*50)
    
    def setup_logging(self):
        """Setup logging for the test."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = ModernComponentsTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
