#!/usr/bin/env python3
"""
Execute Dictionary Regeneration

This script provides easy execution of the dictionary regeneration system
from within the main application context.

INSTRUCTIONS FOR EXECUTION:
===========================

1. From within the running application, open a Python console or debug interface
2. Execute the following commands:

   # Import the execution function
   from tools.execute_regeneration import execute_regeneration_test

   # Run the test (replace 'main_widget' with your actual main widget instance)
   execute_regeneration_test(main_widget)

3. Follow the prompts for Phase 1 testing and manual verification
4. If Phase 1 succeeds, proceed with full regeneration

EXPECTED RESULTS:
================
- Phase 1: 5 images regenerated with >80% success rate
- Manual verification: Images contain real kinetic sequence diagrams
- Phase 2: All 437 images regenerated successfully
- Final result: Professional sequence cards with real diagrams

"""


def execute_regeneration_test(main_widget):
    """
    Execute the complete regeneration test sequence.

    This is the main entry point for testing the dictionary regeneration system.
    Uses the direct approach that bypasses potential beat frame issues.

    Args:
        main_widget: The main widget instance from the application
    """
    print("🎨 EXECUTING DICTIONARY REGENERATION TEST (DIRECT APPROACH)")
    print("=" * 60)

    # Validate main_widget
    if not _validate_main_widget_for_direct(main_widget):
        return False

    # Try the direct approach first (most likely to work)
    print("🚀 Attempting DIRECT regeneration using sequence card pipeline...")
    try:
        from tools.direct_dictionary_regenerator import test_direct_regeneration

        success = test_direct_regeneration(main_widget)

        if success:
            print("✅ DIRECT approach succeeded!")

            # Ask for manual verification
            verification = (
                input(
                    "Do the regenerated images contain REAL sequence diagrams (not blank gray)? (y/N): "
                )
                .lower()
                .strip()
            )
            if verification == "y":
                print("✅ Manual verification passed!")

                # Offer full regeneration
                full_regen = (
                    input("Proceed with full regeneration (all 437 images)? (y/N): ")
                    .lower()
                    .strip()
                )
                if full_regen == "y":
                    from tools.direct_dictionary_regenerator import (
                        full_direct_regeneration,
                    )

                    return full_direct_regeneration(main_widget)
                else:
                    print("⏸️  Full regeneration cancelled")
                    return True
            else:
                print("❌ Manual verification failed - trying fallback approach")
        else:
            print("⚠️  DIRECT approach failed - trying fallback approach")

    except Exception as e:
        print(f"⚠️  DIRECT approach error: {e}")
        print("Trying fallback approach...")

    # Fallback to original approach
    print("\n🔄 Attempting FALLBACK regeneration using beat frame approach...")
    try:
        from tools.test_regeneration_framework import run_regeneration_test

        return run_regeneration_test(main_widget)

    except ImportError as e:
        print(f"❌ Failed to import testing framework: {e}")
        print("💡 Make sure test_regeneration_framework.py is available")
        return False
    except Exception as e:
        print(f"❌ Execution error: {e}")
        import traceback

        traceback.print_exc()
        return False


def _validate_main_widget_for_direct(main_widget) -> bool:
    """Validate that the main_widget has the required components for direct approach."""
    print("🔍 Validating main widget for direct approach...")

    if main_widget is None:
        print("❌ main_widget is None")
        return False

    if not hasattr(main_widget, "sequence_card_tab"):
        print("❌ main_widget missing sequence_card_tab")
        return False

    if main_widget.sequence_card_tab is None:
        print("❌ sequence_card_tab is None")
        return False

    if not hasattr(main_widget.sequence_card_tab, "image_exporter"):
        print("❌ sequence_card_tab missing image_exporter")
        return False

    if main_widget.sequence_card_tab.image_exporter is None:
        print("❌ image_exporter is None")
        return False

    print("✅ main_widget validation passed for direct approach")
    return True


def _validate_main_widget(main_widget) -> bool:
    """Validate that the main_widget has the required components."""
    print("🔍 Validating main widget...")

    if main_widget is None:
        print("❌ main_widget is None")
        return False

    if not hasattr(main_widget, "sequence_workbench"):
        print("❌ main_widget missing sequence_workbench")
        return False

    if main_widget.sequence_workbench is None:
        print("❌ sequence_workbench is None")
        return False

    if not hasattr(main_widget.sequence_workbench, "sequence_beat_frame"):
        print("❌ sequence_workbench missing sequence_beat_frame")
        return False

    if main_widget.sequence_workbench.sequence_beat_frame is None:
        print("❌ sequence_beat_frame is None")
        return False

    print("✅ main_widget validation passed")
    return True


def quick_regeneration_test(main_widget):
    """
    Quick test function for immediate validation.

    This runs just the Phase 1 test (5 images) for quick validation.
    Uses the direct approach first, then fallback.
    """
    print("🚀 QUICK REGENERATION TEST (DIRECT APPROACH)")
    print("=" * 40)

    # Try direct approach first
    if _validate_main_widget_for_direct(main_widget):
        try:
            from tools.direct_dictionary_regenerator import test_direct_regeneration

            print("🎯 Using direct sequence card pipeline...")
            return test_direct_regeneration(main_widget)
        except Exception as e:
            print(f"⚠️  Direct approach failed: {e}")

    # Fallback to original approach
    print("🔄 Falling back to beat frame approach...")
    if not _validate_main_widget(main_widget):
        return False

    try:
        from tools.test_regeneration_framework import quick_test

        return quick_test(main_widget)

    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False


def manual_regeneration_steps(main_widget):
    """
    Manual step-by-step regeneration for debugging.

    This provides manual control over each step of the regeneration process.
    """
    print("🔧 MANUAL REGENERATION STEPS")
    print("=" * 40)

    if not _validate_main_widget(main_widget):
        return False

    print("\nStep 1: Import regeneration functions")
    try:
        from tools.working_dictionary_regenerator import (
            test_regeneration,
            full_regeneration,
        )

        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    print("\nStep 2: Run test regeneration")
    user_input = (
        input("Proceed with test regeneration (5 images)? (y/N): ").lower().strip()
    )
    if user_input != "y":
        print("⏸️  Test cancelled")
        return False

    try:
        success = test_regeneration(main_widget)
        if success:
            print("✅ Test regeneration successful")
        else:
            print("❌ Test regeneration failed")
            return False
    except Exception as e:
        print(f"❌ Test regeneration error: {e}")
        return False

    print("\nStep 3: Manual verification required")
    print("Please check the regenerated images manually:")
    print("- Open 2-3 recently modified dictionary images")
    print("- Verify they contain real kinetic sequence diagrams")
    print("- Check for professional overlays (word names, beat numbers, etc.)")

    verification = (
        input("Do images contain REAL sequence diagrams (not blank gray)? (y/N): ")
        .lower()
        .strip()
    )
    if verification != "y":
        print("❌ Manual verification failed")
        print("💡 The regeneration system still needs debugging")
        return False

    print("✅ Manual verification passed")

    print("\nStep 4: Full regeneration")
    full_regen = (
        input("Proceed with full regeneration (all 437 images)? (y/N): ")
        .lower()
        .strip()
    )
    if full_regen != "y":
        print("⏸️  Full regeneration cancelled")
        return True  # Test was successful

    try:
        success = full_regeneration(main_widget)
        if success:
            print("✅ Full regeneration successful")
            print("🎉 All dictionary images regenerated!")
        else:
            print("❌ Full regeneration failed")
            return False
    except Exception as e:
        print(f"❌ Full regeneration error: {e}")
        return False

    return True


def show_usage_instructions():
    """Show detailed usage instructions."""
    print("📖 DICTIONARY REGENERATION USAGE INSTRUCTIONS")
    print("=" * 60)
    print()
    print("OPTION 1: Complete Test Sequence")
    print("-" * 30)
    print("from tools.execute_regeneration import execute_regeneration_test")
    print("execute_regeneration_test(main_widget)")
    print()
    print("OPTION 2: Quick Test Only")
    print("-" * 20)
    print("from tools.execute_regeneration import quick_regeneration_test")
    print("quick_regeneration_test(main_widget)")
    print()
    print("OPTION 3: Manual Step-by-Step")
    print("-" * 25)
    print("from tools.execute_regeneration import manual_regeneration_steps")
    print("manual_regeneration_steps(main_widget)")
    print()
    print("OPTION 4: Direct Function Calls")
    print("-" * 30)
    print(
        "from tools.working_dictionary_regenerator import test_regeneration, full_regeneration"
    )
    print("test_regeneration(main_widget)  # Test with 5 images")
    print("full_regeneration(main_widget)  # Process all images")
    print()
    print("CRITICAL SUCCESS CRITERIA:")
    print("- Regenerated images must contain actual kinetic sequence diagrams")
    print("- Success rate must exceed 80%")
    print("- Manual verification must confirm visual quality")
    print()
    print("🎯 GOAL: Transform blank gray rectangles into professional sequence cards!")


if __name__ == "__main__":
    print("This script must be executed from within the application context.")
    print("The main_widget instance must be available.")
    print()
    show_usage_instructions()
