import json
from data.constants import DIAMOND, GRID_MODE
from utils.path_helpers import get_user_editable_resource_path
from .default_sequence_provider import DefaultSequenceProvider


class CurrentSequenceLoader:
    def __init__(self, filename="current_sequence.json"):
        self.current_sequence_json = get_user_editable_resource_path(filename)

    def load_current_sequence_json(self) -> list[dict]:
        try:
            with open(self.current_sequence_json, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    return self.get_default_sequence()

                sequence = json.loads(content)
                if not sequence or not isinstance(sequence, list):
                    return self.get_default_sequence()

            return sequence

        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_sequence()

    def get_default_sequence(self) -> list[dict]:
        """Return a default sequence if JSON is missing, empty, or invalid."""
        return DefaultSequenceProvider.get_default_sequence()
