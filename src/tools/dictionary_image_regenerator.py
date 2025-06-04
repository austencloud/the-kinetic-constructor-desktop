#!/usr/bin/env python3
"""
Dictionary Image Regeneration System

This system processes all existing dictionary images and regenerates them with
enhanced professional overlays including word names, difficulty levels, author
information, and creation dates.

Usage:
    python -m tools.dictionary_image_regenerator

Features:
- Scans entire dictionary directory for PNG files
- Extracts existing metadata from images
- Regenerates with professional overlay options
- Preserves original filenames and directory structure
- Provides comprehensive progress reporting and statistics
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.path_helpers import get_dictionary_path
from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.thumbnail_generator import (
    ThumbnailGenerator,
)

logger = logging.getLogger(__name__)


@dataclass
class RegenerationStats:
    """Statistics for the regeneration process."""

    total_words: int = 0
    total_images: int = 0
    successful_regenerations: int = 0
    failed_regenerations: int = 0
    skipped_images: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_images == 0:
            return 0.0
        return (self.successful_regenerations / self.total_images) * 100


class DictionaryImageRegenerator:
    """
    Comprehensive dictionary image regeneration system.

    This class handles the complete process of scanning, extracting metadata,
    and regenerating all dictionary images with professional overlays.
    """

    def __init__(self):
        """Initialize the regeneration system."""
        self.dictionary_path = get_dictionary_path()
        self.stats = RegenerationStats()
        self.thumbnail_generator = None
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for the regeneration process."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def regenerate_all_images(self) -> bool:
        """
        Regenerate all dictionary images with professional overlays.

        Returns:
            True if regeneration was successful (>80% success rate), False otherwise
        """
        print("🎨 Dictionary Image Regeneration System")
        print("=" * 70)
        print(f"📁 Dictionary path: {self.dictionary_path}")

        if not self._validate_dictionary_path():
            return False

        # Initialize thumbnail generator
        if not self._initialize_thumbnail_generator():
            return False

        # Discover all word folders and images
        word_folders = self._discover_word_folders()
        if not word_folders:
            print("ℹ️  No word folders found to process")
            return True

        self.stats.total_words = len(word_folders)
        self.stats.total_images = sum(
            len(png_files) for _, _, png_files in word_folders
        )

        print(f"📊 Found {self.stats.total_words} word folders")
        print(f"📊 Total images to regenerate: {self.stats.total_images}")

        if self.stats.total_images == 0:
            print("ℹ️  No images found to regenerate")
            return True

        # Process each word folder
        self._process_word_folders(word_folders)

        # Show final statistics
        self._show_final_statistics()

        return self.stats.success_rate > 80

    def _validate_dictionary_path(self) -> bool:
        """Validate that the dictionary path exists."""
        if not os.path.exists(self.dictionary_path):
            print(f"❌ Dictionary path does not exist: {self.dictionary_path}")
            return False
        return True

    def _initialize_thumbnail_generator(self) -> bool:
        """Initialize the thumbnail generator system."""
        try:
            # Initialize QApplication if not already done
            from PyQt6.QtWidgets import QApplication
            import sys

            if not QApplication.instance():
                app = QApplication(sys.argv)
                print("✅ QApplication initialized for image generation")

            # Don't create thumbnail generator here - create fresh one for each image
            print("✅ Thumbnail generator system initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize thumbnail generator system: {e}")
            logger.error(f"Failed to initialize thumbnail generator system: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _create_beat_frame(self):
        """Create a beat frame for image generation."""
        try:
            # Import the actual beat frame
            from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
                SequenceBeatFrame,
            )
            from main_window.main_widget.sequence_workbench.sequence_workbench import (
                SequenceWorkbench,
            )

            # Create a minimal sequence workbench for the beat frame
            # Note: This is a simplified approach for regeneration purposes
            sequence_workbench = SequenceWorkbench()
            beat_frame = SequenceBeatFrame(sequence_workbench)

            return beat_frame

        except Exception as e:
            logger.warning(f"Failed to create actual beat frame: {e}")
            # Fallback to temp beat frame
            from main_window.main_widget.browse_tab.temp_beat_frame.temp_beat_frame import (
                TempBeatFrame,
            )

            return TempBeatFrame(None)

    def _discover_word_folders(self) -> List[Tuple[str, str, List[str]]]:
        """
        Discover all word folders containing PNG files.

        Returns:
            List of tuples: (folder_path, word_name, png_files)
        """
        word_folders = []

        try:
            for item in os.listdir(self.dictionary_path):
                item_path = os.path.join(self.dictionary_path, item)
                if os.path.isdir(item_path):
                    # Check if folder contains PNG files
                    png_files = [f for f in os.listdir(item_path) if f.endswith(".png")]
                    if png_files:
                        word_folders.append((item_path, item, png_files))
        except Exception as e:
            print(f"❌ Error discovering word folders: {e}")
            logger.error(f"Error discovering word folders: {e}")

        return word_folders

    def _process_word_folders(self, word_folders: List[Tuple[str, str, List[str]]]):
        """Process each word folder and regenerate images."""
        current_image = 0

        for word_folder_path, word_name, png_files in word_folders:
            print(f"\n🔄 Processing word: {word_name} ({len(png_files)} images)")

            for png_file in png_files:
                current_image += 1
                self._process_single_image(
                    word_folder_path, word_name, png_file, current_image
                )

    def _process_single_image(
        self, word_folder_path: str, word_name: str, png_file: str, current_image: int
    ):
        """Process a single image file."""
        image_path = os.path.join(word_folder_path, png_file)
        progress = f"[{current_image}/{self.stats.total_images}]"

        print(f"   {progress} {png_file}...")

        # Extract metadata from existing image
        metadata = self._extract_image_metadata(image_path)
        if not metadata:
            print(f"   ⚠️  No metadata found, skipping")
            self.stats.skipped_images += 1
            return

        sequence_data = metadata.get("sequence")
        if not sequence_data:
            print(f"   ⚠️  No sequence data found, skipping")
            self.stats.skipped_images += 1
            return

        # Extract variation number from filename
        variation_number = self._extract_variation_number(png_file)

        try:
            # Create fresh thumbnail generator for each image to avoid Qt object deletion issues
            thumbnail_generator = self._create_fresh_thumbnail_generator(word_name)
            if not thumbnail_generator:
                print(f"   ❌ Failed to create thumbnail generator")
                self.stats.failed_regenerations += 1
                return

            # Generate new image with professional overlays
            success = self._regenerate_image_with_generator(
                thumbnail_generator,
                sequence_data,
                variation_number,
                word_folder_path,
                image_path,
            )

            if success:
                print(f"   ✅ Regenerated successfully")
                self.stats.successful_regenerations += 1
            else:
                print(f"   ❌ Regeneration failed")
                self.stats.failed_regenerations += 1

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.stats.failed_regenerations += 1
            self.stats.errors.append(f"{image_path}: {str(e)}")
            logger.error(f"Failed to regenerate {image_path}: {e}")

    def _extract_image_metadata(self, image_path: str) -> Optional[Dict]:
        """Extract metadata from existing dictionary image."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                if hasattr(img, "text") and "metadata" in img.text:
                    metadata_str = img.text["metadata"]
                    return json.loads(metadata_str)

        except Exception as e:
            logger.debug(f"Could not extract metadata from {image_path}: {e}")

        return None

    def _extract_variation_number(self, filename: str) -> int:
        """Extract variation number from filename (e.g., 'word_ver2.png' -> 2)."""
        try:
            # Remove extension
            name_without_ext = os.path.splitext(filename)[0]

            # Look for '_ver' pattern
            if "_ver" in name_without_ext:
                version_part = name_without_ext.split("_ver")[-1]
                return int(version_part)

        except Exception as e:
            logger.debug(f"Could not extract variation number from {filename}: {e}")

        return 1  # Default to version 1

    def _set_current_word(self, word_name: str):
        """Set the current word in the beat frame for overlay generation."""
        try:
            if hasattr(self.thumbnail_generator.beat_frame, "set_current_word"):
                self.thumbnail_generator.beat_frame.set_current_word(word_name)
        except Exception as e:
            logger.debug(f"Could not set current word: {e}")

    def _regenerate_image(
        self,
        sequence_data: Dict,
        variation_number: int,
        directory: str,
        original_path: str,
    ) -> bool:
        """Regenerate a single image with professional overlays."""
        try:
            # Generate new image with professional overlays enabled
            new_image_path = self.thumbnail_generator.generate_and_save_thumbnail(
                sequence_data,
                variation_number,
                directory,
                dictionary=True,  # Enable dictionary-specific rendering with overlays
                fullscreen_preview=False,
            )

            return new_image_path is not None

        except Exception as e:
            logger.error(f"Failed to regenerate image {original_path}: {e}")
            return False

    def _create_fresh_thumbnail_generator(self, word_name: str):
        """Create a fresh thumbnail generator for each image to avoid Qt object deletion."""
        try:
            # Create a fresh beat frame for this image
            beat_frame = self._create_beat_frame()

            # Set the current word
            set_interface = beat_frame.set()
            if hasattr(set_interface, "current_word"):
                set_interface.current_word(word_name)
                logger.debug(f"Set current word to: {word_name}")

            # Create thumbnail generator with this beat frame
            from main_window.main_widget.sequence_workbench.add_to_dictionary_manager.thumbnail_generator import (
                ThumbnailGenerator,
            )

            thumbnail_generator = ThumbnailGenerator(beat_frame)

            return thumbnail_generator

        except Exception as e:
            logger.error(f"Failed to create fresh thumbnail generator: {e}")
            return None

    def _regenerate_image_with_generator(
        self,
        thumbnail_generator,
        sequence_data: Dict,
        variation_number: int,
        directory: str,
        original_path: str,
    ) -> bool:
        """Regenerate a single image with professional overlays using provided generator."""
        try:
            # Generate new image with professional overlays enabled
            new_image_path = thumbnail_generator.generate_and_save_thumbnail(
                sequence_data,
                variation_number,
                directory,
                dictionary=True,  # Enable dictionary-specific rendering with overlays
                fullscreen_preview=False,
            )

            return new_image_path is not None

        except Exception as e:
            logger.error(f"Failed to regenerate image {original_path}: {e}")
            return False

    def _show_final_statistics(self):
        """Display final regeneration statistics."""
        print("\n" + "=" * 70)
        print("🎉 Dictionary Image Regeneration Complete!")
        print(f"📊 Total words: {self.stats.total_words}")
        print(f"📊 Total images: {self.stats.total_images}")
        print(f"✅ Successful regenerations: {self.stats.successful_regenerations}")
        print(f"⚠️  Skipped: {self.stats.skipped_images}")
        print(f"❌ Failed: {self.stats.failed_regenerations}")

        if self.stats.errors:
            print(f"\n❌ Errors encountered:")
            for error in self.stats.errors[:5]:  # Show first 5 errors
                print(f"   {error}")
            if len(self.stats.errors) > 5:
                print(f"   ... and {len(self.stats.errors) - 5} more errors")

        print(f"\n🎯 Success rate: {self.stats.success_rate:.1f}%")


def main():
    """Main entry point for the dictionary image regeneration system."""
    regenerator = DictionaryImageRegenerator()
    success = regenerator.regenerate_all_images()

    if success:
        print("\n🎉 Regeneration completed successfully!")
        print("💡 Next steps:")
        print("   1. Clear browse tab cache to see new images")
        print("   2. Restart the application")
        print("   3. Check browse tab for professional sequence cards")
    else:
        print("\n❌ Regeneration failed or had significant errors")
        print("💡 Check the error messages above for details")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
