"""Generic controller seat of the split designs: rear jaws, front clamp, floor slot, USB-C window.

Any Pro Micro-style board with a top-mount USB-C within the SEAT_* ranges lies in the floor
pocket. Its two back corners wedge into the rear jaws; the front clamp, slid along a floor slot
and locked by one M3 screw from below, pushes its front corners back. Jaw and clamp faces are
angled JAW_PLAN in plan, so the corners slide to the centre line whatever the board's width, and
lean JAW_LEAN over the PCB, so they press its top edge down whatever its thickness. The board's
back edge, and so its USB-C, therefore sit at a position that depends only on the board, and the
USB-C window is plug-sized through the whole back wall: the bottom case forms its lower part,
the top case closes it.

Coordinates: world, as in ``layout``. ``y_r`` is the rear jaws' reference line, ``y_c`` the
clamp's: the plan-V faces pass through ``(+-X_V, y, Z_REF)``.
"""

from __future__ import annotations

import math

from build123d import Align, Box, Cylinder, Location, Part, Plane, Pos

from .params import (
    BOTTOM_T,
    CLAMP_H,
    CLAMP_LEN,
    CLAMP_STEM,
    FASTENERS,
    JAW_CAP,
    JAW_H,
    JAW_LEAN,
    JAW_PLAN,
    JAW_SET,
    MIN,
    PLUG_H,
    PLUG_W,
    POCKET_D,
    SEAT_LEN,
    SEAT_PCB_T,
    SEAT_USB_H,
    SEAT_W,
    SLOT_CBORE,
    USB_WINDOW_PLAY,
    Board,
)

BIG = 400.0
BACK = (Align.CENTER, Align.MIN, Align.MIN)  # box grows to +Y from its origin
FRONT = (Align.CENTER, Align.MAX, Align.MIN)  # box grows to -Y from its origin
S_PLAN = math.tan(math.radians(JAW_PLAN))  # y shift per mm of corner x along a plan-V face
C_LEAN = 1.0 / math.tan(math.radians(JAW_LEAN))  # y shift per mm of height along a leaning face
X_V = SEAT_W[0] / 2  # the V faces start at the narrowest board's corner
X_OUT = SEAT_W[1] / 2 + 0.5  # jaws and clamp horns end just beyond the widest board's corner
Z0 = BOTTOM_T - POCKET_D  # pocket floor: the PCB's underside
Z_REF = Z0 + sum(SEAT_PCB_T) / 2  # mid PCB top
Z_CAP = Z_REF + JAW_CAP  # above this the faces stand vertical
CLAMP_SCREW = 4.0  # insert axis in front of the clamp's reference line
INSERT_L = 5.7  # M3 heat-set insert length
POCKET_HALF = X_OUT + 0.2  # floor pocket half-width: the clamp horns slide in it


def _dw(width: float) -> float:
    """y offset of a board corner on a plan-V face, from the reference line."""
    return (width / 2 - X_V) * S_PLAN


def _dt(pcb_t: float) -> float:
    """y offset of the PCB top edge on a leaning face, from the reference line."""
    return C_LEAN * (Z0 + pcb_t - Z_REF)


def span(longest: bool = True) -> float:
    """``y_r - y_c`` for the longest (default) or the shortest board of the ranges."""
    if longest:
        return SEAT_LEN[1] + 2 * _dw(SEAT_W[1]) + 2 * _dt(SEAT_PCB_T[1])
    return SEAT_LEN[0] + 2 * _dw(SEAT_W[0]) + 2 * _dt(SEAT_PCB_T[0])


def jaw_y(depth: float) -> float:
    """Rear jaws' reference line."""
    return depth / 2 - JAW_SET


def board_back(depth: float, board: Board) -> float:
    """y of ``board``'s back edge, its corners wedged in the rear jaws."""
    return jaw_y(depth) - _dw(board.width) - _dt(board.pcb_t)


def clamp_y(depth: float, board: Board) -> float:
    """The clamp's reference line when it holds ``board``."""
    return jaw_y(depth) - board.length - 2 * _dw(board.width) - 2 * _dt(board.pcb_t)


def check_board(board: Board) -> None:
    """Raise ValueError if ``board`` is outside the seat's ranges."""
    for name, value, (lo, hi) in (
        ("length", board.length, SEAT_LEN),
        ("width", board.width, SEAT_W),
        ("PCB thickness", board.pcb_t, SEAT_PCB_T),
        ("USB-C height", board.usb_h, SEAT_USB_H),
    ):
        if not lo <= value <= hi:
            raise ValueError(f"board {name} {value} outside the split seat's range {lo}-{hi}")


def _half(origin: tuple[float, float, float], normal: tuple[float, float, float]) -> Part:
    """Half-space of the points p with normal . (p - origin) >= 0."""
    return Location(Plane(origin=origin, z_dir=normal)) * Box(BIG, BIG, BIG, align=MIN)


def _leaning(y: float, sx: int, toward: int) -> Part:
    """Material of a rear jaw (``toward`` = +1: behind the face) or a clamp horn (-1: in front of
    it): the plan-V face through ``(sx * X_V, y, Z_REF)``, leaning up to Z_CAP, vertical above."""
    low = _half((sx * X_V, y, Z_REF), (S_PLAN * sx, toward, C_LEAN))
    y_cap = y - toward * C_LEAN * (Z_CAP - Z_REF)
    high = _half((sx * X_V, y_cap, Z_CAP), (S_PLAN * sx, toward, 0.0))
    below = _half((0, 0, Z_CAP), (0, 0, -1))
    return (low & below) + (high - below)


def rear_jaws(depth: float) -> tuple[Part, Part]:
    """(material, carve) of the two rear jaws: add the first, then cut the second -- where the
    PCB corners go, also into the back wall. Between the USB-C window and X_OUT."""
    y_r = jaw_y(depth)
    x0 = window_half_width() - 0.1  # from the window: no strip of wall left for a narrow board to hit
    add, cut = Part(), Part()
    for sx in (-1, 1):
        block = Pos(sx * (x0 + X_OUT) / 2, y_r + 0.5, Z0) * Box(X_OUT - x0, 3.5, JAW_H, align=FRONT)
        material = _leaning(y_r, sx, +1)
        add += block & material
        cut += block - material
    return add, cut


def make_clamp(depth: float, board: Board) -> Part:
    """The front clamp in its position on ``board``: a crossbar whose two leaning plan-V horns push
    the PCB's front corners back, down and to the centre, and an M3 heat-set insert column; the
    M3x6 comes up from below through the floor slot. Print it upside down."""
    y_c = clamp_y(depth, board)
    bar = Pos(0, y_c - 3.0, Z0 + 0.02) * Box(2 * X_OUT, 5.5, CLAMP_H, align=BACK)
    horns = _leaning(y_c, 1, -1) + _leaning(y_c, -1, -1) + _half((0, y_c - 0.5, 0), (0, -1, 0))
    stem = Pos(0, y_c - CLAMP_LEN, Z0 + 0.02) * Box(CLAMP_STEM, CLAMP_LEN - 0.5, CLAMP_H, align=BACK)
    hole = Pos(0, y_c - CLAMP_SCREW, Z0) * Cylinder(FASTENERS["insert"].hole_d / 2, INSERT_L + 0.3, align=MIN)
    return ((bar & horns) + stem) - hole


def floor_slot(depth: float) -> Part:
    """Cutter: the clamp screw's slot through the floor over the whole clamp travel, and the
    counterbore for the M3 button head from below."""
    y_r = jaw_y(depth)
    y0, y1 = y_r - span() - CLAMP_SCREW, y_r - span(longest=False) - CLAMP_SCREW
    fast = FASTENERS["insert"]
    out = Part()
    for d, h in ((fast.clear_d, BOTTOM_T + 2), (fast.head_d + 0.2, SLOT_CBORE + 1)):
        out += Pos(0, (y0 + y1) / 2, -1) * Box(d, y1 - y0, h, align=MIN)
        for y in (y0, y1):
            out += Pos(0, y, -1) * Cylinder(d / 2, h, align=MIN)
    return out


def window_half_width() -> float:
    """USB-C window half-width: the plug overmold + play."""
    return PLUG_W / 2 + USB_WINDOW_PLAY


def window_z() -> tuple[float, float]:
    """Bottom and top of the USB-C window: the plug overmold round any receptacle of the ranges."""
    lo = Z0 + SEAT_PCB_T[0] + SEAT_USB_H[0] / 2 - PLUG_H / 2 - 0.3
    hi = Z0 + SEAT_PCB_T[1] + SEAT_USB_H[1] / 2 + PLUG_H / 2 + 0.3
    return lo, hi


def usb_window(depth: float) -> Part:
    """Cutter: the plug-sized USB-C window through the whole back wall, from just in front of the
    nearest possible receptacle face; cut from both shells, it parts at the seam (no bridge)."""
    lo, hi = window_z()
    y0 = jaw_y(depth) - _dw(SEAT_W[1]) - abs(_dt(SEAT_PCB_T[0])) - 0.5
    return Pos(0, y0, lo) * Box(2 * window_half_width(), depth / 2 + 1 - y0, hi - lo, align=BACK)
