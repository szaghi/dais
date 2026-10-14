"""Geometric acceptance tests: printability, fits, and golden-volume regression guards."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import pytest
from build123d import Align, Box, Cylinder, Part, Pos, Vector
from conftest import BOARD, Built, build_all

from dais import params, seat
from dais.designs import DESIGNS, check
from dais.display import make_keycap
from dais.layout import Layout, between
from dais.params import (
    ARTISAN_TOP,
    BOARDS,
    FUNNEL_BOTTOM,
    LEGACY,
    MIN_WALL,
    PATTERNS,
    PLATE_RELIEF,
    REBATE_H,
    RIM_WALL,
    SW_CUT,
    TILT,
    USB_KEEPOUT,
    WALL,
    Options,
)
from dais.parts import make_coupon
from dais.patterns import MAKERS, fuzzy_modifier, notch_top, notch_width, skin_pattern
from dais.shell import outline
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
        h = (c - Vector(0, lay.key_y, lay.key_z)).dot(up)
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


SPLIT_DESIGNS = [n for n, d in DESIGNS.items() if d.split]
ARTISAN = 19.0  # widest in its lower 4-5 mm (calipers)
ARTISAN_REST = 8.0  # its base above the plate top, key up


@pytest.mark.parametrize("pattern", ["voronoi", "facets", "voronoi-full", "facets-full"])
@pytest.mark.parametrize("name", SPLIT_DESIGNS)
def test_patterns_build_and_print_without_supports(name: str, pattern: str) -> None:
    opt = Options(pattern=pattern)
    d = DESIGNS[name]
    lay, parts = d.layout(BOARD, opt), d.build(BOARD, opt)  # build() runs check(): valid, one solid, no clash
    plain = d.parts(d.layout(BOARD))["top-case"]
    assert parts["top-case"].volume < plain.volume - 50  # the relief really is cut
    assert [o for o in _overhangs(parts["top-case"], lay) if not _is_seat_ring(o)] == []


@pytest.mark.parametrize("pattern", ["voronoi", "facets", "voronoi-full", "facets-full"])
@pytest.mark.parametrize("name", ["split", "plinth"])
def test_patterns_leave_min_wall(name: str, pattern: str) -> None:
    """No relief deeper than the wall allows: MIN_WALL left everywhere, also over the thin rebate."""
    lay = DESIGNS[name].layout(BOARD, Options(pattern=pattern))
    cut = skin_pattern(lay, pattern)
    rebate = outline(lay, RIM_WALL - MIN_WALL + 0.01) & between(lay, -1.0, REBATE_H)
    for zone in (rebate, outline(lay, WALL - MIN_WALL + 0.01)):
        deep = cut & zone
        assert not deep.solids() or deep.volume < 1e-3


@pytest.mark.parametrize("full", [False, True])
def test_fuzzy_is_a_slicer_modifier_only(full: bool) -> None:
    d = DESIGNS["split"]
    lay = d.layout(BOARD, Options(pattern="fuzzy-full" if full else "fuzzy"))
    top = d.parts(lay)["top-case"]
    assert top.volume == pytest.approx(d.parts(d.layout(BOARD))["top-case"].volume, rel=1e-9)  # geometry unchanged
    mod = fuzzy_modifier(lay, full)
    assert mod.is_valid and len(mod.solids()) == 1
    assert (mod & top).volume > 1000  # it encloses the outer walls...
    box = mod.bounding_box()
    assert box.max.Z < lay.h_back - 0.5  # ...not the top face
    if full:  # all four walls, clear of the USB-C notch
        assert box.max.Y > lay.depth / 2 - 0.1
        assert (mod & _notch_zone(lay)).volume < 1e-3
    else:  # front and sides only
        assert box.max.Y < lay.depth / 2 - 1


def _notch_zone(lay: Layout) -> Part:
    """The USB-C plug notch grown by USB_KEEPOUT - 0.1, in the back wall (not the air outside it)."""
    m = USB_KEEPOUT - 0.1
    return Pos(0, lay.depth / 2 - WALL / 2, -1) * Box(
        notch_width(lay) + 2 * m, WALL, notch_top(lay) + m + 1, align=params.MIN
    )


@pytest.mark.parametrize("pattern", ["voronoi-full", "facets-full"])
def test_full_patterns_wrap_the_back_clear_of_the_usb(pattern: str) -> None:
    lay = DESIGNS["split"].layout(BOARD, Options(pattern=pattern))
    cut = skin_pattern(lay, pattern)
    back = Pos(0, lay.depth / 2, 0) * Box(lay.width - 8, 2 * WALL, 400)
    assert (cut & back).volume > 20  # the back wall is textured...
    assert (cut & _notch_zone(lay)).volume < 1e-3  # ...but not round the plug notch


@pytest.mark.parametrize("name", ["plinth", "plinth-long"])
def test_artisan_sits_on_the_plinth_and_travels_into_it(built: Built, name: str) -> None:
    """The top face just under the artisan's base, and the hole clear of it over the full travel."""
    lay, parts = built[name]
    assert ARTISAN_TOP < ARTISAN_REST < ARTISAN_TOP + 1.0
    for drop in (0.0, 2.0, 4.0):
        base = lay.key * Pos(0, 0, ARTISAN_REST - drop) * Box(ARTISAN, ARTISAN, 6.0, align=params.MIN)
        assert base.distance_to(parts["top-case"]) > 0.4, drop  # 0.6 on the flats, 0.43 at the R1 corners


def test_patterns_list() -> None:
    assert set(PATTERNS) == {f"{p}{suffix}" for p in ("fuzzy", *MAKERS) for suffix in ("", "-full")}


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


SEAT_EXTREMES = [  # (length, width, PCB thickness): the clamp's two travel ends and the microSAM
    (params.SEAT_LEN[1], params.SEAT_W[1], params.SEAT_PCB_T[1]),
    (params.SEAT_LEN[0], params.SEAT_W[0], params.SEAT_PCB_T[0]),
    (34.6, 18.4, 1.6),
]


def _pcb(lay: Layout, board: params.Board) -> Part:
    """The PCB envelope where the seat puts ``board``."""
    back = seat.board_back(lay.depth, board)
    return Pos(0, back - board.length / 2, seat.Z0) * Box(board.width, board.length, board.pcb_t, align=params.MIN)


@pytest.mark.parametrize("dims", SEAT_EXTREMES)
@pytest.mark.parametrize("name", SPLIT_DESIGNS)
def test_generic_seat_holds_every_board(built: Built, name: str, dims: tuple[float, float, float]) -> None:
    """Over the whole range: the PCB touches the rear jaws and the clamp without overlapping
    anything, the clamp clears both shells and the clamp screw lands inside the floor slot."""
    lay, parts = built[name]
    board = replace(lay.board, length=dims[0], width=dims[1], pcb_t=dims[2])
    pcb, clamp = _pcb(lay, board), seat.make_clamp(lay.depth, board)
    for part in (parts["bottom-case"], parts["top-case"]):
        assert (pcb & part).volume < 1e-3 and (clamp & part).volume < 1e-3
    assert (pcb & clamp).volume < 1e-3
    assert pcb.distance_to(clamp) < 0.02  # the clamp's horns touch the front corners...
    jaws, _ = seat.rear_jaws(lay.depth)
    assert pcb.distance_to(jaws) < 0.02  # ...and push the back corners into the jaws
    y = seat.clamp_y(lay.depth, board) - seat.CLAMP_SCREW
    screw = Pos(0, y, -1) * Cylinder(1.5, params.BOTTOM_T + 2, align=params.MIN)
    assert (screw & parts["bottom-case"]).volume < 1e-3  # the M3 passes through the slot


@pytest.mark.parametrize("name", SPLIT_DESIGNS)
def test_usb_window_clears_the_plug_and_has_no_bridge(built: Built, name: str) -> None:
    """The plug overmold, round the lowest and the highest receptacle of the range, passes through
    the back wall from the nearest receptacle face: no material of either shell in the way."""
    lay, parts = built[name]
    lo, hi = seat.window_z()
    w = 2 * seat.window_half_width() - 0.1
    plug = Pos(0, lay.depth / 2 - params.WALL - 0.5, lo + 0.05) * Box(
        w, params.WALL + 2, hi - lo - 0.1, align=(Align.CENTER, Align.MIN, Align.MIN)
    )
    for part in ("bottom-case", "top-case"):
        assert (plug & parts[part]).volume < 1e-3, part


def test_split_layout_rejects_a_board_outside_the_seat() -> None:
    with pytest.raises(ValueError, match="outside the split seat"):
        Layout.for_board(BOARDS["rp2040zero"], split=True)
    Layout.for_board(BOARDS["rp2040zero"], split=True, opt=Options(seat="pocket"))  # the fitted pocket takes it


if __name__ == "__main__":
    for which, opt in (("default", Options()), ("legacy", LEGACY)):
        GOLDEN[which].write_text(json.dumps(_volumes(build_all(opt)), indent=1) + "\n")
        print(f"wrote {GOLDEN[which]}")
