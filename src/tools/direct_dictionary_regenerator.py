#!/usr/bin/env python3
"""
Direct Dictionary Image Regeneration Script

This script regenerates dictionary images using the exact same pipeline
that successfully creates sequence card images. It bypasses potential
issues with beat frame initialization by using the proven working approach.

Usage:
    From the main application, call:
    regenerate_dictionary_images_direct()
"""

import os
import json
import logging
from typing import Dict, Optional
from PIL import Image
from PyQt6.QtGui import QPixmap

logger = logging.getLogger(__name__)


def regenerate_dictionary_images_direct(main_widget, max_images: int = None, test_mode: bool = False) -> bool:
    """
    Regenerate dictionary images using the direct sequence card generation pipeline.
    
    This uses the exact same approach that successfully creates sequence card images,
    ensuring we get real kinetic sequence diagrams instead of blank placeholders.
    
    Args:
        main_widget: The main widget instance with access to sequence workbench
        max_images: Maximum number of images to process (for testing)
        test_mode: If True, only process a small subset for testing
        
    Returns:
        True if regeneration was successful, False otherwise
    """
    from utils.path_helpers import get_dictionary_path
    
    print("🎨 Direct Dictionary Image Regeneration")
    print("=" * 50)
    
    dictionary_path = get_dictionary_path()
    print(f"📁 Dictionary path: {dictionary_path}")
    
    if test_mode:
        max_images = max_images or 5
        print(f"🧪 Test mode: Processing maximum {max_images} images")
    
    # Get the sequence card tab's image exporter (this is known to work!)
    if not hasattr(main_widget, 'sequence_card_tab') or not main_widget.sequence_card_tab:
        print("❌ No sequence card tab available")
        return False
    
    sequence_card_tab = main_widget.sequence_card_tab
    if not hasattr(sequence_card_tab, 'image_exporter') or not sequence_card_tab.image_exporter:
        print("❌ No image exporter available in sequence card tab")
        return False
    
    image_exporter = sequence_card_tab.image_exporter
    print("✅ Using sequence card tab's image exporter (proven working pipeline)")
    
    # Discover all word folders and images
    word_folders = _discover_word_folders(dictionary_path)
    if not word_folders:
        print("ℹ️  No word folders found to process")
        return True
    
    # Limit for test mode
    if test_mode or max_images:
        word_folders = _limit_word_folders(word_folders, max_images or 5)
    
    total_words = len(word_folders)
    total_images = sum(len(png_files) for _, _, png_files in word_folders)
    
    print(f"📊 Found {total_words} word folders")
    print(f"📊 Total images to regenerate: {total_images}")
    
    if total_images == 0:
        print("ℹ️  No images found to regenerate")
        return True
    
    # Process each word folder
    successful_regenerations = 0
    failed_regenerations = 0
    skipped_images = 0
    current_image = 0
    
    for word_folder_path, word_name, png_files in word_folders:
        print(f"\n🔄 Processing word: {word_name} ({len(png_files)} images)")
        
        for png_file in png_files:
            current_image += 1
            image_path = os.path.join(word_folder_path, png_file)
            progress = f"[{current_image}/{total_images}]"
            
            print(f"   {progress} {png_file}...")
            
            # Extract metadata from existing image
            metadata = _extract_image_metadata(image_path)
            if not metadata:
                print(f"   ⚠️  No metadata found, skipping")
                skipped_images += 1
                continue
            
            sequence_data = metadata.get("sequence")
            if not sequence_data:
                print(f"   ⚠️  No sequence data found, skipping")
                skipped_images += 1
                continue
            
            # Extract variation number from filename
            variation_number = _extract_variation_number(png_file)
            
            try:
                # Use the direct sequence card generation approach
                success = _regenerate_image_direct(
                    image_exporter, sequence_data, word_name, image_path
                )
                
                if success:
                    print(f"   ✅ Regenerated with real sequence diagrams")
                    successful_regenerations += 1
                else:
                    print(f"   ❌ Regeneration failed")
                    failed_regenerations += 1
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed_regenerations += 1
                logger.error(f"Failed to regenerate {image_path}: {e}")
    
    # Show final statistics
    success_rate = (successful_regenerations / total_images) * 100 if total_images > 0 else 0
    
    print("\n" + "=" * 50)
    print("🎉 Direct Dictionary Image Regeneration Complete!")
    print(f"📊 Total images: {total_images}")
    print(f"✅ Successful regenerations: {successful_regenerations}")
    print(f"⚠️  Skipped: {skipped_images}")
    print(f"❌ Failed: {failed_regenerations}")
    print(f"🎯 Success rate: {success_rate:.1f}%")
    
    if test_mode:
        print(f"\n🧪 Test mode completed!")
        print(f"💡 Ready to run full regeneration on all images")
    else:
        print(f"\n🎨 Dictionary images regenerated with real kinetic sequence diagrams!")
    
    return success_rate > 80


def _regenerate_image_direct(image_exporter, sequence_data: list, word_name: str, original_image_path: str) -> bool:
    """
    Regenerate a single image using the direct sequence card generation pipeline.
    
    This uses the exact same approach that creates working sequence card images.
    """
    try:
        # Use the same options that work for sequence card generation
        options = {
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
        
        # Use the proven working image creation pipeline from sequence card tab
        qimage = image_exporter.export_manager.image_creator.create_sequence_image(
            sequence_data,
            options,
            dictionary=False,  # Enable overlays for professional cards
            fullscreen_preview=False,
            override_word=word_name,  # Pass the word for overlay
        )
        
        if qimage and not qimage.isNull():
            # Convert to pixmap and save
            pixmap = QPixmap.fromImage(qimage)
            if not pixmap.isNull():
                # Save the new image, overwriting the old one
                success = pixmap.save(original_image_path, "PNG")
                if success:
                    # Add metadata back to the image
                    _add_metadata_to_image(original_image_path, sequence_data)
                    return True
                else:
                    print(f"      Failed to save image to {original_image_path}")
                    return False
            else:
                print(f"      Failed to convert QImage to QPixmap")
                return False
        else:
            print(f"      Failed to create QImage")
            return False
            
    except Exception as e:
        print(f"      Direct regeneration error: {e}")
        logger.error(f"Direct regeneration error for {original_image_path}: {e}")
        return False


def _add_metadata_to_image(image_path: str, sequence_data: list) -> None:
    """Add metadata back to the regenerated image."""
    try:
        from datetime import datetime
        from PIL.PngImagePlugin import PngInfo
        
        # Load the image
        with Image.open(image_path) as img:
            # Create metadata
            metadata = {
                "sequence": sequence_data,
                "date_added": datetime.now().isoformat()
            }
            metadata_str = json.dumps(metadata)
            
            # Create PNG info with metadata
            pnginfo = PngInfo()
            pnginfo.add_text("metadata", metadata_str)
            
            # Save with metadata
            img.save(image_path, "PNG", pnginfo=pnginfo)
            
    except Exception as e:
        logger.warning(f"Failed to add metadata to {image_path}: {e}")


def _discover_word_folders(dictionary_path: str):
    """Discover all word folders containing PNG files."""
    word_folders = []
    
    try:
        for item in os.listdir(dictionary_path):
            item_path = os.path.join(dictionary_path, item)
            if os.path.isdir(item_path):
                # Check if folder contains PNG files
                png_files = [f for f in os.listdir(item_path) if f.endswith('.png')]
                if png_files:
                    word_folders.append((item_path, item, png_files))
    except Exception as e:
        print(f"❌ Error discovering word folders: {e}")
        logger.error(f"Error discovering word folders: {e}")
    
    return word_folders


def _limit_word_folders(word_folders, max_images: int):
    """Limit word folders for test mode."""
    limited_folders = []
    total_images = 0
    
    for folder_path, word_name, png_files in word_folders:
        if total_images >= max_images:
            break
        
        # Take only as many images as needed to reach max_images
        remaining_slots = max_images - total_images
        limited_png_files = png_files[:remaining_slots]
        
        if limited_png_files:
            limited_folders.append((folder_path, word_name, limited_png_files))
            total_images += len(limited_png_files)
    
    return limited_folders


def _extract_image_metadata(image_path: str) -> Optional[Dict]:
    """Extract metadata from existing dictionary image."""
    try:
        with Image.open(image_path) as img:
            if hasattr(img, 'text') and 'metadata' in img.text:
                metadata_str = img.text['metadata']
                return json.loads(metadata_str)
                
    except Exception as e:
        logger.debug(f"Could not extract metadata from {image_path}: {e}")
    
    return None


def _extract_variation_number(filename: str) -> int:
    """Extract variation number from filename (e.g., 'word_ver2.png' -> 2)."""
    try:
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Look for '_ver' pattern
        if '_ver' in name_without_ext:
            version_part = name_without_ext.split('_ver')[-1]
            return int(version_part)
            
    except Exception as e:
        logger.debug(f"Could not extract variation number from {filename}: {e}")
    
    return 1  # Default to version 1


# Example usage functions that can be called from the main application
def test_direct_regeneration(main_widget):
    """Test the direct regeneration system with a few images."""
    return regenerate_dictionary_images_direct(main_widget, max_images=5, test_mode=True)


def full_direct_regeneration(main_widget):
    """Run full direct regeneration on all dictionary images."""
    return regenerate_dictionary_images_direct(main_widget, test_mode=False)


# For testing from command line (if run within application context)
if __name__ == "__main__":
    print("This script must be run from within the application context.")
    print("Use: test_direct_regeneration(main_widget) or full_direct_regeneration(main_widget)")
