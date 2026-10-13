"""Display-only models for the photo renders: a Cherry-profile keycap and an MX switch top housing.

Not printed and not part of the fit checks; the line drawings keep using plain envelopes.
"""

from __future__ import annotations

from build123d import Box, Cylinder, Part, Plane, Pos, RectangleRounded, Rot, loft

from .layout import Layout
from .params import MIN

CAP_LIFT = 5.6  # keycap bottom above the plate top, key up
CAP_BOTTOM = 18.0  # 1U skirt
CAP_TOP = (12.6, 14.0)  # top face, X x Y
CAP_H = 9.0  # Cherry-profile height, roughly
CAP_WALL = 1.2
DISH = 0.6  # cylindrical dish depth (axis front-to-back)
SW_TOP = 15.6  # MX top housing base
SW_TOP_TOP = 10.0  # housing top face
SW_TOP_H = 6.6  # housing height above the plate


def _frustum(
    bottom: tuple[float, float], top: tuple[float, float], h: float, r_bot: float, r_top: float, z0: float = 0.0
) -> Part:
    """Loft between two rounded rectangles: ``bottom`` at ``z0``, ``top`` at ``z0 + h``."""
    lo = Plane.XY.offset(z0) * RectangleRounded(*bottom, r_bot)
    hi = Plane.XY.offset(z0 + h) * RectangleRounded(*top, r_top)
    return loft([lo, hi])


def make_keycap(lay: Layout) -> Part:
    """Hollow 1U keycap with a cylindrical dish, seated on the switch in the key frame."""
    outer = _frustum((CAP_BOTTOM, CAP_BOTTOM), CAP_TOP, CAP_H, 1.0, 2.0)
    inner = _frustum(
        (CAP_BOTTOM - 2 * CAP_WALL, CAP_BOTTOM - 2 * CAP_WALL),
        (CAP_TOP[0] - 2 * CAP_WALL, CAP_TOP[1] - 2 * CAP_WALL),
        CAP_H - CAP_WALL - DISH,
        0.6,
        1.2,
        z0=-0.01,
    )
    half = CAP_TOP[0] / 2
    r = (half**2 + DISH**2) / (2 * DISH)  # dish radius from its sagitta over the top width
    dish = Pos(0, 0, CAP_H - DISH + r) * Rot(90, 0, 0) * Cylinder(r, 40)
    cap = outer - inner - dish
    return lay.key * Pos(0, 0, CAP_LIFT) * cap


def make_switch_top(lay: Layout) -> Part:
    """MX top housing above the plate, with the cross stem stub (hidden under the cap)."""
    housing = _frustum((SW_TOP, SW_TOP), (SW_TOP_TOP, SW_TOP_TOP), SW_TOP_H, 0.8, 0.8)
    stem = Pos(0, 0, SW_TOP_H) * (Box(4.0, 1.3, 1.5, align=MIN) + Box(1.1, 4.0, 1.5, align=MIN))
    return lay.key * (housing + stem)
