import json
import os
import hashlib
from typing import TYPE_CHECKING
from main_window.main_widget.metadata_extractor import MetaDataExtractor
from utilities.path_helpers import get_images_and_data_path

if TYPE_CHECKING:
    from .add_to_dictionary_manager import AddToDictionaryManager


def hash_sequence(sequence):
    seq_str = json.dumps(sequence, sort_keys=True)
    return hashlib.sha256(seq_str.encode()).hexdigest()


class StructuralVariationChecker:
    def __init__(self):
        self.dictionary_dir = get_images_and_data_path("dictionary")
        self.metadata_extractor = MetaDataExtractor()

    def check_for_structural_variation(self, current_sequence, base_word):
        base_path = os.path.join(self.dictionary_dir, base_word)
        for root, _, files in os.walk(base_path):
            for filename in files:
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join(root, filename)
                    existing_sequence = self.metadata_extractor.extract_metadata_from_file(
                        file_path
                    )
                    if (
                        existing_sequence
                        and self.are_structural_variations_identical(
                            current_sequence, existing_sequence
                        )
                    ):
                        return True
        return False

    def are_structural_variations_identical(self, seq1, seq2):
        def matches(b1, b2):
            ignore = ["turns", "end_ori", "start_ori"]
            return all(b1[k] == b2[k] for k in b1 if k not in ignore)

        if len(seq1) != len(seq2):
            return False

        for b1, b2 in zip(seq1, seq2):
            for color in ["blue_attributes", "red_attributes"]:
                if color in b1 and color in b2:
                    if not matches(b1[color], b2[color]):
                        return False
        return True

