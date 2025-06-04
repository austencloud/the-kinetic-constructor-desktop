#!/usr/bin/env python3
"""
Test script for beat creation and pictograph updating.

This script tests the core beat creation process to see if beats are properly populated.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_beat_creation():
    """Test creating a beat and updating it with pictograph data."""
    print("🧪 Testing Beat Creation and Pictograph Update")
    print("=" * 50)
    
    try:
        # Initialize QApplication
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication(sys.argv)
            print("✅ QApplication initialized")
        
        # Import required modules
        from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import TempBeatFrame
        from main_window.main_widget.sequence_workbench.sequence_beat_frame.beat import Beat
        from base_widgets.pictograph.elements.views.beat_view import BeatView
        
        print("✅ Modules imported successfully")
        
        # Create minimal mock main widget
        class MockMainWidget:
            def __init__(self):
                self.settings_manager = self._create_mock_settings_manager()
                self.json_manager = self._create_mock_json_manager()
                
            def _create_mock_settings_manager(self):
                class MockSettingsManager:
                    def __init__(self):
                        self.image_export = MockImageExportSettings()
                        self.visibility = MockVisibilitySettings()
                        
                class MockImageExportSettings:
                    def get_all_image_export_options(self):
                        return {
                            "add_beat_numbers": True,
                            "add_reversal_symbols": True,
                            "add_user_info": True,
                            "add_word": True,
                            "add_difficulty_level": True,
                            "include_start_position": True,
                            "combined_grids": False,
                            "additional_height_top": 0,
                            "additional_height_bottom": 0,
                        }
                        
                class MockVisibilitySettings:
                    def get_motion_visibility(self, color):
                        return True
                        
                return MockSettingsManager()
                
            def _create_mock_json_manager(self):
                class MockJsonManager:
                    pass
                return MockJsonManager()

        # Create TempBeatFrame with mock main widget context
        class MockParentWithMainWidget:
            def __init__(self, main_widget):
                self.main_widget = main_widget

        mock_main_widget = MockMainWidget()
        mock_parent = MockParentWithMainWidget(mock_main_widget)
        temp_beat_frame = TempBeatFrame(mock_parent)
        print("✅ TempBeatFrame created")
        
        # Create test beat data (simple motion data)
        test_beat_data = {
            "beat": 1,
            "letter": "A",
            "start_pos": "alpha",
            "end_pos": "beta",
            "blue_motion_type": "pro",
            "blue_prop_rot_dir": "cw",
            "blue_turns": 1,
            "red_motion_type": "anti",
            "red_prop_rot_dir": "ccw", 
            "red_turns": 1,
            "blue_start_loc": "n",
            "blue_end_loc": "s",
            "red_start_loc": "e",
            "red_end_loc": "w"
        }
        
        print("🔍 Creating beat and beat view...")
        
        # Create beat view and beat
        beat_view = BeatView(temp_beat_frame)
        beat = Beat(temp_beat_frame)
        
        print("✅ Beat and BeatView created")
        
        # Set pictograph data
        beat.state.pictograph_data = test_beat_data
        print("✅ Pictograph data set")
        
        # Update pictograph
        print("🔍 Calling update_pictograph...")
        try:
            beat.managers.updater.update_pictograph(test_beat_data)
            print("✅ update_pictograph completed successfully")
        except Exception as e:
            print(f"❌ Error in update_pictograph: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Check if visual elements are properly initialized
        print("🔍 Checking visual elements...")
        
        success = True
        
        # Check grid
        if hasattr(beat.elements, 'grid') and beat.elements.grid:
            print(f"✅ Grid exists and is visible: {beat.elements.grid.isVisible()}")
        else:
            print(f"❌ Grid is missing or None")
            success = False
            
        # Check props
        if hasattr(beat.elements, 'props') and beat.elements.props:
            for color, prop in beat.elements.props.items():
                if prop:
                    print(f"✅ {color} prop exists and is visible: {prop.isVisible()}")
                else:
                    print(f"❌ {color} prop is None")
                    success = False
        else:
            print(f"❌ Props are missing or None")
            success = False
            
        # Check arrows
        if hasattr(beat.elements, 'arrows') and beat.elements.arrows:
            for color, arrow in beat.elements.arrows.items():
                if arrow:
                    print(f"✅ {color} arrow exists and is visible: {arrow.isVisible()}")
                else:
                    print(f"❌ {color} arrow is None")
                    success = False
        else:
            print(f"❌ Arrows are missing or None")
            success = False
        
        # Set beat in beat view
        beat_view.set_beat(beat, 1)
        print("✅ Beat set in BeatView")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting beat creation test...\n")
    
    success = test_beat_creation()
    
    if success:
        print("\n🎉 Beat creation test passed!")
        print("💡 Beats are being created and populated correctly.")
    else:
        print("\n❌ Beat creation test failed.")
        print("💡 There are issues with beat creation or pictograph updating.")
    
    sys.exit(0 if success else 1)
