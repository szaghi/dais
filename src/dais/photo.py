"""Photo renders of every design through Blender Cycles, CPU only, inside a RAM-capped scope.

Writes ``<out>/<design>/<shot>.webp``. The meshes and the scene description go to a work
directory; Blender runs ``blender_scene.py`` on them with the GPU masked out of its view of the
system (``GPU_MASK``, plus ``CUDA_VISIBLE_DEVICES=""`` and GPU compute backends off), at the
lowest CPU priority, and -- when systemd is available -- in a cgroup scope with a hard memory
limit, so a render can never touch the GPU nor squeeze other work on the machine.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from build123d import Part, export_stl
from PIL import Image

from .designs import DESIGNS, Variant
from .display import make_keycap, make_switch_top
from .params import SPLIT_FRONT_Z
from .render import dummies

log = logging.getLogger(__name__)

BACKGROUND = ((246, 244, 239), (232, 228, 219))  # light backdrop, top -> bottom gradient
EXPLODE = 16.0  # tighter than the drawings: keeps the exploded photos large

Vec = tuple[float, float, float]


@dataclass(frozen=True)
class Shot:
    """One camera: direction ``eye - target`` (mm), visible objects, exploded offsets."""

    name: str
    eye: Vec
    target: Vec = (0.0, 0.0, 12.0)
    objects: tuple[str, ...] = ("shell", "base", "feet", "switch", "keycap")
    offsets: dict[str, Vec] = field(default_factory=dict)
    lens: float = 85.0
    margin: float = 1.05
    focus: tuple[float, float, float, float] | None = None  # close-up: frame this sphere (x, y, z, r) in mm


def shots(split: bool) -> list[Shot]:
    """The shot list of one design."""
    up, up2, up3 = (0.0, 0.0, EXPLODE), (0.0, 0.0, 2 * EXPLODE), (0.0, 0.0, 3.2 * EXPLODE)
    exploded = Shot(
        "exploded",
        (-150.0, -190.0, 130.0),
        objects=("shell", "plate", "base", "feet", "switch", "keycap", "pcb", "usb"),
        offsets={"shell": up2, "plate": up, "switch": up, "keycap": up3, "feet": (0.0, 0.0, -EXPLODE / 2)},
    )
    out = [
        Shot("hero", (-150.0, -190.0, 120.0)),
        Shot("low", (190.0, -150.0, 45.0)),
        Shot("back", (140.0, 200.0, 80.0)),
        exploded,
    ]
    if split:  # macro on the seam at the front-left corner
        corner = (-16.0, -19.0, SPLIT_FRONT_Z + 1.0, 9.0)
        out.append(Shot("seam", (-140.0, -170.0, 25.0), lens=100.0, margin=1.0, focus=corner))
    return out


MATERIAL = {
    "shell": "asa-cf",
    "base": "asa-cf-flat",
    "plate": "asa-cf-flat",
    "feet": "tpu",
    "switch": "switch",
    "keycap": "keycap",
    "pcb": "pcb",
    "usb": "metal",
}


def find_blender(explicit: str | None = None) -> str:
    """``--blender``, then $DAIS_BLENDER, then PATH, then /opt/blender/*/blender (newest)."""
    candidates = (
        explicit,
        os.environ.get("DAIS_BLENDER"),
        shutil.which("blender"),
        *sorted(glob.glob("/opt/blender/*/blender"), reverse=True),
    )
    for cand in candidates:
        if cand and Path(cand).is_file():
            return cand
    raise FileNotFoundError("Blender not found: pass --blender or set DAIS_BLENDER")


# Hide the GPU from Blender completely: in a private user + mount namespace, the WSL GPU device
# (/dev/dxg) becomes /dev/null and the WSL driver libraries (/usr/lib/wsl: libcuda, libdxcore) an
# empty tmpfs, so Cycles cannot even load the CUDA driver -- CUDA_VISIBLE_DEVICES alone still lets
# it open /dev/dxg and map libcuda. On a native Linux GPU box the same idea would mask /dev/nvidia*.
GPU_MASK = (
    'for d in /dev/dxg /dev/nvidia*; do [ -e "$d" ] && mount --bind /dev/null "$d"; done; '
    "[ -d /usr/lib/wsl ] && mount -t tmpfs none /usr/lib/wsl; "
    'exec "$@"'
)


def blender_command(blender: str, script: Path, scene: Path, memory: str) -> list[str]:
    """Blender in background mode, niced, GPU-masked, inside a memory-capped systemd scope."""
    cmd = ["nice", "-n", "19", blender, "-b", "--factory-startup", "-noaudio", "-P", str(script), "--", str(scene)]
    if shutil.which("unshare"):
        cmd = ["unshare", "--user", "--map-root-user", "--mount", "sh", "-c", GPU_MASK, "sh", *cmd]
    else:
        log.warning("unshare not available: the GPU driver stays visible (CUDA_VISIBLE_DEVICES still hides it)")
    if shutil.which("systemd-run"):
        cap = ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={memory}", "-p", "MemorySwapMax=0"]
        return cap + cmd
    log.warning("systemd-run not available: Blender runs WITHOUT a hard memory cap")
    return cmd


def stitch(spec: Path, out: Path) -> None:
    """Join overlapping render crops (see ``blender_scene.render_tiles``) into one RGBA image.

    Inside each overlap the two crops are blended with linear ramps, so the seams of the
    per-tile denoising disappear.

    Raises
    ------
    RuntimeError
        If a crop's size differs from its rectangle: resizing it would shift it by a fraction of a
        pixel and show as a seam.
    """
    meta = json.loads(spec.read_text())
    w, h = meta["width"], meta["height"]
    acc = np.zeros((h, w, 4))
    wsum = np.zeros((h, w, 1))
    for t in meta["tiles"]:
        x0, y0, x1, y1 = t["x0"], t["y0"], t["x1"], t["y1"]
        img = Image.open(t["file"]).convert("RGBA")
        if img.size != (x1 - x0, y1 - y0):
            raise RuntimeError(f"{t['file']}: {img.size} != rectangle {(x1 - x0, y1 - y0)}")
        tw, th = x1 - x0, y1 - y0
        rx = np.minimum(np.arange(tw) + 1, np.arange(tw)[::-1] + 1).astype(float)
        ry = np.minimum(np.arange(th) + 1, np.arange(th)[::-1] + 1).astype(float)
        if x0 == 0:
            rx[: tw // 2] = np.inf  # no neighbour on this side: full weight up to the frame edge
        if x1 == w:
            rx[tw // 2 :] = np.inf
        if y0 == 0:
            ry[: th // 2] = np.inf
        if y1 == h:
            ry[th // 2 :] = np.inf
        weight = np.minimum.outer(np.minimum(ry, 64.0), np.minimum(rx, 64.0))[..., None]
        acc[y0:y1, x0:x1] += np.asarray(img, dtype=float) * weight
        wsum[y0:y1, x0:x1] += weight
    Image.fromarray(np.clip(acc / wsum, 0, 255).round().astype(np.uint8), "RGBA").save(out)


def composite(png: Path, out: Path) -> None:
    """Lay the transparent render (with its shadow-catcher shadows) over the light backdrop."""
    fg = Image.open(png).convert("RGBA")
    w, h = fg.size
    top, bottom = BACKGROUND
    grad = Image.linear_gradient("L").resize((w, h))
    bg = Image.composite(Image.new("RGB", (w, h), bottom), Image.new("RGB", (w, h), top), grad).convert("RGBA")
    Image.alpha_composite(bg, fg).convert("RGB").save(out, quality=90)


def photo(
    board: str,
    todo: list[Variant],
    out: Path,
    work: Path,
    *,
    threads: int,
    samples: int,
    resolution: tuple[int, int],
    memory: str,
    tiles: int = 2,
    blender: str | None = None,
    only: list[str] | None = None,
) -> None:
    """Render each (design, options, output name) of ``todo`` to ``out/<output name>/<shot>.webp``."""
    exe = find_blender(blender)
    script = Path(__file__).with_name("blender_scene.py")
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "HIP_VISIBLE_DEVICES": ""}
    for name, opt, dirname in todo:
        design = DESIGNS[name]
        lay = design.layout(board, opt)
        parts = design.build(board, opt)
        split = "top-case" in parts
        d = dummies(lay)
        solids: dict[str, Part] = {
            "shell": parts["top-case" if split else "body"],
            "base": parts["bottom-case" if split else "bottom"],
            **({"plate": parts["plate"]} if "plate" in parts else {}),  # absent when integrated
            "feet": parts["feet"],
            "switch": make_switch_top(lay),
            "keycap": make_keycap(lay),
            "pcb": d["pcb"],
            "usb": d["usb"],
        }
        mesh_dir, raw_dir = work / dirname / "mesh", work / dirname / "raw"
        for p in (mesh_dir, raw_dir, out / dirname):
            p.mkdir(parents=True, exist_ok=True)
        materials = {**MATERIAL, "shell": "asa-fuzzy"} if opt.pattern == "fuzzy" else MATERIAL
        meshes = []
        for key, solid in solids.items():
            path = mesh_dir / f"{key}.stl"
            export_stl(solid, str(path), tolerance=0.005, angular_tolerance=0.05)
            meshes.append({"name": key, "file": str(path), "material": materials[key]})
        todo = [s for s in shots(split) if not only or s.name in only]
        scene = work / dirname / "scene.json"
        shot_list = [
            {
                "name": s.name,
                "eye": s.eye,
                "target": s.target,
                "objects": [o for o in s.objects if o in solids],
                "offsets": s.offsets,
                "lens": s.lens,
                "margin": s.margin,
                "focus": s.focus,
            }
            for s in todo
        ]
        cfg = {
            "threads": threads,
            "samples": samples,
            "resolution": list(resolution),
            "tiles": tiles,
            "output": str(raw_dir),
            "meshes": meshes,
            "shots": shot_list,
        }
        scene.write_text(json.dumps(cfg, indent=1))
        log.info(
            "%s: %d shots, %d threads, %d samples, %dx%d, RAM cap %s",
            dirname,
            len(todo),
            threads,
            samples,
            *resolution,
            memory,
        )
        subprocess.run(blender_command(exe, script, scene, memory), env=env, check=True)
        for s in todo:
            spec = raw_dir / f"{s.name}.tiles.json"
            if spec.exists():
                stitch(spec, raw_dir / f"{s.name}.png")
                spec.unlink()
            composite(raw_dir / f"{s.name}.png", out / dirname / f"{s.name}.webp")
            log.info("wrote %s", out / dirname / f"{s.name}.webp")
