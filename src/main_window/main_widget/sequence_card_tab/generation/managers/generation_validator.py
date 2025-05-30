import logging
from typing import TYPE_CHECKING

from ..generation_params import GenerationParams
from ..generated_sequence_data import GeneratedSequenceData

if TYPE_CHECKING:
    pass


class GenerationValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_sequence_length(
        self, generated_data: GeneratedSequenceData, params: GenerationParams
    ) -> bool:
        if not generated_data:
            return False

        sequence_data = generated_data.sequence_data

        beat_count = len(
            [
                item
                for item in sequence_data
                if item.get("beat") is not None
                and item.get("beat") > 0
                and not item.get("sequence_start_position", False)
            ]
        )

        if beat_count != params.length:
            self.logger.error(
                f"Length validation failed: requested={params.length}, generated={beat_count}"
            )
            self.logger.error(
                f"Sequence structure: {[item.get('beat', 'metadata/start') for item in sequence_data]}"
            )
            return False

        self.logger.info(
            f"Length validation passed: {beat_count} beats generated as requested"
        )
        return True

    def validate_sequence_data(self, sequence_data: list) -> bool:
        if not sequence_data or len(sequence_data) < 3:
            self.logger.error(
                f"Invalid sequence data: length={len(sequence_data) if sequence_data else 0}"
            )
            return False
        return True
