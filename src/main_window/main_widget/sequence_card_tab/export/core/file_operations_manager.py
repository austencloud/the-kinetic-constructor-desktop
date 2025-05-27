"""
File Operations Manager - Handles file and directory operations.

This component extracts file operations logic from the main exporter
following the Single Responsibility Principle.
"""

import logging
import os
from typing import List, Dict, Tuple
from pathlib import Path
from utils.path_helpers import get_dictionary_path, get_sequence_card_image_exporter_path


class FileOperationsManager:
    """
    Handles file and directory operations for export.
    
    Responsibilities:
    - Set up export environment and directories
    - Discover sequences in dictionary
    - Build source and output paths
    - Ensure directory structure exists
    - Handle file system operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # File operation statistics
        self.stats = {
            "directories_created": 0,
            "sequences_discovered": 0,
            "path_operations": 0,
            "file_system_errors": 0
        }
        
        self.logger.info("FileOperationsManager initialized")
    
    def setup_export_environment(self) -> Dict:
        """
        Set up the export environment and validate paths.
        
        Returns:
            Dictionary with export configuration
        """
        try:
            # Get paths
            dictionary_path = get_dictionary_path()
            export_path = get_sequence_card_image_exporter_path()
            
            # Validate dictionary path
            if not os.path.exists(dictionary_path):
                raise FileNotFoundError(f"Dictionary path does not exist: {dictionary_path}")
            
            # Create export directory if needed
            if not os.path.exists(export_path):
                os.makedirs(export_path)
                self.stats["directories_created"] += 1
                self.logger.info(f"Created export directory: {export_path}")
            
            # Discover word folders
            word_folders = self._discover_word_folders(dictionary_path)
            
            config = {
                "dictionary_path": dictionary_path,
                "export_path": export_path,
                "word_folders": word_folders
            }
            
            self.logger.info(
                f"Export environment setup complete: "
                f"dictionary={dictionary_path}, export={export_path}, "
                f"words={len(word_folders)}"
            )
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to setup export environment: {e}")
            self.stats["file_system_errors"] += 1
            raise
    
    def _discover_word_folders(self, dictionary_path: str) -> List[str]:
        """
        Discover word folders in the dictionary.
        
        Args:
            dictionary_path: Path to the dictionary
            
        Returns:
            List of word folder names
        """
        word_folders = []
        
        try:
            for item in os.listdir(dictionary_path):
                item_path = os.path.join(dictionary_path, item)
                if os.path.isdir(item_path) and not item.startswith("__"):
                    word_folders.append(item)
            
            self.logger.info(f"Discovered {len(word_folders)} word folders")
            return word_folders
            
        except Exception as e:
            self.logger.error(f"Failed to discover word folders: {e}")
            self.stats["file_system_errors"] += 1
            return []
    
    def discover_sequences(self, dictionary_path: str, word_folders: List[str]) -> List[Tuple[str, str]]:
        """
        Discover all sequences in the dictionary.
        
        Args:
            dictionary_path: Path to the dictionary
            word_folders: List of word folder names
            
        Returns:
            List of (word, sequence_file) tuples
        """
        sequences = []
        
        try:
            for word in word_folders:
                word_path = os.path.join(dictionary_path, word)
                
                try:
                    for sequence_file in os.listdir(word_path):
                        if sequence_file.endswith(".png") and not sequence_file.startswith("__"):
                            sequences.append((word, sequence_file))
                            self.stats["sequences_discovered"] += 1
                except OSError as e:
                    self.logger.warning(f"Failed to read word folder {word}: {e}")
                    self.stats["file_system_errors"] += 1
            
            self.logger.info(f"Discovered {len(sequences)} sequences total")
            return sequences
            
        except Exception as e:
            self.logger.error(f"Failed to discover sequences: {e}")
            self.stats["file_system_errors"] += 1
            return []
    
    def build_source_path(self, dictionary_path: str, word: str, sequence_file: str) -> str:
        """
        Build the source path for a sequence file.
        
        Args:
            dictionary_path: Path to the dictionary
            word: Word folder name
            sequence_file: Sequence file name
            
        Returns:
            Full path to the source file
        """
        self.stats["path_operations"] += 1
        return os.path.join(dictionary_path, word, sequence_file)
    
    def build_output_path(self, export_path: str, word: str, sequence_file: str) -> str:
        """
        Build the output path for a sequence file.
        
        Args:
            export_path: Base export path
            word: Word folder name
            sequence_file: Sequence file name
            
        Returns:
            Full path to the output file
        """
        self.stats["path_operations"] += 1
        return os.path.join(export_path, word, sequence_file)
    
    def ensure_output_directory(self, output_path: str) -> bool:
        """
        Ensure the output directory exists for a file path.
        
        Args:
            output_path: Full path to the output file
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                self.stats["directories_created"] += 1
                self.logger.debug(f"Created output directory: {output_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create output directory for {output_path}: {e}")
            self.stats["file_system_errors"] += 1
            return False
    
    def get_all_images(self, path: str) -> List[str]:
        """
        Get all image files in a directory tree.
        
        Args:
            path: Root path to search
            
        Returns:
            List of image file paths
        """
        images = []
        
        try:
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith((".png", ".jpg", ".jpeg")):
                        images.append(os.path.join(root, file))
            
            self.logger.debug(f"Found {len(images)} image files in {path}")
            return images
            
        except Exception as e:
            self.logger.error(f"Failed to get images from {path}: {e}")
            self.stats["file_system_errors"] += 1
            return []
    
    def validate_file_access(self, file_path: str, mode: str = "r") -> bool:
        """
        Validate that a file can be accessed with the specified mode.
        
        Args:
            file_path: Path to the file
            mode: Access mode ('r' for read, 'w' for write)
            
        Returns:
            True if file can be accessed
        """
        try:
            if mode == "r":
                return os.path.exists(file_path) and os.access(file_path, os.R_OK)
            elif mode == "w":
                # Check if we can write to the directory
                directory = os.path.dirname(file_path)
                return os.path.exists(directory) and os.access(directory, os.W_OK)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Failed to validate file access for {file_path}: {e}")
            return False
    
    def get_directory_size(self, directory_path: str) -> int:
        """
        Get the total size of a directory in bytes.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        try:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        # Skip files that can't be accessed
                        continue
            
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to calculate directory size for {directory_path}: {e}")
            return 0
    
    def cleanup_empty_directories(self, base_path: str) -> int:
        """
        Remove empty directories from the export path.
        
        Args:
            base_path: Base path to clean up
            
        Returns:
            Number of directories removed
        """
        removed_count = 0
        
        try:
            for root, dirs, files in os.walk(base_path, topdown=False):
                for directory in dirs:
                    dir_path = os.path.join(root, directory)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                            removed_count += 1
                            self.logger.debug(f"Removed empty directory: {dir_path}")
                    except OSError:
                        # Directory not empty or can't be removed
                        continue
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} empty directories")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup empty directories: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get file operations statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset file operations statistics."""
        self.stats = {
            "directories_created": 0,
            "sequences_discovered": 0,
            "path_operations": 0,
            "file_system_errors": 0
        }
        self.logger.info("File operations statistics reset")
