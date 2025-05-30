import copy
import logging
from typing import TYPE_CHECKING

from ..generation_params import GenerationParams

if TYPE_CHECKING:
    pass


class GenerationParameterManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def add_parameter_variation(
        self, base_params: GenerationParams, current_batch_size: int = 1
    ) -> GenerationParams:
        consistent_params = copy.deepcopy(base_params)

        # For batch generation, always use random start positions to ensure natural variation
        # Even if user selected a specific start position for single generation
        if current_batch_size > 1:
            consistent_params.start_position = None
            self.logger.info(
                "Batch generation: forcing random start positions for natural variation"
            )

        self.logger.info(
            f"Using consistent parameters for all sequences in batch: {consistent_params.__dict__}"
        )
        return consistent_params
