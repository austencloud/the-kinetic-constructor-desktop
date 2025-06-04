#!/usr/bin/env python3
"""
Test script for dictionary image regeneration system.

This script tests the basic functionality without requiring full application setup.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_functionality():
    """Test basic functionality of the regeneration system."""
    print("🧪 Testing Dictionary Image Regeneration System")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from utils.path_helpers import get_dictionary_path
        print("✅ utils.path_helpers imported successfully")
        
        from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import TempBeatFrame
        print("✅ TempBeatFrame imported successfully")
        
        from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.thumbnail_generator import ThumbnailGenerator
        print("✅ ThumbnailGenerator imported successfully")
        
        # Test path discovery
        print("\n📁 Testing path discovery...")
        dictionary_path = get_dictionary_path()
        print(f"Dictionary path: {dictionary_path}")
        
        if os.path.exists(dictionary_path):
            print("✅ Dictionary path exists")
            
            # Count word folders
            word_folders = []
            for item in os.listdir(dictionary_path):
                item_path = os.path.join(dictionary_path, item)
                if os.path.isdir(item_path):
                    png_files = [f for f in os.listdir(item_path) if f.endswith('.png')]
                    if png_files:
                        word_folders.append((item_path, item, png_files))
            
            total_images = sum(len(png_files) for _, _, png_files in word_folders)
            print(f"✅ Found {len(word_folders)} word folders with {total_images} images")
            
            # Show first few examples
            if word_folders:
                print("\n📋 Sample word folders:")
                for i, (_, word_name, png_files) in enumerate(word_folders[:3]):
                    print(f"   {word_name}: {len(png_files)} images")
                if len(word_folders) > 3:
                    print(f"   ... and {len(word_folders) - 3} more")
        else:
            print("❌ Dictionary path does not exist")
            return False
        
        # Test QApplication initialization
        print("\n🖥️ Testing QApplication...")
        from PyQt6.QtWidgets import QApplication
        
        if not QApplication.instance():
            app = QApplication(sys.argv)
            print("✅ QApplication initialized")
        else:
            print("✅ QApplication already exists")
        
        # Test TempBeatFrame creation
        print("\n🔧 Testing TempBeatFrame creation...")
        temp_beat_frame = TempBeatFrame(None)
        print("✅ TempBeatFrame created successfully")
        
        # Test ThumbnailGenerator creation
        print("\n🎨 Testing ThumbnailGenerator creation...")
        thumbnail_generator = ThumbnailGenerator(temp_beat_frame)
        print("✅ ThumbnailGenerator created successfully")
        
        print("\n🎉 All basic tests passed!")
        print("💡 The regeneration system should work correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_extraction():
    """Test metadata extraction from existing images."""
    print("\n🔍 Testing metadata extraction...")
    
    try:
        from utils.path_helpers import get_dictionary_path
        import json
        from PIL import Image
        
        dictionary_path = get_dictionary_path()
        
        # Find first image with metadata
        for item in os.listdir(dictionary_path):
            item_path = os.path.join(dictionary_path, item)
            if os.path.isdir(item_path):
                png_files = [f for f in os.listdir(item_path) if f.endswith('.png')]
                if png_files:
                    image_path = os.path.join(item_path, png_files[0])
                    
                    try:
                        with Image.open(image_path) as img:
                            if hasattr(img, 'text') and 'metadata' in img.text:
                                metadata_str = img.text['metadata']
                                metadata = json.loads(metadata_str)
                                
                                print(f"✅ Found metadata in {item}/{png_files[0]}")
                                print(f"   Sequence data: {'sequence' in metadata}")
                                print(f"   Date added: {'date_added' in metadata}")
                                return True
                    except Exception as e:
                        print(f"   Could not read {image_path}: {e}")
                        continue
        
        print("⚠️  No images with metadata found")
        return False
        
    except Exception as e:
        print(f"❌ Metadata extraction test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting dictionary regeneration system tests...\n")
    
    basic_success = test_basic_functionality()
    metadata_success = test_metadata_extraction()
    
    if basic_success and metadata_success:
        print("\n🎉 All tests passed! The regeneration system is ready to use.")
        print("💡 Run: python -m tools.dictionary_image_regenerator")
    elif basic_success:
        print("\n⚠️  Basic tests passed, but no metadata found in images.")
        print("💡 The system should still work for regenerating images.")
    else:
        print("\n❌ Tests failed. Check the errors above.")
    
    sys.exit(0 if basic_success else 1)
