import os
import json
from typing import TYPE_CHECKING
from PyQt6.QtGui import QImage
from PIL import Image, PngImagePlugin, ImageEnhance
import numpy as np
from datetime import datetime


if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.sequence_beat_frame import (
        SequenceBeatFrame,
    )


class ThumbnailGenerator:
    def __init__(self, beat_frame: "SequenceBeatFrame"):
        self.beat_frame = beat_frame
        self.image_creator = beat_frame.image_export_manager.image_creator

    def generate_and_save_thumbnail(
        self,
        sequence,
        structural_variation_number,
        directory,
        dictionary=False,
        fullscreen_preview=False,
    ):
        """Generate and save thumbnail for a sequence variation with professional overlay information."""
        try:
            # REDESIGN: Use sequence card rendering options for dictionary images
            # This ensures dictionary images have word, difficulty, author, and date overlays
            if dictionary:
                # Use professional sequence card rendering options
                options = {
                    "add_beat_numbers": True,
                    "add_reversal_symbols": True,
                    "add_user_info": True,  # Enable author and date info
                    "add_word": True,  # Enable word overlay
                    "add_difficulty_level": True,  # Enable difficulty indicator
                    "include_start_position": True,
                    "combined_grids": False,
                    "additional_height_top": 0,
                    "additional_height_bottom": 0,
                }
                # Override dictionary parameter to False to enable overlays
                beat_frame_image = self.image_creator.create_sequence_image(
                    sequence,
                    options=options,
                    dictionary=False,  # Changed: Enable overlays for professional cards
                    fullscreen_preview=fullscreen_preview,
                )
            else:
                # Use standard options for non-dictionary images
                beat_frame_image = self.image_creator.create_sequence_image(
                    sequence,
                    options=self.image_creator.export_manager.settings_manager.image_export.get_all_image_export_options(),
                    dictionary=dictionary,
                    fullscreen_preview=fullscreen_preview,
                )
        except Exception as e:
            print(f"Warning: Failed to create sequence image: {e}")
            beat_frame_image = None

        pil_image = self.qimage_to_pil(beat_frame_image)

        # CRITICAL FIX: Don't aggressively downscale - preserve quality
        # Only resize if the image is extremely large (>2000px)
        if pil_image.width > 2000 or pil_image.height > 2000:
            # Scale down large images more conservatively
            scale_factor = min(2000 / pil_image.width, 2000 / pil_image.height)
            pil_image = self._resize_image(pil_image, scale_factor)
        # For normal-sized images, keep original size for maximum quality

        pil_image = self._sharpen_image(pil_image)

        metadata = {"sequence": sequence, "date_added": datetime.now().isoformat()}
        metadata_str = json.dumps(metadata)
        info = self._create_png_info(metadata_str)

        image_filename = self._create_image_filename(structural_variation_number)
        image_path = os.path.join(directory, image_filename)
        self._save_image(pil_image, image_path, info)
        return image_path

    def _resize_image(self, image: Image.Image, scale_factor: float) -> Image.Image:
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        return image.resize(new_size, Image.LANCZOS)

    def _sharpen_image(self, image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(
            1.5
        )  # 1.0 is original sharpness; >1.0 increases sharpness

    def qimage_to_pil(self, qimage: QImage) -> Image.Image:
        """Convert QImage to PIL Image with proper error handling."""
        # Check if QImage is valid
        if qimage is None or qimage.isNull():
            print("Warning: QImage is None or null, creating empty image")
            # Return a small empty image as fallback
            return Image.new("RGBA", (100, 100), (255, 255, 255, 0))

        # Convert to proper format
        qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
        width, height = qimage.width(), qimage.height()

        # Check for valid dimensions
        if width <= 0 or height <= 0:
            print(
                f"Warning: Invalid QImage dimensions {width}x{height}, creating empty image"
            )
            return Image.new("RGBA", (100, 100), (255, 255, 255, 0))

        # Get image data pointer
        ptr = qimage.bits()
        if ptr is None:
            print("Warning: QImage bits() returned None, creating empty image")
            return Image.new("RGBA", (100, 100), (255, 255, 255, 0))

        try:
            ptr.setsize(height * width * 4)
            arr = np.array(ptr, copy=False).reshape((height, width, 4))
            arr = arr[..., [2, 1, 0, 3]]  # Adjust for RGB
            return Image.fromarray(arr, "RGBA")
        except Exception as e:
            print(
                f"Warning: Failed to convert QImage to PIL: {e}, creating empty image"
            )
            return Image.new("RGBA", (100, 100), (255, 255, 255, 0))

    def _create_png_info(self, metadata: str) -> PngImagePlugin.PngInfo:
        info = PngImagePlugin.PngInfo()
        info.add_text("metadata", metadata.encode("utf-8"))
        return info

    def _create_image_filename(self, structural_variation_number):
        # Handle both real BeatFrameGetter and mock interface
        if hasattr(self.beat_frame, "get"):
            # Check if get is a method (TempBeatFrame) or attribute (SequenceBeatFrame)
            if callable(self.beat_frame.get):
                # TempBeatFrame case: get() returns MockGetInterface
                base_word = self.beat_frame.get().current_word()
            else:
                # SequenceBeatFrame case: get is BeatFrameGetter instance
                base_word = self.beat_frame.get.current_word()
        else:
            # Fallback
            base_word = "UNKNOWN"
        return f"{base_word}_ver{structural_variation_number}.png"

    def _save_image(
        self, pil_image: Image.Image, image_path: str, info: PngImagePlugin.PngInfo
    ):
        """Save the PIL image to the specified path with maximum quality, creating directories if needed."""
        try:
            # Ensure the directory exists before saving
            directory = os.path.dirname(image_path)
            if directory:  # Only create directory if path has a directory component
                os.makedirs(directory, exist_ok=True)

            # CRITICAL FIX: Save with maximum quality PNG settings
            # compress_level=1 = fastest compression with good quality
            # optimize=True = optimize the PNG for smaller file size without quality loss
            pil_image.save(
                image_path, "PNG", pnginfo=info, compress_level=1, optimize=True
            )

        except PermissionError as e:
            print(f"Permission error saving thumbnail to {image_path}: {e}")
            raise
        except OSError as e:
            print(f"OS error saving thumbnail to {image_path}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error saving thumbnail to {image_path}: {e}")
            raise
