from typing import TYPE_CHECKING, Union
from Enums.Enums import LetterType

from objects.arrow.arrow import Arrow

if TYPE_CHECKING:
    from main_window.main_widget.turns_tuple_generator.turns_tuple_generator import (
        TurnsTupleGenerator,
    )


class MirroredTurnsTupleGenerator:
    def __init__(self, turns_tuple_generator: "TurnsTupleGenerator"):
        self.turns_tuple_generator = turns_tuple_generator

    def generate(self, arrow: "Arrow") -> Union[str, None]:
        letter = arrow.pictograph.letter
        letter_type = LetterType.get_letter_type(arrow.pictograph.letter)

        if not arrow.pictograph.check.has_one_float():
            if (
                arrow.motion.motion_type
                != arrow.pictograph.get.other_motion(arrow.motion).motion_type
                or letter.value in ["S", "T"]
                or letter_type == LetterType.Type2
            ):
                return self.turns_tuple_generator.generate_turns_tuple(arrow.pictograph)

        if letter.value == "Λ-":
            return self.handle_lambda_dash(arrow)

        mirrored_logic = {
            LetterType.Type1: self._handle_type1,
            LetterType.Type4: self._handle_type4,
            LetterType.Type5: self._handle_type56,
            LetterType.Type6: self._handle_type56,
        }

        return mirrored_logic.get(letter_type, lambda x: None)(arrow)

    def _handle_type1(self, arrow: Arrow):
        turns_tuple = self.turns_tuple_generator.generate_turns_tuple(arrow.pictograph)
        if (
            arrow.motion.motion_type
            == arrow.pictograph.get.other_motion(arrow.motion).motion_type
            and not arrow.pictograph.check.has_one_float()
        ):
            items = turns_tuple.strip("()").split(", ")
            return f"({items[1]}, {items[0]})"
        elif (
            arrow.motion.motion_type
            != arrow.pictograph.get.other_motion(arrow.motion).motion_type
            and arrow.pictograph.check.has_one_float()
        ):
            items = turns_tuple.strip("()").split(", ")
            return f"({items[1]}, {items[0]})"
        return turns_tuple

    def _handle_type4(self, arrow: Arrow):
        turns_tuple = self.turns_tuple_generator.generate_turns_tuple(arrow.pictograph)
        prop_rotation = "cw" if "ccw" in turns_tuple else "ccw"
        turns = turns_tuple[turns_tuple.find(",") + 2 :]
        return (
            f"({prop_rotation}, {turns})"
            if "cw" in turns_tuple or "ccw" in turns_tuple
            else None
        )

    def _handle_type56(self, arrow: Arrow):
        turns_tuple = self.turns_tuple_generator.generate_turns_tuple(arrow.pictograph)
        other_arrow = arrow.pictograph.get.other_arrow(arrow)
        if arrow.motion.turns > 0 and other_arrow.motion.turns > 0:
            items = turns_tuple.strip("()").split(", ")
            return f"({items[0]}, {items[2]}, {items[1]})"
        elif arrow.motion.turns > 0 or other_arrow.motion.turns > 0:
            prop_rotation = "cw" if "ccw" in turns_tuple else "ccw"
            turns = turns_tuple[turns_tuple.find(",") + 2 : -1]
            return f"({prop_rotation}, {turns})"

    def handle_lambda_dash(self, arrow: Arrow):
        turns_tuple = self.turns_tuple_generator.generate_turns_tuple(arrow.pictograph)
        if (
            arrow.motion.turns > 0
            and arrow.pictograph.get.other_arrow(arrow).motion.turns > 0
        ):
            items = turns_tuple.strip("()").split(", ")
            return f"({items[0]}, {items[2]}, {items[1]}, {items[4]}, {items[3]})"
        elif (
            arrow.motion.turns > 0
            and arrow.pictograph.get.other_arrow(arrow).motion.turns == 0
        ):
            items = turns_tuple.strip("()").split(", ")
            return f"({items[1]}, {items[0]}, {items[2]})"
        elif (
            arrow.motion.turns == 0
            and arrow.pictograph.get.other_arrow(arrow).motion.turns > 0
        ):
            items = turns_tuple.strip("()").split(", ")
            return f"({items[1]}, {items[0]}, {items[2]})"
        return turns_tuple
