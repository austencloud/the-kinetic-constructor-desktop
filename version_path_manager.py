from pathlib import Path
from enum import Enum
from typing import Optional


class Version(Enum):
    V1 = "v1"
    V2 = "v2"


class PathManager:
    def __init__(self):
        self.root = Path(__file__).parent

    def get_arrow_placement_path(
        self,
        grid_mode: str,
        placement_type: str,
        filename: str,
        version: Version = Version.V1,
    ) -> str:
        if version == Version.V2:
            base_path = self.root / "data" / "arrow_placements" / grid_mode
        else:
            base_path = self.root / "data" / "arrow_placements" / grid_mode

        return str(base_path / filename)

    def get_data_path(self, version: Version = Version.V1) -> Path:

        return self.root / "data"


_path_manager_instance: Optional[PathManager] = None


def get_path_manager() -> PathManager:
    global _path_manager_instance
    if _path_manager_instance is None:
        _path_manager_instance = PathManager()
    return _path_manager_instance
