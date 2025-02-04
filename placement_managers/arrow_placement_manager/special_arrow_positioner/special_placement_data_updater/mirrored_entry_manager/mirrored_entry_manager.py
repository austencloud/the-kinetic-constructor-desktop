from typing import TYPE_CHECKING

from objects.arrow.arrow import Arrow
from .mirrored_entry_data_prep import MirroredEntryDataPrep

from .mirrored_entry_rot_angle_manager import MirroredEntryRotAngleManager
from .mirrored_entry_creator import MirroredEntryCreator
from .mirrored_entry_updater.mirrored_entry_updater import MirroredEntryUpdater

if TYPE_CHECKING:
    from ...special_placement_data_updater.special_placement_data_updater import (
        SpecialPlacementDataUpdater,
    )


class MirroredEntryManager:
    def __init__(self, data_updater: "SpecialPlacementDataUpdater") -> None:
        self.data_updater = data_updater
        self.turns_tuple_generator = (
            data_updater.positioner.placement_manager.pictograph.main_widget.turns_tuple_generator
        )
        self.mirrored_entry_creator = MirroredEntryCreator(self)
        self.mirrored_entry_updater = MirroredEntryUpdater(self)
        self.rot_angle_manager = MirroredEntryRotAngleManager(self)
        self.data_prep = MirroredEntryDataPrep(self)

    def update_mirrored_entry_in_json(self, arrow: "Arrow") -> None:
        if self.data_prep.is_new_entry_needed(arrow):
            self.mirrored_entry_creator.create_entry(arrow.pictograph.letter, arrow)
        else:
            self.mirrored_entry_updater.update_entry(arrow)
