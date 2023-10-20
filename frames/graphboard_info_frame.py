from objects.arrow import Arrow
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget
from data.positions_map import positions_map
from data.letter_types import letter_types
from settings import GRAPHBOARD_SCALE

class Graphboard_Info_Frame(QFrame):
    def __init__(self, main_widget, view):
        super().__init__()
        self.remaining_staff = {}
        self.previous_state = None 
        self.view = view
        self.staff_manager = main_widget.staff_manager
        self.letters = main_widget.letters
        self.main_window = main_widget.main_window


        # Initialize the labels with the 'Left' and 'Right' text
        self.blue_details_label = QLabel("Left")
        self.blue_details_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.blue_details_label.setStyleSheet("color: blue; font-size: 25px; font-weight: bold;")
        
        self.red_details_label = QLabel("Right")
        self.red_details_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.red_details_label.setStyleSheet("color: red; font-size: 25px; font-weight: bold;")

        self.type_position_label = QLabel()
        self.type_position_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Initialize the grid layout
        self.grid_layout = QGridLayout()
        # Set fixed spacing in pixels between the items in your layouts.
        self.grid_layout.setVerticalSpacing(10)  # for example, 10 pixels between rows.
        # Assuming you want the vertical space distribution ratio to be 1:3:2


        # Create a separate layout for headers
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.blue_details_label)
        header_layout.addWidget(self.red_details_label)
        header_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins: left, top, right, bottom

        # Create a separate layout for content (arrow details)
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins: left, top, right, bottom

        # Initialize the type and position layout and labels
        self.type_position_layout = QHBoxLayout()
        self.type_position_layout.addWidget(self.type_position_label)
        self.type_position_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins: left, top, right, bottom
        # Configure the layout properties for the type and position section
        


        # Create a widget to hold the type and position layout, and set its properties
        type_position_widget = QWidget()
        type_position_widget.setLayout(self.type_position_layout)
        type_position_widget.setFixedHeight(int(240 * GRAPHBOARD_SCALE))  # Or another value that suits the design

        # Instead of directly adding layouts, we will add them to QWidgets and then add these widgets to the grid
        # Create a widget to hold the header layout
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(int(120 * GRAPHBOARD_SCALE))
        #remove the padding on the top

        
        # Create a widget to hold the content layout
        content_widget = QWidget()
        content_widget.setLayout(self.content_layout)

        # Adjust the grid layout to add widgets instead of layouts
        # The row stretches ensure that the header takes only the space it needs, and the rest goes to content
        self.grid_layout.addWidget(header_widget, 0, 0)  # Add the header widget
        self.grid_layout.addWidget(content_widget, 1, 0)  # Add the content widget
        self.grid_layout.addWidget(type_position_widget, 2, 0)  # Add to the third row (index 2) and first column (index 0)

        self.grid_layout.setRowStretch(0, 0)  # Do not stretch the header row; let it determine its size based on content
        self.grid_layout.setRowStretch(1, 1)  # Allow the content row to take up the remaining space

        # Setup the main layout
        self.setLayout(self.grid_layout)
        self.setFixedWidth(int(900 * GRAPHBOARD_SCALE))
        self.setFixedHeight(int(900 * GRAPHBOARD_SCALE))
        
    def update_type_and_position_info(self):
        # Determine the current letter and its type
        current_letter, current_letter_type = self.determine_current_letter_and_type()

        # Check if the letter and type were successfully retrieved
        if current_letter and current_letter_type:
            # Determine the start and end positions based on the current state
            start_end_positions = self.get_start_end_locations()
            if start_end_positions:
                start_position, end_position = start_end_positions


            # Now that you have new type, letter, and position information, you can update the relevant label.
            info_text = f"<center><h2>{current_letter_type}</h2><p style='font-size: 18px; font-family:'Cambria;''>{start_position} → {end_position}</center></p>"
            self.type_position_label.setText(info_text)
        else:
            # Handle cases where the letter or type is not identified
            self.type_position_label.setText("")
            
    def connect_graphboard_view(self, view):
        self.view = view

    ### GETTERS ###

    def get_current_letter(self):
        self.letter = self.determine_current_letter_and_type()[0]
        if self.letter is not None:
            return self.letter
    
    def determine_current_letter_and_type(self):
        current_combination = []
        for item in self.view.items():
            if isinstance(item, Arrow):
                attributes = item.get_attributes()
                sorted_attributes = {k: attributes[k] for k in sorted(attributes.keys())}
                current_combination.append(sorted_attributes)
        # Sort the list of dictionaries by the 'color' key
        current_combination = sorted(current_combination, key=lambda x: x['color'])
        letter_type = None
        for letter, combinations in self.letters.items():
            combinations = [sorted([x for x in combination if 'color' in x], key=lambda x: x['color']) for combination in combinations]
            if current_combination in combinations:
                self.letter = letter
                for type, letters in letter_types.items():  # Determine the type if a letter is found
                    if self.letter in letters:
                        current_type = type
                        break
                return self.letter, current_type  # Return both values here
        self.letter = None  # Set to None if no match is found

        return self.letter, letter_type  # Always return two values
   
    def update(self):
        self.remaining_staff = {}  # Reset the remaining staff info

        # Create placeholders for arrow attributes to ensure alignment
        blue_attributes = {}
        red_attributes = {}

        # Now, we can construct the initial text for the labels since we have initialized the attributes.
        blue_text = ""
        red_text = ""

        # Process the arrows and construct detailed information
        for arrow in [item for item in self.view.items() if isinstance(item, Arrow)]:
            
            if not arrow.is_ghost:
                arrow.set_attributes_from_filename()  # Ensure the attributes are up-to-date

            # Update the respective attribute dictionaries
            attributes_dict = blue_attributes if arrow.color == 'blue' else red_attributes if arrow.color == 'red' else None

            if attributes_dict is not None:
                attributes_dict['Type'] = arrow.motion_type.capitalize()
                attributes_dict['Start'] = arrow.start_location.capitalize()
                attributes_dict['End'] = arrow.end_location.capitalize()
                attributes_dict['Turns'] = str(arrow.turns)

        # Construct information strings ensuring the values (not keys) are bold and aligned
        blue_info_label = self.construct_info_string_label(blue_attributes)
        red_info_label = self.construct_info_string_label(red_attributes)

        # Append arrow information to the section text
        blue_text += blue_info_label.text()
        red_text += red_info_label.text()

        self.clear_layout(self.content_layout)

        self.content_layout.addWidget(blue_info_label)
        self.content_layout.addWidget(red_info_label)

        # Now that you have new type, letter, and position information, you can update the relevant label.
        self.update_type_and_position_info()

        # Inform the graphboard view about the current letter
        self.view.update_letter(self.determine_current_letter_and_type()[0])


        # Update the staffs on the graphboard based on the new state
        self.staff_manager.update_graphboard_staffs(self.view.scene())

    @staticmethod
    def clear_layout(layout):
        """Removes all widgets from the given layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def construct_info_string_label(self, attributes):
        """Constructs a formatted string for arrow information with aligned values."""
        info_strings = []
        for key, value in attributes.items():
            if value:  # Check if the value is not an empty string
                # Make keys italic and values bold, and both black in color
                info_strings.append(f"<span style='font-style: italic; color: black;'>{key}:</span> <span style='font-weight: bold; color: black;'>{value}</span><br>")

        # Combine all attribute strings and wrap them in a paragraph with a specific font size
        return QLabel("<p style='font-size: 18px; text-align: left;'>" + "".join(info_strings) + "</p>")
    
    def get_start_end_locations(self):
        positions = []
        arrow_items = []
        counter = 1
        start_location_red = None
        end_location_red = None
        start_location_blue = None
        end_location_blue = None
        color_red = None
        color_blue = None
        for item in self.view.items():
            if isinstance(item, Arrow):
                arrow_items.append(item)

        for arrow in arrow_items:
            if arrow.color == 'red':
                start_location_red = arrow.start_location
                end_location_red = arrow.end_location
                color_red = arrow.color
                counter += 1
            else: # arrow.color == 'blue'
                start_location_blue = arrow.start_location
                end_location_blue = arrow.end_location
                color_blue = arrow.color

        if start_location_red is not None and end_location_red is not None and start_location_blue is not None and end_location_blue is not None:
            start_key = (start_location_red, color_red, start_location_blue, color_blue)
            end_key = (end_location_red, color_red, end_location_blue, color_blue)
            start_location = positions_map.get(start_key)
            end_location = positions_map.get(end_key)
            positions.append(start_location)
            positions.append(end_location)


        if positions is not None:
            return positions
        else:
            print("no positions returned by get_start_end_locations")
            return None

