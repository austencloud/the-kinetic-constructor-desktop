import os
from typing import TYPE_CHECKING

from utilities.path_helpers import get_images_and_data_path

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class ThumbnailFinder:
    def __init__(self, main_widget: "MainWidget") -> None:
        self.main_widget = main_widget
        self.dictionary_dir = get_images_and_data_path("dictionary")

    def find_thumbnails(self, word_dir: str) -> list[str]:
        thumbnails = []
        for root, _, files in os.walk(word_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg")):
                    thumbnails.append(os.path.join(root, file))
        return thumbnails

    def get_all_thumbnails(self):
        thumbnails = {}
        for word in os.listdir(self.dictionary_dir):
            word_dir = os.path.join(self.dictionary_dir, word)
            if os.path.isdir(word_dir):
                thumbnails[word] = self.find_thumbnails(word_dir)
        return thumbnails
