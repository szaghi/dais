"""Hidden-line SVG views of every design, for the documentation.

Writes ``<out>/<design>/<view>.svg`` (the same view set for every design, plus the seam
close-up of the split designs) and ``<out>/common/{plate,coupon}.svg``. The switch, keycap,
board and USB-C are envelope DUMMIES (plain boxes) for checking fit; they are not printed parts.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from build123d import Align, Box, Compound, ExportSVG, LineType, Pos, Shape

from .designs import DESIGNS
from .layout import Layout
from .params import BOTTOM_T, MAX, MIN, POCKET_D, SPLIT_FRONT_Z, SW_BELOW, SW_PINS
from .parts import make_coupon, make_plate

log = logging.getLogger(__name__)

SW_TOP_H = 6.6  # MX upper housing above the plate
CAP_LIFT = 5.6  # keycap bottom above the plate top, key up
CAP_H = 22.0  # keycap envelope height (1U, 18 x 18; tall enough for an artisan)
EXPLODE = 24.0
BACKGROUND = "#f4f1ea"  # warm off-white card behind each view
PX_PER_MM = 6.0  # display size of the SVGs

Vec = tuple[float, float, float]

# view: (eye, target, up, hidden lines)
VIEWS: dict[str, tuple[Vec, Vec, Vec, bool]] = {
    "assembled": ((-150.0, -190.0, 120.0), (0.0, 0.0, 12.0), (0, 0, 1), False),
    "detail": ((190.0, -150.0, 45.0), (0.0, 0.0, 12.0), (0, 0, 1), False),  # low three-quarter
    "front": ((0.0, -300.0, 12.0), (0.0, 0.0, 12.0), (0, 0, 1), False),
    "side": ((300.0, 0.0, 12.0), (0.0, 0.0, 12.0), (0, 0, 1), False),
    "back": ((140.0, 200.0, 80.0), (0.0, 0.0, 12.0), (0, 0, 1), False),
    "plan": ((0.0, 0.0, 300.0), (0.0, 0.0, 0.0), (0, 1, 0), False),
    "exploded": ((-150.0, -190.0, 120.0), (0.0, 0.0, 30.0), (0, 0, 1), False),
    "section": ((300.0, 0.0, 12.0), (0.0, 0.0, 12.0), (0, 0, 1), True),
    "underside": ((-120.0, -150.0, -130.0), (0.0, 0.0, 12.0), (0, 0, 1), False),
    "base-board": ((-150.0, -190.0, 160.0), (0.0, 0.0, 5.0), (0, 0, 1), False),
}


def dummies(lay: Layout) -> dict[str, Shape]:
    """Envelope solids for the non-printed parts, in assembly position."""
    b = lay.board
    bz = BOTTOM_T - POCKET_D
    usb_l = 7.35
    key = lay.key
    return {
        "pcb": Pos(0, lay.board_back - b.length / 2, bz) * Box(b.width, b.length, b.pcb_t, align=MIN),
        "usb": Pos(0, lay.board_back + b.usb_overhang - usb_l / 2, bz + b.pcb_t)
        * Box(b.usb_w, usb_l, b.usb_h, align=MIN),
        "sw_top": key * Box(15.6, 15.6, SW_TOP_H, align=MIN),
        "sw_bot": key * Box(13.9, 13.9, SW_BELOW, align=MAX),
        "sw_pin": key * Pos(0, 0, -SW_BELOW) * Box(1.5, 1.0, SW_PINS, align=MAX),
        "cap": key * Pos(0, 0, CAP_LIFT) * Box(18, 18, CAP_H, align=MIN),
    }


def write_svg(
    shapes: list[Shape], path: Path, eye: Vec, target: Vec, hidden: bool = False, up: Vec = (0, 0, 1)
) -> None:
    """Hidden-line projection of ``shapes`` seen from ``eye`` towards ``target``."""
    exp = ExportSVG(scale=5, line_weight=0.3)
    exp.add_layer("hidden", line_color=0xB4B4B4, line_type=LineType.ISO_DOT, line_weight=0.15)
    exp.add_layer("visible", line_color=0x202020, line_weight=0.35)
    origin = tuple(e - t for e, t in zip(eye, target, strict=True))
    vis, hid = Compound(children=shapes).project_to_viewport(origin, viewport_up=up)
    if hidden:
        exp.add_shape(hid, layer="hidden")
    exp.add_shape(vis, layer="visible")
    path.parent.mkdir(parents=True, exist_ok=True)
    exp.write(str(path))
    _add_background(path)
    log.info("wrote %s", path)


def _add_background(path: Path, pad_frac: float = 0.04) -> None:
    """Pad the viewBox and put a light rounded card behind the drawing.

    Dark strokes on a transparent canvas vanish on dark themes; a filled card reads the same
    on any background (unlike prefers-color-scheme CSS, which many SVG viewers ignore).
    """
    svg = path.read_text(encoding="utf-8")
    m = re.search(r'viewBox="([-\d.e]+) ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)"', svg)
    if m is None:
        raise RuntimeError(f"{path}: no viewBox")
    x, y, w, h = map(float, m.groups())
    pad = pad_frac * max(w, h)
    x, y, w, h = x - pad, y - pad, w + 2 * pad, h + 2 * pad
    svg = svg.replace(m.group(0), f'viewBox="{x:g} {y:g} {w:g} {h:g}"', 1)
    size = f'width="{w * PX_PER_MM:.0f}px" height="{h * PX_PER_MM:.0f}px"'
    svg = re.sub(r'width="[^"]*" height="[^"]*"', size, svg, count=1)
    card = f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{pad:g}" fill="{BACKGROUND}"/>'
    svg = re.sub(r"(<svg [^>]*>)", rf"\1\n  {card}", svg, count=1)
    path.write_text(svg, encoding="utf-8")


def render_design(board: str, name: str, out: str) -> str:
    """Write the standard view set of one design, plus its close-ups."""
    design = DESIGNS[name]
    lay = design.layout(board)
    parts = design.build(board)
    split = "top-case" in parts
    shell = parts["top-case" if split else "body"]
    base = parts["bottom-case" if split else "bottom"]
    plate, feet = parts["plate"], parts["feet"]
    d = dummies(lay)
    switch = [d["sw_top"], d["cap"]]
    case = [shell, base, feet]
    half = Pos(-100, 0, 0) * Box(200, 200, 200)  # keep x < 0
    lift = Pos(0, 0, EXPLODE)
    scenes: dict[str, list[Shape]] = {
        "assembled": [*case, *switch],
        "detail": [*case, *switch],
        "front": [*case, *switch],
        "side": [*case, *switch],
        "back": [*case, *switch],
        "plan": case,
        "exploded": [lift * lift * s for s in switch]
        + [lift * lift * shell, lift * plate, d["pcb"], d["usb"], base, Pos(0, 0, -EXPLODE / 2) * feet],
        "section": [
            s & half
            for s in (shell, base, plate, feet, d["pcb"], d["usb"], d["sw_top"], d["sw_bot"], d["sw_pin"], d["cap"])
        ],
        "underside": [shell],
        "base-board": [base, d["pcb"], d["usb"]],
    }
    directory = Path(out) / name
    for view, shapes in scenes.items():
        eye, target, up, hidden = VIEWS[view]
        write_svg(shapes, directory / f"{view}.svg", eye, target, hidden, up)
    if split:
        # close-up of the seam: front wall cut at x = 0, seen from +X
        zf = SPLIT_FRONT_Z + 3.0  # window centred a little above the seam
        win = Pos(-50, -lay.depth / 2 - 1, zf - 6) * Box(100, 9, 12, align=(Align.CENTER, Align.MIN, Align.MIN))
        write_svg(
            [s & half & win for s in (shell, base)],
            directory / "seam.svg",
            (300.0, -lay.depth / 2 + 3, zf),
            (0.0, -lay.depth / 2 + 3, zf),
        )
    return name


def render_all(board: str, out: Path, names: list[str], jobs: int | None = None) -> None:
    """Render the selected designs in parallel, then the shared parts."""
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for name in pool.map(render_design, [board] * len(names), names, [str(out)] * len(names)):
            log.info("rendered %s", name)
    plate = make_plate(DESIGNS["side-cove"].layout(board))
    write_svg([plate], out / "common" / "plate.svg", (0.0, 0.0, 300.0), (0.0, 0.0, 0.0), up=(0, 1, 0))
    write_svg([make_coupon()], out / "common" / "coupon.svg", (0.0, 0.0, 200.0), (31.5, 0.0, 0.0), up=(0, 1, 0))
