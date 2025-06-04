#!/usr/bin/env python3
"""
Test script to verify the navigation sidebar layout and styling fixes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

def test_sidebar_widget_hierarchy():
    """Test the widget hierarchy and layout structure."""
    print("🔍 Testing sidebar widget hierarchy...")
    
    try:
        from browse_tab_v2.components.modern_navigation_sidebar import ModernNavigationSidebar
        from browse_tab_v2.core.interfaces import BrowseTabConfig
        from browse_tab_v2.core.state import SequenceModel
        
        # Create test application
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Set dark theme for testing
        app.setStyle('Fusion')
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        app.setPalette(palette)
        
        # Create sidebar
        config = BrowseTabConfig()
        sidebar = ModernNavigationSidebar(config)
        
        # Create test sequences with Type 3 letters
        test_sequences = [
            SequenceModel(
                id="1", name="W-ABC", thumbnails=[], difficulty=1, length=3,
                author="Test", tags=[]
            ),
            SequenceModel(
                id="2", name="ABCD", thumbnails=[], difficulty=2, length=4,
                author="Test", tags=[]
            ),
            SequenceModel(
                id="3", name="BCDE", thumbnails=[], difficulty=1, length=5,
                author="Test", tags=[]
            ),
        ]
        
        # Update sidebar with sequences
        sidebar.update_for_sequences(test_sequences, "alphabetical")
        
        # Test widget hierarchy
        print(f"📊 Sidebar widget hierarchy:")
        print(f"  - Main sidebar widget: {type(sidebar).__name__}")
        print(f"  - Header frame: {type(sidebar.header_frame).__name__}")
        print(f"  - Content area: {type(sidebar.content_area).__name__}")
        print(f"  - Content widget: {type(sidebar.content_widget).__name__}")
        print(f"  - Content layout: {type(sidebar.content_layout).__name__}")
        
        # Test button creation and parenting
        print(f"\n🔘 Button analysis:")
        print(f"  - Number of buttons created: {len(sidebar.buttons)}")
        print(f"  - Button sections: {list(sidebar.buttons.keys())}")
        
        # Check button parenting
        for section_name, button in sidebar.buttons.items():
            parent_widget = button.parent()
            parent_name = type(parent_widget).__name__ if parent_widget else "None"
            print(f"  - Button '{section_name}' parent: {parent_name}")
            
            # Check if button is in the correct layout
            button_in_layout = False
            for i in range(sidebar.content_layout.count()):
                item = sidebar.content_layout.itemAt(i)
                if item and item.widget() == button:
                    button_in_layout = True
                    break
            
            print(f"    - In content layout: {button_in_layout}")
            
            # Check button styling
            stylesheet = button.styleSheet()
            has_glassmorphism = "rgba(255, 255, 255, 0.08)" in stylesheet
            print(f"    - Has glassmorphism styling: {has_glassmorphism}")
        
        # Test layout structure
        print(f"\n📐 Layout structure:")
        print(f"  - Content layout item count: {sidebar.content_layout.count()}")
        
        for i in range(sidebar.content_layout.count()):
            item = sidebar.content_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_type = type(widget).__name__
                    print(f"    - Item {i}: {widget_type}")
                else:
                    print(f"    - Item {i}: Spacer/Layout item")
        
        # Verify buttons are not in header
        header_layout = sidebar.header_frame.layout()
        header_button_count = 0
        if header_layout:
            for i in range(header_layout.count()):
                item = header_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, 'clicked'):  # It's a button
                        header_button_count += 1
        
        print(f"  - Buttons incorrectly in header: {header_button_count}")
        
        # Test visual display
        print(f"\n🎨 Visual testing:")
        
        # Create test window
        window = QMainWindow()
        window.setWindowTitle("Navigation Sidebar Test")
        window.setGeometry(100, 100, 300, 600)
        
        # Set dark background
        window.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 30, 30, 1), stop:1 rgba(20, 20, 20, 1));
            }
        """)
        
        # Add sidebar to window
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Navigation Sidebar Test")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add sidebar
        layout.addWidget(sidebar)
        
        window.setCentralWidget(central_widget)
        window.show()
        
        print(f"✅ Test window created and displayed")
        print(f"📝 Visual inspection points:")
        print(f"  1. Buttons should appear in the content area below 'Sections' header")
        print(f"  2. Buttons should have glassmorphism styling (semi-transparent white)")
        print(f"  3. Buttons should NOT be stacked in the header area")
        print(f"  4. Expected sections: A, B, W-")
        
        # Summary
        success = True
        issues = []
        
        if len(sidebar.buttons) == 0:
            success = False
            issues.append("No buttons were created")
        
        if header_button_count > 0:
            success = False
            issues.append(f"{header_button_count} buttons incorrectly placed in header")
        
        # Check if any button has wrong parent
        wrong_parent_count = 0
        for button in sidebar.buttons.values():
            if button.parent() != sidebar.content_widget:
                wrong_parent_count += 1
        
        if wrong_parent_count > 0:
            success = False
            issues.append(f"{wrong_parent_count} buttons have wrong parent widget")
        
        if success:
            print(f"\n🎉 All layout tests passed!")
        else:
            print(f"\n❌ Layout issues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        return window, success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def main():
    """Run the sidebar layout test."""
    print("🚀 Starting navigation sidebar layout and styling test...\n")
    
    window, success = test_sidebar_widget_hierarchy()
    
    if window:
        print(f"\n💡 Test window is displayed. Check visually:")
        print(f"  - Are buttons visible in the content area?")
        print(f"  - Do buttons have proper glassmorphism styling?")
        print(f"  - Are buttons NOT collapsed in the header?")
        print(f"\nPress Ctrl+C to exit...")
        
        try:
            # Keep window open for visual inspection
            app = QApplication.instance()
            if app:
                app.exec()
        except KeyboardInterrupt:
            print(f"\n👋 Test completed.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
