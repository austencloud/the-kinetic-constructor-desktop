import json
from datetime import datetime
from PIL import PngImagePlugin
from main_window.main_widget.metadata_extractor import MetaDataExtractor


class MetadataManager:
    def __init__(self):
        self.metadata_extractor = MetaDataExtractor()

    def create_png_info(self, metadata: dict) -> PngImagePlugin.PngInfo:
        info = PngImagePlugin.PngInfo()
        info.add_text("metadata", json.dumps(metadata))
        return info

    def extract_metadata_from_file(self, file_path: str) -> dict:
        return self.metadata_extractor.extract_metadata_from_file(file_path)

    def prepare_export_metadata(
        self, base_metadata: dict, export_options: dict
    ) -> dict:
        enhanced_metadata = base_metadata.copy()
        enhanced_metadata["export_options"] = export_options
        enhanced_metadata["export_date"] = datetime.now().isoformat()
        return enhanced_metadata

    def validate_metadata(self, metadata: dict) -> bool:
        return metadata and "sequence" in metadata

    def compare_sequence_metadata(
        self, source_metadata: dict, output_metadata: dict
    ) -> bool:
        if not self.validate_metadata(source_metadata) or not self.validate_metadata(
            output_metadata
        ):
            return False
        return source_metadata["sequence"] == output_metadata["sequence"]
