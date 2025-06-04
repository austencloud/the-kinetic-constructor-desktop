#!/usr/bin/env python3
"""
Direct test for the FilterCriteria fix - specifically testing the greater_than_or_equal operator.

This script directly tests the FilterCriteria class and the smart filter panel functionality
without needing to launch the full application.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_filter_criteria_operators():
    """Test that FilterCriteria accepts the new operators."""
    print("Testing FilterCriteria operators...")

    try:
        from src.browse_tab_v2.core.interfaces import FilterCriteria, FilterType

        # Test the original operators
        print("✅ Testing original operators...")

        criteria1 = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=3, operator="equals"
        )
        print(f"✅ 'equals' operator works: {criteria1}")

        criteria2 = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=3, operator="greater_than"
        )
        print(f"✅ 'greater_than' operator works: {criteria2}")

        # Test the new operators that were causing the error
        print("\n✅ Testing new operators...")

        criteria3 = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=4, operator="greater_than_or_equal"
        )
        print(f"✅ 'greater_than_or_equal' operator works: {criteria3}")

        criteria4 = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=2, operator="less_than_or_equal"
        )
        print(f"✅ 'less_than_or_equal' operator works: {criteria4}")

        print("\n🎉 All FilterCriteria operators work correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing FilterCriteria: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_filter_service_operators():
    """Test that FilterService can handle the new operators."""
    print("\nTesting FilterService with new operators...")

    try:
        from src.browse_tab_v2.core.interfaces import (
            FilterCriteria,
            FilterType,
            SequenceModel,
        )
        from src.browse_tab_v2.services.filter_service import FilterService
        from src.browse_tab_v2.core.interfaces import BrowseTabConfig

        # Create test config
        config = BrowseTabConfig()

        # Create filter service
        filter_service = FilterService(config=config)

        # Create test sequences
        sequences = [
            SequenceModel(
                id="seq1",
                name="Easy Sequence",
                thumbnails=["test1.png"],
                difficulty=1,
                length=4,
                author="Test",
                tags=[],
                is_favorite=False,
            ),
            SequenceModel(
                id="seq2",
                name="Medium Sequence",
                thumbnails=["test2.png"],
                difficulty=3,
                length=6,
                author="Test",
                tags=[],
                is_favorite=False,
            ),
            SequenceModel(
                id="seq3",
                name="Hard Sequence",
                thumbnails=["test3.png"],
                difficulty=5,
                length=8,
                author="Test",
                tags=[],
                is_favorite=True,
            ),
        ]

        # Test greater_than_or_equal filter (this was the failing case)
        print("Testing greater_than_or_equal filter...")
        criteria = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=3, operator="greater_than_or_equal"
        )

        # This should work now without throwing ValueError
        import asyncio

        async def test_filter():
            filtered = await filter_service.apply_filters(sequences, [criteria])
            return filtered

        filtered_sequences = asyncio.run(test_filter())

        # Should return sequences with difficulty >= 3 (seq2 and seq3)
        expected_count = 2
        actual_count = len(filtered_sequences)

        if actual_count == expected_count:
            print(
                f"✅ greater_than_or_equal filter works correctly: {actual_count} sequences returned"
            )
            for seq in filtered_sequences:
                print(f"   - {seq.name} (difficulty: {seq.difficulty})")
        else:
            print(
                f"❌ Filter returned {actual_count} sequences, expected {expected_count}"
            )
            return False

        # Test less_than_or_equal filter
        print("\nTesting less_than_or_equal filter...")
        criteria2 = FilterCriteria(
            filter_type=FilterType.DIFFICULTY, value=3, operator="less_than_or_equal"
        )

        async def test_filter2():
            filtered = await filter_service.apply_filters(sequences, [criteria2])
            return filtered

        filtered_sequences2 = asyncio.run(test_filter2())

        # Should return sequences with difficulty <= 3 (seq1 and seq2)
        expected_count2 = 2
        actual_count2 = len(filtered_sequences2)

        if actual_count2 == expected_count2:
            print(
                f"✅ less_than_or_equal filter works correctly: {actual_count2} sequences returned"
            )
            for seq in filtered_sequences2:
                print(f"   - {seq.name} (difficulty: {seq.difficulty})")
        else:
            print(
                f"❌ Filter returned {actual_count2} sequences, expected {expected_count2}"
            )
            return False

        print("\n🎉 All FilterService operators work correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing FilterService: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_smart_filter_panel_creation():
    """Test that SmartFilterPanel can be created without errors."""
    print("\nTesting SmartFilterPanel creation...")

    try:
        # We need PyQt6 for this test
        from PyQt6.QtWidgets import QApplication
        import sys

        # Create minimal QApplication if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        from src.browse_tab_v2.components.smart_filter_panel import SmartFilterPanel

        # Create the panel
        panel = SmartFilterPanel()

        print("✅ SmartFilterPanel created successfully")

        # Test that the high difficulty quick filter can be added
        print("Testing high difficulty quick filter...")

        # This should not raise a ValueError anymore
        panel._add_quick_filter("high_difficulty")

        print("✅ High difficulty quick filter added successfully")

        print("\n🎉 SmartFilterPanel works correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing SmartFilterPanel: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING BROWSE TAB V2 FILTER CRITERIA FIX")
    print("=" * 60)

    all_passed = True

    # Test 1: FilterCriteria operators
    if not test_filter_criteria_operators():
        all_passed = False

    # Test 2: FilterService with new operators
    if not test_filter_service_operators():
        all_passed = False

    # Test 3: SmartFilterPanel creation
    if not test_smart_filter_panel_creation():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The FilterCriteria fix is working correctly.")
        print("✅ The 'greater_than_or_equal' operator error has been resolved.")
        print("✅ High difficulty button should now work without errors.")
    else:
        print("❌ SOME TESTS FAILED! Please review the errors above.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
