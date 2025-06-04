from dataclasses import dataclass
from typing import Dict


@dataclass
class DictionaryDataManager:
    _data: Dict = None

    def __post_init__(self):
        if self._data is None:
            self._data = {}

    def get_data(self) -> Dict:
        return self._data

    def set_data(self, data: Dict) -> None:
        self._data = data

    def clear_data(self) -> None:
        self._data.clear()
