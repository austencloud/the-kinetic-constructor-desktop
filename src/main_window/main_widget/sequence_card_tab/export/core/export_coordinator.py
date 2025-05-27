"""
Export Coordinator - Orchestrates all image export operations.

This coordinator replaces the monolithic SequenceCardImageExporter with a clean
architecture that follows the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from .image_converter import ImageConverter
from .batch_processor import BatchProcessor
from .cache_manager import CacheManager
from .memory_manager import MemoryManager
from .file_operations_manager import FileOperationsManager

if TYPE_CHECKING:
    from ..image_exporter import SequenceCardImageExporter


class ExportCoordinator:
    """
    Coordinates all image export operations using focused components.
    
    This coordinator orchestrates:
    - Image conversion (QImage to PIL with memory management)
    - Batch processing (memory-efficient processing)
    - Cache management (regeneration logic, metadata validation)
    - Memory management (monitoring, cleanup, garbage collection)
    - File operations (directory creation, path handling)
    
    Each responsibility is handled by a dedicated component following SRP.
    """
    
    def __init__(self, exporter: "SequenceCardImageExporter"):
        self.exporter = exporter
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized components
        self.image_converter = ImageConverter()
        self.batch_processor = BatchProcessor(exporter)
        self.cache_manager = CacheManager(exporter.metadata_extractor)
        self.memory_manager = MemoryManager()
        self.file_operations = FileOperationsManager()
        
        # Export statistics
        self.stats = {
            "processed_sequences": 0,
            "regenerated_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "start_time": None,
            "end_time": None
        }
        
        self.logger.info("ExportCoordinator initialized with component architecture")
    
    def export_all_images(self) -> dict:
        """
        Coordinate the complete image export process.
        
        Returns:
            Dictionary with export statistics and results
        """
        self.logger.info("Starting coordinated image export process")
        self.stats["start_time"] = datetime.now()
        
        try:
            # Phase 1: Setup and validation
            export_config = self._setup_export_environment()
            if not export_config:
                return self._create_error_result("Failed to setup export environment")
            
            # Phase 2: Discover sequences
            sequences = self._discover_sequences(export_config)
            if not sequences:
                return self._create_error_result("No sequences found to export")
            
            # Phase 3: Process in batches
            self._process_sequences_in_batches(sequences, export_config)
            
            # Phase 4: Cleanup and finalize
            self._finalize_export()
            
            return self._create_success_result()
            
        except Exception as e:
            self.logger.error(f"Export coordination failed: {e}")
            return self._create_error_result(f"Export failed: {str(e)}")
    
    def _setup_export_environment(self) -> Optional[dict]:
        """Setup the export environment and validate paths."""
        try:
            config = self.file_operations.setup_export_environment()
            self.memory_manager.initialize_monitoring()
            return config
        except Exception as e:
            self.logger.error(f"Failed to setup export environment: {e}")
            return None
    
    def _discover_sequences(self, config: dict) -> list:
        """Discover all sequences to be exported."""
        try:
            return self.file_operations.discover_sequences(
                config["dictionary_path"],
                config["word_folders"]
            )
        except Exception as e:
            self.logger.error(f"Failed to discover sequences: {e}")
            return []
    
    def _process_sequences_in_batches(self, sequences: list, config: dict) -> None:
        """Process sequences using the batch processor."""
        try:
            # Configure batch processor
            self.batch_processor.configure(
                sequences=sequences,
                export_config=config,
                image_converter=self.image_converter,
                cache_manager=self.cache_manager,
                memory_manager=self.memory_manager,
                file_operations=self.file_operations
            )
            
            # Process batches
            batch_results = self.batch_processor.process_all_batches()
            
            # Update statistics
            self.stats.update(batch_results)
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            self.stats["failed_count"] += 1
    
    def _finalize_export(self) -> None:
        """Finalize the export process."""
        self.stats["end_time"] = datetime.now()
        self.memory_manager.final_cleanup()
        
        # Log summary
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.logger.info(f"Export completed in {duration:.2f} seconds")
        self.logger.info(f"Statistics: {self.stats}")
    
    def _create_success_result(self) -> dict:
        """Create success result dictionary."""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "message": "Export completed successfully"
        }
    
    def _create_error_result(self, error_message: str) -> dict:
        """Create error result dictionary."""
        return {
            "success": False,
            "statistics": self.stats.copy(),
            "error": error_message
        }
    
    # Delegation methods for backward compatibility
    def convert_qimage_to_pil(self, qimage, max_dimension: int = 3000):
        """Convert QImage to PIL Image."""
        return self.image_converter.convert_qimage_to_pil(qimage, max_dimension)
    
    def check_regeneration_needed(self, source_path: str, output_path: str) -> tuple:
        """Check if regeneration is needed."""
        return self.cache_manager.needs_regeneration(source_path, output_path)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage."""
        return self.memory_manager.get_current_usage()
    
    def force_memory_cleanup(self) -> None:
        """Force memory cleanup."""
        self.memory_manager.force_cleanup()
    
    def get_export_statistics(self) -> dict:
        """Get current export statistics."""
        return self.stats.copy()
    
    def cancel_export(self) -> None:
        """Cancel the export process."""
        self.batch_processor.cancel_processing()
        self.logger.info("Export cancellation requested")
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics from all components.
        
        Returns:
            Dictionary with component performance data
        """
        return {
            "coordinator_stats": self.stats.copy(),
            "memory_stats": self.memory_manager.get_stats(),
            "batch_stats": self.batch_processor.get_stats(),
            "cache_stats": self.cache_manager.get_stats(),
            "file_stats": self.file_operations.get_stats(),
            "converter_stats": self.image_converter.get_stats()
        }
