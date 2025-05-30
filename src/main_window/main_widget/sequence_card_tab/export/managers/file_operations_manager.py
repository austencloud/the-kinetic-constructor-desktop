import os
from typing import List, Tuple
from .metadata_manager import MetadataManager


class FileOperationsManager:
    def __init__(self):
        self.metadata_manager = MetadataManager()

    def get_all_images(self, path: str) -> List[str]:
        image_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_files.append(os.path.join(root, file))
        return image_files

    def check_regeneration_needed(
        self, source_path: str, output_path: str
    ) -> Tuple[bool, str]:
        if not os.path.exists(output_path):
            return True, "Output file does not exist"

        source_mtime = os.path.getmtime(source_path)
        output_mtime = os.path.getmtime(output_path)
        if source_mtime > output_mtime:
            return True, "Source file is newer than output file"

        try:
            output_metadata = self.metadata_manager.extract_metadata_from_file(
                output_path
            )
            if not self.metadata_manager.validate_metadata(output_metadata):
                return True, "Output file has invalid or missing metadata"

            source_metadata = self.metadata_manager.extract_metadata_from_file(
                source_path
            )
            if not self.metadata_manager.validate_metadata(source_metadata):
                return True, "Source file has invalid or missing metadata"

            if not self.metadata_manager.compare_sequence_metadata(
                source_metadata, output_metadata
            ):
                return True, "Sequence data has changed"

            if "export_options" not in output_metadata:
                return True, "Output file missing export options"

            return False, "Up to date"

        except Exception as e:
            return True, f"Error during check: {str(e)}"

    def get_word_folders(self, dictionary_path: str) -> List[str]:
        try:
            return [
                f
                for f in os.listdir(dictionary_path)
                if os.path.isdir(os.path.join(dictionary_path, f))
                and not f.startswith("__")
            ]
        except Exception:
            return []

    def get_sequences_in_word(self, word_path: str) -> List[str]:
        try:
            return [
                f
                for f in os.listdir(word_path)
                if f.endswith(".png") and not f.startswith("__")
            ]
        except Exception:
            return []

    def ensure_directory_exists(self, path: str):
        os.makedirs(path, exist_ok=True)
