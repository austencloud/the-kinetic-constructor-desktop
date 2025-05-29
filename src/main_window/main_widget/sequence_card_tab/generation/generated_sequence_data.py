import random
from typing import List, Dict, Any
from .generation_params import GenerationParams


class GeneratedSequenceData:
    def __init__(self, sequence_data: List[Dict[str, Any]], params: GenerationParams):
        self.sequence_data = sequence_data
        self.params = params
        self.id = f"gen_{random.randint(10000, 99999)}"
        self.word = self._extract_word_from_sequence()
        self.image_path = None
        self.approved = False

    def _extract_word_from_sequence(self) -> str:
        """
        Extract word from sequence using the same logic as current_word_label.
        Ignores start position (index 1) and metadata (index 0), uses only actual beats.
        """
        try:
            if self.sequence_data and len(self.sequence_data) > 2:
                # Skip metadata (index 0) and start position (index 1)
                # Use only the actual sequence beats (index 2 onwards)
                sequence_beats = self.sequence_data[2:]
                letters = []
                for beat in sequence_beats:
                    if "letter" in beat:
                        letters.append(beat["letter"])

                if letters:
                    # Apply the same word simplification logic as current_word_label
                    from utils.word_simplifier import WordSimplifier

                    word = "".join(letters)
                    return WordSimplifier.simplify_repeated_word(word)
                else:
                    return f"Generated_{self.id}"
            return f"Generated_{self.id}"
        except Exception as e:
            print(f"Error extracting word from sequence: {e}")
            return f"Generated_{self.id}"
