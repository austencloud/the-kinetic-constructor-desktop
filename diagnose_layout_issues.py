#!/usr/bin/env python3
"""
Layout Issues Diagnostic Tool

This script analyzes the browse tab v2 layout issues:
1. Window expansion when switching to browse tab
2. UI element overlay between active filters and search sections

It examines the widget hierarchy, size policies, and actual dimensions
to identify the root causes and provide specific fixes.
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def analyze_widget_hierarchy():
    """Analyze the widget hierarchy to identify layout issues."""
    print("="*80)
    print("BROWSE TAB V2 LAYOUT DIAGNOSTIC ANALYSIS")
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
        print(f"Main window size: {main_window.size().width()} x {main_window.size().height()}")
        
        # Analyze the widget hierarchy
        print("\n" + "="*60)
        print("WIDGET HIERARCHY ANALYSIS")
        print("="*60)
        
        # Find browse tab components
        browse_tab_adapter = find_browse_tab_adapter(main_window)
        if not browse_tab_adapter:
            print("❌ Could not find browse tab adapter")
            return False
        
        print("✅ Found browse tab adapter")
        analyze_browse_tab_structure(browse_tab_adapter)
        
        # Analyze size policies
        print("\n" + "="*60)
        print("SIZE POLICY ANALYSIS")
        print("="*60)
        analyze_size_policies(browse_tab_adapter)
        
        # Analyze layout spacing and margins
        print("\n" + "="*60)
        print("LAYOUT SPACING AND MARGINS ANALYSIS")
        print("="*60)
        analyze_layout_properties(browse_tab_adapter)
        
        # Check for overlay issues
        print("\n" + "="*60)
        print("UI ELEMENT OVERLAY ANALYSIS")
        print("="*60)
        analyze_overlay_issues(browse_tab_adapter)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_browse_tab_adapter(main_window):
    """Find the browse tab adapter in the widget hierarchy."""
    try:
        # Look for BrowseTabV2Adapter
        adapters = main_window.findChildren(type(main_window))
        for adapter in adapters:
            if 'BrowseTabV2Adapter' in str(type(adapter)):
                return adapter
        
        # Alternative search through main widget
        if hasattr(main_window, 'main_widget'):
            main_widget = main_window.main_widget
            if hasattr(main_widget, 'right_stack'):
                right_stack = main_widget.right_stack
                for i in range(right_stack.count()):
                    widget = right_stack.widget(i)
                    if 'BrowseTabV2Adapter' in str(type(widget)):
                        return widget
        
        return None
        
    except Exception as e:
        print(f"Error finding browse tab adapter: {e}")
        return None

def analyze_browse_tab_structure(adapter):
    """Analyze the internal structure of the browse tab."""
    try:
        print(f"Browse Tab Adapter: {type(adapter).__name__}")
        print(f"  Size: {adapter.size().width()} x {adapter.size().height()}")
        print(f"  Minimum Size: {adapter.minimumSize().width()} x {adapter.minimumSize().height()}")
        print(f"  Maximum Size: {adapter.maximumSize().width()} x {adapter.maximumSize().height()}")
        
        # Find internal browse tab v2
        if hasattr(adapter, 'browse_tab_v2'):
            browse_tab = adapter.browse_tab_v2
            print(f"\nBrowse Tab V2: {type(browse_tab).__name__}")
            print(f"  Size: {browse_tab.size().width()} x {browse_tab.size().height()}")
            
            # Find view component
            if hasattr(browse_tab, 'view'):
                view = browse_tab.view
                print(f"\nBrowse Tab View: {type(view).__name__}")
                print(f"  Size: {view.size().width()} x {view.size().height()}")
                
                # Find filter panel
                if hasattr(view, 'filter_panel'):
                    filter_panel = view.filter_panel
                    print(f"\nSmart Filter Panel: {type(filter_panel).__name__}")
                    print(f"  Size: {filter_panel.size().width()} x {filter_panel.size().height()}")
                    print(f"  Minimum Size: {filter_panel.minimumSize().width()} x {filter_panel.minimumSize().height()}")
                    print(f"  Maximum Size: {filter_panel.maximumSize().width()} x {filter_panel.maximumSize().height()}")
                    
                    # Analyze filter panel sections
                    analyze_filter_panel_sections(filter_panel)
                
                # Find content stack
                if hasattr(view, 'content_stack'):
                    content_stack = view.content_stack
                    print(f"\nContent Stack: {type(content_stack).__name__}")
                    print(f"  Size: {content_stack.size().width()} x {content_stack.size().height()}")
        
    except Exception as e:
        print(f"Error analyzing browse tab structure: {e}")

def analyze_filter_panel_sections(filter_panel):
    """Analyze the sections within the filter panel."""
    try:
        print("\n  Filter Panel Sections:")
        
        # Find child widgets
        children = filter_panel.findChildren(type(filter_panel))
        sections = []
        
        for child in children:
            if hasattr(child, 'objectName'):
                obj_name = child.objectName()
                if obj_name in ['searchSection', 'chipsSection', 'controlsSection']:
                    sections.append((obj_name, child))
        
        for name, section in sections:
            print(f"    {name}: {section.size().width()} x {section.size().height()}")
            if hasattr(section, 'minimumSize'):
                print(f"      Min: {section.minimumSize().width()} x {section.minimumSize().height()}")
            if hasattr(section, 'maximumSize'):
                print(f"      Max: {section.maximumSize().width()} x {section.maximumSize().height()}")
        
    except Exception as e:
        print(f"Error analyzing filter panel sections: {e}")

def analyze_size_policies(adapter):
    """Analyze size policies throughout the hierarchy."""
    try:
        from PyQt6.QtWidgets import QSizePolicy
        
        def policy_name(policy):
            policy_map = {
                QSizePolicy.Policy.Fixed: "Fixed",
                QSizePolicy.Policy.Minimum: "Minimum", 
                QSizePolicy.Policy.Maximum: "Maximum",
                QSizePolicy.Policy.Preferred: "Preferred",
                QSizePolicy.Policy.Expanding: "Expanding",
                QSizePolicy.Policy.MinimumExpanding: "MinimumExpanding",
                QSizePolicy.Policy.Ignored: "Ignored"
            }
            return policy_map.get(policy, str(policy))
        
        def analyze_widget_policy(widget, name):
            policy = widget.sizePolicy()
            h_policy = policy_name(policy.horizontalPolicy())
            v_policy = policy_name(policy.verticalPolicy())
            print(f"{name}: H={h_policy}, V={v_policy}")
        
        analyze_widget_policy(adapter, "Browse Tab Adapter")
        
        if hasattr(adapter, 'browse_tab_v2'):
            browse_tab = adapter.browse_tab_v2
            analyze_widget_policy(browse_tab, "Browse Tab V2")
            
            if hasattr(browse_tab, 'view'):
                view = browse_tab.view
                analyze_widget_policy(view, "Browse Tab View")
                
                if hasattr(view, 'filter_panel'):
                    filter_panel = view.filter_panel
                    analyze_widget_policy(filter_panel, "Smart Filter Panel")
                
                if hasattr(view, 'content_stack'):
                    content_stack = view.content_stack
                    analyze_widget_policy(content_stack, "Content Stack")
        
    except Exception as e:
        print(f"Error analyzing size policies: {e}")

def analyze_layout_properties(adapter):
    """Analyze layout margins, spacing, and constraints."""
    try:
        def analyze_layout(widget, name):
            layout = widget.layout()
            if layout:
                margins = layout.contentsMargins()
                spacing = layout.spacing()
                print(f"{name} Layout:")
                print(f"  Margins: {margins.left()}, {margins.top()}, {margins.right()}, {margins.bottom()}")
                print(f"  Spacing: {spacing}")
        
        analyze_layout(adapter, "Browse Tab Adapter")
        
        if hasattr(adapter, 'browse_tab_v2'):
            browse_tab = adapter.browse_tab_v2
            if hasattr(browse_tab, 'view'):
                view = browse_tab.view
                analyze_layout(view, "Browse Tab View")
                
                if hasattr(view, 'filter_panel'):
                    filter_panel = view.filter_panel
                    analyze_layout(filter_panel, "Smart Filter Panel")
        
    except Exception as e:
        print(f"Error analyzing layout properties: {e}")

def analyze_overlay_issues(adapter):
    """Analyze potential UI element overlay issues."""
    try:
        if hasattr(adapter, 'browse_tab_v2'):
            browse_tab = adapter.browse_tab_v2
            if hasattr(browse_tab, 'view'):
                view = browse_tab.view
                if hasattr(view, 'filter_panel'):
                    filter_panel = view.filter_panel
                    
                    # Check if sections are overlapping
                    print("Checking for section overlaps in SmartFilterPanel...")
                    
                    # Get section positions
                    children = filter_panel.findChildren(type(filter_panel))
                    sections = {}
                    
                    for child in children:
                        if hasattr(child, 'objectName'):
                            obj_name = child.objectName()
                            if obj_name in ['searchSection', 'chipsSection', 'controlsSection']:
                                pos = child.pos()
                                size = child.size()
                                sections[obj_name] = {
                                    'pos': (pos.x(), pos.y()),
                                    'size': (size.width(), size.height()),
                                    'bottom': pos.y() + size.height()
                                }
                    
                    # Check for overlaps
                    if 'searchSection' in sections and 'chipsSection' in sections:
                        search_bottom = sections['searchSection']['bottom']
                        chips_top = sections['chipsSection']['pos'][1]
                        
                        if search_bottom > chips_top:
                            print(f"⚠️  OVERLAY DETECTED: Search section bottom ({search_bottom}) overlaps chips section top ({chips_top})")
                        else:
                            print(f"✅ No overlay: Search section bottom ({search_bottom}) < chips section top ({chips_top})")
                    
                    # Print section details
                    for name, info in sections.items():
                        print(f"{name}: pos={info['pos']}, size={info['size']}, bottom={info['bottom']}")
        
    except Exception as e:
        print(f"Error analyzing overlay issues: {e}")

def main():
    """Main diagnostic function."""
    print("Starting layout diagnostic analysis...")
    print("Make sure the application is running and browse tab is visible.")
    
    # Wait for user to switch to browse tab
    time.sleep(2)
    
    success = analyze_widget_hierarchy()
    
    print("\n" + "="*80)
    if success:
        print("✅ DIAGNOSTIC ANALYSIS COMPLETED")
        print("Review the output above to identify layout issues.")
    else:
        print("❌ DIAGNOSTIC ANALYSIS FAILED")
        print("Make sure the application is running with browse tab visible.")
    print("="*80)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
