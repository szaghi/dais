"""Split designs: a top case and a bottom case parted on a plane parallel to the top.

The bottom case is shrunk in plan by SPLIT_STEP and its lip slides into a rebate inside the
top case; the shadow step under the top case's convex rounded rim is the only feature of the
sides. The same code builds the rectangular and the trapezoidal plan (``Layout.front_width``).
"""

from __future__ import annotations

import math

from build123d import Axis, Box, Cylinder, Part, Pos, chamfer, fillet

from .layout import Layout, above_floor, below_roof, between, half_space, seam_z
from .params import (
    BOSS_R,
    BOTTOM_EDGE,
    BOTTOM_T,
    LIP_FIT,
    LIP_T,
    LIP_TOP_GAP,
    MIN,
    REBATE_H,
    RIM_R,
    RIM_WALL,
    SCREW_CLEAR,
    SCREW_HEAD_D,
    SCREW_HEAD_H,
    SCREW_PILOT,
    SPLIT_BOSS_INSET,
    SPLIT_SCREW_ENGAGE,
    SPLIT_SCREW_L,
    SPLIT_STEP,
    TILT,
    TOP_BOSS_R,
    WALL,
)
from .parts import make_bottom
from .shell import key_well_and_pilots, outer_shell, outline, plan_pts, side_x, usb_cuts


def split_bosses(lay: Layout) -> tuple[tuple[float, float], ...]:
    """Screw axes: WALL + SPLIT_BOSS_INSET from both walls of each corner (follows a trapezoid)."""
    pts = plan_pts(lay, WALL + SPLIT_BOSS_INSET)
    return tuple((sx * abs(x), y) for sx in (-1, 1) for x, y in (pts[0], pts[3]))


def _wall_web(lay: Layout, x: float, y: float) -> Part:
    """Block from a screw axis into its corner, overlapping both walls (tall: clip it)."""
    sx, sy = math.copysign(1, x), math.copysign(1, y)
    y_wall = sy * (lay.depth / 2 - WALL + 0.5)
    x_wall = sx * (max(side_x(lay, y, WALL), side_x(lay, y_wall, WALL)) + 0.5)
    web = Pos((x + x_wall) / 2, (y + y_wall) / 2, -1) * Box(abs(x_wall - x), abs(y_wall - y), lay.big, align=MIN)
    return web & outline(lay, 1.0)


def make_top_case(lay: Layout) -> Part:
    """Upper shell: convex rounded lower rim, inner rebate, screw columns up to the roof."""
    t = math.radians(TILT)
    top = outer_shell(lay) & half_space(lay, 0.0, above=True)
    seam_face = top.faces().sort_by(Axis((0, 0, 0), (0, -math.sin(t), math.cos(t))))[0]
    top = fillet(seam_face.edges(), radius=RIM_R)

    top -= outline(lay, WALL) & below_roof(lay)
    top -= outline(lay, RIM_WALL) & between(lay, -1.0, REBATE_H)
    top -= key_well_and_pilots(lay)

    # columns from the rebate top up to the roof: printed top down, nothing starts in mid-air
    slab = half_space(lay, REBATE_H, above=True) & below_roof(lay, lift=0.5)
    for x, y in split_bosses(lay):
        column = Pos(x, y, -1) * Cylinder(TOP_BOSS_R, lay.big, align=MIN) + _wall_web(lay, x, y)
        top += column & slab
        top -= (Pos(x, y, -1) * Cylinder(SCREW_PILOT / 2, lay.big, align=MIN)) & half_space(
            lay, REBATE_H + SPLIT_SCREW_ENGAGE - 0.4, above=False
        )  # blind: the tip stops 0.4 short
    return top - usb_cuts(lay)


def make_bottom_case(lay: Layout) -> Part:
    """Lower shell: shrunk by SPLIT_STEP, lip up into the top case rebate, floor, screw columns."""
    lip_out = RIM_WALL + LIP_FIT
    lip_in = lip_out + LIP_T
    lip_top = REBATE_H - LIP_TOP_GAP

    case = outline(lay, SPLIT_STEP) & half_space(lay, 0.0, above=False)
    case = chamfer(case.faces().sort_by(Axis.Z)[0].edges(), length=BOTTOM_EDGE)
    case += (outline(lay, lip_out) - outline(lay, lip_in)) & between(lay, -1.0, lip_top)
    case -= outline(lay, lip_in) & above_floor(lay)
    # floor: same board seat and feet recesses as the one-piece bottom plate
    case -= Pos(0, 0, -1) * Box(lay.in_x + 0.2, lay.in_y + 0.2, BOTTOM_T + 1, align=MIN)
    case += make_bottom(lay, fused=True)

    for x, y in split_bosses(lay):
        # trimmed 0.01 inside the lip faces: coincident faces make the OCC union invalid
        case += (Pos(x, y, 0) * Cylinder(BOSS_R, lay.big, align=MIN) & outline(lay, lip_out + 0.01)) & (
            half_space(lay, lip_top - 0.01, above=False)
        )
        case -= Pos(x, y, -1) * Cylinder(SCREW_CLEAR / 2, lay.big, align=MIN)
        # head bearing height: the tip stops 0.8 below the column top (its blind pilot ends 0.4 below)
        seat = seam_z(lay, y) + REBATE_H + SPLIT_SCREW_ENGAGE - 0.8 - SPLIT_SCREW_L
        if seat < SCREW_HEAD_H:
            raise ValueError(f"SPLIT_SCREW_L too long: head would stand {SCREW_HEAD_H - seat:.2f} mm below the floor")
        case -= Pos(x, y, -1) * Cylinder(SCREW_HEAD_D / 2, seat + 1, align=MIN)

    return case - usb_cuts(lay)
