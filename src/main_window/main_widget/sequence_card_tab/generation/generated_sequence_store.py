# src/main_window/main_widget/sequence_card_tab/generation/generated_sequence_store.py
import os
import tempfile
import json
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from .generation_manager import GeneratedSequenceData


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sequences = {}  # Dict[str, GeneratedSequenceData]
        self.temp_dir = None
        self.temp_image_files = {}  # Dict[str, str] - sequence_id -> temp_file_path
        self.max_sequences = 50  # Limit to prevent memory issues

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
        """Create a temporary image file for the sequence."""
        try:
            if not self.temp_dir:
                return

            # For now, create a placeholder file
            # In a full implementation, this would generate the actual sequence image
            temp_file_path = os.path.join(self.temp_dir, f"{sequence_data.id}.png")

            # Create a placeholder file (in real implementation, generate actual image)
            with open(temp_file_path, "w") as f:
                f.write(f"Placeholder for sequence {sequence_data.id}")

            # Store the path
            self.temp_image_files[sequence_data.id] = temp_file_path
            sequence_data.image_path = temp_file_path

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
                # Fallback to placeholder
                return self._create_placeholder_image(sequence_data, temp_file_path)

        except Exception as e:
            print(f"Error ensuring temp image for sequence {sequence_data.id}: {e}")
            return ""

    def _generate_sequence_image_file(
        self, sequence_data: GeneratedSequenceData, output_path: str
    ) -> bool:
        """Generate an actual image file for the sequence."""
        try:
            # This would use the same image generation logic as the approval dialog
            # For now, create a placeholder that indicates it's a generated sequence
            from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
            from PyQt6.QtCore import QRect

            # Create a placeholder image
            pixmap = QPixmap(400, 300)
            pixmap.fill(QColor(45, 55, 72))  # Dark background

            painter = QPainter(pixmap)
            painter.setPen(QColor(225, 229, 233))  # Light text

            # Set font
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)

            # Draw text
            text = (
                f"Generated Sequence\n\n"
                f"Word: {sequence_data.word}\n"
                f"Length: {sequence_data.params.length} beats\n"
                f"Level: {sequence_data.params.level}\n"
                f"Mode: {sequence_data.params.generation_mode.title()}\n"
                f"Continuity: {sequence_data.params.prop_continuity.title()}"
            )

            rect = QRect(20, 20, 360, 260)
            painter.drawText(rect, 0, text)
            painter.end()

            # Save the image
            success = pixmap.save(output_path, "PNG")
            return success

        except Exception as e:
            print(f"Error generating sequence image file: {e}")
            return False

    def _create_placeholder_image(
        self, sequence_data: GeneratedSequenceData, output_path: str
    ) -> str:
        """Create a simple placeholder image."""
        try:
            # Create a simple text file as placeholder
            with open(output_path.replace(".png", ".txt"), "w") as f:
                f.write(f"Generated sequence placeholder: {sequence_data.word}")
            return output_path.replace(".png", ".txt")
        except Exception as e:
            print(f"Error creating placeholder: {e}")
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
