"""Dimensions derived from the board choice, and the reference frames every part is built in.

Coordinates: z = 0 is the case bottom, -Y the front (low side), +Y the back (USB-C side).
The key frame (``Layout.key``) has its origin at the plate-top centre, tilted by ``TILT``
about X; the split designs add a parting frame (``parting``) on the seam plane.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from build123d import Box, Location, Part, Pos, Rot

from .params import (
    BEZEL,
    BOARD_FIT,
    BOTTOM_T,
    COMP_H,
    MAX,
    MIN,
    PLATE,
    POCKET_D,
    SPLIT_FRONT_Z,
    STOP_T,
    SW_BELOW,
    SW_HALF,
    SW_PIN_Y,
    SW_PINS,
    TILT,
    USB_WALL_LEFT,
    WALL,
    WELL,
    WELL_DEPTH,
    WIRE_GAP,
    Board,
    Options,
)


@dataclass(frozen=True)
class Layout:
    """Dimensions derived from the board choice."""

    board: Board
    width: float  # body X at the back
    front_width: float  # body X at the front (> width: trapezoidal plan)
    depth: float  # body Y
    in_x: float
    in_y: float
    key_z: float  # plate top centre height (key frame origin)
    h_front: float
    h_back: float
    usb_z: float
    board_back: float  # Y of the PCB back edge
    bosses: tuple[tuple[float, float], ...]  # one-piece body bosses
    opt: Options  # construction choices: plate, fastener, bevel, pattern

    @classmethod
    def for_board(cls, board: Board, front_extra: float = 0.0, opt: Options | None = None) -> Layout:
        """Size the case around ``board``; ``front_extra`` > 0 widens the front (trapezoidal plan)."""
        opt = opt or Options()
        t = math.radians(TILT)
        width = WELL + 2 * BEZEL
        setback = max(0.0, board.usb_overhang - USB_WALL_LEFT)
        in_y = board.length + BOARD_FIT + STOP_T + 1.0 + setback
        depth = max(width, in_y + 2 * WALL)
        in_y = depth - 2 * WALL
        in_x = width - 2 * WALL
        board_top = BOTTOM_T - POCKET_D + board.pcb_t
        # lowest switch point below the plate-top centre (tilted housing corner / pin tips)
        drop = max(
            SW_BELOW * math.cos(t) + SW_HALF * math.sin(t), (SW_BELOW + SW_PINS) * math.cos(t) + SW_PIN_Y * math.sin(t)
        )
        key_z = board_top + COMP_H + WIRE_GAP + drop
        top_c = key_z + WELL_DEPTH / math.cos(t)  # top face height above the key centre
        bx, by = in_x / 2 - opt.fast.boss_inset, in_y / 2 - opt.fast.boss_inset
        lay = cls(
            board=board,
            width=width,
            front_width=width + front_extra,
            depth=depth,
            in_x=in_x,
            in_y=in_y,
            key_z=key_z,
            h_front=top_c - depth / 2 * math.tan(t),
            h_back=top_c + depth / 2 * math.tan(t),
            usb_z=board_top + board.usb_h / 2,
            board_back=in_y / 2 - setback,
            bosses=tuple((sx * bx, sy * by) for sx in (-1, 1) for sy in (-1, 1)),
            opt=opt,
        )
        if (board.width + BOARD_FIT) / 2 + 1.0 > bx - opt.fast.boss_r:
            raise ValueError("board too wide for the bosses: increase BEZEL")
        if PLATE / 2 * math.cos(t) > in_y / 2 or PLATE / 2 > in_x / 2:
            raise ValueError("plate does not fit the cavity")
        return lay

    @property
    def key(self) -> Location:
        """Key frame: plate top centre, tilted by TILT about X (rises to the back)."""
        return Pos(0, 0, self.key_z) * Rot(TILT, 0, 0)

    @property
    def big(self) -> float:
        """Size of the oversized cutters and slabs that get clipped by intersection."""
        return 4 * self.depth


def below_roof(lay: Layout, lift: float = 0.0) -> Part:
    """Half-space under the cavity roof (plate-top plane), raised ``lift`` along the key normal.

    ``lift`` > 0 reaches into the top skin, so columns clipped by it fuse with the skin.
    """
    return lay.key * Pos(0, 0, lift) * Box(2 * lay.big, 2 * lay.big, 2 * lay.big, align=MAX)


def above_floor(lay: Layout) -> Part:
    """Half-space above the bottom plate / floor top."""
    return Pos(0, 0, BOTTOM_T) * Box(lay.big, lay.big, lay.big, align=MIN)


def parting(lay: Layout, offset: float = 0.0) -> Location:
    """Parting plane frame: SPLIT_FRONT_Z up the front face, parallel to the top, raised by ``offset``."""
    return Pos(0, -lay.depth / 2, SPLIT_FRONT_Z) * Rot(TILT, 0, 0) * Pos(0, 0, offset)


def half_space(lay: Layout, offset: float, above: bool) -> Part:
    """Half-space above or below the parting plane raised by ``offset``."""
    big = 2 * lay.big
    return parting(lay, offset) * Box(big, big, big, align=MIN if above else MAX)


def between(lay: Layout, lo: float, hi: float) -> Part:
    """Slab between two planes parallel to the parting plane."""
    return half_space(lay, lo, above=True) & half_space(lay, hi, above=False)


def seam_z(lay: Layout, y: float) -> float:
    """World height of the parting plane at plan position ``y``."""
    return SPLIT_FRONT_Z + (y + lay.depth / 2) * math.tan(math.radians(TILT))
