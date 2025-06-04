"""
Test Fixed Navigation Sidebar - Complete Overhaul

Tests the completely rewritten ModernNavigationSidebar component with:
1. Proper glassmorphism styling matching Browse Tab v2 components
2. Individual section buttons (A, B, C not A-C ranges) based on actual sequence data
3. Sort-responsive navigation (alphabetical, difficulty, date, length)
4. Fixed width design with proper visual hierarchy
5. Integration with BrowseTabView
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication

from src.browse_tab_v2.components.modern_navigation_sidebar import (
    ModernNavigationSidebar, SectionDataExtractor, ModernSidebarButton
)
from src.browse_tab_v2.core.interfaces import BrowseTabConfig, SequenceModel


class TestFixedNavigationSidebar:
    """Test the fixed navigation sidebar with proper architecture."""

    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = BrowseTabConfig()
        config.enable_animations = False  # Disable for testing
        return config

    @pytest.fixture
    def test_sequences(self):
        """Create test sequences with varied data for section extraction."""
        sequences = []
        
        # Alphabetical test data
        names = ['Apple Sequence', 'Banana Flow', 'Cherry Dance', 'Fig Pattern', 
                'Grape Motion', 'Mango Twist', 'Pear Spin', 'Strawberry Loop', 'Zebra Jump']
        
        for i, name in enumerate(names):
            sequence = SequenceModel(
                id=f"seq_{i:03d}",
                name=name,
                thumbnails=[f"{name.lower().replace(' ', '_')}.png"],
                difficulty=1 + (i % 5),  # 1-5 difficulty range
                length=3 + (i % 10),     # 3-12 length range
                author=f"Author {i % 3}",  # 3 different authors
                tags=[f"tag{i % 4}", "test"]
            )
            sequences.append(sequence)
        
        return sequences

    def test_section_data_extractor_alphabetical(self, test_sequences):
        """Test alphabetical section extraction."""
        extractor = SectionDataExtractor()
        sections = extractor.extract_alphabetical_sections(test_sequences)
        
        # Should extract individual letters that have sequences
        expected_letters = ['A', 'B', 'C', 'F', 'G', 'M', 'P', 'S', 'Z']
        assert sections == expected_letters
        assert len(sections) == 9

    def test_section_data_extractor_difficulty(self, test_sequences):
        """Test difficulty section extraction."""
        extractor = SectionDataExtractor()
        sections = extractor.extract_difficulty_sections(test_sequences)
        
        # Should have all three difficulty categories
        expected_difficulties = ['Advanced', 'Beginner', 'Intermediate']
        assert set(sections) == set(expected_difficulties)
        assert len(sections) == 3

    def test_section_data_extractor_length(self, test_sequences):
        """Test length section extraction."""
        extractor = SectionDataExtractor()
        sections = extractor.extract_length_sections(test_sequences)
        
        # Should have all three length categories
        expected_lengths = ['Long', 'Medium', 'Short']
        assert set(sections) == set(expected_lengths)
        assert len(sections) == 3

    def test_section_data_extractor_author(self, test_sequences):
        """Test author section extraction."""
        extractor = SectionDataExtractor()
        sections = extractor.extract_author_sections(test_sequences)
        
        # Should have 3 different authors
        expected_authors = ['Author 0', 'Author 1', 'Author 2']
        assert set(sections) == set(expected_authors)
        assert len(sections) == 3

    def test_modern_sidebar_button_creation(self, app):
        """Test ModernSidebarButton creation and styling."""
        button = ModernSidebarButton("A", "A")
        
        # Check basic properties
        assert button.text() == "A"
        assert button.section_id == "A"
        assert button.is_active == False
        
        # Check size constraints
        assert button.minimumHeight() == 32
        assert button.maximumHeight() == 36

    def test_modern_sidebar_button_active_state(self, app):
        """Test button active state changes."""
        button = ModernSidebarButton("A", "A")
        
        # Test setting active
        button.set_active(True)
        assert button.is_active == True
        assert button.property("active") == True
        
        # Test setting inactive
        button.set_active(False)
        assert button.is_active == False
        assert button.property("active") == False

    def test_modern_navigation_sidebar_creation(self, app, config):
        """Test ModernNavigationSidebar creation with fixed width."""
        sidebar = ModernNavigationSidebar(config)
        
        # Check fixed width design
        assert sidebar.width() == sidebar.sidebar_width
        assert sidebar.sidebar_width == 200
        
        # Check initial state
        assert len(sidebar.current_sequences) == 0
        assert sidebar.current_sort_criteria == "alphabetical"
        assert len(sidebar.sections) == 0
        assert len(sidebar.buttons) == 0
        
        # Check components exist
        assert sidebar.header_frame is not None
        assert sidebar.title_label is not None
        assert sidebar.separator_line is not None
        assert sidebar.content_area is not None

    def test_sidebar_update_for_alphabetical_sequences(self, app, config, test_sequences):
        """Test sidebar update with alphabetical sort."""
        sidebar = ModernNavigationSidebar(config)
        
        # Update with alphabetical sort
        sidebar.update_for_sequences(test_sequences, "alphabetical")
        
        # Check sections are extracted correctly
        expected_letters = ['A', 'B', 'C', 'F', 'G', 'M', 'P', 'S', 'Z']
        assert sidebar.sections == expected_letters
        assert sidebar.current_sort_criteria == "alphabetical"
        assert len(sidebar.buttons) == 9
        
        # Check buttons are created
        for letter in expected_letters:
            assert letter in sidebar.buttons
            assert sidebar.buttons[letter].text() == letter

    def test_sidebar_update_for_difficulty_sequences(self, app, config, test_sequences):
        """Test sidebar update with difficulty sort."""
        sidebar = ModernNavigationSidebar(config)
        
        # Update with difficulty sort
        sidebar.update_for_sequences(test_sequences, "difficulty")
        
        # Check sections are extracted correctly
        expected_difficulties = ['Advanced', 'Beginner', 'Intermediate']
        assert set(sidebar.sections) == set(expected_difficulties)
        assert sidebar.current_sort_criteria == "difficulty"
        assert len(sidebar.buttons) == 3

    def test_sidebar_update_for_length_sequences(self, app, config, test_sequences):
        """Test sidebar update with length sort."""
        sidebar = ModernNavigationSidebar(config)
        
        # Update with length sort
        sidebar.update_for_sequences(test_sequences, "length")
        
        # Check sections are extracted correctly
        expected_lengths = ['Long', 'Medium', 'Short']
        assert set(sidebar.sections) == set(expected_lengths)
        assert sidebar.current_sort_criteria == "length"
        assert len(sidebar.buttons) == 3

    def test_sidebar_section_button_clicks(self, app, config, test_sequences):
        """Test section button click handling."""
        sidebar = ModernNavigationSidebar(config)
        sidebar.update_for_sequences(test_sequences, "alphabetical")
        
        # Mock signal handler
        click_handler = Mock()
        sidebar.section_clicked.connect(click_handler)
        
        # Test button click
        sidebar.buttons["A"].click()
        click_handler.assert_called_once_with("A")
        
        # Check active state is set
        assert sidebar.active_section == "A"
        assert sidebar.buttons["A"].is_active == True

    def test_sidebar_active_section_management(self, app, config, test_sequences):
        """Test active section highlighting."""
        sidebar = ModernNavigationSidebar(config)
        sidebar.update_for_sequences(test_sequences, "alphabetical")
        
        # Set active section
        sidebar.set_active_section("A")
        assert sidebar.active_section == "A"
        assert sidebar.buttons["A"].is_active == True
        
        # Change active section
        sidebar.set_active_section("B")
        assert sidebar.active_section == "B"
        assert sidebar.buttons["A"].is_active == False
        assert sidebar.buttons["B"].is_active == True
        
        # Clear active section
        sidebar.set_active_section(None)
        assert sidebar.active_section is None
        assert sidebar.buttons["B"].is_active == False

    def test_sidebar_get_sequences_for_section(self, app, config, test_sequences):
        """Test getting sequences for a specific section."""
        sidebar = ModernNavigationSidebar(config)
        sidebar.update_for_sequences(test_sequences, "alphabetical")
        
        # Get sequences for letter "A"
        a_sequences = sidebar.get_sequences_for_section("A")
        assert len(a_sequences) == 1
        assert a_sequences[0].name == "Apple Sequence"
        
        # Get sequences for letter "B"
        b_sequences = sidebar.get_sequences_for_section("B")
        assert len(b_sequences) == 1
        assert b_sequences[0].name == "Banana Flow"
        
        # Test with difficulty sort
        sidebar.update_for_sequences(test_sequences, "difficulty")
        beginner_sequences = sidebar.get_sequences_for_section("Beginner")
        assert len(beginner_sequences) > 0
        for seq in beginner_sequences:
            assert getattr(seq, 'difficulty', 1) <= 2

    def test_sidebar_sort_criteria_changes(self, app, config, test_sequences):
        """Test sidebar updates when sort criteria changes."""
        sidebar = ModernNavigationSidebar(config)
        
        # Start with alphabetical
        sidebar.update_for_sequences(test_sequences, "alphabetical")
        initial_sections = sidebar.get_sections()
        assert "A" in initial_sections
        
        # Change to difficulty
        sidebar.update_for_sequences(test_sequences, "difficulty")
        difficulty_sections = sidebar.get_sections()
        assert "Beginner" in difficulty_sections
        assert "A" not in difficulty_sections
        
        # Change to length
        sidebar.update_for_sequences(test_sequences, "length")
        length_sections = sidebar.get_sections()
        assert "Short" in length_sections
        assert "Beginner" not in length_sections

    def test_sidebar_empty_sequences_handling(self, app, config):
        """Test sidebar behavior with empty sequences."""
        sidebar = ModernNavigationSidebar(config)
        
        # Update with empty sequences
        sidebar.update_for_sequences([], "alphabetical")
        
        # Should have no sections or buttons
        assert len(sidebar.sections) == 0
        assert len(sidebar.buttons) == 0
        assert sidebar.current_sort_criteria == "alphabetical"

    def test_sidebar_visual_hierarchy(self, app, config):
        """Test sidebar visual hierarchy and layout."""
        sidebar = ModernNavigationSidebar(config)
        
        # Check header is fixed height
        assert sidebar.header_frame.height() == 40
        
        # Check separator exists
        assert sidebar.separator_line.height() == 1
        
        # Check content area is scrollable
        assert sidebar.content_area is not None
        assert sidebar.content_widget is not None

    def test_sidebar_glassmorphism_styling(self, app, config):
        """Test that glassmorphism styling is applied."""
        sidebar = ModernNavigationSidebar(config)
        
        # Check that stylesheet is applied
        stylesheet = sidebar.styleSheet()
        assert "rgba(255, 255, 255, 0.08)" in stylesheet  # Background
        assert "border-radius: 20px" in stylesheet  # Rounded corners
        assert "backdrop-filter: blur(10px)" in stylesheet  # Glassmorphism


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
