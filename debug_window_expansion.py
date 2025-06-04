#!/usr/bin/env python3
"""
Debug Window Expansion Issue

This script will help identify exactly what's causing the main window to expand
when switching to the browse tab v2. It will measure window dimensions before
and after tab switches and identify the culprit component.
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def debug_window_expansion():
    """Debug the window expansion issue by measuring dimensions."""
    print("="*80)
    print("WINDOW EXPANSION DEBUG ANALYSIS")
    print("="*80)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # Get the running application
        app = QApplication.instance()
        if not app:
            print("❌ No running QApplication found. Please start the application first.")
            return False
        
        print("✅ Found running QApplication")
        
        # Find main window
        main_window = None
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'main_widget') or 'MainWindow' in str(type(widget)):
                main_window = widget
                break
        
        if not main_window:
            print("❌ Could not find main window")
            return False
        
        print("✅ Found main window")
        
        # Record initial window dimensions
        initial_size = main_window.size()
        initial_width = initial_size.width()
        initial_height = initial_size.height()
        
        print(f"\n📏 INITIAL WINDOW DIMENSIONS:")
        print(f"   Width: {initial_width}px")
        print(f"   Height: {initial_height}px")
        
        # Find the tab system
        main_widget = main_window.main_widget
        if not hasattr(main_widget, 'right_stack'):
            print("❌ Could not find right stack")
            return False
        
        right_stack = main_widget.right_stack
        print(f"\n📋 RIGHT STACK INFO:")
        print(f"   Widget count: {right_stack.count()}")
        print(f"   Current index: {right_stack.currentIndex()}")
        
        # List all tabs
        for i in range(right_stack.count()):
            widget = right_stack.widget(i)
            widget_type = str(type(widget).__name__)
            widget_size = widget.size()
            print(f"   Tab {i}: {widget_type} ({widget_size.width()}x{widget_size.height()})")
        
        # Find browse tab
        browse_tab_index = -1
        for i in range(right_stack.count()):
            widget = right_stack.widget(i)
            if 'BrowseTabV2Adapter' in str(type(widget)):
                browse_tab_index = i
                break
        
        if browse_tab_index == -1:
            print("❌ Could not find browse tab")
            return False
        
        print(f"\n🎯 BROWSE TAB FOUND at index {browse_tab_index}")
        
        # Switch to a different tab first (if not already)
        if right_stack.currentIndex() == browse_tab_index:
            # Switch to a different tab first
            other_index = 0 if browse_tab_index != 0 else 1
            if other_index < right_stack.count():
                print(f"\n🔄 Switching away from browse tab to index {other_index}")
                right_stack.setCurrentIndex(other_index)
                app.processEvents()
                time.sleep(0.5)
                
                # Measure window after switching away
                away_size = main_window.size()
                print(f"📏 WINDOW SIZE AFTER SWITCHING AWAY:")
                print(f"   Width: {away_size.width()}px (change: {away_size.width() - initial_width:+d})")
                print(f"   Height: {away_size.height()}px (change: {away_size.height() - initial_height:+d})")
        
        # Now switch to browse tab and measure
        print(f"\n🔄 Switching TO browse tab (index {browse_tab_index})")
        right_stack.setCurrentIndex(browse_tab_index)
        app.processEvents()
        time.sleep(0.5)
        
        # Measure window after switching to browse tab
        browse_size = main_window.size()
        width_change = browse_size.width() - initial_width
        height_change = browse_size.height() - initial_height
        
        print(f"\n📏 WINDOW SIZE AFTER SWITCHING TO BROWSE TAB:")
        print(f"   Width: {browse_size.width()}px (change: {width_change:+d})")
        print(f"   Height: {browse_size.height()}px (change: {height_change:+d})")
        
        # Analyze the change
        if abs(width_change) > 5 or abs(height_change) > 5:
            print(f"\n⚠️  WINDOW EXPANSION DETECTED!")
            print(f"   Width change: {width_change:+d}px")
            print(f"   Height change: {height_change:+d}px")
            
            # Analyze browse tab components
            analyze_browse_tab_components(right_stack.widget(browse_tab_index))
            
        else:
            print(f"\n✅ NO SIGNIFICANT WINDOW EXPANSION DETECTED")
            print(f"   Changes are within acceptable range (±5px)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_browse_tab_components(browse_tab_adapter):
    """Analyze the browse tab components to find size issues."""
    print(f"\n🔍 ANALYZING BROWSE TAB COMPONENTS:")
    
    try:
        # Analyze adapter
        adapter_size = browse_tab_adapter.size()
        adapter_min = browse_tab_adapter.minimumSize()
        adapter_max = browse_tab_adapter.maximumSize()
        
        print(f"\n📦 BrowseTabV2Adapter:")
        print(f"   Current: {adapter_size.width()}x{adapter_size.height()}")
        print(f"   Minimum: {adapter_min.width()}x{adapter_min.height()}")
        print(f"   Maximum: {adapter_max.width()}x{adapter_max.height()}")
        
        # Find internal browse tab
        if hasattr(browse_tab_adapter, 'browse_tab_v2'):
            browse_tab = browse_tab_adapter.browse_tab_v2
            if hasattr(browse_tab, '_view') and browse_tab._view:
                view = browse_tab._view
                view_size = view.size()
                view_min = view.minimumSize()
                view_max = view.maximumSize()
                
                print(f"\n📦 BrowseTabView:")
                print(f"   Current: {view_size.width()}x{view_size.height()}")
                print(f"   Minimum: {view_min.width()}x{view_min.height()}")
                print(f"   Maximum: {view_max.width()}x{view_max.height()}")
                
                # Find filter panel
                if hasattr(view, 'filter_panel'):
                    panel = view.filter_panel
                    panel_size = panel.size()
                    panel_min = panel.minimumSize()
                    panel_max = panel.maximumSize()
                    
                    print(f"\n📦 SmartFilterPanel:")
                    print(f"   Current: {panel_size.width()}x{panel_size.height()}")
                    print(f"   Minimum: {panel_min.width()}x{panel_min.height()}")
                    print(f"   Maximum: {panel_max.width()}x{panel_max.height()}")
                    
                    # Check if minimum height is the culprit
                    if panel_min.height() > 150:
                        print(f"   ⚠️  POTENTIAL ISSUE: Minimum height ({panel_min.height()}px) may be too large")
                
                # Find content stack
                if hasattr(view, 'content_stack'):
                    stack = view.content_stack
                    stack_size = stack.size()
                    stack_min = stack.minimumSize()
                    stack_max = stack.maximumSize()
                    
                    print(f"\n📦 Content Stack:")
                    print(f"   Current: {stack_size.width()}x{stack_size.height()}")
                    print(f"   Minimum: {stack_min.width()}x{stack_min.height()}")
                    print(f"   Maximum: {stack_max.width()}x{stack_max.height()}")
        
        # Check layout
        layout = browse_tab_adapter.layout()
        if layout:
            margins = layout.contentsMargins()
            spacing = layout.spacing()
            print(f"\n📦 Adapter Layout:")
            print(f"   Margins: {margins.left()}, {margins.top()}, {margins.right()}, {margins.bottom()}")
            print(f"   Spacing: {spacing}")
        
    except Exception as e:
        print(f"❌ Error analyzing components: {e}")

def main():
    """Main debug function."""
    print("Starting window expansion debug analysis...")
    print("Make sure the application is running.")
    
    # Wait for user to be ready
    time.sleep(1)
    
    success = debug_window_expansion()
    
    print("\n" + "="*80)
    if success:
        print("✅ DEBUG ANALYSIS COMPLETED")
        print("Review the output above to identify the expansion cause.")
    else:
        print("❌ DEBUG ANALYSIS FAILED")
        print("Make sure the application is running.")
    print("="*80)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
