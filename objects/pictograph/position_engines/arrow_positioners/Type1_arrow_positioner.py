from objects.pictograph.position_engines.arrow_positioners.base_arrow_positioner import (
    BaseArrowPositioner,
)
from constants import (
    RED,
    BLUE,
    PRO,
    ANTI,
    CLOCKWISE,
    COUNTER_CLOCKWISE,
    NORTHEAST,
    SOUTHEAST,
    SOUTHWEST,
    NORTHWEST,
)
from objects.arrow import Arrow
from PyQt6.QtCore import QPointF


class Type1ArrowPositioner(BaseArrowPositioner):
    ### POSITIONING METHODS ###
    def _reposition_E(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_E_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)

    def _reposition_G(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_G_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)

    def _reposition_H(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_H_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)

    def _reposition_I(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_I_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)
            self._apply_shift_adjustment(arrow.ghost, adjustment)

    def _reposition_P(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_P_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)

    def _reposition_Q(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_Q_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)

    def _reposition_R(self) -> None:
        for arrow in self.arrows:
            adjustment = self._calculate_R_adjustment(arrow)
            self._apply_shift_adjustment(arrow, adjustment)

    ### ADJUSTMENT CALCULATIONS ###

    def _calculate_E_adjustment(self, arrow: Arrow) -> QPointF:
        if arrow.turns in [0, 1, 2, 3]:
            adjustments = {
                NORTHEAST: QPointF(35, -35),
                SOUTHEAST: QPointF(35, 35),
                SOUTHWEST: QPointF(-35, 35),
                NORTHWEST: QPointF(-35, -35),
            }
            return adjustments.get(arrow.loc, QPointF(0, 0))

        if arrow.turns == 0.5:
            if arrow.motion.prop_rot_dir == CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-60, 115),
                    SOUTHEAST: QPointF(-115, -60),
                    SOUTHWEST: QPointF(60, -115),
                    NORTHWEST: QPointF(115, 60),
                }
            elif arrow.motion.prop_rot_dir == COUNTER_CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-115, 60),
                    SOUTHEAST: QPointF(-60, -115),
                    SOUTHWEST: QPointF(115, -60),
                    NORTHWEST: QPointF(60, 115),
                }

            return adjustments.get(arrow.loc, QPointF(0, 0))

        elif arrow.turns == 1.5:
            if arrow.motion.prop_rot_dir == CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-60, -10),
                    SOUTHEAST: QPointF(10, -60),
                    SOUTHWEST: QPointF(60, 10),
                    NORTHWEST: QPointF(-10, 60),
                }
            elif arrow.motion.prop_rot_dir == COUNTER_CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(10, 60),
                    SOUTHEAST: QPointF(-60, 10),
                    SOUTHWEST: QPointF(-10, -60),
                    NORTHWEST: QPointF(60, -10),
                }

            return adjustments.get(arrow.loc, QPointF(0, 0))

        elif arrow.turns == 2.5:
            if arrow.motion.prop_rot_dir == CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-55, 80),
                    SOUTHEAST: QPointF(-80, -55),
                    SOUTHWEST: QPointF(55, -80),
                    NORTHWEST: QPointF(80, 55),
                }
            elif arrow.motion.prop_rot_dir == COUNTER_CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-80, 55),
                    SOUTHEAST: QPointF(-55, -80),
                    SOUTHWEST: QPointF(80, -55),
                    NORTHWEST: QPointF(55, 80),
                }

            return adjustments.get(arrow.loc, QPointF(0, 0))

        else:
            return QPointF(0, 0)

    def _calculate_G_adjustment(self, arrow: Arrow) -> QPointF:
        adjustments = {
            0: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(80, -100),
                        SOUTHEAST: QPointF(100, 80),
                        SOUTHWEST: QPointF(-80, 100),
                        NORTHWEST: QPointF(-100, -80),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(100, -80),
                        SOUTHEAST: QPointF(80, 100),
                        SOUTHWEST: QPointF(-100, 80),
                        NORTHWEST: QPointF(-80, -100),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(35, -35),
                        SOUTHEAST: QPointF(35, 35),
                        SOUTHWEST: QPointF(-35, 35),
                        NORTHWEST: QPointF(-35, -35),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(35, -35),
                        SOUTHEAST: QPointF(35, 35),
                        SOUTHWEST: QPointF(-35, 35),
                        NORTHWEST: QPointF(-35, -35),
                    },
                },
            },
            0.5: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(45, 100),
                        SOUTHEAST: QPointF(-100, 45),
                        SOUTHWEST: QPointF(-45, -100),
                        NORTHWEST: QPointF(100, -45),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-100, -45),
                        SOUTHEAST: QPointF(45, -100),
                        SOUTHWEST: QPointF(100, 45),
                        NORTHWEST: QPointF(-45, 100),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(10, 30),
                        SOUTHEAST: QPointF(-30, 10),
                        SOUTHWEST: QPointF(-10, -30),
                        NORTHWEST: QPointF(30, -10),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-30, -10),
                        SOUTHEAST: QPointF(10, -30),
                        SOUTHWEST: QPointF(30, 10),
                        NORTHWEST: QPointF(-10, 30),
                    },
                },
            },
            1: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(40, -25),
                        SOUTHEAST: QPointF(25, 40),
                        SOUTHWEST: QPointF(-40, 25),
                        NORTHWEST: QPointF(-25, -40),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(25, -40),
                        SOUTHEAST: QPointF(40, 25),
                        SOUTHWEST: QPointF(-25, 40),
                        NORTHWEST: QPointF(-40, -25),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-45, -35),
                        SOUTHEAST: QPointF(35, -45),
                        SOUTHWEST: QPointF(45, 35),
                        NORTHWEST: QPointF(-35, 45),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(35, 45),
                        SOUTHEAST: QPointF(-45, 35),
                        SOUTHWEST: QPointF(-35, -45),
                        NORTHWEST: QPointF(45, -35),
                    },
                },
            },
            1.5: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(1, 35),
                        SOUTHEAST: QPointF(-35, -1),
                        SOUTHWEST: QPointF(1, -35),
                        NORTHWEST: QPointF(35, 1),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-35, -1),
                        SOUTHEAST: QPointF(-1, -35),
                        SOUTHWEST: QPointF(35, -1),
                        NORTHWEST: QPointF(1, 35),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-30, -29),
                        SOUTHEAST: QPointF(29, -30),
                        SOUTHWEST: QPointF(30, 29),
                        NORTHWEST: QPointF(-29, 30),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(29, 30),
                        SOUTHEAST: QPointF(-30, 29),
                        SOUTHWEST: QPointF(-29, -30),
                        NORTHWEST: QPointF(30, -29),
                    },
                },
            },
            2: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(95, -105),
                        SOUTHEAST: QPointF(105, 95),
                        SOUTHWEST: QPointF(-95, 105),
                        NORTHWEST: QPointF(-105, -95),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(105, -95),
                        SOUTHEAST: QPointF(95, 105),
                        SOUTHWEST: QPointF(-105, 95),
                        NORTHWEST: QPointF(-95, -105),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(40, -45),
                        SOUTHEAST: QPointF(45, 40),
                        SOUTHWEST: QPointF(-40, 45),
                        NORTHWEST: QPointF(-45, -40),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(45, -40),
                        SOUTHEAST: QPointF(40, 45),
                        SOUTHWEST: QPointF(-45, 40),
                        NORTHWEST: QPointF(-40, -45),
                    },
                },
            },
            2.5: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(5, -35),
                        SOUTHEAST: QPointF(35, 5),
                        SOUTHWEST: QPointF(-5, 35),
                        NORTHWEST: QPointF(-35, -5),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(35, -5),
                        SOUTHEAST: QPointF(5, 35),
                        SOUTHWEST: QPointF(-35, 5),
                        NORTHWEST: QPointF(-5, -35),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(30, 65),
                        SOUTHEAST: QPointF(-65, 30),
                        SOUTHWEST: QPointF(-30, -65),
                        NORTHWEST: QPointF(65, -30),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-65, -30),
                        SOUTHEAST: QPointF(30, -65),
                        SOUTHWEST: QPointF(65, 30),
                        NORTHWEST: QPointF(-30, 65),
                    },
                },
            },
            3: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(30, -25),
                        SOUTHEAST: QPointF(25, 30),
                        SOUTHWEST: QPointF(-30, 25),
                        NORTHWEST: QPointF(-25, -30),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(25, -30),
                        SOUTHEAST: QPointF(30, 25),
                        SOUTHWEST: QPointF(-25, 30),
                        NORTHWEST: QPointF(-30, -25),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-45, -35),
                        SOUTHEAST: QPointF(35, -45),
                        SOUTHWEST: QPointF(45, 35),
                        NORTHWEST: QPointF(-35, 45),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(35, 45),
                        SOUTHEAST: QPointF(-45, 35),
                        SOUTHWEST: QPointF(-35, -45),
                        NORTHWEST: QPointF(45, -35),
                    },
                },
            },
        }
        turn_adjustments = adjustments.get(arrow.turns, {})
        color_adjustments = turn_adjustments.get(arrow.color, {})
        direction_adjustments = color_adjustments.get(arrow.motion.prop_rot_dir, {})
        return direction_adjustments.get(arrow.loc, QPointF(0, 0))

    def _calculate_H_adjustment(self, arrow: Arrow) -> QPointF:
        adjustments = {
            0: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(120, -95),
                        SOUTHEAST: QPointF(95, 120),
                        SOUTHWEST: QPointF(-120, 95),
                        NORTHWEST: QPointF(-95, -120),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(95, -120),
                        SOUTHEAST: QPointF(120, 95),
                        SOUTHWEST: QPointF(-95, 120),
                        NORTHWEST: QPointF(-120, -95),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(55, -55),
                        SOUTHEAST: QPointF(55, 55),
                        SOUTHWEST: QPointF(-55, 55),
                        NORTHWEST: QPointF(-55, -55),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(55, -55),
                        SOUTHEAST: QPointF(55, 55),
                        SOUTHWEST: QPointF(-55, 55),
                        NORTHWEST: QPointF(-55, -55),
                    },
                },
            },
            0.5: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-45, 115),
                        SOUTHEAST: QPointF(-115, -45),
                        SOUTHWEST: QPointF(45, -115),
                        NORTHWEST: QPointF(115, 45),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-115, 45),
                        SOUTHEAST: QPointF(-45, -115),
                        SOUTHWEST: QPointF(115, -45),
                        NORTHWEST: QPointF(45, 115),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-90, 155),
                        SOUTHEAST: QPointF(-155, -90),
                        SOUTHWEST: QPointF(90, -155),
                        NORTHWEST: QPointF(155, 90),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-155, 90),
                        SOUTHEAST: QPointF(-90, -155),
                        SOUTHWEST: QPointF(155, -90),
                        NORTHWEST: QPointF(90, 155),
                    },
                },
            },
            1: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(120, -95),
                        SOUTHEAST: QPointF(95, 120),
                        SOUTHWEST: QPointF(-120, 95),
                        NORTHWEST: QPointF(-95, -120),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(95, -120),
                        SOUTHEAST: QPointF(120, 95),
                        SOUTHWEST: QPointF(-95, 120),
                        NORTHWEST: QPointF(-120, -95),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(55, -55),
                        SOUTHEAST: QPointF(55, 55),
                        SOUTHWEST: QPointF(-55, 55),
                        NORTHWEST: QPointF(-55, -55),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(55, -55),
                        SOUTHEAST: QPointF(55, 55),
                        SOUTHWEST: QPointF(-55, 55),
                        NORTHWEST: QPointF(-55, -55),
                    },
                },
            },
            1.5: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(1, 35),
                        SOUTHEAST: QPointF(-35, -1),
                        SOUTHWEST: QPointF(1, -35),
                        NORTHWEST: QPointF(35, 1),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-35, -1),
                        SOUTHEAST: QPointF(-1, -35),
                        SOUTHWEST: QPointF(35, -1),
                        NORTHWEST: QPointF(1, 35),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-30, -29),
                        SOUTHEAST: QPointF(29, -30),
                        SOUTHWEST: QPointF(30, 29),
                        NORTHWEST: QPointF(-29, 30),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(29, 30),
                        SOUTHEAST: QPointF(-30, 29),
                        SOUTHWEST: QPointF(-29, -30),
                        NORTHWEST: QPointF(30, -29),
                    },
                },
            },
            2: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(95, -105),
                        SOUTHEAST: QPointF(105, 95),
                        SOUTHWEST: QPointF(-95, 105),
                        NORTHWEST: QPointF(-105, -95),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(105, -95),
                        SOUTHEAST: QPointF(95, 105),
                        SOUTHWEST: QPointF(-105, 95),
                        NORTHWEST: QPointF(-95, -105),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(40, 45),
                        SOUTHEAST: QPointF(-45, 40),
                        SOUTHWEST: QPointF(-40, -45),
                        NORTHWEST: QPointF(45, -40),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(-45, -40),
                        SOUTHEAST: QPointF(40, -45),
                        SOUTHWEST: QPointF(45, 40),
                        NORTHWEST: QPointF(-40, 45),
                    },
                },
            },
            2.5: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(10, -30),
                        SOUTHEAST: QPointF(30, 10),
                        SOUTHWEST: QPointF(-10, 30),
                        NORTHWEST: QPointF(-30, -10),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(30, -10),
                        SOUTHEAST: QPointF(10, 30),
                        SOUTHWEST: QPointF(-30, 10),
                        NORTHWEST: QPointF(-10, -30),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-45, -35),
                        SOUTHEAST: QPointF(35, -45),
                        SOUTHWEST: QPointF(45, 35),
                        NORTHWEST: QPointF(-35, 45),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(35, 45),
                        SOUTHEAST: QPointF(-45, 35),
                        SOUTHWEST: QPointF(-35, -45),
                        NORTHWEST: QPointF(45, -35),
                    },
                },
            },
            3: {
                RED: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(30, -25),
                        SOUTHEAST: QPointF(25, 30),
                        SOUTHWEST: QPointF(-30, 25),
                        NORTHWEST: QPointF(-25, -30),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(25, -30),
                        SOUTHEAST: QPointF(30, 25),
                        SOUTHWEST: QPointF(-25, 30),
                        NORTHWEST: QPointF(-30, -25),
                    },
                },
                BLUE: {
                    CLOCKWISE: {
                        NORTHEAST: QPointF(-45, -35),
                        SOUTHEAST: QPointF(35, -45),
                        SOUTHWEST: QPointF(45, 35),
                        NORTHWEST: QPointF(-35, 45),
                    },
                    COUNTER_CLOCKWISE: {
                        NORTHEAST: QPointF(35, 45),
                        SOUTHEAST: QPointF(-45, 35),
                        SOUTHWEST: QPointF(-35, -45),
                        NORTHWEST: QPointF(45, -35),
                    },
                },
            },
        }
        turn_adjustments = adjustments.get(arrow.turns, {})
        color_adjustments = turn_adjustments.get(arrow.color, {})
        direction_adjustments = color_adjustments.get(arrow.motion.prop_rot_dir, {})
        return direction_adjustments.get(arrow.loc, QPointF(0, 0))

    def _calculate_I_adjustment(self, arrow: Arrow) -> QPointF:
        anti_adjustments = {
            NORTHEAST: QPointF(55, -55),
            SOUTHEAST: QPointF(55, 55),
            SOUTHWEST: QPointF(-55, 55),
            NORTHWEST: QPointF(-55, -55),
        }

        pro_cw_adjustments = {
            NORTHEAST: QPointF(90, -110),
            SOUTHEAST: QPointF(110, 90),
            SOUTHWEST: QPointF(-90, 110),
            NORTHWEST: QPointF(-110, -90),
        }

        pro_ccw_adjustments = {
            NORTHEAST: QPointF(110, -90),
            SOUTHEAST: QPointF(90, 110),
            SOUTHWEST: QPointF(-110, 90),
            NORTHWEST: QPointF(-90, -110),
        }

        adjustments = {
            PRO: {
                CLOCKWISE: pro_cw_adjustments,
                COUNTER_CLOCKWISE: pro_ccw_adjustments,
            },
            ANTI: {
                CLOCKWISE: anti_adjustments,
                COUNTER_CLOCKWISE: anti_adjustments,
            },
        }

        motion_type_adjustments = adjustments.get(arrow.motion_type, {})
        rotation_adjustments = motion_type_adjustments.get(
            arrow.motion.prop_rot_dir, {}
        )
        return rotation_adjustments.get(arrow.loc, QPointF(0, 0))

    def _calculate_P_adjustment(self, arrow: Arrow) -> QPointF:
        blue_adjustments = {
            NORTHEAST: QPointF(35, -35),
            SOUTHEAST: QPointF(35, 35),
            SOUTHWEST: QPointF(-35, 35),
            NORTHWEST: QPointF(-35, -35),
        }

        red_ccw_adjustments = {
            NORTHEAST: QPointF(70, -110),
            SOUTHEAST: QPointF(110, 70),
            SOUTHWEST: QPointF(-70, 110),
            NORTHWEST: QPointF(-110, -70),
        }

        red_cw_adjustments = {
            NORTHEAST: QPointF(110, -70),
            SOUTHEAST: QPointF(70, 110),
            SOUTHWEST: QPointF(-110, 70),
            NORTHWEST: QPointF(-70, -110),
        }

        adjustments = {
            RED: {
                CLOCKWISE: red_cw_adjustments,
                COUNTER_CLOCKWISE: red_ccw_adjustments,
            },
            BLUE: {
                CLOCKWISE: blue_adjustments,
                COUNTER_CLOCKWISE: blue_adjustments,
            },
        }

        color_adjustments = adjustments.get(arrow.color, {})
        rotation_adjustments = color_adjustments.get(arrow.motion.prop_rot_dir, {})
        return rotation_adjustments.get(arrow.loc, QPointF(0, 0))

    def _calculate_Q_adjustment(self, arrow: Arrow) -> QPointF:
        if arrow.turns in [0, 1, 2, 3]:
            blue_adjustments = {
                NORTHEAST: QPointF(35, -35),
                SOUTHEAST: QPointF(35, 35),
                SOUTHWEST: QPointF(-35, 35),
                NORTHWEST: QPointF(-35, -35),
            }

            red_cw_adjustments = {
                NORTHEAST: QPointF(70, -110),
                SOUTHEAST: QPointF(110, 70),
                SOUTHWEST: QPointF(-70, 110),
                NORTHWEST: QPointF(-110, -70),
            }

            red_ccw_adjustments = {
                NORTHEAST: QPointF(110, -70),
                SOUTHEAST: QPointF(70, 110),
                SOUTHWEST: QPointF(-110, 70),
                NORTHWEST: QPointF(-70, -110),
            }

            adjustments = {
                RED: {
                    CLOCKWISE: red_cw_adjustments,
                    COUNTER_CLOCKWISE: red_ccw_adjustments,
                },
                BLUE: {
                    CLOCKWISE: blue_adjustments,
                    COUNTER_CLOCKWISE: blue_adjustments,
                },
            }

            color_adjustments = adjustments.get(arrow.color, {})
            rotation_adjustments = color_adjustments.get(arrow.motion.prop_rot_dir, {})
            return rotation_adjustments.get(arrow.loc, QPointF(0, 0))

        elif arrow.turns == 0.5:
            if arrow.motion.prop_rot_dir == CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-60, 95),
                    SOUTHEAST: QPointF(-95, -60),
                    SOUTHWEST: QPointF(60, -95),
                    NORTHWEST: QPointF(95, 60),
                }
            elif arrow.motion.prop_rot_dir == COUNTER_CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-95, 60),
                    SOUTHEAST: QPointF(-60, -95),
                    SOUTHWEST: QPointF(95, -60),
                    NORTHWEST: QPointF(60, 95),
                }

            return adjustments.get(arrow.loc, QPointF(0, 0))

        elif arrow.turns == 1.5:
            return QPointF(0, 0)

        elif arrow.turns == 2.5:
            if arrow.motion.prop_rot_dir == CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-95, 94),
                    SOUTHEAST: QPointF(-94, -95),
                    SOUTHWEST: QPointF(95, -94),
                    NORTHWEST: QPointF(94, 95),
                }
            elif arrow.motion.prop_rot_dir == COUNTER_CLOCKWISE:
                adjustments = {
                    NORTHEAST: QPointF(-94, 95),
                    SOUTHEAST: QPointF(-95, -94),
                    SOUTHWEST: QPointF(94, -95),
                    NORTHWEST: QPointF(95, 94),
                }

            return adjustments.get(arrow.loc, QPointF(0, 0))

        else:
            return QPointF(0, 0)

    def _calculate_R_adjustment(self, arrow: Arrow) -> QPointF:
        pro_cw_adjustments = {
            NORTHEAST: QPointF(75, -60),
            SOUTHEAST: QPointF(60, 75),
            SOUTHWEST: QPointF(-75, 60),
            NORTHWEST: QPointF(-60, -75),
        }
        pro_ccw_adjustments = {
            NORTHEAST: QPointF(60, -75),
            SOUTHEAST: QPointF(75, 60),
            SOUTHWEST: QPointF(-60, 75),
            NORTHWEST: QPointF(-75, -60),
        }

        anti_cw_adjustments = {
            NORTHEAST: QPointF(30, -30),
            SOUTHEAST: QPointF(30, 30),
            SOUTHWEST: QPointF(-30, 30),
            NORTHWEST: QPointF(-30, -30),
        }
        anti_ccw_adjustments = {
            NORTHEAST: QPointF(35, -25),
            SOUTHEAST: QPointF(25, 35),
            SOUTHWEST: QPointF(-35, 25),
            NORTHWEST: QPointF(-25, -35),
        }

        adjustments = {
            PRO: {
                CLOCKWISE: pro_cw_adjustments,
                COUNTER_CLOCKWISE: pro_ccw_adjustments,
            },
            ANTI: {
                CLOCKWISE: anti_cw_adjustments,
                COUNTER_CLOCKWISE: anti_ccw_adjustments,
            },
        }

        motion_type_adjustments = adjustments.get(arrow.motion_type, {})
        rotation_adjustments = motion_type_adjustments.get(
            arrow.motion.prop_rot_dir, {}
        )
        return rotation_adjustments.get(arrow.loc, QPointF(0, 0))
