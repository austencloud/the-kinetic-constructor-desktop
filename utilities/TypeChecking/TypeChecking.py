from typing import *


from .letter_lists import *
from typing import Literal
from constants import *

Turns = Union[int, float]
MotionTypes = Literal["shift", "pro", "anti", "float", "dash", "static"]
Locations = Literal["n", "ne", "e", "se", "s", "sw", "w", "nw"]
Colors = Literal["blue", "red"]
Orientations = Literal["in", "out", "clock", "counter"]
ParallelCombinationsSet = Set[Tuple[str, str, str, str]]
Handpaths = Literal["dash_handpath", "static_handpath", "cw_handpath", "ccw_handpath"]
RotationAngles = Literal[0, 90, 180, 270]
PropRotDirs = Literal["cw", "ccw", "no_rot"]
OptimalLocationEntries = Dict[Literal["x", "y"], float]
StartEndLocationTuple = Tuple[Locations]
OptimalLocationDicts = Dict[str, OptimalLocationEntries]
Positions = Literal["alpha", "beta", "gamma"]
SpecificPositions = Literal[
    "alpha1",
    "alpha2",
    "alpha3",
    "alpha4",
    "beta1",
    "beta2",
    "beta3",
    "beta4",
    "gamma1",
    "gamma2",
    "gamma3",
    "gamma4",
    "gamma5",
    "gamma6",
    "gamma7",
    "gamma8",
]
ShiftHandpaths = Literal["cw_handpath", "ccw_handpath"]
Handpaths = Literal["dash_handpath", "static_handpath", "cw_handpath", "ccw_handpath"]
HexColors = Literal["#ED1C24", "#2E3192"]
Directions = Literal["left", "right", "up", "down"]
GridModes = Literal["diamond", "box"]
RadialOrientations = Literal["in", "out"]
AntiradialOrientations = Literal["clock", "counter"]
OrientationTypes = Literal["radial", "antiradial"]
Axes = Literal["horizontal", "vertical"]
MotionTypeCombinations = Literal[
    "pro_vs_pro",
    "anti_vs_anti",
    "static_vs_static",
    "pro_vs_anti",
    "static_vs_pro",
    "static_vs_anti",
    "dash_vs_pro",
    "dash_vs_anti",
    "dash_vs_static",
    "dash_vs_dash",
]
LeadStates = Literal["leading", "trailing"]
VtgTimings = Literal["split", "together"]
VtgDirections = Literal["same", "opp"]
Letters = Literal[
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "W",
    "X",
    "Y",
    "Z",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "Σ",
    "Δ",
    "θ",
    "Ω",
    "W-",
    "X-",
    "Y-",
    "Z-",
    "Σ-",
    "Δ-",
    "θ-",
    "Ω-",
    "Φ",
    "Ψ",
    "Λ",
    "Φ-",
    "Ψ-",
    "Λ-",
    "α",
    "β",
    "Γ",
]
AdjustmentStrs = Literal["-1", "-0.5", "+1", "+0.5"]
AdjustmentNums = Union[float, int]
LetterTypeNums = Literal["Type1", "Type2", "Type3", "Type4", "Type5", "Type6"]
LetterTypeDescriptions = Literal[
    "Dual-Shift", "Shift", "Cross-Shift", "Dash", "Dual-Dash", "Static"
]
MotionAttributes = Literal[
    "color",
    "arrow",
    "prop",
    "motion_type",
    "prop_rot_dir",
    "turns",
    "start_loc",
    "start_ori",
    "end_loc",
    "end_ori",
    "lead_state",
]
