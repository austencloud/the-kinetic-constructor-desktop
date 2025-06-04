"""
Test Critical Bug Fixes for Browse Tab v2

Tests the fixes for:
1. Sequence viewer display issues (thumbnail click → image display)
2. Action panel layout issues (positioning and alignment)
3. Image path resolution (thumbnails vs image_paths)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication

from src.browse_tab_v2.components.modern_sequence_viewer import ModernSequenceViewer
from src.browse_tab_v2.components.modern_action_panel import ModernActionPanel
from src.browse_tab_v2.core.interfaces import BrowseTabConfig, SequenceModel


class TestCriticalBugFixes:
    """Test critical bug fixes for browse tab v2."""

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
    def sequence_with_thumbnails(self):
        """Create sequence with thumbnails attribute."""
        return SequenceModel(
            id="test_001",
            name="Test Sequence",
            thumbnails=["image1.png", "image2.png", "image3.png"],
            difficulty=2,
            length=6,
            author="Test Author",
            tags=["test"]
        )

    @pytest.fixture
    def sequence_with_metadata_paths(self):
        """Create sequence with image paths in metadata."""
        return SequenceModel(
            id="test_002",
            name="Test Sequence 2",
            thumbnails=[],  # Empty thumbnails
            difficulty=3,
            length=8,
            author="Test Author",
            tags=["test"],
            metadata={
                "image_paths": ["meta_image1.png", "meta_image2.png"],
                "thumbnails": ["meta_thumb1.png", "meta_thumb2.png"]
            }
        )

    def test_bug_fix_image_path_resolution_thumbnails(self, app, config, sequence_with_thumbnails):
        """Test that sequence viewer correctly resolves thumbnails attribute."""
        viewer = ModernSequenceViewer(config)
        
        # Display sequence with thumbnails
        viewer.display_sequence(sequence_with_thumbnails, 0)
        
        # Check that variation_paths is correctly set from thumbnails
        assert viewer.variation_paths == ["image1.png", "image2.png", "image3.png"]
        assert len(viewer.variation_paths) == 3
        assert viewer.current_variation_index == 0
        
        # Check navigation controls are updated
        assert viewer.navigation_controls.total_variations == 3
        assert viewer.navigation_controls.current_variation == 0

    def test_bug_fix_image_path_resolution_metadata(self, app, config, sequence_with_metadata_paths):
        """Test that sequence viewer falls back to metadata for image paths."""
        viewer = ModernSequenceViewer(config)
        
        # Display sequence with paths in metadata
        viewer.display_sequence(sequence_with_metadata_paths, 0)
        
        # Should use thumbnails from metadata first
        assert viewer.variation_paths == ["meta_thumb1.png", "meta_thumb2.png"]
        assert len(viewer.variation_paths) == 2

    def test_bug_fix_image_path_resolution_fallback(self, app, config):
        """Test fallback behavior when no image paths are found."""
        sequence_no_images = SequenceModel(
            id="test_003",
            name="No Images",
            thumbnails=[],
            difficulty=1,
            length=4,
            author="Test",
            tags=[]
        )
        
        viewer = ModernSequenceViewer(config)
        viewer.display_sequence(sequence_no_images, 0)
        
        # Should have empty variation_paths
        assert viewer.variation_paths == []
        assert viewer.navigation_controls.total_variations == 0

    def test_bug_fix_action_panel_height(self, app, config):
        """Test that action panel has reduced height to fit in viewport."""
        action_panel = ModernActionPanel()
        
        # Check that height is reduced from 100 to 80
        assert action_panel.height() <= 80
        
        # Check that all buttons are still accessible
        assert action_panel.edit_button is not None
        assert action_panel.save_button is not None
        assert action_panel.delete_button is not None
        assert action_panel.fullscreen_button is not None

    def test_bug_fix_sequence_viewer_spacing(self, app, config, sequence_with_thumbnails):
        """Test that sequence viewer has reduced spacing to fit action panel."""
        viewer = ModernSequenceViewer(config)
        
        # Check layout spacing is reduced
        layout = viewer.layout()
        assert layout.spacing() == 10  # Should be reduced from 15
        
        # Check content frame spacing
        content_layout = viewer.content_frame.layout()
        assert content_layout.spacing() == 8  # Should be reduced from 10

    def test_bug_fix_navigation_between_variations(self, app, config, sequence_with_thumbnails):
        """Test navigation between variations works correctly."""
        viewer = ModernSequenceViewer(config)
        viewer.display_sequence(sequence_with_thumbnails, 0)
        
        # Test navigation to next variation
        viewer.navigate_to_variation(1)
        assert viewer.current_variation_index == 1
        
        # Test navigation to previous variation
        viewer.navigate_to_variation(0)
        assert viewer.current_variation_index == 0
        
        # Test navigation controls update
        assert viewer.navigation_controls.current_variation == 0
        assert viewer.navigation_controls.total_variations == 3

    def test_bug_fix_action_panel_button_signals(self, app, config, sequence_with_thumbnails):
        """Test that action panel buttons emit correct signals."""
        viewer = ModernSequenceViewer(config)
        viewer.display_sequence(sequence_with_thumbnails, 0)
        
        # Mock signal handlers
        edit_handler = Mock()
        save_handler = Mock()
        
        viewer.edit_requested.connect(edit_handler)
        viewer.save_requested.connect(save_handler)
        
        # Test button clicks
        viewer.action_panel.edit_button.click()
        edit_handler.assert_called_once_with("test_001")
        
        viewer.action_panel.save_button.click()
        save_handler.assert_called_once_with("test_001")

    def test_bug_fix_empty_state_handling(self, app, config):
        """Test that empty state is handled correctly."""
        viewer = ModernSequenceViewer(config)
        
        # Test with None sequence
        viewer.display_sequence(None, 0)
        assert viewer.current_sequence is None
        assert "Select a sequence" in viewer.title_label.text()
        
        # Test clearing
        viewer.clear()
        assert viewer.variation_paths == []
        assert viewer.current_variation_index == 0

    def test_bug_fix_image_display_error_handling(self, app, config):
        """Test that image display handles missing images gracefully."""
        from src.browse_tab_v2.components.modern_image_display import ModernImageDisplay
        
        image_display = ModernImageDisplay(config)
        
        # Test loading non-existent image
        image_display.load_image_with_transition("non_existent_image.png")
        
        # Should not crash and should show loading state
        assert image_display.is_loading is True
        
        # Test empty state
        image_display.show_empty_state()
        assert "No image selected" in image_display.image_label.text()

    def test_bug_fix_sequence_viewer_layout_proportions(self, app, config, sequence_with_thumbnails):
        """Test that sequence viewer layout proportions are correct."""
        viewer = ModernSequenceViewer(config)
        viewer.display_sequence(sequence_with_thumbnails, 0)
        
        # Check that all components are present and properly sized
        assert viewer.header_frame is not None
        assert viewer.content_frame is not None
        assert viewer.action_panel is not None
        
        # Check that action panel is at the bottom
        layout = viewer.layout()
        assert layout.itemAt(layout.count() - 1).widget() == viewer.action_panel


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
