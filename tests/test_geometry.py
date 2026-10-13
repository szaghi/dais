"""Geometric acceptance tests: printability, fits, and golden-volume regression guards."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import pytest
from build123d import Box, Cylinder, Part, Pos, Vector
from conftest import BOARD, Built, build_all

from dais import params
from dais.designs import DESIGNS, check
from dais.display import make_keycap
from dais.layout import Layout
from dais.params import BOARDS, FUNNEL_BOTTOM, LEGACY, PATTERNS, PLATE_RELIEF, SW_CUT, TILT, Options
from dais.parts import make_coupon
from dais.split import split_bosses

GOLDEN = {
    "default": Path(__file__).with_name("golden_volumes.json"),
    "legacy": Path(__file__).with_name("golden_volumes_legacy.json"),
}
SEAT_RING = FUNNEL_BOTTOM**2 - SW_CUT**2  # the switch seat: the one horizontal overhang allowed


def _overhangs(part: Part, lay: Layout, max_angle: float = 45.0) -> list[tuple[float, float]]:
    """Faces facing the bed when printed top down, below the top face: (height along the key normal, area)."""
    t = math.radians(TILT)
    up = Vector(0, -math.sin(t), math.cos(t))
    found = []
    for f in part.faces():
        c = f.center()
        h = (c - Vector(0, 0, lay.key_z)).dot(up)
        if f.normal_at(c).dot(up) > math.cos(math.radians(max_angle)) + 1e-6 and h < 3.5 and f.area > 0.05:
            found.append((round(h, 2), round(f.area, 2)))
    return found


def _is_seat_ring(oh: tuple[float, float]) -> bool:
    """The integrated plate's switch seat: at the plate top, FUNNEL_BOTTOM^2 - SW_CUT^2 in area,
    a (FUNNEL_BOTTOM - SW_CUT) / 2 = 0.9 mm horizontal overhang -- short enough to print unsupported."""
    return abs(oh[0]) < 0.05 and abs(oh[1] - SEAT_RING) < 0.5


def _volumes(built: Built) -> dict[str, float]:
    got = {f"{n}/{p}": s.volume for n, (_, parts) in built.items() for p, s in parts.items()}
    got["coupon"] = make_coupon().volume
    return got


@pytest.mark.parametrize("which", ["default", "legacy"])
def test_golden_volumes(built: Built, built_legacy: Built, which: str) -> None:
    """Every part keeps its volume: an unintended geometry change fails here. The legacy set pins
    the first prototypes, so new options can never disturb them.

    After an intended change, regenerate with ``python tests/test_geometry.py``.
    """
    golden = json.loads(GOLDEN[which].read_text())
    got = _volumes(built if which == "default" else built_legacy)
    assert got.keys() == golden.keys()
    for key, vol in golden.items():
        assert got[key] == pytest.approx(vol, rel=1e-9), key


@pytest.mark.parametrize("name", list(DESIGNS))
def test_top_shell_prints_without_supports(built: Built, name: str) -> None:
    lay, parts = built[name]
    shell = parts["top-case" if DESIGNS[name].split else "body"]
    found = [o for o in _overhangs(shell, lay) if not _is_seat_ring(o)]
    if DESIGNS[name].split:
        assert found == []
    else:
        assert len(found) == 1 and found[0][1] < 10.0  # the one-piece body's USB-C slot roof, bridged
    assert (FUNNEL_BOTTOM - SW_CUT) / 2 <= 1.0


@pytest.mark.parametrize("pattern", PATTERNS)
@pytest.mark.parametrize("name", ["split", "split-trapezoid"])
def test_patterns_build_and_print_without_supports(name: str, pattern: str) -> None:
    opt = Options(pattern=pattern)
    d = DESIGNS[name]
    lay, parts = d.layout(BOARD, opt), d.build(BOARD, opt)  # build() runs check(): valid, one solid, no clash
    plain = d.parts(d.layout(BOARD))["top-case"]
    assert parts["top-case"].volume < plain.volume - 50  # the relief really is cut
    assert [o for o in _overhangs(parts["top-case"], lay) if not _is_seat_ring(o)] == []


@pytest.mark.parametrize("name", list(DESIGNS))
def test_pressed_keycap_clears_the_funnel(built: Built, name: str) -> None:
    lay, parts = built[name]
    shell = parts["top-case" if DESIGNS[name].split else "body"]
    pressed = lay.key * Pos(0, 0, -4.0) * lay.key.inverse() * make_keycap(lay)  # full 4 mm travel
    assert pressed.distance_to(shell) > 0.3


def test_insert_holes_have_wall() -> None:
    fast = Options().fast
    assert fast.boss_r - fast.hole_d / 2 >= 1.9 and fast.top_boss_r - fast.hole_d / 2 >= 1.9
    assert fast.head_d / 2 < fast.boss_r  # the counterbore stays inside the bottom-case column


def test_legacy_plate_relief_clears_every_body_boss(built_legacy: Built) -> None:
    lay, parts = built_legacy["side-cove"]
    for x, y in lay.bosses:  # all four: one OCC cut once dropped silently at a single corner
        grown = Pos(x, y, 0) * Cylinder(lay.opt.fast.boss_r + PLATE_RELIEF - 0.01, 400)
        assert (parts["plate"] & grown).volume == pytest.approx(0.0, abs=1e-6), (x, y)


@pytest.mark.parametrize("name", ["split", "split-trapezoid"])
def test_legacy_split_columns_clear_the_plate(built_legacy: Built, name: str) -> None:
    lay, parts = built_legacy[name]
    roof = lay.key * Pos(0, 0, -0.01) * Box(400, 400, 400, align=params.MAX)
    assert parts["plate"].distance_to(parts["top-case"] & roof) > 1.0


def test_integrated_plate_has_no_separate_part(built: Built) -> None:
    assert all("plate" not in parts for _, parts in built.values())


def test_split_screw_axes_follow_the_trapezoid() -> None:
    rect = DESIGNS["split"].layout(BOARD)
    trap = DESIGNS["split-trapezoid"].layout(BOARD)
    assert split_bosses(trap)[0][0] < split_bosses(rect)[0][0]  # front screws move out with the wider front


def test_check_rejects_a_clash() -> None:
    with pytest.raises(RuntimeError, match="intersect"):
        check({"a": Part() + Box(10, 10, 10), "b": Part() + Pos(5, 0, 0) * Box(10, 10, 10)})


def test_layout_rejects_a_board_too_wide() -> None:
    with pytest.raises(ValueError, match="too wide"):
        Layout.for_board(replace(BOARDS["microsam"], width=40.0))


if __name__ == "__main__":
    for which, opt in (("default", Options()), ("legacy", LEGACY)):
        GOLDEN[which].write_text(json.dumps(_volumes(build_all(opt)), indent=1) + "\n")
        print(f"wrote {GOLDEN[which]}")
