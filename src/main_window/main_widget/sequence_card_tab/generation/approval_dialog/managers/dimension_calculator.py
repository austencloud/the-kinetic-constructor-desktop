from PyQt6.QtWidgets import QGridLayout
from typing import List, Dict
import logging

from ...generation_manager import GeneratedSequenceData


class ApprovalDialogDimensionCalculator:
    def __init__(self, parent_size, sequences_count):
        self.sequences_count = sequences_count
        self.dialog_width = int(parent_size.width() * 0.9) if parent_size else 1400
        self.dialog_height = int(parent_size.height() * 0.9) if parent_size else 900
        self.available_width = self.dialog_width - 80
        self.available_height = self.dialog_height - 200

    def calculate_card_dimensions(self, columns: int):
        grid_spacing = 15
        scroll_margins = 40
        total_spacing = (columns - 1) * grid_spacing + scroll_margins
        available_card_width = (self.available_width - total_spacing) // columns

        card_width = available_card_width
        image_width = int(card_width)
        image_height = int(image_width * 0.7)

        info_section_height = 20
        card_margins = 30
        card_height = image_height + info_section_height + card_margins

        max_card_height = self.available_height
        card_height = min(card_height, max_card_height)

        if card_height == max_card_height:
            image_height = card_height - info_section_height - card_margins
            image_width = int(image_height / 0.7)

        logging.info(
            f"Card dimensions for {columns} columns: {card_width}x{card_height}, image: {image_width}x{image_height}"
        )
        return card_width, card_height, image_width, image_height
