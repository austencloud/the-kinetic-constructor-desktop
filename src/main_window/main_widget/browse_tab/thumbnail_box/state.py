from typing import Optional


class ThumbnailBoxState:
    def __init__(self, thumbnails: Optional[list[str]] = None):
        self.thumbnails: list[str] = thumbnails if thumbnails else []
        self.current_index: int = 0

    def update_thumbnails(self, thumbnails: list[str]):
        self.thumbnails = thumbnails
        if self.current_index >= len(self.thumbnails):
            self.current_index = max(0, len(self.thumbnails) - 1)

    def set_current_index(self, index: int):
        if 0 <= index < len(self.thumbnails):
            self.current_index = index

    def get_current_thumbnail(self) -> Optional[str]:
        if self.thumbnails and 0 <= self.current_index < len(self.thumbnails):
            return self.thumbnails[self.current_index]
        return None

    def clear(self):
        self.thumbnails.clear()
        self.current_index = 0
