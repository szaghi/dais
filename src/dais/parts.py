"""Parts shared between designs: switch plate, bottom plate / floor, feet, switch-fit coupon."""

from __future__ import annotations

from build123d import Axis, Box, Cylinder, Part, Pos, Text, extrude, fillet

from .layout import Layout
from .params import (
    BOARD_FIT,
    BOTTOM_FIT,
    BOTTOM_T,
    FOOT_INSET,
    FOOT_RECESS,
    FOOT_T,
    FOOT_W,
    JOINT_GROOVE_D,
    JOINT_GROOVE_W,
    MAX,
    MIN,
    PLATE,
    PLATE_RELIEF,
    PLATE_SCREW,
    PLATE_SCREW_CLEAR,
    PLATE_T,
    POCKET_D,
    STOP_T,
    SW_CUT,
)


def make_plate(lay: Layout) -> Part:
    """Switch plate in the key frame; printed flat it is as true as the coupon."""
    plate = Box(PLATE, PLATE, PLATE_T, align=MAX)
    # corner reliefs around the one-piece body bosses, which run up past the plate to the roof; cut
    # before the corner fillets (cutting a filleted corner, OCC silently dropped one of the four cuts)
    for x, y in lay.bosses:
        plate -= lay.key.inverse() * Pos(x, y, 0) * Cylinder(lay.opt.fast.boss_r + PLATE_RELIEF, lay.big)
    corners = plate.edges().filter_by(Axis.Z)
    if corners:
        plate = fillet(corners, radius=1.0)
    plate -= Box(SW_CUT, SW_CUT, 3 * PLATE_T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            plate -= Pos(sx * PLATE_SCREW, sy * PLATE_SCREW, 0) * Cylinder(PLATE_SCREW_CLEAR / 2, 3 * PLATE_T)
    return lay.key * plate


def make_bottom(lay: Layout, fused: bool = False) -> Part:
    """Bottom plate, flush in the body opening: board seat, screws, feet recesses.

    ``fused``: floor of a split bottom case -- overlaps the walls, no screw holes (the case adds its own).
    """
    b = lay.board
    grow = 0.1 if fused else -BOTTOM_FIT
    bottom = Box(lay.in_x + 2 * grow, lay.in_y + 2 * grow, BOTTOM_T, align=MIN)

    back = lay.board_back
    pocket_l = b.length + BOARD_FIT
    bottom -= Pos(0, back - pocket_l / 2 + 0.5, BOTTOM_T - POCKET_D) * Box(
        b.width + BOARD_FIT, pocket_l + 1, POCKET_D + 1, align=MIN
    )
    if b.pin_row_x is not None:
        for sx in (-1, 1):
            bottom -= Pos(sx * b.pin_row_x, back - pocket_l / 2 + 0.5, BOTTOM_T - POCKET_D - JOINT_GROOVE_D) * Box(
                JOINT_GROOVE_W, pocket_l + 1, JOINT_GROOVE_D + 0.01, align=MIN
            )
    # front stop: a wall up to the board top, so the plug pushes into the bottom plate
    bottom += Pos(0, back - pocket_l - STOP_T / 2, BOTTOM_T) * Box(
        b.width + BOARD_FIT + 1.6, STOP_T, b.pcb_t - POCKET_D, align=MIN
    )

    for x, y in () if fused else lay.bosses:
        bottom -= Pos(x, y, -1) * Cylinder(lay.opt.fast.clear_d / 2, BOTTOM_T + 2, align=MIN)
        bottom -= Pos(x, y, 0) * Cylinder(lay.opt.fast.head_d / 2, lay.opt.fast.head_h, align=MIN)
    for y in feet_y(lay):
        bottom -= Pos(0, y, 0) * Box(foot_len(lay) + 0.4, FOOT_W + 0.4, FOOT_RECESS, align=MIN)
    return bottom


def feet_y(lay: Layout) -> tuple[float, float]:
    """Centre lines of the two feet strips."""
    y = lay.in_y / 2 - BOTTOM_FIT - FOOT_INSET
    return (-y, y)


def foot_len(lay: Layout) -> float:
    """Strip length: clear of the corner screw heads."""
    return 2 * (lay.bosses[-1][0] - lay.opt.fast.head_d / 2 - 1.5)


def make_feet(lay: Layout) -> Part:
    """Two TPU strips, in their installed position."""
    feet = Part()
    for y in feet_y(lay):
        strip = Box(foot_len(lay), FOOT_W, FOOT_T, align=MIN)
        strip = fillet(strip.edges().filter_by(Axis.Z), radius=FOOT_W / 2 - 0.01)
        feet += Pos(0, y, FOOT_RECESS - FOOT_T) * strip
    return feet


def make_coupon(cuts: tuple[float, ...] = (13.9, 14.0, 14.1, 14.2)) -> Part:
    """Row of 1.5 mm test plates, each with its cutout size engraved."""
    pitch = 21.0
    coupon = Part()
    for i, cut in enumerate(cuts):
        tile = Pos(i * pitch, 0, 0) * Box(20, 26, PLATE_T, align=MIN)
        tile -= Pos(i * pitch, 3, -1) * Box(cut, cut, PLATE_T + 2, align=MIN)
        label = Pos(i * pitch, -9.5, PLATE_T) * Text(f"{cut:.1f}", font_size=4)
        tile -= extrude(label, amount=-0.4)
        coupon += tile
    return coupon
