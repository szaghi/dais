"""Skin patterns for the sides of the split top case: flutes, knurl, hex scales, ripple.

Each pattern is a cutter, built face by face in a local frame (x along the face, y = world up,
z = outward normal, surface at z = 0) and clipped to a band parallel to the top. The top case
prints top face down, so every relief is shaped for that: groove walls lean at most 45 deg from
the print axis, hex pockets have 45 deg drafted walls, and the lower groove ends ramp out at
PATTERN_RAMP instead of stopping on a flat ceiling. The back face (USB-C) stays plain.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Box,
    Circle,
    Compound,
    Cylinder,
    Face,
    GeomType,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    RegularPolygon,
    Rot,
    Spline,
    Vector,
    extrude,
    sweep,
)

from .layout import Layout
from .params import (
    FLUTE_PITCH,
    FLUTE_R,
    HEX_FLATS,
    HEX_GAP,
    KNURL_PITCH,
    PATTERN_BOTTOM,
    PATTERN_DEPTH,
    PATTERN_MARGIN,
    PATTERN_RAMP,
    PATTERN_TOP,
    REBATE_H,
    RIPPLE_AMP,
    RIPPLE_PITCH,
    RIPPLE_R,
    RIPPLE_WAVE,
    SPLIT_FRONT_Z,
    TILT,
    TOP_EDGE,
    Pattern,
)
from .shell import outer_shell

BIG = 400.0
ABOVE = (Align.CENTER, Align.CENTER, Align.MIN)
BELOW = (Align.CENTER, Align.CENTER, Align.MAX)


class _Face:
    """A planar side face of the top case: local frame, extent along it, and the pattern band."""

    def __init__(self, lay: Layout, face: Face) -> None:
        t = math.radians(TILT)
        n = face.normal_at(face.center())
        n = Vector(n.X, n.Y, 0).normalized()
        u = Vector(0, 0, 1).cross(n)  # with z_dir = n this makes local y = world up
        c = face.center()
        self.loc = Location(Plane(origin=(c.X, c.Y, 0), x_dir=u, z_dir=n))
        xs = [(Vector(v) - Vector(c.X, c.Y, 0)).dot(u) for v in face.vertices()]
        self.x0, self.x1 = min(xs) + PATTERN_MARGIN, max(xs) - PATTERN_MARGIN
        # band in parting-frame heights: above the rebate, below the top bevel
        self._p0 = Vector(0, -lay.depth / 2, SPLIT_FRONT_Z)
        self._nrm = Vector(0, -math.sin(t), math.cos(t))
        self._c, self._u = Vector(c.X, c.Y, 0), u
        top = (lay.h_front - SPLIT_FRONT_Z) * math.cos(t)  # parting plane -> top face
        self.h0 = REBATE_H + PATTERN_BOTTOM
        self.h1 = top - TOP_EDGE - PATTERN_TOP

    def y_at(self, x: float, h: float) -> float:
        """Local y (world z) where the face meets parting-frame height ``h``, at local ``x``."""
        p = self._c + self._u * x
        return (h - (p - self._p0).dot(self._nrm)) / self._nrm.Z

    def line(self, h: float) -> tuple[float, float]:
        """``(c, k)`` of the band edge ``y = c + k x`` at height ``h``."""
        c = self.y_at(0.0, h)
        return c, self.y_at(1.0, h) - c

    def clip(self) -> Part:
        """Band region: lower edge a ramp into the wall, upper edge and ends perpendicular."""
        (c0, k0), (c1, k1) = self.line(self.h0), self.line(self.h1)
        a = math.radians(PATTERN_RAMP)
        low_n = Vector(-k0 * math.cos(a), math.cos(a), math.sin(a)).normalized()
        low = Location(Plane(origin=(0, c0, 0), z_dir=low_n)) * Box(BIG, BIG, BIG, align=ABOVE)
        high = Location(Plane(origin=(0, c1, 0), z_dir=Vector(-k1, 1, 0).normalized())) * Box(
            BIG, BIG, BIG, align=BELOW
        )
        ends = Pos((self.x0 + self.x1) / 2, 0, 0) * Box(self.x1 - self.x0, BIG, BIG)
        return low & high & ends

    def y_range(self) -> tuple[float, float]:
        """Lowest and highest local y of the band over the face."""
        ys = [self.y_at(x, h) for x in (self.x0, self.x1) for h in (self.h0, self.h1)]
        return min(ys), max(ys)


def _faces(lay: Layout) -> list[_Face]:
    """Front and side faces of the outer shell (vertical and planar); not the back (USB-C)."""
    out = []
    for f in outer_shell(lay).faces():
        if f.geom_type != GeomType.PLANE:
            continue
        n = f.normal_at(f.center())
        if abs(n.Z) < 1e-6 and n.Y < 0.9:
            out.append(_Face(lay, f))
    return out


def _flutes(face: _Face) -> Part:
    """Vertical grooves, whole ones only, evenly spread over the face."""
    lo, hi = face.y_range()
    n = int((face.x1 - face.x0 - 2 * FLUTE_R) // FLUTE_PITCH) + 1
    start = (face.x0 + face.x1) / 2 - (n - 1) * FLUTE_PITCH / 2
    rod = Cylinder(FLUTE_R, hi - lo + 4, align=ABOVE)
    cut = Part()
    for i in range(n):
        cut += Pos(start + i * FLUTE_PITCH, lo - 2, FLUTE_R - PATTERN_DEPTH) * Rot(-90, 0, 0) * rod
    return cut


def _knurl(face: _Face) -> Part:
    """Crossed 90 deg V-grooves at +-45 deg: raised diamonds between them."""
    d = PATTERN_DEPTH
    vee = Polygon((-(d + 1.0), 1.0), (d + 1.0, 1.0), (0.0, -d), align=None)  # (across, z): apex at -d
    lo, hi = face.y_range()
    span = (face.x1 - face.x0) + (hi - lo)
    groove = extrude(Plane.YZ * vee, amount=span + 5, both=True)  # along local x
    cx, cy = (face.x0 + face.x1) / 2, (lo + hi) / 2
    m = int(span / KNURL_PITCH) + 2
    grooves = []
    for sign in (1, -1):
        a = math.radians(45 * sign)
        normal = Vector(-math.sin(a), math.cos(a), 0)  # spacing direction, across the grooves
        for i in range(-m, m + 1):
            off = i * KNURL_PITCH
            grooves.append(Pos(cx + normal.X * off, cy + normal.Y * off, 0) * Rot(0, 0, 45 * sign) * groove)
    # one compound, one boolean: fusing ~90 crossing grooves one by one is quadratic in OCC
    return Part(Compound(grooves).wrapped)


def _hex(face: _Face) -> Part:
    """Pointy-top hexagonal pockets with 45 deg drafted walls in staggered rows that follow the band
    (parallel to the top), columns centred on the face; whole hexagons only."""
    r = HEX_FLATS / math.sqrt(3)  # circumradius at the surface
    lift = 0.5  # start the cutter above the surface so it opens cleanly
    pocket = Pos(0, 0, lift) * extrude(
        RegularPolygon(r + lift, 6, rotation=30), amount=PATTERN_DEPTH + lift, dir=(0, 0, -1), taper=45
    )
    dx, dy = HEX_FLATS + HEX_GAP, (HEX_FLATS + HEX_GAP) * math.sqrt(3) / 2
    (c0, k), (c1, _) = face.line(face.h0), face.line(face.h1)
    ramp = PATTERN_DEPTH / math.tan(math.radians(PATTERN_RAMP))
    first, last = c0 + ramp + r, c1 - r  # row centre lines at x = 0
    rows = int((last - first) / dy) + 1
    first += ((last - first) - (rows - 1) * dy) / 2  # centre the rows in the band
    cols = int((face.x1 - face.x0 - HEX_FLATS) / dx) + 1
    x_first = (face.x0 + face.x1) / 2 - (cols - 1) * dx / 2
    cut = Part()
    for j in range(rows):
        shift = 0.5 * dx if j % 2 else 0.0
        for i in range(cols):
            x = x_first + i * dx + shift
            if x + HEX_FLATS / 2 > face.x1:
                continue
            cut += Pos(x, first + j * dy + k * x, 0) * pocket
    return cut


def _ripple(face: _Face) -> Part:
    """Wide shallow grooves swept along a gentle sine, following the band (parallel to the top);
    laid out so each whole groove stays inside the band -- only the face ends clip them."""
    (c0, k), (c1, _) = face.line(face.h0), face.line(face.h1)
    half = math.sqrt(2 * RIPPLE_R * PATTERN_DEPTH - PATTERN_DEPTH**2)  # groove half-width on the face
    ramp = PATTERN_DEPTH / math.tan(math.radians(PATTERN_RAMP))
    first, last = c0 + ramp + half + RIPPLE_AMP, c1 - half - RIPPLE_AMP
    n = int((last - first) / RIPPLE_PITCH) + 1
    first += ((last - first) - (n - 1) * RIPPLE_PITCH) / 2
    xa, xb = face.x0 - 3, face.x1 + 3
    axis_z = RIPPLE_R - PATTERN_DEPTH
    cut = Part()
    for j in range(n):
        base = first + j * RIPPLE_PITCH
        phase = j * math.pi / 2
        xs = [xa + i * (xb - xa) / 24 for i in range(25)]
        pts = [(x, base + k * x + RIPPLE_AMP * math.sin(2 * math.pi * x / RIPPLE_WAVE + phase), axis_z) for x in xs]
        path = Spline(*pts)
        profile = Plane(origin=path @ 0, z_dir=path % 0) * Circle(RIPPLE_R)
        cut += sweep(profile, path=path)
    return cut


MAKERS = {"flutes": _flutes, "knurl": _knurl, "hex": _hex, "ripple": _ripple}


def skin_pattern(lay: Layout, pattern: Pattern) -> Part:
    """The cutter of ``pattern`` over the front and side faces of the top case."""
    cut = Part()
    for face in _faces(lay):
        cut += face.loc * (MAKERS[pattern](face) & face.clip())
    return cut
