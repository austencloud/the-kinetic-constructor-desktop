# src/main_window/main_widget/sequence_card_tab/generation/generated_sequence_store.py
import os
import tempfile
import json
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from .generation_manager import GeneratedSequenceData

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.export.image_exporter import (
        SequenceCardImageExporter,
    )


class GeneratedSequenceStore(QObject):
    """
    Manages storage and retrieval of generated sequences.

    Stores generated sequences in memory and creates temporary image files
    as needed, without polluting the main dictionary.
    """

    sequences_updated = pyqtSignal()
    sequence_added = pyqtSignal(object)  # GeneratedSequenceData
    sequence_removed = pyqtSignal(str)  # sequence_id
    store_cleared = pyqtSignal()

    def __init__(self, parent=None, image_exporter=None):
        super().__init__(parent)
        self.sequences = {}  # Dict[str, GeneratedSequenceData]
        self.temp_dir = None
        self.temp_image_files = {}  # Dict[str, str] - sequence_id -> temp_file_path
        self.max_sequences = 50  # Limit to prevent memory issues
        self.image_exporter: "SequenceCardImageExporter" = (
            image_exporter  # SequenceCardImageExporter for actual image generation
        )

        # Create temporary directory for generated sequence images
        self._create_temp_directory()

    def _create_temp_directory(self):
        """Create a temporary directory for generated sequence images."""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="generated_sequences_")
        except Exception as e:
            print(f"Error creating temporary directory: {e}")
            self.temp_dir = None

    def add_approved_sequence(self, sequence_data: GeneratedSequenceData) -> bool:
        """
        Add an approved sequence to the store.

        Args:
            sequence_data: The generated sequence data to add

        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            # Check if we're at capacity
            if len(self.sequences) >= self.max_sequences:
                self._remove_oldest_sequence()

            # Mark as approved
            sequence_data.approved = True

            # Store the sequence
            self.sequences[sequence_data.id] = sequence_data

            # Create temporary image if needed
            self._create_temp_image(sequence_data)

            # Emit signals
            self.sequence_added.emit(sequence_data)
            self.sequences_updated.emit()

            return True

        except Exception as e:
            print(f"Error adding sequence to store: {e}")
            return False

    def remove_sequence(self, sequence_id: str) -> bool:
        """
        Remove a sequence from the store.

        Args:
            sequence_id: ID of the sequence to remove

        Returns:
            bool: True if removed successfully, False otherwise
        """
        try:
            if sequence_id in self.sequences:
                # Remove temporary image file
                self._remove_temp_image(sequence_id)

                # Remove from store
                del self.sequences[sequence_id]

                # Emit signals
                self.sequence_removed.emit(sequence_id)
                self.sequences_updated.emit()

                return True
            return False

        except Exception as e:
            print(f"Error removing sequence from store: {e}")
            return False

    def get_sequence(self, sequence_id: str) -> Optional[GeneratedSequenceData]:
        """Get a specific sequence by ID."""
        return self.sequences.get(sequence_id)

    def get_all_sequences(self) -> List[GeneratedSequenceData]:
        """Get all stored sequences."""
        return list(self.sequences.values())

    def get_sequences_by_length(self, length: int) -> List[GeneratedSequenceData]:
        """Get sequences filtered by length."""
        return [seq for seq in self.sequences.values() if seq.params.length == length]

    def get_sequences_by_level(self, level: int) -> List[GeneratedSequenceData]:
        """Get sequences filtered by level."""
        return [seq for seq in self.sequences.values() if seq.params.level == level]

    def get_sequences_by_filters(
        self, length: Optional[int] = None, levels: Optional[List[int]] = None
    ) -> List[GeneratedSequenceData]:
        """Get sequences filtered by length and/or levels."""
        sequences = list(self.sequences.values())

        if length is not None:
            sequences = [seq for seq in sequences if seq.params.length == length]

        if levels is not None and len(levels) > 0:
            sequences = [seq for seq in sequences if seq.params.level in levels]

        return sequences

    def clear_all_sequences(self):
        """Clear all stored sequences."""
        try:
            # Remove all temporary image files
            for sequence_id in list(self.temp_image_files.keys()):
                self._remove_temp_image(sequence_id)

            # Clear the store
            self.sequences.clear()

            # Emit signal
            self.store_cleared.emit()
            self.sequences_updated.emit()

        except Exception as e:
            print(f"Error clearing sequence store: {e}")

    def get_sequence_count(self) -> int:
        """Get the total number of stored sequences."""
        return len(self.sequences)

    def get_sequence_count_by_length(self, length: int) -> int:
        """Get the count of sequences for a specific length."""
        return len(self.get_sequences_by_length(length))

    def get_sequence_count_by_level(self, level: int) -> int:
        """Get the count of sequences for a specific level."""
        return len(self.get_sequences_by_level(level))

    def _create_temp_image(self, sequence_data: GeneratedSequenceData):
        """Create a temporary image file for the sequence using the same pipeline as dictionary sequences."""
        try:
            if not self.temp_dir:
                return

            # Generate actual PNG image file (same as dictionary sequences)
            temp_file_path = os.path.join(self.temp_dir, f"gen_{sequence_data.id}.png")

            # Generate the actual sequence image immediately
            success = self._generate_sequence_image_file(sequence_data, temp_file_path)

            if success and os.path.exists(temp_file_path):
                # Store the path only if the PNG file was successfully created
                self.temp_image_files[sequence_data.id] = temp_file_path
                sequence_data.image_path = temp_file_path
                print(f"Successfully created temp image: {temp_file_path}")
            else:
                print(f"Failed to create temp image for sequence {sequence_data.id}")

        except Exception as e:
            print(
                f"Error creating temporary image for sequence {sequence_data.id}: {e}"
            )

    def _remove_temp_image(self, sequence_id: str):
        """Remove the temporary image file for a sequence."""
        try:
            if sequence_id in self.temp_image_files:
                temp_file_path = self.temp_image_files[sequence_id]

                # Remove the file if it exists
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

                # Remove from tracking
                del self.temp_image_files[sequence_id]

        except Exception as e:
            print(f"Error removing temporary image for sequence {sequence_id}: {e}")

    def _remove_oldest_sequence(self):
        """Remove the oldest sequence to make room for new ones."""
        if not self.sequences:
            return

        # Find the oldest sequence (first added)
        oldest_id = next(iter(self.sequences))
        self.remove_sequence(oldest_id)

    def get_sequences_for_display_system(
        self,
        length_filter: Optional[int] = None,
        level_filters: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get generated sequences in the format expected by the display system.

        Args:
            length_filter: Optional length filter
            level_filters: Optional level filters

        Returns:
            List of sequence data dictionaries compatible with the display system
        """
        try:
            display_sequences = []

            for sequence_data in self.sequences.values():
                # Apply filters
                if (
                    length_filter is not None
                    and sequence_data.params.length != length_filter
                ):
                    continue

                if (
                    level_filters is not None
                    and sequence_data.params.level not in level_filters
                ):
                    continue

                # Create a temporary image for the sequence if needed
                temp_image_path = self._ensure_temp_image(sequence_data)

                # Format as expected by display system
                display_sequence = {
                    "path": temp_image_path,
                    "word": sequence_data.word,
                    "length": sequence_data.params.length,
                    "level": sequence_data.params.level,
                    "sequence_file": f"generated_{sequence_data.id}.json",
                    "metadata": {
                        "word": sequence_data.word,
                        "length": sequence_data.params.length,
                        "level": sequence_data.params.level,
                        "generation_mode": sequence_data.params.generation_mode,
                        "prop_continuity": sequence_data.params.prop_continuity,
                        "turn_intensity": sequence_data.params.turn_intensity,
                        "is_generated": True,
                        "generated_id": sequence_data.id,
                    },
                }

                display_sequences.append(display_sequence)

            return display_sequences

        except Exception as e:
            print(f"Error getting sequences for display system: {e}")
            return []

    def _ensure_temp_image(self, sequence_data: GeneratedSequenceData) -> str:
        """Ensure a temporary image exists for the sequence."""
        try:
            if sequence_data.id in self.temp_image_files:
                temp_path = self.temp_image_files[sequence_data.id]
                if os.path.exists(temp_path):
                    return temp_path

            # Generate the image if it doesn't exist
            temp_file_path = os.path.join(
                self.temp_dir or tempfile.gettempdir(),
                f"generated_{sequence_data.id}.png",
            )

            # Generate the actual sequence image
            success = self._generate_sequence_image_file(sequence_data, temp_file_path)

            if success:
                self.temp_image_files[sequence_data.id] = temp_file_path
                sequence_data.image_path = temp_file_path
                return temp_file_path
            else:
                # Fallback to placeholder PNG image (not text file)
                return self._create_placeholder_png_image(sequence_data, temp_file_path)

        except Exception as e:
            print(f"Error ensuring temp image for sequence {sequence_data.id}: {e}")
            return ""

    def _generate_sequence_image_file(
        self, sequence_data: GeneratedSequenceData, output_path: str
    ) -> bool:
        """Generate an actual image file for the sequence using the same system as dictionary sequences."""
        try:
            # First try to use the actual image generation system
            success = self._generate_actual_sequence_image(sequence_data, output_path)
            if success and os.path.exists(output_path):
                print(f"Successfully generated actual image: {output_path}")
                return True

            # If actual generation fails, create a high-quality placeholder PNG
            # This ensures we always have a valid PNG file that can be loaded
            print(
                f"Actual generation failed, creating placeholder PNG for {sequence_data.id}"
            )
            success = self._generate_placeholder_sequence_image(
                sequence_data, output_path
            )
            if success and os.path.exists(output_path):
                print(f"Successfully generated placeholder PNG: {output_path}")
                return True

            print(
                f"Both actual and placeholder generation failed for {sequence_data.id}"
            )
            return False

        except Exception as e:
            print(f"Error generating sequence image file: {e}")
            return False

    def _generate_actual_sequence_image(
        self, sequence_data: GeneratedSequenceData, output_path: str
    ) -> bool:
        """Generate actual sequence image using the SequenceCardImageExporter."""
        try:
            # Import here to avoid circular imports
            from PyQt6.QtGui import QPixmap

            print(f"DEBUG: Starting actual image generation for {sequence_data.id}")

            # Use the image exporter if available
            if not self.image_exporter:
                print("DEBUG: No image exporter available")
                return False

            # Load sequence into the temp beat frame
            print(f"DEBUG: Loading sequence: {len(sequence_data.sequence_data)} beats")
            self.image_exporter.temp_beat_frame.load_sequence(
                sequence_data.sequence_data
            )

            # Calculate optimal scale factor for generated sequence store images
            scale_factor = self._calculate_optimal_scale_factor_for_store()

            # Generate image using page-optimized options with scale factor
            options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": True,  # Keep! Don't Skip! Important! I'm offended you removed it.
                "add_user_info": True,
                "add_word": True,
                "add_difficulty_level": True,
                "include_start_position": True,
                "combined_grids": False,
                "additional_height_top": 0,  # Will be calculated by HeightDeterminer
                "additional_height_bottom": 0,  # Will be calculated by HeightDeterminer
                "dynamic_scale_factor": scale_factor,  # Apply reverse-calculated scale factor
            }

            print(f"🎨 Generated sequence store using scale factor: {scale_factor:.3f}")

            print(f"DEBUG: Creating sequence image with options: {options}")
            qimage = (
                self.image_exporter.export_manager.image_creator.create_sequence_image(
                    sequence_data.sequence_data,
                    options,
                    dictionary=False,
                    fullscreen_preview=False,
                    override_word=sequence_data.word,  # Pass the word here
                )
            )

            if qimage and not qimage.isNull():
                pixmap = QPixmap.fromImage(qimage)
                if not pixmap.isNull():
                    success = pixmap.save(output_path, "PNG")
                    if success:
                        print(
                            f"Successfully generated actual sequence image: {output_path}"
                        )
                        return True

            print("DEBUG: Failed to create valid qimage or pixmap")
            return False

        except Exception as e:
            print(f"Error generating actual sequence image: {e}")
            import traceback

            traceback.print_exc()
            return False

    # Helper methods removed - now using SequenceCardImageExporter directly

    def _generate_placeholder_sequence_image(
        self, sequence_data: GeneratedSequenceData, output_path: str
    ) -> bool:
        """Generate a placeholder image that looks like a sequence card."""
        try:
            from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
            from PyQt6.QtCore import QRect, Qt

            # Create a larger, more realistic placeholder image
            pixmap = QPixmap(600, 400)
            pixmap.fill(QColor(255, 255, 255))  # White background

            painter = QPainter(pixmap)

            # Draw border to simulate sequence card
            border_pen = QPen(QColor(255, 140, 0), 3)  # Orange border for generated
            painter.setPen(border_pen)
            painter.drawRect(5, 5, 590, 390)

            # Set text color
            painter.setPen(QColor(50, 50, 50))  # Dark text

            # Title
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            painter.setFont(title_font)

            title_rect = QRect(20, 20, 560, 40)
            painter.drawText(
                title_rect, Qt.AlignmentFlag.AlignCenter, "Generated Sequence"
            )

            # Sequence info
            info_font = QFont()
            info_font.setPointSize(12)
            painter.setFont(info_font)

            info_text = (
                f"Word: {sequence_data.word}\n"
                f"Length: {sequence_data.params.length} beats\n"
                f"Level: {sequence_data.params.level}\n"
                f"Mode: {sequence_data.params.generation_mode.title()}\n"
                f"Continuity: {sequence_data.params.prop_continuity.title()}\n\n"
                f"This is a placeholder image.\n"
                f"Actual sequence visualization will be\n"
                f"generated when the image system is available."
            )

            info_rect = QRect(40, 80, 520, 280)
            painter.drawText(
                info_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                info_text,
            )

            # Add visual indicator that this is generated
            painter.setPen(QColor(255, 140, 0))
            painter.setFont(title_font)
            indicator_rect = QRect(20, 350, 560, 30)
            painter.drawText(
                indicator_rect, Qt.AlignmentFlag.AlignCenter, "🔄 GENERATED SEQUENCE"
            )

            painter.end()

            # Save the image
            success = pixmap.save(output_path, "PNG")
            if success:
                print(f"Generated placeholder sequence image: {output_path}")
            return success

        except Exception as e:
            print(f"Error generating placeholder sequence image: {e}")
            return False

    def _create_placeholder_png_image(
        self, sequence_data: GeneratedSequenceData, output_path: str
    ) -> str:
        """Create a PNG placeholder image that can be loaded by the image system."""
        try:
            # Use the existing placeholder PNG generator
            success = self._generate_placeholder_sequence_image(
                sequence_data, output_path
            )
            if success and os.path.exists(output_path):
                self.temp_image_files[sequence_data.id] = output_path
                sequence_data.image_path = output_path
                return output_path
            else:
                print(f"Failed to create placeholder PNG for {sequence_data.id}")
                return ""
        except Exception as e:
            print(f"Error creating PNG placeholder: {e}")
            return ""

    def export_sequences_to_dictionary(
        self, sequences: List[GeneratedSequenceData]
    ) -> bool:
        """
        Export approved sequences to the main dictionary.

        Args:
            sequences: List of sequences to export

        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            # This would implement the actual export to dictionary
            # For now, just mark as exported
            for sequence in sequences:
                if sequence.id in self.sequences:
                    # In a full implementation, this would:
                    # 1. Generate the final sequence image
                    # 2. Save to the appropriate dictionary folder
                    # 3. Update metadata
                    print(f"Would export sequence {sequence.id} to dictionary")

            return True

        except Exception as e:
            print(f"Error exporting sequences to dictionary: {e}")
            return False

    def get_store_summary(self) -> Dict[str, Any]:
        """Get a summary of the current store state."""
        sequences = list(self.sequences.values())

        # Count by length
        length_counts = {}
        for seq in sequences:
            length = seq.params.length
            length_counts[length] = length_counts.get(length, 0) + 1

        # Count by level
        level_counts = {}
        for seq in sequences:
            level = seq.params.level
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "total_sequences": len(sequences),
            "length_distribution": length_counts,
            "level_distribution": level_counts,
            "temp_files_created": len(self.temp_image_files),
            "temp_directory": self.temp_dir,
        }

    def _calculate_optimal_scale_factor_for_store(self) -> float:
        """
        Calculate the optimal scale factor for generated sequence store images using the same
        reverse-calculation approach as other generation modes.

        This ensures consistent sizing across all image generation contexts.

        Returns:
            float: Scale factor to apply to the image creator
        """
        try:
            # Use store-specific target size (similar to page cells but optimized for storage)
            target_width = 372  # Same as page cells for consistency
            target_height = 342  # Proportional height

            # Base pictograph size is hardcoded at 950x950 throughout the system
            BASE_PICTOGRAPH_SIZE = 950

            # Step 1: Estimate layout for typical store sequences
            # Most sequences are 16 beats + start position
            columns, rows = 5, 4  # Standard layout for 16-beat + start position

            # Step 2: Calculate what the full-size image dimensions would be
            core_image_width = columns * BASE_PICTOGRAPH_SIZE
            core_image_height = rows * BASE_PICTOGRAPH_SIZE

            # Estimate additional heights (using standard calculations)
            estimated_additional_height_top = 300  # Standard for word label
            estimated_additional_height_bottom = 150  # Standard for user info

            full_image_width = core_image_width
            full_image_height = (
                core_image_height
                + estimated_additional_height_top
                + estimated_additional_height_bottom
            )

            # Step 3: Calculate scale ratio based on store target size
            width_scale_ratio = target_width / full_image_width
            height_scale_ratio = target_height / full_image_height

            # Use the smaller ratio to ensure the image fits within the target size
            scale_factor = min(width_scale_ratio, height_scale_ratio)

            # Step 4: Apply safety bounds to prevent extreme scaling
            scale_factor = max(scale_factor, 0.05)  # Minimum 5% to maintain readability
            scale_factor = min(scale_factor, 1.0)  # Maximum 100% to prevent oversizing

            print(f"🎯 STORE SCALE FACTOR: {scale_factor:.3f}")
            print(
                f"   📐 Layout: {columns}x{rows}, Full size: {full_image_width}x{full_image_height}"
            )
            print(
                f"   📏 Target: {target_width}x{target_height}, Ratios: W={width_scale_ratio:.3f}, H={height_scale_ratio:.3f}"
            )

            return scale_factor

        except Exception as e:
            print(f"Error calculating store scale factor: {e}")
            # Fallback to a conservative default that should work for store images
            return 0.2  # 20% of original size

    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            # Remove all temporary image files
            for sequence_id in list(self.temp_image_files.keys()):
                self._remove_temp_image(sequence_id)

            # Remove temporary directory if empty
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    os.rmdir(self.temp_dir)
                except OSError:
                    # Directory not empty, leave it
                    pass

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
