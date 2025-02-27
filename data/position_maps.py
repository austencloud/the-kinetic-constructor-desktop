from data.constants import *


quarter_position_map_cw = {
    ALPHA1: ALPHA3,
    ALPHA2: ALPHA4,
    ALPHA3: ALPHA5,
    ALPHA4: ALPHA6,
    ALPHA5: ALPHA7,
    ALPHA6: ALPHA8,
    ALPHA7: ALPHA1,
    ALPHA8: ALPHA2,
    BETA1: BETA3,
    BETA2: BETA4,
    BETA3: BETA5,
    BETA4: BETA6,
    BETA5: BETA7,
    BETA6: BETA8,
    BETA7: BETA1,
    BETA8: BETA2,
    GAMMA1: GAMMA3,
    GAMMA2: GAMMA4,
    GAMMA3: GAMMA5,
    GAMMA4: GAMMA6,
    GAMMA5: GAMMA7,
    GAMMA6: GAMMA8,
    GAMMA7: GAMMA1,
    GAMMA8: GAMMA2,
    GAMMA9: GAMMA11,
    GAMMA10: GAMMA12,
    GAMMA11: GAMMA13,
    GAMMA12: GAMMA14,
    GAMMA13: GAMMA15,
    GAMMA14: GAMMA16,
    GAMMA15: GAMMA9,
    GAMMA16: GAMMA10,
}

quarter_position_map_ccw = {
    ALPHA1: ALPHA7,
    ALPHA2: ALPHA8,
    ALPHA3: ALPHA1,
    ALPHA4: ALPHA2,
    ALPHA5: ALPHA3,
    ALPHA6: ALPHA4,
    ALPHA7: ALPHA5,
    ALPHA8: ALPHA6,
    BETA1: BETA7,
    BETA2: BETA8,
    BETA3: BETA1,
    BETA4: BETA2,
    BETA5: BETA3,
    BETA6: BETA4,
    BETA7: BETA5,
    BETA8: BETA6,
    GAMMA1: GAMMA7,
    GAMMA2: GAMMA8,
    GAMMA3: GAMMA1,
    GAMMA4: GAMMA2,
    GAMMA5: GAMMA3,
    GAMMA6: GAMMA4,
    GAMMA7: GAMMA5,
    GAMMA8: GAMMA6,
    GAMMA9: GAMMA15,
    GAMMA10: GAMMA16,
    GAMMA11: GAMMA9,
    GAMMA12: GAMMA10,
    GAMMA13: GAMMA11,
    GAMMA14: GAMMA12,
    GAMMA15: GAMMA13,
    GAMMA16: GAMMA14,
}

half_position_map = {
    ALPHA1: ALPHA5,
    ALPHA2: ALPHA6,
    ALPHA3: ALPHA7,
    ALPHA4: ALPHA8,
    ALPHA5: ALPHA1,
    ALPHA6: ALPHA2,
    ALPHA7: ALPHA3,
    ALPHA8: ALPHA4,
    BETA1: BETA5,
    BETA2: BETA6,
    BETA3: BETA7,
    BETA4: BETA8,
    BETA5: BETA1,
    BETA6: BETA2,
    BETA7: BETA3,
    BETA8: BETA4,
    GAMMA1: GAMMA5,
    GAMMA2: GAMMA6,
    GAMMA3: GAMMA7,
    GAMMA4: GAMMA8,
    GAMMA5: GAMMA1,
    GAMMA6: GAMMA2,
    GAMMA7: GAMMA3,
    GAMMA8: GAMMA4,
    GAMMA9: GAMMA13,
    GAMMA10: GAMMA14,
    GAMMA11: GAMMA15,
    GAMMA12: GAMMA16,
    GAMMA13: GAMMA9,
    GAMMA14: GAMMA10,
    GAMMA15: GAMMA11,
    GAMMA16: GAMMA12,
}
box_positions = [
    ALPHA2,
    ALPHA4,
    ALPHA6,
    ALPHA8,
    BETA2,
    BETA4,
    BETA6,
    BETA8,
    GAMMA2,
    GAMMA4,
    GAMMA6,
    GAMMA8,
    GAMMA10,
    GAMMA12,
    GAMMA14,
    GAMMA16,
]

diamond_positions = [
    ALPHA1,
    ALPHA3,
    ALPHA5,
    ALPHA7,
    BETA1,
    BETA3,
    BETA5,
    BETA7,
    GAMMA1,
    GAMMA3,
    GAMMA5,
    GAMMA7,
    GAMMA9,
    GAMMA11,
    GAMMA13,
    GAMMA15,
]
