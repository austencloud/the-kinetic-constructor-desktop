#!/usr/bin/env python3
"""
Final Dictionary Image Regeneration Script

This script provides a working solution to regenerate dictionary images
using the proper ImageCreator approach. It's designed to work independently
of the complex browse_tab structure changes.

Usage:
    Run this script directly from the application or as a standalone tool.
"""

import os
import json
from typing import Dict, Optional
from PIL import Image


def regenerate_dictionary_images_final(main_widget=None):
    """
    Final working approach to regenerate dictionary images.

    This uses the real ImageCreator system to create proper kinetic sequence diagrams.

    Args:
        main_widget: The main widget instance (required for accessing ImageCreator)
    """
    print("🎨 FINAL DICTIONARY IMAGE REGENERATION")
    print("=" * 60)

    try:
        # Get dictionary path
        import sys
        import os

        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.path_helpers import get_dictionary_path

        dictionary_path = get_dictionary_path()
        print(f"📁 Dictionary path: {dictionary_path}")

        if not os.path.exists(dictionary_path):
            print(f"❌ Dictionary path does not exist: {dictionary_path}")
            return False

        # Discover all images
        word_folders = _discover_word_folders(dictionary_path)
        if not word_folders:
            print("ℹ️  No word folders found")
            return False

        total_images = sum(len(png_files) for _, _, png_files in word_folders)
        print(f"📊 Found {total_images} images to regenerate")

        # Process images with simplified approach
        successful = 0
        failed = 0
        skipped = 0

        for word_folder_path, word_name, png_files in word_folders:
            print(f"\n🔄 Processing word: {word_name}")

            for png_file in png_files:
                image_path = os.path.join(word_folder_path, png_file)
                print(f"   Processing: {png_file}")

                # Extract metadata
                metadata = _extract_metadata(image_path)
                if not metadata:
                    print(f"   ⚠️  No metadata, skipping")
                    skipped += 1
                    continue

                sequence_data = metadata.get("sequence")
                if not sequence_data:
                    print(f"   ⚠️  No sequence data, skipping")
                    skipped += 1
                    continue

                # Generate new image using REAL ImageCreator system
                try:
                    success = _regenerate_image_with_real_image_creator(
                        sequence_data, word_name, image_path, main_widget
                    )
                    if success:
                        print(f"   ✅ Regenerated successfully")
                        successful += 1
                    else:
                        print(f"   ❌ Regeneration failed")
                        failed += 1
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    failed += 1

        # Show results
        total_processed = successful + failed + skipped
        success_rate = (
            (successful / total_processed) * 100 if total_processed > 0 else 0
        )

        print(f"\n📊 FINAL REGENERATION RESULTS:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped: {skipped}")
        print(f"🎯 Success rate: {success_rate:.1f}%")

        if successful > 0:
            print(f"\n🎉 Successfully regenerated {successful} images!")
            print(
                "💡 Check the regenerated images to verify they contain real sequence diagrams"
            )
            return True
        else:
            print(f"\n❌ No images were successfully regenerated")
            return False

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return False


def _discover_word_folders(dictionary_path: str):
    """Discover word folders containing PNG files."""
    word_folders = []

    for item in os.listdir(dictionary_path):
        item_path = os.path.join(dictionary_path, item)
        if os.path.isdir(item_path):
            png_files = [f for f in os.listdir(item_path) if f.endswith(".png")]
            if png_files:
                word_folders.append((item_path, item, png_files))

    return word_folders


def _extract_metadata(image_path: str) -> Optional[Dict]:
    """Extract metadata from image."""
    try:
        with Image.open(image_path) as img:
            if hasattr(img, "text") and "metadata" in img.text:
                return json.loads(img.text["metadata"])
    except Exception:
        pass
    return None


def _regenerate_image_with_real_image_creator(
    sequence_data: list, word_name: str, output_path: str, main_widget=None
) -> bool:
    """
    Regenerate a single image using the ACTUAL ImageCreator system.

    This uses the real ThumbnailGenerator and ImageCreator pipeline that
    creates proper kinetic sequence diagrams with beat drawings and notation.

    Args:
        sequence_data: The sequence data to render
        word_name: The word name (for logging)
        output_path: Where to save the generated image
        main_widget: The main widget instance (required for accessing ImageCreator)
    """
    try:
        # Import the real components
        from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.thumbnail_generator import (
            ThumbnailGenerator,
        )

        if not main_widget:
            print(
                f"      No main_widget provided - regeneration must be run from within the application"
            )
            return False

        # Get the sequence workbench
        sequence_workbench = getattr(main_widget, "sequence_workbench", None)
        if not sequence_workbench:
            print(
                f"      No sequence_workbench available - regeneration must be run from within the application"
            )
            return False

        # Get the beat frame
        beat_frame = getattr(sequence_workbench, "beat_frame", None)
        if not beat_frame:
            print(
                f"      No sequence_beat_frame available - regeneration must be run from within the application"
            )
            return False

        # Create the real ThumbnailGenerator
        thumbnail_generator = ThumbnailGenerator(beat_frame)

        # Extract variation number from filename
        filename = os.path.basename(output_path)
        variation_number = 1
        if "_" in filename:
            try:
                variation_number = int(filename.split("_")[1].split(".")[0])
            except:
                variation_number = 1

        # Get the directory
        directory = os.path.dirname(output_path)

        # Use the REAL thumbnail generator to create the image
        # This will use the actual ImageCreator.create_sequence_image() method
        new_image_path = thumbnail_generator.generate_and_save_thumbnail(
            sequence_data,
            variation_number,
            directory,
            dictionary=True,  # Enable dictionary-specific rendering with professional overlays
            fullscreen_preview=False,
        )

        if new_image_path and os.path.exists(new_image_path):
            # If the new path is different from the output path, move it
            if new_image_path != output_path:
                import shutil

                shutil.move(new_image_path, output_path)

            print(f"      ✅ Generated real sequence image using ImageCreator")
            return True
        else:
            print(f"      ❌ ThumbnailGenerator failed to create image")
            return False

    except Exception as e:
        print(f"      ❌ Error using real ImageCreator: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎨 Starting Final Dictionary Regeneration...")
    success = regenerate_dictionary_images_final()

    if success:
        print("\n🎉 FINAL REGENERATION COMPLETED!")
        print(
            "✅ Dictionary images have been regenerated with professional sequence cards"
        )
        print("💡 Check the dictionary folder to see the new images")
        print("💡 These images should now display properly in the browse tab")
    else:
        print("\n❌ FINAL REGENERATION FAILED!")
        print("💡 Check the error messages above for details")

    exit(0 if success else 1)
