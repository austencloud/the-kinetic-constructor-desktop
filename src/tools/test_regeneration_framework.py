#!/usr/bin/env python3
"""
Dictionary Regeneration Testing Framework

This framework provides comprehensive testing for the dictionary regeneration system.
It must be executed from within the main application where main_widget is available.

Usage:
    From within the application:
    from tools.test_regeneration_framework import run_regeneration_test
    run_regeneration_test(main_widget)
"""

import os
import json
import time
from typing import Dict, Optional, List, Tuple
from PIL import Image


def run_regeneration_test(main_widget) -> bool:
    """
    Execute the complete regeneration testing sequence.

    Args:
        main_widget: The main widget instance from the application

    Returns:
        True if all tests pass and regeneration is successful
    """
    print("🧪 DICTIONARY REGENERATION TESTING FRAMEWORK")
    print("=" * 70)
    print("Testing the working dictionary regeneration system...")

    # Phase 1: Initial Test
    print("\n📋 PHASE 1: INITIAL TEST (5 images)")
    print("-" * 50)

    phase1_success = _run_phase1_test(main_widget)

    if not phase1_success:
        print("\n❌ PHASE 1 FAILED - Stopping test sequence")
        return False

    # Manual verification prompt
    print("\n🔍 MANUAL VERIFICATION REQUIRED")
    print("-" * 50)
    verification_passed = _prompt_manual_verification()

    if not verification_passed:
        print("\n❌ MANUAL VERIFICATION FAILED - Stopping test sequence")
        return False

    # Phase 2: Full Regeneration
    print("\n📋 PHASE 2: FULL REGENERATION (all images)")
    print("-" * 50)

    user_consent = (
        input("Proceed with full regeneration of all 437 images? (y/N): ")
        .lower()
        .strip()
    )
    if user_consent != "y":
        print("⏸️  Full regeneration cancelled by user")
        return True  # Phase 1 was successful

    phase2_success = _run_phase2_full_regeneration(main_widget)

    if phase2_success:
        print("\n🎉 ALL PHASES COMPLETED SUCCESSFULLY!")
        print(
            "💡 Dictionary images have been regenerated with real kinetic sequence diagrams"
        )
        return True
    else:
        print("\n❌ PHASE 2 FAILED")
        return False


def _run_phase1_test(main_widget) -> bool:
    """Run Phase 1: Initial test with 5 images."""
    try:
        from tools.working_dictionary_regenerator import test_regeneration

        print("⏳ Running test regeneration (5 images)...")
        start_time = time.time()

        success = test_regeneration(main_widget)

        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️  Phase 1 completed in {duration:.1f} seconds")

        if success:
            print("✅ Phase 1 test completed successfully!")

            # Analyze the test results
            _analyze_test_results()

            return True
        else:
            print("❌ Phase 1 test failed!")
            return False

    except Exception as e:
        print(f"❌ Phase 1 test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def _analyze_test_results() -> None:
    """Analyze the results of the test regeneration."""
    print("\n📊 ANALYZING TEST RESULTS...")

    try:
        from utils.path_helpers import get_dictionary_path

        dictionary_path = get_dictionary_path()

        # Find recently modified images (within last 5 minutes)
        recent_images = []
        current_time = time.time()

        for item in os.listdir(dictionary_path):
            item_path = os.path.join(dictionary_path, item)
            if os.path.isdir(item_path):
                for file in os.listdir(item_path):
                    if file.endswith(".png"):
                        file_path = os.path.join(item_path, file)
                        mod_time = os.path.getmtime(file_path)
                        if current_time - mod_time < 300:  # 5 minutes
                            recent_images.append((file_path, item, file))

        print(f"📈 Found {len(recent_images)} recently modified images")

        if recent_images:
            print("\n🔍 SAMPLE ANALYSIS:")
            for i, (file_path, word, filename) in enumerate(recent_images[:3]):
                print(f"\n   Sample {i+1}: {word}/{filename}")
                _analyze_single_image(file_path)

    except Exception as e:
        print(f"⚠️  Analysis error: {e}")


def _analyze_single_image(image_path: str) -> None:
    """Analyze a single regenerated image."""
    try:
        with Image.open(image_path) as img:
            print(f"      Size: {img.size}")
            print(f"      Mode: {img.mode}")

            # Check if it's a blank gray image
            colors = img.getcolors(maxcolors=256 * 256 * 256)
            if colors and len(colors) <= 5:
                print(f"      Colors: {len(colors)} (simple - check if blank)")
                for count, color in colors[:2]:
                    if color == (240, 240, 240, 255) or color == (240, 240, 240):
                        print(
                            f"      ⚠️  DETECTED BLANK GRAY: {count} pixels of {color}"
                        )
                    else:
                        print(f"      ✅ Non-blank color: {count} pixels of {color}")
            else:
                print(
                    f"      ✅ Complex image: {len(colors) if colors else 'many'} colors (likely real diagram)"
                )

            # Check metadata
            if hasattr(img, "text") and "metadata" in img.text:
                print(f"      ✅ Metadata: Present")
            else:
                print(f"      ⚠️  Metadata: Missing")

    except Exception as e:
        print(f"      ❌ Analysis error: {e}")


def _prompt_manual_verification() -> bool:
    """Prompt user for manual verification of regenerated images."""
    print("Please manually verify the regenerated images:")
    print()
    print("1. Navigate to the dictionary folder and open 2-3 recently modified images")
    print("2. Verify each image contains:")
    print("   ✅ Actual kinetic sequence diagrams (NOT blank gray rectangles)")
    print("   ✅ Beat drawings with arrows and notation")
    print("   ✅ Professional overlays (word names, difficulty levels, beat numbers)")
    print("   ✅ Proper dimensions (800x600) and clear visual quality")
    print()
    print("3. Check that images are NOT:")
    print("   ❌ Blank gray rectangles (240, 240, 240 color)")
    print("   ❌ Placeholder text or simple colored shapes")
    print("   ❌ Corrupted or malformed images")
    print()

    while True:
        response = (
            input(
                "Do the regenerated images contain REAL kinetic sequence diagrams? (y/n/help): "
            )
            .lower()
            .strip()
        )

        if response == "y":
            print("✅ Manual verification PASSED")
            return True
        elif response == "n":
            print("❌ Manual verification FAILED")
            print(
                "💡 The regeneration system is still creating blank/placeholder images"
            )
            return False
        elif response == "help":
            _show_verification_help()
        else:
            print("Please enter 'y' for yes, 'n' for no, or 'help' for assistance")


def _show_verification_help() -> None:
    """Show detailed help for manual verification."""
    print("\n📖 VERIFICATION HELP:")
    print("-" * 30)
    print("WHAT TO LOOK FOR:")
    print("✅ GOOD (Real sequence diagrams):")
    print("   - Complex drawings with stick figures in different poses")
    print("   - Arrows showing movement directions")
    print("   - Beat numbers (1, 2, 3, etc.) on each beat")
    print("   - Reversal symbols (if applicable)")
    print("   - Word name displayed prominently")
    print("   - Difficulty level indicator")
    print("   - Multiple colors and detailed graphics")
    print()
    print("❌ BAD (Still broken):")
    print("   - Solid gray rectangles")
    print("   - Simple text on plain background")
    print("   - 'Placeholder' or 'Mock' text")
    print("   - Single solid color with minimal content")
    print("   - Missing beat diagrams or stick figures")
    print()


def _run_phase2_full_regeneration(main_widget) -> bool:
    """Run Phase 2: Full regeneration of all images."""
    try:
        from tools.working_dictionary_regenerator import full_regeneration

        print("⏳ Running full regeneration (all 437 images)...")
        print("⚠️  This may take several minutes...")

        start_time = time.time()

        success = full_regeneration(main_widget)

        end_time = time.time()
        duration = end_time - start_time

        print(
            f"⏱️  Phase 2 completed in {duration:.1f} seconds ({duration/60:.1f} minutes)"
        )

        if success:
            print("✅ Phase 2 full regeneration completed successfully!")

            # Final verification
            _final_verification_prompt()

            return True
        else:
            print("❌ Phase 2 full regeneration failed!")
            return False

    except Exception as e:
        print(f"❌ Phase 2 error: {e}")
        import traceback

        traceback.print_exc()
        return False


def _final_verification_prompt() -> None:
    """Prompt for final verification after full regeneration."""
    print("\n🎉 FULL REGENERATION COMPLETE!")
    print("-" * 40)
    print("NEXT STEPS:")
    print("1. Clear browse tab cache to see new images")
    print("2. Restart the application if needed")
    print("3. Check browse tab for professional sequence cards")
    print("4. Verify random samples show real kinetic diagrams")
    print()
    print("💡 All 436+ dictionary images should now display as professional")
    print("   sequence cards with real kinetic notation diagrams!")


# Convenience function for quick testing
def quick_test(main_widget):
    """Quick test function for immediate use."""
    print("🚀 QUICK REGENERATION TEST")
    print("=" * 40)

    try:
        from tools.working_dictionary_regenerator import test_regeneration

        success = test_regeneration(main_widget)

        if success:
            print("\n✅ Quick test PASSED!")
            print("💡 Ready for full regeneration")
        else:
            print("\n❌ Quick test FAILED!")
            print("💡 Check the error messages above")

        return success

    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False


if __name__ == "__main__":
    print("This testing framework must be run from within the application context.")
    print("Usage: run_regeneration_test(main_widget)")
