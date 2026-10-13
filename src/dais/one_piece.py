"""One-piece designs: a wedge body closed by a flush bottom plate, sculpted by a ball-cutter cove.

``side`` -- one teardrop cove on each side, centred along it.
``wrap`` -- one continuous cove along the front, round both front corners, then along each side.
"""

from __future__ import annotations

import math
from typing import Literal

from build123d import Axis, Box, Cylinder, Part, Pos, Rot, Sphere, Torus, chamfer

from .layout import Layout, above_floor, below_roof
from .params import (
    BOSS_H,
    BOSS_R,
    BOTTOM_EDGE,
    BOTTOM_T,
    COVE_BALL,
    COVE_BOTTOM,
    COVE_DEPTH,
    COVE_MARGIN,
    MIN,
    PLUG_H,
    PLUG_W,
    R_CORNER,
    SCREW_PILOT,
    TILT,
    USB_SLOT_FIT,
    USB_WALL_LEFT,
    WALL,
)
from .shell import key_well_and_pilots, outer_shell

Cove = Literal["side", "wrap"]


def make_body(lay: Layout, cove: Cove) -> Part:
    """Wedge shell: top skin with key well, coves, bosses up to the roof, USB-C slot and plug recess."""
    b = lay.board
    body = outer_shell(lay)
    body = chamfer(body.faces().sort_by(Axis.Z)[0].edges(), length=BOTTOM_EDGE)

    # cavity: vertical walls, roof = plate-top plane of the key frame
    walls = Pos(0, 0, -1) * Box(lay.in_x, lay.in_y, lay.h_back + 2, align=MIN)
    body -= walls & below_roof(lay)
    body -= key_well_and_pilots(lay)
    body -= wrap_cove(lay) if cove == "wrap" else side_coves(lay)

    # bosses for the bottom plate, each tied into its corner by a web; columns run up to the roof
    # (printed top down, a boss ending below the roof would start in mid-air)
    column = above_floor(lay) & below_roof(lay, lift=0.5)
    for x, y in lay.bosses:
        body += (Pos(x, y, -1) * Cylinder(BOSS_R, lay.big, align=MIN) + _corner_web(lay, x, y)) & column
        body -= Pos(x, y, BOTTOM_T - 1) * Cylinder(SCREW_PILOT / 2, BOSS_H, align=MIN)

    # USB-C: receptacle slot, overmold recess open through the bottom edge
    back = lay.in_y / 2
    body -= Pos(0, back + WALL / 2, lay.usb_z) * Box(b.usb_w + USB_SLOT_FIT, WALL + 2, b.usb_h + USB_SLOT_FIT)
    recess = WALL - USB_WALL_LEFT
    body -= Pos(0, lay.depth / 2 - recess / 2 + 0.5, -1) * Box(
        PLUG_W, recess + 1, lay.usb_z + PLUG_H / 2 + 1, align=MIN
    )
    return body


def _corner_web(lay: Layout, x: float, y: float) -> Part:
    """Block from a boss axis into its corner, fusing the boss with both walls (tall: clip it)."""
    sx, sy = math.copysign(1, x), math.copysign(1, y)
    wx, wy = lay.in_x / 2 + 0.5 - abs(x), lay.in_y / 2 + 0.5 - abs(y)
    return Pos(x + sx * wx / 2, y + sy * wy / 2, -1) * Box(wx, wy, lay.big, align=MIN)


def _cutter_path(start: tuple[float, float, float], yaw: float, length: float) -> Part:
    """Ball cutter swept from ``start`` along +Y risen by TILT, yawed ``yaw`` deg about Z."""
    tube = Rot(-90, 0, 0) * Cylinder(COVE_BALL, length, align=MIN)  # along +Y
    return Pos(*start) * (Sphere(COVE_BALL) + Rot(0, 0, yaw) * Rot(TILT, 0, 0) * tube)


def _cove_half_width() -> float:
    """Visible half-width of the cove on a flat face, at full depth."""
    return math.sqrt(2 * COVE_BALL * COVE_DEPTH - COVE_DEPTH**2)


def _cove_z_front() -> float:
    """World height of the cove axis on the front face: lower edge at COVE_BOTTOM."""
    return COVE_BOTTOM + _cove_half_width()


def _cove_z_key(lay: Layout) -> float:
    """Key-frame height of the cove axis (parallel to the top) through its front-face point."""
    t = math.radians(TILT)
    y, z = -lay.depth / 2, _cove_z_front() - lay.key_z
    return -y * math.sin(t) + z * math.cos(t)


def side_coves(lay: Layout) -> Part:
    """Teardrop on each side: round head, tail running out; COVE_MARGIN clear of front and back."""
    head_half = _cove_half_width()
    y_head = -lay.depth / 2 + COVE_MARGIN + head_half
    run = lay.depth / 2 - COVE_MARGIN - y_head
    drift = math.degrees(math.atan2(COVE_DEPTH, run))
    path = Sphere(COVE_BALL) + Rot(-90, 0, 0) * Cylinder(COVE_BALL, run + 10, align=MIN)  # along +Y
    coves = Part()
    for sx in (-1, 1):
        head = Pos(sx * (lay.width / 2 - COVE_DEPTH + COVE_BALL), y_head, _cove_z_key(lay))
        coves += lay.key * head * Rot(0, 0, -sx * drift) * path
    return coves


def wrap_cove(lay: Layout) -> Part:
    """One continuous cove: along the front, round both front corners at constant depth, then
    along each side, rising with the top and drifting out to run out COVE_MARGIN before the back."""
    off = COVE_BALL - COVE_DEPTH  # cutter centre outside the surface
    z = _cove_z_front()
    cx, cy = lay.width / 2 - R_CORNER, -lay.depth / 2 + R_CORNER  # front corner fillet axes (x = +-cx)
    big = lay.big
    cove = Pos(0, -lay.depth / 2 - off, z) * Rot(0, 90, 0) * Cylinder(COVE_BALL, 2 * cx)
    run = lay.depth / 2 - COVE_MARGIN - cy  # plan length of each side run
    drift = math.degrees(math.atan2(COVE_DEPTH, run))
    for sx in (-1, 1):
        ring = Pos(sx * cx, cy, z) * Torus(R_CORNER + off, COVE_BALL)
        quadrant = Pos(sx * (cx + big / 2), cy - big / 2, z) * Box(big, big, big)
        cove += ring & quadrant
        cove += _cutter_path((sx * (lay.width / 2 + off), cy, z), -sx * drift, run / math.cos(math.radians(TILT)) + 10)
    return cove
