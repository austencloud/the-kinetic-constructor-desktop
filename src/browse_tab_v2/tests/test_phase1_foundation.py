"""
Test suite for Phase 1 foundation architecture.

This test suite validates that the core foundation components
are working correctly before proceeding to Phase 2.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from typing import List

# Import core components
from ..core.interfaces import (
    SequenceModel, FilterCriteria, FilterType, SearchCriteria,
    LoadingState, SortOrder, BrowseTabConfig
)
from ..core.state import StateManager, BrowseState, StateAction
from ..services.sequence_service import SequenceService
from ..services.filter_service import FilterService
from ..services.cache_service import CacheService
from ..services.image_loader import AsyncImageLoader
from ..services.performance_monitor import PerformanceMonitor
from ..viewmodels.browse_tab_viewmodel import BrowseTabViewModel
from ..core.service_registry import ServiceRegistry, configure_services
from .. import BrowseTabV2Factory


class TestPhase1Foundation:
    """Test Phase 1 foundation components."""
    
    @pytest.fixture
    def sample_sequences(self) -> List[SequenceModel]:
        """Create sample sequence data for testing."""
        return [
            SequenceModel(
                id="seq_001",
                name="Test Sequence 1",
                thumbnails=["thumb1.png"],
                difficulty=3,
                length=8,
                author="Alice",
                tags=["beginner", "flow"],
                is_favorite=False
            ),
            SequenceModel(
                id="seq_002", 
                name="Advanced Flow",
                thumbnails=["thumb2.png"],
                difficulty=5,
                length=12,
                author="Bob",
                tags=["advanced", "dynamic"],
                is_favorite=True
            ),
            SequenceModel(
                id="seq_003",
                name="Static Poses",
                thumbnails=["thumb3.png"],
                difficulty=2,
                length=6,
                author="Charlie",
                tags=["beginner", "static"],
                is_favorite=False
            )
        ]
    
    @pytest.fixture
    def config(self) -> BrowseTabConfig:
        """Create test configuration."""
        return BrowseTabConfig(
            max_concurrent_image_loads=2,
            image_cache_size=50,
            enable_performance_monitoring=True,
            enable_debug_logging=True
        )
    
    def test_sequence_model_creation(self):
        """Test SequenceModel creation and properties."""
        sequence = SequenceModel(
            id="test_001",
            name="Test Sequence",
            thumbnails=["test.png"],
            difficulty=3,
            length=5,
            author="Test Author",
            tags=["test", "example"]
        )
        
        assert sequence.id == "test_001"
        assert sequence.name == "Test Sequence"
        assert sequence.difficulty == 3
        assert sequence.length == 5
        assert sequence.author == "Test Author"
        assert "test" in sequence.tags
        assert not sequence.is_favorite  # Default value
        assert isinstance(sequence.metadata, dict)
    
    def test_filter_criteria_creation(self):
        """Test FilterCriteria creation and validation."""
        criteria = FilterCriteria(
            filter_type=FilterType.DIFFICULTY,
            value=3,
            operator="equals"
        )
        
        assert criteria.filter_type == FilterType.DIFFICULTY
        assert criteria.value == 3
        assert criteria.operator == "equals"
        
        # Test invalid operator
        with pytest.raises(ValueError):
            FilterCriteria(
                filter_type=FilterType.DIFFICULTY,
                value=3,
                operator="invalid_operator"
            )
    
    def test_state_manager_initialization(self):
        """Test StateManager initialization and basic operations."""
        state_manager = StateManager()
        
        # Test initial state
        initial_state = state_manager.get_current_state()
        assert isinstance(initial_state, BrowseState)
        assert initial_state.sequences == []
        assert initial_state.loading_state == LoadingState.IDLE
        assert initial_state.grid_columns == 3
    
    def test_state_manager_updates(self, sample_sequences):
        """Test StateManager state updates."""
        state_manager = StateManager()
        
        # Track state changes
        state_changes = []
        state_manager.state_changed.connect(lambda s: state_changes.append(s))
        
        # Update state
        state_manager.dispatch(StateAction.LOAD_SEQUENCES, {
            'sequences': sample_sequences
        })
        
        # Verify update
        current_state = state_manager.get_current_state()
        assert len(current_state.sequences) == 3
        assert len(state_changes) == 1
        assert current_state.loading_state == LoadingState.LOADED
    
    def test_state_immutability(self):
        """Test that state objects are immutable."""
        state_manager = StateManager()
        original_state = state_manager.get_current_state()
        
        # Update state
        state_manager.dispatch(StateAction.SET_GRID_COLUMNS, {'columns': 4})
        new_state = state_manager.get_current_state()
        
        # Verify immutability
        assert original_state.grid_columns == 3
        assert new_state.grid_columns == 4
        assert original_state.state_id != new_state.state_id
    
    @pytest.mark.asyncio
    async def test_sequence_service_basic_operations(self, sample_sequences, config):
        """Test SequenceService basic operations."""
        # Mock json_manager
        mock_json_manager = Mock()
        mock_json_manager.loader_saver.load_json_file.return_value = {}
        
        service = SequenceService(json_manager=mock_json_manager, config=config)
        
        # Test with empty data (should return empty list)
        sequences = await service.get_all_sequences()
        assert isinstance(sequences, list)
        
        # Test performance stats
        stats = service.get_performance_stats()
        assert isinstance(stats, dict)
        assert 'total_sequences' in stats
    
    @pytest.mark.asyncio
    async def test_filter_service_operations(self, sample_sequences, config):
        """Test FilterService operations."""
        service = FilterService(config=config)
        
        # Test filter application
        criteria = [FilterCriteria(
            filter_type=FilterType.DIFFICULTY,
            value=3,
            operator="equals"
        )]
        
        filtered = await service.apply_filters(sample_sequences, criteria)
        assert len(filtered) == 1
        assert filtered[0].difficulty == 3
        
        # Test sorting
        sorted_sequences = await service.sort_sequences(
            sample_sequences,
            "name",
            SortOrder.ASC
        )
        
        assert len(sorted_sequences) == 3
        assert sorted_sequences[0].name <= sorted_sequences[1].name
    
    @pytest.mark.asyncio
    async def test_cache_service_operations(self, config):
        """Test CacheService operations."""
        service = CacheService(config=config)
        
        # Test cache stats
        stats = await service.get_cache_stats()
        assert isinstance(stats, dict)
        assert 'total_requests' in stats
        
        # Test cache clear
        await service.clear_cache()
        
        # Verify stats reset
        stats_after_clear = await service.get_cache_stats()
        assert stats_after_clear['total_requests'] == 0
    
    def test_performance_monitor_operations(self, config):
        """Test PerformanceMonitor operations."""
        monitor = PerformanceMonitor(config=config)
        
        # Test timer operations
        timer_id = monitor.start_timer("test_operation")
        assert timer_id is not None
        
        time.sleep(0.01)  # Small delay
        duration = monitor.stop_timer(timer_id)
        assert duration > 0
        
        # Test metric recording
        monitor.record_metric("test_metric", 100.0, "ms", "test")
        
        # Test performance report
        report = monitor.get_performance_report()
        assert isinstance(report, dict)
        assert 'timing' in report
    
    def test_service_registry_operations(self, config):
        """Test ServiceRegistry operations."""
        registry = ServiceRegistry()
        registry.configure(config)
        
        # Test service registration
        from ..core.interfaces import IFilterService
        from ..services.filter_service import FilterService
        
        registry.register_singleton(IFilterService, FilterService)
        
        # Test service resolution
        filter_service = registry.resolve(IFilterService)
        assert isinstance(filter_service, FilterService)
        
        # Test singleton behavior
        filter_service2 = registry.resolve(IFilterService)
        assert filter_service is filter_service2
    
    @pytest.mark.asyncio
    async def test_viewmodel_initialization(self, config):
        """Test BrowseTabViewModel initialization."""
        # Create mock services
        mock_state_manager = Mock(spec=StateManager)
        mock_state_manager.get_current_state.return_value = BrowseState()
        mock_state_manager.state_changed = Mock()
        mock_state_manager.state_changed.connect = Mock()
        
        mock_sequence_service = AsyncMock()
        mock_filter_service = AsyncMock()
        mock_cache_service = AsyncMock()
        mock_image_loader = Mock()
        
        # Create ViewModel
        viewmodel = BrowseTabViewModel(
            state_manager=mock_state_manager,
            sequence_service=mock_sequence_service,
            filter_service=mock_filter_service,
            cache_service=mock_cache_service,
            image_loader=mock_image_loader,
            config=config
        )
        
        assert viewmodel is not None
        assert viewmodel.config == config
    
    def test_factory_creation(self):
        """Test BrowseTabV2Factory creation."""
        # Test factory with mock services
        mock_services = {
            'sequence_service': AsyncMock(),
            'filter_service': AsyncMock(),
            'cache_service': AsyncMock(),
            'image_loader': Mock()
        }
        
        browse_tab = BrowseTabV2Factory.create_for_testing(mock_services)
        assert browse_tab is not None
        assert not browse_tab.is_initialized()
    
    def test_configuration_validation(self):
        """Test configuration validation and defaults."""
        # Test default configuration
        config = BrowseTabConfig()
        assert config.max_concurrent_image_loads == 4
        assert config.image_cache_size == 200
        assert config.default_columns == 3
        assert config.min_item_width == 280
        
        # Test custom configuration
        custom_config = BrowseTabConfig(
            max_concurrent_image_loads=8,
            image_cache_size=500,
            default_columns=4
        )
        assert custom_config.max_concurrent_image_loads == 8
        assert custom_config.image_cache_size == 500
        assert custom_config.default_columns == 4


if __name__ == "__main__":
    # Run basic smoke test
    print("Running Phase 1 Foundation Tests...")
    
    # Test basic imports
    try:
        from ..core.interfaces import SequenceModel, BrowseTabConfig
        from ..core.state import StateManager
        from ..services.sequence_service import SequenceService
        from .. import BrowseTabV2Factory
        print("✓ All imports successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        exit(1)
    
    # Test basic object creation
    try:
        config = BrowseTabConfig()
        state_manager = StateManager()
        print("✓ Basic object creation successful")
    except Exception as e:
        print(f"✗ Object creation failed: {e}")
        exit(1)
    
    print("Phase 1 Foundation Tests Completed Successfully! ✓")
    print("\nReady to proceed to Phase 2: Modern UI Components")
