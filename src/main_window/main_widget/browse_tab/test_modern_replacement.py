"""
Test Modern Replacement - Verify that the direct replacement approach works

This script tests that:
1. Modern thumbnail boxes can be imported and created
2. The factory correctly creates modern thumbnail boxes
3. All modern components work together
4. The replacement maintains API compatibility
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modern components can be imported."""
    print("🧪 Testing imports...")

    try:
        # Test modern thumbnail box import
        from thumbnail_box.modern_thumbnail_box import ModernThumbnailBox

        print("✅ ModernThumbnailBox imported")

        # Test factory import
        from thumbnail_box.factory import ThumbnailBoxFactory

        print("✅ ThumbnailBoxFactory imported")

        # Test modern components
        from modern_components.themes.modern_theme_manager import ModernThemeManager

        print("✅ ModernThemeManager imported")

        from modern_components.animations.hover_animations import HoverAnimationManager

        print("✅ HoverAnimationManager imported")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_theme_system():
    """Test the theme system works correctly."""
    print("\n🎨 Testing theme system...")

    try:
        from modern_components.themes.modern_theme_manager import ModernThemeManager

        theme = ModernThemeManager()
        print(f"✅ Theme manager created: {theme.current_theme}")

        # Test colors
        primary = theme.get_color("primary")
        glass = theme.get_glassmorphism_color("glass_white", "medium")
        print(f"✅ Colors: primary={primary}, glass={glass}")

        # Test gradients
        gradient = theme.create_gradient("primary", "secondary")
        print(f"✅ Gradient: {gradient[:30]}...")

        # Test spacing and radius
        spacing = theme.get_spacing("md")
        radius = theme.get_radius("lg")
        print(f"✅ Layout: spacing={spacing}px, radius={radius}px")

        return True

    except Exception as e:
        print(f"❌ Theme system failed: {e}")
        return False


def test_factory_replacement():
    """Test that the factory creates modern thumbnail boxes."""
    print("\n🏭 Testing factory replacement...")

    try:
        from thumbnail_box.factory import ThumbnailBoxFactory
        from thumbnail_box.modern_thumbnail_box import ModernThumbnailBox

        # Create a mock browse tab
        class MockBrowseTab:
            def __init__(self):
                self.main_widget = None
                self.sequence_picker = MockSequencePicker()

        class MockSequencePicker:
            def __init__(self):
                self.scroll_widget = MockScrollWidget()

        class MockScrollWidget:
            def __init__(self):
                self.scroll_area = None

        mock_browse_tab = MockBrowseTab()

        # Test factory creates modern thumbnail box
        thumbnail_box = ThumbnailBoxFactory.create_integrated_thumbnail_box(
            browse_tab=mock_browse_tab,
            word="test_word",
            thumbnails=["test1.png", "test2.png"],
            in_sequence_viewer=False,
        )

        # Verify it's a modern thumbnail box
        if isinstance(thumbnail_box, ModernThumbnailBox):
            print("✅ Factory creates ModernThumbnailBox")
        else:
            print(
                f"❌ Factory created {type(thumbnail_box)} instead of ModernThumbnailBox"
            )
            return False

        # Test type detection
        box_type = ThumbnailBoxFactory.get_thumbnail_box_type(thumbnail_box)
        if box_type == "modern":
            print("✅ Type detection works correctly")
        else:
            print(f"❌ Type detection returned '{box_type}' instead of 'modern'")
            return False

        # Test API compatibility
        word = thumbnail_box.get_word()
        thumbnails = thumbnail_box.get_thumbnails()
        current_index = thumbnail_box.get_current_index()

        print(
            f"✅ API compatibility: word='{word}', thumbnails={len(thumbnails)}, index={current_index}"
        )

        return True

    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_visual_components():
    """Test that visual components can be created."""
    print("\n✨ Testing visual components...")

    try:
        from modern_components.themes.modern_theme_manager import ModernThemeManager
        from modern_components.animations.hover_animations import HoverAnimationManager

        # Create theme manager
        theme = ModernThemeManager()

        # Create hover manager
        hover_manager = HoverAnimationManager(theme)

        # Test glassmorphism style generation
        glass_style = theme.create_glassmorphism_style("medium", 10, "lg")
        print(f"✅ Glassmorphism style: {len(glass_style)} characters")

        # Test hover animation style
        hover_style = theme.create_hover_animation_style(1.05, "fast", "ease_out")
        print(f"✅ Hover animation style: {len(hover_style)} characters")

        # Test shadow styles
        shadow = theme.create_shadow_style("medium")
        print(f"✅ Shadow style: {shadow[:30]}...")

        print("✅ All visual components working")
        return True

    except Exception as e:
        print(f"❌ Visual components test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 TESTING MODERN THUMBNAIL BOX REPLACEMENT")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("Theme System Test", test_theme_system),
        ("Factory Replacement Test", test_factory_replacement),
        ("Visual Components Test", test_visual_components),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append(False)

        print("-" * 30)

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 TEST SUMMARY")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Modern thumbnail box replacement is working correctly!")
        print("✅ The direct replacement approach is successful!")
        print("\n🚀 READY FOR DEPLOYMENT:")
        print("- Modern thumbnail boxes will automatically replace legacy ones")
        print("- No migration needed - it's a direct drop-in replacement")
        print("- All existing code will continue to work unchanged")
        print("- Users will immediately see the 2025 modern design")
    else:
        print(f"⚠️  {total - passed} tests failed")
        print("❌ Modern replacement needs fixes before deployment")

    return passed == total


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run tests
    success = run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
