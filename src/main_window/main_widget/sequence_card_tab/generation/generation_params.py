class GenerationParams:
    def __init__(
        self,
        length: int = 16,
        level: int = 1,
        turn_intensity: int = 1,
        prop_continuity: str = "continuous",
        generation_mode: str = "freeform",
        rotation_type: str = "halved",
        CAP_type: str = "strict_rotated",
        start_position: str = None,
    ):
        self.length = length
        self.level = level
        self.turn_intensity = turn_intensity
        self.prop_continuity = prop_continuity
        self.generation_mode = generation_mode
        self.rotation_type = rotation_type
        self.CAP_type = CAP_type
        self.start_position = start_position
