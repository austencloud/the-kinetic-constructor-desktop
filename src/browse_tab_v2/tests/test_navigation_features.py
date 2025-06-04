"""
Test Navigation Features for Browse Tab v2

Tests the navigation features including:
1. ModernNavigationSidebar - collapsible sidebar with section navigation
2. DynamicSectionHeaders - section grouping and headers
3. SmoothScrollNavigation - smooth scrolling and viewport tracking
4. Integration with BrowseTabView layout
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QScrollArea
from PyQt6.QtCore import Qt

from src.browse_tab_v2.components.modern_navigation_sidebar import ModernNavigationSidebar
from src.browse_tab_v2.components.dynamic_section_headers import (
    DynamicSectionHeaders, SectionType, SectionHeaderManager
)
from src.browse_tab_v2.components.smooth_scroll_navigation import SmoothScrollNavigation
from src.browse_tab_v2.core.interfaces import BrowseTabConfig, SequenceModel


class TestNavigationFeatures:
    """Test navigation features for browse tab v2."""

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
        """Create test sequences for navigation."""
        sequences = []
        
        # Create sequences with different starting letters
        for i, letter in enumerate(['A', 'B', 'C', 'F', 'G', 'M', 'P', 'S', 'Z']):
            sequence = SequenceModel(
                id=f"seq_{letter.lower()}_{i}",
                name=f"{letter}Test Sequence {i}",
                thumbnails=[f"{letter.lower()}_image.png"],
                difficulty=1 + (i % 5),
                length=3 + (i % 8),
                author=f"Author {i % 3}",
                tags=[f"tag{i % 4}", "test"]
            )
            sequences.append(sequence)
        
        return sequences

    def test_modern_navigation_sidebar_creation(self, app, config):
        """Test ModernNavigationSidebar creation and basic functionality."""
        sidebar = ModernNavigationSidebar(config)
        
        # Check initial state
        assert sidebar.is_collapsed == False
        assert sidebar.width() == sidebar.expanded_width
        assert len(sidebar.sections) == 0
        assert sidebar.active_section is None
        
        # Check components exist
        assert sidebar.toggle_button is not None
        assert sidebar.content_area is not None
        assert sidebar.title_label is not None

    def test_navigation_sidebar_sections_update(self, app, config):
        """Test updating sidebar sections."""
        sidebar = ModernNavigationSidebar(config)
        
        # Update with test sections
        test_sections = {
            "A-C": "A-C (5 sequences)",
            "D-F": "D-F (3 sequences)",
            "G-I": "G-I (2 sequences)"
        }
        
        sidebar.update_sections(test_sections)
        
        # Check sections are updated
        assert len(sidebar.sections) == 3
        assert len(sidebar.buttons) == 3
        assert "A-C" in sidebar.buttons
        assert "D-F" in sidebar.buttons
        assert "G-I" in sidebar.buttons

    def test_navigation_sidebar_collapse_expand(self, app, config):
        """Test sidebar collapse and expand functionality."""
        sidebar = ModernNavigationSidebar(config)
        
        # Test collapse
        sidebar._toggle_collapse()
        assert sidebar.is_collapsed == True
        assert sidebar.toggle_button.text() == "▶"
        assert not sidebar.content_area.isVisible()
        
        # Test expand
        sidebar._toggle_collapse()
        assert sidebar.is_collapsed == False
        assert sidebar.toggle_button.text() == "◀"
        assert sidebar.content_area.isVisible()

    def test_navigation_sidebar_active_section(self, app, config):
        """Test active section highlighting."""
        sidebar = ModernNavigationSidebar(config)
        
        # Add sections
        test_sections = {"A-C": "A-C", "D-F": "D-F"}
        sidebar.update_sections(test_sections)
        
        # Set active section
        sidebar.set_active_section("A-C")
        assert sidebar.active_section == "A-C"
        assert sidebar.buttons["A-C"].is_active == True
        assert sidebar.buttons["D-F"].is_active == False
        
        # Change active section
        sidebar.set_active_section("D-F")
        assert sidebar.active_section == "D-F"
        assert sidebar.buttons["A-C"].is_active == False
        assert sidebar.buttons["D-F"].is_active == True

    def test_section_header_manager_alphabetical_grouping(self, test_sequences):
        """Test alphabetical grouping in SectionHeaderManager."""
        manager = SectionHeaderManager()
        
        groups = manager.group_sequences(test_sequences, SectionType.ALPHABETICAL)
        
        # Check groups are created correctly
        assert "A-C" in groups
        assert "D-F" in groups
        assert "M-O" in groups
        assert "P-R" in groups
        assert "S-U" in groups
        assert "V-Z" in groups
        
        # Check sequences are in correct groups
        a_c_sequences = groups["A-C"]
        assert len(a_c_sequences) == 3  # A, B, C sequences
        assert all(seq.name[0] in ['A', 'B', 'C'] for seq in a_c_sequences)

    def test_section_header_manager_length_grouping(self, test_sequences):
        """Test length-based grouping."""
        manager = SectionHeaderManager()
        
        groups = manager.group_sequences(test_sequences, SectionType.LENGTH)
        
        # Check length groups exist
        assert "Short (1-4 beats)" in groups
        assert "Medium (5-8 beats)" in groups
        assert "Long (9+ beats)" in groups
        
        # Verify sequences are grouped by length
        for group_name, sequences in groups.items():
            for seq in sequences:
                if "Short" in group_name:
                    assert seq.length <= 4
                elif "Medium" in group_name:
                    assert 5 <= seq.length <= 8
                elif "Long" in group_name:
                    assert seq.length >= 9

    def test_section_header_manager_difficulty_grouping(self, test_sequences):
        """Test difficulty-based grouping."""
        manager = SectionHeaderManager()
        
        groups = manager.group_sequences(test_sequences, SectionType.DIFFICULTY)
        
        # Check difficulty groups
        assert "Beginner (1-2)" in groups
        assert "Intermediate (3-4)" in groups
        assert "Advanced (5+)" in groups
        
        # Verify sequences are grouped by difficulty
        for group_name, sequences in groups.items():
            for seq in sequences:
                if "Beginner" in group_name:
                    assert seq.difficulty <= 2
                elif "Intermediate" in group_name:
                    assert 3 <= seq.difficulty <= 4
                elif "Advanced" in group_name:
                    assert seq.difficulty >= 5

    def test_dynamic_section_headers_creation(self, app, config):
        """Test DynamicSectionHeaders creation."""
        headers = DynamicSectionHeaders(config)
        
        # Check initial state
        assert len(headers.current_sequences) == 0
        assert headers.current_section_type == SectionType.ALPHABETICAL
        assert len(headers.headers) == 0
        assert len(headers.section_groups) == 0

    def test_dynamic_section_headers_update(self, app, config, test_sequences):
        """Test updating section headers with sequences."""
        headers = DynamicSectionHeaders(config)
        
        # Update with test sequences
        headers.update_sequences(test_sequences, SectionType.ALPHABETICAL)
        
        # Check headers are created
        assert len(headers.current_sequences) == len(test_sequences)
        assert len(headers.section_groups) > 0
        assert len(headers.headers) == len(headers.section_groups)
        
        # Check section names
        section_names = headers.get_section_names()
        assert "A-C" in section_names
        assert "D-F" in section_names

    def test_smooth_scroll_navigation_creation(self, app, config):
        """Test SmoothScrollNavigation creation."""
        # Create mock scroll area
        scroll_area = QScrollArea()
        
        smooth_scroll = SmoothScrollNavigation(scroll_area, config)
        
        # Check initial state
        assert smooth_scroll.scroll_area == scroll_area
        assert smooth_scroll.is_animating == False
        assert len(smooth_scroll.section_positions) == 0
        assert smooth_scroll.viewport_tracker is not None

    def test_smooth_scroll_navigation_section_positions(self, app, config):
        """Test updating section positions."""
        scroll_area = QScrollArea()
        smooth_scroll = SmoothScrollNavigation(scroll_area, config)
        
        # Update section positions
        test_positions = {
            "A-C": 0,
            "D-F": 400,
            "G-I": 800
        }
        
        smooth_scroll.update_section_positions(test_positions)
        
        # Check positions are stored
        assert smooth_scroll.section_positions == test_positions
        assert smooth_scroll.viewport_tracker.section_positions == test_positions

    def test_smooth_scroll_navigation_scroll_to_section(self, app, config):
        """Test scrolling to a specific section."""
        scroll_area = QScrollArea()
        smooth_scroll = SmoothScrollNavigation(scroll_area, config)
        
        # Set up section positions
        test_positions = {"A-C": 0, "D-F": 400}
        smooth_scroll.update_section_positions(test_positions)
        
        # Test immediate scroll (no animation)
        smooth_scroll.scroll_to_section("D-F", animated=False)
        
        # Check scroll position (would need actual scroll bar)
        # This is a basic test - full testing would require scroll bar setup

    def test_smooth_scroll_position_persistence(self, app, config):
        """Test scroll position saving and restoring."""
        scroll_area = QScrollArea()
        smooth_scroll = SmoothScrollNavigation(scroll_area, config)
        
        # Save position
        smooth_scroll.position_manager.save_position("filter1", 200)
        smooth_scroll.position_manager.save_position("filter2", 500)
        
        # Restore positions
        pos1 = smooth_scroll.position_manager.restore_position("filter1")
        pos2 = smooth_scroll.position_manager.restore_position("filter2")
        pos3 = smooth_scroll.position_manager.restore_position("nonexistent")
        
        assert pos1 == 200
        assert pos2 == 500
        assert pos3 is None

    def test_navigation_integration_signals(self, app, config):
        """Test signal connections between navigation components."""
        sidebar = ModernNavigationSidebar(config)
        
        # Mock signal handlers
        section_handler = Mock()
        collapse_handler = Mock()
        
        sidebar.section_clicked.connect(section_handler)
        sidebar.collapse_toggled.connect(collapse_handler)
        
        # Add sections and test signals
        test_sections = {"A-C": "A-C"}
        sidebar.update_sections(test_sections)
        
        # Simulate button click
        sidebar.buttons["A-C"].click()
        section_handler.assert_called_once_with("A-C")
        
        # Simulate collapse toggle
        sidebar._toggle_collapse()
        collapse_handler.assert_called_once_with(True)

    def test_navigation_responsive_behavior(self, app, config):
        """Test responsive behavior of navigation components."""
        sidebar = ModernNavigationSidebar(config)
        
        # Test width constraints
        assert sidebar.expanded_width == 200
        assert sidebar.collapsed_width == 40
        
        # Test collapse behavior
        sidebar._toggle_collapse()
        # After animation, width should be collapsed_width
        # (Animation testing would require more complex setup)

    def test_navigation_error_handling(self, app, config):
        """Test error handling in navigation components."""
        # Test with invalid section types
        headers = DynamicSectionHeaders(config)
        
        # Should not crash with empty sequences
        headers.update_sequences([], SectionType.ALPHABETICAL)
        assert len(headers.section_groups) == 0
        
        # Test smooth scroll with invalid section
        scroll_area = QScrollArea()
        smooth_scroll = SmoothScrollNavigation(scroll_area, config)
        
        # Should not crash when scrolling to non-existent section
        smooth_scroll.scroll_to_section("nonexistent", animated=False)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
