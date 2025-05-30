from PyQt6.QtWidgets import QGridLayout
from typing import List, Dict
import logging

from ...generation_manager import GeneratedSequenceData


class ApprovalDialogLayoutManager:
    def __init__(self, grid_layout, dimension_calculator):
        self.grid_layout = grid_layout
        self.dimension_calculator = dimension_calculator
        self.current_columns = 3
        self.min_columns = 2
        self.max_columns = 4
        self._updating_layout = False

    def update_layout(
        self, sequences: List[GeneratedSequenceData], columns: int, card_factory_func
    ):
        if self._updating_layout:
            return

        self._updating_layout = True
        try:
            for i in reversed(range(self.grid_layout.count())):
                child = self.grid_layout.itemAt(i).widget()
                if child:
                    self.grid_layout.removeWidget(child)

            self.current_columns = columns
            cards = {}

            for i, sequence_data in enumerate(sequences):
                row = i // self.current_columns
                col = i % self.current_columns
                card = card_factory_func(sequence_data, self.current_columns)
                cards[sequence_data.id] = card
                self.grid_layout.addWidget(card, row, col)

            logging.info(
                f"Grid layout updated: {len(sequences)} cards in {self.current_columns} columns"
            )
            return cards
        finally:
            self._updating_layout = False
