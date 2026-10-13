"""The design registry: every printable variant, the parts it is made of, and the fit checks.

Each design builds a complete, self-contained part set in assembly position; the shared parts
(plate, feet, bottom plate) are built per design so that each output directory prints alone.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from build123d import Part

from .layout import Layout
from .one_piece import Cove, make_body
from .params import BOARDS, TRAP_FRONT_EXTRA, Options
from .parts import make_bottom, make_feet, make_plate
from .split import make_bottom_case, make_top_case


@dataclass(frozen=True)
class Design:
    """A printable variant of the case."""

    name: str  # output directory and docs slug
    title: str
    summary: str
    front_extra: float  # 0: rectangular plan; > 0: trapezoid, front wider than the back
    parts: Callable[[Layout], dict[str, Part]]

    def layout(self, board: str, opt: Options | None = None) -> Layout:
        """Layout of this design for ``board`` built with ``opt`` (default: ``Options()``)."""
        return Layout.for_board(BOARDS[board], front_extra=self.front_extra, opt=opt)

    @property
    def split(self) -> bool:
        """Top case + bottom case (pattern-capable), as opposed to a one-piece body."""
        return self.parts is _split

    def build(self, board: str, opt: Options | None = None) -> dict[str, Part]:
        """All printed parts in assembly position, checked for validity and clashes."""
        parts = self.parts(self.layout(board, opt))
        check(parts)
        return parts


def _one_piece(cove: Cove) -> Callable[[Layout], dict[str, Part]]:
    def parts(lay: Layout) -> dict[str, Part]:
        parts = {"body": make_body(lay, cove), "bottom": make_bottom(lay)}
        return _with_plate_and_feet(parts, lay)

    return parts


def _split(lay: Layout) -> dict[str, Part]:
    parts = {"top-case": make_top_case(lay), "bottom-case": make_bottom_case(lay)}
    return _with_plate_and_feet(parts, lay)


def _with_plate_and_feet(parts: dict[str, Part], lay: Layout) -> dict[str, Part]:
    """Add the shared parts: the switch plate only when it is not integrated in the top shell."""
    if lay.opt.plate == "separate":
        parts["plate"] = make_plate(lay)
    parts["feet"] = make_feet(lay)
    return parts


DESIGNS: dict[str, Design] = {
    d.name: d
    for d in (
        Design(
            "side-cove",
            "Side coves",
            "one-piece wedge, a teardrop ball-cutter cove centred on each side",
            0.0,
            _one_piece("side"),
        ),
        Design(
            "wrap-cove",
            "Wrap cove",
            "one-piece wedge, one continuous cove along the front, round the corners and down each side",
            0.0,
            _one_piece("wrap"),
        ),
        Design(
            "split",
            "Split case",
            "top case over an inset bottom case, parted 2 mm above the bottom; the seam is the feature",
            0.0,
            _split,
        ),
        Design(
            "split-trapezoid",
            "Split case, trapezoidal plan",
            "the split case with a front 10 mm wider than the back",
            TRAP_FRONT_EXTRA,
            _split,
        ),
    )
}


def check(parts: dict[str, Part]) -> None:
    """Every part a valid single solid (feet excepted), no two parts intersecting.

    Raises
    ------
    RuntimeError
        On an invalid solid, a floating feature or a clash.
    """
    for name, part in parts.items():
        if not part.is_valid:
            raise RuntimeError(f"{name}: invalid solid")
        if len(part.solids()) != 1 and name != "feet":
            raise RuntimeError(f"{name}: {len(part.solids())} disjoint solids (floating feature)")
    names = list(parts)
    for i, a in enumerate(names):
        for c in names[i + 1 :]:
            clash = (parts[a] & parts[c]).volume
            if clash > 1e-3:
                raise RuntimeError(f"{a} and {c} intersect: {clash:.3f} mm^3")


Variant = tuple[str, Options, str]  # design name, options, output name


def variants(names: list[str], opt: Options, patterns: list[str | None]) -> list[Variant]:
    """Every requested design x pattern; patterns apply to the split designs only.

    The output name is the design name, suffixed with the pattern when there is one.
    """
    out: list[Variant] = []
    for pattern in patterns:
        for name in names:
            if pattern and not DESIGNS[name].split:
                continue
            out.append((name, replace(opt, pattern=pattern), f"{name}-{pattern}" if pattern else name))
    return out
