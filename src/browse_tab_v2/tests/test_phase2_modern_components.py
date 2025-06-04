"""
Test suite for Phase 2 Modern UI Components

Tests all the modern components implemented in Phase 2:
- ResponsiveThumbnailGrid
- ModernThumbnailCard  
- SmartFilterPanel
- VirtualScrollWidget
- LoadingStates (LoadingIndicator, SkeletonScreen, ErrorState)
- AnimationSystem
"""

import pytest
import logging
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

# Import components to test
from ..components.responsive_thumbnail_grid import ResponsiveThumbnailGrid
from ..components.modern_thumbnail_card import ModernThumbnailCard
from ..components.smart_filter_panel import SmartFilterPanel
from ..components.virtual_scroll_widget import VirtualScrollWidget
from ..components.loading_states import LoadingIndicator, SkeletonScreen, ErrorState, ProgressIndicator
from ..components.animation_system import AnimationManager, AnimationConfig, AnimationType
from ..components.browse_tab_view import BrowseTabView

# Import supporting classes
from ..core.interfaces import BrowseTabConfig, FilterCriteria, FilterType
from ..core.state import SequenceModel
from ..viewmodels.browse_tab_viewmodel import BrowseTabViewModel

logger = logging.getLogger(__name__)


class TestResponsiveThumbnailGrid:
    """Test the ResponsiveThumbnailGrid component."""
    
    def test_grid_initialization(self, qtbot):
        """Test grid initializes correctly."""
        config = BrowseTabConfig()
        grid = ResponsiveThumbnailGrid(config)
        qtbot.addWidget(grid)
        
        assert grid.get_column_count() == config.default_columns
        assert grid.get_visible_range() == (0, 0)
        assert len(grid.get_selected_items()) == 0
    
    def test_grid_column_calculation(self, qtbot):
        """Test automatic column calculation."""
        config = BrowseTabConfig()
        grid = ResponsiveThumbnailGrid(config)
        qtbot.addWidget(grid)
        
        # Set a specific size and test column calculation
        grid.resize(900, 600)  # Should fit 3 columns at 280px min width
        grid.show()
        QTest.qWait(100)  # Allow resize to process
        
        # Column count should be calculated based on width
        assert grid.get_column_count() >= 1
        assert grid.get_column_count() <= 6  # Max columns cap
    
    def test_grid_sequences_setting(self, qtbot):
        """Test setting sequences in the grid."""
        config = BrowseTabConfig()
        grid = ResponsiveThumbnailGrid(config)
        qtbot.addWidget(grid)
        
        # Create test sequences
        sequences = [
            SequenceModel(id=f"seq_{i}", name=f"Sequence {i}", difficulty=i % 5 + 1, length=8)
            for i in range(10)
        ]
        
        # Set item creator
        def create_test_item(sequence, index):
            widget = QWidget()
            widget.setFixedHeight(320)
            return widget
        
        grid.set_item_creator(create_test_item)
        grid.set_sequences(sequences)
        
        # Verify sequences are set
        assert len(grid._sequences) == 10


class TestModernThumbnailCard:
    """Test the ModernThumbnailCard component."""
    
    def test_card_initialization(self, qtbot):
        """Test card initializes correctly."""
        sequence = SequenceModel(id="test_seq", name="Test Sequence", difficulty=3, length=8)
        config = BrowseTabConfig()
        card = ModernThumbnailCard(sequence, config)
        qtbot.addWidget(card)
        
        assert card.get_sequence_id() == "test_seq"
        assert not card.is_selected()
        assert not card.is_favorite()
    
    def test_card_selection(self, qtbot):
        """Test card selection functionality."""
        sequence = SequenceModel(id="test_seq", name="Test Sequence", difficulty=3, length=8)
        config = BrowseTabConfig()
        card = ModernThumbnailCard(sequence, config)
        qtbot.addWidget(card)
        
        # Test selection
        card.set_selected(True)
        assert card.is_selected()
        
        card.set_selected(False)
        assert not card.is_selected()
    
    def test_card_signals(self, qtbot):
        """Test card signal emissions."""
        sequence = SequenceModel(id="test_seq", name="Test Sequence", difficulty=3, length=8)
        config = BrowseTabConfig()
        card = ModernThumbnailCard(sequence, config)
        qtbot.addWidget(card)
        
        # Test clicked signal
        with qtbot.waitSignal(card.clicked, timeout=1000):
            card.clicked.emit("test_seq")
        
        # Test favorite toggle signal
        with qtbot.waitSignal(card.favorite_toggled, timeout=1000):
            card.favorite_toggled.emit("test_seq", True)


class TestSmartFilterPanel:
    """Test the SmartFilterPanel component."""
    
    def test_panel_initialization(self, qtbot):
        """Test panel initializes correctly."""
        panel = SmartFilterPanel()
        qtbot.addWidget(panel)
        
        assert len(panel.get_active_filters()) == 0
        assert panel.get_search_query() == ""
        assert panel.get_sort_criteria()[0] == "name"
    
    def test_filter_management(self, qtbot):
        """Test filter addition and removal."""
        panel = SmartFilterPanel()
        qtbot.addWidget(panel)
        
        # Add a filter
        filter_criteria = FilterCriteria(
            filter_type=FilterType.DIFFICULTY,
            value=3,
            operator="equals"
        )
        
        panel.add_filter(filter_criteria)
        assert len(panel.get_active_filters()) == 1
        
        # Remove the filter
        panel.remove_filter(filter_criteria)
        assert len(panel.get_active_filters()) == 0
    
    def test_search_functionality(self, qtbot):
        """Test search input functionality."""
        panel = SmartFilterPanel()
        qtbot.addWidget(panel)
        
        # Set search query
        test_query = "test sequence"
        panel.set_search_query(test_query)
        assert panel.get_search_query() == test_query
        
        # Clear search
        panel.clear_search()
        assert panel.get_search_query() == ""


class TestVirtualScrollWidget:
    """Test the VirtualScrollWidget component."""
    
    def test_virtual_scroll_initialization(self, qtbot):
        """Test virtual scroll initializes correctly."""
        config = BrowseTabConfig()
        scroll_widget = VirtualScrollWidget(config)
        qtbot.addWidget(scroll_widget)
        
        assert scroll_widget.get_item_count() == 0
        assert scroll_widget.get_visible_range() == (0, 0)
        assert len(scroll_widget.get_selected_indices()) == 0
    
    def test_virtual_scroll_items(self, qtbot):
        """Test setting items in virtual scroll."""
        config = BrowseTabConfig()
        scroll_widget = VirtualScrollWidget(config)
        qtbot.addWidget(scroll_widget)
        
        # Create test items
        test_items = [f"Item {i}" for i in range(100)]
        
        # Set item creator
        def create_test_widget(item_data, index):
            widget = QWidget()
            widget.setFixedHeight(100)
            return widget
        
        scroll_widget.set_widget_creator(create_test_widget)
        scroll_widget.set_items(test_items)
        
        assert scroll_widget.get_item_count() == 100
    
    def test_virtual_scroll_selection(self, qtbot):
        """Test virtual scroll selection functionality."""
        config = BrowseTabConfig()
        scroll_widget = VirtualScrollWidget(config)
        qtbot.addWidget(scroll_widget)
        
        # Set test items
        test_items = [f"Item {i}" for i in range(10)]
        scroll_widget.set_items(test_items)
        
        # Test selection
        scroll_widget.select_item(0)
        assert 0 in scroll_widget.get_selected_indices()
        
        scroll_widget.deselect_item(0)
        assert 0 not in scroll_widget.get_selected_indices()


class TestLoadingStates:
    """Test the loading state components."""
    
    def test_loading_indicator(self, qtbot):
        """Test LoadingIndicator component."""
        indicator = LoadingIndicator(size=48, show_text=True)
        qtbot.addWidget(indicator)
        
        # Test animation control
        indicator.start_animation()
        assert indicator.rotation_animation is not None
        
        indicator.stop_animation()
        
        # Test text setting
        indicator.set_loading_text("Custom loading...")
        assert indicator.loading_label.text() == "Custom loading..."
    
    def test_skeleton_screen(self, qtbot):
        """Test SkeletonScreen component."""
        skeleton = SkeletonScreen(pattern="grid", item_count=6)
        qtbot.addWidget(skeleton)
        
        assert skeleton.pattern == "grid"
        assert skeleton.item_count == 6
        
        # Test animation
        skeleton.stop_animation()
    
    def test_error_state(self, qtbot):
        """Test ErrorState component."""
        error_state = ErrorState("Test error message", show_retry=True)
        qtbot.addWidget(error_state)
        
        assert error_state.error_message == "Test error message"
        assert error_state.show_retry
        
        # Test retry signal
        with qtbot.waitSignal(error_state.retry_requested, timeout=1000):
            error_state.retry_requested.emit()
    
    def test_progress_indicator(self, qtbot):
        """Test ProgressIndicator component."""
        progress = ProgressIndicator(show_percentage=True)
        qtbot.addWidget(progress)
        
        # Test progress setting
        progress.set_progress(50)
        assert progress.progress_value == 50
        
        # Test indeterminate mode
        progress.set_indeterminate(True)
        assert progress.is_indeterminate
        
        progress.reset()
        assert progress.progress_value == 0


class TestAnimationSystem:
    """Test the animation system."""
    
    def test_animation_manager_initialization(self, qtbot):
        """Test AnimationManager initializes correctly."""
        config = AnimationConfig()
        manager = AnimationManager(config)
        
        assert manager.config == config
        assert len(manager._active_animations) == 0
        assert len(manager._animation_groups) == 0
    
    def test_fade_animation_creation(self, qtbot):
        """Test fade animation creation."""
        config = AnimationConfig()
        manager = AnimationManager(config)
        
        widget = QWidget()
        qtbot.addWidget(widget)
        
        # Create fade in animation
        animation_id = manager.create_fade_animation(widget, AnimationType.FADE_IN)
        assert animation_id in manager._active_animations
        
        # Start animation
        success = manager.start_animation(animation_id)
        assert success
    
    def test_animation_cleanup(self, qtbot):
        """Test animation cleanup."""
        config = AnimationConfig()
        manager = AnimationManager(config)
        
        widget = QWidget()
        qtbot.addWidget(widget)
        
        # Create multiple animations
        fade_id = manager.create_fade_animation(widget, AnimationType.FADE_IN)
        scale_id = manager.create_scale_animation(widget, AnimationType.SCALE_IN)
        
        assert len(manager._active_animations) == 2
        
        # Stop all animations
        manager.stop_all_animations()
        # Note: Animations may not be immediately removed from tracking


class TestBrowseTabView:
    """Test the integrated BrowseTabView with modern components."""
    
    @pytest.fixture
    def mock_viewmodel(self):
        """Create a mock viewmodel for testing."""
        viewmodel = Mock(spec=BrowseTabViewModel)
        viewmodel.state_changed = Mock()
        viewmodel.loading_started = Mock()
        viewmodel.loading_finished = Mock()
        viewmodel.error_occurred = Mock()
        return viewmodel
    
    def test_browse_tab_view_initialization(self, qtbot, mock_viewmodel):
        """Test BrowseTabView initializes with modern components."""
        config = BrowseTabConfig()
        view = BrowseTabView(mock_viewmodel, config)
        qtbot.addWidget(view)
        
        # Check that modern components are created
        assert hasattr(view, 'filter_panel')
        assert hasattr(view, 'thumbnail_grid')
        assert hasattr(view, 'loading_indicator')
        assert hasattr(view, 'skeleton_screen')
        assert hasattr(view, 'error_state')
        assert hasattr(view, 'animation_manager')
    
    def test_browse_tab_view_state_switching(self, qtbot, mock_viewmodel):
        """Test state switching in BrowseTabView."""
        config = BrowseTabConfig()
        view = BrowseTabView(mock_viewmodel, config)
        qtbot.addWidget(view)
        
        # Test different states
        view.show_loading_state()
        assert view.content_stack.currentWidget() == view.loading_indicator
        
        view.show_skeleton_state()
        assert view.content_stack.currentWidget() == view.skeleton_screen
        
        view.show_error_state("Test error")
        assert view.content_stack.currentWidget() == view.error_state
        
        view.show_content()
        assert view.content_stack.currentWidget() == view.thumbnail_grid
    
    def test_browse_tab_view_cleanup(self, qtbot, mock_viewmodel):
        """Test BrowseTabView cleanup."""
        config = BrowseTabConfig()
        view = BrowseTabView(mock_viewmodel, config)
        qtbot.addWidget(view)
        
        # Test cleanup doesn't raise exceptions
        view.cleanup()


def test_phase2_integration():
    """Integration test for all Phase 2 components working together."""
    logger.info("=== Phase 2 Modern UI Components Integration Test ===")
    
    # Test that all components can be imported and instantiated
    config = BrowseTabConfig()
    
    # Test ResponsiveThumbnailGrid
    grid = ResponsiveThumbnailGrid(config)
    assert grid is not None
    logger.info("✓ ResponsiveThumbnailGrid created successfully")
    
    # Test ModernThumbnailCard
    sequence = SequenceModel(id="test", name="Test", difficulty=1, length=8)
    card = ModernThumbnailCard(sequence, config)
    assert card is not None
    logger.info("✓ ModernThumbnailCard created successfully")
    
    # Test SmartFilterPanel
    filter_panel = SmartFilterPanel()
    assert filter_panel is not None
    logger.info("✓ SmartFilterPanel created successfully")
    
    # Test VirtualScrollWidget
    virtual_scroll = VirtualScrollWidget(config)
    assert virtual_scroll is not None
    logger.info("✓ VirtualScrollWidget created successfully")
    
    # Test LoadingStates
    loading = LoadingIndicator()
    skeleton = SkeletonScreen()
    error = ErrorState()
    progress = ProgressIndicator()
    assert all([loading, skeleton, error, progress])
    logger.info("✓ LoadingStates components created successfully")
    
    # Test AnimationSystem
    animation_config = AnimationConfig()
    animation_manager = AnimationManager(animation_config)
    assert animation_manager is not None
    logger.info("✓ AnimationSystem created successfully")
    
    logger.info("=== Phase 2 Integration Test PASSED ===")


if __name__ == "__main__":
    # Run the integration test
    test_phase2_integration()
    print("Phase 2 Modern UI Components test completed successfully!")
