from data.start_end_location_mapping import start_end_location_mapping

class ArrowAttributes:
    ARROW_ATTRIBUTES = [
        'color', 'motion_type', 'rotation_direction', 
        'quadrant', 'end_location', 'start_location', 'turns'
    ]
    
    def __init__(self, arrow, arrow_dict = None):
        if arrow_dict:
            self.update_attributes(arrow, arrow_dict)

    def update_attributes(self, arrow, arrow_dict):
        for attr in self.ARROW_ATTRIBUTES:
            value = arrow_dict.get(attr)
            if attr == 'turns':
                value = int(value)
            setattr(arrow, attr, value)

    def get_start_end_locations(self, motion_type, rotation_direction, quadrant):
        return start_end_location_mapping.get(
            quadrant, {}).get(rotation_direction, {}).get(motion_type, (None, None))

    def get_attributes(self, arrow):
        return {attr: getattr(arrow, attr) for attr in self.ARROW_ATTRIBUTES}

    def create_dict_from_arrow(self, arrow):
        start_location, end_location = self.get_start_end_locations(arrow.motion_type, arrow.rotation_direction, arrow.quadrant)
        
        arrow_dict = {
            'color': arrow.color,
            'motion_type': arrow.motion_type,
            'rotation_direction': arrow.rotation_direction,
            'quadrant': arrow.quadrant,
            'start_location': start_location,
            'end_location': end_location,
            'turns': arrow.turns
        }
        return arrow_dict