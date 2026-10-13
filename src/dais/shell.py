"""Geometry shared by every design: plan outline, wedge, key well, plate pilots, USB-C cuts."""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Part,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    chamfer,
    extrude,
    fillet,
)

from .layout import Layout
from .params import (
    MIN,
    PLATE_SCREW,
    PLUG_H,
    PLUG_W,
    R_CORNER,
    SCREW_PILOT,
    TILT,
    TOP_EDGE,
    USB_SLOT_FIT,
    WELL,
    WELL_DEPTH,
    WELL_R,
    WELL_RIM,
)


def side_x(lay: Layout, y: float, inset: float) -> float:
    """|x| of the side wall at plan ``y``, the outline shrunk by ``inset`` (normal to each edge)."""
    hb, hf, hd = lay.width / 2, lay.front_width / 2, lay.depth / 2
    k = (hb - hf) / (2 * hd)  # dx/dy of the side edge
    return hf + (y + hd) * k - inset * math.sqrt(1 + k * k)


def plan_pts(lay: Layout, inset: float) -> list[tuple[float, float]]:
    """Plan trapezoid (rectangle when front_width == width), shrunk by ``inset``; sharp corners."""
    yf, yb = -lay.depth / 2 + inset, lay.depth / 2 - inset
    xf, xb = side_x(lay, yf, inset), side_x(lay, yb, inset)
    return [(-xf, yf), (xf, yf), (xb, yb), (-xb, yb)]


def outline(lay: Layout, offset: float) -> Part:
    """Tall prism of the plan outline (R_CORNER corners) shrunk by ``offset``, from z = -1."""
    prism = Pos(0, 0, -1) * extrude(Polygon(*plan_pts(lay, offset), align=None), amount=lay.big)
    return fillet(prism.edges().filter_by(Axis.Z), radius=max(R_CORNER - offset, 0.3))


def wedge(lay: Layout) -> Part:
    """Side-profile prism (vertical front and back, top face at TILT) cut to the plan outline."""
    y0, y1 = -lay.depth / 2, lay.depth / 2
    slope = math.tan(math.radians(TILT))
    mid = (lay.h_front + lay.h_back) / 2
    side = Polygon((y0, 0), (y1, 0), (y1, mid + y1 * slope), (y0, mid + y0 * slope), align=None)
    prism = extrude(Plane.YZ * side, amount=lay.front_width / 2 + 1, both=True)
    return prism & (Pos(0, 0, -1) * extrude(Polygon(*plan_pts(lay, 0.0), align=None), amount=lay.big))


def outer_shell(lay: Layout) -> Part:
    """Solid wedge with R_CORNER vertical corners and the chamfered top perimeter."""
    shell = wedge(lay)
    shell = fillet(shell.edges().filter_by(Axis.Z), radius=R_CORNER)
    return chamfer(shell.faces().sort_by(Axis.Z)[-1].edges(), length=TOP_EDGE)


def key_well_and_pilots(lay: Layout) -> Part:
    """Cutter: the 1U key well with its 45 deg rim chamfer, and the four plate screw pilots."""
    well = Pos(0, 0, -1) * Box(WELL, WELL, WELL_DEPTH + 2, align=MIN)
    well = fillet(well.edges().filter_by(Axis.Z), radius=WELL_R)
    rim = extrude(
        Pos(0, 0, WELL_DEPTH - WELL_RIM) * RectangleRounded(WELL, WELL, WELL_R), amount=WELL_RIM + 1, taper=-45
    )
    cut = lay.key * (well + rim)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cut += (
                lay.key * Pos(sx * PLATE_SCREW, sy * PLATE_SCREW, -1) * Cylinder(SCREW_PILOT / 2, WELL_DEPTH, align=MIN)
            )
    return cut


def usb_cuts(lay: Layout) -> Part:
    """USB-C receptacle slot (through wall and lip zone) + plug notch from the receptacle face out
    through the back; the split designs cut it from both shells, since the seam crosses the plug."""
    b = lay.board
    slot_l = lay.depth / 2 + 1 - (lay.board_back - 0.5)
    slot = Pos(0, lay.board_back - 0.5 + slot_l / 2, lay.usb_z) * Box(
        b.usb_w + USB_SLOT_FIT, slot_l, b.usb_h + USB_SLOT_FIT
    )
    face = lay.board_back + b.usb_overhang
    notch = Pos(0, face, -1) * Box(
        PLUG_W, lay.depth, lay.usb_z + PLUG_H / 2 + 0.3 + 1, align=(Align.CENTER, Align.MIN, Align.MIN)
    )
    return slot + notch
