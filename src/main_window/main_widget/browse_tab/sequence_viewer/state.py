from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.thumbnail_box.favorites_manager import (
        ThumbnailBox,
    )


class SequenceViewerState:
    def __init__(self):
        self.sequence_json: Optional[dict] = None
        self.matching_thumbnail_box: "ThumbnailBox" = None
