#!/usr/bin/env python3
"""
Standalone test for Phase 1 foundation architecture.

This script tests the core foundation components without pytest dependencies.
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all core imports work."""
    print("Testing imports...")

    try:
        from browse_tab_v2.core.interfaces import (
            SequenceModel,
            FilterCriteria,
            FilterType,
            SearchCriteria,
            LoadingState,
            SortOrder,
            BrowseTabConfig,
        )

        print("✓ Core interfaces imported successfully")

        from browse_tab_v2.core.state import StateManager, BrowseState, StateAction

        print("✓ State management imported successfully")

        from browse_tab_v2.services.sequence_service import SequenceService
        from browse_tab_v2.services.filter_service import FilterService
        from browse_tab_v2.services.cache_service import CacheService

        print("✓ Services imported successfully")

        from browse_tab_v2.viewmodels.browse_tab_viewmodel import BrowseTabViewModel

        print("✓ ViewModel imported successfully")

        from browse_tab_v2 import BrowseTabV2Factory

        print("✓ Factory imported successfully")

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_basic_objects():
    """Test basic object creation."""
    print("\nTesting basic object creation...")

    try:
        from browse_tab_v2.core.interfaces import (
            SequenceModel,
            BrowseTabConfig,
            FilterCriteria,
            FilterType,
            LoadingState,
        )
        from browse_tab_v2.core.state import StateManager, BrowseState

        # Test SequenceModel
        sequence = SequenceModel(
            id="test_001",
            name="Test Sequence",
            thumbnails=["test.png"],
            difficulty=3,
            length=5,
            author="Test Author",
            tags=["test"],
        )
        assert sequence.id == "test_001"
        assert sequence.difficulty == 3
        print("✓ SequenceModel creation successful")

        # Test BrowseTabConfig
        config = BrowseTabConfig()
        assert config.max_concurrent_image_loads == 4
        assert config.default_columns == 3
        print("✓ BrowseTabConfig creation successful")

        # Test StateManager
        state_manager = StateManager()
        initial_state = state_manager.get_current_state()
        assert isinstance(initial_state, BrowseState)
        assert initial_state.loading_state == LoadingState.IDLE
        print("✓ StateManager creation successful")

        # Test FilterCriteria
        criteria = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=3, operator="equals"
        )
        assert criteria.filter_type == FilterType.DIFFICULTY
        print("✓ FilterCriteria creation successful")

        return True

    except Exception as e:
        print(f"✗ Object creation failed: {e}")
        return False


def test_state_management():
    """Test state management functionality."""
    print("\nTesting state management...")

    try:
        from browse_tab_v2.core.state import StateManager, StateAction
        from browse_tab_v2.core.interfaces import SequenceModel, LoadingState

        state_manager = StateManager()

        # Test state changes
        state_changes = []
        state_manager.state_changed.connect(lambda s: state_changes.append(s))

        # Create sample sequences
        sequences = [
            SequenceModel(
                id="seq_001",
                name="Test Sequence 1",
                thumbnails=["thumb1.png"],
                difficulty=3,
                length=8,
                author="Alice",
                tags=["test"],
            )
        ]

        # Dispatch action
        state_manager.dispatch(StateAction.LOAD_SEQUENCES, {"sequences": sequences})

        # Verify state update
        current_state = state_manager.get_current_state()
        assert len(current_state.sequences) == 1
        assert current_state.loading_state == LoadingState.LOADED
        assert len(state_changes) == 1
        print("✓ State management working correctly")

        return True

    except Exception as e:
        print(f"✗ State management test failed: {e}")
        return False


async def test_async_services():
    """Test async service functionality."""
    print("\nTesting async services...")

    try:
        from browse_tab_v2.services.sequence_service import SequenceService
        from browse_tab_v2.services.filter_service import FilterService
        from browse_tab_v2.services.cache_service import CacheService
        from browse_tab_v2.core.interfaces import (
            BrowseTabConfig,
            FilterCriteria,
            FilterType,
        )

        config = BrowseTabConfig()

        # Test SequenceService
        sequence_service = SequenceService(config=config)
        sequences = await sequence_service.get_all_sequences()
        assert isinstance(sequences, list)
        print("✓ SequenceService working correctly")

        # Test FilterService
        filter_service = FilterService(config=config)

        # Create test data
        from browse_tab_v2.core.interfaces import SequenceModel

        test_sequences = [
            SequenceModel(
                id="seq_001",
                name="Test Sequence",
                thumbnails=["test.png"],
                difficulty=3,
                length=5,
                author="Test",
                tags=["test"],
            )
        ]

        # Test filtering
        criteria = [
            FilterCriteria(
                filter_type=FilterType.DIFFICULTY, value=3, operator="equals"
            )
        ]

        filtered = await filter_service.apply_filters(test_sequences, criteria)
        assert len(filtered) == 1
        print("✓ FilterService working correctly")

        # Test CacheService
        cache_service = CacheService(config=config)
        stats = await cache_service.get_cache_stats()
        assert isinstance(stats, dict)
        print("✓ CacheService working correctly")

        return True

    except Exception as e:
        print(f"✗ Async services test failed: {e}")
        return False


def test_service_registry():
    """Test service registry functionality."""
    print("\nTesting service registry...")

    try:
        from browse_tab_v2.core.service_registry import (
            ServiceRegistry,
            configure_services,
        )
        from browse_tab_v2.core.interfaces import BrowseTabConfig, IFilterService
        from browse_tab_v2.services.filter_service import FilterService

        config = BrowseTabConfig()

        # Test registry creation
        registry = ServiceRegistry()
        registry.configure(config)

        # Test service registration
        registry.register_singleton(IFilterService, FilterService)

        # Test service resolution
        filter_service = registry.resolve(IFilterService)
        assert isinstance(filter_service, FilterService)

        # Test singleton behavior
        filter_service2 = registry.resolve(IFilterService)
        assert filter_service is filter_service2

        print("✓ Service registry working correctly")
        return True

    except Exception as e:
        print(f"✗ Service registry test failed: {e}")
        return False


async def main():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("BROWSE TAB V2 - PHASE 1 FOUNDATION TESTS")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Basic Object Tests", test_basic_objects),
        ("State Management Tests", test_state_management),
        ("Async Services Tests", test_async_services),
        ("Service Registry Tests", test_service_registry),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)

        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")

        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 60)
    print(f"PHASE 1 TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL PHASE 1 TESTS PASSED!")
        print("\n✅ Phase 1 Foundation Architecture is working correctly!")
        print("✅ Ready to proceed to Phase 2: Modern UI Components")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
