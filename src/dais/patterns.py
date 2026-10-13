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

import itertools
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
    FULL_MARGIN,
    FUZZY_SKIN,
    MIN_WALL,
    PATTERN_BOTTOM,
    PATTERN_MARGIN,
    PATTERN_MAX_UP,
    PATTERN_RAMP,
    PATTERN_SEED,
    PATTERN_TOP,
    R_CORNER,
    REBATE_H,
    RIM_R,
    RIM_WALL,
    SPLIT_FRONT_Z,
    TILT,
    TOP_EDGE,
    VORONOI_CELL,
    VORONOI_DEPTH,
    VORONOI_DRAFT,
    VORONOI_GROOVE,
    Pattern,
)
from .shell import outer_shell, outline, plan_pts

BIG = 400.0
ABOVE = (Align.CENTER, Align.CENTER, Align.MIN)
BELOW = (Align.CENTER, Align.CENTER, Align.MAX)


class _Face:
    """A planar side face of the top case: local frame, extent along it, and the pattern band."""

    def __init__(self, lay: Layout, face: Face, full: bool = False) -> None:
        t = math.radians(TILT)
        n = face.normal_at(face.center())
        n = Vector(n.X, n.Y, 0).normalized()
        u = Vector(0, 0, 1).cross(n)  # with z_dir = n this makes local y = world up
        c = face.center()
        self.loc = Location(Plane(origin=(c.X, c.Y, 0), x_dir=u, z_dir=n))
        xs = [(Vector(v) - Vector(c.X, c.Y, 0)).dot(u) for v in face.vertices()]
        margin = FULL_MARGIN if full else PATTERN_MARGIN
        self.x0, self.x1 = min(xs) + margin, max(xs) - margin
        # band in parting-frame heights: above the rebate, below the top bevel
        self._p0 = Vector(0, -lay.depth / 2, SPLIT_FRONT_Z)
        self._nrm = Vector(0, -math.sin(t), math.cos(t))
        self._c, self._u = Vector(c.X, c.Y, 0), u
        top = (lay.h_front - SPLIT_FRONT_Z) * math.cos(t)  # parting plane -> top face
        if full:  # the whole flat side: from the rim round's tangent line to the top bevel line
            self.h0, self.h1 = RIM_R + FULL_MARGIN, top - TOP_EDGE - FULL_MARGIN
        else:  # a band above the rebate (full wall thickness behind it)
            self.h0, self.h1 = REBATE_H + PATTERN_BOTTOM, top - TOP_EDGE - PATTERN_TOP

    def h_at(self, x: float, y: float) -> float:
        """Parting-frame height of the local face point (x, y)."""
        return (self._c + self._u * x - self._p0).dot(self._nrm) + y * self._nrm.Z

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


def _faces(lay: Layout, full: bool = False) -> list[_Face]:
    """Front and side faces of the outer shell (vertical and planar); not the back (USB-C)."""
    out = []
    for f in outer_shell(lay).faces():
        if f.geom_type != GeomType.PLANE:
            continue
        n = f.normal_at(f.center())
        if abs(n.Z) < 1e-6 and n.Y < 0.9:
            out.append(_Face(lay, f, full))
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
            # over the rebate the wall is only RIM_WALL thick: cap the depth so MIN_WALL remains
            ratio = _rebate_depth_ratio(face, corners, normals, depth)
            if ratio > 0 and depth * ratio > RIM_WALL - MIN_WALL:
                depth = (RIM_WALL - MIN_WALL) / ratio
                apex = Vector(apex.X, apex.Y, -depth)
                normals = []
                for a, b in zip(corners, corners[1:] + corners[:1], strict=True):
                    n = (b - a).cross(apex - a).normalized()
                    normals.append((a, n if n.Z > 0 else -n))
            prism = Pos(0, 0, -2) * extrude(Polygon(*[(c.X, c.Y) for c in corners], align=None), amount=3)
            for a, n in normals:
                prism &= Location(Plane(origin=a, z_dir=n)) * Box(BIG, BIG, BIG, align=ABOVE)
            tiles.append(prism)
    return Part(Compound(tiles).wrapped)


def _rebate_depth_ratio(
    face: _Face, corners: list[Vector], normals: list[tuple[Vector, Vector]], depth: float
) -> float:
    """Largest relief depth over the rebate zone, as a fraction of the apex depth (0 if none there)."""
    worst = 0.0
    for i in range(11):
        for j in range(11):
            a, b = i / 10, j / 10  # bilinear over the (sheared) tile
            p = (
                corners[0] * (1 - a) * (1 - b)
                + corners[1] * a * (1 - b)
                + corners[2] * a * b
                + corners[3] * (1 - a) * b
            )
            if face.h_at(p.X, p.Y) > REBATE_H + 0.3:
                continue
            z = max(o.Z - (n.X * (p.X - o.X) + n.Y * (p.Y - o.Y)) / n.Z for o, n in normals)  # the relief surface
            worst = max(worst, -z / depth)
    return worst


class _Seg:
    """One flat piece of the unrolled front strip (a face, or a chord of a front corner round):
    local frame x along the strip (travel direction), y = world up, z = outward normal."""

    def __init__(self, lay: Layout, p0: Pt, p1: Pt, u0: float) -> None:
        t = math.radians(TILT)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.L = math.hypot(dx, dy)
        self.t = Vector(dx / self.L, dy / self.L, 0)
        self.n = Vector(self.t.Y, -self.t.X, 0)  # outward: right of travel on a CCW outline
        self.p0 = Vector(p0[0], p0[1], 0)
        self.u0 = u0
        self.loc = Location(Plane(origin=self.p0, x_dir=self.t, z_dir=self.n))
        self._P0 = Vector(0, -lay.depth / 2, SPLIT_FRONT_Z)
        self._nrm = Vector(0, -math.sin(t), math.cos(t))

    def y_at(self, x: float, h: float) -> float:
        p = self.p0 + self.t * x
        return (h - (p - self._P0).dot(self._nrm)) / self._nrm.Z

    def h_at(self, x: float, y: float) -> float:
        return (self.p0 + self.t * x - self._P0).dot(self._nrm) + y * self._nrm.Z

    def local(self, u: float, s: float, h0: float, z: float = 0.0) -> Vector:
        """Unrolled strip point (u along, s above the band's lower edge, z out) -> local frame."""
        x = u - self.u0
        return Vector(x, self.y_at(x, h0) + s, z)

    def to_local(self, v: Vector) -> Vector:
        """A world direction in this segment's local frame."""
        return Vector(v.dot(self.t), v.Z, v.dot(self.n))


class _Strip:
    """Front strip unrolled: left side, front-left corner round, front, front-right round, right
    side. The rounds are split into CORNER_CHORDS flat chords (R3: 0.03 mm off the true arc)."""

    CORNER_CHORDS = 6

    def __init__(self, lay: Layout) -> None:
        t = math.radians(TILT)
        top = (lay.h_front - SPLIT_FRONT_Z) * math.cos(t)
        self.h0, self.h1 = RIM_R + FULL_MARGIN, top - TOP_EDGE - FULL_MARGIN
        self.H = (self.h1 - self.h0) / math.cos(t)
        v0, v1, v2, v3 = plan_pts(lay, 0.0)  # CCW: front-left, front-right, back-right, back-left
        path = [self._tangent_out(v2, v3, v0)]  # left side starts at the back-left round
        path += self._round(v3, v0, v1) + self._round(v0, v1, v2)
        path.append(self._tangent_in(v1, v2, v3))  # right side ends at the back-right round
        self.segs, u = [], 0.0
        for a, b in itertools.pairwise(path):
            seg = _Seg(lay, a, b, u)
            self.segs.append(seg)
            u += seg.L
        self.ua, self.ub = FULL_MARGIN, u - FULL_MARGIN

    @staticmethod
    def _fillet(prev: Pt, v: Pt, nxt: Pt) -> tuple[Pt, Pt, Pt, float, float]:
        """R_CORNER round at ``v``: tangent points, centre and start/end angles."""
        a = Vector(v[0] - prev[0], v[1] - prev[1], 0).normalized()
        b = Vector(nxt[0] - v[0], nxt[1] - v[1], 0).normalized()
        theta = math.acos(max(-1.0, min(1.0, (-a).dot(b))))  # interior angle
        d = R_CORNER / math.tan(theta / 2)
        t1, t2 = (v[0] - a.X * d, v[1] - a.Y * d), (v[0] + b.X * d, v[1] + b.Y * d)
        inward = (b - a).normalized()
        c = (v[0] + inward.X * R_CORNER / math.sin(theta / 2), v[1] + inward.Y * R_CORNER / math.sin(theta / 2))
        f1, f2 = math.atan2(t1[1] - c[1], t1[0] - c[0]), math.atan2(t2[1] - c[1], t2[0] - c[0])
        if f2 < f1:
            f2 += 2 * math.pi  # CCW outline: the round turns counter-clockwise
        return t1, t2, c, f1, f2

    def _round(self, prev: Pt, v: Pt, nxt: Pt) -> list[Pt]:
        _, _, c, f1, f2 = self._fillet(prev, v, nxt)
        n = self.CORNER_CHORDS
        return [
            (c[0] + R_CORNER * math.cos(f1 + (f2 - f1) * i / n), c[1] + R_CORNER * math.sin(f1 + (f2 - f1) * i / n))
            for i in range(n + 1)
        ]

    def _tangent_out(self, prev: Pt, v: Pt, nxt: Pt) -> Pt:
        return self._fillet(prev, v, nxt)[1]

    def _tangent_in(self, prev: Pt, v: Pt, nxt: Pt) -> Pt:
        return self._fillet(prev, v, nxt)[0]

    def clip(self, i: int) -> Part:
        """Segment ``i``'s share of the band: ramped lower edge, upper edge, and its two ends --
        the bisector planes with its neighbours (pieces meet exactly), or the strip ends."""
        seg = self.segs[i]
        c0, c1 = seg.y_at(0.0, self.h0), seg.y_at(0.0, self.h1)
        k0, k1 = seg.y_at(1.0, self.h0) - c0, seg.y_at(1.0, self.h1) - c1
        a = math.radians(PATTERN_RAMP)
        low_n = Vector(-k0 * math.cos(a), math.cos(a), math.sin(a)).normalized()
        region = Location(Plane(origin=(0, c0, 0), z_dir=low_n)) * Box(BIG, BIG, BIG, align=ABOVE)
        region &= Location(Plane(origin=(0, c1, 0), z_dir=Vector(-k1, 1, 0).normalized())) * Box(
            BIG, BIG, BIG, align=BELOW
        )
        if i == 0:
            start = Location(Plane(origin=(self.ua - seg.u0, 0, 0), z_dir=(1, 0, 0)))
        else:
            start = Location(Plane(origin=(0, 0, 0), z_dir=seg.to_local((self.segs[i - 1].t + seg.t).normalized())))
        region &= start * Box(BIG, BIG, BIG, align=ABOVE)
        if i == len(self.segs) - 1:
            end = Location(Plane(origin=(self.ub - seg.u0, 0, 0), z_dir=(1, 0, 0)))
        else:
            end = Location(Plane(origin=(seg.L, 0, 0), z_dir=seg.to_local((seg.t + self.segs[i + 1].t).normalized())))
        return region & (end * Box(BIG, BIG, BIG, align=BELOW))

    def near(self, i: int, umin: float, umax: float, pad: float = 1.0) -> bool:
        seg = self.segs[i]
        return umax >= seg.u0 - pad and umin <= seg.u0 + seg.L + pad


def _voronoi_full(lay: Layout) -> Part:
    """``voronoi`` over the whole front strip, continuous round the front corners."""
    strip = _Strip(lay)
    w, h = strip.ub - strip.ua, strip.H
    rng = random.Random(PATTERN_SEED * 1000 + round(w))
    pts: list[Pt] = []
    for _ in range(15000):
        q = (rng.uniform(0, w), rng.uniform(0, h))
        if all(math.dist(q, o) > 0.8 * VORONOI_CELL for o in pts):
            pts.append(q)
    mirrored = pts + [(-x, y) for x, y in pts] + [(2 * w - x, y) for x, y in pts]
    mirrored += [(x, -y) for x, y in pts] + [(x, 2 * h - y) for x, y in pts]
    vor = Voronoi(np.array(mirrored))
    run = (VORONOI_DEPTH + 0.02) * math.tan(math.radians(VORONOI_DRAFT))
    cells = []
    for i, (px, py) in enumerate(pts):
        region = vor.regions[vor.point_region[i]]
        if -1 in region or not region:
            continue
        cell = [tuple(vor.vertices[v]) for v in region]
        cell.sort(key=lambda q: math.atan2(q[1] - py, q[0] - px))
        top = _inset([(x + strip.ua, y) for x, y in cell], VORONOI_GROOVE / 2)
        if top is None or len(top := _dedupe(top)) < 3:
            continue
        foot = _miter(top, run)
        cells.append((top, foot, min(q[0] for q in foot), max(q[0] for q in foot)))
    cut = Part()
    for i, seg in enumerate(strip.segs):
        pads = []
        for top, foot, umin, umax in cells:
            if not strip.near(i, umin, umax):
                continue
            a = Plane.XY.offset(0.01) * Polygon(
                *[(v.X, v.Y) for v in (seg.local(u, y, strip.h0) for u, y in top)], align=None
            )
            b = Plane.XY.offset(-VORONOI_DEPTH - 0.01) * Polygon(
                *[(v.X, v.Y) for v in (seg.local(u, y, strip.h0) for u, y in foot)], align=None
            )
            pads.append(loft([a, b]))
        yc = seg.y_at(seg.L / 2, strip.h0) + strip.H / 2
        piece = Pos(seg.L / 2, yc, (1 - VORONOI_DEPTH) / 2) * Box(seg.L + 4, BIG, 1 + VORONOI_DEPTH)
        if pads:
            piece -= Part(Compound(pads).wrapped)
        cut += seg.loc * (piece & strip.clip(i))
    return cut


def _facets_full(lay: Layout) -> Part:
    """``facets`` over the whole front strip, tiles continuing round the front corners."""
    strip = _Strip(lay)
    w = strip.ub - strip.ua
    nx, ny = max(1, round(w / FACET_TILE)), max(1, round(strip.H / FACET_TILE))
    tw, th = w / nx, strip.H / ny
    rng = random.Random(PATTERN_SEED * 1000 + round(w) + 1)
    pieces: list[list[Part]] = [[] for _ in strip.segs]

    def facets_in(seg: _Seg, corners: list[tuple[float, float]], apex: tuple[float, float, float]) -> tuple:
        cs = [seg.local(u, y, strip.h0) for u, y in corners]
        ap = seg.local(apex[0], apex[1], strip.h0, apex[2])
        normals = []
        for a, b in zip(cs, cs[1:] + cs[:1], strict=True):
            n = (b - a).cross(ap - a).normalized()
            normals.append((a, n if n.Z > 0 else -n))
        return cs, normals

    for j in range(ny):
        for i in range(nx):
            u, y = strip.ua + i * tw, j * th
            corners = [(u, y), (u + tw, y), (u + tw, y + th), (u, y + th)]
            segs = [k for k in range(len(strip.segs)) if strip.near(k, u, u + tw, pad=0.0)]
            depth = rng.uniform(*FACET_DEPTH)
            for attempt in range(60):
                apex = (u + rng.uniform(0.25, 0.75) * tw, y + rng.uniform(0.35, 0.85) * th, -depth)
                if all(n.Y <= PATTERN_MAX_UP for k in segs for _, n in facets_in(strip.segs[k], corners, apex)[1]):
                    break
                if attempt % 10 == 9:
                    depth *= 0.85
            else:
                continue
            ratio = max(
                _rebate_depth_ratio(strip.segs[k], *facets_in(strip.segs[k], corners, apex), depth) for k in segs
            )
            if ratio > 0 and depth * ratio > RIM_WALL - MIN_WALL:
                depth = (RIM_WALL - MIN_WALL) / ratio
                apex = (apex[0], apex[1], -depth)
            for k in segs:
                cs, normals = facets_in(strip.segs[k], corners, apex)
                prism = Pos(0, 0, -2) * extrude(Polygon(*[(c.X, c.Y) for c in cs], align=None), amount=3)
                for a, n in normals:
                    prism &= Location(Plane(origin=a, z_dir=n)) * Box(BIG, BIG, BIG, align=ABOVE)
                pieces[k].append(prism)
    cut = Part()
    for k, seg in enumerate(strip.segs):
        if pieces[k]:
            cut += seg.loc * (Part(Compound(pieces[k]).wrapped) & strip.clip(k))
    return cut


MAKERS = {"voronoi": _voronoi, "facets": _facets}
FULL_MAKERS = {"voronoi": _voronoi_full, "facets": _facets_full}


def is_full(pattern: Pattern) -> bool:
    """A ``-full`` variant: the whole flat side instead of a band."""
    return pattern.endswith("-full")


def skin_pattern(lay: Layout, pattern: Pattern) -> Part | None:
    """The cutter of ``pattern`` over the front and side faces of the top case (None for fuzzy)."""
    base = pattern.removesuffix("-full")
    if base not in MAKERS:
        return None
    if is_full(pattern):  # one continuous strip: front, sides and the front corner rounds
        return FULL_MAKERS[base](lay)
    cut = Part()
    for face in _faces(lay):
        cut += face.loc * (MAKERS[base](face) & face.clip())
    return cut


def fuzzy_modifier(lay: Layout, full: bool = False) -> Part:
    """Slicer modifier for ``fuzzy``: a FUZZY_SKIN-thick shell inside the front and side walls of the
    top case, between the rebate and the top bevel, clear of the back (USB-C). Load it as a modifier
    with fuzzy skin on: only the perimeters it encloses get fuzzed."""
    t = math.radians(TILT)
    top = (lay.h_front - SPLIT_FRONT_Z) * math.cos(t)
    skin = outline(lay, -0.5) - outline(lay, FUZZY_SKIN)
    if full:  # the whole flat side, rim round to top bevel
        band = between(lay, RIM_R + 0.2, top - TOP_EDGE - 0.2)
    else:
        band = between(lay, REBATE_H + 0.3, top - TOP_EDGE - 0.4)
    back = Pos(0, lay.depth / 2 - R_CORNER - 0.5, 0) * Box(BIG, BIG, BIG, align=(Align.CENTER, Align.MIN, Align.CENTER))
    return (skin & band) - back
