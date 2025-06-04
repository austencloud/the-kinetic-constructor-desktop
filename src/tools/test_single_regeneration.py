#!/usr/bin/env python3
"""
Test script for single dictionary image regeneration.

This script tests regenerating just one image to verify the system works.
"""

import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_single_regeneration():
    """Test regenerating a single dictionary image."""
    print("🧪 Testing Single Dictionary Image Regeneration")
    print("=" * 50)
    
    try:
        # Initialize QApplication
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication(sys.argv)
            print("✅ QApplication initialized")
        
        # Import required modules
        from utils.path_helpers import get_dictionary_path
        from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import TempBeatFrame
        from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.thumbnail_generator import ThumbnailGenerator
        
        # Get dictionary path and find first image
        dictionary_path = get_dictionary_path()
        print(f"📁 Dictionary path: {dictionary_path}")
        
        # Find first image with metadata
        test_image_path = None
        test_word = None
        test_metadata = None
        
        for item in os.listdir(dictionary_path):
            item_path = os.path.join(dictionary_path, item)
            if os.path.isdir(item_path):
                png_files = [f for f in os.listdir(item_path) if f.endswith('.png')]
                if png_files:
                    image_path = os.path.join(item_path, png_files[0])
                    
                    # Try to extract metadata
                    try:
                        from PIL import Image
                        with Image.open(image_path) as img:
                            if hasattr(img, 'text') and 'metadata' in img.text:
                                metadata_str = img.text['metadata']
                                metadata = json.loads(metadata_str)
                                
                                if 'sequence' in metadata:
                                    test_image_path = image_path
                                    test_word = item
                                    test_metadata = metadata
                                    break
                    except Exception as e:
                        print(f"   Could not read {image_path}: {e}")
                        continue
        
        if not test_image_path:
            print("❌ No suitable test image found")
            return False
        
        print(f"📋 Test image: {test_word}/{os.path.basename(test_image_path)}")
        
        # Create TempBeatFrame and ThumbnailGenerator
        temp_beat_frame = TempBeatFrame(None)
        thumbnail_generator = ThumbnailGenerator(temp_beat_frame)
        print("✅ ThumbnailGenerator created")
        
        # Set current word
        try:
            set_interface = temp_beat_frame.set()
            set_interface.current_word(test_word)
            print(f"✅ Set current word to: {test_word}")
        except Exception as e:
            print(f"⚠️  Could not set current word: {e}")
        
        # Extract variation number
        filename = os.path.basename(test_image_path)
        variation_number = 1
        try:
            name_without_ext = os.path.splitext(filename)[0]
            if '_ver' in name_without_ext:
                version_part = name_without_ext.split('_ver')[-1]
                variation_number = int(version_part)
        except Exception:
            pass
        
        print(f"📊 Variation number: {variation_number}")
        
        # Test regeneration
        print("🎨 Testing image regeneration...")
        try:
            sequence_data = test_metadata['sequence']
            directory = os.path.dirname(test_image_path)
            
            new_image_path = thumbnail_generator.generate_and_save_thumbnail(
                sequence_data,
                variation_number,
                directory,
                dictionary=True,  # Enable dictionary-specific rendering with overlays
                fullscreen_preview=False,
            )
            
            if new_image_path:
                print(f"✅ Image regenerated successfully: {new_image_path}")
                return True
            else:
                print("❌ Image regeneration returned None")
                return False
                
        except Exception as e:
            print(f"❌ Image regeneration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting single image regeneration test...\n")
    
    success = test_single_regeneration()
    
    if success:
        print("\n🎉 Single image regeneration test passed!")
        print("💡 The regeneration system should work for all images.")
    else:
        print("\n❌ Single image regeneration test failed.")
        print("💡 Check the errors above for details.")
    
    sys.exit(0 if success else 1)
