from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from .base_sidebar_section import BaseSidebarSection
from .button.sidebar_button import SidebarButton


class SidebarDateAddedSection(BaseSidebarSection):
    def create_widgets(self, sections_data: list[str]) -> None:
        parsed_dates = []
        for section in sections_data:
            if section == "Unknown":
                continue
            month, day, year = section.split("-")  # order your code reads them
            parsed_dates.append((int(year), int(month), int(day), section))

        parsed_dates.sort(reverse=True, key=lambda x: (x[0], x[1], x[2]))

        current_year = None

        if parsed_dates:
            first_spacer = QLabel()
            first_spacer.setFixedHeight(1)
            first_spacer.setStyleSheet(
                "background-color: white; border: none; margin: 0;"
            )
            self.manager.layout.addWidget(first_spacer)
            self._widgets_created.append(first_spacer)

        for year, month, day, section in parsed_dates:
            if year != current_year:
                year_label = QLabel(str(year))
                year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.style_header_label(year_label)
                self.manager.layout.addWidget(year_label)
                self._widgets_created.append(year_label)

                year_spacer = QLabel()
                year_spacer.setFixedHeight(1)
                year_spacer.setStyleSheet(
                    "background-color: white; border: none; margin: 0;"
                )
                self.manager.layout.addWidget(year_spacer)
                self._widgets_created.append(year_spacer)

                current_year = year

            date_button = SidebarButton(self.get_formatted_day(section))
            date_button.clicked_signal.connect(
                lambda section=section, btn=date_button: self.manager.scroll_to_section(
                    section, btn
                )
            )
            self.add_centered_button(date_button)
            self._widgets_created.append(date_button)
            self.manager.buttons.append(date_button)
        self.manager.layout.addStretch(1)
