"""
Batch Processor - Handles memory-efficient batch processing of sequences.

This component extracts batch processing logic from the main exporter
following the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, List, Dict, Tuple, Optional
from datetime import datetime
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from ..image_exporter import SequenceCardImageExporter
    from .image_converter import ImageConverter
    from .cache_manager import CacheManager
    from .memory_manager import MemoryManager
    from .file_operations_manager import FileOperationsManager


class BatchProcessor:
    """
    Handles memory-efficient batch processing of sequences.
    
    Responsibilities:
    - Process sequences in memory-safe batches
    - Coordinate between components for each sequence
    - Track processing progress and statistics
    - Handle cancellation requests
    - Manage UI responsiveness during processing
    """
    
    def __init__(self, exporter: "SequenceCardImageExporter"):
        self.exporter = exporter
        self.logger = logging.getLogger(__name__)
        
        # Processing configuration
        self.batch_size = 15
        self.memory_check_interval = 5
        self.cancel_requested = False
        
        # Component references (set during configuration)
        self.image_converter: Optional["ImageConverter"] = None
        self.cache_manager: Optional["CacheManager"] = None
        self.memory_manager: Optional["MemoryManager"] = None
        self.file_operations: Optional["FileOperationsManager"] = None
        
        # Processing state
        self.current_batch = 0
        self.total_batches = 0
        self.sequences: List[Tuple[str, str]] = []
        self.export_config: Dict = {}
        
        # Statistics
        self.stats = {
            "batches_processed": 0,
            "sequences_processed": 0,
            "sequences_regenerated": 0,
            "sequences_skipped": 0,
            "sequences_failed": 0,
            "processing_start_time": None,
            "processing_end_time": None
        }
        
        self.logger.info("BatchProcessor initialized")
    
    def configure(
        self,
        sequences: List[Tuple[str, str]],
        export_config: Dict,
        image_converter: "ImageConverter",
        cache_manager: "CacheManager",
        memory_manager: "MemoryManager",
        file_operations: "FileOperationsManager"
    ) -> None:
        """Configure the batch processor with components and data."""
        self.sequences = sequences
        self.export_config = export_config
        self.image_converter = image_converter
        self.cache_manager = cache_manager
        self.memory_manager = memory_manager
        self.file_operations = file_operations
        
        self.total_batches = (len(sequences) + self.batch_size - 1) // self.batch_size
        self.cancel_requested = False
        
        self.logger.info(
            f"Batch processor configured: {len(sequences)} sequences, "
            f"{self.total_batches} batches, batch size {self.batch_size}"
        )
    
    def process_all_batches(self) -> Dict:
        """
        Process all batches of sequences.
        
        Returns:
            Dictionary with processing results and statistics
        """
        self.stats["processing_start_time"] = datetime.now()
        self.logger.info("Starting batch processing")
        
        try:
            for batch_index in range(self.total_batches):
                if self.cancel_requested:
                    self.logger.info("Processing cancelled by user request")
                    break
                
                self.current_batch = batch_index
                self._process_single_batch(batch_index)
                
                # Memory cleanup between batches
                self.memory_manager.check_and_cleanup_if_needed(force_cleanup=True)
                
                # Keep UI responsive
                QApplication.processEvents()
            
            self.stats["processing_end_time"] = datetime.now()
            return self._create_processing_result()
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            self.stats["processing_end_time"] = datetime.now()
            return self._create_error_result(str(e))
    
    def _process_single_batch(self, batch_index: int) -> None:
        """Process a single batch of sequences."""
        start_idx = batch_index * self.batch_size
        end_idx = min(start_idx + self.batch_size, len(self.sequences))
        batch_sequences = self.sequences[start_idx:end_idx]
        
        self.logger.info(
            f"Processing batch {batch_index + 1}/{self.total_batches} "
            f"(sequences {start_idx + 1}-{end_idx})"
        )
        
        for sequence_idx, (word, sequence_file) in enumerate(batch_sequences):
            if self.cancel_requested:
                break
            
            try:
                self._process_single_sequence(word, sequence_file, start_idx + sequence_idx)
            except Exception as e:
                self.logger.error(f"Failed to process sequence {sequence_file}: {e}")
                self.stats["sequences_failed"] += 1
        
        self.stats["batches_processed"] += 1
    
    def _process_single_sequence(self, word: str, sequence_file: str, global_index: int) -> None:
        """Process a single sequence."""
        # Build paths
        source_path = self.file_operations.build_source_path(
            self.export_config["dictionary_path"], word, sequence_file
        )
        output_path = self.file_operations.build_output_path(
            self.export_config["export_path"], word, sequence_file
        )
        
        # Ensure output directory exists
        self.file_operations.ensure_output_directory(output_path)
        
        # Check memory usage periodically
        if global_index % self.memory_check_interval == 0:
            self.memory_manager.check_and_cleanup_if_needed()
        
        # Keep UI responsive
        QApplication.processEvents()
        
        # Check if regeneration is needed
        needs_regen, reason = self.cache_manager.needs_regeneration(source_path, output_path)
        
        if needs_regen:
            self._regenerate_sequence_image(source_path, output_path, word, sequence_file)
            self.stats["sequences_regenerated"] += 1
        else:
            self.logger.debug(f"Skipping {sequence_file}: {reason}")
            self.stats["sequences_skipped"] += 1
        
        self.stats["sequences_processed"] += 1
    
    def _regenerate_sequence_image(
        self, source_path: str, output_path: str, word: str, sequence_file: str
    ) -> None:
        """Regenerate a sequence image."""
        try:
            # Extract metadata
            metadata = self.exporter.metadata_extractor.extract_metadata_from_file(source_path)
            if not metadata or "sequence" not in metadata:
                raise ValueError("Invalid or missing sequence metadata")
            
            sequence = metadata["sequence"]
            
            # Define export options
            export_options = self._get_export_options()
            
            # Generate the image
            self.exporter.temp_beat_frame.load_sequence(sequence)
            qimage = self.exporter.export_manager.image_creator.create_sequence_image(
                sequence, export_options, dictionary=False, fullscreen_preview=False
            )
            
            # Convert to PIL image
            pil_image = self.image_converter.convert_qimage_to_pil(qimage)
            
            # Add metadata
            metadata["export_options"] = export_options
            metadata["export_date"] = datetime.now().isoformat()
            png_info = self.exporter._create_png_info(metadata)
            
            # Save with optimized compression
            pil_image.save(
                output_path,
                "PNG",
                compress_level=self.exporter.quality_settings["png_compression"],
                pnginfo=png_info,
            )
            
            self.logger.debug(f"Successfully regenerated: {sequence_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to regenerate {sequence_file}: {e}")
            raise
    
    def _get_export_options(self) -> Dict:
        """Get standard export options."""
        return {
            "add_word": True,
            "add_user_info": True,
            "add_difficulty_level": True,
            "add_date": True,
            "add_note": True,
            "add_beat_numbers": True,
            "add_reversal_symbols": True,
            "combined_grids": False,
            "include_start_position": True,
        }
    
    def cancel_processing(self) -> None:
        """Cancel the current processing operation."""
        self.cancel_requested = True
        self.logger.info("Batch processing cancellation requested")
    
    def get_progress_info(self) -> Dict:
        """Get current progress information."""
        total_sequences = len(self.sequences)
        progress_percent = (self.stats["sequences_processed"] / max(1, total_sequences)) * 100
        
        return {
            "current_batch": self.current_batch + 1,
            "total_batches": self.total_batches,
            "sequences_processed": self.stats["sequences_processed"],
            "total_sequences": total_sequences,
            "progress_percent": round(progress_percent, 1),
            "sequences_regenerated": self.stats["sequences_regenerated"],
            "sequences_skipped": self.stats["sequences_skipped"],
            "sequences_failed": self.stats["sequences_failed"]
        }
    
    def _create_processing_result(self) -> Dict:
        """Create processing result dictionary."""
        duration = None
        if self.stats["processing_start_time"] and self.stats["processing_end_time"]:
            duration = (
                self.stats["processing_end_time"] - self.stats["processing_start_time"]
            ).total_seconds()
        
        return {
            "success": True,
            "processed_sequences": self.stats["sequences_processed"],
            "regenerated_count": self.stats["sequences_regenerated"],
            "skipped_count": self.stats["sequences_skipped"],
            "failed_count": self.stats["sequences_failed"],
            "batches_processed": self.stats["batches_processed"],
            "duration_seconds": duration,
            "cancelled": self.cancel_requested
        }
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create error result dictionary."""
        return {
            "success": False,
            "error": error_message,
            "processed_sequences": self.stats["sequences_processed"],
            "regenerated_count": self.stats["sequences_regenerated"],
            "skipped_count": self.stats["sequences_skipped"],
            "failed_count": self.stats["sequences_failed"]
        }
    
    def get_stats(self) -> Dict:
        """Get batch processing statistics."""
        return self.stats.copy()
