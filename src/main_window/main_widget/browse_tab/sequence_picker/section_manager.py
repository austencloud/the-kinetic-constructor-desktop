import json
from datetime import datetime
from typing import TYPE_CHECKING
from enums.letter.letter_type import LetterType
from main_window.main_widget.metadata_extractor import MetaDataExtractor
from ..section_header import BrowseTabSectionHeader
from PIL import Image

if TYPE_CHECKING:
    from .sequence_picker import SequencePicker


class SequencePickerSectionManager:
    def __init__(self, sequence_picker: "SequencePicker"):
        self.sequence_picker = sequence_picker

    def add_header(self, row_index, num_columns, section):
        header_title = f"{section}"
        header = BrowseTabSectionHeader(header_title)
        self.sequence_picker.scroll_widget.section_headers[section] = header
        self.sequence_picker.scroll_widget.grid_layout.addWidget(
            header, row_index, 0, 1, num_columns
        )

    def get_sorted_sections(self, sort_method: str, sections: list[str]) -> list[str]:
        if sort_method == "sequence_length":
            sorted_sections = sorted(
                sections, key=lambda x: int(x) if x.isdigit() else x
            )

        elif sort_method == "date_added":
            try:
                # Extract unique years first
                all_years = sorted(
                    set(s.split("-")[-1] for s in sections if s != "Unknown"),
                    reverse=True,
                )

                # Ensure sections are fully sorted by date within each year
                sorted_sections = []
                for year in all_years:
                    year_sections = [s for s in sections if s.endswith(year)]
                    sorted_year_sections = sorted(
                        year_sections,
                        key=lambda x: datetime.strptime(x, "%m-%d-%Y"),
                        reverse=True,
                    )
                    sorted_sections.extend(sorted_year_sections)

            except ValueError as e:
                print(f"[ERROR] Date parsing issue in sections: {sections} -> {e}")
                sorted_sections = list(sections)  # Fallback to whatever exists

            if "Unknown" in sections:
                sorted_sections.append("Unknown")

        elif sort_method == "level":
            # Sort numerically and filter valid levels
            valid_levels = {"1", "2", "3"}
            sorted_sections = sorted(
                [s for s in sections if s in valid_levels], key=lambda x: int(x)
            )
            # Add missing levels
            for level in ["1", "2", "3"]:
                if level not in sorted_sections:
                    sorted_sections.append(level)
        elif sort_method == "alphabetical":
            sorted_sections = sorted(sections, key=self.custom_sort_key)
        else:
            # return a value error
            raise ValueError(f"Invalid sort method: {sort_method}")
        return sorted_sections

    def custom_sort_key(self, section_str: str) -> tuple[int, int]:
        return LetterType.sort_key(section_str)

    def get_section_from_word(
        self, word, sort_order, sequence_length=None, thumbnails=None
    ):
        if sort_order == "sequence_length":
            return str(sequence_length) if sequence_length is not None else "Unknown"
        elif sort_order == "date_added":
            if thumbnails:
                date_added = self.get_date_added(thumbnails)
                if date_added:
                    return date_added.strftime("%m-%d-%Y")
                else:
                    print(f"[WARNING] No date found for: {word}, defaulting to Unknown")
                    return "Unknown"

            return "Unknown"
        elif sort_order == "level":
            for thumbnail in thumbnails:
                level = MetaDataExtractor().get_level(thumbnail)
                if level != 0:
                    return str(level)
                else:
                    raise ValueError(f"Level not found for: {word}")
            return "Unknown"
        else:
            section: str = word[:2] if len(word) > 1 and word[1] == "-" else word[0]
            if not section.isdigit():
                if section[0] in {"α", "β", "θ"}:
                    section = section.lower()
                else:
                    section = section.upper()
            return section

    def get_date_added(self, thumbnails):
        dates = []
        for thumbnail in thumbnails:
            try:
                image = Image.open(thumbnail)
                info = image.info
                metadata = info.get("metadata")
                if metadata:
                    metadata_dict = json.loads(metadata)
                    date_added = metadata_dict.get("date_added")
                    if date_added:
                        try:
                            dates.append(datetime.fromisoformat(date_added))
                        except ValueError:
                            print(
                                f"[WARNING] Could not parse date for {thumbnail}"
                            )  # Added logging
            except FileNotFoundError as e:
                print(f"[WARNING] File not found: {thumbnail} - {e}")
                continue 
            except Exception as e:
                print(f"[ERROR] An error occurred while processing {thumbnail}: {e}")

        return max(dates, default=datetime.min)
