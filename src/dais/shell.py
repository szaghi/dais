"""Geometry shared by every design: plan outline, wedge, key well, plate pilots, USB-C cuts."""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Face,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    chamfer,
    extrude,
    fillet,
)

from .layout import Layout
from .params import (
    FUNNEL_BOTTOM,
    MAX,
    MIN,
    PLATE,
    PLATE_SCREW,
    PLATE_SCREW_PILOT,
    PLATE_T,
    PLUG_H,
    PLUG_W,
    R_CORNER,
    SW_CUT,
    TILT,
    USB_SLOT_FIT,
    WALL,
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


def bevel(part: Part, face: Face, height: float, angle: float) -> Part:
    """Chamfer the edges of ``face``: ``height`` along the side walls, at ``angle`` from ``face``.

    Steeper than 45 deg means less overhang per layer where the face lies on the print bed.
    """
    if abs(angle - 45.0) < 1e-9:
        return chamfer(face.edges(), length=height)
    return chamfer(face.edges(), length=height / math.tan(math.radians(angle)), length2=height, reference=face)


def top_edge(lay: Layout) -> float:
    """Height of the top-perimeter chamfer: the design's, its run capped at R_CORNER - 1 (a longer
    run eats the corner rounds; OCC fails on it, e.g. the plinth's 2.5 mm at 45 deg)."""
    return min(lay.look.top_edge, (R_CORNER - 1.0) * math.tan(math.radians(lay.opt.bevel)))


def outer_shell(lay: Layout) -> Part:
    """Solid wedge with R_CORNER vertical corners and the bevelled top perimeter."""
    shell = wedge(lay)
    shell = fillet(shell.edges().filter_by(Axis.Z), radius=R_CORNER)
    return bevel(shell, shell.faces().sort_by(Axis.Z)[-1], top_edge(lay), lay.opt.bevel)


def key_well(lay: Layout) -> Part:
    """Cutter: the 1U key well with its bevelled rim, and below it either the plate screw pilots
    (separate plate) or the switch opening of the integrated plate: a 45 deg funnel down to
    FUNNEL_BOTTOM at the plate top -- printed top down, a flat ring would overhang -- and the
    SW_CUT cutout through the PLATE_T web."""
    size, depth = lay.look.well, lay.look.well_depth
    well = Pos(0, 0, -1) * Box(size, size, depth + 2, align=MIN)
    well = fillet(well.edges().filter_by(Axis.Z), radius=WELL_R)
    rim = extrude(
        Pos(0, 0, depth - WELL_RIM) * RectangleRounded(size, size, WELL_R),
        amount=WELL_RIM + 1,
        taper=-(90.0 - lay.opt.bevel),
    )
    if lay.opt.plate == "separate":
        cut = lay.key * (well + rim)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cut += (
                    lay.key
                    * Pos(sx * PLATE_SCREW, sy * PLATE_SCREW, -1)
                    * Cylinder(PLATE_SCREW_PILOT / 2, depth, align=MIN)
                )
        return cut
    # sharp corners: a tapered rounded rectangle grows its corner radius with height and would
    # pinch a pressed keycap's corners (0.18 mm); sharp ones keep the diagonal clearance
    funnel = extrude(Rectangle(FUNNEL_BOTTOM, FUNNEL_BOTTOM), amount=depth + 2, taper=-45)
    cutout = Box(SW_CUT, SW_CUT, 2 * PLATE_T + 2)
    return lay.key * ((well & funnel) + rim + cutout)


def integrated_plate(lay: Layout) -> Part:
    """The switch plate as part of the top shell: a PLATE_T web under the top skin (cut by ``key_well``);
    a key moved forward (board behind the switch) would push it through the front wall: clipped."""
    plate = lay.key * Box(PLATE, PLATE, PLATE_T, align=MAX)
    return plate if lay.key_y == 0.0 else plate & outline(lay, WALL - 0.5)


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
