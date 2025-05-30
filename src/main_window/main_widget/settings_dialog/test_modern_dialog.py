"""
Test script for the modern settings dialog components.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from PyQt6.QtWidgets import QApplication

def test_glassmorphism_styler():
    """Test the glassmorphism styler."""
    try:
        from ....styles.glassmorphism_styler import GlassmorphismStyler
        
        # Test color retrieval
        primary_color = GlassmorphismStyler.get_color('primary')
        print(f"✅ Primary color: {primary_color}")
        
        # Test font creation
        heading_font = GlassmorphismStyler.get_font('heading_large')
        print(f"✅ Heading font: {heading_font.pointSize()}pt")
        
        # Test style creation
        button_style = GlassmorphismStyler.create_modern_button('primary')
        print(f"✅ Button style created: {len(button_style)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Glassmorphism styler test failed: {e}")
        return False

def test_modern_components():
    """Test modern components."""
    try:
        from .core.modern_components import SettingCard, ModernButton, ModernToggle
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test SettingCard
        card = SettingCard("Test Card", "This is a test description")
        print(f"✅ SettingCard created: {card.title}")
        
        # Test ModernButton
        button = ModernButton("Test Button", "primary")
        print(f"✅ ModernButton created: {button.text()}")
        
        # Test ModernToggle
        toggle = ModernToggle("Test Toggle")
        print(f"✅ ModernToggle created: {toggle.text()}")
        
        return True
    except Exception as e:
        print(f"❌ Modern components test failed: {e}")
        return False

def test_action_buttons():
    """Test modern action buttons."""
    try:
        from .core.modern_action_buttons import ModernActionButtons
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        action_buttons = ModernActionButtons()
        print(f"✅ ModernActionButtons created")
        
        # Test state changes
        action_buttons.set_has_changes(True)
        print(f"✅ Set has changes: True")
        
        action_buttons.set_apply_success(True)
        print(f"✅ Set apply success: True")
        
        return True
    except Exception as e:
        print(f"❌ Action buttons test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Modern Settings Dialog Components")
    print("=" * 50)
    
    tests = [
        ("Glassmorphism Styler", test_glassmorphism_styler),
        ("Modern Components", test_modern_components),
        ("Action Buttons", test_action_buttons),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Modern settings dialog components are working.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
