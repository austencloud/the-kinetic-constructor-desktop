"""
Cache Manager - Handles cache validation and regeneration logic.

This component extracts cache management logic from the main exporter
following the Single Responsibility Principle.
"""

import logging
import os
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.metadata_extractor import MetaDataExtractor


class CacheManager:
    """
    Handles cache validation and regeneration logic.
    
    Responsibilities:
    - Determine if files need regeneration
    - Validate metadata consistency
    - Compare source and output files
    - Track cache hit/miss statistics
    - Manage cache invalidation strategies
    """
    
    def __init__(self, metadata_extractor: "MetaDataExtractor"):
        self.metadata_extractor = metadata_extractor
        self.logger = logging.getLogger(__name__)
        
        # Cache statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "regeneration_checks": 0,
            "metadata_errors": 0,
            "file_not_found": 0,
            "timestamp_mismatches": 0,
            "metadata_mismatches": 0
        }
        
        self.logger.info("CacheManager initialized")
    
    def needs_regeneration(self, source_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Determine if an image needs to be regenerated.
        
        Args:
            source_path: Path to the source sequence file
            output_path: Path to the output image file
            
        Returns:
            Tuple of (needs_regeneration: bool, reason: str)
        """
        self.stats["regeneration_checks"] += 1
        
        try:
            # Check 1: Output file existence
            if not os.path.exists(output_path):
                self.stats["file_not_found"] += 1
                self.stats["cache_misses"] += 1
                return True, "Output file does not exist"
            
            # Check 2: File timestamps
            timestamp_check = self._check_file_timestamps(source_path, output_path)
            if timestamp_check[0]:
                self.stats["timestamp_mismatches"] += 1
                self.stats["cache_misses"] += 1
                return timestamp_check
            
            # Check 3: Metadata validation
            metadata_check = self._validate_metadata_consistency(source_path, output_path)
            if metadata_check[0]:
                self.stats["metadata_mismatches"] += 1
                self.stats["cache_misses"] += 1
                return metadata_check
            
            # All checks passed - no regeneration needed
            self.stats["cache_hits"] += 1
            return False, "Up to date"
            
        except Exception as e:
            self.logger.error(f"Error checking regeneration for {source_path}: {e}")
            self.stats["metadata_errors"] += 1
            self.stats["cache_misses"] += 1
            return True, f"Error during check: {str(e)}"
    
    def _check_file_timestamps(self, source_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Check if source file is newer than output file.
        
        Args:
            source_path: Path to source file
            output_path: Path to output file
            
        Returns:
            Tuple of (needs_regeneration: bool, reason: str)
        """
        try:
            source_mtime = os.path.getmtime(source_path)
            output_mtime = os.path.getmtime(output_path)
            
            if source_mtime > output_mtime:
                return True, "Source file is newer than output file"
            
            return False, "Timestamps are current"
            
        except OSError as e:
            return True, f"Error checking timestamps: {e}"
    
    def _validate_metadata_consistency(self, source_path: str, output_path: str) -> Tuple[bool, str]:
        """
        Validate metadata consistency between source and output files.
        
        Args:
            source_path: Path to source file
            output_path: Path to output file
            
        Returns:
            Tuple of (needs_regeneration: bool, reason: str)
        """
        try:
            # Extract metadata from both files
            output_metadata = self.metadata_extractor.extract_metadata_from_file(output_path)
            source_metadata = self.metadata_extractor.extract_metadata_from_file(source_path)
            
            # Validate output metadata
            if not output_metadata or "sequence" not in output_metadata:
                return True, "Output file has invalid or missing metadata"
            
            # Validate source metadata
            if not source_metadata or "sequence" not in source_metadata:
                return True, "Source file has invalid or missing metadata"
            
            # Compare sequence data
            if source_metadata["sequence"] != output_metadata["sequence"]:
                return True, "Sequence data has changed"
            
            # Check for export options in output metadata
            if "export_options" not in output_metadata:
                return True, "Output file missing export options"
            
            # Validate export options consistency
            validation_result = self._validate_export_options(output_metadata["export_options"])
            if validation_result[0]:
                return validation_result
            
            return False, "Metadata is consistent"
            
        except Exception as e:
            return True, f"Metadata validation error: {e}"
    
    def _validate_export_options(self, export_options: dict) -> Tuple[bool, str]:
        """
        Validate export options for consistency.
        
        Args:
            export_options: Export options dictionary
            
        Returns:
            Tuple of (needs_regeneration: bool, reason: str)
        """
        # Define required export options
        required_options = {
            "add_word", "add_user_info", "add_difficulty_level", 
            "add_date", "add_note", "add_beat_numbers", 
            "add_reversal_symbols", "combined_grids", "include_start_position"
        }
        
        # Check if all required options are present
        missing_options = required_options - set(export_options.keys())
        if missing_options:
            return True, f"Missing export options: {missing_options}"
        
        # Validate option values (could be extended with specific validation rules)
        for option, value in export_options.items():
            if not isinstance(value, (bool, str, int, float)):
                return True, f"Invalid export option value for {option}: {value}"
        
        return False, "Export options are valid"
    
    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate as a percentage.
        
        Returns:
            Cache hit rate percentage (0-100)
        """
        total_checks = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_checks == 0:
            return 0.0
        
        return (self.stats["cache_hits"] / total_checks) * 100
    
    def invalidate_cache_for_file(self, output_path: str) -> bool:
        """
        Invalidate cache for a specific file by removing it.
        
        Args:
            output_path: Path to the output file to invalidate
            
        Returns:
            True if file was removed, False otherwise
        """
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
                self.logger.info(f"Cache invalidated for: {output_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to invalidate cache for {output_path}: {e}")
            return False
    
    def get_cache_summary(self, source_dir: str, output_dir: str) -> dict:
        """
        Get a summary of cache status for a directory.
        
        Args:
            source_dir: Source directory path
            output_dir: Output directory path
            
        Returns:
            Dictionary with cache summary statistics
        """
        summary = {
            "total_source_files": 0,
            "total_output_files": 0,
            "up_to_date_files": 0,
            "outdated_files": 0,
            "missing_files": 0,
            "error_files": 0
        }
        
        try:
            # Count source files
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.endswith(".png") and not file.startswith("__"):
                        summary["total_source_files"] += 1
                        
                        source_path = os.path.join(root, file)
                        # Calculate corresponding output path
                        rel_path = os.path.relpath(source_path, source_dir)
                        output_path = os.path.join(output_dir, rel_path)
                        
                        needs_regen, reason = self.needs_regeneration(source_path, output_path)
                        
                        if "does not exist" in reason:
                            summary["missing_files"] += 1
                        elif "Error" in reason:
                            summary["error_files"] += 1
                        elif needs_regen:
                            summary["outdated_files"] += 1
                        else:
                            summary["up_to_date_files"] += 1
            
            # Count output files
            if os.path.exists(output_dir):
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(".png"):
                            summary["total_output_files"] += 1
            
        except Exception as e:
            self.logger.error(f"Error generating cache summary: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def get_stats(self) -> dict:
        """Get cache management statistics."""
        hit_rate = self.get_cache_hit_rate()
        
        return {
            **self.stats,
            "cache_hit_rate_percent": round(hit_rate, 2),
            "total_checks": self.stats["cache_hits"] + self.stats["cache_misses"]
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "regeneration_checks": 0,
            "metadata_errors": 0,
            "file_not_found": 0,
            "timestamp_mismatches": 0,
            "metadata_mismatches": 0
        }
        self.logger.info("Cache statistics reset")
