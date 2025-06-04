"""
Test Sequence Viewer Integration

Tests the critical missing component - ModernSequenceViewer and its integration
with the browse tab layout and thumbnail grid.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

from src.browse_tab_v2.components.modern_sequence_viewer import ModernSequenceViewer
from src.browse_tab_v2.components.modern_image_display import ModernImageDisplay
from src.browse_tab_v2.components.navigation_controls import NavigationControls
from src.browse_tab_v2.components.modern_action_panel import ModernActionPanel
from src.browse_tab_v2.components.browse_tab_view import BrowseTabView
from src.browse_tab_v2.core.interfaces import BrowseTabConfig
from src.browse_tab_v2.core.state import SequenceModel


class TestSequenceViewerIntegration:
    """Test the sequence viewer integration with browse tab."""

    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        # Don't quit the app as it might be shared

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = BrowseTabConfig()
        config.enable_animations = False  # Disable for testing
        return config

    @pytest.fixture
    def mock_sequence(self):
        """Create mock sequence for testing."""
        sequence = Mock(spec=SequenceModel)
        sequence.id = "test_sequence_001"
        sequence.name = "Test Sequence"
        sequence.difficulty = "Beginner"
        sequence.length = 8
        sequence.image_paths = [
            "test_image_1.png",
            "test_image_2.png",
            "test_image_3.png",
        ]
        sequence.created_date = "2024-01-01"
        sequence.tags = ["test", "sequence"]
        return sequence

    def test_sequence_viewer_creation(self, app, config):
        """Test that ModernSequenceViewer can be created."""
        viewer = ModernSequenceViewer(config)

        assert viewer is not None
        assert viewer.config == config
        assert viewer.current_sequence is None
        assert viewer.current_variation_index == 0

        # Check components are created
        assert viewer.image_display is not None
        assert viewer.navigation_controls is not None
        assert viewer.action_panel is not None
        assert viewer.metadata_display is not None

    def test_sequence_viewer_display_sequence(self, app, config, mock_sequence):
        """Test displaying a sequence in the viewer."""
        viewer = ModernSequenceViewer(config)

        # Display the sequence
        viewer.display_sequence(mock_sequence, 0)

        # Check state is updated
        assert viewer.current_sequence == mock_sequence
        assert viewer.current_variation_index == 0
        assert viewer.variation_paths == mock_sequence.image_paths

        # Check UI is updated
        assert "Test Sequence" in viewer.title_label.text()
        assert "Beginner" in viewer.info_label.text()

    def test_sequence_viewer_navigation(self, app, config, mock_sequence):
        """Test navigation between variations."""
        viewer = ModernSequenceViewer(config)
        viewer.display_sequence(mock_sequence, 0)

        # Test navigate to next variation
        viewer.navigate_to_variation(1)
        assert viewer.current_variation_index == 1

        # Test navigate to previous variation
        viewer.navigate_to_variation(0)
        assert viewer.current_variation_index == 0

        # Test invalid navigation
        viewer.navigate_to_variation(10)  # Should not change
        assert viewer.current_variation_index == 0

    def test_sequence_viewer_signals(self, app, config, mock_sequence):
        """Test that sequence viewer emits correct signals."""
        viewer = ModernSequenceViewer(config)
        viewer.display_sequence(mock_sequence, 0)

        # Mock signal handlers
        edit_handler = Mock()
        save_handler = Mock()
        delete_handler = Mock()
        fullscreen_handler = Mock()

        viewer.edit_requested.connect(edit_handler)
        viewer.save_requested.connect(save_handler)
        viewer.delete_requested.connect(delete_handler)
        viewer.fullscreen_requested.connect(fullscreen_handler)

        # Trigger action buttons
        viewer.action_panel.edit_button.click()
        edit_handler.assert_called_once_with(mock_sequence.id)

        viewer.action_panel.save_button.click()
        save_handler.assert_called_once_with(mock_sequence.id)

    def test_browse_tab_layout_with_sequence_viewer(self, app, config):
        """Test that BrowseTabView includes sequence viewer with correct layout."""
        # Mock dependencies
        with patch(
            "src.browse_tab_v2.components.browse_tab_view.track_component"
        ), patch(
            "src.browse_tab_v2.components.browse_tab_view.log_main_window_change"
        ), patch(
            "src.browse_tab_v2.components.browse_tab_view.set_phase"
        ):

            # Create mock viewmodel
            mock_viewmodel = Mock()
            mock_viewmodel.state_changed = Mock()
            mock_viewmodel.loading_started = Mock()
            mock_viewmodel.loading_finished = Mock()
            mock_viewmodel.error_occurred = Mock()

            view = BrowseTabView(mock_viewmodel, config)

            # Check that sequence viewer is created
            assert hasattr(view, "sequence_viewer")
            assert view.sequence_viewer is not None
            assert isinstance(view.sequence_viewer, ModernSequenceViewer)

            # Check layout structure
            assert hasattr(view, "left_panel")
            main_layout = view.layout()
            assert main_layout.count() == 2  # Left panel + sequence viewer

            # Check stretch factors (2:1 ratio)
            assert main_layout.stretch(0) == 2  # Left panel
            assert main_layout.stretch(1) == 1  # Sequence viewer

    def test_thumbnail_click_displays_in_viewer(self, app, config, mock_sequence):
        """Test that clicking a thumbnail displays sequence in viewer."""
        # Mock dependencies
        with patch(
            "src.browse_tab_v2.components.browse_tab_view.track_component"
        ), patch(
            "src.browse_tab_v2.components.browse_tab_view.log_main_window_change"
        ), patch(
            "src.browse_tab_v2.components.browse_tab_view.set_phase"
        ), patch(
            "src.browse_tab_v2.debug.window_resize_tracker.get_tracker"
        ):

            # Create mock viewmodel
            mock_viewmodel = Mock()
            mock_viewmodel.state_changed = Mock()
            mock_viewmodel.loading_started = Mock()
            mock_viewmodel.loading_finished = Mock()
            mock_viewmodel.error_occurred = Mock()

            view = BrowseTabView(mock_viewmodel, config)
            view._sequences = [mock_sequence]  # Set test data

            # Simulate thumbnail click
            view._on_item_clicked(mock_sequence.id, 0)

            # Check sequence is displayed in viewer
            assert view.sequence_viewer.current_sequence == mock_sequence
            assert view.sequence_viewer.current_variation_index == 0

    def test_image_display_component(self, app, config):
        """Test ModernImageDisplay component."""
        image_display = ModernImageDisplay(config)

        assert image_display is not None
        assert image_display.current_image_path is None
        assert image_display.is_loading is False

        # Test empty state
        image_display.show_empty_state()
        assert "No image selected" in image_display.image_label.text()

    def test_navigation_controls_component(self, app, config):
        """Test NavigationControls component."""
        nav_controls = NavigationControls()

        assert nav_controls is not None
        assert nav_controls.current_variation == 0
        assert nav_controls.total_variations == 0
        assert not nav_controls.is_enabled

        # Test setting variation info
        nav_controls.set_variation_info(1, 3)
        assert nav_controls.current_variation == 1
        assert nav_controls.total_variations == 3
        assert nav_controls.is_enabled
        assert "Variation 2 of 3" in nav_controls.variation_label.text()

    def test_action_panel_component(self, app, config):
        """Test ModernActionPanel component."""
        action_panel = ModernActionPanel()

        assert action_panel is not None
        assert not action_panel.is_enabled
        assert action_panel.current_sequence_id is None

        # Test enabling
        action_panel.set_enabled(True)
        assert action_panel.is_enabled
        assert action_panel.edit_button.isEnabled()
        assert action_panel.save_button.isEnabled()
        assert action_panel.delete_button.isEnabled()
        assert action_panel.fullscreen_button.isEnabled()

    def test_sequence_viewer_empty_state(self, app, config):
        """Test sequence viewer empty state."""
        viewer = ModernSequenceViewer(config)

        # Should start in empty state
        assert "Select a sequence" in viewer.title_label.text()
        assert not viewer.navigation_controls.is_enabled
        assert not viewer.action_panel.is_enabled

        # Test clearing
        viewer.clear()
        assert viewer.current_sequence is None
        assert viewer.current_variation_index == 0
        assert viewer.variation_paths == []

    def test_sequence_viewer_error_handling(self, app, config):
        """Test sequence viewer handles errors gracefully."""
        viewer = ModernSequenceViewer(config)

        # Test with None sequence
        viewer.display_sequence(None, 0)
        assert viewer.current_sequence is None

        # Test with invalid variation index
        mock_seq = Mock()
        mock_seq.id = "test"
        mock_seq.name = "Test"
        mock_seq.difficulty = "Easy"
        mock_seq.length = 4
        mock_seq.image_paths = ["test.png"]

        viewer.display_sequence(mock_seq, 0)
        viewer.navigate_to_variation(-1)  # Invalid
        assert viewer.current_variation_index == 0

        viewer.navigate_to_variation(10)  # Invalid
        assert viewer.current_variation_index == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
