"""Command line: ``dais build | render | photo | list | params``."""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing
import re
import shutil
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, fields, replace
from pathlib import Path

from build123d import Part, export_step, export_stl

from .designs import DESIGNS, Variant, variants
from .params import (
    BOARDS,
    FASTENERS,
    FOOT_RECESS,
    FOOT_T,
    LEGACY,
    PATTERNS,
    PLINTH,
    PLINTH_LONG,
    TILT,
    Fastener,
    Look,
    Options,
)
from .parts import make_coupon
from .patterns import fuzzy_modifier, is_full

log = logging.getLogger(__name__)

# spawn, not fork: a forked worker can inherit a lock held by an OpenCascade or fontconfig thread
# of the parent (after any OCC work in-process) and deadlock; spawn starts a clean interpreter
SPAWN = multiprocessing.get_context("spawn")


def export(parts: dict[str, Part], directory: Path) -> None:
    """Write every part as ``stl/<part>.stl`` (slicer) and ``step/<part>.step`` (CAD)."""
    for sub in ("stl", "step"):
        (directory / sub).mkdir(parents=True, exist_ok=True)
    for name, part in parts.items():
        export_stl(part, str(directory / "stl" / f"{name}.stl"))
        export_step(part, str(directory / "step" / f"{name}.step"))


def _build_one(board: str, name: str, opt: Options, dirname: str, out: str) -> str:
    design = DESIGNS[name]
    lay = design.layout(board, opt)
    parts = design.build(board, opt)
    directory = Path(out) / board / dirname
    export(parts, directory)
    if opt.pattern and opt.pattern.startswith("fuzzy"):  # a slicer modifier volume, not a printed part
        export({"modifier-fuzzy-skin": fuzzy_modifier(lay, is_full(opt.pattern))}, directory)
    (directory / "options.json").write_text(json.dumps(asdict(opt), indent=1) + "\n")
    vols = ", ".join(f"{p} {s.volume / 1000:.1f}" for p, s in parts.items())
    return (
        f"{dirname:24} {lay.front_width:.1f} (front) / {lay.width:.1f} (back) x {lay.depth:.1f} mm, "
        f"h {lay.h_front:.1f} -> {lay.h_back:.1f} mm (+{FOOT_T - FOOT_RECESS:.1f} feet), "
        f"tilt {TILT:.0f} deg; cm^3: {vols}"
    )


def options(args: argparse.Namespace) -> Options:
    """Build options from the command line: defaults (or ``--legacy``), then explicit overrides."""
    opt = LEGACY if getattr(args, "legacy", False) else Options()
    overrides = {k: getattr(args, k, None) for k in ("plate", "fastener", "bevel", "seat")}
    return replace(opt, **{k: v for k, v in overrides.items() if v is not None})


def targets(args: argparse.Namespace) -> list[Variant]:
    """(design, options, output name) for every design x pattern asked for."""
    pattern = getattr(args, "pattern", None)
    patterns: list[str | None] = list(PATTERNS) if pattern == "all" else [pattern]
    return variants(args.design or list(DESIGNS), options(args), patterns)


def _describe(opt: Options) -> str:
    return f"plate {opt.plate}, {opt.fast.label}, bevel {opt.bevel:g} deg"


def cmd_build(args: argparse.Namespace) -> None:
    """Build, check and export the selected designs and the switch-fit coupon."""
    root = Path(args.out) / args.board
    if args.clean and root.exists():
        shutil.rmtree(root)
    todo = targets(args)
    log.info("options: %s", _describe(todo[0][1]))
    with ProcessPoolExecutor(max_workers=args.jobs, mp_context=SPAWN) as pool:
        jobs = [pool.submit(_build_one, args.board, n, o, d, args.out) for n, o, d in todo]
        for job in jobs:
            log.info("%s", job.result())
    export({"coupon": make_coupon()}, root / "coupon")
    log.info("-> %s/{%s,coupon}/{stl,step}/", root, ",".join(d for _, _, d in todo))


def cmd_render(args: argparse.Namespace) -> None:
    """Render the documentation views."""
    from .render import render_all

    render_all(args.board, Path(args.out), targets(args), args.jobs)


def cmd_photo(args: argparse.Namespace) -> None:
    """Photo renders through Blender Cycles (CPU only, RAM-capped)."""
    from .photo import photo

    w, h = (800, 600) if args.preview else (1600, 1200)
    photo(
        args.board,
        targets(args),
        Path(args.out),
        Path("out") / args.board / "photo-work",
        threads=args.threads,
        samples=args.samples or (24 if args.preview else 128),
        resolution=(w, h),
        memory=args.memory,
        tiles=args.tiles or (1 if args.preview else 2),
        blender=args.blender,
        only=args.shot,
    )


def cmd_list(_args: argparse.Namespace) -> None:
    """Print the designs."""
    for d in DESIGNS.values():
        print(f"{d.name:16} {d.title}: {d.summary}")


def params_markdown() -> str:
    """The parameter reference page, parsed from the sections and comments of ``params.py``."""
    src = Path(__file__).with_name("params.py").read_text(encoding="utf-8").splitlines()
    lines = [
        "# Parameters",
        "",
        "Every dimension of the case is one constant in `src/dais/params.py` (mm, degrees).",
        "Values marked **MEASURE** are placeholders waiting for calipers or the coupon test.",
        "",
        "<!-- generated by `dais params`: edit params.py, not this page -->",
    ]
    structured = {"Fasteners": _fastener_table, "Build options": _options_table, "Design looks": _look_table}
    table = False
    for line in src:
        head = re.match(r"# --- (.+?) -+$", line)
        const = re.match(r"([A-Z][A-Z0-9_]*) = ([^#]+?)\s*(?:#\s*(.*))?$", line)
        if head:
            name = head.group(1)
            lines += ["", f"## {name}", ""]
            if name in structured:
                lines += structured[name]()
                table = False
            else:
                lines += ["| Constant | Value | Meaning |", "|---|---|---|"]
                table = True
        elif const and table and not re.match(r"[{\w]+\(|\{", const.group(2)):  # scalars, not dicts/objects
            note = (const.group(3) or "").replace("MEASURE", "**MEASURE**").replace("|", "\\|")
            lines.append(f"| `{const.group(1)}` | {const.group(2)} | {note} |")
    return "\n".join(lines) + "\n"


def _fastener_table() -> list[str]:
    """``FASTENERS``, one column per fastener (mm)."""
    names = list(FASTENERS)
    rows = ["| `FASTENERS` | " + " | ".join(f"`{n}`" for n in names) + " |", "|---" * (len(names) + 1) + "|"]
    for f in fields(Fastener):
        rows.append(f"| `{f.name}` | " + " | ".join(str(getattr(FASTENERS[n], f.name)) for n in names) + " |")
    return rows


def _look_table() -> list[str]:
    """``Look`` defaults (the first four designs) against ``PLINTH`` and ``PLINTH_LONG``."""
    looks = {"default": Look(), "`PLINTH`": PLINTH, "`PLINTH_LONG`": PLINTH_LONG}
    rows = ["| `Look` | " + " | ".join(looks) + " |", "|---" * (len(looks) + 1) + "|"]
    for f in fields(Look):
        rows.append(f"| `{f.name}` | " + " | ".join(str(getattr(v, f.name)) for v in looks.values()) + " |")
    return rows


def _options_table() -> list[str]:
    """``Options`` defaults against ``LEGACY`` (the first prototypes); patterns: ``PATTERNS``."""
    rows = ["| `Options` | default | `LEGACY` |", "|---|---|---|"]
    for f in fields(Options):
        rows.append(f"| `{f.name}` | {getattr(Options(), f.name)} | {getattr(LEGACY, f.name)} |")
    return [*rows, "", "`PATTERNS`: " + ", ".join(f"`{p}`" for p in PATTERNS) + " (split top case sides)."]


def cmd_params(args: argparse.Namespace) -> None:
    """Write (or print) the parameter reference page."""
    text = params_markdown()
    if args.out == "-":
        print(text, end="")
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        log.info("wrote %s", args.out)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(prog="dais", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser, out: str) -> None:
        p.add_argument("--board", choices=sorted(BOARDS), default="microsam")
        p.add_argument(
            "--design", choices=list(DESIGNS), action="append", help="only this design (repeatable; default: all)"
        )
        p.add_argument("--out", default=out, help=f"output root (default: {out})")
        p.add_argument("-j", "--jobs", type=int, default=None, help="parallel processes (default: CPUs)")
        p.add_argument("--pattern", choices=[*PATTERNS, "all"], help="skin pattern on the split top case sides")
        p.add_argument("--plate", choices=["integrated", "separate"], help="switch plate (default integrated)")
        p.add_argument("--fastener", choices=sorted(FASTENERS), help="case screws (default insert: M3 heat-set)")
        p.add_argument("--bevel", type=float, help="bed-side chamfer angle from horizontal, deg (default 60)")
        p.add_argument(
            "--seat", choices=["generic", "pocket"], help="split controller seat (default generic: jaws + clamp)"
        )
        p.add_argument("--legacy", action="store_true", help="first-prototype build: separate plate, M2, 45 deg")

    p = sub.add_parser("build", help="build, check and export STL + STEP")
    common(p, "out")
    p.add_argument("--clean", action="store_true", help="remove <out>/<board>/ first")
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("render", help="render the SVG views for the docs")
    common(p, "docs/public/img")
    p.set_defaults(func=cmd_render)
    p = sub.add_parser("photo", help="photo renders with Blender Cycles (CPU only, RAM-capped)")
    common(p, "docs/public/photo")
    p.add_argument("--shot", action="append", help="only this shot (hero, low, back, exploded, seam; repeatable)")
    p.add_argument("--preview", action="store_true", help="800x600, 24 samples")
    p.add_argument("--samples", type=int, default=None, help="Cycles samples (default 128, preview 24)")
    p.add_argument("--threads", type=int, default=8, help="CPU threads for Cycles (default 8)")
    p.add_argument("--memory", default="2G", help="hard RAM cap of the Blender process (default 2G)")
    p.add_argument(
        "--tiles", type=int, default=None, help="render/denoise as N x N overlapping crops (default 2, preview 1)"
    )
    p.add_argument("--blender", default=None, help="Blender executable (default: $DAIS_BLENDER, PATH, /opt/blender)")
    p.set_defaults(func=cmd_photo)
    sub.add_parser("list", help="list the designs").set_defaults(func=cmd_list)
    p = sub.add_parser("params", help="write the parameter reference page")
    p.add_argument("--out", default="docs/guide/parameters.md", help="output file, - for stdout")
    p.set_defaults(func=cmd_params)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("build123d").setLevel(logging.WARNING)
    args.func(args)


if __name__ == "__main__":
    main()
