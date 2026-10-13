"""Skin patterns for the sides of the split top case: fuzzy skin, voronoi leather, facets.

``fuzzy`` changes no geometry: it exports a modifier volume -- a thin shell inside the front and
side walls -- for the slicer's fuzzy-skin setting, so the texture stays off the top face, the
bevels, the seam and the back. ``voronoi`` and ``facets`` are cutters, built face by face in a
local frame (x along the face, y = world up, z = outward normal, surface at z = 0) and clipped to
a band parallel to the top. The top case prints top face down, so every relief face turned
toward the bed stays within PATTERN_MAX_UP (about 33 deg from the wall, 40 deg with the 7 deg
print tilt), and the band's lower edge ramps out at PATTERN_RAMP. The back face (USB-C) stays plain.
"""

from __future__ import annotations

import math
import random

import numpy as np
from build123d import (
    Align,
    Box,
    Compound,
    Face,
    GeomType,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Vector,
    extrude,
    loft,
)
from scipy.spatial import Voronoi

from .layout import Layout, between
from .params import (
    FACET_DEPTH,
    FACET_TILE,
    FUZZY_SKIN,
    PATTERN_BOTTOM,
    PATTERN_MARGIN,
    PATTERN_MAX_UP,
    PATTERN_RAMP,
    PATTERN_SEED,
    PATTERN_TOP,
    R_CORNER,
    REBATE_H,
    SPLIT_FRONT_Z,
    TILT,
    TOP_EDGE,
    VORONOI_CELL,
    VORONOI_DEPTH,
    VORONOI_DRAFT,
    VORONOI_GROOVE,
    Pattern,
)
from .shell import outer_shell, outline

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


Pt = tuple[float, float]


def _rng(face: _Face) -> random.Random:
    """Reproducible per-face randomness."""
    return random.Random(PATTERN_SEED * 1000 + round(face.x1 - face.x0) * 37 + round(face.h1 * 10))


def _area(poly: list[Pt]) -> float:
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1], strict=True))


def _inset(poly: list[Pt], d: float) -> list[Pt] | None:
    """Convex CCW polygon offset inward by ``d`` (outward when negative); None when it collapses.

    Half-plane clipping, not edge-line intersection: an inset makes short edges vanish (Voronoi
    cells have many), which intersecting consecutive offset lines cannot handle.
    """
    xs, ys = [q[0] for q in poly], [q[1] for q in poly]
    m = abs(d) + 1.0
    out: list[Pt] = [
        (min(xs) - m, min(ys) - m),
        (max(xs) + m, min(ys) - m),
        (max(xs) + m, max(ys) + m),
        (min(xs) - m, max(ys) + m),
    ]
    for a, b in zip(poly, poly[1:] + poly[:1], strict=True):
        ex, ey = b[0] - a[0], b[1] - a[1]
        n = math.hypot(ex, ey)
        if n < 1e-9:
            continue
        nx, ny = -ey / n, ex / n  # inward (left) normal of a CCW edge
        c = nx * a[0] + ny * a[1] + d  # keep points with n . p >= c

        def side(q: Pt, nx: float = nx, ny: float = ny, c: float = c) -> float:
            return nx * q[0] + ny * q[1] - c

        clipped: list[Pt] = []
        for p, q in zip(out, out[1:] + out[:1], strict=True):
            sp, sq = side(p), side(q)
            if sp >= 0:
                clipped.append(p)
            if sp * sq < 0:
                t = sp / (sp - sq)
                clipped.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        out = clipped
        if len(out) < 3:
            return None
    return out if _area(out) > 0.3 else None


def _dedupe(poly: list[Pt], tol: float = 0.05) -> list[Pt]:
    """Drop vertices closer than ``tol`` to the previous one (short edges make degenerate lofts)."""
    out: list[Pt] = []
    for q in poly:
        if not out or math.dist(q, out[-1]) > tol:
            out.append(q)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= tol:
        out.pop()
    return out


def _miter(poly: list[Pt], r: float) -> list[Pt]:
    """Convex CCW polygon offset outward by ``r``, vertex for vertex (miter joins)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, v, b = poly[i - 1], poly[i], poly[(i + 1) % n]
        n1 = _left_normal(a, v)
        n2 = _left_normal(v, b)
        k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        out.append((v[0] - r * (n1[0] + n2[0]) / k, v[1] - r * (n1[1] + n2[1]) / k))
    return out


def _left_normal(a: Pt, b: Pt) -> Pt:
    ex, ey = b[0] - a[0], b[1] - a[1]
    n = math.hypot(ex, ey)
    return (-ey / n, ex / n)


def _sheared(face: _Face, pts: list[Pt]) -> list[tuple[float, float]]:
    """Band coordinates (x, s above the band's lower edge) -> local face (x, y)."""
    c0, k = face.line(face.h0)
    return [(x, c0 + k * x + s) for x, s in pts]


def _voronoi(face: _Face) -> Part:
    """Leather: raised Voronoi cells over the whole band, separated by V grooves with drafted walls."""
    (c0, _), (c1, _) = face.line(face.h0), face.line(face.h1)
    w, h = face.x1 - face.x0, c1 - c0
    rng = _rng(face)
    pts: list[Pt] = []
    for _ in range(4000):  # dart throwing: a loose Poisson-disk set, leather-irregular
        p = (rng.uniform(0, w), rng.uniform(0, h))
        if all(math.dist(p, q) > 0.8 * VORONOI_CELL for q in pts):
            pts.append(p)
    # mirror across the four sides: the rectangle edges become Voronoi edges, every cell bounded
    mirrored = pts + [(-x, s) for x, s in pts] + [(2 * w - x, s) for x, s in pts]
    mirrored += [(x, -s) for x, s in pts] + [(x, 2 * h - s) for x, s in pts]
    vor = Voronoi(np.array(mirrored))
    pads, failed = [], []
    for i, (px, ps) in enumerate(pts):
        region = vor.regions[vor.point_region[i]]
        if -1 in region or not region:
            continue
        cell = [tuple(vor.vertices[v]) for v in region]
        cell.sort(key=lambda q: math.atan2(q[1] - ps, q[0] - px))  # CCW around the seed
        top = _inset([(x + face.x0, s) for x, s in cell], VORONOI_GROOVE / 2)
        if top is None:
            continue
        top = _dedupe(top)
        if len(top) < 3:
            continue
        run = (VORONOI_DEPTH + 0.02) * math.tan(math.radians(VORONOI_DRAFT))
        foot = _miter(top, run)  # vertex-for-vertex outward offset: the loft pairs matching corners
        a = Plane.XY.offset(0.01) * Polygon(*_sheared(face, top), align=None)
        b = Plane.XY.offset(-VORONOI_DEPTH - 0.01) * Polygon(*_sheared(face, foot), align=None)
        try:
            pads.append(loft([a, b]))  # drafted pad: tapered extrusion's 2D offset fails on sharp cells
        except Exception as err:
            failed.append(err)
    if failed:
        raise RuntimeError(f"voronoi: {len(failed)} of {len(failed) + len(pads)} cell pads failed to loft")
    slab = Pos((face.x0 + face.x1) / 2, (c0 + c1) / 2, (1 - VORONOI_DEPTH) / 2) * Box(w + 2, BIG, 1 + VORONOI_DEPTH)
    return slab - Part(Compound(pads).wrapped)


def _facets(face: _Face) -> Part:
    """Faceted panel: one inverted pyramid per tile, apex at a random point and depth; every facet
    turned toward the bed checked against PATTERN_MAX_UP (the apex is moved/shallowed until it is)."""
    (c0, k), (c1, _) = face.line(face.h0), face.line(face.h1)
    w, h = face.x1 - face.x0, c1 - c0
    nx, ny = max(1, round(w / FACET_TILE)), max(1, round(h / FACET_TILE))
    tw, th = w / nx, h / ny
    rng = _rng(face)

    def p3(x: float, s: float, z: float) -> Vector:
        return Vector(x, c0 + k * x + s, z)

    tiles = []
    for j in range(ny):
        for i in range(nx):
            x, s = face.x0 + i * tw, j * th
            corners = [p3(x, s, 0), p3(x + tw, s, 0), p3(x + tw, s + th, 0), p3(x, s + th, 0)]  # CCW
            depth = rng.uniform(*FACET_DEPTH)
            for attempt in range(60):
                u, v = rng.uniform(0.25, 0.75), rng.uniform(0.35, 0.85)
                apex = p3(x + u * tw, s + v * th, -depth)
                normals = []
                for a, b in zip(corners, corners[1:] + corners[:1], strict=True):
                    n = (b - a).cross(apex - a).normalized()
                    normals.append((a, n if n.Z > 0 else -n))
                if all(n.Y <= PATTERN_MAX_UP for _, n in normals):
                    break
                if attempt % 10 == 9:
                    depth *= 0.85
            else:
                continue  # no printable apex found: leave the tile flat
            prism = Pos(0, 0, -2) * extrude(Polygon(*[(c.X, c.Y) for c in corners], align=None), amount=3)
            for a, n in normals:
                prism &= Location(Plane(origin=a, z_dir=n)) * Box(BIG, BIG, BIG, align=ABOVE)
            tiles.append(prism)
    return Part(Compound(tiles).wrapped)


MAKERS = {"voronoi": _voronoi, "facets": _facets}


def skin_pattern(lay: Layout, pattern: Pattern) -> Part | None:
    """The cutter of ``pattern`` over the front and side faces of the top case (None for ``fuzzy``)."""
    if pattern not in MAKERS:
        return None
    cut = Part()
    for face in _faces(lay):
        cut += face.loc * (MAKERS[pattern](face) & face.clip())
    return cut


def fuzzy_modifier(lay: Layout) -> Part:
    """Slicer modifier for ``fuzzy``: a FUZZY_SKIN-thick shell inside the front and side walls of the
    top case, between the rebate and the top bevel, clear of the back (USB-C). Load it as a modifier
    with fuzzy skin on: only the perimeters it encloses get fuzzed."""
    t = math.radians(TILT)
    top = (lay.h_front - SPLIT_FRONT_Z) * math.cos(t)
    skin = outline(lay, -0.5) - outline(lay, FUZZY_SKIN)
    band = between(lay, REBATE_H + 0.3, top - TOP_EDGE - 0.4)
    back = Pos(0, lay.depth / 2 - R_CORNER - 0.5, 0) * Box(BIG, BIG, BIG, align=(Align.CENTER, Align.MIN, Align.CENTER))
    return (skin & band) - back
