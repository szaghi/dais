"""Geometric acceptance tests: printability, fits, and a golden-volume regression guard."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import pytest
from build123d import Box, Cylinder, Part, Pos, Vector

from dais import params
from dais.designs import DESIGNS, check
from dais.layout import Layout
from dais.params import BOARDS, BOSS_R, PLATE_RELIEF, TILT
from dais.parts import make_coupon
from dais.split import split_bosses

GOLDEN = Path(__file__).with_name("golden_volumes.json")


def _overhangs(part: Part, lay: Layout, max_angle: float = 45.0) -> list[tuple[float, float]]:
    """Faces facing the bed when printed top down, below the roof: (height along the key normal, area)."""
    t = math.radians(TILT)
    up = Vector(0, -math.sin(t), math.cos(t))
    found = []
    for f in part.faces():
        c = f.center()
        h = (c - Vector(0, 0, lay.key_z)).dot(up)
        if f.normal_at(c).dot(up) > math.cos(math.radians(max_angle)) + 1e-6 and h < 3.5 and f.area > 0.05:
            found.append((round(h, 2), round(f.area, 2)))
    return found


def test_golden_volumes(built: dict) -> None:
    """Every part keeps its volume: an unintended geometry change fails here.

    After an intended change, regenerate with ``python tests/test_geometry.py``.
    """
    golden = json.loads(GOLDEN.read_text())
    got = {f"{n}/{p}": s.volume for n, (_, parts) in built.items() for p, s in parts.items()}
    got["coupon"] = make_coupon().volume
    assert got.keys() == golden.keys()
    for key, vol in golden.items():
        assert got[key] == pytest.approx(vol, rel=1e-9), key


@pytest.mark.parametrize("name", ["split", "split-trapezoid"])
def test_top_case_prints_without_supports(built: dict, name: str) -> None:
    lay, parts = built[name]
    assert _overhangs(parts["top-case"], lay) == []


@pytest.mark.parametrize("name", ["side-cove", "wrap-cove"])
def test_body_only_overhang_is_the_usb_bridge(built: dict, name: str) -> None:
    lay, parts = built[name]
    found = _overhangs(parts["body"], lay)
    assert len(found) == 1 and found[0][1] < 10.0  # the receptacle slot roof, bridged


def test_plate_relief_clears_every_body_boss(built: dict) -> None:
    lay, parts = built["side-cove"]
    for x, y in lay.bosses:  # all four: one OCC cut once dropped silently at a single corner
        grown = Pos(x, y, 0) * Cylinder(BOSS_R + PLATE_RELIEF - 0.01, 400)
        assert (parts["plate"] & grown).volume == pytest.approx(0.0, abs=1e-6), (x, y)


@pytest.mark.parametrize("name", ["split", "split-trapezoid"])
def test_split_columns_clear_the_plate(built: dict, name: str) -> None:
    lay, parts = built[name]
    roof = lay.key * Pos(0, 0, -0.01) * Box(400, 400, 400, align=params.MAX)
    assert parts["plate"].distance_to(parts["top-case"] & roof) > 1.0


def test_split_screw_axes_follow_the_trapezoid() -> None:
    rect = DESIGNS["split"].layout("microsam")
    trap = DESIGNS["split-trapezoid"].layout("microsam")
    front_r, front_t = split_bosses(rect)[0], split_bosses(trap)[0]
    assert front_t[0] < front_r[0]  # front screws move out with the wider front


def test_check_rejects_a_clash() -> None:
    with pytest.raises(RuntimeError, match="intersect"):
        check({"a": Part() + Box(10, 10, 10), "b": Part() + Pos(5, 0, 0) * Box(10, 10, 10)})


def test_layout_rejects_a_board_too_wide() -> None:
    with pytest.raises(ValueError, match="too wide"):
        Layout.for_board(replace(BOARDS["microsam"], width=40.0))


if __name__ == "__main__":
    vols = {}
    for n, d in DESIGNS.items():
        for p, s in d.build("microsam").items():
            vols[f"{n}/{p}"] = s.volume
    vols["coupon"] = make_coupon().volume
    GOLDEN.write_text(json.dumps(vols, indent=1) + "\n")
    print(f"wrote {GOLDEN}")
